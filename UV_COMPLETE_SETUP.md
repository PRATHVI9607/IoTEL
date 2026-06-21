# 🚀 Complete UV Setup Guide — Drone Control & Spoofing Attack

This guide walks you through setting up the drone control system and attack framework using UV package manager.

---

## 📋 Prerequisites

### All Systems
- Python 3.11+ (UV will manage this automatically)
- UV package manager installed
- Network connectivity between all devices

### Hardware (Drone System)
- Raspberry Pi 4+ with Raspbian OS
- Pixhawk flight controller
- USB UART adapter or RPI UART
- WiFi network for RPI connectivity

---

## 🛠️ Installation Steps

### Step 1: Install UV (All Systems)

**Windows (PowerShell - Run as Administrator)**
```powershell
# Install UV
irm https://astral.sh/uv/install.ps1 | iex

# Verify
uv --version
```

**Linux / macOS**
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"

# Verify
uv --version
```

---

### Step 2: Setup Laptop GCS (Defender) — Windows

```powershell
# Navigate to laptop folder
cd c:\Workspace\IoTEL\laptop

# Run setup script (one-time)
.\uv_setup.ps1

# This will:
# ✓ Check UV installation
# ✓ Install all Flask, PyMavLink, requests dependencies
# ✓ Verify setup is complete
```

**Verify Laptop GCS Setup**
```powershell
# Test basic dependencies
uv run python -c "import flask; import requests; print('✓ OK')"
```

---

### Step 3: Setup RPI Bridge — SSH to Raspberry Pi

```bash
# SSH into RPI
ssh pi@<RPI_IP>
# Example: ssh pi@10.58.17.137

# Navigate to rpi folder
cd rpi

# Run setup script (one-time)
./uv_setup.sh

# This will:
# ✓ Check UV installation
# ✓ Install PyMavLink, pyserial, requests
# ✓ Prepare for Pixhawk connection
```

**Verify RPI Setup**
```bash
# Test dependencies
uv run python3 -c "import pymavlink; import serial; print('✓ OK')"
```

---

### Step 4: Setup Attacker Console — Windows (Different PC)

```powershell
# Navigate to attacker folder
cd c:\Workspace\IoTEL\laptop2_attacker

# Run setup script (one-time)
.\uv_setup.ps1

# This will:
# ✓ Check UV installation
# ✓ Install requests, scapy, colorama
# ✓ Prepare attack tools
```

**Verify Attacker Setup**
```powershell
# Test dependencies
uv run python -c "import requests; import scapy; import colorama; print('✓ OK')"
```

---

## ▶️ Running the System

### Configuration: Update IPs in Your Network

**Step 1: Find Your Device IPs**
```bash
# On Windows (PowerShell)
ipconfig

# On Linux/macOS
hostname -I
# or
ifconfig | grep inet
```

**Step 2: Update Default IPs**

Edit the run scripts to use your actual IPs:

**Laptop GCS** (`laptop/uv_run.ps1`):
```powershell
$RpiIp = "YOUR_RPI_IP"      # E.g., "192.168.1.100"
$Port = 5000
```

**RPI Bridge** (`rpi/uv_run.sh`):
```bash
LAPTOP_IP="YOUR_LAPTOP_IP"  # E.g., "192.168.1.50"
LAPTOP_PORT="5000"
```

---

### Running Step-by-Step

**Terminal 1: Start RPI Bridge** (SSH to RPI)
```bash
cd rpi
./uv_run.sh YOUR_LAPTOP_IP 5000

# Output should show:
# [CONNECT] Connecting to PixHawk on /dev/ttyAMA0...
# [OK] Connected successfully (HEARTBEAT received)
```

**Terminal 2: Start Laptop GCS** (Windows)
```powershell
cd c:\Workspace\IoTEL\laptop
.\uv_run.ps1 -RpiIp YOUR_RPI_IP -Port 5000

# Output should show:
# ✓ Connected successfully
# Dashboard URL: http://localhost:5000
```

**Terminal 3: Start Attacker Console** (Windows - Different PC if possible)
```powershell
cd c:\Workspace\IoTEL\laptop2_attacker
.\uv_run.ps1

# Then choose:
# [1] Phase 1 — Network Scan (auto-discover targets)
# [2] Phase 2 — Passive Sniff
# [3] Phase 3A — Telemetry Spoof
# [4] Phase 3B — Command Injection
# [5] Combo — Sniff + Spoof
```

---

## 🎮 Operating the System

### Defender (Laptop A - GCS)

**Dashboard Access**
```
Open browser: http://localhost:5000
```

**Web Dashboard Features**
- Live telemetry display (GPS, altitude, battery, heading)
- Flight mode selector
- Current alerts and anomalies
- Command history log
- Real-time status indicators

**Voice Control** (Optional)
```powershell
# With voice support enabled
.\uv_run.ps1 -RpiIp YOUR_RPI_IP -Voice

