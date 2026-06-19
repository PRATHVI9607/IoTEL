#!/bin/bash
# IoTEL RPI Drone Bridge — setup with uv
# Run as root: sudo bash setup.sh
set -e

cd "$(dirname "$0")"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo bash setup.sh"
    exit 1
fi

echo "[1/5] Updating package lists..."
apt-get update -y

echo "      Removing broken packages that block apt..."
# aziot-identity-service is an Azure IoT Edge artifact with an unresolvable dep
# on this Pi; it has nothing to do with this project — remove it cleanly.
apt-get purge -y aziot-identity-service 2>/dev/null || true
apt-get autoremove -y 2>/dev/null || true

echo "      Installing system deps..."
apt-get install -y --no-install-recommends python3 python3-pip curl git

echo "[2/5] Installing uv..."
if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
# Make uv available in this shell session regardless of how it was installed
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
source "$HOME/.local/bin/env" 2>/dev/null || true
# Verify
uv --version

echo "[3/5] Enabling UART & disabling Bluetooth..."
CONFIG=/boot/firmware/config.txt
[ -f "$CONFIG" ] || CONFIG=/boot/config.txt
grep -q "enable_uart=1"        "$CONFIG" || echo "enable_uart=1"        >> "$CONFIG"
grep -q "dtoverlay=disable-bt" "$CONFIG" || echo "dtoverlay=disable-bt" >> "$CONFIG"
systemctl disable bluetooth 2>/dev/null || true
systemctl stop    bluetooth 2>/dev/null || true

echo "[4/5] Adding user to dialout (serial port access)..."
TARGET_USER="${SUDO_USER:-pi}"
usermod -aG dialout "$TARGET_USER" 2>/dev/null || true

echo "[5/5] Syncing Python dependencies with uv..."
uv sync

echo ""
echo "=========================================="
echo " Setup complete!"
echo " Reboot for UART changes to take effect."
echo "=========================================="
echo ""
echo "After reboot, run with:"
echo "  uv run python rpi_drone_bridge.py --ip <LAPTOP_IP>"
