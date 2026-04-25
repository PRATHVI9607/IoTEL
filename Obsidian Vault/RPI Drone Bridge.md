---
id: RPI Drone Bridge
tags:
  - raspberry-pi
  - onboard
  - software
---

# 🍓 RPI Drone Bridge

The Raspberry Pi runs on the drone, directly attached to the Pixhawk via UART.

## Code Structure
Located in `rpi/rpi_drone_bridge.py`.

## Responsibilities
- Receives MAVLink telemetry from the **[[Hardware Setup]]** via UART on `/dev/ttyAMA0` or `/dev/serial0`.
- Broadcasts telemetry stream out to the **[[Laptop GCS (Ground Control Station)]]** via Wi-Fi.
- Modifies drone behavior through the `dronekit`, `pymavlink` and `pyserial` libraries upon request from the user.

## Running the Code
```bash
sudo python3 rpi_drone_bridge.py --ip 192.168.1.100 --baud 57600
```
*(Wait for Laptop IP connection or run standalone)*
