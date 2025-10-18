# ZTS-3000 Anemometer Driver for ROS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Hardware setup

This is a driver for the ZTS-3000 anemometer pair that uses RS485 and Modbus RTU to communicate, specifically:
- ZTS-3000-FXJT-N01-T01 (wind direction sensor, 16 directions)
- ZTS-3000-FSJT-N01-T01 (wind speed sensor, 0-70 m/s range, 0.1 m/s resolution)

Both start out with a modbus ID of 1, so one of them needs to be set to something else, the default config here uses wind speed mapped to 2. This can be done with most modbus tools.

You'll also need a modbus to USB adapter, e.g. the CH341, and connect both sensors to it in parallel.

## Installation

```bash
cd ~/catkin_ws/src
git clone -b ros1 https://github.com/MoffKalast/zts_3000_ros.git
cd ..
rosdep install -i --from-path src/zts_3000_ros -y
catkin_make
```

Install version 3.6.X of pymodbus specifically, there are significant API differences between versions:

```bash
pip install pymodbus=3.6.9
```

## Udev Rule Setup

Create `/etc/udev/rules.d/99-anemometer.rules` and add a rule to map your RS485 MODBUS to USB adapter to /dev/ttyMODBUS, here's an example for CH341:
```bash
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="ttyMODBUS", MODE="0666"
```

The vendor id, product id and serial can be found with `udevadm info -a -n /dev/ttyUSB0`.

Reload udev rules:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Usage
```bash
roslaunch zts_3000_ros anemometer.launch
```
## Parameters
- `~port` (string, default: "/dev/ttyMODBUS") - Serial port device
- `~baud` (int, default: 4800) - Baud rate
- `~modbus_id_wind_dir` (int, default: 1) - Modbus slave ID for direction sensor
- `~modbus_id_wind_speed` (int, default: 2) - Modbus slave ID for speed sensor
- `~frame_id` (string, default: "anemometer_link") - TF frame for published data

## Topics

- `/wind` (geometry_msgs/Vector3Stamped) - Wind vector in m/s
- `/wind/speed` (std_msgs/Float32) - Wind speed magnitude in m/s
- `/wind/dir` (std_msgs/Float32) - Wind direction in radians