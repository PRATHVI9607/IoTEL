"""Push updated rpi_drone_bridge.py to the RPI via SFTP."""
import paramiko

IP, USER, PW = '10.182.210.137', 'prathvi', 'prathvi9607'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(IP, username=USER, password=PW, timeout=10)

sftp = c.open_sftp()
sftp.put(
    r'c:\Workspace\IoTEL\rpi\rpi_drone_bridge.py',
    '/home/prathvi/IDP_2/rpi/rpi_drone_bridge.py'
)
sftp.close()
print('Pushed rpi_drone_bridge.py to RPI.')
c.close()
