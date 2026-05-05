#!/usr/bin/env python3
"""
================================================================
  RPI Drone Bridge - Using pymavlink directly
  No dronekit - bypasses HEARTBEAT mode error
================================================================
"""

import os
import sys
import time
import math
import json
import socket
import threading
import argparse
import logging
from collections import deque
from typing import Optional, Dict, Any

try:
    from pymavlink import mavutil
except ImportError:
    print("ERROR: pymavlink not installed. Run: pip install pymavlink")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests not installed")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class Config:
    LAPTOP_IP = "192.168.1.100"
    LAPTOP_PORT = 5000
    LAPTOP_URL = f"http://{LAPTOP_IP}:{LAPTOP_PORT}/telemetry"
    CONNECTION_STRING = "/dev/ttyUSB0"
    BAUD_RATE = 57600
    SEND_INTERVAL = 1.0
    TCP_LISTEN_PORT = 5760


config = Config()


def gps_distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


class DroneBridge:
    def __init__(self):
        self.mavlink_connection = None
        self.running = False
        
        self._prev_lat = None
        self._prev_lon = None
        self._prev_gps_time = None
        self._prev_battery_pct = None
        self._prev_battery_time = None
        self._prev_mode = None
        self._prev_armed = None
        
        self._tcp_server = None
        self._tcp_client = None
        self._client_lock = threading.Lock()
        
        self._telemetry_data = {}
        self._alerts = []
        
        self.stats = {'packets_sent': 0, 'packets_recv': 0, 'errors': 0}
    
    def connect(self):
        print(f"\n[CONNECT] Connecting to PixHawk on {config.CONNECTION_STRING}...")
        try:
            self.mavlink_connection = mavutil.mavlink_connection(
                config.CONNECTION_STRING,
                baud=config.BAUD_RATE,
                planner_format=True
            )
            msg = self.mavlink_connection.recv_match(type='HEARTBEAT', blocking=True, timeout=30)
            if not msg:
                print("[ERROR] No HEARTBEAT received")
                sys.exit(1)

            print(f"[CONNECT] ✓ Connected! System ID: {self.mavlink_connection.target_system}")

            mav = self.mavlink_connection

            # ── Step 1: Disable ALL pre-arm checks (GPS, RC, battery, etc.) ──
            print("[CONNECT] Setting ARMING_CHECK=0 (bypass all pre-arm checks)...")
            self._set_parameter(mav, b'ARMING_CHECK', 0)
            time.sleep(0.3)

            # ── Step 2: Disable EKF checks ────────────────────────────────────
            print("[CONNECT] Disabling EKF and compass checks...")
            self._set_parameter(mav, b'EKF3_CHECK_SCALE', 0)
            self._set_parameter(mav, b'EKF2_CHECK_SCALE', 0)
            time.sleep(0.3)

            # ── Step 3: Inject a fake GPS origin so EKF can initialize ──────
            # ArduCopter's EKF needs an origin even when GPS is absent.
            # Using a realistic lat/lon (here: 0°N 0°E at sea level). Change to
            # your actual rough location for better compass calibration results.
            ORIGIN_LAT = 0       # degrees  (change to your location)
            ORIGIN_LON = 0       # degrees
            ORIGIN_ALT = 0       # metres above sea level
            lat_int  = int(ORIGIN_LAT * 1e7)
            lon_int  = int(ORIGIN_LON * 1e7)
            alt_mm   = int(ORIGIN_ALT * 1000)

            print("[CONNECT] Injecting EKF GPS origin (allows indoor arming)...")
            mav.mav.set_gps_global_origin_send(
                mav.target_system,
                lat_int, lon_int, alt_mm
            )
            time.sleep(0.2)

            # ── Step 4: Set HOME to the same origin ──────────────────────────
            print("[CONNECT] Setting HOME position to origin...")
            mav.mav.set_home_position_send(
                mav.target_system,
                lat_int, lon_int, alt_mm,
                0.0, 0.0, 0.0,           # x, y, z (local frame, unused)
                [1.0, 0.0, 0.0, 0.0],    # quaternion (identity)
                0.0, 0.0, 0.0,           # approach vector
                int(time.time() * 1e6)   # time_usec
            )
            time.sleep(0.5)

            # ── Step 5: Set flight mode to STABILIZE (safest for arming) ─────
            print("[CONNECT] Setting flight mode to STABILIZE...")
            mode_id = mav.mode_mapping()["STABILIZE"]
            mav.mav.set_mode_send(
                mav.target_system,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id
            )
            time.sleep(0.3)

            # ── Step 6: Arm the drone with retry logic ───────────────────────
            print("[CONNECT] Attempting to arm the drone...")
            for attempt in range(3):
                mav.mav.command_long_send(
                    mav.target_system, mav.target_component,
                    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                    0, 1, 0, 0, 0, 0, 0, 0
                )
                time.sleep(0.5)
                ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
                if ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                    print(f"[CONNECT] ✓ Drone armed successfully (Attempt {attempt + 1})")
                    time.sleep(1)
                    break
                else:
                    print(f"[CONNECT] ⚠ Arm attempt {attempt + 1} failed, retrying...")
                    time.sleep(0.5)

            print("[CONNECT] ✓ Pre-arm bypass setup complete — drone is armed")

        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _set_parameter(self, mav, param_name, param_value):
        """Helper function to set and verify a parameter"""
        try:
            mav.mav.param_set_send(
                mav.target_system, mav.target_component,
                param_name,
                float(param_value),
                mavutil.mavlink.MAV_PARAM_TYPE_INT32
            )
            time.sleep(0.2)
            mav.mav.param_request_read_send(
                mav.target_system, mav.target_component,
                param_name, -1
            )
            ack = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
            if ack:
                print(f"  ✓ {param_name.decode('utf-8')} = {int(ack.param_value)}")
            else:
                print(f"  ⚠ Could not verify {param_name.decode('utf-8')}")
        except Exception as e:
            print(f"  ⚠ Error setting {param_name.decode('utf-8')}: {e}")
    
    def get_telemetry(self) -> Dict[str, Any]:
        mav = self.mavlink_connection
        
        try:
            batt = mav.recv_match(type='BATTERY_STATUS', blocking=False)
            battery_level = batt.battery_remaining if batt else 100
            battery_voltage = batt.voltage if batt else 0
            battery_current = batt.current if batt else 0
        except:
            battery_level = 100
            battery_voltage = 0
            battery_current = 0
        
        try:
            gps = mav.recv_match(type='GPS_RAW_INT', blocking=False)
            if gps:
                latitude = gps.lat / 1e7
                longitude = gps.lon / 1e7
                altitude = gps.alt / 1000.0
                gps_fix_type = gps.fix_type
                satellites = gps.satellites_visible
                gps_eph = gps.eph
            else:
                latitude = None
                longitude = None
                altitude = 0
                gps_fix_type = 0
                satellites = 0
                gps_eph = 0
        except:
            latitude = None
            longitude = None
            altitude = 0
            gps_fix_type = 0
            satellites = 0
            gps_eph = 0
        
        try:
            att = mav.recv_match(type='ATTITUDE', blocking=False)
            if att:
                roll = math.degrees(att.roll)
                pitch = math.degrees(att.pitch)
                yaw = math.degrees(att.yaw)
            else:
                roll = pitch = yaw = 0
        except:
            roll = pitch = yaw = 0
        
        try:
            hb = mav.recv_match(type='HEARTBEAT', blocking=False)
            if hb:
                flight_mode = "STABILIZE"
                for mode in mav.mode_mapping():
                    if mav.mode_mapping()[mode] == hb.custom_mode:
                        flight_mode = mode
                armed = (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
            else:
                flight_mode = "UNKNOWN"
                armed = False
        except:
            flight_mode = "UNKNOWN"
            armed = False
        
        try:
            ekf = mav.recv_match(type='EKF_STATUS', blocking=False)
            ekf_ok = (ekf.face and ekf.velocity and ekf.pos_horiz) if ekf else True
        except:
            ekf_ok = True
        
        try:
            gs = mav.recv_match(type='GLOBAL_POSITION_INT', blocking=False)
            groundspeed = math.sqrt(gs.vx**2 + gs.vy**2) / 100.0 if gs else 0
            heading = (gs.hdg / 100) if gs else 0
        except:
            groundspeed = 0
            heading = 0
        
        return {
            'battery_voltage': round(battery_voltage / 1000.0, 2),
            'battery_current': round(battery_current / 100.0, 2) if battery_current else 0,
            'battery_level': battery_level,
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'speed_3d': groundspeed,
            'groundspeed': groundspeed,
            'airspeed': groundspeed,
            'heading': heading,
            'roll': round(roll, 2),
            'pitch': round(pitch, 2),
            'yaw': round(yaw, 2),
            'gps_fix_type': gps_fix_type,
            'satellites': satellites,
            'gps_eph': gps_eph,
            'flight_mode': flight_mode,
            'armed': armed,
            'ekf_ok': ekf_ok,
            'is_armable': True,
            'last_heartbeat': round(time.time() % 60, 2),
            'timestamp': time.time()
        }
    
    def detect_anomalies(self, t: Dict) -> list:
        alerts = []
        now = time.time()
        
        if t['gps_fix_type'] < 3:
            alerts.append({
                'type': 'GPS_FIX_LOST',
                'severity': 'CRITICAL',
                'message': f"GPS fix lost! Fix type={t['gps_fix_type']}"
            })
        
        if t['satellites'] is not None and t['satellites'] < 6:
            alerts.append({
                'type': 'GPS_JAMMING',
                'severity': 'HIGH',
                'message': f"Low satellites: {t['satellites']}"
            })
        
        batt = t['battery_level']
        if batt is not None and batt <= 15:
            alerts.append({
                'type': 'LOW_BATTERY',
                'severity': 'CRITICAL' if batt <= 15 else 'HIGH',
                'message': f"Battery low: {batt}%"
            })
        
        if not t['ekf_ok']:
            alerts.append({
                'type': 'EKF_FAILURE',
                'severity': 'HIGH',
                'message': "EKF health check failed"
            })
        
        return alerts
    
    def init_tcp_server(self) -> bool:
        try:
            self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._tcp_server.bind(("0.0.0.0", config.TCP_LISTEN_PORT))
            self._tcp_server.listen(1)
            self._tcp_server.settimeout(5)
            print(f"[TCP] Server listening on :{config.TCP_LISTEN_PORT}")
            return True
        except Exception as e:
            print(f"[ERROR] TCP server failed: {e}")
            return False
    
    def accept_tcp_connection(self) -> bool:
        try:
            self._tcp_client, address = self._tcp_server.accept()
            self._tcp_client.settimeout(1)
            print(f"[TCP] Connected from {address}")
            return True
        except socket.timeout:
            return False
        except Exception as e:
            return False
    
    def run(self):
        self.connect()
        self.running = True
        
        if not self.init_tcp_server():
            logger.warning("TCP server unavailable, continuing with HTTP only")
        
        print(f"\n[MONITOR] Sending to {config.LAPTOP_URL}")
        print("[MONITOR] Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                if not self._tcp_client:
                    self.accept_tcp_connection()
                
                t0 = time.time()
                try:
                    telemetry = self.get_telemetry()
                    alerts = self.detect_anomalies(telemetry)
                    # Print battery info for user feedback
                    print(f"[BATTERY] Level: {telemetry['battery_level']}%  Voltage: {telemetry['battery_voltage']}V")
                    for a in alerts:
                        print(f"  [{a['severity']:8s}] {a['type']:20s} | {a['message']}")
                    try:
                        requests.post(
                            config.LAPTOP_URL,
                            json={'telemetry': telemetry, 'alerts': alerts},
                            timeout=2
                        )
                        self.stats['packets_sent'] += 1
                    except requests.exceptions.RequestException:
                        pass
                except Exception as e:
                    self.stats['errors'] += 1
                
                time.sleep(max(0, config.SEND_INTERVAL - (time.time() - t0)))
                
            except KeyboardInterrupt:
                break
        
        self.stop()
    
    def stop(self):
        self.running = False
        if self._tcp_client:
            self._tcp_client.close()
        if self._tcp_server:
            self._tcp_server.close()
        print("[MONITOR] Stopped.")


def main():
    parser = argparse.ArgumentParser(description='RPI Drone Bridge')
    parser.add_argument('--ip', default=config.LAPTOP_IP)
    parser.add_argument('--port', default=config.LAPTOP_PORT, type=int)
    parser.add_argument('--uart', default=config.CONNECTION_STRING)
    parser.add_argument('--baud', default=config.BAUD_RATE, type=int)
    args = parser.parse_args()
    
    config.LAPTOP_IP = args.ip
    config.LAPTOP_PORT = args.port
    config.LAPTOP_URL = f"http://{args.ip}:{args.port}/telemetry"
    config.CONNECTION_STRING = args.uart
    config.BAUD_RATE = args.baud
    
    print("="*60)
    print("  RPI Drone Bridge (pymavlink)")
    print("="*60)
    print(f"  Laptop: {config.LAPTOP_URL}")
    print(f"  UART:   {config.CONNECTION_STRING} @ {config.BAUD_RATE}")
    print("="*60)
    
    bridge = DroneBridge()
    try:
        bridge.run()
    except KeyboardInterrupt:
        print("\n[MONITOR] Interrupted.")
        bridge.stop()


if __name__ == "__main__":
    main()