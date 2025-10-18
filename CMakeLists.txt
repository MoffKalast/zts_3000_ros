cmake_minimum_required(VERSION 3.0.2)
project(zts_3000_ros)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  rospy
  std_msgs
)

catkin_package(
  CATKIN_DEPENDS geometry_msgs rospy std_msgs
)

include_directories(
    ${catkin_INCLUDE_DIRS}
)

install(PROGRAMS
    scripts/modbus_driver_node.py
    DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)