# IoTEL Drone Bridge Setup Template

Complete setup guide for RPi → Pixhawk Cube telemetry bridge with GPS/battery monitoring.

---

## Phase 1: Hardware & Network Setup

### 1.1 Physical Connections
- **RPi GPIO 14 (TX) → Pixhawk TELEM2 RX**
- **RPi GPIO 15 (RX) → Pixhawk TELEM2 TX**
- **GND → GND**
- Verify UART on RPi: `ls -la /dev/ttyAMA0`

### 1.2 Network Discovery
```bash
# Find RPi on network
nmap -sn 172.16.0.0/16  # or your subnet

# SSH into RPi
ssh prathvi@172.16.172.137  # update IP as needed
```

### 1.3 Verify Serial Port
```bash
# On RPi
lsof /dev/ttyAMA0  # check if port is free
stty -F /dev/ttyAMA0 57600  # set baud rate
```

---

## Phase 2: Software Installation

### 2.1 On RPi
```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project venv
cd ~/IDP_2/rpi
uv venv
source .venv/bin/activate

# Install dependencies
uv add pymavlink
uv add pyserial
uv add future
```

### 2.2 On Laptop (MAVProxy testing)
```bash
pip install MAVProxy pymavlink future
```

---

## Phase 3: Pixhawk Parameter Configuration

**Critical Parameters** (verify via MAVProxy or Mission Planner):

| Parameter | Value | Purpose |
|-----------|-------|---------|
| SERIAL2_PROTOCOL | 2 | MAVLink on TELEM2 |
| SERIAL2_BAUD | 57 | 57600 baud (encoded as 57) |
| SERIAL3_PROTOCOL | 5 | GPS on TELEM1 |
| SERIAL3_BAUD | 38 | 38400 baud |
| GPS1_TYPE | 1 | u-blox GPS |
| GPS_AUTO_CONFIG | 1 | Auto-config GPS |
| BATT_MONITOR | 4 | Analog voltage + current |
| BATT_VOLT_PIN | 0 | Pin A0 |
| BATT_CURR_PIN | 1 | Pin A1 |
| EKF3_CHECK_SCALE | 100 | EKF health |

**Verify via MAVProxy:**
```bash
mavproxy.py --master=/dev/ttyAMA0 --baudrate=57600 --console
param fetch-all
param show SERIAL2_*
```

---

## Phase 4: Core Bridge Architecture

### 4.1 DroneBridge Class (Python)

```python
import threading
from pymavlink import mavutil
from typing import Dict, Any

class DroneBridge:
    def __init__(self, port, baud=57600):
        self.mav = mavutil.mavlink_connection(port, baud=baud)
        self.running = True
        self._msg_cache = {}
        self._msg_lock = threading.Lock()
        self._gps_ever_fixed = False
        
        # Start background recv thread
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()
        
        # Wait for first heartbeat
        hb = self.mav.recv_match(type='HEARTBEAT', blocking=True, timeout=10)
        if not hb:
            raise RuntimeError("No HEARTBEAT from Pixhawk")
    
    def _recv_loop(self):
        """Background thread: continuously read MAVLink messages into cache."""
        while self.running:
            try:
                msg = self.mav.recv_match(blocking=True, timeout=1)
                if msg is None:
                    continue
                with self._msg_lock:
                    self._msg_cache[msg.get_type()] = msg
            except Exception:
                break
    
    def _get_msg(self, msg_type):
        """Fetch latest cached message of given type."""
        with self._msg_lock:
            return self._msg_cache.get(msg_type)
    
    def get_telemetry(self) -> Dict[str, Any]:
        """Extract telemetry from cached messages."""
        sys_status = self._get_msg('SYS_STATUS')
        batt = self._get_msg('BATTERY_STATUS')
        gps = self._get_msg('GPS_RAW_INT')
        
        # Battery
        batt_v = sys_status.voltage_battery / 1000.0 if sys_status else 0
        batt_pct = sys_status.battery_remaining if sys_status else 0
        
        # GPS
        if gps and gps.fix_type >= 3:  # 3D fix or better
            self._gps_ever_fixed = True
        
        fix_types = ['NO_GPS', 'NO_FIX', '2D_FIX', '3D_FIX', 'DGPS', 'RTK_FLOAT', 'RTK_FIXED']
        fix_str = fix_types[gps.fix_type] if gps else 'UNKNOWN'
        
        lat = gps.lat / 1e7 if gps else 0
        lon = gps.lon / 1e7 if gps else 0
        sats = gps.satellites_visible if gps else 0
        
        return {
            'battery_voltage': batt_v,
            'battery_level': batt_pct,
            'gps_fix': fix_str,
            'gps_sats': sats,
            'gps_lat': lat,
            'gps_lon': lon,
        }
    
    def close(self):
        self.running = False
        self._recv_thread.join(timeout=2)
```

### 4.2 Main Loop Example

