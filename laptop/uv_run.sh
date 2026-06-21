#!/bin/bash
# ================================================================
#  UV Run Script for Laptop GCS
#  Quick launcher with intelligent defaults
# ================================================================

RPI_IP="${1:-10.58.17.137}"
PORT="${2:-5000}"
VOICE="${3:---no-voice}"

if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    cat << EOF
╔════════════════════════════════════════════════════════════════╗
║           Laptop GCS — UV Run Script                           ║
╚════════════════════════════════════════════════════════════════╝

USAGE:
  ./uv_run.sh [RPI_IP] [PORT] [--voice]

PARAMETERS:
  RPI_IP     RPI IP address (default: 10.58.17.137)
  PORT       Web server port (default: 5000)
  --voice    Enable voice control features

EXAMPLES:
  # Basic run with defaults
  ./uv_run.sh

  # Connect to specific RPI
  ./uv_run.sh 192.168.1.100

  # With voice control + custom port
  ./uv_run.sh 192.168.1.100 8000 --voice

ACCESS:
  Once running, open your browser to: http://localhost:$PORT
EOF
    exit 0
fi

echo ""
echo -e "\033[36m╔════════════════════════════════════════════════╗\033[0m"
echo -e "\033[36m║   Laptop GCS — Ground Control Station         ║\033[0m"
echo -e "\033[36m╚════════════════════════════════════════════════╝\033[0m"
echo ""

echo -e "\033[33mConfiguration:\033[0m"
echo "  RPI IP:        $RPI_IP"
echo "  Web Port:      $PORT"
echo "  Voice Control: $(if [[ "$VOICE" == "--voice" ]]; then echo "ENABLED"; else echo "disabled"; fi)"
echo ""

echo -e "\033[32mStarting Ground Control Station...\033[0m"
echo -e "\033[36mDashboard URL: http://localhost:$PORT\033[0m"
echo ""

if [[ "$VOICE" == "--voice" ]]; then
    uv run -f voice python laptop_gcs.py --rpi "$RPI_IP" --port "$PORT"
else
    uv run python laptop_gcs.py --rpi "$RPI_IP" --port "$PORT"
fi
