# 🚁 Voice Drone Control System

A comprehensive voice-based drone control system that connects a Pixhawk/Cube flight controller to a Raspberry Pi 4 via UART, with a beautiful voice-controlled Ground Control Station running on your laptop.

![System Architecture](docs/SYSTEM_ARCHITECTURE.png)

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Hardware Requirements](#-hardware-requirements)
- [Hardware Connections](#-hardware-connections)
- [Quick Start Guide](#-quick-start-guide)
- [RPI Setup](#-rpi-setup)
- [Laptop Setup](#-laptop-setup)
- [Configuration](#-configuration)
- [Running the System](#-running-the-system)
- [Voice Commands](#-voice-commands)
- [Flight Modes](#-flight-modes)
- [Troubleshooting](#-troubleshooting)
- [Safety](#-safety)
- [License](#-license)

---

## 🌟 Features

- **Voice Control** - Command your drone using natural voice commands
- **Beautiful UI** - Loki Theme-inspired dashboard with eco-green color palette
- **Real-time Telemetry** - Live altitude, speed, GPS, and battery monitoring
- **UART Communication** - Direct Pixhawk to RPI connection via serial
- **TCP Telemetry Bridge** - Wireless connection between RPI and laptop
- **Multiple Flight Modes** - Support for Stabilize, Loiter, RTL, Land, etc.
- **Command History** - Full log of all commands sent to drone
- **Light/Dark Theme** - Toggle between themes

---

## 🔧 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VOICE DRONE CONTROL SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                     ┌───────────────────────┐                               │
│                     │    RASPBERRY PI 4    │                               │
│                     │    (On the Drone)   │                               │
│                     └──────────┬──────────┘                               │
│                                │                                            │
│              UART              │              TCP Socket                      │
│              (TTL)             │              (WiFi)                          │
│                                │                                            │
│     ┌──────────────────────────┼──────────────────────────┐                   │
│     │                          │                          │                    │
│     ▼                          │                          ▼                    │
│ ┌────────────┐               │               ┌──────────────┐                │
│ │  PIXHAWK   │               │               │    LAPTOP   │                │
│ │  (Flight  │◄──────────────┼───────────────►│  (Ground   │                │
│ │ Controller)               │               │  Control)  │                │
│ └────────────┘               │               └──────────────┘                │
│                                │                          │                    │
│                                │            ┌──────────────▼──────────┐       │
│                                │            │    Voice Control GCS   │       │
│                                │            │    + Web Dashboard    │       │
│                                │            └───────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Hardware Requirements

### On the Drone (RPI Side)

| Component | Description | Notes |
|-----------|-------------|-------|
| Raspberry Pi 4 | 4GB or 8GB model | Recommended 8GB |
| Micro SD Card | 32GB+ Class 10 | With Raspberry Pi OS Lite |
| USB-C Power | 5V 3A | Separate power from Pixhawk |
| TTL Serial Cable | FT232R or CP2102 | **Must be 3.3V logic** |
| Jumper Wires | 4x female-to-female | For direct GPIO connection |
| WiFi Dongle | If not using built-in WiFi | Optional |
| Case/Enclosure | Protection | Recommended |

### Flight Controller

| Component | Description | Notes |
|-----------|-------------|-------|
| Pixhawk 4 | Popular choice | |
| Pixhawk 6X | Newer version | |
| Cube | Alternative | |

### On the Laptop

| Component | Description | Notes |
|-----------|-------------|-------|
| Laptop | Any with Python 3.8+ | |
| Microphone | Built-in or external | Required for voice |
| WiFi | For telemetry | |

---

## 🔌 Hardware Connections

### UART Connection (RPI ↔ Pixhawk)

#### Pinout Reference

```
┌─────────────────────────────────────────────────────────────────┐
│              RASPBERRY PI 4 GPIO HEADER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    3.3V  (1) (2)  5V                                            │
│    SDA   (3) (4)  5V                                            │
│    SCL   (5) (6)  GND                                            │
│    GPIO4 (7) (8)  GPIO 14 (TX) ◄──────────► Pixhawk RX          │
│    GND   (9) (10) GPIO 15 (RX) ◄──────────► Pixhawk TX          │
│   GPIO18 (11)(12) GPIO 18                                       │
│   GPIO21 (13)(14) GND                                            │
│   MOSI  (15)(16) GPIO 21                                       │
│   MISO  (17)(18) GPIO 22                                       │
│   SCLK  (19)(20) GND                                            │
│    CE1  (21)(22) CE0                                            │
│   MOSI  (23)(24) SCLK                                           │
│    GND  (25)(26) CE0                                            │
│                                                                  │
│   IMPORTANT: Use GPIO 14 (TX) and GPIO 15 (RX)                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Connection Diagram

```
Raspberry Pi 4                          Pixhawk (TELEM1)
───────────────                        ──────────────────
                                          
GPIO 14 (TX)  ─────────────────────────►  RX
GPIO 15 (RX)  ◄─────────────────────────  TX
GPIO 6 (GND)  ──────────────────────────  GND
     GND      ──────────────────────────  GND

⚠️ IMPORTANT: Use 3.3V TTL logic, NOT 5V!
```

### Enable UART on Raspberry Pi

1. Edit the boot config:
```bash
sudo nano /boot/firmware/config.txt
```

2. Add these lines at the end:
```bash
# Enable UART
enable_uart=1
dtoverlay=disable-bt
```

3. Disable Bluetooth (which uses the same UART):
```bash
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth
```

4. Reboot:
```bash
sudo reboot
```

5. Verify UART is enabled:
```bash
ls -l /dev/serial0
```

### Pixhawk Configuration

Using Mission Planner or QGroundControl:

1. Connect to Pixhawk via USB
2. Go to **Parameters** → **SERIAL0_BAUD** (or TELEM1)
3. Set baud to **57600**
4. Set protocol to **MAVLink**
5. Save and reboot

---

## 🚀 Quick Start Guide

### Step 1: Hardware Setup

1. Connect Pixhawk TELEM1 to Raspberry Pi UART
2. Power Pixhawk separately (do NOT power from RPI)
3. Power Raspberry Pi with USB-C (5V 3A)
4. Configure Pixhawk serial port for MAVLink at 57600 baud

### Step 2: RPI Setup

```bash
# 1. Copy files to RPI
scp -r voice-drone-control/rpi pi@192.168.4.1:~/

# 2. SSH into RPI
ssh pi@192.168.4.1

# 3. Run setup script
cd ~/voice-drone-control/rpi
chmod +x setup.sh
sudo bash setup.sh

# 4. Install DroneBridge as service
sudo cp dronebridge.service /etc/systemd/system/
sudo systemctl enable dronebridge
sudo systemctl start dronebridge

# 5. Check status
sudo systemctl status dronebridge
```

### Step 3: Laptop Setup

```bash
# 1. Clone repository
cd ~/voice-drone-control/laptop

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run GCS
python gcs_server.py --host 192.168.4.1 --port 5760
```

### Step 4: Access Dashboard

Open your browser and navigate to:

```
http://localhost:5000
```

---

## 💻 RPI Setup

### Manual Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
pip3 install dronekit pymavlink pyserial

# Enable UART
sudo nano /boot/firmware/config.txt
# Add: enable_uart=1

# Disable Bluetooth
sudo systemctl disable bluetooth

# Reboot
sudo reboot

# Test UART
ls -l /dev/serial0
```

### Running DroneBridge

```bash
# Basic usage
python3 drone_bridge.py

# With custom settings
python3 drone_bridge.py --uart /dev/serial0 --baud 57600 --port 5760

# As systemd service
sudo cp dronebridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dronebridge
sudo systemctl start dronebridge
```

### DroneBridge Options

| Option | Default | Description |
|--------|---------|-------------|
| `--uart`, `-u` | /dev/serial0 | UART device path |
| `--baud`, `-b` | 57600 | UART baud rate |
| `--port`, `-p` | 5760 | TCP listen port |
| `--host` | 0.0.0.0 | TCP bind address |
| `--verbose`, `-v` | False | Enable debug logging |

---

## 💻 Laptop Setup

### Installation

```bash
# Create project directory
mkdir -p ~/voice-drone-control
cd ~/voice-drone-control

# Clone or copy files
cp -r /path/to/voice-drone-control/laptop .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Voice Recognition Setup (Optional)

For full voice recognition support:

```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev python3-all

# macOS
brew install portaudio

# Windows
# Download portaudio from http://www.portaudio.com/download.html
```

### Running GCS

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Run voice control dashboard
python gcs_server.py --host 192.168.4.1 --port 5760 --port-gui 5000

# Access at http://localhost:5000
```

### GCS Server Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | 192.168.4.1 | RPI IP address |
| `--port` | 5760 | RPI TCP port |
| `--port-gui` | 5000 | Web dashboard port |
| `--debug` | False | Enable Flask debug |

---

## ⚙️ Configuration

### Network Configuration

#### Option A: RPI as WiFi Access Point

```bash
# Configure hostapd
sudo apt install hostapd

sudo nano /etc/hostapd/hostapd.conf
```

```ini
interface=wlan0
ssid=DroneControl
hw_mode=g
channel=6
wpa=2
wpa_passphrase=drone1234
```

```bash
# Start hostapd
sudo systemctl start hostapd
```

#### Option B: Connect to Existing WiFi

```bash
# Edit wpa_supplicant
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

```ini
network={
    ssid="YourWiFiNetwork"
    psk="YourPassword"
}
```

```bash
sudo wpa_cli reconfigure
```

### Pixhawk Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| SERIAL0_BAUD | 57600 | Telemetry baud rate |
| SERIAL0_PROTOCOL | 1 | MAVLink |
| TELEM1_BAUD | 57600 | Secondary port |
| TELEM1_PROTOCOL | 1 | MAVLink |

---

## ▶️ Running the System

### Starting the RPI Side

```bash
# SSH into RPI
ssh pi@192.168.4.1

# Navigate to project
cd ~/voice-drone-control/rpi

# Run DroneBridge
python3 drone_bridge.py --uart /dev/serial0 --baud 57600 --port 5760

# Or run as service
sudo systemctl start dronebridge
```

### Starting the Laptop Side

```bash
# Activate environment
source venv/bin/activate

# Run GCS
python gcs_server.py --host 192.168.4.1 --port 5760

# Open browser
# http://localhost:5000
```

### Connect and Fly

1. Open dashboard at `http://localhost:5000`
2. Enter RPI IP (default: 192.168.4.1)
3. Click **Connect**
4. Use voice or buttons to control

---

## 🎤 Voice Commands

### Basic Commands

| Command | Action |
|---------|--------|
| "Takeoff" / "Take off" | Initiate takeoff (10m default) |
| "Land" | Land the drone |
| "Return home" / "RTL" | Return to launch point |
| "Arm" | Arm the motors |
| "Disarm" | Disarm the motors |
| "Loiter" / "Hover" | Hold position |
| "Stop" | Stop movement |

### Flight Mode Commands

| Command | Mode |
|---------|------|
| "Stabilize" | STABILIZE |
| "Alt hold" | ALT_HOLD |
| "Position" | POSHOLD |
| "Guided" | GUIDED |
| "Auto" | AUTO |
| "Manual" | MANUAL |

### Emergency Commands

| Command | Action |
|---------|--------|
| "Emergency land" | Force landing |
| "Stop" / "Halt" | Immediate hover |

---

## 🛸 Flight Modes

### Available Modes

| Mode | Description |
|------|-------------|
| **STABILIZE** | Manual mode, self-leveling |
| **ALT_HOLD** | Holds altitude, manual XY |
| **LOITER** | Holds position via GPS |
| **GUIDED** | Go to specific point |
| **AUTO** | Execute mission |
| **LAND** | Automatic landing |
| **RTL** | Return to launch |

### Quick Command Buttons

- **Arm** - Enable motors
- **Disarm** - Disable motors
- **Takeoff** - Take off to 10m
- **Land** - Execute landing
- **Return** - Return to home
- **Loiter** - Hold position
- **Emergency** - Force land

---

## 🔧 Troubleshooting

### UART Connection Issues

```bash
# Check UART exists
ls -l /dev/serial0

# Test UART permissions
ls -l /dev/ttyS0

# Add user to dialout group
sudo usermod -a -G dialout $USER
```

### Connection Issues

```bash
# Check if service is running
sudo systemctl status dronebridge

# Check logs
sudo journalctl -u dronebridge -f

# Test connection
nc -zv 192.168.4.1 5760
```

### Voice Recognition Issues

```bash
# Test microphone
python3 -c "import speech_recognition as sr; r = sr.Recognizer(); print(r.listen_nothing)"

# List microphones
python3 -c "import speech_recognition as sr; print([m.name for m in sr.Microphone().list_microphones()])"
```

### DroneKit Issues

```bash
# Check dronekit installation
pip show dronekit

# Reinstall if needed
pip install --upgrade dronekit
```

### Common Errors

| Error | Solution |
|-------|---------|
| "Permission denied" | Add user to dialout group |
| "Connection refused" | Check IP and port |
| "Device not found" | Check UART path |
| "Module not found" | Install dependencies |

---

## ⚠️ Safety

### Pre-Flight Checklist

- [ ] Props removed for testing
- [ ] Battery charged
- [ ] GPS lock acquired
- [ ] RC controller ready (for manual override)
- [ ] Clear line of sight
- [ ] Safe altitude for testing

### Safety Rules

1. **Always have manual RC ready** - For emergency override
2. **Never fly indoors** without GPS
3. **Test on ground first** - With props OFF
4. **Keep battery disconnected** until ready to fly
5. **Never power RPI from Pixhawk**
6. **Use 3.3V TTL** - Not 5V!
7. **Follow local regulations** - Check FAA/local laws

### Emergency Procedures

1. **Lost connection**: Drone enters RTL (if configured)
2. **RC failsafe**: Returns to launch or lands
3. **Emergency land**: Say "Emergency land"

---

## 📚 Documentation

- [Pixhawk Documentation](https://docs.px4.io/)
- [DroneKit Docs](https://dronekit-python.readthedocs.io/)
- [MAVLink Protocol](https://mavlink.io/)
- [Raspberry Pi UART](https://www.raspberrypi.com/documentation/)

---

## 📝 License

MIT License - See LICENSE file for details.

---

## 🙏 Acknowledgments

- [DroneKit](https://github.com/dronekit/dronekit-python) - Python API for drones
- [MAVLink](https://mavlink.io/) - Drone communication protocol
- [Pixhawk](https://px4.io/) - Open source flight controller
- [Raspberry Pi](https://www.raspberrypi.com/) - Single board computer

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

---

## 📞 Support

- Open an [issue](https://github.com/your-repo/issues) for bugs
- Check [troubleshooting](#-troubleshooting) section
- Review dronekit documentation

---

**⚠️ WARNING: Always follow local regulations when flying drones. This software is for educational and experimental purposes. Use at your own risk.**