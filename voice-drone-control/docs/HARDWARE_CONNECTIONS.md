# Voice-Based Drone Control System - Hardware Connections

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM OVERVIEW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐         TELEMETRY         ┌──────────────┐              │
│   │              │      (WiFi/USB TTL)        │              │              │
│   │  RASPBERRY   │ ←───────────────────────→  │    LAPTOP   │              │
│   │    PI 4      │        UDP Socket         │  (GCS)      │              │
│   │              │                          │              │              │
│   └──────┬───────┘                          └──────┬───────┘              │
│          │                                          │                      │
│          │ UART                                     │                      │
│          │ (TTL 3.3V)                                │                      │
│          │                                           │                      │
│   ┌──────▼───────┐                          ┌──────▼───────┐              │
│   │   PIXHAWK    │                          │  UI/Dashboard│              │
│   │ (Flight Ctrl)│                          │  (Voice Cmd) │              │
│   └──────────────┘                          └──────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Hardware Components Required

### 1. Raspberry Pi 4 (On Drone)
- Raspberry Pi 4 (4GB or 8GB recommended)
- Micro SD Card (32GB+, Class 10)
- TTL Serial Cable (3.3V logic level)
- Power supply (USB-C, 5V 3A)
- WiFi dongle (or use built-in WiFi)
- Plastic enclosure (recommended)

### 2. Flight Controller
- **Option A:** Pixhawk 4 / Pixhawk 6X
- **Option B:** Cube (Pixhawk Cube)
- Both use MAVLink protocol

### 3. Telemetry Radio (Two Options)

#### Option A: WiFi Telemetry (Used in This Project)
- ESP8266 WiFi modules on both sides
- OR use RPI's built-in WiFi for TCP connection

#### Option B: Traditional RF Telemetry
- 433MHz/915MHz telemetry radios
- SiK Radio v3

### 4. Laptop/Ground Station
- Any laptop with Python 3.8+
- Microphone (built-in or external)
- WiFi connectivity

## UART Connections (RPI ↔ Pixhawk)

### Pixhawk 4 / Cube UART Pinout

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pixhawk Serial Ports                          │
├───────────────���─────────────────────────────────────────────────┤
│                                                                  │
│  USB    │  TELEM1  │  TELEM2  │  SERIAL4  │  GPS             │
│  ───────┼──────────┼──────────┼──────────┼─────────         │
│  │      │  │       │  │       │  │       │  │                │
│  TX ────┼── RX    │  RX     │  TX      │  TX              │
│  RX ◄───│  ── TX  │  ── TX  │  ── RX   │  ── RX           │
│  CTS ───│  ── RTS │  ── RTS │  ── RTS  │  ── RX           │
│  RTS ◄──│  ── CTS │  ── CTS │  ── CTS  │  ── TX           │
│  GND ───│  ── GND │  ── GND │  ── GND  │  ── GND          │
│                                                                  │
│  Default: TELEM1 (baud 57600), TELEM2 (baud 57600)              │
│           SERIAL4 (baud 115200)                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Raspberry Pi 4 UART Pinout (GPIO Header)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4 GPIO                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    2  ┌── 3.3V                                                 │
│    4  ┌── 5V                                                   │
│    6  ┌── GND ─────────── Connect to Pixhawk GND                 │
│    8  ┌── GPIO 14 (TXD0) ──── Connect to Pixhawk RX            │
│   10  ┌── GPIO 15 (RXD0) ──── Connect to Pixhawk TX            │
│   12  ┌── GPIO 18 ────────── Optional: RTS                      │
│   14  ┌── GPIO 15 (TXD0) ──── Optional: CTS                     │
│                                                                  │
│                  ┌────────────────┐                            │
│                  │   GPIO PINOUT   │                            │
│                  │   (Top View)   │                            │
│                  │                │                            │
│                  │  ┌────┬────┐   │                            │
│                  │  │ 3.3V│  5V │   │                            │
│                  │  ├────┼────┤   │                            │
│                  │  │GPIO│GPIO│   │                            │
│                  │  │  8 │  9 │   │                            │
│                  │  ├────┼────┤   │                            │
│                  │  │GND │GPIO│   │                            │
│                  │  │    │ 14 │   │                            │
│                  │  ├────┼────┤   │                            │
│                  │  │GPIO│GPIO│   │                            │
│                  │  │ 15 │ 18 │   │                            │
│                  │  └────┴────┘   │                            │
│                  └────────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Direct UART Connection Diagram

```
┌─────────────────┐                           ┌─────────────────┐
│                 │                           │                 │
│  RASPBERRY PI   │                           │   PIXHAWK       │
│                 │                           │                 │
│  GPIO 14 (TX) ──┼───────────────────────────┼─► RX (TELEM1)   │
│                 │     TTL Cable (3.3V)     │                 │
│  GPIO 15 (RX) ◄─┼───────────────────────────┼─◄ TX (TELEM1)   │
│                 │                           │                 │
│  GPIO 6 (GND)  ─┼───────────────────────────┼─ GND           │
│                 │                           │                 │
│     GND        ─┼───────────────────────────┼─ GND           │
│                 │                           │                 │
└─────────────────┘                           └─────────────────┘

WIRE COLOR CODE (Optional):
- Red:   3.3V (NOT connected - Pixhawk provides its own power)
- Black: GND
- Green: TX (RPI) → RX (Pixhawk)
- White: RX (RPI) → TX (Pixhawk)
```

### TTL Serial Cable Options

#### Option 1: USB-to-TTL Cable (easiest)
- FTDI FT232R USB-to-TTL cable
- OR CP2102/CH340 USB-to-TTL adapter
- Set to 3.3V (not 5V!)

