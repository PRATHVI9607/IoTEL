#!/usr/bin/env python3
"""SSH helper — run commands on the RPI via paramiko."""
import paramiko, sys

HOST, USER, PW = '10.182.210.137', 'prathvi', 'prathvi9607'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PW, timeout=15)

def run(cmd, sudo=False):
    if sudo:
        cmd = f"echo '{PW}' | sudo -S bash -c '{cmd}'"
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode()
    return out.strip()

mode = sys.argv[1] if len(sys.argv) > 1 else 'diagnose'

if mode == 'diagnose':
    print('=== Serial ports ===')
    print(run('ls -la /dev/ttyUSB* /dev/ttyACM* /dev/ttyAMA* /dev/serial* 2>/dev/null || echo none'))
    print()
    print('=== USB devices ===')
    print(run('lsusb 2>/dev/null || echo none'))
    print()
    print('=== Recent dmesg (tty/serial) ===')
    print(run('dmesg | grep -iE "tty|serial|usb" | tail -20'))
    print()
    print('=== groups for prathvi ===')
    print(run('groups prathvi'))

elif mode == 'fix':
    print('--- Removing broken aziot package ---')
    print(run('apt-get purge -y aziot-identity-service 2>&1 || true', sudo=True))
    print(run('apt-get autoremove -y 2>&1 || true', sudo=True))

    print('\n--- Syncing uv deps ---')
    print(run('cd ~/IDP_2/rpi && /home/prathvi/.local/bin/uv sync 2>&1'))

elif mode == 'run':
    uart = sys.argv[2] if len(sys.argv) > 2 else '/dev/ttyAMA0'
    laptop_ip = sys.argv[3] if len(sys.argv) > 3 else '10.182.210.136'
    print(f'Running bridge on {uart} -> laptop {laptop_ip}')
    print(run(
        f'cd ~/IDP_2/rpi && nohup /home/prathvi/.local/bin/uv run python rpi_drone_bridge.py '
        f'--ip {laptop_ip} --uart {uart} --baud 57600 > /tmp/bridge.log 2>&1 &'
    ))

client.close()
