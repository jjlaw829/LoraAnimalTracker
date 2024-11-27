import smbus
import time
import math

import os, sys
sys.path.append("/home/ip")
import accelerometertest


# I2C bus (use 1 for Raspberry Pi 3 or 4)
bus = smbus.SMBus(1)

# QMC5883L I2C address
address = 0x0D

# Function to read a 16-bit value (high and low byte)
def read_word(reg):
    high = bus.read_byte_data(address, reg)
    low = bus.read_byte_data(address, reg + 1)
    value = (high << 8) + low
    # Handle two's complement
    if value >= 32768:
        value -= 65536
    return value

# # Fix to make low byte the least significant byte, according to datasheet
# def read_word(reg):
    # high = bus.read_byte_data(address, reg)
    # low = bus.read_byte_data(address, reg - 1)
    # value = (high << 8) + low
    # # Handle two's complement
    # if value >= 32768:
        # value -= 65536
    # return value

# Initialize the QMC5883L (default 0x09, 0x01)  **Changed this to match QMC5883lCompass arduino library, and readings got much more accurate. Think register addresses are incorrect now
bus.write_byte_data(address, 0x09, 0x29)  # Set the measurement mode
time.sleep(0.1)  # Wait for the sensor to stabilize

# Calibration function
def calibrate_sensor(samples=1000):
    # Initialize min/max values for each axis
    x_min, x_max = float('inf'), float('-inf')
    y_min, y_max = float('inf'), float('-inf')
    z_min, z_max = float('inf'), float('-inf')

    print("Collecting calibration data... Please rotate the sensor in all directions.")
    for _ in range(samples):
        # Read the magnetic field data (X, Y, Z)  **changed from 0x03, 0x05, 0x07 to match datasheet
        x = read_word(0x01)
        y = read_word(0x03)
        z = read_word(0x05)
        
        # Update min/max for each axis
        x_min = min(x_min, x)
        x_max = max(x_max, x)
        y_min = min(y_min, y)
        y_max = max(y_max, y)
        z_min = min(z_min, z)
        z_max = max(z_max, z)

        time.sleep(0.05)

    # Compute offsets (average of min and max) and scaling factors (half the range)
    x_offset = (x_max + x_min) / 2
    y_offset = (y_max + y_min) / 2
    z_offset = (z_max + z_min) / 2

    x_scale = (x_max - x_min) / 2
    y_scale = (y_max - y_min) / 2
    z_scale = (z_max - z_min) / 2

    # Return the calibration parameters
    print("Calibration complete.")
    print(f"Offsets: X={x_offset}, Y={y_offset}, Z={z_offset}")
    print(f"Scales: X={x_scale}, Y={y_scale}, Z={z_scale}")

    return x_offset, y_offset, z_offset, x_scale, y_scale, z_scale

# Direction from degree function
def get_direction(degree):
    """Return the compass direction based on the azimuth degree."""
    if 22.5 <= degree < 67.5:
        return "NE"
    elif 67.5 <= degree < 112.5:
        return "E"
    elif 112.5 <= degree < 157.5:
        return "SE"
    elif 157.5 <= degree < 202.5:
        return "S"
    elif 202.5 <= degree < 247.5:
        return "SW"
    elif 247.5 <= degree < 292.5:
        return "W"
    elif 292.5 <= degree < 337.5:
        return "NW"
    else:
        return "N"
        
# Magnetic Declination Function
def set_magnetic_declination(degrees, minutes):
    md = float(degrees + minutes/60.0)
    return md
    
# Function to calculate heading in degrees
def calculate_heading(x, y):
    # Calculate angle in radians
    angle_rad = math.atan2(y, x)

    # Convert angle to degrees
    heading = math.degrees(angle_rad)
    
    # Adjust for magnetic declination  **Added this to match arduino
    magnetic_declination = set_magnetic_declination(-5, 23)
    heading += magnetic_declination
    
    
    # Normalize the heading to 0-360 degrees
    if heading < 0:
        heading += 360
        
    # Fix upside down sensor
    heading = 360 - heading
    
    return heading
    
# Function for tilt compensation with  MPU6050
# Xm, Ym, Zm are calibrated magnetic sensor measurements
def tilt_compensation(Xm, Ym, Zm):
    pitch, roll = accelerometertest.calculate_orientation()
    
    # Tilt compensated X value
    Xh = (Xm * math.cos(pitch)) + (Zm * math.sin(pitch))
    
    # Tilt compensated Y value
    Yh = (Xm * math.sin(roll) * math.sin(pitch)) + (Ym * math.sin(roll) * math.cos(pitch))
    
    return Xh, Yh
    
    
# Calibrate the sensor (you can change the number of samples)
#x_offset, y_offset, z_offset, x_scale, y_scale, z_scale = calibrate_sensor(samples=500)
x_offset, y_offset, z_offset, x_scale, y_scale, z_scale = -1383.00, -440.00, 889.00, 1.27, 0.93, 0.8

# Now you can use these calibration parameters to adjust the sensor readings
while True:
    # Read the magnetic field data (X, Y, Z)
    x_raw = read_word(0x01)
    y_raw = read_word(0x03)
    z_raw = read_word(0x05)

    # Output raw values for debugging
    print(f"Raw X: {x_raw}, Y: {y_raw}, Z: {z_raw}")

    # Apply calibration offsets and scaling factors
    x = (x_raw - x_offset) / x_scale
    y = (y_raw - y_offset) / y_scale
    z = (z_raw - z_offset) / z_scale

    # Calculate the heading (magnetic north)
    heading = calculate_heading(x, y)
    
    # Get direction facing
    direction = get_direction(heading)
    
    # Tilt compensated heading
    Xh, Yh = tilt_compensation(x, y, z)
    heading_tilt = calculate_heading(Xh, Yh)
    
    # Tilt compensated direction
    direction_tilt = get_direction(heading_tilt) 
    
    # Output the adjusted sensor values and heading
    print(f"Calibrated X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}, Heading: {heading:.2f} degrees, Pointing: {direction}")
    print(f"Tilt-Compensated Heading: {heading_tilt:.2f}, Pointing {direction_tilt}\n")
    
    time.sleep(1)  # Update interval
