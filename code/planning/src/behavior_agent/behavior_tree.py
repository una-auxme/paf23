#!/usr/bin/env python

import functools
from py_trees.behaviours import Running
import py_trees_ros
import rospy
import sys
import behaviours
from py_trees.composites import Parallel, Selector, Sequence

"""
Source: https://github.com/ll7/psaf2
"""

# flake8: noqa: E501


def grow_a_tree(role_name):

    rules = Parallel(
        "Rules",
        children=[
            Selector
            ("Priorities",
                children=[
                    Selector("Road Features",
                             children=[
                                 behaviours.maneuvers.LeaveParkingSpace("Leave Parking Space"),
                                 Sequence("Intersection",
                                          children=[
                                              behaviours.road_features.IntersectionAhead
                                              ("Intersection Ahead?"),
                                              Sequence("Intersection Actions",
                                                       children=[
                                                           behaviours.intersection.Approach
                                                           ("Approach Intersection"),
                                                           behaviours.intersection.Wait
                                                           ("Wait Intersection"),
                                                           behaviours.intersection.Enter
                                                           ("Enter Intersection"),
                                                           behaviours.intersection.Leave
                                                           ("Leave Intersection")
                                                       ])
                                          ]),
                             ]),
                    Selector("Laneswitching", children=[
                        Sequence("Laneswitch",
                                children=[
                                    behaviours.road_features.LaneChangeAhead
                                    ("Lane Change Ahead?"),
                                    Sequence("Lane Change Actions",
                                             children=[
                                                 behaviours.lane_change.Approach
                                                 ("Approach Change"),
                                                 behaviours.lane_change.Wait
                                                 ("Wait Change"),
                                                 behaviours.lane_change.Enter
                                                 ("Enter Change"),
                                                 behaviours.lane_change.Leave
                                                 ("Leave Change")
                                             ])
                                ]),
                        Sequence("Overtaking",
                                children=[
                                    behaviours.road_features.OvertakeAhead
                                    ("Overtake Ahead?"),
                                    Sequence("Overtake Actions",
                                             children=[
                                                 behaviours.overtake.Approach
                                                 ("Approach Overtake"),
                                                 behaviours.overtake.Wait
                                                 ("Wait Overtake"),
                                                 behaviours.overtake.Enter
                                                 ("Enter Overtake"),
                                                 behaviours.overtake.Leave
                                                 ("Leave Overtake")
                                             ])
                                ]),

                    ]),
                    behaviours.maneuvers.UnstuckRoutine("Unstuck Routine"),
                    behaviours.maneuvers.Cruise("Cruise")
                ])
        ])

    metarules = Sequence("Meta", children=[behaviours.meta.Start("Start"), rules,
                                           behaviours.meta.End("End")])
    root = Parallel("Root", children=[
        behaviours.topics2blackboard.create_node(role_name),
        metarules,
        Running("Idle")
    ])
    return root


def shutdown(behaviour_tree):
    behaviour_tree.interrupt()


def main():
    """
    Entry point for the demo script.
    """
    rospy.init_node('behavior_tree', anonymous=True)
    role_name = rospy.get_param("~role_name", "hero")
    root = grow_a_tree(role_name)
    behaviour_tree = py_trees_ros.trees.BehaviourTree(root)
    rospy.on_shutdown(functools.partial(shutdown, behaviour_tree))

    if not behaviour_tree.setup(timeout=15):
        rospy.logerr("Tree Setup failed")
        sys.exit(1)
    rospy.loginfo("tree setup worked")
    r = rospy.Rate(5.3)
    while not rospy.is_shutdown():
        behaviour_tree.tick()
        try:
            r.sleep()
        except rospy.ROSInterruptException:
            pass

if __name__ == "__main__":
    main()
