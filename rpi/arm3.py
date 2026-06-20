from pymavlink import mavutil
import time

# Use the stable UART
connection_string = '/dev/ttyAMA0'
baud_rate = 57600

print("Connecting to Pixhawk via SERIAL1 (TELEM1)...")

master = mavutil.mavlink_connection(connection_string, baud=baud_rate)

master.wait_heartbeat()
print("Heartbeat received!")

# ARM
print("Arming...")
master.arducopter_arm()
master.motors_armed_wait()
print("Armed!")

# Wait 15 sec
time.sleep(15)

# DISARM
print("Disarming...")
master.arducopter_disarm()
master.motors_disarmed_wait()
print("Disarmed!")
