# Voice Drone Control System - Hardware Connections

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  SYSTEM OVERVIEW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                          │
│   ┌──────────┐       TELEMETRY        ┌──────────┐          │
│   │         │      (TCP/WiFi)        │         │          │
│   │  RPI 4  │ ◄───────────────────► │  LAPTOP │          │
│   │ (Drone) │      UDP Socket       │  (GCS) │          │
│   │         │                      │         │          │
│   └────┬────┘                      └────┬────┘          │
│        │  UART (TTL 3.3V)               │                │
│        │                                │                │
│   ┌────▼────┐                      ┌────▼────┐          │
│   │PIXHAWK │                      │Dashboard│          │
│   │   ✓   │                      │  (UI)   │          │
│   └───────┘                        └─────────┘          │
│                                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## Hardware Components Required

### On the Drone (RPI Side)

| Component | Description | Notes |
|-----------|-------------|-------|
| Raspberry Pi 4 | 4GB or 8GB | Recommended 8GB |
| Micro SD Card | 32GB+ Class 10 | With Raspberry Pi OS Lite |
| USB-C Power | 5V 3A | **Separate from Pixhawk** |
| TTL Serial Cable | FT232R/CP2102 | **Must be 3.3V logic** |
| Jumper Wires | 4x female-female | For GPIO connection |
| WiFi (optional) | Built-in or dongle | For telemetry |

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
| Microphone | Built-in or external | For voice |
| WiFi | For RPI connection | |

---

## UART Connections (RPI ↔ Pixhawk)

### Pinout Reference

#### Raspberry Pi 4 GPIO Header

```
    3.3V  (1) (2)  5V
    SDA   (3) (4)  5V
    SCL   (5) (6)  GND
   GPIO4  (7) (8)  GPIO 14 (TX) ◄──────► Pixhawk RX
   GND    (9) (10) GPIO 15 (RX) ◄──────► Pixhawk TX
   GPIO18 (11)(12) GPIO 18
   GPIO21 (13)(14) GND
    MOSI  (15)(16) GPIO 21
    MISO  (17)(18) GPIO 22
    SCLK  (19)(20) GND
    CE1   (21)(22) CE0
    MOSI  (23)(24) SCLK
    GND   (25)(26) CE0
```

**IMPORTANT: Use GPIO 14 (TX) and GPIO 15 (RX)**

#### Connection Diagram

```
Raspberry Pi 4              Pixhawk (TELEM1/TELEM2)
─────────────              ─────────────────
                                  
GPIO 14 (TX)  ─────────────────────────►  RX
GPIO 15 (RX)  ◄─────────────────────────  TX
GPIO 6 (GND)  ──────────────────────────  GND
     GND      ──────────────────────────  GND
```

#### TTL Serial Cable (Alternative)

```
USB TTL Adapter           Pixhawk TELEM1
──────────────        ─────────────
  TX (Green)   ─────────────► RX
  RX (White)  ◄───────────── TX
  GND (Black) ────────────── GND
```

---

## Enable UART on Raspberry Pi

### Method 1: Boot Config

```bash
sudo nano /boot/firmware/config.txt
```

Add at the end:
```bash
enable_uart=1
dtoverlay=disable-bt
```

### Method 2: Disable Bluetooth

```bash
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth
```

### Method 3: Verify

```bash
ls -l /dev/serial0
```

Should show: `/dev/serial0 -> ttyAMA0` or `/dev/serial0 -> ttyS0`

---

## Pixhawk Configuration

### Via Mission Planner / QGroundControl

1. Connect Pixhawk via USB
2. Go to **Parameters**
3. Set **SERIAL0_BAUD** = 57600 (or TELEM1)
4. Set **SERIAL0_PROTOCOL** = 1 (MAVLink)
5. Click **Save** and reboot

### Serial Port Options

| Port | Default Baud | Purpose |
|------|------------|---------|
| SERIAL0 | 57600 | USB |
| TELEM1 | 57600 | Primary Telemetry |
| TELEM2 | 57600 | Secondary Telemetry |
| SERIAL4 | 115200 | Debug |

---

## Telemetry Connection (RPI ↔ Laptop)

### Option A: Direct WiFi (RPI as AP)

```
RPI 4                    Laptop
──────────              ──────
 WiFi AP                WiFi Client
 SSID: DroneAP          Connects to
 Pass: drone123          192.168.4.1
 IP: 192.168.4.1       Port: 5760
```

### Option B: Same Network

