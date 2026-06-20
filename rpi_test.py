"""
========================================================
  RPi Onboard Drone Health Monitor (PyMavlink)
  Runs ON the Raspberry Pi connected to PixHawk
========================================================
  REQUIREMENTS:
    pip install pymavlink requests

  WIRING:
    PixHawk TELEM2 → RPi GPIO14(TX) / GPIO15(RX)
    OR via USB cable: PixHawk USB → RPi USB port

  HOW TO RUN:
    1. Edit LAPTOP_IP below
    2. python3 rpi_monitor_pymavlink.py

========================================================
"""

from pymavlink import mavutil
import requests
import time
import math
import sys

# ─── CONFIGURATION ────────────────────────────────────
LAPTOP_IP         = "10.28.115.142"      # ← Change to your laptop's IP
LAPTOP_PORT       = 5000
LAPTOP_URL        = f"http://{LAPTOP_IP}:{LAPTOP_PORT}/telemetry"

CONNECTION_STRING = "/dev/ttyS0"        # ← Change if using USB, e.g., /dev/ttyUSB0
BAUD_RATE         = 57600
SEND_INTERVAL     = 1.0                   # Seconds between each data send

# Attack detection thresholds
GPS_MIN_SATELLITES    = 6
GPS_MIN_FIX_TYPE      = 3      # 3 = 3D fix minimum
GPS_SPOOF_JUMP_M      = 25     # Max realistic position jump in <5s (meters)
BATTERY_DRAIN_RATE    = 5.0    # %/min — above this triggers anomaly alert
HEARTBEAT_TIMEOUT     = 3.0    # Seconds before alerting heartbeat loss
LOW_BATTERY_WARN      = 25     # % — warning threshold
LOW_BATTERY_CRIT      = 15     # % — critical threshold


# ─── UTILITY: GPS distance (Haversine) ────────────────
def gps_distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2   = math.radians(lat1), math.radians(lat2)
    dp       = math.radians(lat2 - lat1)
    dl       = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