**Pinout:**
```
USB TTL Adapter          Pixhawk TELEM1
──────────────         ─────────────
  TX  (Green)   ─────────────► RX
  RX  (White)  ◄───────────── TX
  GND (Black)  ────────────── GND
```

#### Option 2: Direct GPIO Connection
```
Required components:
- Jumper wires (3x female-to-female)
- Level shifter (optional if Pixhawk is 3.3V tolerant)

Connection:
RPI GPIO 14 (TXD0) ────► Pixhawk TELEM1 RX
RPI GPIO 15 (RXD0) ◄───► Pixhawk TELEM1 TX
RPI GPIO 6 (GND)   ────► Pixhawk GND
```

### Enable UART on Raspberry Pi

1. Edit `/boot/firmware/config.txt`:
```bash
sudo nano /boot/firmware/config.txt
```

2. Add at the end:
```bash
# Enable UART
enable_uart=1
dtoverlay=disable-bt
```

3. Disable Bluetooth (free up UART):
```bash
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth
```

4. Reboot:
```bash
sudo reboot
```

5. Verify:
```bash
ls -l /dev/serial0
```

## Telemetry Connection (RPI ↔ Laptop)

### Option A: WiFi Access Point (RPI as Host)

```
Raspberry Pi 4                    Laptop
┌─────────────────┐             ┌─────────────────┐
│   WiFi AP Mode   │◄───────────►│   WiFi Client   │
│                 │   WiFi       │                 │
│   SSID: DroneAP │             │   Connects to   │
│   Pass: drone123│             │   192.168.4.1   │
│   IP: 192.168.4.1              │   Port: 5760    │
└─────────────────┘             └─────────────────┘
```

### Option B: TCP Socket over WiFi

```
┌─────────────────────────────────────────────────────────────────┐
│                      TCP TELEMETRY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   RASPBERRY PI                    LAPTOP                        │
│   ┌─────────────────┐          ┌─────────────────┐              │
│   │  UDP Server    │          │  TCP Client    │               │
│   │  Port: 5760   │◄─────────►│  Port: 5760    │               │
│   │  Bind: 0.0.0.0│  TCP      │  Connect to:   │               │
│   │               │  Socket  │  RPI_IP:5760   │               │
│   └─────────────────┘          └─────────────────┘              │
│                                                                  │
│   Works over local WiFi network                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Complete Hardware Checklist

```
┌─────────────────────────────────────────────────────────────────┐
��                    COMPONENT CHECKLIST                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ON DRONE:                                                      │
│  ────────                                                       │
│  □ Raspberry Pi 4 (4GB/8GB)                                     │
│  □ Micro SD Card (32GB+)                                        │
│  □ USB-C Power Supply (5V 3A)                                   │
│  □ TTL Serial Adapter (3.3V FTDI/CP2102)                        │
│  □ Jumper wires (4x)                                            │
│  □ WiFi Dongle (if needed)                                      │
│  □ Case/Enclosure                                               │
│  □ Heat shrink (optional)                                       │
│                                                                  │
│  FLIGHT CONTROLLER:                                             │
│  ───────────────                                                │
│  □ Pixhawk 4 / Cube / Pixhawk 6X                                │
│  □ Power module                                                 │
│  □ GPS module                                                   │
│  □ RC Receiver (if manual override needed)                     │
│  □ Telemetry radio (if using RF)                               │
│                                                                  │
│  ON LAPTOP:                                                     │
│  ─────────                                                      │
│  □ Laptop with Python 3.8+                                      │
│  □ External microphone (recommended)                            │
│  □ WiFi connection                                              │
│                                                                  │
│  TOOLS:                                                         │
│  ─────                                                         │
│  □ Screwdriver set                                              │
│  □ Multimeter                                                  │
│  □ Soldering iron (optional)                                    │
│  □ Electrical tape                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Safety Precautions

⚠️ **IMPORTANT WARNINGS:**

1. **Never power Pixhawk from RPI** - Use separate power source
2. **Use 3.3V TTL** - NOT 5V, may damage flight controller
3. **Ground properly** - Connect GND between devices
4. **Test on ground first** - Never fly initially
5. **Keep manual RC ready** - For emergency override
6. **Check props removed** - When testing motors

### Power Configuration

```
┌─────────────────────────────────────────────────────────────────┐
│                       POWER SETUP                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PIXHAWK POWER (from ESC/power module):                          │
│  ┌─────────────────┐                                           │
│  │                │                                           │
│  │  ┌─────────┐   │                                           │
│  │  │  LiPo   │───┼──► Power Module ──► Pixhawk               │
│  │  │ Battery │   │                                           │
│  │  └─────────┘   │                                           │
│  │       │        │                                           │
│  │     11.1V     │                                           │
│  │     (3S)      │                                           │
│  └────────────────┘                                           │
│                                                                  │
│  RPI POWER (separate):                                          │
│  ┌─────────────────┐                                           │
│  │                │                                           │
│  │  ┌─────────┐   │                                           │
│  │  │ 5V 3A  │───┼──► USB-C ──► RPI                          │
│  │  │ Power  │   │                                           │
│  │  │Supply │   │                                           │
│  │  └─────────┘   │                                           │
│  └────────────────┘                                           │
│                                                                  │
│  SEPARATE POWER IS CRITICAL!                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Testing Procedure

1. **Step 1:** Connect RPI to Pixhawk via UART
2. **Step 2:** Configure Pixhawk TELEM1 port (baud 57600)
3. **Step 3:** Enable UART on RPI
4. **Step 4:** Test RPI ↔ Pixhawk connection
5. **Step 5:** Configure WiFi/AP on RPI
6. **Step 6:** Connect laptop via WiFi
7. **Step 7:** Test telemetry bridge
8. **Step 8:** Test voice commands
9. **Step 9:** Pre-flight checks
10. **Step 10:** First flight (props OFF)