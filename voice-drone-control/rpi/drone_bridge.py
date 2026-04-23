#!/usr/bin/env python3
"""
Raspberry Pi DroneBridge - UART to TCP Telemetry Bridge
Connects to Pixhawk via UART and bridges MAVLink to laptop via TCP

Author: Voice Drone Control System
"""

import os
import sys
import time
import socket
import threading
import argparse
import logging
from collections import deque
from typing import Optional, Tuple

try:
    from dronekit import connect, Vehicle
    from pymavlink import mavutil
    DRONEKIT_AVAILABLE = True
except ImportError:
    DRONEKIT_AVAILABLE = False
    print("Warning: dronekit not installed. Install with: pip install dronekit")

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("Warning: pyserial not installed. Install with: pip install pyserial")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/var/log/dronebridge.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MAVLinkBridge:
    """Bridge MAVLink between UART and TCP socket"""
    
    def __init__(
        self,
        uart_device: str = '/dev/serial0',
        uart_baud: int = 57600,
        tcp_port: int = 5760,
        tcp_host: str = '0.0.0.0',
        heartbeat_rate: float = 1.0,
        max_queue_size: int = 100
    ):
        self.uart_device = uart_device
        self.uart_baud = uart_baud
        self.tcp_port = tcp_port
        self.tcp_host = tcp_host
        self.heartbeat_rate = heartbeat_rate
        
        self.uart: Optional[serial.Serial] = None
        self.tcp_server: Optional[socket.socket] = None
        self.tcp_client: Optional[socket.socket] = None
        self.vehicle: Optional[Vehicle] = None
        
        self.running = False
        self.connected = False
        
        self.uart_to_tcp_queue = deque(maxlen=max_queue_size)
        self.tcp_to_uart_queue = deque(maxlen=max_queue_size)
        
        self._uart_lock = threading.Lock()
        self._tcp_lock = threading.Lock()
        
        self.stats = {
            'uart_bytes_sent': 0,
            'uart_bytes_recv': 0,
            'tcp_bytes_sent': 0,
            'tcp_bytes_recv': 0,
            'packets_sent': 0,
            'packets_recv': 0,
            'errors': 0
        }
        
    def initialize_uart(self) -> bool:
        """Initialize UART connection to Pixhawk"""
        if not SERIAL_AVAILABLE:
            logger.error("pyserial not available")
            return False
            
        try:
            logger.info(f"Connecting to Pixhawk on {self.uart_device} at {self.uart_baud} baud")
            
            self.uart = serial.Serial(
                port=self.uart_device,
                baudrate=self.uart_baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                write_timeout=1
            )
            
            time.sleep(2)
            
            self.connected = True
            logger.info(f"UART connected successfully on {self.uart_device}")
            return True
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to UART: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to UART: {e}")
            return False
    
    def initialize_dronekit(self) -> bool:
        """Initialize DroneKit connection"""
        if not DRONEKIT_AVAILABLE:
            logger.error("dronekit not available")
            return False
            
        try:
            logger.info(f"Connecting to vehicle via {self.uart_device}")
            connection_string = self.uart_device
            self.vehicle = connect(connection_string, wait_ready=True, baud=self.uart_baud)
            
            logger.info(f"Vehicle connected: {self.vehicle.version}")
            logger.info(f"Vehicle mode: {self.vehicle.mode.name}")
            logger.info(f"Armed: {self.vehicle.armed}")
            logger.info(f"Location: {self.vehicle.location.global_relative_frame}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to vehicle: {e}")
            return False
    
    def initialize_tcp_server(self) -> bool:
        """Initialize TCP server for laptop connection"""
        try:
            self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_server.bind((self.tcp_host, self.tcp_port))
            self.tcp_server.listen(1)
            self.tcp_server.settimeout(5)
            
            logger.info(f"TCP server listening on {self.tcp_host}:{self.tcp_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create TCP server: {e}")
            return False
    
    def accept_tcp_connection(self) -> bool:
        """Accept incoming TCP connection from laptop"""
        try:
            logger.info("Waiting for TCP connection...")
            self.tcp_client, address = self.tcp_server.accept()
            self.tcp_client.settimeout(1)
            logger.info(f"Accepted connection from {address}")
            return True
            
        except socket.timeout:
            return False
        except Exception as e:
            logger.error(f"Failed to accept connection: {e}")
            return False
    
    def read_uart(self) -> Optional[bytes]:
        """Read data from UART"""
        if not self.uart or not self.connected:
            return None
            
        try:
            with self._uart_lock:
                if self.uart.in_waiting > 0:
                    data = self.uart.read(self.uart.in_waiting)
                    self.stats['uart_bytes_recv'] += len(data)
                    return data
        except Exception as e:
            logger.error(f"Error reading UART: {e}")
            self.stats['errors'] += 1
            
        return None
    
    def write_uart(self, data: bytes) -> bool:
        """Write data to UART"""
        if not self.uart or not self.connected:
            return False
            
        try:
            with self._uart_lock:
                self.uart.write(data)
                self.stats['uart_bytes_sent'] += len(data)
                return True
        except Exception as e:
            logger.error(f"Error writing UART: {e}")
            self.stats['errors'] += 1
            
        return False
    
    def read_tcp(self) -> Optional[bytes]:
        """Read data from TCP client"""
        if not self.tcp_client:
            return None
            
        try:
            data = self.tcp_client.recv(4096)
            if data:
                self.stats['tcp_bytes_recv'] += len(data)
                return data
        except socket.timeout:
            pass
        except Exception as e:
            logger.error(f"Error reading TCP: {e}")
            self.stats['errors'] += 1
            
        return None
    
    def write_tcp(self, data: bytes) -> bool:
        """Write data to TCP client"""
        if not self.tcp_client:
            return False
            
        try:
            with self._tcp_lock:
                self.tcp_client.sendall(data)
                self.stats['tcp_bytes_sent'] += len(data)
                return True
        except Exception as e:
            logger.error(f"Error writing TCP: {e}")
            self.stats['errors'] += 1
            self.tcp_client = None
            
        return False
    
    def process_uart_to_tcp(self):
        """Process data from UART to TCP"""
        data = self.read_uart()
        if data and self.tcp_client:
            self.write_tcp(data)
            self.stats['packets_recv'] += 1
            
    def process_tcp_to_uart(self):
        """Process data from TCP to UART"""
        data = self.read_tcp()
        if data:
            self.write_uart(data)
            self.stats['packets_sent'] += 1
    
    def get_vehicle_state(self) -> dict:
        """Get current vehicle state"""
        if not self.vehicle:
            return {}
            
        try:
            return {
                'armed': self.vehicle.armed,
                'mode': self.vehicle.mode.name,
                'system_status': self.vehicle.system_status.name,
                'gps': {
                    'lat': self.vehicle.location.global_relative_frame.lat,
                    'lon': self.vehicle.location.global_relative_frame.lon,
                    'alt': self.vehicle.location.global_relative_frame.alt
                } if self.vehicle.location.global_relative_frame else None,
                'attitude': {
                    'pitch': self.vehicle.attitude.pitch,
                    'roll': self.vehicle.attitude.roll,
                    'yaw': self.vehicle.attitude.yaw
                } if self.vehicle.attitude else None,
                'velocity': list(self.vehicle.velocity) if self.vehicle.velocity else None,
                'heading': self.vehicle.heading,
                'ground_speed': self.vehicle.groundspeed,
                'air_speed': self.vehicle.airspeed,
                'battery': {
                    'voltage': self.vehicle.battery.voltage,
                    'current': self.vehicle.battery.current,
                    'level': self.vehicle.battery.level
                } if self.vehicle.battery else None
            }
        except Exception as e:
            logger.error(f"Error getting vehicle state: {e}")
            return {}
    
    def send_command(self, command: str) -> Tuple[bool, str]:
        """Send command to vehicle"""
        if not self.vehicle:
            return False, "Vehicle not connected"
            
        try:
            command = command.lower().strip()
            
            if command in ['arm', 'arm vehicle']:
                self.vehicle.armed = True
                return True, "Arm command sent"
                
            elif command in ['disarm', 'land']:
                self.vehicle.armed = False
                return True, "Disarm command sent"
                
            elif command.startswith('takeoff') or command.startswith('take off'):
                parts = command.split()
                if len(parts) > 1:
                    altitude = float(parts[1])
                else:
                    altitude = 10
                    
                from dronekit import Command
                cmds = self.vehicle.commands
                cmds.download()
                cmds.wait_ready()
                
                takeoff_cmd = Command(
                    0, 0, 0,
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                    0, 0, 0, 0, 0, 0,
                    0, 0, altitude
                )
                cmds.add(takeoff_cmd)
                cmds.upload()
                return True, f"Takeoff to {altitude}m sent"
                
            elif command.startswith('rtl') or command == 'return to launch':
                cmds = self.vehicle.commands
                cmds.download()
                cmds.wait_ready()
                
                rtl_cmd = Command(
                    0, 0, 0,
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    mavutil.mavlink.MAV_CMD_NAV_RTL,
                    0, 0, 0, 0, 0, 0,
                    0, 0, 0
                )
                cmds.add(rtl_cmd)
                cmds.upload()
                return True, "RTL command sent"
                
            elif command.startswith('loiter'):
                self.vehicle.mode = VehicleMode('LOITER')
                return True, "Loiter mode set"
                
            elif command.startswith('stabilize'):
                self.vehicle.mode = VehicleMode('STABILIZE')
                return True, "Stabilize mode set"
                
            elif command.startswith('althold') or command == 'alt hold':
                self.vehicle.mode = VehicleMode('ALT_HOLD')
                return True, "Alt Hold mode set"
                
            elif command.startswith('position') or command == 'position mode':
                self.vehicle.mode = VehicleMode('POSHOLD')
                return True, "Position Hold mode set"
                
            elif command.startswith('guided'):
                self.vehicle.mode = VehicleMode('GUIDED')
                return True, "Guided mode set"
                
            elif command.startswith('land'):
                self.vehicle.mode = VehicleMode('LAND')
                return True, "Land mode set"
                
            else:
                return False, f"Unknown command: {command}"
                
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False, str(e)
    
    def start(self) -> bool:
        """Start the bridge"""
        self.running = True
        
        if not self.initialize_uart():
            logger.warning("UART initialization failed, running in TCP-bridge mode only")
            
        if not self.initialize_tcp_server():
            logger.error("TCP server initialization failed")
            return False
            
        logger.info("DroneBridge started successfully")
        return True
    
    def stop(self):
        """Stop the bridge"""
        self.running = False
        
        if self.tcp_client:
            self.tcp_client.close()
        if self.tcp_server:
            self.tcp_server.close()
        if self.uart:
            self.uart.close()
        if self.vehicle:
            self.vehicle.close()
            
        logger.info("DroneBridge stopped")
    
    def run(self):
        """Main loop"""
        if not self.start():
            return
            
        last_heartbeat = time.time()
        
        while self.running:
            try:
                if not self.tcp_client:
                    if not self.accept_tcp_connection():
                        time.sleep(0.1)
                        continue
                        
                self.process_uart_to_tcp()
                self.process_tcp_to_uart()
                
                if time.time() - last_heartbeat > self.heartbeat_rate:
                    state = self.get_vehicle_state()
                    if state:
                        logger.info(f"Heartbeat: {state}")
                    last_heartbeat = time.time()
                    
                time.sleep(0.001)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                self.stats['errors'] += 1
                
        self.stop()
    
    def get_stats(self) -> dict:
        """Get statistics"""
        return self.stats.copy()


def main():
    parser = argparse.ArgumentParser(
        description='Raspberry Pi DroneBridge - UART to TCP MAVLink Bridge'
    )
    parser.add_argument(
        '--uart', '-u',
        default='/dev/serial0',
        help='UART device path (default: /dev/serial0)'
    )
    parser.add_argument(
        '--baud', '-b',
        type=int,
        default=57600,
        help='UART baud rate (default: 57600)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5760,
        help='TCP port (default: 5760)'
    )
    parser.add_argument(
        '--host', 
        default='0.0.0.0',
        help='TCP bind host (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    bridge = MAVLinkBridge(
        uart_device=args.uart,
        uart_baud=args.baud,
        tcp_port=args.port,
        tcp_host=args.host
    )
    
    logger.info("Starting DroneBridge...")
    logger.info(f"UART: {args.uart} @ {args.baud}")
    logger.info(f"TCP: {args.host}:{args.port}")
    
    bridge.run()


if __name__ == '__main__':
    main()