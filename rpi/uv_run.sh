#!/bin/bash
# ================================================================
#  UV Run Script for RPI Drone Bridge
#  Quick launcher with defaults
# ================================================================

LAPTOP_IP="${1:-10.58.17.137}"
LAPTOP_PORT="${2:-5000}"

if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    cat << EOF
╔════════════════════════════════════════════════════════════════╗
║           RPI Bridge — UV Run Script                           ║
╚════════════════════════════════════════════════════════════════╝

USAGE:
  ./uv_run.sh [LAPTOP_IP] [LAPTOP_PORT]

PARAMETERS:
  LAPTOP_IP       Laptop GCS IP (default: 10.58.17.137)
  LAPTOP_PORT     Laptop GCS port (default: 5000)

EXAMPLES:
  # Basic run with defaults
  ./uv_run.sh

  # Connect to specific laptop
  ./uv_run.sh 192.168.1.50

  # Custom port
  ./uv_run.sh 192.168.1.50 5000

HARDWARE REQUIREMENTS:
  - Pixhawk connected to UART (/dev/ttyAMA0)
  - GPS module connected to Pixhawk
  - Powered via battery or 5V supply
EOF
    exit 0
fi

echo ""
echo -e "\033[36m╔════════════════════════════════════════════════╗\033[0m"
echo -e "\033[36m║   RPI Drone Bridge                             ║\033[0m"
echo -e "\033[36m╚════════════════════════════════════════════════╝\033[0m"
echo ""

echo -e "\033[33mConfiguration:\033[0m"
echo "  Laptop IP:     $LAPTOP_IP"
echo "  Laptop Port:   $LAPTOP_PORT"
echo "  Local Port:    5760 (TCP Server)"
echo ""

echo -e "\033[32mStarting RPI Bridge...\033[0m"
echo "$(date '+%H:%M:%S') [INFO] Connecting to Pixhawk..."
echo ""

uv run python3 rpi_drone_bridge.py --ip "$LAPTOP_IP" --port "$LAPTOP_PORT"
