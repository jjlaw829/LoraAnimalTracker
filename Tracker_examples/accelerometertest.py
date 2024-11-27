import os, sys
import math
import time
sys.path.append("/home/ip/LoraAnimalTracker/lib/python3.11/site-packages")
import board
import adafruit_mpu6050

# Accelerometer Setup
i2c = board.I2C()
mpu = adafruit_mpu6050.MPU6050(i2c)


# Calibration offsets (if needed)
#0.5434837768554687 -0.7829039428710937 10.529698901367187 **This is a stand in, get average offset

OFFSET_X = 0
OFFSET_Y = 0
OFFSET_Z = 0
#mpu.accelerometer_offset = (OFFSET_X, OFFSET_Y, OFFSET_Z)

def calculate_orientation():
    accel_x, accel_y, accel_z = mpu.acceleration
    accel_x -= OFFSET_X
    accel_y -= OFFSET_Y
    accel_z -= OFFSET_Z

    # Calculate pitch and roll angles
    pitch = math.atan2(accel_x, math.sqrt(accel_y**2 + accel_z**2)) * 180 / math.pi
    roll = math.atan2(-accel_y, accel_z) * 180 / math.pi

    # Convert to range -180 to 180
    if pitch > 180:
        pitch -= 360
    if roll > 180:
        roll -= 360

    return pitch, roll


def main(args):
    while True:
        accel_x, accel_y, accel_z = mpu.acceleration
        accel_x -= OFFSET_X
        accel_y -= OFFSET_Y
        accel_z -= OFFSET_Z

        pitch, roll = calculate_orientation()
        print(f"Accelerometer values (x, y, z): {accel_x} {accel_y} {accel_z}")
        print(f"Pitch: {pitch:.2f} Roll: {roll:.2f}\n")
        time.sleep(1)
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
