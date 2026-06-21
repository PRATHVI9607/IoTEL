#!/bin/bash
# ================================================================
#  UV Setup Script for Laptop GCS (Ground Control Station)
#  Linux/macOS version
# ================================================================

echo -e "\033[36m╔════════════════════════════════════════════════╗\033[0m"
echo -e "\033[36m║   Laptop GCS — UV Package Setup               ║\033[0m"
echo -e "\033[36m╚════════════════════════════════════════════════╝\033[0m"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "\033[31m✗ UV not found! Install from: https://docs.astral.sh/uv/getting-started/\033[0m"
    exit 1
fi

uvVersion=$(uv --version)
echo -e "\033[32m✓ UV found: $uvVersion\033[0m"
echo ""

echo -e "\033[33mInstalling dependencies with UV...\033[0m"
uv sync --all-extras

echo ""
echo -e "\033[32m✓ Setup complete! To run the GCS:\033[0m"
echo ""
echo -e "\033[36m  uv run python laptop_gcs.py --rpi <RPI_IP> --port 5000\033[0m"
echo ""
echo -e "\033[36mOr with voice control:\033[0m"
echo -e "\033[36m  uv run -f voice python laptop_gcs.py --rpi <RPI_IP>\033[0m"
echo ""
