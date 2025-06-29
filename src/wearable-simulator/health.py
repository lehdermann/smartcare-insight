#
# SmartCare Insight - health.py
#
# Copyright 2025 SmartCare Insight Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Health check endpoint for the wearable simulator.
This allows container orchestration systems to monitor the health of the service.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
import time
import socket
from typing import Dict, Any

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health checks."""
    
    def __init__(self, mqtt_connected: bool, *args, **kwargs):
        self.mqtt_connected = mqtt_connected
        # BaseHTTPRequestHandler calls do_GET inside __init__
        # So we have to call super().__init__ after setting attributes.
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests to the health check endpoint."""
        if self.path == '/health':
            # Check MQTT connection status
            status_code = 200 if self.mqtt_connected else 503
            health_status = "healthy" if self.mqtt_connected else "unhealthy"
            
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": health_status,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "services": {
                    "mqtt": "connected" if self.mqtt_connected else "disconnected"
                }
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

class HealthCheckServer:
    """Simple HTTP server for health checks."""
    
    def __init__(self, port: int = 8000, mqtt_connected: bool = False):
        self.port = port
        self.mqtt_connected = mqtt_connected
        self.server = None
        self.thread = None
    
    def update_mqtt_status(self, connected: bool):
        """Update the MQTT connection status."""
        self.mqtt_connected = connected
    
    def start(self):
        """Start the health check server in a separate thread."""
        def handler(*args):
            return HealthCheckHandler(self.mqtt_connected, *args)
        
        self.server = HTTPServer(('0.0.0.0', self.port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        print(f"Health check server started on port {self.port}")
    
    def stop(self):
        """Stop the health check server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.thread:
                self.thread.join(timeout=1)
            print("Health check server stopped")

def is_port_available(port: int) -> bool:
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except OSError:
            return False

if __name__ == "__main__":
    # Example usage
    import time
    
    print("Starting health check server...")
    health_server = HealthCheckServer(port=8000, mqtt_connected=True)
    health_server.start()
    
    try:
        while True:
            # Simulate MQTT connection status changes
            time.sleep(10)
            health_server.update_mqtt_status(not health_server.mqtt_connected)
            print(f"MQTT status: {'connected' if health_server.mqtt_connected else 'disconnected'}")
    except KeyboardInterrupt:
        print("Stopping health check server...")
        health_server.stop()
