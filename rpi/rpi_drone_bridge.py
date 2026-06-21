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


# Probed in order. ttyAMA0 (GPIO UART) is first because that is where the
# PixHawk telemetry is wired on this airframe; the CP210x USB bridge enumerates
# as ttyUSB0 but carries no MAVLink, so detection must verify by heartbeat.
_CANDIDATE_PORTS = [
    "/dev/ttyAMA0",   # RPi GPIO UART (GPIO 14/15) — PixHawk TELEM
    "/dev/serial0",   # usually a symlink to ttyAMA0
    "/dev/ttyUSB0",   # USB-serial bridge (CP210x/FTDI)
    "/dev/ttyUSB1",
    "/dev/ttyACM0",   # PixHawk native USB CDC
    "/dev/ttyACM1",
    "/dev/ttyS0",     # mini-UART
]


def _has_heartbeat(port: str, baud: int, timeout: float = 4.0) -> bool:
    """Open a port briefly and return True only if a MAVLink HEARTBEAT arrives."""
    try:
        m = mavutil.mavlink_connection(port, baud=baud)
    except Exception as e:
        print(f"[DETECT] {port} @ {baud}: open failed ({e})")
        return False
    try:
        hb = m.recv_match(type='HEARTBEAT', blocking=True, timeout=timeout)
        if hb:
            print(f"[DETECT] {port} @ {baud}: HEARTBEAT from system {m.target_system}")
            return True
        return False
    finally:
        m.close()


def detect_serial_port(baud: int) -> str:
    """Find the port that actually speaks MAVLink, verified by heartbeat."""
    candidates = [p for p in _CANDIDATE_PORTS
                  if os.path.exists(p) and os.access(p, os.R_OK | os.W_OK)]
    if not candidates:
        # Nothing openable — report what exists so the user knows why
        existing = [p for p in _CANDIDATE_PORTS if os.path.exists(p)]
        if existing:
            raise RuntimeError(
                f"No accessible serial port. Found {existing} but no R/W permission. "
                f"Fix: sudo usermod -aG dialout $USER  (then re-login)"
            )
        raise RuntimeError("No serial port found. Is the PixHawk connected/powered?")

    print(f"[DETECT] Probing for PixHawk on: {', '.join(candidates)}")
    for port in candidates:
        if _has_heartbeat(port, baud):
            return port

    # No heartbeat anywhere — fall back to the first candidate and let connect()
    # surface the real error (e.g. PixHawk unpowered).
    print(f"[DETECT] No heartbeat on any port; falling back to {candidates[0]}")
    return candidates[0]


