#!/usr/bin/env python3
"""
================================================================
  RPI Unified Drone Health Monitor + Voice Bridge
  Runs ON the Raspberry Pi connected to PixHawk
================================================================
  FEATURES:
    - Connects to PixHawk via UART/USB
    - Monitors drone health & detects anomalies
    - Sends telemetry to laptop
    - Bridges voice commands to drone
    
  WIRING:
    - UART: PixHawk TELEM2 → RPi GPIO14(TX) / GPIO15(RX)
    - USB: PixHawk USB → RPi USB port
    
  HOW TO RUN:
    - Edit LAPTOP_IP below (find with `ipconfig` on Windows)
    - Run: sudo python3 rpi_drone_bridge.py
    
  CONNECTION STRINGS:
    - UART (GPIO):  "/dev/ttyAMA0"   baud=57600
    - USB cable:  "/dev/ttyUSB0"   baud=57600
    - SITL test:  "tcp:127.0.0.1:5760"
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
from typing import Optional, Tuple, Dict, Any

try:
    from dronekit import connect, VehicleMode, Command
    from pymavlink import mavutil
except ImportError:
    print("ERROR: dronekit not installed. Run: pip install dronekit pymavlink")
    sys.exit(1)

import dronekit

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== CONFIGURATION ====================
class Config:
    LAPTOP_IP = "192.168.1.100"
    LAPTOP_PORT = 5000
    LAPTOP_URL = f"http://{LAPTOP_IP}:{LAPTOP_PORT}/telemetry"
    
    CONNECTION_STRING = "/dev/ttyAMA0"
    BAUD_RATE = 57600
    SEND_INTERVAL = 1.0
    
    TCP_LISTEN_HOST = "0.0.0.0"
    TCP_LISTEN_PORT = 5760
    
    GPS_MIN_SATELLITES = 6
    GPS_MIN_FIX_TYPE = 3
    GPS_SPOOF_JUMP_M = 25
    BATTERY_DRAIN_RATE = 5.0
    HEARTBEAT_TIMEOUT = 3.0
    LOW_BATTERY_WARN = 25
    LOW_BATTERY_CRIT = 15


config = Config()


# ==================== GPS UTILITY ====================
def gps_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates using Haversine formula"""
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


