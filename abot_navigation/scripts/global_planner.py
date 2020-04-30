#!/usr/bin/env python
import rospy
import tf
from nav_msgs.srv import GetMap
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from abot_navigation.srv import Plan,PlanResponse

import numpy as np
import matplotlib.pyplot as plt
import sys


from a_star import AStarPlanner

class GlobalPlanner:
    def __init__(self):
        self.plan_sx = 0.0
        self.plan_sy = 0.0
        self.plan_gx = 8.0
        self.plan_gy = -8.0
        self.plan_grid_size = 0.03
        self.plan_robot_radius = 0.15
        self.plan_ox = []
        self.plan_oy = []
        self.plan_rx = []
        self.plan_ry = []

        self.tf = tf.TransformListener()
        self.goal_sub = rospy.Subscriber('/abot/goal',PoseStamped,self.goalCallback)
        self.plan_srv = rospy.Service('/abot/global_plan',Plan,self.replan)
        self.path_pub = rospy.Publisher('/abot/global_path',Path,queue_size = 1)

        self.updateMap()
        # self.updateGlobalPose()

        pass
    def goalCallback(self,msg):
        self.plan_goal = msg
        self.plan_gx = msg.pose.position.x
        self.plan_gy = msg.pose.position.y
        print("get new goal!!! ",self.plan_goal)
        self.replan(0)
        pass
    def updateGlobalPose(self):
        try:
            self.tf.waitForTransform("/map", "/base_footprint", rospy.Time(), rospy.Duration(4.0))
            (self.trans,self.rot) = self.tf.lookupTransform('/map','/base_footprint',rospy.Time(0))
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            print("get tf error!")
        self.plan_sx = self.trans[0]
        self.plan_sy = self.trans[1]

    def replan(self,req):
        print('get request for replan!!!!!!!!')
        self.updateGlobalPose()
        self.plan_rx,self.plan_ry = self.a_star.planning(self.plan_sx,self.plan_sy,self.plan_gx,self.plan_gy)
        self.publishPath()
        res = True
        return PlanResponse(res)
    def updateMap(self):
        rospy.wait_for_service('/static_map')
        try:
            getMap = rospy.ServiceProxy('/static_map',GetMap)
            self.map = getMap().map
        except:
            e = sys.exc_info()[0]
            print('Service call failed: %s'%e)
        # Update for planning algorithm
        # print(self.map.info.resolution,self.map.info.origin.position.x)
        map_data = np.array(self.map.data).reshape((-1,self.map.info.height)).transpose()
        # M, N = map_data.shape
        # K = 2
        # L = 2
        # MK = M // K
        # NL = N // L
        # map_data = map_data[:MK*K, :NL*L].reshape(MK, K, NL, L).max(axis=(1, 3))
        ox,oy = np.nonzero(map_data > 50)
        self.plan_ox = (ox*self.map.info.resolution+self.map.info.origin.position.x).tolist()
        self.plan_oy = (oy*self.map.info.resolution+self.map.info.origin.position.y).tolist()
        # print("indice : ",self.plan_ox,self.plan_oy)
        self.a_star = AStarPlanner(self.plan_ox,self.plan_oy,self.plan_grid_size,self.plan_robot_radius)

    def showMap(self):
        plt.plot(self.plan_ox, self.plan_oy, ".k")
        plt.plot(self.plan_sx, self.plan_sy, "og")
        plt.plot(self.plan_gx, self.plan_gy, "xb")
        plt.grid(True)
        plt.axis("equal")

    def publishPath(self):
        path = Path()
        path.header.seq = 0
        path.header.stamp = rospy.Time(0)
        path.header.frame_id = 'map'
        for i in range(len(self.plan_rx)):
            pose = PoseStamped()
            pose.header.seq = i
            pose.header.stamp = rospy.Time(0)
            pose.header.frame_id = 'map'
            pose.pose.position.x = self.plan_rx[len(self.plan_rx)-1-i]
            pose.pose.position.y = self.plan_ry[len(self.plan_rx)-1-i]
            pose.pose.position.z = 0.01
            pose.pose.orientation.x = 0#self.rot[0]
            pose.pose.orientation.y = 0#self.rot[1]
            pose.pose.orientation.z = 0#self.rot[2]
            pose.pose.orientation.w = 1#self.rot[3]
            path.poses.append(pose)
        self.path_pub.publish(path)
        
    


def main():
    rospy.init_node('global_planner')
    gp = GlobalPlanner()
    # gp.updateMap()
    # gp.updateGlobalPose()
    # gp.replan(0)
    rospy.spin()
    pass

if __name__ == '__main__':
    main()
