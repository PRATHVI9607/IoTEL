#!/bin/bash
# IoTEL RPI Drone Bridge — setup with uv
# Run as root: sudo bash setup.sh
set -e

cd "$(dirname "$0")"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo bash setup.sh"
    exit 1
fi

echo "[1/5] Updating system..."
apt-get update -y
apt-get install -y python3 python3-pip curl git

echo "[2/5] Installing uv..."
if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Make uv available to root in this session
    source "$HOME/.local/bin/env" 2>/dev/null || true
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
fi

echo "[3/5] Enabling UART & disabling Bluetooth..."
CONFIG=/boot/firmware/config.txt
[ -f "$CONFIG" ] || CONFIG=/boot/config.txt
grep -q "enable_uart=1"     "$CONFIG" || echo "enable_uart=1"     >> "$CONFIG"
grep -q "dtoverlay=disable-bt" "$CONFIG" || echo "dtoverlay=disable-bt" >> "$CONFIG"
systemctl disable bluetooth 2>/dev/null || true
systemctl stop    bluetooth 2>/dev/null || true

echo "[4/5] Adding user to dialout (serial port access)..."
SUDO_USER="${SUDO_USER:-pi}"
usermod -aG dialout "$SUDO_USER" 2>/dev/null || true

echo "[5/5] Syncing Python dependencies with uv..."
uv sync

echo ""
echo "=========================================="
echo " Setup complete!"
echo " NOTE: Reboot for UART changes to apply."
echo "=========================================="
echo ""
echo "Run with:"
echo "  uv run python rpi_drone_bridge.py --ip <LAPTOP_IP>"
echo ""
echo "If your project is in ~/IDP_2, run from there:"
echo "  cd ~/IDP_2/rpi && sudo bash setup.sh"
