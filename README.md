# 🚁 Voice Drone Control System

A comprehensive voice-based drone control system with health monitoring, anomaly detection, and beautiful web dashboard.

![System](https://img.shields.io/badge/Voice-Control-blue) ![DroneKit](https://img.shields.io/badge/DroneKit-2.14+-green) ![Python](https://img.shields.io/badge/Python-3.8+-blue)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Hardware Requirements](#-hardware-requirements)
- [Quick Start](#-quick-start)
- [RPI Setup](#-rpi-setup)
- [Laptop Setup](#-laptop-setup)
- [Running the System](#-running-the-system)
- [Voice Commands](#-voice-commands)
- [Flight Modes](#-flight-modes)
- [Troubleshooting](#-troubleshooting)
- [Safety](#-safety)

---

## 🌟 Features

- **Voice Control** - Command your drone with voice
- **Health Monitoring** - Real-time drone health tracking
- **Anomaly Detection** - GPS spoofing, jamming, battery alerts
- **Beautiful Dashboard** - Loki Theme with eco-green colors
- **TCP Telemetry Bridge** - Wireless RPI to laptop connection
- **Command History** - Full log of all commands
- **Multiple Flight Modes** - Stabilize, Loiter, RTL, Land, etc.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                   VOICE DRONE CONTROL SYSTEM                 │
├────────────────────────────────────────────────────────────────────┤
│                                                             │
│                   RASPBERRY PI 4                            │
│                   (On the Drone)                             │
│                   ┌──────────────┐                          │
│                   │ RPI Bridge   │                          │
│                   │ + Monitor   │                          │
│                   └──────┬───────┘                          │
│                          │                                   │
│              UART        │      TCP Socket                     │
│              (3.3V)    │      (WiFi)                        │
│                          │                                   │
│                   ┌──────▼───────┐                          │
│                   │   PIXHAWK   │                          │
│                   │  Flight    │                          │
│                   │ Controller │                          │
│                   └────────────┘                          │
│                               │                            │
│                      ┌────────┴────────┐                   │
│                      │                 │                   │
│                 Telemetry          RC Link                 │
│                      │                 │                   │
└──────────────────────┼─────────────────┼────────────────────┘
                      │                 │
                      ▼                 ▼
              ┌──────────────┐   ┌──────────────┐
              │   LAPTOP    │   │    RC      │
              │  (GCS)     │   │ Controller│
              │            │   │          │
              │ Web UI     │   │ Manual   │
              │ + Voice   │   │ Override │
              └───────────┘   └──────────┘
```

---

## 📦 Hardware Requirements

### On the Drone (RPI Side)

| Component | Description | Notes |
|-----------|-------------|-------|
| Raspberry Pi 4 | 4GB or 8GB | |
| Micro SD Card | 32GB+ Class 10 | With Raspberry Pi OS |
| USB-C Power | 5V 3A | **Separate from Pixhawk** |
| TTL Serial Cable | FT232R/CP2102 | **Must be 3.3V** |
| Jumper Wires | 4x female-female | For GPIO |

### Flight Controller

- Pixhawk 4 / Pixhawk 6X / Cube

### On the Laptop

- Laptop with Python 3.8+
- Microphone (for voice)
- WiFi connection

---

## 🚀 Quick Start

### 1. Hardware Connections

```
Raspberry Pi 4              Pixhawk (TELEM1)
─────────────              ──────────
GPIO 14 (TX)  ─────────────►  RX
GPIO 15 (RX)  ◄─────────────  TX
GND          ──────────────  GND
```

### 2. RPI Setup

```bash
# Copy files to RPI
scp -r rpi pi@192.168.1.100:~/

# SSH into RPI
ssh pi@192.168.1.100

# Run setup
cd ~/rpi
chmod +x setup.sh
sudo bash setup.sh

# Edit IP in code
nano rpi_drone_bridge.py
# Change: LAPTOP_IP = "YOUR_LAPTOP_IP"

# Run
sudo python3 rpi_drone_bridge.py --ip 192.168.1.X
```

### 3. Laptop Setup

```bash
# Copy files to laptop
cd laptop

# Create venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install
pip install -r requirements.txt

# Run
python laptop_gcs.py --rpi 192.168.1.100

# Open browser
http://localhost:5000
```

---

## 🔧 RPI Setup

### Manual Installation

```bash
# Update
sudo apt update && sudo apt upgrade -y

# Install dependencies
pip3 install dronekit pymavlink pyserial requests

# Enable UART
sudo nano /boot/firmware/config.txt
# Add: enable_uart=1

# Disable Bluetooth
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth

# Reboot
sudo reboot

# Verify
ls -l /dev/serial0
```

### Running the Code

```bash
# Basic
sudo python3 rpi_drone_bridge.py

# With options
sudo python3 rpi_drone_bridge.py \
    --ip 192.168.1.100 \
    --port 5000 \
    --uart /dev/ttyAMA0 \
    --baud 57600

# As service
sudo cp dronebridge.service /etc/systemd/system/
sudo systemctl enable dronebridge
sudo systemctl start dronebridge
```

### RPI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--ip` | 192.168.1.100 | Laptop IP |
| `--port` | 5000 | Laptop HTTP port |
| `--uart` | /dev/ttyAMA0 | UART device |
| `--baud` | 57600 | Baud rate |
| `--tcp-port` | 5760 | TCP listen port |

---

## 💻 Laptop Setup

### Installation

```bash
# Create venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Code

```bash
# Basic
python laptop_gcs.py

# With options
python laptop_gcs.py \
    --rpi 192.168.1.100 \
    --port 5760 \
    --web 5000
```

### Open Dashboard

```
http://localhost:5000
```

### Laptop Options

| Option | Default | Description |
|--------|---------|-------------|
| `--rpi` | 192.168.1.100 | RPI IP |
| `--port` | 5760 | RPI TCP port |
| `--web` | 5000 | Web server port |

---

## ▶️ Running the System

### Start RPI Side

```bash
# SSH into RPI
ssh pi@192.168.1.100

# Navigate
cd ~/rpi

# Run bridge + monitor
sudo python3 rpi_drone_bridge.py --ip YOUR_LAPTOP_IP
```

### Start Laptop Side

```bash
# Activate
source venv/bin/activate

# Run GCS
python laptop_gcs.py --rpi 192.168.1.100

# Open browser
# http://localhost:5000
```

### Connect and Control

1. Open dashboard at `http://localhost:5000`
2. Enter RPI IP address
3. Click **Connect**
4. Use voice buttons or type commands

---

## 🎤 Voice Commands

### Basic Commands

| Command | Action |
|---------|--------|
| "Arm" | Enable motors |
| "Disarm" | Disable motors |
| "Takeoff" / "Take off" | Take off (10m) |
| "Land" | Land the drone |
| "RTL" / "Return" | Return to launch |
| "Loiter" / "Hover" | Hold position |
| "Stabilize" | Stabilize mode |
| "Alt hold" | Altitude hold |
| "Guided" | Guided mode |
| "Auto" | Auto mode |

### Emergency Commands

| Command | Action |
|---------|--------|
| "Emergency land" | Force land |
| "Stop" / "Halt" | Immediate hover |

---

## 🛸 Flight Modes

| Mode | Description |
|------|-------------|
| **STABILIZE** | Manual, self-leveling |
| **ALT_HOLD** | Hold altitude, manual XY |
| **LOITER** | Hold GPS position |
| **GUIDED** | Go to point |
| **AUTO** | Execute mission |
| **LAND** | Automatic landing |
| **RTL** | Return to launch |
| **POSHOLD** | Position hold |

---

## 🔧 Troubleshooting

### UART Not Found

```bash
# Check
ls -l /dev/serial0

# Enable
sudo raspi-config
# → Interface Options → Serial Port → Enable
```

### Permission Denied

```bash
# Add to dialout
sudo usermod -a -G dialout $USER

# Log out and back in
```

### Connection Failed

```bash
# Check firewall
sudo ufw status

# Allow ports
sudo ufw allow 5760/tcp
sudo ufw allow 5000/tcp
```

### DroneKit Import Error

```bash
# Reinstall
pip install --upgrade dronekit pymavlink
```

---

## ⚠️ Safety

### Pre-Flight Checklist

- [ ] Props **REMOVED** for testing
- [ ] Battery charged
- [ ] GPS lock acquired (≥6 satellites)
- [ ] RC controller ready
- [ ] Clear line of sight

### Safety Rules

1. **Always keep RC ready** - For manual override
2. **Never fly indoors** without GPS
3. **Test on ground first** - Props OFF
4. **Separate power** - RPI from Pixhawk power
5. **Use 3.3V TTL** - Not 5V!
6. **Follow regulations** - Check local laws

### Emergency Procedures

1. **Lost connection** → RTL (if configured)
2. **RC failsafe** → Returns to launch
3. **Emergency** → "Emergency land" command

---

## 📁 Project Structure

```
├── rpi/
│   ├── rpi_drone_bridge.py    # Main RPI code
│   ├── requirements.txt      # Python deps
│   └── setup.sh            # Setup script
│
├── laptop/
│   ├── laptop_gcs.py       # GCS server
│   ├── requirements.txt   # Python deps
│   └── dashboard/
│       └── templates/
│           └── index.html  # Web dashboard
│
├── docs/
│   └── HARDWARE_CONNECTIONS.md  # Connection docs
│
└── README.md
```

---

## 🙏 Acknowledgments

- [DroneKit](https://github.com/dronekit/dronekit-python)
- [MAVLink](https://mavlink.io/)
- [Pixhawk](https://px4.io/)

---

## 📝 License

MIT License - See LICENSE file.

---

**⚠️ WARNING: Always follow local regulations. Use at your own risk.**

© 2026 Voice Drone Control System