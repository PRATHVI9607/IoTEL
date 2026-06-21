#!/bin/bash
# ================================================================
#  UV Run Script for Attacker Console
#  Full attack orchestration tool
# ================================================================

RPI_IP="${1:-}"
GCS_IP="${2:-}"
RPI_PORT="${3:-5760}"
GCS_PORT="${4:-5000}"

if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]] || ([ -z "$RPI_IP" ] && [ -z "$GCS_IP" ]); then
    cat << EOF
╔════════════════════════════════════════════════════════════════╗
║         Attacker Console — Full Attack Framework               ║
║         Educational Use — IDP Security Research                ║
╚════════════════════════════════════════════════════════════════╝

USAGE:
  ./uv_run.sh [RPI_IP] [GCS_IP] [RPI_PORT] [GCS_PORT]

PARAMETERS:
  RPI_IP      RPI Drone IP (auto-discover if not set)
  GCS_IP      Laptop GCS IP (auto-discover if not set)
  RPI_PORT    RPI port (default: 5760)
  GCS_PORT    GCS port (default: 5000)

EXAMPLES:
  # Auto-discover targets via network scan
  ./uv_run.sh

  # Specify targets
  ./uv_run.sh 10.193.181.136 10.193.181.50

  # Custom ports
  ./uv_run.sh 192.168.1.100 192.168.1.50 5760 5000

FEATURES:
  [1] Phase 1  — Network Scan (discover drone & GCS)
  [2] Phase 2  — Passive Telemetry Sniff
  [3] Phase 3A — Telemetry Spoof (fake GCS data)
  [4] Phase 3B — Command Injection (TCP)
  [5] Combo    — Sniff + Spoof simultaneously

ATTACKS:
  - GPS Position Shift (500m offset)
  - Battery Critical (fake low battery)
  - Fake Landing (drone stopped)
  - Inject Alerts (confuse operator)
  - Mode Change (LOITER → STABILIZE)
  - Fake Jamming Alerts
  - Command Injection (arm, disarm, land, etc.)
EOF
    exit 0
fi

echo ""
echo -e "\033[31m╔════════════════════════════════════════════════╗\033[0m"
echo -e "\033[31m║           ATTACK CONSOLE                      ║\033[0m"
echo -e "\033[31m║     Enemy Drone Detection & Spoofing          ║\033[0m"
echo -e "\033[31m║     Educational Use Only                      ║\033[0m"
echo -e "\033[31m╚════════════════════════════════════════════════╝\033[0m"
echo ""

if [ -n "$RPI_IP" ]; then
    echo -e "\033[33mRPI Target:  $RPI_IP:$RPI_PORT\033[0m"
fi
if [ -n "$GCS_IP" ]; then
    echo -e "\033[33mGCS Target:  $GCS_IP:$GCS_PORT\033[0m"
fi
if [ -z "$RPI_IP" ] && [ -z "$GCS_IP" ]; then
    echo -e "\033[36mNo targets specified — Network scan will auto-discover\033[0m"
fi

echo ""
echo -e "\033[32mStarting Attack Console...\033[0m"
echo ""

args=("python" "full_attack.py")
if [ -n "$RPI_IP" ]; then args+=(--rpi "$RPI_IP"); fi
if [ -n "$GCS_IP" ]; then args+=(--gcs "$GCS_IP"); fi

uv run "${args[@]}"