```python
from rpi_drone_bridge import DroneBridge
import time

bridge = DroneBridge('/dev/ttyAMA0', baud=57600)

try:
    while True:
        telem = bridge.get_telemetry()
        print(f"[BATT] {telem['battery_voltage']:.2f}V {telem['battery_level']}%  "
              f"[GPS] {telem['gps_fix']} sats={telem['gps_sats']} "
              f"lat={telem['gps_lat']:.6f} lon={telem['gps_lon']:.6f}")
        time.sleep(1)
except KeyboardInterrupt:
    bridge.close()
```

---

## Phase 5: Diagnostic Tools

### 5.1 Full Diagnostic (`rpi_full_diag.py`)
- Checks all critical Pixhawk parameters
- Auto-fixes common misconfigurations
- Samples 20s of live telemetry
- Reports GPS fix status, satellite count, battery voltage

**Usage:**
```bash
python tools/rpi_full_diag.py
```

### 5.2 GPS-Only Diagnostic (`rpi_gps_diag.py`)
- Verifies GPS1_TYPE, SERIAL3_PROTOCOL/BAUD
- Auto-configures if wrong
- Samples GPS_RAW_INT for 15s
- Reports fix type, sat count, coordinates

### 5.3 Battery-Only Diagnostic (`rpi_batt_diag.py`)
- Checks BATT_MONITOR setting
- Reads SYS_STATUS, BATTERY_STATUS, POWER_STATUS
- Verifies power module connectivity

---

## Phase 6: Common Issues & Fixes

### Issue 1: No HEARTBEAT at any baud rate
**Cause:** Another process holding UART (e.g., stale bridge process)
```bash
# Kill existing process
sudo fuser -k /dev/ttyAMA0
```

### Issue 2: GPS always reads zero despite working hardware
**Cause:** Sequential `recv_match()` calls discard non-matching messages
**Fix:** Use background daemon thread with message cache (see Phase 4.1)

### Issue 3: False positive GPS alerts indoors
**Cause:** No fix ever acquired, but alert fires on ANY fix change
**Fix:** Add `_gps_ever_fixed` flag, only alert on state transitions after first fix

### Issue 4: Network unreachable to RPi
**Cause:** WiFi subnet changed or IP reassigned
**Fix:** Scan subnet, update connection IP
```bash
nmap -sn 172.16.0.0/16 | grep -i rpi
```

### Issue 5: MAVProxy missing dependencies
**Error:** `ModuleNotFoundError: No module named 'future'`
**Fix:** Install on RPi
```bash
uv add future
```

---

## Phase 7: Testing Checklist

- [ ] Serial port accessible on RPi: `/dev/ttyAMA0` at 57600 baud
- [ ] Pixhawk parameters set (SERIAL2/3_PROTOCOL, GPS1_TYPE, BATT_MONITOR)
- [ ] MAVProxy connects and shows HEARTBEAT
- [ ] Full diagnostic runs without errors
- [ ] GPS reports fix type, satellites, coordinates
- [ ] Battery reports voltage and percentage
- [ ] Background recv thread active and caching messages
- [ ] Main telemetry loop prints stable values

---

## Phase 8: GPS Spoofing Demo (Optional)

For testing EKF behavior with fake GPS:

```bash
# Via MAVProxy console:
mavproxy.py --master=/dev/ttyAMA0 --baudrate=57600 --console
gps set 1.352 103.82  # Spoof Singapore coords
gps status
```

Or via Python script sending MAVLink GPS_INPUT messages.

---

## Phase 9: Project File Structure

```
MyProject/
├── rpi/
│   ├── rpi_drone_bridge.py       # Main bridge (DroneBridge class)
│   ├── arm.py, arm1.py, arm3.py  # Arming helpers
│   └── .venv/                     # Python venv
├── tools/
│   ├── rpi_full_diag.py          # Full diagnostic
│   ├── rpi_gps_diag.py           # GPS diagnostic
│   └── rpi_batt_diag.py          # Battery diagnostic
├── laptop/
│   └── mavproxy_test.py          # Testing script
└── SETUP_TEMPLATE.md             # This file
```

---

## Phase 10: Git Workflow

```bash
# On RPi
git init
git add -A
git commit -m "initial: RPi bridge + diagnostics"
git remote add origin <your-repo>
git push -u origin main

# On Laptop
git clone <your-repo>
git checkout -b hikki  # feature branch
# ... make changes ...
git push -u origin hikki

# Back on RPi
git pull origin hikki
```

---

## Key Learnings

1. **Never use sequential recv_match() for multiple message types** — use background thread + cache
2. **GPS takes time to fix** — suppress alerts until first fix acquired
3. **UART can hang** — always check `lsof /dev/ttyAMA0` before assuming connection failed
4. **Parameter misconfigurations are silent** — use diagnostic tools to verify before debugging
5. **MAVProxy is invaluable** — use it to confirm Pixhawk transmitting expected messages

---

**Last Updated:** 2026-06-20  
**Status:** Production-ready template with all fixes applied
