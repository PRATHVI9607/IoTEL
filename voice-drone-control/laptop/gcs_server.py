#!/usr/bin/env python3
"""
Voice Drone Control - Ground Control Station
TCP client that connects to RPI DroneBridge and provides voice command interface

Author: Voice Drone Control System
"""

import os
import sys
import time
import json
import socket
import threading
import argparse
import logging
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from typing import Optional, Dict, Any

try:
    from dronekit import connect, VehicleMode
    DRONEKIT_AVAILABLE = True
except ImportError:
    DRONEKIT_AVAILABLE = False
    print("Warning: dronekit not installed")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'voice-drone-control-secret-key'


class GCSState:
    """Ground Control Station State"""
    
    def __init__(self):
        self.tcp_socket: Optional[socket.socket] = None
        self.connected = False
        self.rpi_host = '192.168.4.1'
        self.rpi_port = 5760
        
        self.vehicle_state: Dict[str, Any] = {}
        self.last_command = ""
        self.command_history = []
        self.telemetry_history = []
        
        self.voice_active = False
        self.recognizer = None
        self.microphone = None
        
        self.stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'connection_time': 0,
            'errors': 0
        }
        
        self.running = False
        self.start_time = 0
    
    def connect(self, host: str = None, port: int = None) -> bool:
        """Connect to RPI DroneBridge"""
        if host:
            self.rpi_host = host
        if port:
            self.rpi_port = port
            
        try:
            logger.info(f"Connecting to RPI at {self.rpi_host}:{self.rpi_port}")
            
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(10)
            self.tcp_socket.connect((self.rpi_host, self.rpi_port))
            self.tcp_socket.settimeout(1)
            
            self.connected = True
            self.start_time = time.time()
            
            logger.info("Connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from RPI"""
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except:
                pass
        self.tcp_socket = None
        self.connected = False
        logger.info("Disconnected")
    
    def send_command(self, command: str) -> tuple:
        """Send command to vehicle via TCP"""
        if not self.connected or not self.tcp_socket:
            return False, "Not connected"
            
        try:
            # Convert voice command to MAVLink command
            mavlink_cmd = self._convert_command(command)
            
            self.tcp_socket.sendall(mavlink_cmd.encode() + b'\n')
            self.last_command = command
            self.command_history.append({
                'command': command,
                'timestamp': time.time(),
                'status': 'sent'
            })
            self.stats['packets_sent'] += 1
            
            # Read response
            try:
                response = self.tcp_socket.recv(4096).decode()
                return True, response
            except socket.timeout:
                return True, "Command sent (no response)"
                
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self.stats['errors'] += 1
            return False, str(e)
    
    def send_mavlink(self, data: bytes) -> bool:
        """Send raw MAVLink data"""
        if not self.connected or not self.tcp_socket:
            return False
            
        try:
            self.tcp_socket.sendall(data)
            self.stats['packets_sent'] += 1
            return True
        except Exception as e:
            logger.error(f"Error sending MAVLink: {e}")
            return False
    
    def receive_mavlink(self) -> Optional[bytes]:
        """Receive MAVLink data"""
        if not self.connected or not self.tcp_socket:
            return None
            
        try:
            data = self.tcp_socket.recv(4096)
            if data:
                self.stats['packets_received'] += 1
                return data
        except socket.timeout:
            pass
        except Exception as e:
            logger.error(f"Error receiving MAVLink: {e}")
            
        return None
    
    def _convert_command(self, voice_cmd: str) -> str:
        """Convert voice command to vehicle command"""
        cmd = voice_cmd.lower().strip()
        
        command_map = {
            'arm': 'ARM',
            'disarm': 'DISARM',
            'takeoff': 'TAKEOFF',
            'take off': 'TAKEOFF',
            'land': 'LAND',
            'rtl': 'RTL',
            'return': 'RTL',
            'return home': 'RTL',
            'loiter': 'LOITER',
            'hover': 'LOITER',
            'stabilize': 'STABILIZE',
            'althold': 'ALTHOLD',
            'alt hold': 'ALTHOLD',
            'position': 'POSHOLD',
            'position hold': 'POSHOLD',
            'guided': 'GUIDED',
            'manual': 'MANUAL',
            'auto': 'AUTO',
            'circle': 'CIRCLE',
            'break': 'LAND',
            'emergency': 'LAND',
            'go forward': 'MAV_CMD_CONDITION_YAW',
            'go back': 'MAV_CMD_CONDITION_YAW',
            'turn left': 'MAV_CMD_CONDITION_YAW',
            'turn right': 'MAV_CMD_CONDITION_YAW',
        }
        
        for key, value in command_map.items():
            if key in cmd:
                return value
                
        return 'UNKNOWN'
    
    def init_voice(self) -> bool:
        """Initialize voice recognition"""
        if not DRONEKIT_AVAILABLE:
            try:
                import speech_recognition as sr
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                with self.microphone as mic:
                    self.recognizer.adjust_for_ambient_noise(mic)
                logger.info("Voice recognition initialized")
                return True
            except Exception as e:
                logger.error(f"Voice init failed: {e}")
                return False
        return False
    
    def listen_voice(self) -> Optional[str]:
        """Listen for voice command"""
        if not self.recognizer or not self.microphone:
            return None
            
        try:
            with self.microphone as mic:
                audio = self.recognizer.listen(mic, timeout=5)
                
            command = self.recognizer.recognize_google(audio)
            logger.info(f"Voice command: {command}")
            return command
            
        except Exception as e:
            logger.error(f"Voice recognition error: {e}")
            return None
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return {
            'connected': self.connected,
            'vehicle_state': self.vehicle_state,
            'last_command': self.last_command,
            'command_history': self.command_history[-10:],
            'stats': self.stats,
            'uptime': time.time() - self.start_time if self.start_time else 0
        }


gcs = GCSState()


@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')


@app.route('/api/connect', methods=['POST'])
def api_connect():
    """Connect to RPI"""
    data = request.get_json()
    host = data.get('host', '192.168.4.1')
    port = data.get('port', 5760)
    
    success = gcs.connect(host, port)
    return jsonify({'success': success, 'message': 'Connected' if success else 'Failed'})


@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    """Disconnect from RPI"""
    gcs.disconnect()
    return jsonify({'success': True})


@app.route('/api/status')
def api_status():
    """Get GCS status"""
    return jsonify(gcs.get_state())


@app.route('/api/command', methods=['POST'])
def api_command():
    """Send command to vehicle"""
    data = request.get_json()
    command = data.get('command', '')
    
    success, response = gcs.send_command(command)
    return jsonify({'success': success, 'response': response})


@app.route('/api/voice/start', methods=['POST'])
def api_voice_start():
    """Start voice recognition"""
    if not gcs.voice_active:
        gcs.init_voice()
        gcs.voice_active = True
    return jsonify({'success': True})


@app.route('/api/voice/stop', methods=['POST'])
def api_voice_stop():
    """Stop voice recognition"""
    gcs.voice_active = False
    return jsonify({'success': True})


@app.route('/api/telemetry')
def api_telemetry():
    """Stream telemetry data"""
    def generate():
        while True:
            if gcs.connected:
                data = gcs.receive_mavlink()
                if data:
                    yield f"data: {data.hex()}\n\n"
            time.sleep(0.01)
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


# Voice Commands Mapping
VOICE_COMMANDS = {
    'takeoff': 'Takeoff to specified altitude',
    'land': 'Land the drone',
    'return home': 'Return to launch point',
    'arm': 'Arm the motors',
    'disarm': 'Disarm the motors',
    'loiter': 'Hold position',
    'hover': 'Hold position',
    'stabilize': 'Stabilize flight mode',
    'alt hold': 'Altitude hold mode',
    'position hold': 'Position hold mode',
    'guided': 'Guided mode',
    'auto': 'Auto mode',
    'manual': 'Manual mode',
    'emergency land': 'Emergency landing',
    'go up': 'Increase altitude',
    'go down': 'Decrease altitude',
    'stop': 'Stop and hover',
}


def main():
    parser = argparse.ArgumentParser(description='Voice Drone Control GCS')
    parser.add_argument('--host', default='192.168.4.1', help='RPI IP address')
    parser.add_argument('--port', type=int, default=5760, help='RPI port')
    parser.add_argument('--port-gui', type=int, default=5000, help='Web server port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    logger.info("Starting Voice Drone Control GCS...")
    logger.info(f"Connecting to: {args.host}:{args.port}")
    
    gcs.rpi_host = args.host
    gcs.rpi_port = args.port
    
    app.run(host='0.0.0.0', port=args.port_gui, debug=args.debug)


if __name__ == '__main__':
    main()