class Config:
    LAPTOP_IP = "192.168.1.100"
    LAPTOP_PORT = 5000
    LAPTOP_URL = f"http://{LAPTOP_IP}:{LAPTOP_PORT}/telemetry"
    CONNECTION_STRING = None   # auto-detected at startup
    BAUD_RATE = 57600
    SEND_INTERVAL = 1.0
    TCP_LISTEN_PORT = 5760
    BENCH_MODE = False  # True = bypass GPS/arming for indoor bench testing


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
        self._gps_ever_fixed = False
        
        self._tcp_server = None
        self._tcp_client = None
        self._client_lock = threading.Lock()
        self._cmd_buffer = b""

        self._msg_cache = {}
        self._msg_lock = threading.Lock()

        self._telemetry_data = {}
        self._alerts = []

        self.stats = {'packets_sent': 0, 'packets_recv': 0, 'errors': 0}
    
    def _fix_port_permission(self, port: str) -> bool:
        import subprocess
        print(f"[PERM] Permission denied on {port} — attempting sudo chmod ...")
        result = subprocess.run(
            ["sudo", "chmod", "a+rw", port],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"[PERM] Fixed permissions on {port}")
            return True
        print(f"[PERM] Could not fix automatically: {result.stderr.strip()}")
        print(f"[PERM] Run once manually:  sudo usermod -aG dialout $USER  then log out/in")
        return False

    def connect(self):
        print(f"\n[CONNECT] Connecting to PixHawk on {config.CONNECTION_STRING}...")
        try:
            # Auto-fix permission if needed before opening
            if not os.access(config.CONNECTION_STRING, os.R_OK | os.W_OK):
                self._fix_port_permission(config.CONNECTION_STRING)

            self.mavlink_connection = mavutil.mavlink_connection(
                config.CONNECTION_STRING,
                baud=config.BAUD_RATE,
                planner_format=True
            )
            msg = self.mavlink_connection.recv_match(type='HEARTBEAT', blocking=True, timeout=30)
            if not msg:
                print("[ERROR] No HEARTBEAT received")
                sys.exit(1)

            print(f"[CONNECT] Connected! System ID: {self.mavlink_connection.target_system}")
            mav = self.mavlink_connection

            mav.mav.request_data_stream_send(
                mav.target_system, mav.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1
            )

            t = threading.Thread(target=self._recv_loop, daemon=True)
            t.start()

            if config.BENCH_MODE:
                # Indoor bench testing — bypass GPS/EKF/arming checks so the
                # PixHawk can arm without a GPS fix or battery.
                print("[CONNECT] BENCH MODE: bypassing pre-arm checks...")
                self._set_parameter(mav, b'ARMING_CHECK', 0)
                time.sleep(0.3)
                self._set_parameter(mav, b'EKF3_CHECK_SCALE', 0)
                self._set_parameter(mav, b'EKF2_CHECK_SCALE', 0)
                time.sleep(0.3)

                # Inject fake GPS origin so EKF can initialise indoors
                lat_int, lon_int, alt_mm = 0, 0, 0
                mav.mav.set_gps_global_origin_send(mav.target_system, lat_int, lon_int, alt_mm)
                mav.mav.set_home_position_send(
                    mav.target_system, lat_int, lon_int, alt_mm,
                    0.0, 0.0, 0.0, [1.0, 0.0, 0.0, 0.0],
                    0.0, 0.0, 0.0, int(time.time() * 1e6)
                )
                time.sleep(0.5)

                mode_id = mav.mode_mapping()["STABILIZE"]
                mav.mav.set_mode_send(
                    mav.target_system,
                    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                    mode_id
                )
                time.sleep(0.3)

                for attempt in range(3):
                    mav.mav.command_long_send(
                        mav.target_system, mav.target_component,
                        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                        0, 1, 0, 0, 0, 0, 0, 0
                    )
                    time.sleep(0.5)
                    ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
                    if ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                        print(f"[CONNECT] Armed (bench mode, attempt {attempt + 1})")
                        break
                    else:
                        print(f"[CONNECT] Arm attempt {attempt + 1} failed, retrying...")
                        time.sleep(0.5)
            else:
                # Normal flight mode — respect Mission Planner parameter config.
                # GPS lock, battery, and EKF must be healthy before arming.
                print("[CONNECT] Normal mode — using Mission Planner parameters.")
                print("[CONNECT] Waiting for EKF to initialise (GPS lock needed outdoors)...")

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

    def _recv_loop(self):
        """Background thread — reads every MAVLink message and stores latest by type."""
        mav = self.mavlink_connection
        while self.running or self.mavlink_connection:
            try:
                msg = mav.recv_match(blocking=True, timeout=1)
                if msg is None:
                    continue
                with self._msg_lock:
                    self._msg_cache[msg.get_type()] = msg
            except Exception:
                break

    def _get_msg(self, msg_type):
        with self._msg_lock:
            return self._msg_cache.get(msg_type)

    def get_telemetry(self) -> Dict[str, Any]:
        sys_status = self._get_msg('SYS_STATUS')
        batt       = self._get_msg('BATTERY_STATUS')
        gps        = self._get_msg('GPS_RAW_INT')
        att        = self._get_msg('ATTITUDE')
        hb         = self._get_msg('HEARTBEAT')
        ekf        = self._get_msg('EKF_STATUS_REPORT')
        gs         = self._get_msg('GLOBAL_POSITION_INT')

        # Battery
        try:
            if sys_status and sys_status.voltage_battery > 0:
                battery_voltage = sys_status.voltage_battery
                battery_current = sys_status.current_battery if sys_status.current_battery != -1 else 0
            elif batt:
                battery_voltage = batt.voltages[0] if batt.voltages[0] != 65535 else 0
                battery_current = batt.current_battery if batt.current_battery != -1 else 0
            else:
                battery_voltage = 0
                battery_current = 0
            if batt and batt.battery_remaining > 0:
                battery_level = batt.battery_remaining
            elif sys_status and sys_status.battery_remaining > 0:
                battery_level = sys_status.battery_remaining
            else:
                battery_level = 100
        except:
            battery_voltage = 0
            battery_current = 0
            battery_level = 100

        # GPS
        try:
            if gps:
                latitude      = gps.lat / 1e7
                longitude     = gps.lon / 1e7
                altitude      = gps.alt / 1000.0
                gps_fix_type  = gps.fix_type
                satellites    = gps.satellites_visible
                gps_eph       = gps.eph
            else:
                latitude = longitude = None
                altitude = gps_fix_type = satellites = gps_eph = 0
        except:
            latitude = longitude = None
            altitude = gps_fix_type = satellites = gps_eph = 0

        # Attitude
        try:
            if att:
                roll  = math.degrees(att.roll)
                pitch = math.degrees(att.pitch)
                yaw   = math.degrees(att.yaw)
            else:
                roll = pitch = yaw = 0
        except:
            roll = pitch = yaw = 0

        # Flight mode + armed
        try:
            if hb:
                flight_mode = "STABILIZE"
                for mode in self.mavlink_connection.mode_mapping():
                    if self.mavlink_connection.mode_mapping()[mode] == hb.custom_mode:
                        flight_mode = mode
                armed = (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
            else:
                flight_mode = "UNKNOWN"
                armed = False
        except:
            flight_mode = "UNKNOWN"
            armed = False

        # EKF
        try:
            ekf_ok = (ekf.flags & 0x1FF) == 0x1FF if ekf else True
        except:
            ekf_ok = True

        # Speed + heading
        try:
            groundspeed = math.sqrt(gs.vx**2 + gs.vy**2) / 100.0 if gs else 0
            heading = (gs.hdg / 100) if gs else 0
        except:
            groundspeed = heading = 0
        
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

        fix = t['gps_fix_type']
        sats = t['satellites'] or 0

        if fix >= 3:
            self._gps_ever_fixed = True

        if self._gps_ever_fixed and fix < 3:
            # Only alert if we HAD a fix and then lost it (real anomaly)
            alerts.append({
                'type': 'GPS_FIX_LOST',
                'severity': 'CRITICAL',
                'message': f"GPS fix lost! Fix type={fix}"
            })
        elif not self._gps_ever_fixed:
            # Still acquiring — informational only, not an alert
            fix_labels = {0: 'NO_GPS', 1: 'NO_FIX', 2: '2D_FIX'}
            print(f"[GPS] Acquiring... ({fix_labels.get(fix, fix)}, {sats} sats)")

        if self._gps_ever_fixed and sats < 6:
            alerts.append({
                'type': 'GPS_JAMMING',
                'severity': 'HIGH',
                'message': f"Low satellites: {sats}"
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
            # Short timeout: each run-loop pass polls for a command without
            # blocking long enough to throttle the telemetry push rate.
            self._tcp_client.settimeout(0.05)
            self._cmd_buffer = b""
            print(f"[TCP] Connected from {address}")
            return True
        except socket.timeout:
            return False
        except Exception as e:
            return False
    
    def _poll_commands(self):
        """Non-blocking read of newline-delimited JSON commands from the GCS."""
        if not self._tcp_client:
            return
        try:
            data = self._tcp_client.recv(4096)
            if data == b"":
                # Peer closed the connection.
                print("[TCP] GCS disconnected")
                try:
                    self._tcp_client.close()
                except OSError:
                    pass
                self._tcp_client = None
                self._cmd_buffer = b""
                return
            self._cmd_buffer += data
        except socket.timeout:
            return
        except (ConnectionResetError, OSError):
            self._tcp_client = None
            self._cmd_buffer = b""
            return

        # The GCS frames each command as JSON + b'\n'.
        while b"\n" in self._cmd_buffer:
            line, self._cmd_buffer = self._cmd_buffer.split(b"\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                print(f"[TCP] Ignoring malformed command: {line!r}")
                continue
            cmd = msg.get("command", "")
            if cmd:
                self.handle_command(cmd)

    def handle_command(self, command: str):
        """Execute a GCS command on the PixHawk via MAVLink."""
        mav = self.mavlink_connection
        if not mav:
            print(f"[CMD] '{command}' ignored — no MAVLink connection")
            return

        command = (command or "").strip().lower()
        print(f"[CMD] Received: {command}")

        # ArduPilot custom flight modes (set via SET_MODE custom mode id).
        mode_map = {
            "land": "LAND", "rtl": "RTL", "loiter": "LOITER",
            "stabilize": "STABILIZE", "guided": "GUIDED",
            "alt_hold": "ALT_HOLD", "althold": "ALT_HOLD",
            "auto": "AUTO", "poshold": "POSHOLD",
        }

        try:
            if command in ("arm", "disarm"):
                arm_val = 1 if command == "arm" else 0
                mav.mav.command_long_send(
                    mav.target_system, mav.target_component,
                    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                    0, arm_val, 0, 0, 0, 0, 0, 0
                )
            elif command == "takeoff":
                mav.mav.command_long_send(
                    mav.target_system, mav.target_component,
                    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                    0, 0, 0, 0, 0, 0, 0, 10  # 10 m target altitude
                )
            elif command in mode_map:
                mode_name = mode_map[command]
                mapping = mav.mode_mapping() or {}
                if mode_name not in mapping:
                    print(f"[CMD] Mode {mode_name} not supported by this airframe")
                    return
                mav.mav.set_mode_send(
                    mav.target_system,
                    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                    mapping[mode_name]
                )
            else:
                print(f"[CMD] Unknown command: {command}")
                return
        except Exception as e:
            print(f"[CMD] Error executing '{command}': {e}")
            return

        # Read the ACK from the cache populated by the _recv_loop thread,
        # rather than calling recv_match here (which would race that thread).
        time.sleep(0.3)
        ack = self._get_msg('COMMAND_ACK')
        if ack is not None:
            if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print(f"[CMD] '{command}' ACCEPTED by PixHawk")
            else:
                result_names = {
                    1: "TEMPORARILY_REJECTED", 2: "DENIED",
                    3: "UNSUPPORTED", 4: "FAILED",
                    5: "IN_PROGRESS",
                }
                reason = result_names.get(ack.result, f"result={ack.result}")
                print(f"[CMD] '{command}' REJECTED by PixHawk: {reason} "
                      f"(pre-arm check? try --bench indoors or wait for GPS lock)")

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

                # Read & execute any commands the GCS sent over TCP.
                self._poll_commands()

                t0 = time.time()
                try:
                    telemetry = self.get_telemetry()
                    alerts = self.detect_anomalies(telemetry)
                    fix_labels = {0:'NO_GPS',1:'NO_FIX',2:'2D_FIX',3:'3D_FIX',4:'DGPS',5:'RTK_FLOAT',6:'RTK_FIXED'}
                    fix_str = fix_labels.get(telemetry['gps_fix_type'], str(telemetry['gps_fix_type']))
                    lat = f"{telemetry['latitude']:.6f}" if telemetry['latitude'] else "---"
                    lon = f"{telemetry['longitude']:.6f}" if telemetry['longitude'] else "---"
                    print(f"[BATT] {telemetry['battery_voltage']}V {telemetry['battery_level']}%  "
                          f"[GPS] {fix_str} sats={telemetry['satellites']} lat={lat} lon={lon}")
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
    parser.add_argument('--uart', default=None, help='Serial port (auto-detected if omitted)')
    parser.add_argument('--baud', default=config.BAUD_RATE, type=int)
    parser.add_argument('--bench', action='store_true',
                        help='Bench/indoor mode: bypass GPS, EKF and arming checks')
    args = parser.parse_args()

    config.LAPTOP_IP = args.ip
    config.LAPTOP_PORT = args.port
    config.LAPTOP_URL = f"http://{args.ip}:{args.port}/telemetry"
    config.BAUD_RATE = args.baud
    config.CONNECTION_STRING = args.uart if args.uart else detect_serial_port(args.baud)
    config.BENCH_MODE = args.bench
    
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