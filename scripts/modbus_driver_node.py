#!/usr/bin/env python3
"""
ROS Noetic node for ZTS-3000 wind sensors via Modbus.
Publishes wind speed, direction, and vector data.
"""

import rospy
import math
from pymodbus.client import ModbusSerialClient
from geometry_msgs.msg import Vector3Stamped
from std_msgs.msg import Float32

# Lookup table mapping ADDR3 values to 16-point compass directions
ADDR3_WIND_DIRECTION = {
	112: 157.5, 96: 180, 224: 202.5, 192: 225, 
	193: 247.5, 129: 270, 131: 292.5, 3: 315,
	7: 337.5, 6: 0, 14: 22.5, 12: 45,
	28: 67.5, 24: 90, 56: 112.5, 48: 135
}


class AnemometerNode:
	def __init__(self):
		rospy.init_node('anemometer_node')
		
		# Parameters
		self.port = rospy.get_param('~port', '/dev/ttyMODBUS')
		self.baudrate = rospy.get_param('~baud', 4800)
		self.speed_id = rospy.get_param('~modbus_id_wind_speed', 2)
		self.dir_id = rospy.get_param('~modbus_id_wind_dir', 1)
		self.frame_id = rospy.get_param('~frame_id', 'anemometer_link')
		
		# Serial parameters (fixed for ZTS-3000)
		self.parity = 'N'
		self.stopbits = 1
		self.bytesize = 8
		self.timeout = 1.0
		self.data_received = False
		
		# Publishers
		self.wind_pub = rospy.Publisher('/wind', Vector3Stamped, queue_size=10)
		self.speed_pub = rospy.Publisher('/wind/speed', Float32, queue_size=10)
		self.dir_pub = rospy.Publisher('/wind/dir', Float32, queue_size=10)
		
		# Initialize Modbus client
		self.client = ModbusSerialClient(
			port=self.port,
			baudrate=self.baudrate,
			parity=self.parity,
			stopbits=self.stopbits,
			bytesize=self.bytesize,
			timeout=self.timeout
		)
		
		while not self.client.connect():
			rospy.logerr(f"Waiting to connect to Modbus device on {self.port}")
			rospy.sleep(2.0)
		
		rospy.loginfo(f"Connected to anemometer on {self.port} at {self.baudrate} baud")
		rospy.loginfo(f"Speed sensor ID: {self.speed_id}, Direction sensor ID: {self.dir_id}")
	
	def read_register(self, device_id, address, count=1):
		"""Read holding registers with version compatibility."""
		try:
			# Try 'slave' parameter for pymodbus 3.9.x compatibility
			result = self.client.read_holding_registers(
				address=address, 
				count=count, 
				slave=device_id
			)
		except TypeError:
			try:
				# Fallback to 'unit' parameter
				result = self.client.read_holding_registers(
					address=address, 
					count=count, 
					unit=device_id
				)
			except TypeError:
				# Fallback to 'device_id' parameter (newer versions)
				result = self.client.read_holding_registers(
					address=address, 
					count=count, 
					device_id=device_id
				)
		
		if result.isError():
			raise IOError(f"Modbus error from device {device_id} at address {address}")
		return result.registers
	
	def publish_data(self, speed, direction, vx, vy):
		"""Publish wind data to ROS topics."""
		if speed is None:
			return
		
		timestamp = rospy.Time.now()
		
		# Publish Vector3Stamped
		wind_msg = Vector3Stamped()
		wind_msg.header.stamp = timestamp
		wind_msg.header.frame_id = self.frame_id
		wind_msg.vector.x = vx
		wind_msg.vector.y = vy
		wind_msg.vector.z = 0.0
		self.wind_pub.publish(wind_msg)
		
		# Publish speed
		speed_msg = Float32()
		speed_msg.data = speed
		self.speed_pub.publish(speed_msg)
		
		# Publish direction
		dir_msg = Float32()
		dir_msg.data = direction
		self.dir_pub.publish(dir_msg)
	
	def update(self):
		"""Read wind speed and direction from sensors."""
		try:
			# Read speed (register 0)
			speed_regs = self.read_register(self.speed_id, 0, 1)
			raw_speed = speed_regs[0]
			speed = raw_speed / 10.0  # Convert to m/s
			
			# Read direction (register 3)
			dir_regs = self.read_register(self.dir_id, 3, 1)
			direction_deg = ADDR3_WIND_DIRECTION.get(dir_regs[0])
			
			if direction_deg is None:
				rospy.logwarn(f"Unknown direction code: {dir_regs[0]}")
			
			# Calculate vector components (math convention: 0° = East, CCW positive)
			rad = math.radians(direction_deg)
			vx = speed * math.cos(rad)
			vy = speed * math.sin(rad)

			if not self.data_received:
				rospy.loginfo("Data received! SPD:"+str(speed)+" DIR:"+str(direction_deg))
				self.data_received = True

			self.publish_data(speed, rad, vx, vy)
			
		except Exception as e:
			rospy.logerr(f"Error reading sensors: {e}")
			return
			
	def cleanup(self):
		"""Clean shutdown."""
		rospy.loginfo("Shutting down anemometer node")
		if self.client:
			self.client.close()


node = AnemometerNode()
rospy.on_shutdown(node.cleanup)

rate = rospy.Rate(10)
while not rospy.is_shutdown():
	node.update()
	rate.sleep()
