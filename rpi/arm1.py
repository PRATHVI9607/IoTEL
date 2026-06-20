from pymavlink import mavutil
import time

# ---- CONFIG ----
# Adjust UART port depending on your RPi
# Common: /dev/ttyAMA0 or /dev/serial0
connection_string = '/dev/serial0'
baud_rate = 57600   # Match this with Pixhawk SERIALx_BAUD

# ---- CONNECT ----
print("Connecting to Pixhawk...")
master = mavutil.mavlink_connection(connection_string, baud=baud_rate)

# Wait for heartbeat
master.wait_heartbeat()
print("Heartbeat received from system (system %u component %u)" %
      (master.target_system, master.target_component))

# ---- ARM ----
print("Arming drone...")

master.mav.command_long_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0,
    1,  # 1 = arm, 0 = disarm
    0, 0, 0, 0, 0, 0
)

# Wait until armed
master.motors_armed_wait()
print("Drone is ARMED")

# ---- WAIT 15 SECONDS ----
print("Waiting for 15 seconds...")
time.sleep(15)

# ---- DISARM ----
print("Disarming drone...")

master.mav.command_long_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0,
    0,  # disarm
    0, 0, 0, 0, 0, 0
)

master.motors_disarmed_wait()
print("Drone is DISARMED")

print("Done.")