# Say voice commands:
# - "arm"
# - "takeoff"
# - "land"
# - "return home"
# - "loiter"
```

**Manual Commands**
```
Available via web dashboard:
- ARM / DISARM
- TAKEOFF / LAND
- LOITER / STABILIZE / ALT_HOLD
- RETURN TO LAUNCH (RTL)
```

---

### Attacker (Laptop B - Full Attack Console)

**Phase 1: Network Discovery**
```
[1] Phase 1 — Network Scan
    → Scans for RPI (port 5760)
    → Scans for GCS (port 5000)
    → Auto-identifies targets
```

**Phase 2: Passive Sniffing**
```
[2] Phase 2 — Passive Telemetry Sniff
    → Connects to RPI's TCP server
    → Captures all telemetry packets
    → Displays real drone state
```

**Phase 3A: Telemetry Spoofing**
```
[3] Phase 3A — Telemetry Spoof
    Available attacks:
    ✓ GPS Shift (500m offset)
    ✓ GPS Drift (gradual position slip)
    ✓ Battery Critical (fake low battery)
    ✓ Fake Landing (drone appears to land)
    ✓ Inject Alerts (confuse operator)
    ✓ Jamming Alert (fake GPS loss)
    ✓ Mode Change (fake mode switch)
```

**Phase 3B: Command Injection**
```
[4] Phase 3B — Command Injection
    Available commands:
    ✓ arm — Arm motors
    ✓ disarm — Stop motors (DANGEROUS!)
    ✓ takeoff — Climb to 10m
    ✓ land — Descend and land
    ✓ rtl — Return to home
    ✓ loiter — Hover
    ✓ stabilize — Manual mode
```

---

## 📊 Expected Outputs

### RPI Bridge Success
```
[CONNECT] Connecting to PixHawk on /dev/ttyAMA0...
[OK] Connected successfully
[HEARTBEAT] Received from PixHawk
[TCP_SERVER] Listening on 5760...
[TELEMETRY] lat=12.9716 lon=77.5946 alt=10.2 battery=78%
```

### Laptop GCS Success
```
Connected successfully to RPI at 10.58.17.137:5760
Starting Flask web server on http://localhost:5000
[INFO] Received telemetry from RPI
[INFO] GPS Fix: 3D lock, 12 satellites
[ALERT] Battery level: 78%
```

### Attacker Console Success
```
╔════════════════╗
║  ATTACK CONSOLE║
╚════════════════╝

[SCAN] Scanning 192.168.1.0/24...
[FOUND] RPI at 192.168.1.100:5760 ✓
[FOUND] GCS at 192.168.1.50:5000 ✓

Ready for attacks. Choose phase...
```

---

## ✅ Verification Checklist

- [ ] UV installed on all systems
- [ ] All setup scripts completed successfully
- [ ] RPI Bridge connected to Pixhawk (HEARTBEAT received)
- [ ] Laptop GCS dashboard accessible at http://localhost:5000
- [ ] Dashboard shows live telemetry (GPS, battery, etc.)
- [ ] Attacker console discovers RPI and GCS automatically
- [ ] Voice commands work (if enabled)
- [ ] Manual commands execute from dashboard
- [ ] Spoofed telemetry changes GCS dashboard values
- [ ] Command injection forces drone mode changes

---

## 🚨 Troubleshooting

### Common Issues

**"uv: command not found"**
```powershell
# Restart PowerShell after installation
# Or manually add to PATH:
$env:PATH += ";$env:APPDATA\Python\Scripts"
```

**RPI can't connect to Pixhawk**
```bash
# Check UART connection
ls -la /dev/ttyAMA0

# Test with minicom
minicom -b 57600 -o -D /dev/ttyAMA0

# For USB adapter:
ls /dev/ttyUSB*
```

**GCS can't reach RPI**
```powershell
# Check network connectivity
ping 10.58.17.137

# Test TCP connection
Test-NetConnection -ComputerName 10.58.17.137 -Port 5760
```

**Spoofing attacks don't work**
```
Make sure:
1. Attacker and GCS are on same network
2. GCS hasn't moved endpoints
3. RPI hasn't disconnected
```

**Scripts won't run**
```powershell
# Allow script execution (Windows)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Make scripts executable (Linux)
chmod +x ./uv_run.sh
chmod +x ./uv_setup.sh
```

---

## 📚 Additional Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [PyMavLink API](https://ardupilot.org/dev/docs/mavlink-commands.html)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Scapy Tutorial](https://scapy.readthedocs.io/)

---

## ⚠️ Safety Warning

**This system controls real drone hardware. Always:**
- Test in a safe, controlled environment
- Have a manual kill switch ready
- Never test arm/disarm/takeoff without supervision
- Keep propellers OFF during testing
- Have an RC controller as backup

---

✅ Setup Complete! Your system is ready to go. 🚁
