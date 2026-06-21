#!/bin/bash
# ================================================================
#  UV Setup Script for Attacker Console
#  Linux/macOS version
# ================================================================

echo -e "\033[36m╔════════════════════════════════════════════════╗\033[0m"
echo -e "\033[36m║   Attacker Console — UV Setup                 ║\033[0m"
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
echo -e "\033[32m✓ Setup complete! To run the attack console:\033[0m"
echo ""
echo -e "\033[36m  uv run python full_attack.py\033[0m"
echo ""
echo -e "\033[36mOr with specific targets:\033[0m"
echo -e "\033[36m  uv run python full_attack.py --rpi 10.193.181.136 --gcs 10.193.181.50\033[0m"
echo ""
echo -e "\033[33m⚠ WARNING: Educational use only!\033[0m"
echo ""
