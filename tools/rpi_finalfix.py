"""Final fixes: cmdline.txt serial console removal, config.txt dedup, then reboot."""
import paramiko, time

IP, USER, PW = '10.182.210.137', 'prathvi', 'prathvi9607'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(IP, username=USER, password=PW, timeout=15)

def run(cmd):
    _, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8', errors='replace').strip()
    err = e.read().decode('utf-8', errors='replace').strip()
    return out, err

def sudo_python(script):
    """Run a Python script as root on the RPI."""
    escaped = script.replace("'", "'\\''")
    cmd = f"echo '{PW}' | sudo -S python3 -c '{escaped}'"
    out, err = run(cmd)
    if out: print(out)
    if err and 'sudo' not in err.lower(): print('[err]', err)

# ── 1. Check actual config.txt size / dedup ──────────────────────────────────
print('=== config.txt (full) ===')
out, _ = run('sudo cat /boot/firmware/config.txt')
print(out)

# Fix if [all] block is duplicated
if out.count('dtoverlay=disable-bt') > 1:
    print('\n[FIX] config.txt has duplicate entries — deduplicating...')
    sudo_python("""
lines = open('/boot/firmware/config.txt').readlines()
seen = set()
deduped = []
for line in lines:
    if line.strip() in seen and line.strip():
        continue
    seen.add(line.strip())
    deduped.append(line)
open('/boot/firmware/config.txt', 'w').writelines(deduped)
print('config.txt deduplicated')
""")
else:
    print('\n[OK] config.txt looks clean')

# ── 2. Fix cmdline.txt — remove console=serial0,XXXXX ───────────────────────
print('\n=== cmdline.txt (before) ===')
out, _ = run('cat /boot/firmware/cmdline.txt')
print(out)

if 'console=serial0' in out:
    print('\n[FIX] Removing console=serial0,115200 from cmdline.txt...')
    sudo_python("""
import re
path = '/boot/firmware/cmdline.txt'
content = open(path).read()
fixed = re.sub(r'console=serial0,\d+\s*', '', content).strip()
open(path, 'w').write(fixed + '\n')
print('cmdline.txt fixed')
""")
    out2, _ = run('cat /boot/firmware/cmdline.txt')
    print('\n=== cmdline.txt (after) ===')
    print(out2)
else:
    print('[OK] cmdline.txt already clean')

# ── 3. Verify final state ────────────────────────────────────────────────────
print('\n=== Final config.txt (last 8 lines) ===')
out, _ = run('tail -8 /boot/firmware/config.txt')
print(out)

# ── 4. Reboot ────────────────────────────────────────────────────────────────
print('\n[REBOOT] Rebooting RPI in 3 seconds...')
time.sleep(1)
c.exec_command(f'echo {PW} | sudo -S reboot')
print('[REBOOT] Reboot command sent.')
print()
print('Wait ~30 seconds, then run on the RPI:')
print('  cd ~/IDP_2/rpi')
print('  uv run python rpi_drone_bridge.py --ip 10.182.210.136 --uart /dev/ttyAMA0')

c.close()
