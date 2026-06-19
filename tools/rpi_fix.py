"""Fix boot config, serial console, and sync uv deps on the RPI."""
import paramiko, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

IP, USER, PW = '10.182.210.137', 'prathvi', 'prathvi9607'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(IP, username=USER, password=PW, timeout=15)

def run(cmd, show=True):
    _, o, e = c.exec_command(cmd)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    if show and out: print(out)
    if show and err: print('[err]', err)
    return out

def sudo(cmd, show=True):
    return run(f'echo "{PW}" | sudo -S bash -c \'{cmd}\'', show=show)

# ── 1. Read extra RPI-only files ──────────────────────────────────────────────
print('='*60)
print('=== arm.py ===')
print(run('cat ~/IDP_2/rpi/arm.py'))
print()
print('=== arm1.py ===')
print(run('cat ~/IDP_2/rpi/arm1.py'))
print()
print('=== arm3.py ===')
print(run('cat ~/IDP_2/rpi/arm3.py'))
print()
print('=== rpi_test.py ===')
print(run('cat ~/IDP_2/rpi_test.py'))
print('='*60)

# ── 2. Fix /boot/firmware/config.txt ─────────────────────────────────────────
print('\n[FIX] Adding dtoverlay=disable-bt to config.txt...')
result = sudo(
    'grep -q dtoverlay=disable-bt /boot/firmware/config.txt '
    '|| echo dtoverlay=disable-bt >> /boot/firmware/config.txt && echo done'
)
print('config.txt:', result)

# ── 3. Remove serial console from cmdline.txt ─────────────────────────────────
print('\n[FIX] Removing console=serial0,115200 from cmdline.txt...')
# sed in-place: remove the console=serial0,XXXXX token
result = sudo(
    "sed -i 's/console=serial0,[0-9]* //g' /boot/firmware/cmdline.txt && echo done"
)
print('cmdline.txt:', result)

print('\n[CHECK] New cmdline.txt:')
print(sudo('cat /boot/firmware/cmdline.txt'))

print('\n[CHECK] Last 5 lines of config.txt:')
print(sudo('tail -5 /boot/firmware/config.txt'))

# ── 4. uv sync in rpi/ ───────────────────────────────────────────────────────
print('\n[FIX] Running uv sync in ~/IDP_2/rpi...')
print(run('cd ~/IDP_2/rpi && /home/prathvi/.local/bin/uv sync 2>&1'))

print()
print('='*60)
print('All done! Reboot the RPI now:')
print('  sudo reboot')
print()
print('After reboot, run:')
print('  cd ~/IDP_2/rpi')
print('  uv run python rpi_drone_bridge.py --ip 10.182.210.136 --uart /dev/ttyAMA0')
print('='*60)

c.close()
