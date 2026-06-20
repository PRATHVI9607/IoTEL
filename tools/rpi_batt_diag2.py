"""Kill any process holding ttyAMA0, then run battery diagnostic."""
import paramiko, io, time

IP, USER, PW = '172.17.0.1', 'prathvi', 'prathvi9607'

SCRIPT = r"""
import sys, time
sys.path.insert(0, '/home/prathvi/IDP_2/rpi/.venv/lib/python3.13/site-packages')
from pymavlink import mavutil

mav = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)
hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=20)
if not hb:
    print("ERROR: no heartbeat"); sys.exit(1)
print(f"Connected! System {mav.target_system}")

def get_param(name):
    mav.mav.param_request_read_send(mav.target_system, mav.target_component, name.encode(), -1)
    r = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
    return r.param_value if r else None

print("\n=== BATTERY PARAMETERS ===")
for p in ['BATT_MONITOR','BATT_VOLT_PIN','BATT_CURR_PIN','BATT_VOLT_MULT','BATT_AMP_PERVLT','BATT2_MONITOR']:
    v = get_param(p)
    print(f"  {p:<22} = {v:.4f}" if v is not None else f"  {p:<22} = NOT FOUND")

mav.mav.request_data_stream_send(mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1)

results = {}
deadline = time.time() + 10
while time.time() < deadline:
    msg = mav.recv_match(blocking=False)
    if not msg:
        time.sleep(0.05); continue
    t = msg.get_type()
    if t == 'SYS_STATUS' and 'sys' not in results:
        results['sys'] = (msg.voltage_battery, msg.current_battery, msg.battery_remaining)
    elif t == 'BATTERY_STATUS' and 'batt' not in results:
        v0 = msg.voltages[0] if msg.voltages[0] != 65535 else 0
        results['batt'] = (v0, msg.current_battery, msg.battery_remaining)
    elif t == 'POWER_STATUS' and 'pwr' not in results:
        results['pwr'] = (msg.Vcc, msg.Vservo, msg.flags)

print("\n=== RAW MESSAGE VALUES ===")
sys_r = results.get('sys', ('no msg','no msg','no msg'))
print(f"  SYS_STATUS:     {sys_r[0]} mV  |  {sys_r[1]} cA  |  {sys_r[2]}% remaining")
batt_r = results.get('batt', ('no msg','no msg','no msg'))
print(f"  BATTERY_STATUS: {batt_r[0]} mV cell0  |  {batt_r[1]} cA  |  {batt_r[2]}% remaining")
pwr_r = results.get('pwr', ('no msg','no msg','no msg'))
print(f"  POWER_STATUS:   Vcc={pwr_r[0]} mV  Vservo={pwr_r[1]} mV  flags={pwr_r[2]}")

print("\n=== DIAGNOSIS ===")
flags = pwr_r[2] if pwr_r[2] != 'no msg' else 0
brick1 = bool(flags & 0x2)
brick2 = bool(flags & 0x4)
usb    = bool(flags & 0x1)
print(f"  USB power:     {usb}")
print(f"  POWER1 brick:  {brick1}  <- flight battery power module")
print(f"  POWER2 brick:  {brick2}  <- secondary power")

volt = sys_r[0] if sys_r[0] != 'no msg' else 0
if not brick1:
    print("\n  [ROOT CAUSE] POWER1 not connected")
    print("  YES — plug your power module 6-pin cable into POWER1 on the Pixhawk")
    print("  The power module (PM02/PM07) 6-pin GH cable carries 5V + volt sense + curr sense")
elif volt < 100:
    print("\n  [INFO] POWER1 connected but voltage=0 — check BATT_VOLT_MULT or battery not plugged into PM")
else:
    print(f"\n  [OK] Battery reading {volt/1000:.2f}V via POWER1")
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(IP, username=USER, password=PW, timeout=15)

# Kill anything holding the serial port
print("Killing any process holding /dev/ttyAMA0...")
_, o, _ = c.exec_command(f'echo {PW} | sudo -S fuser -k /dev/ttyAMA0 2>/dev/null; sleep 2; echo done')
print(o.read().decode().strip())

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(SCRIPT.encode()), '/tmp/batt_diag.py')
sftp.close()

print("\nRunning battery diagnostic...\n" + "="*50)
_, o, e = c.exec_command(
    'cd ~/IDP_2/rpi && /home/prathvi/.local/bin/uv run python /tmp/batt_diag.py',
    timeout=60
)
print(o.read().decode('utf-8', errors='replace'))
errs = [l for l in e.read().decode('utf-8', errors='replace').splitlines()
        if l.strip() and 'warning' not in l.lower()]
if errs:
    print('[stderr]', '\n'.join(errs[:5]))
c.close()
