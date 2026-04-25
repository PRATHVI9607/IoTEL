---
id: Voice Commands
tags:
  - commands
  - voice
---

# 🎤 Voice Commands

These are the commands interpreted by the **[[Laptop GCS (Ground Control Station)]]** and passed onto the **[[RPI Drone Bridge]]**.

## Flight Actions
- **"Arm"** / **"Disarm"**: Enable or disable the drone's motors safely.
- **"Takeoff"** / **"Take off"**: Initiate a 10-meter takeoff sequence.
- **"Land"**: Command the drone to land at its current position.
- **"RTL"** / **"Return"**: Send the drone back to its initial launch position.
- **"Emergency land"**: Force land immediately.
- **"Stop"** / **"Halt"**: Suspend current tasks and switch to hover mode.

## Flight Modes
- **"Stabilize"**: Manual, self-leveling mode.
- **"Loiter"** / **"Hover"**: Locks the GPS coordinate to hold strict position.
- **"Alt hold"**: Keeps a steady altitude while ignoring lateral drifts.
- **"Auto"**: Executes a pre-planned waypoint mission.
- **"Guided"**: Moves exactly to an orchestrated point.
