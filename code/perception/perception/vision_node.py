from typing import List
import copy

import cv2
import numpy as np
import torch
from sklearn.cluster import DBSCAN

import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor
from paf_common.parameters import update_attributes
from rclpy.parameter import Parameter

from cv_bridge import CvBridge
from sensor_msgs.msg import Image as ImageMsg
from perception_interfaces.msg import TrafficLightImages
from mapping_interfaces.msg import ClusteredPointsArray

# Permissively-licensed (BSD-3-Clause) detectors from torchvision.
# NOTE: This intentionally replaces the AGPL-3.0 `ultralytics` (YOLOv8/YOLO11)
# models previously used here, which were incompatible with this MIT-licensed
# project. See THIRD_PARTY_LICENSES.md for details.
from torchvision.models.detection import (
    fasterrcnn_resnet50_fpn_v2,
    FasterRCNN_ResNet50_FPN_V2_Weights,
    fasterrcnn_mobilenet_v3_large_320_fpn,
    FasterRCNN_MobileNet_V3_Large_320_FPN_Weights,
    retinanet_resnet50_fpn_v2,
    RetinaNet_ResNet50_FPN_V2_Weights,
)
from torchvision.utils import draw_bounding_boxes

from .vision_node_helper import (
    tvrcnn_label_to_carla,
    carla_class_names,
    carla_colors,
    TRAFFIC_LIGHT_LABEL,
)
from .perception_utils import array_to_clustered_points


