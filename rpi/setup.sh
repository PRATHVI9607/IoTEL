#!/bin/bash
#================================================================
#  RPI Setup Script for Voice Drone Control
#  Run this on the Raspberry Pi
#================================================================

set -e

echo "============================================"
echo "  Voice Drone Control - RPI Setup"
echo "============================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo bash setup.sh"
    exit 1
fi

echo "[1/6] Updating system..."
apt-get update
apt-get upgrade -y

echo "[2/6] Installing Python and dependencies..."
apt-get install -y python3 python3-pip python3-venv git

echo "[3/6] Enabling UART..."
if ! grep -q "enable_uart=1" /boot/firmware/config.txt; then
    echo "enable_uart=1" >> /boot/firmware/config.txt
fi

# Disable Bluetooth to free up UART
echo "[4/6] Disabling Bluetooth..."
systemctl disable bluetooth || true
systemctl stop bluetooth || true

# Install Python packages
echo "[5/6] Installing Python packages..."
pip3 install --upgrade pip setuptools wheel
pip3 install dronekit pymavlink pyserial requests

# Create log directory
echo "[6/6] Creating directories..."
mkdir -p /var/log || true

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Connect Pixhawk to RPI UART (GPIO 14/15)"
echo "2. Configure Pixhawk TELEM1 (57600 baud)"
echo "3. Edit rpi_drone_bridge.py with laptop IP"
echo "4. Run: sudo python3 rpi_drone_bridge.py"
echo "5. Reboot if needed: sudo reboot"