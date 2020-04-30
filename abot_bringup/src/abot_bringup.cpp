#include "abot_bringup/abot.h"

double RobotV_ = 0;
double YawRate_ = 0;
double last_received_time = 0;
// 速度控制消息的回调函数
void cmdCallback(const geometry_msgs::Twist& msg)
{
	RobotV_ = msg.linear.x * 1000;
	YawRate_ = msg.angular.z;
    last_received_time = ros::WallTime::now().toSec();
}
    
int main(int argc, char** argv)
{
    //初始化ROS节点
	ros::init(argc, argv, "abot_bringup");									
    ros::NodeHandle nh;
    
    //初始化abot
    abot::ABot robot;
    if(!robot.init())
        ROS_ERROR("abot initialized failed.");
	ROS_INFO("abot initialized successful.");
    
    ros::Subscriber sub = nh.subscribe("cmd_vel", 50, cmdCallback);
    
    last_received_time = ros::WallTime::now().toSec();
    //循环运行
    ros::Rate loop_rate(50);
	while (ros::ok()) 
    {
		if (ros::WallTime::now().toSec() - last_received_time > 0.5)
		{
			RobotV_ = 0;
			YawRate_ = 0;
            ROS_INFO("No cmd_vel received!");
		}
        ros::spinOnce();
        
        // 机器人控制
       	robot.spinOnce(RobotV_, YawRate_);
        
		loop_rate.sleep();
	}

	return 0;
}