```
RPI 4                    Laptop
──────────              ──────
 Same WiFi              Same WiFi
 RPI_IP: 192.168.1.XX   Connect to
 Port: 5760             RPI_IP:5760
```

### Option C: Ethernet Direct

```
RPI 4                    Laptop
──────────              ──────
 Ethernet               Ethernet
 RPI_IP: 192.168.1.X    Connect to
 Port: 5760             RPI_IP:5760
```

---

## Network Configuration

### Set Static IP (RPI)

```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```bash
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8
```

### Connect to WiFi (RPI)

```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Add:
```bash
network={
    ssid="YourWiFiNetwork"
    psk="YourPassword"
}
```

```bash
sudo wpa_cli reconfigure
```

---

## Power Configuration

### ⚠️ CRITICAL: Separate Power

```
┌─────────────────────────────────────┐
│         POWER SETUP                  │
├─────────────────────────────────────┤
│                                     │
│  PIXHAWK (from battery/ESCs):       │
│  ┌─────────┐                        │
│  │ LiPo   │──► Power Module ──► Pixhawk│
│  │Battery │                        │
│  └─────────┘                        │
│       11.1V (3S)                  │
│                                     │
│  RPI (separate):                    │
│  ┌─────────┐                        │
│  │ 5V 3A  │──► USB-C ──► RPI      │
│  │ Power  │                        │
│  └─────────┘                        │
│                                     │
│  ⚠️ NEVER power RPI from Pixhawk!   │
│                                     │
└─────────────────────────────────────┘
```

---

## Complete Wiring Checklist

```
┌─────────────────────────────────────┐
│      COMPONENT CHECKLIST              │
├─────────────────────────────────────┤
│                                     │
│  ON DRONE:                         │
│  □ Raspberry Pi 4                   │
│  □ 32GB+ microSD                   │
│  □ USB-C power (5V 3A)             │
│  □ TTL cable (3.3V)                │
│  □ Jumper wires                    │
│  □ Case (optional)                  │
│                                     │
│  FLIGHT CONTROLLER:                  │
│  □ Pixhawk 4/6X or Cube           │
│  □ Power module                    │
│  □ GPS module                     │
│  □ RC receiver (optional)           │
│                                     │
│  ON LAPTOP:                        │
│  □ Laptop (Python 3.8+)             │
│  □ Microphone                     │
│  □ WiFi connection                 │
│                                     │
│  TOOLS:                           │
│  □ Multimeter                     │
│  □ Screwdriver set                 │
│  □ Electrical tape                │
│                                     │
└─────────────────────────────────────┘
```

---

## Testing Procedure

### Step 1: UART Test

```bash
# On RPI, test UART
ls -l /dev/serial0
# Should show: lrwxrwxrwx 1 root root ... serial0 -> ttyAMA0

# Test read
cat /dev/serial0
# Should see MAVLink data if Pixhawk connected
```

### Step 2: Connection Test

```bash
# On RPI, test laptop connection
ping 192.168.1.100

# On laptop, test RPI
ping 192.168.1.100  # or your RPI IP
```

### Step 3: Full Test

```bash
# RPI - run monitor
sudo python3 rpi_drone_bridge.py

# Laptop - run GCS  
python laptop_gcs.py

# Open browser: http://localhost:5000
```

---

## Safety Precautions

⚠️ **IMPORTANT WARNINGS:**

1. **Never power Pixhawk from RPI** - Use separate power source
2. **Use 3.3V TTL** - Not 5V! May damage flight controller
3. **Ground properly** - Connect GND between devices
4. **Props OFF for testing** - Always remove props initially
5. **Keep RC ready** - For manual emergency override
6. **Test on ground first** - Before first flight

### Pre-Flight Checklist

- [ ] Props removed
- [ ] Battery charged
- [ ] GPS lock acquired (satellites ≥ 6)
- [ ] RC controller ready
- [ ] Clear line of sight
- [ ] Safety area identified

---

## Troubleshooting

### UART Not Found

```bash
# Check if UART is enabled
ls -l /dev/serial0

# If not, enable it
sudo raspi-config
# → Interface Options → Serial Port → Enable
```

### Permission Denied

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and back in
```

### Connection Refused

```bash
# Check if service is running on RPI
systemctl status dronebridge

# Check logs
journalctl -u dronebridge -f
```

### Firewall Blocking

```bash
# On RPI, Allow port
sudo ufw allow 5760/tcp
sudo ufw allow 5000/tcp
```