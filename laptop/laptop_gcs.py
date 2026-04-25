#!/usr/bin/env python3
"""
================================================================
  Laptop Ground Control Station - Voice + Dashboard
  Runs on your laptop
================================================================
  FEATURES:
    - Receives telemetry from RPI
    - Web dashboard with Loki Theme
    - Voice command recognition
    - CLI fallback monitor
    
  HOW TO RUN:
    - Install requirements: pip install -r requirements.txt
    - Run: python laptop_gcs.py
    - Open: http://localhost:5000
    
  OPTIONS:
    --rpi <IP>     RPI IP address (default: 192.168.1.100)
    --port <port>   Web server port (default: 5000)
================================================================
"""

import os
import sys
import time
import json
import socket
import threading
import argparse
import logging
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from typing import Optional, Dict, Any
from collections import deque

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'voice-drone-control-secret-key'


class GCSState:
    def __init__(self):
        self.tcp_socket = None
        self.connected = False
        self.rpi_ip = '192.168.1.100'
        self.rpi_port = 5760
        self.web_port = 5000
        
        self.telemetry_data = {}
        self.alerts = []
        self.command_history = deque(maxlen=50)
        
        self.stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'errors': 0
        }
        
        self.start_time = 0
        self.running = False
    
    def connect_to_rpi(self, ip: str = None, port: int = None) -> bool:
        if ip:
            self.rpi_ip = ip
        if port:
            self.rpi_port = port
        
        try:
            logger.info(f"Connecting to RPI at {self.rpi_ip}:{self.rpi_port}")
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(10)
            self.tcp_socket.connect((self.rpi_ip, self.rpi_port))
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
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except:
                pass
        self.tcp_socket = None
        self.connected = False
        logger.info("Disconnected")
    
    def send_command(self, command: str) -> tuple:
        if not self.connected or not self.tcp_socket:
            return False, "Not connected to RPI"
        
        try:
            cmd_data = json.dumps({'command': command}).encode()
            self.tcp_socket.sendall(cmd_data + b'\n')
            self.stats['packets_sent'] += 1
            self.command_history.append({
                'command': command,
                'timestamp': time.time(),
                'status': 'sent'
            })
            return True, "Command sent"
        except Exception as e:
            logger.error(f"Command error: {e}")
            self.stats['errors'] += 1
            return False, str(e)
    
    def receive_data(self) -> Optional[Dict]:
        if not self.connected or not self.tcp_socket:
            return None
        
        try:
            data = self.tcp_socket.recv(8192)
            if data:
                self.stats['packets_received'] += 1
                return json.loads(data.decode())
        except socket.timeout:
            pass
        except Exception as e:
            logger.error(f"Receive error: {e}")
        
        return None
    
    def get_state(self) -> Dict[str, Any]:
        return {
            'connected': self.connected,
            'telemetry': self.telemetry_data,
            'alerts': self.alerts,
            'command_history': list(self.command_history)[-10:],
            'stats': self.stats,
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'rpi_ip': self.rpi_ip,
            'rpi_port': self.rpi_port
        }


gcs = GCSState()


# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/connect', methods=['POST'])
def api_connect():
    data = request.get_json()
    ip = data.get('ip', '192.168.1.100')
    port = data.get('port', 5760)
    
    success = gcs.connect_to_rpi(ip, port)
    return jsonify({'success': success})


@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    gcs.disconnect()
    return jsonify({'success': True})


@app.route('/api/status')
def api_status():
    return jsonify(gcs.get_state())


@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.get_json()
    command = data.get('command', '')
    success, response = gcs.send_command(command)
    return jsonify({'success': success, 'response': response})


# ==================== TELEMETRY RECEIVER ====================
@app.route('/telemetry', methods=['POST'])
def telemetry():
    data = request.json
    gcs.telemetry_data = data.get('telemetry', {})
    gcs.alerts = data.get('alerts', [])
    return jsonify({'status': 'received'})


# ==================== MAIN ====================
def main():
    parser = argparse.ArgumentParser(description='Laptop Ground Control Station')
    parser.add_argument('--rpi', default='192.168.1.100', help='RPI IP address')
    parser.add_argument('--port', default=5760, type=int, help='RPI port')
    parser.add_argument('--web', default=5000, type=int, help='Web server port')
    args = parser.parse_args()
    
    gcs.rpi_ip = args.rpi
    gcs.rpi_port = args.port
    gcs.web_port = args.web
    
    logger.info("="*60)
    logger.info("  Laptop Ground Control Station")
    logger.info("="*60)
    logger.info(f"  RPI:     {args.rpi}:{args.port}")
    logger.info(f"  Web:     http://localhost:{args.web}")
    logger.info("="*60)
    
    # Try to connect to RPI automatically
    gcs.connect_to_rpi(args.rpi, args.port)
    
    # Start receiving data in background thread
    def receive_loop():
        while gcs.running or not gcs.running:
            if not gcs.connected:
                time.sleep(1)
                continue
            
            data = gcs.receive_data()
            if data:
                gcs.telemetry_data = data.get('telemetry', {})
                gcs.alerts = data.get('alerts', [])
            
            time.sleep(0.1)
    
    gcs.running = True
    receiver_thread = threading.Thread(target=receive_loop, daemon=True)
    receiver_thread.start()
    
    app.run(host='0.0.0.0', port=args.web, debug=False)


if __name__ == '__main__':
    main()