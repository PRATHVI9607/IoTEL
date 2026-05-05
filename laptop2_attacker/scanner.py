#!/usr/bin/env python3
"""
================================================================
  Network Scanner — Phase 1: Discover Drone & GCS on the network
  Runs on LAPTOP B (Attacker)
================================================================
  Scans the local subnet for:
    - RPI drone bridge (TCP port 5760)
    - Laptop A GCS web server (HTTP port 5000)
  
  USAGE:
    python scanner.py
    python scanner.py --subnet 192.168.1.0/24
    python scanner.py --subnet 10.193.181.0/24
================================================================
"""

import socket
import ipaddress
import argparse
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    # Fallback: no colors
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""


# ==================== CONFIGURATION ====================
DRONE_PORT = 5760       # RPI drone bridge TCP port
GCS_PORT = 5000         # Laptop A GCS HTTP port
SCAN_TIMEOUT = 1.0      # Timeout per connection attempt (seconds)
MAX_THREADS = 50        # Parallel scan threads


def get_local_ip() -> str:
    """Get the local IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def guess_subnet(local_ip: str) -> str:
    """Guess the /24 subnet from local IP."""
    parts = local_ip.split(".")
    return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"


def scan_port(ip: str, port: int, timeout: float = SCAN_TIMEOUT) -> bool:
    """Check if a specific port is open on the given IP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def scan_host(ip: str) -> dict:
    """Scan a single host for drone and GCS ports."""
    result = {"ip": ip, "drone_port": False, "gcs_port": False}
    result["drone_port"] = scan_port(ip, DRONE_PORT)
    result["gcs_port"] = scan_port(ip, GCS_PORT)
    return result


def verify_drone_connection(ip: str, port: int = DRONE_PORT) -> dict:
    """
    Attempt to connect to the drone TCP bridge and read telemetry data
    to verify it's actually the drone, not just an open port.
    """
    info = {"verified": False, "data": None}
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((ip, port))
        
        # Try to read data (the RPI bridge sends JSON telemetry)
        data = sock.recv(4096)
        if data:
            try:
                parsed = json.loads(data.decode())
                if "telemetry" in parsed:
                    info["verified"] = True
                    info["data"] = parsed["telemetry"]
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        sock.close()
    except Exception:
        pass
    return info


def verify_gcs_connection(ip: str, port: int = GCS_PORT) -> dict:
    """
    Attempt to connect to the GCS HTTP server and check if the
    /api/status endpoint responds.
    """
    info = {"verified": False, "data": None}
    try:
        import requests
        resp = requests.get(f"http://{ip}:{port}/api/status", timeout=3)
        if resp.status_code == 200:
            info["verified"] = True
            info["data"] = resp.json()
    except Exception:
        pass
    return info


def print_banner():
    """Print the scanner banner."""
    print(f"""
{Fore.RED}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════╗
║           🔍  DRONE NETWORK SCANNER  🔍                ║
║          Enemy Drone Detection — Phase 1                ║
╚══════════════════════════════════════════════════════════╝
{Style.RESET_ALL}""")


