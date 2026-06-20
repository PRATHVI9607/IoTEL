#!/usr/bin/env python3
"""
Simple ARM command for Drone using pymavlink
Run on RPI: python3 arm.py
"""

from pymavlink import mavutil
import sys

try:
    print("[CONNECT] Connecting to PixHawk on /dev/ttyS0...")
    mav = mavutil.mavlink_connection('/dev/ttyS0', baud=57600)
    
    print("[CONNECT] Waiting for HEARTBEAT...")
    msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=30)
    if not msg:
        print("[ERROR] No HEARTBEAT received")
        sys.exit(1)
    
    print("[CONNECT] ✓ Connected!")
    
    print("[ARM] Sending ARM command...")
    mav.mav.command_long_send(
        mav.target_system, 
        mav.target_component, 
        400,  # MAV_CMD_COMPONENT_ARM_DISARM
        0, 
        1,    # Arm
        0, 0, 0, 0, 0, 0
    )
    
    print("[ARM] Waiting for acknowledgement...")
    ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
    
    if ack and ack.result == 0:
        print("[ARM] ✓ Drone Armed Successfully!")
    else:
        print("[ARM] ⚠ Arm command failed or not acknowledged")
        
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
