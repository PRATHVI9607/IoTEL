#!/bin/bash
# Raspberry Pi Setup Script for Voice Drone Control System
# Run this on the Raspberry Pi

set -e

echo "========================================="
echo "  Voice Drone Control - RPI Setup"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo bash setup.sh"
    exit 1
fi

echo "[1/7] Updating system..."
apt-get update
apt-get upgrade -y

echo "[2/7] Installing Python and dependencies..."
apt-get install -y python3 python3-pip python3-venv python3-dev git build-essential

echo "[3/7] Enabling UART..."
if ! grep -q "enable_uart=1" /boot/firmware/config.txt; then
    echo "enable_uart=1" >> /boot/firmware/config.txt
fi

echo "[4/7] Disabling Bluetooth (free up UART)..."
systemctl disable bluetooth
systemctl stop bluetooth

echo "[5/7] Installing Python packages..."
pip3 install --upgrade pip setuptools wheel
pip3 install dronekit pymavlink pyserial

echo "[6/7] Creating service user..."
useradd -r -s /bin/false drone || true
usermod -aG dialout drone

echo "[7/7] Setting permissions..."
chmod +x /home/pi/voice-drone-control/rpi/drone_bridge.py

echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Connect Pixhawk to RPI UART"
echo "2. Configure Pixhawk TELEM1 (57600 baud)"
echo "3. Run: python3 drone_bridge.py"
echo "4. Reboot: sudo reboot"