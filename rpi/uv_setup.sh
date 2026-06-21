#!/bin/bash
# ================================================================
#  UV Setup Script for RPI Drone Bridge
#  Linux version (for Raspberry Pi)
# ================================================================

echo -e "\033[36m╔════════════════════════════════════════════════╗\033[0m"
echo -e "\033[36m║   RPI Drone Bridge — UV Setup                 ║\033[0m"
echo -e "\033[36m╚════════════════════════════════════════════════╝\033[0m"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "\033[31m✗ UV not found!\033[0m"
    echo "Install UV with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

uvVersion=$(uv --version)
echo -e "\033[32m✓ UV found: $uvVersion\033[0m"
echo ""

echo -e "\033[33mInstalling dependencies with UV...\033[0m"
uv sync

echo ""
echo -e "\033[32m✓ Setup complete! To run the RPI bridge:\033[0m"
echo ""
echo -e "\033[36m  uv run python3 rpi_drone_bridge.py [--laptop <IP>] [--port <PORT>]\033[0m"
echo ""
echo "Typical command:"
echo -e "\033[36m  uv run python3 rpi_drone_bridge.py --laptop 10.58.17.137 --port 5760\033[0m"
echo ""
