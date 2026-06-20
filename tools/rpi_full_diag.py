"""
Full diagnostic: GPS + Battery + Serial config via RPi -> Pixhawk Cube.
Setup: RPi UART -> Cube TELEM2 (SERIAL2), GPS on GPS1 (SERIAL3), Battery on POWER1.
"""
import paramiko, io

IP, USER, PW = '172.16.172.137', 'prathvi', 'prathvi9607'

DIAG = r"""
import sys, time
sys.path.insert(0, '/home/prathvi/IDP_2/rpi/.venv/lib/python3.13/site-packages')
from pymavlink import mavutil

print("Connecting to Pixhawk Cube via /dev/ttyAMA0 (TELEM2)...")
mav = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)
hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=20)
if not hb:
    print("ERROR: No HEARTBEAT — check UART wiring and SERIAL2_PROTOCOL")
    sys.exit(1)
print(f"Connected! System {mav.target_system}  Component {mav.target_component}\n")

def get_param(name):
    mav.mav.param_request_read_send(mav.target_system, mav.target_component, name.encode(), -1)
    r = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=4)
    return r.param_value if r else None

def set_param(name, value, ptype=None):
    import mavutil as _m
    pt = ptype or mavutil.mavlink.MAV_PARAM_TYPE_REAL32
    mav.mav.param_set_send(mav.target_system, mav.target_component, name.encode(), float(value), pt)
    time.sleep(0.4)
    r = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=4)
    if r:
        print(f"  [SET] {name} -> {r.param_value}")
    return r.param_value if r else None

# ── 1. Dump all relevant params ──────────────────────────────────────────────
PARAMS = [
    # Serial / TELEM2 (RPi connection)
    'SERIAL2_PROTOCOL', 'SERIAL2_BAUD',
    # GPS port — GPS1 = SERIAL3 on Cube
    'SERIAL3_PROTOCOL', 'SERIAL3_BAUD',
    # GPS config
    'GPS1_TYPE', 'GPS2_TYPE', 'GPS_AUTO_CONFIG',
    # Battery
    'BATT_MONITOR', 'BATT_VOLT_PIN', 'BATT_CURR_PIN',
    'BATT_VOLT_MULT', 'BATT_AMP_PERVLT', 'BATT_CAPACITY',
    'BATT2_MONITOR',
    # Arming / EKF
    'ARMING_CHECK', 'EK3_ENABLE', 'EKF3_CHECK_SCALE',
]

print("=== PARAMETER DUMP ===")
vals = {}
for p in PARAMS:
    v = get_param(p)
    vals[p] = v
    if v is not None:
        print(f"  {p:<24} = {v:.0f}")
    else:
        print(f"  {p:<24} = NOT FOUND")

# ── 2. Auto-fix known bad values ─────────────────────────────────────────────
print("\n=== AUTO-FIX ===")
fixes = []

# SERIAL2 must be MAVLink (1=MAVLink1, 2=MAVLink2) for RPi connection
s2_proto = vals.get('SERIAL2_PROTOCOL')
if s2_proto is not None and s2_proto not in (1, 2):
    print(f"  [FIX] SERIAL2_PROTOCOL={int(s2_proto)} is wrong (needs 1 or 2) -> setting 2")
    set_param('SERIAL2_PROTOCOL', 2)
    fixes.append('SERIAL2_PROTOCOL=2')
elif s2_proto in (1, 2):
    print(f"  [OK]  SERIAL2_PROTOCOL={int(s2_proto)} (MAVLink)")

# SERIAL2 baud must match RPi side (57 = 57600)
s2_baud = vals.get('SERIAL2_BAUD')
if s2_baud is not None and s2_baud != 57:
    print(f"  [FIX] SERIAL2_BAUD={int(s2_baud)} -> setting 57 (57600)")
    set_param('SERIAL2_BAUD', 57)
    fixes.append('SERIAL2_BAUD=57')
elif s2_baud == 57:
    print(f"  [OK]  SERIAL2_BAUD=57 (57600)")

# SERIAL3 must be GPS protocol (5)
s3_proto = vals.get('SERIAL3_PROTOCOL')
if s3_proto is not None and s3_proto != 5:
    print(f"  [FIX] SERIAL3_PROTOCOL={int(s3_proto)} -> setting 5 (GPS)")
    set_param('SERIAL3_PROTOCOL', 5)
    fixes.append('SERIAL3_PROTOCOL=5')
elif s3_proto == 5:
    print(f"  [OK]  SERIAL3_PROTOCOL=5 (GPS)")

# SERIAL3 baud — most u-blox modules default 38400 (38); some need 115
s3_baud = vals.get('SERIAL3_BAUD')
if s3_baud is not None and s3_baud not in (38, 115):
    print(f"  [FIX] SERIAL3_BAUD={int(s3_baud)} is unusual -> setting 38 (38400)")
    set_param('SERIAL3_BAUD', 38)
    fixes.append('SERIAL3_BAUD=38')
elif s3_baud in (38, 115):
    print(f"  [OK]  SERIAL3_BAUD={int(s3_baud)}")

# GPS1_TYPE must be non-zero
gps_type = vals.get('GPS1_TYPE')
if gps_type is not None and gps_type == 0:
    print(f"  [FIX] GPS1_TYPE=0 (disabled!) -> setting 1 (AUTO)")
    set_param('GPS1_TYPE', 1)
    fixes.append('GPS1_TYPE=1')
elif gps_type:
    print(f"  [OK]  GPS1_TYPE={int(gps_type)}")

# GPS_AUTO_CONFIG should be 1
gac = vals.get('GPS_AUTO_CONFIG')
if gac is not None and gac != 1:
    print(f"  [FIX] GPS_AUTO_CONFIG={int(gac)} -> setting 1")
    set_param('GPS_AUTO_CONFIG', 1)
    fixes.append('GPS_AUTO_CONFIG=1')
elif gac == 1:
    print(f"  [OK]  GPS_AUTO_CONFIG=1")

# BATT_MONITOR — 4=Analog V+I (standard power module on POWER1)
bm = vals.get('BATT_MONITOR')
if bm is not None and bm == 0:
    print(f"  [FIX] BATT_MONITOR=0 (disabled!) -> setting 4")
    set_param('BATT_MONITOR', 4)
    fixes.append('BATT_MONITOR=4')
elif bm:
    print(f"  [OK]  BATT_MONITOR={int(bm)}")

# EKF3_CHECK_SCALE — should be 100, not 0
ekf_scale = vals.get('EKF3_CHECK_SCALE')
if ekf_scale is not None and ekf_scale < 50:
    print(f"  [FIX] EKF3_CHECK_SCALE={int(ekf_scale)} -> setting 100")
    set_param('EKF3_CHECK_SCALE', 100)
    fixes.append('EKF3_CHECK_SCALE=100')
elif ekf_scale and ekf_scale >= 50:
    print(f"  [OK]  EKF3_CHECK_SCALE={int(ekf_scale)}")

if not fixes:
    print("  No param fixes needed.")

# ── 3. Live telemetry sample (20s) ───────────────────────────────────────────
print("\n=== LIVE TELEMETRY (20s sample) ===")
mav.mav.request_data_stream_send(
    mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1
)

results = {}
deadline = time.time() + 20
while time.time() < deadline:
    msg = mav.recv_match(blocking=False)
    if not msg:
        time.sleep(0.05)
        continue
    t = msg.get_type()
    if t == 'GPS_RAW_INT':
        results['gps'] = {'fix': msg.fix_type, 'sats': msg.satellites_visible,
                          'lat': msg.lat/1e7, 'lon': msg.lon/1e7, 'eph': msg.eph}
    elif t == 'SYS_STATUS':
        results['sys'] = {'voltage': msg.voltage_battery, 'current': msg.current_battery,
                          'remaining': msg.battery_remaining}
    elif t == 'BATTERY_STATUS':
        v0 = msg.voltages[0] if msg.voltages[0] != 65535 else 0
        results['batt'] = {'voltage': v0, 'current': msg.current_battery,
                           'remaining': msg.battery_remaining}
    elif t == 'POWER_STATUS':
        results['pwr'] = {'Vcc': msg.Vcc, 'Vservo': msg.Vservo, 'flags': msg.flags}
    elif t == 'HEARTBEAT':
        results['mode'] = mavutil.mode_string_v10(msg)
        results['armed'] = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
    elif t == 'EKF_STATUS_REPORT':
        results['ekf'] = msg.flags

# ── 4. Print results ─────────────────────────────────────────────────────────
fix_names = {0:'NO_GPS',1:'NO_FIX',2:'2D_FIX',3:'3D_FIX',4:'DGPS',5:'RTK_FLOAT',6:'RTK_FIXED'}

gps_r  = results.get('gps', {})
sys_r  = results.get('sys', {})
batt_r = results.get('batt', {})
pwr_r  = results.get('pwr', {})

print(f"\n  GPS fix:      {fix_names.get(gps_r.get('fix',-1),'?')} (type {gps_r.get('fix','no msg')})")
print(f"  Satellites:   {gps_r.get('sats','no msg')}")
print(f"  Lat/Lon:      {gps_r.get('lat','?')} , {gps_r.get('lon','?')}")

print(f"\n  Battery (SYS_STATUS):    {sys_r.get('voltage','no msg')} mV  |  {sys_r.get('current','no msg')} cA  |  {sys_r.get('remaining','no msg')}%")
print(f"  Battery (BATTERY_STATUS): {batt_r.get('voltage','no msg')} mV  |  {batt_r.get('current','no msg')} cA  |  {batt_r.get('remaining','no msg')}%")

flags = pwr_r.get('flags', None)
if flags is not None:
    print(f"\n  POWER_STATUS Vcc:     {pwr_r.get('Vcc')} mV")
    print(f"  POWER_STATUS Vservo:  {pwr_r.get('Vservo')} mV")
    print(f"  USB power:            {bool(flags & 0x1)}")
    print(f"  POWER1 brick valid:   {bool(flags & 0x2)}")
    print(f"  POWER2 brick valid:   {bool(flags & 0x4)}")
else:
    print("\n  POWER_STATUS: no message received")

print(f"\n  Mode:  {results.get('mode','?')}")
print(f"  Armed: {results.get('armed','?')}")

ekf_f = results.get('ekf')
if ekf_f is not None:
    ekf_healthy = (ekf_f & 0x1FF) == 0x1FF
    print(f"  EKF flags: {ekf_f}  ({'HEALTHY' if ekf_healthy else 'NOT READY — needs GPS fix outdoors'})")
else:
    print("  EKF: no EKF_STATUS_REPORT received")

# ── 5. Diagnosis ─────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("DIAGNOSIS")
print("="*50)

# GPS
fix = gps_r.get('fix', -1)
sats = gps_r.get('sats', 0)
if 'gps' not in results:
    print("[GPS] PROBLEM: No GPS_RAW_INT message at all")
    print("      -> Check GPS1_TYPE != 0 and SERIAL3_PROTOCOL=5")
    print("      -> Reseat GPS connector on GPS1 port")
elif fix == 0:
    print("[GPS] PROBLEM: fix_type=0 — module not detected by Pixhawk")
    print("      -> Reseat GPS connector, try power-cycling Cube")
    print("      -> Confirm GPS_AUTO_CONFIG=1, GPS1_TYPE=1")
elif fix < 3:
    print(f"[GPS] WAITING: Module found, {sats} sats, no 3D lock yet (fix={fix})")
    print("      -> Go outdoors with clear sky view")
    print("      -> Wait 1-2 min, antenna face-up, away from metal")
else:
    print(f"[GPS] OK: {fix_names[fix]} with {sats} satellites")

# Battery
volt_sys = sys_r.get('voltage', 0) or 0
brick1 = bool(flags & 0x2) if flags is not None else None

if 'sys' not in results and 'batt' not in results:
    print("[BATT] PROBLEM: No battery messages at all")
    print("       -> Set BATT_MONITOR=4 in Mission Planner, reboot")
elif volt_sys < 100:
    if brick1 is False:
        print("[BATT] PROBLEM: voltage=0 AND POWER1 brick not detected")
        print("       -> The 6-pin GH cable from power module is NOT plugged into POWER1")
        print("       -> Plug PM02/PM07 6-pin cable -> POWER1 on Cube")
    elif brick1 is True:
        print("[BATT] PROBLEM: POWER1 connected but voltage reads 0")
        print("       -> Check BATT_VOLT_MULT (set ~18.182 for Holybro PM02)")
        print("       -> Check BATT_VOLT_PIN=2, BATT_CURR_PIN=3 for Cube POWER1")
    else:
        print("[BATT] PROBLEM: voltage=0, cannot read POWER_STATUS")
        print("       -> Confirm BATT_MONITOR=4, plug 6-pin PM cable into POWER1")
else:
    print(f"[BATT] OK: {volt_sys/1000:.2f}V from SYS_STATUS")

# ARMING_CHECK summary
ac = vals.get('ARMING_CHECK', -1)
if ac == 0:
    print("[ARM]  ARMING_CHECK=0 — all checks disabled (bench/test mode)")
elif ac is not None:
    print(f"[ARM]  ARMING_CHECK={int(ac)} — some checks active (normal for flight)")

if fixes:
    print(f"\n[FIXED] Applied {len(fixes)} param fix(es): {', '.join(fixes)}")
    print("[ACTION] Reboot the Pixhawk Cube to apply SERIAL changes")
else:
    print("\n[PARAMS] All checked params look correct")
"""

print("Connecting to RPi...")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(IP, username=USER, password=PW, timeout=15)

# Kill anything holding the UART first
print("Clearing /dev/ttyAMA0...")
_, o, _ = c.exec_command(f'echo {PW} | sudo -S fuser -k /dev/ttyAMA0 2>/dev/null; sleep 1; echo cleared')
print(o.read().decode().strip())

# Upload and run
sftp = c.open_sftp()
sftp.putfo(io.BytesIO(DIAG.encode()), '/tmp/full_diag.py')
sftp.close()

print("Running full diagnostic (30s)...\n" + "="*60)
_, o, e = c.exec_command(
    'cd ~/IDP_2/rpi && /home/prathvi/.local/bin/uv run python /tmp/full_diag.py',
    timeout=120
)
print(o.read().decode('utf-8', errors='replace'))
errs = [l for l in e.read().decode('utf-8', errors='replace').splitlines()
        if l.strip() and 'warning' not in l.lower()]
if errs:
    print('[stderr]', '\n'.join(errs[:10]))
c.close()
