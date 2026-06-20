"""Reboot PixHawk via MAVLink, then re-check GPS after boot."""
import paramiko, time, io

IP, USER, PW = '10.182.210.137', 'prathvi', 'prathvi9607'

SCRIPT = r"""
import sys, time
sys.path.insert(0, '/home/prathvi/IDP_2/rpi/.venv/lib/python3.13/site-packages')
from pymavlink import mavutil

mav = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)
mav.recv_match(type='HEARTBEAT', blocking=True, timeout=15)
print(f"Connected to System {mav.target_system}")

print("Sending PixHawk reboot command...")
mav.mav.command_long_send(
    mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
    0,
    1, 0, 0, 0, 0, 0, 0  # param1=1 means reboot autopilot
)
time.sleep(1)
print("Reboot sent. Waiting 10s for PixHawk to come back...")
time.sleep(10)

# Reconnect and check GPS
print("Reconnecting...")
mav2 = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)
hb = mav2.recv_match(type='HEARTBEAT', blocking=True, timeout=20)
if not hb:
    print("ERROR: PixHawk didn't come back")
    sys.exit(1)
print(f"PixHawk back online!")

# Request data streams
mav2.mav.request_data_stream_send(
    mav2.target_system, mav2.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1
)

print("Checking GPS for 10s...")
fix_names = {0:'NO_GPS',1:'NO_FIX',2:'2D',3:'3D',4:'DGPS',5:'RTK_FLOAT',6:'RTK_FIXED'}
deadline = time.time() + 10
gps = {}
while time.time() < deadline:
    msg = mav2.recv_match(blocking=False)
    if msg and msg.get_type() == 'GPS_RAW_INT':
        gps = {'fix': msg.fix_type, 'sats': msg.satellites_visible}
    time.sleep(0.05)

fix = gps.get('fix', -1)
sats = gps.get('sats', 0)
print(f"\nGPS status after reboot:")
print(f"  Fix type:   {fix_names.get(fix, 'unknown')} ({fix})")
print(f"  Satellites: {sats}")

if fix == 0:
    print("\n[PROBLEM] GPS still showing NO_GPS — module may not be properly connected")
    print("  Check: GPS cable firmly seated in GPS1 port on Pixhawk")
    print("  Check: GPS module LEDs (should blink on power-up)")
elif fix == 1 and sats == 0:
    print("\n[EXPECTED] GPS module talking but no satellites yet")
    print("  -> Go OUTDOORS with clear sky — should get fix in 1-2 min")
    print("  -> GPS antenna must face UP, away from metal/carbon")
else:
    print(f"\n[OK] GPS has {fix_names.get(fix)} with {sats} sats")
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(IP, username=USER, password=PW, timeout=15)

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(SCRIPT.encode()), '/tmp/reboot_px.py')
sftp.close()

print("Rebooting PixHawk and checking GPS...\n" + "="*50)
_, o, e = c.exec_command(
    'cd ~/IDP_2/rpi && /home/prathvi/.local/bin/uv run python /tmp/reboot_px.py',
    timeout=60
)
print(o.read().decode('utf-8', errors='replace'))
errs = [l for l in e.read().decode('utf-8', errors='replace').splitlines()
        if l.strip() and 'warning' not in l.lower()]
if errs:
    print('[stderr]', '\n'.join(errs[:5]))
c.close()