# ==================== DRONE MONITOR ====================
class DroneMonitor:
    def __init__(self):
        self.vehicle = None
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
        
        self.stats = {
            'packets_sent': 0,
            'packets_recv': 0,
            'errors': 0
        }
    
    def connect(self):
        print(f"\n[CONNECT] Connecting to PixHawk on {config.CONNECTION_STRING}...")
        try:
            self.vehicle = connect(
                config.CONNECTION_STRING,
                baud=config.BAUD_RATE,
                wait_ready=False,
                timeout=60
            )
            
            def suppress_heartbeat_error(self, name, msg):
                pass
            
            self.vehicle.add_message_listener('HEARTBEAT', suppress_heartbeat_error)
            
            time.sleep(2)
            
            try:
                self._prev_mode = self.vehicle.mode.name
            except:
                self._prev_mode = "UNKNOWN"
            
            try:
                self._prev_armed = self.vehicle.armed
            except:
                self._prev_armed = False
                
            print(f"[CONNECT] ✓ Connected! Mode={self._prev_mode} Armed={self._prev_armed}")
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            sys.exit(1)
    
    def get_telemetry(self) -> Dict[str, Any]:
        v = self.vehicle
        
        try:
            loc = v.location.global_relative_frame
        except:
            loc = type('obj', (object,), {'lat': None, 'lon': None, 'alt': 0})()
        
        try:
            att = v.attitude
        except:
            att = type('obj', (object,), {'roll': 0, 'pitch': 0, 'yaw': 0})()
        
        try:
            vel = v.velocity or [0, 0, 0]
            spd = math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
        except:
            spd = 0
            vel = [0, 0, 0]
        
        try:
            battery_level = v.battery.level
        except:
            battery_level = 0
        
        try:
            groundspeed = v.groundspeed
        except:
            groundspeed = 0
            
        try:
            airspeed = v.airspeed
        except:
            airspeed = 0
            
        try:
            heading = v.heading
        except:
            heading = 0
            
        try:
            gps_fix_type = v.gps_0.fix_type
        except:
            gps_fix_type = 0
            
        try:
            satellites = v.gps_0.satellites_visible
        except:
            satellites = 0
            
        try:
            gps_eph = v.gps_0.eph
        except:
            gps_eph = 0
            
        try:
            flight_mode = v.mode.name
        except:
            flight_mode = "UNKNOWN"
            
        try:
            armed = v.armed
        except:
            armed = False
            
        try:
            ekf_ok = v.ekf_ok
        except:
            ekf_ok = True
            
        try:
            is_armable = v.is_armable
        except:
            is_armable = False
            
        try:
            last_heartbeat = v.last_heartbeat
        except:
            last_heartbeat = 0
        
        return {
            'battery_voltage': 0,
            'battery_current': 0,
            'battery_level': battery_level,
            
            'latitude': loc.lat,
            'longitude': loc.lon,
            'altitude': round(loc.alt or 0, 2),
            
            'speed_3d': round(spd, 2),
            'groundspeed': round(groundspeed, 2),
            'airspeed': round(airspeed, 2),
            'heading': heading,
            
            'roll': round(math.degrees(att.roll), 2),
            'pitch': round(math.degrees(att.pitch), 2),
            'yaw': round(math.degrees(att.yaw), 2),
            
            'gps_fix_type': gps_fix_type,
            'satellites': satellites,
            'gps_eph': gps_eph,
            
            'flight_mode': flight_mode,
            'armed': armed,
            'ekf_ok': ekf_ok,
            'is_armable': is_armable,
            'last_heartbeat': round(last_heartbeat, 2),
            
            'timestamp': time.time()
        }
    
    def detect_anomalies(self, t: Dict) -> list:
        alerts = []
        now = time.time()
        
        if t['gps_fix_type'] < config.GPS_MIN_FIX_TYPE:
            alerts.append({
                'type': 'GPS_FIX_LOST',
                'severity': 'CRITICAL',
                'message': f"GPS fix lost! Fix type={t['gps_fix_type']}"
            })
        
        if t['satellites'] is not None and t['satellites'] < config.GPS_MIN_SATELLITES:
            alerts.append({
                'type': 'GPS_JAMMING',
                'severity': 'HIGH',
                'message': f"Low satellites: {t['satellites']}"
            })
        
        lat, lon = t['latitude'], t['longitude']
        if lat and lon and self._prev_lat and self._prev_gps_time:
            dt = now - self._prev_gps_time
            dist = gps_distance_meters(self._prev_lat, self._prev_lon, lat, lon)
            max_expected = max(t['groundspeed'] * dt * 1.5, 5)
            if dt < 5 and dist > max(config.GPS_SPOOF_JUMP_M, max_expected):
                alerts.append({
                    'type': 'GPS_SPOOFING',
                    'severity': 'CRITICAL',
                    'message': f"Position jumped {dist:.1f}m"
                })
        self._prev_lat, self._prev_lon = lat, lon
        self._prev_gps_time = now
        
        batt = t['battery_level']
        if batt is not None:
            if self._prev_battery_pct is not None and self._prev_battery_time:
                dt_min = (now - self._prev_battery_time) / 60.0
                if dt_min > 0.1:
                    drain = (self._prev_battery_pct - batt) / dt_min
                    if drain > config.BATTERY_DRAIN_RATE:
                        alerts.append({
                            'type': 'BATTERY_ANOMALY',
                            'severity': 'HIGH',
                            'message': f"Abnormal drain: {drain:.1f}%/min"
                        })
            if batt <= config.LOW_BATTERY_CRIT:
                alerts.append({
                    'type': 'LOW_BATTERY',
                    'severity': 'CRITICAL',
                    'message': f"Battery critical: {batt}%"
                })
            elif batt <= config.LOW_BATTERY_WARN:
                alerts.append({
                    'type': 'LOW_BATTERY',
                    'severity': 'HIGH',
                    'message': f"Battery low: {batt}%"
                })
            self._prev_battery_pct = batt
            self._prev_battery_time = now
        
        if self._prev_mode and self._prev_mode != t['flight_mode']:
            alerts.append({
                'type': 'MODE_CHANGE',
                'severity': 'HIGH',
                'message': f"Mode: {self._prev_mode} → {t['flight_mode']}"
            })
        self._prev_mode = t['flight_mode']
        
        if self._prev_armed is not None and not self._prev_armed and t['armed']:
            alerts.append({
                'type': 'UNEXPECTED_ARM',
                'severity': 'CRITICAL',
                'message': "Drone armed unexpectedly!"
            })
        self._prev_armed = t['armed']
        
        if t['last_heartbeat'] > config.HEARTBEAT_TIMEOUT:
            alerts.append({
                'type': 'HEARTBEAT_LOSS',
                'severity': 'CRITICAL',
                'message': f"Heartbeat lost: {t['last_heartbeat']}s"
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
            self._tcp_server.bind((config.TCP_LISTEN_HOST, config.TCP_LISTEN_PORT))
            self._tcp_server.listen(1)
            self._tcp_server.settimeout(5)
            print(f"[TCP] Server listening on {config.TCP_LISTEN_HOST}:{config.TCP_LISTEN_PORT}")
            return True
        except Exception as e:
            print(f"[ERROR] TCP server failed: {e}")
            return False
    
    def accept_tcp_connection(self) -> bool:
        try:
            logger.info("Waiting for laptop connection...")
            self._tcp_client, address = self._tcp_server.accept()
            self._tcp_client.settimeout(1)
            logger.info(f"[TCP] Connected from {address}")
            return True
        except socket.timeout:
            return False
        except Exception as e:
            logger.error(f"TCP accept error: {e}")
            return False
    
    def process_tcp_commands(self):
        if not self._tcp_client:
            return None
        
        try:
            data = self._tcp_client.recv(4096)
            if data:
                self.stats['packets_recv'] += 1
                return data
        except socket.timeout:
            pass
        except Exception as e:
            logger.error(f"TCP recv error: {e}")
            self._tcp_client = None
        
        return None
    
    def send_tcp_data(self, data: bytes) -> bool:
        if not self._tcp_client:
            return False
        
        try:
            with self._client_lock:
                self._tcp_client.sendall(data)
                self.stats['packets_sent'] += 1
            return True
        except Exception as e:
            logger.error(f"TCP send error: {e}")
            self._tcp_client = None
            return False
    
    def send_to_laptop(self, telemetry: Dict, alerts: list):
        try:
            requests.post(
                config.LAPTOP_URL,
                json={'telemetry': telemetry, 'alerts': alerts},
                timeout=2
            )
            self.stats['packets_sent'] += 1
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.stats['errors'] += 1
    
    def process_voice_command(self, command: str) -> Tuple[bool, str]:
        if not self.vehicle:
            return False, "Vehicle not connected"
        
        try:
            cmd = command.lower().strip()
            
            if cmd in ['arm', 'arm vehicle']:
                self.vehicle.armed = True
                return True, "Arm command sent"
            
            elif cmd in ['disarm', ' disarm']:
                self.vehicle.armed = False
                return True, "Disarm command sent"
            
            elif cmd in ['takeoff', 'take off']:
                altitude = 10
                cmds = self.vehicle.commands
                cmds.download()
                cmds.wait_ready()
                
                takeoff_cmd = Command(
                    0, 0, 0,
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                    0, 0, 0, 0, 0, 0,
                    0, 0, altitude
                )
                cmds.add(takeoff_cmd)
                cmds.upload()
                return True, f"Takeoff to {altitude}m"
            
            elif cmd in ['rtl', 'return', 'return home']:
                self.vehicle.mode = VehicleMode('RTL')
                return True, "RTL command sent"
            
            elif cmd in ['loiter', 'hover']:
                self.vehicle.mode = VehicleMode('LOITER')
                return True, "Loiter mode set"
            
            elif cmd in ['stabilize']:
                self.vehicle.mode = VehicleMode('STABILIZE')
                return True, "Stabilize mode set"
            
            elif cmd in ['althold', 'alt hold']:
                self.vehicle.mode = VehicleMode('ALT_HOLD')
                return True, "Alt Hold mode set"
            
            elif cmd in ['land']:
                self.vehicle.mode = VehicleMode('LAND')
                return True, "Land mode set"
            
            elif cmd in ['guided']:
                self.vehicle.mode = VehicleMode('GUIDED')
                return True, "Guided mode set"
            
            elif cmd in ['auto']:
                self.vehicle.mode = VehicleMode('AUTO')
                return True, "Auto mode set"
            
            elif cmd in ['hold', 'poshold', 'position hold']:
                self.vehicle.mode = VehicleMode('POSHOLD')
                return True, "Position Hold mode set"
            
            else:
                return False, f"Unknown command: {command}"
                
        except Exception as e:
            logger.error(f"Command error: {e}")
            return False, str(e)
    
    def run(self):
        self.connect()
        self.running = True
        
        if not self.init_tcp_server():
            logger.warning("TCP server unavailable, continuing with HTTP only")
        
        print(f"\n[MONITOR] Sending to {config.LAPTOP_URL}")
        print(f"[MONITOR] TCP bridge on :{config.TCP_LISTEN_PORT}")
        print("[MONITOR] Press Ctrl+C to stop\n")
        
        last_heartbeat = time.time()
        
        while self.running:
            try:
                if not self._tcp_client:
                    self.accept_tcp_connection()
                
                t0 = time.time()
                try:
                    telemetry = self.get_telemetry()
                    alerts = self.detect_anomalies(telemetry)
                    
                    for a in alerts:
                        print(f"  [{a['severity']:8s}] {a['type']:20s} | {a['message']}")
                    
                    self.send_to_laptop(telemetry, alerts)
                    
                    if self._tcp_client:
                        self.send_tcp_data(json.dumps({
                            'telemetry': telemetry,
                            'alerts': alerts
                        }).encode())
                    
                    command_data = self.process_tcp_commands()
                    if command_data:
                        try:
                            cmd_json = json.loads(command_data.decode())
                            if 'command' in cmd_json:
                                self.process_voice_command(cmd_json['command'])
                        except:
                            pass
                            
                except Exception as e:
                    logger.error(f"Error: {e}")
                    self.stats['errors'] += 1
                
                sleep_time = max(0, config.SEND_INTERVAL - (time.time() - t0))
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print("\n[MONITOR] Interrupted.")
                break
        
        self.stop()
    
    def stop(self):
        self.running = False
        if self._tcp_client:
            self._tcp_client.close()
        if self._tcp_server:
            self._tcp_server.close()
        if self.vehicle:
            self.vehicle.close()
        print("[MONITOR] Stopped.")


# ==================== ENTRY POINT ====================
def main():
    parser = argparse.ArgumentParser(description='RPI Drone Monitor + Voice Bridge')
    parser.add_argument('--ip', default=config.LAPTOP_IP, help='Laptop IP address')
    parser.add_argument('--port', default=config.LAPTOP_PORT, type=int, help='Laptop port')
    parser.add_argument('--uart', default=config.CONNECTION_STRING, help='UART device')
    parser.add_argument('--baud', default=config.BAUD_RATE, type=int, help='Baud rate')
    parser.add_argument('--tcp-port', default=config.TCP_LISTEN_PORT, type=int, help='TCP listen port')
    args = parser.parse_args()
    
    config.LAPTOP_IP = args.ip
    config.LAPTOP_PORT = args.port
    config.CONNECTION_STRING = args.uart
    config.BAUD_RATE = args.baud
    config.TCP_LISTEN_PORT = args.tcp_port
    config.LAPTOP_URL = f"http://{args.ip}:{args.port}/telemetry"
    
    print("="*60)
    print("  RPI Drone Health Monitor + Voice Bridge")
    print("="*60)
    print(f"  Laptop IP:   {config.LAPTOP_IP}")
    print(f"  Laptop URL:  {config.LAPTOP_URL}")
    print(f"  UART:       {config.CONNECTION_STRING} @ {config.BAUD_RATE}")
    print(f"  TCP:        :{config.TCP_LISTEN_PORT}")
    print("="*60)
    
    m = DroneMonitor()
    try:
        m.run()
    except KeyboardInterrupt:
        print("\n[MONITOR] Interrupted.")
        m.stop()


if __name__ == "__main__":
    main()