class VisionNode(Node):
    """
    VisionNode:

    The Vision-Node provides object-detection features.
    It can handle different camera angles and easily switch between
    pretrained torchvision detection models.

    Detection is performed with permissively-licensed torchvision models
    (Apache/BSD-licensed COCO weights). Each detection's bounding box is
    converted to a binary mask so that the existing lidar-point extraction,
    clustering and downstream mapping pipeline stay unchanged.
    """

    def __init__(self):
        super().__init__(type(self).__name__)
        self.get_logger().info(f"{type(self).__name__} node initializing...")

        # dictionary of pretrained models: name -> (factory, weights_enum)
        self.model_dict = {
            "fasterrcnn_resnet50_fpn_v2": (
                fasterrcnn_resnet50_fpn_v2,
                FasterRCNN_ResNet50_FPN_V2_Weights,
            ),
            "fasterrcnn_mobilenet_v3_large_320_fpn": (
                fasterrcnn_mobilenet_v3_large_320_fpn,
                FasterRCNN_MobileNet_V3_Large_320_FPN_Weights,
            ),
            "retinanet_resnet50_fpn_v2": (
                retinanet_resnet50_fpn_v2,
                RetinaNet_ResNet50_FPN_V2_Weights,
            ),
        }

        # general setup
        self.bridge = CvBridge()

        # Parameters
        self.role_name = (
            self.declare_parameter("role_name", "hero")
            .get_parameter_value()
            .string_value
        )
        self.view_camera = (
            self.declare_parameter("view_camera", False)
            .get_parameter_value()
            .bool_value
        )
        self.camera_resolution = (
            self.declare_parameter("camera_resolution", 1280)
            .get_parameter_value()
            .integer_value
        )
        self.model = (
            self.declare_parameter("model", "fasterrcnn_resnet50_fpn_v2")
            .get_parameter_value()
            .string_value
        )
        self.score_threshold = (
            self.declare_parameter(
                "score_threshold",
                0.5,
                descriptor=ParameterDescriptor(
                    description="Minimum detection confidence to keep a box",
                ),
            )
            .get_parameter_value()
            .double_value
        )
        # Traffic light parameters
        self.min_x: int = (
            self.declare_parameter(
                "min_x",
                485,
                descriptor=ParameterDescriptor(
                    description="Left End of Traffic Light bounding box",
                ),
            )
            .get_parameter_value()
            .integer_value
        )
        self.max_x: int = (
            self.declare_parameter(
                "max_x",
                780,
                descriptor=ParameterDescriptor(
                    description="Right End of Traffic Light bounding box",
                ),
            )
            .get_parameter_value()
            .integer_value
        )
        self.max_y: int = (
            self.declare_parameter(
                "max_y",
                360,
                descriptor=ParameterDescriptor(
                    description="Lower End of Traffic Light bounding box measuring "
                    "from the top. (0,0) is the top left corner",
                ),
            )
            .get_parameter_value()
            .integer_value
        )
        self.min_prob: float = (
            self.declare_parameter(
                "min_prob",
                0.30,
                descriptor=ParameterDescriptor(
                    description="Minimal Probability, that it's a light",
                ),
            )
            .get_parameter_value()
            .double_value
        )

        self.depth_images = []
        self.lidar_array = None

        self.setup_subscriber()
        self.setup_publisher()
        self.setup_model()

        self.add_on_set_parameters_callback(self._set_parameters_callback)
        self.get_logger().info(f"{type(self).__name__} node initialized.")

    def _set_parameters_callback(self, params: List[Parameter]):
        """Callback for parameter updates."""
        return update_attributes(self, params)

    def setup_subscriber(self):
        self.create_subscription(
            msg_type=ImageMsg,
            callback=self.handle_camera_image,
            topic=f"/carla/{self.role_name}/Center/image",
            qos_profile=1,
        )

        self.create_subscription(
            msg_type=ImageMsg,
            callback=self.handle_lidar_array,
            topic="/paf/hero/Center/dist_array",
            qos_profile=1,
        )

    def setup_publisher(self):
        """
        sets up all publishers for the Vision-Node
        """

        self.pointcloud_publisher = self.create_publisher(
            msg_type=ClusteredPointsArray,
            topic=f"/paf/{self.role_name}/visualization_pointcloud",
            qos_profile=1,
        )

        self.publisher_center = self.create_publisher(
            msg_type=ImageMsg,
            topic=f"/paf/{self.role_name}/Center/segmented_image",
            qos_profile=1,
        )

        self.traffic_light_publisher = self.create_publisher(
            msg_type=TrafficLightImages,
            topic=f"/paf/{self.role_name}/Center/segmented_traffic_light",
            qos_profile=1,
        )

    def setup_model(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self.model not in self.model_dict:
            available = ", ".join(self.model_dict.keys())
            raise ValueError(
                f"Model '{self.model}' is not supported. Available: {available}"
            )
        factory, weights_enum = self.model_dict[self.model]
        self.get_logger().info(
            f"Loading torchvision model '{self.model}' on device '{self.device}' "
            f"(weights: {weights_enum.DEFAULT})"
        )
        # Weights are downloaded from download.pytorch.org on first use.
        self.model = factory(weights=weights_enum.DEFAULT)
        self.model.eval()
        self.model.to(self.device)

    def handle_camera_image(self, image):
        """
        This function handles a new camera image and publishes the
        calculated visualization according to the correct camera angle

        Args:
            image (image msg): Image from camera scubscription
        """
        prediction = self.predict(
            image=image,
            image_size=self.camera_resolution,
            lidar_array=copy.deepcopy(self.lidar_array),
        )

        if self.view_camera and prediction is not None:
            cv_image, boxes, carla_classes = prediction
            self.publish_image(cv_image, image.header, boxes, carla_classes)

    def handle_lidar_array(self, lidar_array):
        """
        This function overwrites the current lidar depth image from
        the lidar distance node with the latest depth image.
        The function also calculates the depth values of the lidar

        Args:
            lidar_array (image msg): Depth image frim Lidar Distance Node
        """
        # callback function for lidar depth image
        # since frequency is lower than image frequency
        # the latest lidar image is saved
        lidar_array = self.bridge.imgmsg_to_cv2(
            img_msg=lidar_array, desired_encoding="passthrough"
        )
        lidar_array_copy = copy.deepcopy(lidar_array)
        # add camera height to the z-axis
        lidar_array_copy[..., 2] += 1.7
        self.lidar_array = lidar_array_copy

    def _boxes_to_masks(self, boxes, image_shape):
        """Convert xyxy bounding boxes to boolean masks of shape (N, H, W).

        Each box becomes a filled rectangle so it can be fed into the existing
        segmentation-mask based lidar-point extraction.
        """
        h, w = image_shape[:2]
        masks = np.zeros((len(boxes), h, w), dtype=bool)
        for i, (x1, y1, x2, y2) in enumerate(boxes):
            x1 = int(max(0, min(w, x1)))
            y1 = int(max(0, min(h, y1)))
            x2 = int(max(0, min(w, x2)))
            y2 = int(max(0, min(h, y2)))
            if x2 > x1 and y2 > y1:
                masks[i, y1:y2, x1:x2] = True
        return masks

    def predict(self, image, lidar_array, image_size=640):
        """
        This function takes in an image from a camera, runs a torchvision
        detection model on it and looks for lidar points inside the
        detected bounding boxes.

        This function also implements a visualization of what has been
        calculated for RViz.

        Args:
            image (image msg): image from camera subsription

        Returns:
            (cv image, boxes, carla_classes): visualization output for rviz
                and the raw detections, or None if nothing was detected.
        """
        if lidar_array is None or lidar_array.size == 0:
            self.get_logger().warn("No valid lidar data found", throttle_duration_sec=2)
            return None
        cv_image = self.bridge.imgmsg_to_cv2(
            img_msg=image, desired_encoding="passthrough"
        )
        # image is with encoding bgr8 therefore we need to convert it to rgb
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

        # torchvision detection models expect float tensors in [0, 1], CHW
        img_tensor = (
            torch.from_numpy(cv_image).permute(2, 0, 1).to(dtype=torch.float32) / 255.0
        )
        img_tensor = img_tensor.to(self.device)

        with torch.inference_mode():
            output = self.model([img_tensor])[0]

        boxes = output["boxes"].cpu().numpy()
        labels = output["labels"].cpu().numpy()
        scores = output["scores"].cpu().numpy()

        keep = scores >= self.score_threshold
        boxes, labels = boxes[keep], labels[keep]

        if len(boxes) == 0:
            self.pointcloud_publisher.publish(ClusteredPointsArray())
            return None

        carla_classes = np.asarray(tvrcnn_label_to_carla)[labels]

        # proceed with traffic light detection
        if TRAFFIC_LIGHT_LABEL in labels:
            self.process_traffic_lights(boxes, scores, labels, cv_image, image.header)

        masks = self._boxes_to_masks(boxes, cv_image.shape[:2])
        valid_points, class_indices = self.process_segmentation_mask(
            masks,
            lidar_array=lidar_array,
        )
        if valid_points is None or valid_points.size == 0:
            self.pointcloud_publisher.publish(ClusteredPointsArray())
            return None
        clustered_points, cluster_indices, carla_classes_indices = self.cluster_points(
            valid_points, class_indices, carla_classes
        )
        if clustered_points is None or clustered_points.size == 0:
            self.pointcloud_publisher.publish(ClusteredPointsArray())
            return None
        clustered_lidar_points_msg = array_to_clustered_points(
            self.get_clock().now(),
            clustered_points,
            cluster_indices,
            object_class_array=carla_classes_indices,
        )
        self.pointcloud_publisher.publish(clustered_lidar_points_msg)

        return cv_image, boxes, carla_classes

    def publish_image(self, image, image_header, boxes, carla_classes):
        """
        Publishes the image with the detected bounding boxes to RViz.

        Args:
            image (cv image): image to be published
            image_header: stamp/frame for the image message
            boxes (np.ndarray): detected bounding boxes (xyxy)
            carla_classes (np.ndarray): CARLA class per box
        """
        # Convert image to tensor (CHW, uint8)
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).to(dtype=torch.uint8)

        if len(boxes) > 0:
            boxes_tensor = torch.as_tensor(boxes, dtype=torch.float32)
            names = np.asarray(carla_class_names)[carla_classes].tolist()
            class_colors = [
                tuple(int(c) for c in rgb)
                for rgb in np.array(carla_colors)[carla_classes].tolist()
            ]
            drawn_images = draw_bounding_boxes(
                image_tensor,
                boxes_tensor,
                labels=names,
                colors=class_colors,
                width=3,
            )
        else:
            drawn_images = image_tensor

        # Convert the drawn image back to numpy array and BGR format
        bgr_image = cv2.cvtColor(
            drawn_images.permute(1, 2, 0).cpu().numpy(), cv2.COLOR_RGB2BGR
        )

        # Publish vision result to RViz
        img_msg = self.bridge.cv2_to_imgmsg(bgr_image, encoding="bgr8")
        img_msg.header = image_header
        self.publisher_center.publish(img_msg)

    def process_segmentation_mask(self, segmentation_array, lidar_array):
        # Only process the segmentation mask if the distance array is not None
        car_length = 4.9
        car_width = 1.86436
        # Filter out points that are not in the car and not on the road and are not zero
        car_filter_mask = (
            # filter out points that are not in the car
            (lidar_array[..., 0] >= -car_length / 2)
            & (lidar_array[..., 0] <= car_length / 2)
            & (lidar_array[..., 1] >= -car_width / 2)
            & (lidar_array[..., 1] <= car_width / 2)
        )
        # Filter out points that are on the road
        road_filter_mask = lidar_array[..., 2] >= 0.3
        # Filter out points that are zero
        zero_filter_mask = (
            ~(lidar_array[..., 0] == 0.0)
            & ~(lidar_array[..., 1] == 0.0)
            & ~(lidar_array[..., 2] == 1.7)
        )
        lidar_filter_mask = ~car_filter_mask & road_filter_mask & zero_filter_mask
        # tiled_mask holds all the valid points
        valid_points_from_mask = (
            segmentation_array.astype(bool) & lidar_filter_mask[None, ...]
        )
        # get the x, y, z values of the valid points
        valid_indices = np.nonzero(valid_points_from_mask)
        valid_points = lidar_array[valid_indices[1], valid_indices[2]]
        return valid_points, valid_indices[0]

    def cluster_points(
        self, points, class_indices, carla_classes, eps=0.5, min_samples=2
    ):
        """
        Clusters all points in the point cloud and determines the largest cluster for
        each segmentation class in one pass.

        Parameters:
            points (numpy structured array): Array of points with fields 'x', 'y', 'z'.
            class_indices (numpy array): Array of segmentation mask indices for each
                point
            eps (float): Maximum distance between points to be considered in the same
                neighborhood
            min_samples (int): Minimum number of points to form a dense region (cluster)

        Returns:
            clustered_points (numpy structured array): Points belonging to the largest
                cluster for each class index.
            valid_labels (numpy array): Labels corresponding to each class index (one
                per class).
            valid_class_indices (numpy array): Class indices corresponding to the
                returned points.
        """
        if points.size == 0:
            return np.array([], dtype=points.dtype), [], []

        # Apply DBSCAN clustering to all points at once
        db = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = db.fit_predict(points)

        # Combine class indices and cluster labels to identify unique groups
        combined_labels = np.vstack((class_indices, cluster_labels)).T

        # Ignore noise points (cluster_label == -1)
        valid_mask = cluster_labels != -1
        valid_points = points[valid_mask]
        valid_combined_labels = combined_labels[valid_mask]
        valid_class_indices = class_indices[valid_mask]

        # Find the largest cluster for each class
        unique_combinations, inverse_indices = np.unique(
            valid_combined_labels, axis=0, return_inverse=True
        )
        counts = np.bincount(inverse_indices)

        # Map the largest cluster for each class
        largest_clusters = {}
        for idx, (class_idx, _) in enumerate(unique_combinations):
            if (
                class_idx not in largest_clusters
                or counts[idx] > counts[largest_clusters[class_idx]]
            ):
                largest_clusters[class_idx] = idx

        # Extract points belonging to the largest cluster for each class
        selected_points_mask = np.isin(
            inverse_indices,
            [largest_clusters[class_idx] for class_idx in largest_clusters],
        )
        clustered_points = valid_points[selected_points_mask]

        return (
            clustered_points,
            valid_class_indices[selected_points_mask],
            carla_classes[valid_class_indices[selected_points_mask]],
        )

    def process_traffic_lights(self, boxes, scores, labels, cv_image, image_header):
        # calculates, if a detected traffic light is plausible
        # gathers the indices of the bounding boxes of possible traffic lights
        indices = np.where(labels == TRAFFIC_LIGHT_LABEL)[0]

        msg = TrafficLightImages()
        msg.header = image_header
        msg.images = []

        # set the dynamic values
        min_x = self.min_x
        max_x = self.max_x
        max_y = self.max_y  # 360  # middle of image
        min_prob = self.min_prob  # 0.30

        cv_height, cv_width = cv_image.shape[:2]

        # calculate on every bounding box
        for index in indices:
            box = boxes[index]
            score = scores[index]
            x1, y1, x2, y2 = box
            # calculate values about plausability
            if score < min_prob:
                continue

            if (x2 - x1) * 1.5 > (y2 - y1):
                continue  # ignore horizontal boxes

            if y2 > max_y:
                continue

            if x1 < min_x:
                continue

            if x2 > max_x:
                continue

            x1i, y1i, x2i, y2i = int(x1), int(y1), int(x2), int(y2)
            # crop image
            segmented = cv_image[y1i:y2i, x1i:x2i]
            if segmented.size == 0:
                continue

            traffic_light_image = self.bridge.cv2_to_imgmsg(segmented, encoding="rgb8")
            traffic_light_image.header = image_header
            msg.images.append(traffic_light_image)

        if msg.images:
            # publish collected and cropped traffic light image to the topic
            self.traffic_light_publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    try:
        node = VisionNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
