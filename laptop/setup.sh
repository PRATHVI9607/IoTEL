#!/bin/bash
#================================================================
#  Laptop Setup Script for Voice Drone Control
#  Run this on your laptop
#================================================================

set -e

echo "============================================"
echo "  Voice Drone Control - Laptop Setup"
echo "============================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Install from python.org"
    exit 1
fi

echo "Python version: $(python3 --version)"

echo "[1/4] Creating virtual environment..."
python3 -m venv venv

echo "[2/4] Activating virtual environment..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

echo "[3/4] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/4] Installation complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Edit laptop_gcs.py with RPI IP if needed"
echo "2. Run: python laptop_gcs.py"
echo "3. Open browser: http://localhost:5000"
echo ""
echo "To activate environment in future:"
echo "  source venv/bin/activate  (Linux/Mac)"
echo "  venv\\Scripts\\activate   (Windows)"