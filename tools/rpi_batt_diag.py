"""Diagnose battery reading issues on PixHawk."""
import paramiko, io

IP, USER, PW = '10.182.210.137', 'prathvi', 'prathvi9607'

SCRIPT = r"""
import sys, time
sys.path.insert(0, '/home/prathvi/IDP_2/rpi/.venv/lib/python3.13/site-packages')
from pymavlink import mavutil

mav = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)
mav.recv_match(type='HEARTBEAT', blocking=True, timeout=15)
print(f"Connected to System {mav.target_system}")

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
        mavutil.mavlink.MAV_PARAM_TYPE_REAL32
    )
    time.sleep(0.4)
    r = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
    if r:
        print(f"  SET {name} = {r.param_value:.4f}")
    return r.param_value if r else None

print("\n=== BATTERY PARAMETERS ===")
batt_params = [
    'BATT_MONITOR',
    'BATT_VOLT_PIN', 'BATT_CURR_PIN',
    'BATT_VOLT_MULT', 'BATT_AMP_PERVLT',
    'BATT_VOLT_OFFSET', 'BATT_AMP_OFFSET',
    'BATT_CAPACITY', 'BATT_LOW_VOLT', 'BATT_CRT_VOLT',
    'BATT2_MONITOR',
]
vals = {}
for p in batt_params:
    v = get_param(p)
    vals[p] = v
    if v is not None:
        print(f"  {p:<22} = {v:.4f}")
    else:
        print(f"  {p:<22} = NOT FOUND")

print("\n=== RAW MESSAGES (10s) ===")
mav.mav.request_data_stream_send(
    mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1
)
results = {}
deadline = time.time() + 10
while time.time() < deadline:
    msg = mav.recv_match(blocking=False)
    if not msg:
        time.sleep(0.05)
        continue
    t = msg.get_type()
    if t == 'SYS_STATUS' and 'sys' not in results:
        results['sys'] = {
            'voltage': msg.voltage_battery,
            'current': msg.current_battery,
            'remaining': msg.battery_remaining,
            'sensors_present': msg.onboard_control_sensors_present,
            'sensors_health': msg.onboard_control_sensors_health,
        }
    elif t == 'BATTERY_STATUS' and 'batt' not in results:
        v = msg.voltages[0] if msg.voltages[0] != 65535 else None
        results['batt'] = {
            'voltage_cell': v,
            'current': msg.current_battery,
            'remaining': msg.battery_remaining,
            'id': msg.id,
        }
    elif t == 'POWER_STATUS' and 'pwr' not in results:
        results['pwr'] = {
            'Vcc': msg.Vcc,
            'Vservo': msg.Vservo,
            'flags': msg.flags,
        }

sys_r = results.get('sys', {})
print(f"  SYS_STATUS voltage:    {sys_r.get('voltage','no msg')} mV")
print(f"  SYS_STATUS current:    {sys_r.get('current','no msg')} cA")
print(f"  SYS_STATUS remaining:  {sys_r.get('remaining','no msg')} %")

batt_r = results.get('batt', {})
print(f"  BATTERY_STATUS cell0:  {batt_r.get('voltage_cell','no msg')} mV")
print(f"  BATTERY_STATUS cur:    {batt_r.get('current','no msg')} cA")

pwr_r = results.get('pwr', {})
print(f"  POWER_STATUS Vcc:      {pwr_r.get('Vcc','no msg')} mV  (flight controller 5V rail)")
print(f"  POWER_STATUS Vservo:   {pwr_r.get('Vservo','no msg')} mV  (servo rail)")
flags = pwr_r.get('flags', 0)
if isinstance(flags, int):
    print(f"  POWER_STATUS flags:    {flags}")
    print(f"    USB connected:       {bool(flags & 0x1)}")
    print(f"    POWER1 brick valid:  {bool(flags & 0x2)}")
    print(f"    POWER2 brick valid:  {bool(flags & 0x4)}")

print("\n=== DIAGNOSIS ===")
monitor = vals.get('BATT_MONITOR', 0)
volt_raw = sys_r.get('voltage', 0) or 0
brick1 = bool(flags & 0x2) if isinstance(pwr_r.get('flags',0), int) else None
brick2 = bool(flags & 0x4) if isinstance(pwr_r.get('flags',0), int) else None

if monitor == 0:
    print("  [PROBLEM] BATT_MONITOR=0 — battery monitoring is OFF")
    print("  [FIX]     Set BATT_MONITOR=4 in Mission Planner")
elif volt_raw == 0 or volt_raw < 100:
    print("  [PROBLEM] Battery voltage reads 0 (or near 0)")
    print()
    if brick1 == False:
        print("  [ROOT CAUSE] POWER1 brick not detected — power module NOT connected to POWER1")
        print()
        print("  What to connect:")
        print("    Your power module (PM02/PM07) has TWO cables:")
        print("    1. Battery XT60 -> PM -> ESCs (power path)")
        print("    2. 6-pin GH cable from PM -> POWER1 port on Pixhawk")
        print("       This 6-pin cable carries: 5V, GND, voltage sense, current sense")
        print()
        print("  YES you need to plug the 6-pin cable into POWER1")
    elif brick1 == True:
        print("  [INFO] POWER1 IS connected but voltage still 0")
        print("  [CHECK] BATT_VOLT_MULT may be wrong")
        mult = vals.get('BATT_VOLT_MULT', 0)
        print(f"  Current BATT_VOLT_MULT = {mult:.3f}")
        if mult is not None and mult < 1:
            print("  [FIX] BATT_VOLT_MULT is too low — set to 18.182 (Holybro) or 10.1 (3DR)")
    else:
        print("  [INFO] Could not read POWER_STATUS flags")
        print("  [CHECK] Is the 6-pin power module cable plugged into POWER1 port?")
else:
    print(f"  [OK] Battery reading {volt_raw/1000:.2f}V")
    print(f"  [INFO] If voltage seems wrong, calibrate BATT_VOLT_MULT")
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(IP, username=USER, password=PW, timeout=15)
sftp = c.open_sftp()
sftp.putfo(io.BytesIO(SCRIPT.encode()), '/tmp/batt_diag.py')
sftp.close()

print("Running battery diagnostic...\n" + "="*50)
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