# ─── DRONE MONITOR ────────────────────────────────────
class DroneMonitor:

    def __init__(self):
        self.master = None
        self.running = False

        # State for anomaly detection
        self._prev_lat          = None
        self._prev_lon          = None
        self._prev_gps_time     = None
        self._prev_battery_pct  = None
        self._prev_battery_time = None
        self._prev_mode         = None
        self._prev_armed        = None

        self.last_heartbeat_time = time.time()
        
        # Telemetry State
        self.telemetry = {
            "battery_voltage": 0.0,
            "battery_current": 0.0,
            "battery_level": 0,
            "latitude": 0.0,
            "longitude": 0.0,
            "altitude": 0.0,
            "speed_3d": 0.0,
            "groundspeed": 0.0,
            "airspeed": 0.0,
            "heading": 0,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
            "gps_fix_type": 0,
            "satellites": 0,
            "gps_eph": 0.0,
            "flight_mode": "UNKNOWN",
            "armed": False,
            "ekf_ok": True,
            "is_armable": False,
            "last_heartbeat": 0.0,
            "timestamp": 0.0,
        }

    # ── Connect to PixHawk ──────────────────────────
    def connect(self):
        print(f"\n[CONNECT] Connecting to PixHawk on {CONNECTION_STRING} via PyMavlink...")
        try:
            self.master = mavutil.mavlink_connection(CONNECTION_STRING, baud=BAUD_RATE)
            print("[CONNECT] Waiting for heartbeat...")
            self.master.wait_heartbeat()
            print(f"[CONNECT] ✓ Connected! System {self.master.target_system} Component {self.master.target_component}")
            
            # Request all data streams
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_ALL,
                4, # 4 Hz
                1  # start
            )
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            sys.exit(1)

    # ── Read all telemetry from PixHawk ─────────────
    def update_telemetry(self):
        while True:
            msg = self.master.recv_match(blocking=False)
            if not msg:
                break
                
            msg_type = msg.get_type()
            
            if msg_type == 'HEARTBEAT':
                self.last_heartbeat_time = time.time()
                self.telemetry["armed"] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
                self.telemetry["flight_mode"] = mavutil.mode_string_v10(msg)
                self.telemetry["ekf_ok"] = True # Simplified, actual EKF needs SYS_STATUS or EKF_STATUS_REPORT
                
            elif msg_type == 'SYS_STATUS':
                self.telemetry["battery_voltage"] = msg.voltage_battery / 1000.0
                self.telemetry["battery_current"] = msg.current_battery / 100.0
                self.telemetry["battery_level"] = msg.battery_remaining
                # Check sensor health for EKF
                if (msg.onboard_control_sensors_health & mavutil.mavlink.MAV_SYS_STATUS_AHRS) == 0:
                     self.telemetry["ekf_ok"] = False
                
            elif msg_type == 'GLOBAL_POSITION_INT':
                self.telemetry["latitude"] = msg.lat / 1e7
                self.telemetry["longitude"] = msg.lon / 1e7
                self.telemetry["altitude"] = msg.alt / 1000.0
                vx, vy, vz = msg.vx / 100.0, msg.vy / 100.0, msg.vz / 100.0
                self.telemetry["speed_3d"] = round(math.sqrt(vx**2 + vy**2 + vz**2), 2)
                
            elif msg_type == 'VFR_HUD':
                self.telemetry["airspeed"] = msg.airspeed
                self.telemetry["groundspeed"] = msg.groundspeed
                self.telemetry["heading"] = msg.heading
                
            elif msg_type == 'ATTITUDE':
                self.telemetry["roll"] = round(math.degrees(msg.roll), 2)
                self.telemetry["pitch"] = round(math.degrees(msg.pitch), 2)
                self.telemetry["yaw"] = round(math.degrees(msg.yaw), 2)
                
            elif msg_type == 'GPS_RAW_INT':
                self.telemetry["gps_fix_type"] = msg.fix_type
                self.telemetry["satellites"] = msg.satellites_visible
                self.telemetry["gps_eph"] = msg.eph / 100.0
                
        self.telemetry["last_heartbeat"] = round(time.time() - self.last_heartbeat_time, 2)
        self.telemetry["timestamp"] = time.time()
        
        return self.telemetry.copy()

    # ── Run all attack/anomaly checks ───────────────
    def detect_anomalies(self, t):
        """Returns list of {type, severity, message} alert dicts."""
        alerts = []
        now    = time.time()

        # CHECK 1 — GPS Fix Lost
        if t["gps_fix_type"] < GPS_MIN_FIX_TYPE:
            alerts.append({
                "type": "GPS_FIX_LOST", "severity": "CRITICAL",
                "message": f"GPS fix lost! Fix type={t['gps_fix_type']} (need ≥{GPS_MIN_FIX_TYPE})"
            })

        # CHECK 2 — GPS Jamming (too few satellites)
        if t["satellites"] is not None and t["satellites"] < GPS_MIN_SATELLITES:
            alerts.append({
                "type": "GPS_JAMMING", "severity": "HIGH",
                "message": f"Low satellites: {t['satellites']} (min {GPS_MIN_SATELLITES}). Possible jamming."
            })

        # CHECK 3 — GPS Spoofing (sudden position jump)
        lat, lon = t["latitude"], t["longitude"]
        if lat and lon and self._prev_lat and self._prev_gps_time:
            dt   = now - self._prev_gps_time
            dist = gps_distance_meters(self._prev_lat, self._prev_lon, lat, lon)
            max_expected = max(t["groundspeed"] * dt * 1.5, 5)
            if dt < 5 and dist > max(GPS_SPOOF_JUMP_M, max_expected):
                alerts.append({
                    "type": "GPS_SPOOFING", "severity": "CRITICAL",
                    "message": f"Position jumped {dist:.1f}m in {dt:.1f}s — GPS spoof suspected!"
                })
        self._prev_lat, self._prev_lon = lat, lon
        self._prev_gps_time = now

        # CHECK 4 — Battery anomaly / low battery
        batt = t["battery_level"]
        if batt is not None:
            if self._prev_battery_pct is not None and self._prev_battery_time:
                dt_min = (now - self._prev_battery_time) / 60.0
                if dt_min > 0.1:
                    drain = (self._prev_battery_pct - batt) / dt_min
                    if drain > BATTERY_DRAIN_RATE:
                        alerts.append({
                            "type": "BATTERY_ANOMALY", "severity": "HIGH",
                            "message": f"Abnormal drain: {drain:.1f}%/min (limit {BATTERY_DRAIN_RATE})"
                        })
            if batt <= LOW_BATTERY_CRIT:
                alerts.append({
                    "type": "LOW_BATTERY", "severity": "CRITICAL",
                    "message": f"Battery critical: {batt}% — LAND NOW!"
                })
            elif batt <= LOW_BATTERY_WARN:
                alerts.append({
                    "type": "LOW_BATTERY", "severity": "HIGH",
                    "message": f"Battery low: {batt}% — return to home."
                })
            self._prev_battery_pct  = batt
            self._prev_battery_time = now

        # CHECK 5 — Unexpected mode change
        if self._prev_mode and self._prev_mode != t["flight_mode"]:
            sev = "HIGH" if t["flight_mode"] in ("GUIDED","AUTO") else "MEDIUM"
            alerts.append({
                "type": "MODE_CHANGE", "severity": sev,
                "message": f"Mode changed: {self._prev_mode} → {t['flight_mode']}"
            })
        self._prev_mode = t["flight_mode"]

        # CHECK 6 — Unexpected arming
        if self._prev_armed is not None and not self._prev_armed and t["armed"]:
            alerts.append({
                "type": "UNEXPECTED_ARM", "severity": "CRITICAL",
                "message": "Drone armed unexpectedly — possible remote takeover!"
            })
        self._prev_armed = t["armed"]

        # CHECK 7 — Heartbeat loss & EKF
        if t["last_heartbeat"] > HEARTBEAT_TIMEOUT:
            alerts.append({
                "type": "HEARTBEAT_LOSS", "severity": "CRITICAL",
                "message": f"PixHawk heartbeat lost for {t['last_heartbeat']:.1f}s!"
            })
        if not t["ekf_ok"]:
            alerts.append({
                "type": "EKF_FAILURE", "severity": "HIGH",
                "message": "EKF health check failed — navigation unreliable!"
            })

        return alerts

    # ── POST data to laptop ─────────────────────────
    def send_to_laptop(self, telemetry, alerts):
        try:
            requests.post(LAPTOP_URL,
                          json={"telemetry": telemetry, "alerts": alerts},
                          timeout=2)
        except requests.exceptions.ConnectionError:
            print(f"[WARN] Laptop unreachable at {LAPTOP_URL}")
        except Exception as e:
            print(f"[WARN] Send error: {e}")

    # ── Main monitoring loop ─────────────────────────
    def run(self):
        self.connect()
        self.running = True
        print(f"\n[MONITOR] Sending data to {LAPTOP_URL} every {SEND_INTERVAL}s")
        print("[MONITOR] Press Ctrl+C to stop\n")

        while self.running:
            t0 = time.time()
            try:
                telemetry = self.update_telemetry()
                alerts    = self.detect_anomalies(telemetry)
                
                # Terminal output on RPi
                print(f"[{time.strftime('%H:%M:%S')}] Mode: {telemetry['flight_mode']} | Armed: {telemetry['armed']} | Bat: {telemetry['battery_level']}% | Sats: {telemetry['satellites']}")
                for a in alerts:
                    print(f"  [{a['severity']:8s}] {a['type']:20s} | {a['message']}")
                    
                self.send_to_laptop(telemetry, alerts)
            except Exception as e:
                print(f"[ERROR] {e}")
            time.sleep(max(0, SEND_INTERVAL - (time.time() - t0)))

    def stop(self):
        self.running = False
        if self.master:
            self.master.close()
        print("[MONITOR] Stopped.")


# ─── ENTRY POINT ──────────────────────────────────────
if __name__ == "__main__":
    m = DroneMonitor()
    try:
        m.run()
    except KeyboardInterrupt:
        print("\n[MONITOR] Interrupted.")
        m.stop()
