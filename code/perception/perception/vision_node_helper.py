# CARLA visualization colors, indexed by CARLA class id (0..12)
carla_colors = [
    [0, 0, 0],  # 0: None
    [70, 70, 70],  # 1: Buildings
    [190, 153, 153],  # 2: Fences
    [72, 0, 90],  # 3: Other
    [220, 20, 60],  # 4: Pedestrians
    [153, 153, 153],  # 5: Poles
    [157, 234, 50],  # 6: RoadLines
    [128, 64, 128],  # 7: Roads
    [244, 35, 232],  # 8: Sidewalks
    [107, 142, 35],  # 9: Vegetation
    [0, 0, 255],  # 10: Vehicles
    [102, 102, 156],  # 11: Walls
    [220, 220, 0],  # 12: TrafficSigns
]

# Human-readable names, indexed by CARLA class id (0..12)
carla_class_names = [
    "None",
    "Buildings",
    "Fences",
    "Other",
    "Pedestrians",
    "Poles",
    "RoadLines",
    "Roads",
    "Sidewalks",
    "Vegetation",
    "Vehicles",
    "Walls",
    "TrafficSigns",
]

# COCO category ids as emitted by torchvision detection models
# (category_id, 0 == background).
# See: https://pytorch.org/vision/stable/models.html#object-detection
PERSON_LABEL = 1
TRAFFIC_LIGHT_LABEL = 10


def _build_tvrcnn_label_to_carla():
    """Map a torchvision COCO category_id (index) to a CARLA class id.

    Default is 3 (Other); only the categories relevant for driving are mapped.
    This reproduces the same CARLA classes that the previous ultralytics-based
    mapping produced, so downstream consumers are unaffected.
    """
    mapping = [3] * 91  # indices 0..90, 0 == background -> Other
    mapping[PERSON_LABEL] = 4  # Person -> Pedestrians
    mapping[2] = 10  # Bicycle -> Vehicles
    mapping[3] = 10  # Car -> Vehicles
    mapping[4] = 10  # Motorbike -> Vehicles
    mapping[5] = 10  # Airplane -> Vehicles
    mapping[6] = 10  # Bus -> Vehicles
    mapping[7] = 10  # Train -> Vehicles
    mapping[8] = 10  # Truck -> Vehicles
    mapping[9] = 10  # Boat -> Vehicles
    mapping[TRAFFIC_LIGHT_LABEL] = 12  # Traffic Light -> TrafficSigns
    mapping[13] = 12  # Stop Sign -> TrafficSigns
    return mapping


tvrcnn_label_to_carla = _build_tvrcnn_label_to_carla()

COCO_CLASS_COUNT = 80
