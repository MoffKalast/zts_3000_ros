#!/usr/bin/env python3
"""
Fast Modbus polling (synchronous) for ZTS-3000 wind sensors.
Compatible with pymodbus 3.9.x
"""

import time
import math
from pymodbus.client import ModbusSerialClient

# Lookup table mapping ADDR3 values to 16-point compass directions
addr3_wind_direction = {
    112: 157.5, 96: 180, 224: 202.5, 192: 225, 
    193: 247.5, 129: 270, 131: 292.5, 3: 315,
    7: 337.5, 6: 0, 14: 22.5, 12: 45,
    28: 67.5, 24: 90, 56: 112.5, 48: 135
}

# ---- Configuration ----
PORT = "/dev/ttyUSB0"
BAUDRATE = 4800
PARITY = "N"
STOPBITS = 1
BYTESIZE = 8
TIMEOUT = 1.0  # Increased timeout

SPEED_ID = 2
DIR_ID = 1

def read_register(client, device_id, address, count=1):
    """Read holding registers using synchronous API."""
    # Try both parameter names for compatibility
    try:
        result = client.read_holding_registers(
            address=address, 
            count=count, 
            slave=device_id  # Changed from device_id to slave
        )
    except TypeError:
        # Fallback if 'slave' doesn't work
        result = client.read_holding_registers(
            address=address, 
            count=count, 
            unit=device_id  # Or try 'unit'
        )
    
    if result.isError():
        raise IOError(f"Modbus error from device {device_id} at {address}: {result}")
    return result.registers


client = ModbusSerialClient(
    port=PORT,
    baudrate=BAUDRATE,
    parity=PARITY,
    stopbits=STOPBITS,
    bytesize=BYTESIZE,
    timeout=TIMEOUT  # Explicit timeout
)

if not client.connect():
    print("Failed to open serial port")
    exit(1)

print("Polling sensors...")
try:
    while True:
        try:
            # --- Speed ---
            speed_regs = read_register(client, SPEED_ID, 0, 1)
            raw_speed = speed_regs[0]
            speed = raw_speed / 10.0  # m/s

            # --- Direction ---
            dir_regs = read_register(client, DIR_ID, 3, 1)
            direction_deg = addr3_wind_direction.get(dir_regs[0])

            if direction_deg is None:
                print(f"Unknown direction code: {dir_regs[0]}")
                time.sleep(0.1)
                continue

            # --- Vector (math convention) ---
            rad = math.radians(direction_deg)
            vx = speed * math.cos(rad)
            vy = speed * math.sin(rad)

            print(
                f"Speed: {speed:5.2f} m/s | "
                f"Dir: {direction_deg:6.1f}° | "
                f"Vector: ({vx:6.2f}, {vy:6.2f})"
            )
            
            time.sleep(0.1)  # Small delay between reads

        except Exception as e:
            print(f"Read error: {e}")
            time.sleep(2.0)

except KeyboardInterrupt:
    print("Stopped.")
finally:
    client.close()