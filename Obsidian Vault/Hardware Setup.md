---
id: Hardware Setup
tags:
  - hardware
  - wiring
---

# 🔌 Hardware Setup

For a full list of parts and strict warnings, please make sure to read this carefully.

## Core Components
- **Flight Controller**: Pixhawk 4 / Pixhawk 6X / Cube.
- **Companion Computer**: Raspberry Pi 4 (onboard).
- **Power**: **CRITICAL** - You must use separate power sources for the RPI (5V 3A via USB-C) and the Pixhawk (LiPo + Power module). 

## RPI ↔ Pixhawk Connection

| Raspberry Pi 4 | Pixhawk (TELEM1) |
|----------------|------------------|
| GPIO 14 (TX)   | RX               |
| GPIO 15 (RX)   | TX               |
| GND            | GND              |

**Note**: You must use **3.3V TTL logic**. NEVER power the Pixhawk from the RPI!

For more software context on how UART is opened, see the **[[RPI Drone Bridge]]** documentation.