def run_scan(subnet: str, verbose: bool = False):
    """Run the full network scan."""
    print_banner()
    
    local_ip = get_local_ip()
    print(f"  {Fore.CYAN}Local IP:{Style.RESET_ALL}     {local_ip}")
    print(f"  {Fore.CYAN}Scan Subnet:{Style.RESET_ALL}  {subnet}")
    print(f"  {Fore.CYAN}Target Ports:{Style.RESET_ALL}  {DRONE_PORT} (Drone TCP), {GCS_PORT} (GCS HTTP)")
    print(f"  {Fore.CYAN}Threads:{Style.RESET_ALL}       {MAX_THREADS}")
    print()
    
    network = ipaddress.ip_network(subnet, strict=False)
    hosts = [str(ip) for ip in network.hosts()]
    
    print(f"  Scanning {len(hosts)} hosts...\n")
    
    drone_hosts = []
    gcs_hosts = []
    start_time = time.time()
    scanned = 0
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(scan_host, ip): ip for ip in hosts}
        
        for future in as_completed(futures):
            scanned += 1
            result = future.result()
            
            if result["drone_port"]:
                drone_hosts.append(result["ip"])
                print(f"  {Fore.GREEN}[+] DRONE FOUND{Style.RESET_ALL}  {result['ip']}:{DRONE_PORT}  ← RPI Drone Bridge!")
            
            if result["gcs_port"]:
                gcs_hosts.append(result["ip"])
                print(f"  {Fore.YELLOW}[+] GCS FOUND{Style.RESET_ALL}    {result['ip']}:{GCS_PORT}  ← Laptop A Dashboard!")
            
            if verbose and scanned % 25 == 0:
                print(f"  {Fore.WHITE}[~] Scanned {scanned}/{len(hosts)} hosts...{Style.RESET_ALL}")
    
    elapsed = time.time() - start_time
    
    # ==================== RESULTS ====================
    print(f"\n{'='*58}")
    print(f"  {Fore.RED}{Style.BRIGHT}SCAN RESULTS{Style.RESET_ALL}")
    print(f"{'='*58}")
    print(f"  Hosts scanned: {len(hosts)} in {elapsed:.1f}s")
    print()
    
    if drone_hosts:
        print(f"  {Fore.GREEN}{Style.BRIGHT}🎯 DRONE(S) DETECTED:{Style.RESET_ALL}")
        for ip in drone_hosts:
            print(f"     → {ip}:{DRONE_PORT}")
            # Verify
            vinfo = verify_drone_connection(ip)
            if vinfo["verified"]:
                t = vinfo["data"]
                print(f"       {Fore.GREEN}✓ VERIFIED — Live telemetry received!{Style.RESET_ALL}")
                print(f"       GPS:     {t.get('latitude', '?')}, {t.get('longitude', '?')}")
                print(f"       Alt:     {t.get('altitude', '?')}m")
                print(f"       Mode:    {t.get('flight_mode', '?')}")
                print(f"       Armed:   {t.get('armed', '?')}")
                print(f"       Battery: {t.get('battery_level', '?')}%")
            else:
                print(f"       {Fore.YELLOW}⚠ Port open but could not verify telemetry{Style.RESET_ALL}")
        print()
    else:
        print(f"  {Fore.RED}✗ No drone bridge found on port {DRONE_PORT}{Style.RESET_ALL}\n")
    
    if gcs_hosts:
        print(f"  {Fore.YELLOW}{Style.BRIGHT}📡 GCS DASHBOARD(S) DETECTED:{Style.RESET_ALL}")
        for ip in gcs_hosts:
            print(f"     → {ip}:{GCS_PORT}")
            vinfo = verify_gcs_connection(ip)
            if vinfo["verified"]:
                print(f"       {Fore.GREEN}✓ VERIFIED — GCS API responding!{Style.RESET_ALL}")
                state = vinfo["data"]
                print(f"       Connected: {state.get('connected', '?')}")
                print(f"       RPI IP:    {state.get('rpi_ip', '?')}")
            else:
                print(f"       {Fore.YELLOW}⚠ Port open but GCS API not verified{Style.RESET_ALL}")
        print()
    else:
        print(f"  {Fore.RED}✗ No GCS dashboard found on port {GCS_PORT}{Style.RESET_ALL}\n")
    
    print(f"{'='*58}")
    
    # Return results for use by other scripts
    return {
        "drone_ips": drone_hosts,
        "gcs_ips": gcs_hosts,
        "local_ip": local_ip,
        "scan_time": elapsed
    }


def main():
    parser = argparse.ArgumentParser(description="Drone Network Scanner — Phase 1")
    parser.add_argument("--subnet", default=None, help="Subnet to scan (e.g., 192.168.1.0/24)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show scan progress")
    parser.add_argument("--threads", type=int, default=MAX_THREADS, help="Number of scan threads")
    args = parser.parse_args()
    
    global MAX_THREADS
    MAX_THREADS = args.threads
    
    subnet = args.subnet
    if not subnet:
        local_ip = get_local_ip()
        subnet = guess_subnet(local_ip)
        print(f"  Auto-detected subnet: {subnet}")
    
    results = run_scan(subnet, verbose=args.verbose)
    
    # Save results for other attack scripts to use
    with open("scan_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to scan_results.json")


if __name__ == "__main__":
    main()
