import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('10.182.210.137', username='prathvi', password='prathvi9607', timeout=10)

def run(cmd):
    _, o, _ = c.exec_command(cmd)
    return o.read().decode().strip()

def sudo(cmd):
    _, o, _ = c.exec_command('sudo -S ' + cmd, get_pty=False)
    o.channel.send('prathvi9607\n')
    return o.read().decode().strip()

print('=== cmdline.txt ===')
print(run('sudo cat /boot/firmware/cmdline.txt 2>/dev/null || sudo cat /boot/cmdline.txt 2>/dev/null'))
print()
print('=== config.txt (last 15 lines) ===')
print(run('sudo tail -15 /boot/firmware/config.txt 2>/dev/null || sudo tail -15 /boot/config.txt'))
print()
print('=== IDP_2 structure ===')
print(run('find ~/IDP_2 -not -path "*/.venv*" -not -path "*/venv/*" -not -path "*/__pycache__*" -not -path "*/.git*" -type f 2>/dev/null | sort'))
print()
print('=== Python version ===')
print(run('python3 --version'))
print()
print('=== uv version ===')
print(run('/home/prathvi/.local/bin/uv --version 2>/dev/null || echo "uv not in path"'))

c.close()
