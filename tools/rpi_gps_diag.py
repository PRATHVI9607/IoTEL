"""Upload and run GPS/system diagnostic on the RPI."""
import paramiko, time, io

IP, USER, PW = '10.182.210.137', 'prathvi', 'prathvi9607'

DIAG_SCRIPT = r"""
import sys, time
sys.path.insert(0, '/home/prathvi/IDP_2/rpi/.venv/lib/python3.13/site-packages')
from pymavlink import mavutil

UART = '/dev/ttyAMA0'
BAUD = 57600

print("Connecting to PixHawk...")
mav = mavutil.mavlink_connection(UART, baud=BAUD)
msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=15)
if not msg:
    print("ERROR: No heartbeat")
    sys.exit(1)
print(f"Connected! System {mav.target_system}")

def get_param(name):
    mav.mav.param_request_read_send(
        mav.target_system, mav.target_component,
        name.encode(), -1
    )
    r = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
    return r.param_value if r else None

def set_param(name, value):
    mav.mav.param_set_send(
        mav.target_system, mav.target_component,
        name.encode(), float(value),
        mavutil.mavlink.MAV_PARAM_TYPE_INT32
    )
    time.sleep(0.3)
    r = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
    return r.param_value if r else None

print("\n=== KEY PARAMETERS ===")
params = [
    'GPS1_TYPE', 'GPS2_TYPE', 'GPS_AUTO_CONFIG',
    'SERIAL2_PROTOCOL', 'SERIAL2_BAUD',
    'SERIAL3_PROTOCOL', 'SERIAL3_BAUD',
    'BATT_MONITOR', 'ARMING_CHECK',
    'EKF3_CHECK_SCALE', 'EK3_ENABLE',
]
vals = {}
for p in params:
    v = get_param(p)
    vals[p] = v
    print(f"  {p:<22} = {int(v) if v is not None else 'NOT FOUND'}")

# ── Auto-fix bad params ──────────────────────────────────────────────────────
fixes = []

# EKF3_CHECK_SCALE should be 100 (default), not 0 or garbage
ekf_scale = vals.get('EKF3_CHECK_SCALE')
if ekf_scale is not None and (ekf_scale < 50 or ekf_scale > 200):
    print(f"\n[AUTO-FIX] EKF3_CHECK_SCALE={int(ekf_scale)} is wrong -> setting to 100")
    set_param('EKF3_CHECK_SCALE', 100)
    fixes.append('EKF3_CHECK_SCALE = 100')

# SERIAL3_BAUD=230 means 230400 which is wrong for GPS (should be 38 = 38400)
s3_baud = vals.get('SERIAL3_BAUD')
if s3_baud is not None and s3_baud not in (38, 57, 115):
    print(f"\n[AUTO-FIX] SERIAL3_BAUD={int(s3_baud)} is unusual -> setting to 38 (38400)")
    set_param('SERIAL3_BAUD', 38)
    fixes.append('SERIAL3_BAUD = 38')

print("\n=== LIVE TELEMETRY (15s sample) ===")
mav.mav.request_data_stream_send(
    mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1
)

results = {}
deadline = time.time() + 15
while time.time() < deadline:
    msg = mav.recv_match(blocking=False)
    if not msg:
        time.sleep(0.05)
        continue
    t = msg.get_type()
    if t == 'GPS_RAW_INT':
        results['gps'] = {
            'fix': msg.fix_type,
            'sats': msg.satellites_visible,
            'lat': msg.lat / 1e7,
            'lon': msg.lon / 1e7,
            'eph': msg.eph,
        }
    elif t == 'SYS_STATUS':
        results['battery'] = {
            'voltage': msg.voltage_battery / 1000.0,
            'current': msg.current_battery / 100.0,
            'remaining': msg.battery_remaining,
        }
    elif t == 'HEARTBEAT':
        results['mode'] = mavutil.mode_string_v10(msg)
        results['armed'] = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
    elif t == 'EKF_STATUS_REPORT':
        results['ekf_flags'] = msg.flags

fix_names = {0:'NO_GPS',1:'NO_FIX',2:'2D_FIX',3:'3D_FIX',4:'DGPS',5:'RTK_FLOAT',6:'RTK_FIXED'}
gps  = results.get('gps', {})
batt = results.get('battery', {})

print(f"  GPS fix:    {fix_names.get(gps.get('fix',-1),'?')} (type {gps.get('fix','no msg')})")
print(f"  Satellites: {gps.get('sats','no msg')}")
print(f"  Lat/Lon:    {gps.get('lat','?')}, {gps.get('lon','?')}")
print(f"  Battery:    {batt.get('voltage','?')}V  {batt.get('current','?')}A  {batt.get('remaining','?')}%")
print(f"  Mode:       {results.get('mode','?')}")
print(f"  Armed:      {results.get('armed','?')}")
ekf_f = results.get('ekf_flags')
if ekf_f is not None:
    print(f"  EKF flags:  {ekf_f} (need flags & 0x1FF == 511 for full health)")
else:
    print(f"  EKF flags:  no EKF_STATUS_REPORT received")

print("\n=== DIAGNOSIS ===")
fix = gps.get('fix', -1)
sats = gps.get('sats', 0)

if 'gps' not in results:
    print("  [PROBLEM] No GPS_RAW_INT message received at all")
    print("  [CHECK]   GPS module not connected or not powered")
elif fix == 0:
    print("  [PROBLEM] GPS module not detected (fix_type=0, no module)")
    print("  [CHECK]   Reseat GPS connector on GPS1 port")
    print("  [CHECK]   Try power cycling")
elif fix < 3:
    print(f"  [WARN]    GPS detected ({sats} sats) but no 3D fix yet")
    if sats == 0:
        print("  [CHECK]   Are you outdoors with clear sky view?")
        print("  [CHECK]   GPS antenna pointing up, not blocked by metal")
    else:
        print(f"  [INFO]    {sats} sats visible — wait 1-2 min for lock")
else:
    print(f"  [OK]      GPS {fix_names[fix]} with {sats} satellites")

if batt.get('voltage', 0) < 0.5:
    print("  [WARN]    Battery voltage very low/zero — no flight battery connected?")
else:
    print(f"  [OK]      Battery at {batt.get('voltage')}V")

if fixes:
    print(f"\n  [AUTO-FIXED] {', '.join(fixes)}")
    print("  [ACTION]  Reboot PixHawk to apply GPS baud change")
"""

print("Connecting to RPI...")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(IP, username=USER, password=PW, timeout=15)

print("Uploading script...")
sftp = c.open_sftp()
sftp.putfo(io.BytesIO(DIAG_SCRIPT.encode()), '/tmp/gps_diag.py')
sftp.close()

print("Running diagnostic (20s)...\n" + "="*50)
_, o, e = c.exec_command(
    'cd ~/IDP_2/rpi && /home/prathvi/.local/bin/uv run python /tmp/gps_diag.py',
    timeout=90
)
out = o.read().decode('utf-8', errors='replace')
err = e.read().decode('utf-8', errors='replace')
print(out)
errs = [l for l in err.splitlines() if l.strip() and 'warning' not in l.lower()]
if errs:
    print('[stderr]', '\n'.join(errs[:10]))
c.close()
