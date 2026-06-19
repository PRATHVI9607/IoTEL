"""Upload a fix script via SFTP then run it as root — avoids shell quoting hell."""
import paramiko, time, io

IP, USER, PW = '10.182.210.137', 'prathvi', 'prathvi9607'

# Wait for RPI to come back after reboot
print('Waiting for RPI to come back online...')
for attempt in range(20):
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(IP, username=USER, password=PW, timeout=5)
        print(f'Connected (attempt {attempt+1})')
        break
    except Exception:
        print(f'  attempt {attempt+1}/20 — not up yet, retrying...')
        time.sleep(5)
else:
    print('ERROR: Could not reconnect after 100s')
    exit(1)

def run(cmd):
    _, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8', errors='replace').strip()
    err = e.read().decode('utf-8', errors='replace').strip()
    return out, err

# ── Upload the fix script via SFTP ───────────────────────────────────────────
fix_script = b"""
import re
path = '/boot/firmware/cmdline.txt'
content = open(path).read()
fixed = re.sub(r'console=serial0,\\d+\\s*', '', content).strip()
open(path, 'w').write(fixed + '\\n')
print('Fixed:', open(path).read().strip())
"""

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(fix_script), '/tmp/fix_cmdline.py')
sftp.close()

# ── Run it as root ────────────────────────────────────────────────────────────
print('\n[FIX] Removing serial console from cmdline.txt...')
out, err = run(f'echo {PW} | sudo -S python3 /tmp/fix_cmdline.py')
if out: print(out)
if err and 'sudo' not in err: print('[err]', err)

# ── Verify ────────────────────────────────────────────────────────────────────
print('\n=== cmdline.txt (final) ===')
out, _ = run('cat /boot/firmware/cmdline.txt')
print(out)

if 'console=serial0' not in out:
    print('\n[OK] Serial console removed! Rebooting for changes to take effect...')
    c.exec_command(f'echo {PW} | sudo -S reboot')
    print('[REBOOT] Done. Wait ~30s, then on the RPI run:')
    print()
    print('  cd ~/IDP_2/rpi')
    print('  uv run python rpi_drone_bridge.py --ip 10.182.210.136 --uart /dev/ttyAMA0')
else:
    print('\n[WARN] console=serial0 still present — manual fix needed')

c.close()
