#
# SmartCare Insight - main.py
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

import json
import logging
import os
import random
import signal
import sys
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_signal_generator import EnhancedSignalGenerator
from config.settings import settings
from health import HealthCheckServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wearable_simulator.log')
    ]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
running = True

class WearableSimulator:
    """A simulator for wearable health monitoring devices."""
    
    def __init__(self):
        """Initialize the wearable simulator with configuration from environment variables."""
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        # Initialize signal generator with patient condition if specified
        self.condition = os.getenv('CONDITION')
        self.signal_generator = EnhancedSignalGenerator(condition=self.condition)
        
        # MQTT settings
        self.mqtt_broker = os.getenv('MQTT_BROKER', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
        self.mqtt_username = os.getenv('MQTT_USERNAME')
        self.mqtt_password = os.getenv('MQTT_PASSWORD')
        self.mqtt_topic = os.getenv('MQTT_TOPIC', 'wearables/data')
        self.mqtt_qos = int(os.getenv('MQTT_QOS', '1'))
        self.mqtt_retain = os.getenv('MQTT_RETAIN', 'false').lower() == 'true'
        
        # Device and patient settings
        self.device_id = os.getenv('DEVICE_ID', f'wearable-{random.randint(1000, 9999)}')
        self.patient_id = os.getenv('PATIENT_ID', f'patient-{random.randint(1000, 9999)}')
        
        # Simulation settings
        self.sample_rate = int(os.getenv('SAMPLE_RATE', '4'))  # samples per minute
        self.sample_interval = 60.0 / self.sample_rate  # seconds between samples
        
        # Health check server
        self.health_check_port = int(os.getenv('HEALTH_CHECK_PORT', '8000'))
        self.health_server = HealthCheckServer(port=self.health_check_port, mqtt_connected=False)
        
        # MQTT client
        self.client = None
        self.connected = False
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown."""
        global running
        logger.info(f"Received signal {signum}, shutting down...")
        running = False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            self.connected = True
            self.health_server.update_mqtt_status(True)
            logger.info(f"Connected to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
            
            # Publish device metadata on connect
            self.publish_device_metadata()
        else:
            self.health_server.update_mqtt_status(False)
            logger.error(f"Failed to connect to MQTT broker with result code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        was_connected = self.connected
        self.connected = False
        self.health_server.update_mqtt_status(False)
        
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection (rc={rc}), attempting to reconnect...")
            self.reconnect()
        else:
            logger.info("Disconnected from MQTT broker")
    
    def publish_device_metadata(self):
        """Publish static device metadata to a retained topic."""
        if not self.connected:
            return
            
        metadata = {
            'device_id': self.device_id,
            'patient_id': self.patient_id,
            'type': 'wearable',
            'model': 'Simulated Wearable v1.0',
            'firmware': '1.0.0',
            'capabilities': ['heart_rate', 'blood_pressure', 'oxygen', 'glucose', 'activity'],
            'condition': self.condition if self.condition else 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        metadata_topic = f"{self.mqtt_topic}/metadata/{self.device_id}"
        try:
            result = self.client.publish(
                topic=metadata_topic,
                payload=json.dumps(metadata),
                qos=1,
                retain=True
            )
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published device metadata to {metadata_topic}")
            else:
                logger.error(f"Failed to publish device metadata: {result.rc}")
        except Exception as e:
            logger.error(f"Error publishing device metadata: {e}")
    
    def connect(self):
        """Connect to the MQTT broker."""
        logger.info(f"Creating MQTT client with ID: {self.device_id}")
        self.client = mqtt.Client(client_id=self.device_id, clean_session=True)
        
        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        # Set credentials if provided
        if self.mqtt_username and self.mqtt_password:
            logger.info(f"Setting MQTT credentials for user: {self.mqtt_username}")
            self.client.username_pw_set(self.mqtt_username, self.mqtt_password)
        else:
            logger.info("No MQTT credentials provided, using anonymous access")
        
        # Set Last Will and Testament (LWT)
        lwt_topic = f"{self.mqtt_topic}/status/{self.device_id}"
        self.client.will_set(lwt_topic, payload="offline", qos=1, retain=True)
        
        # Start the health check server
        self.health_server.start()
        
        try:
            logger.info(f"Connecting to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}...")
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
            # Publish online status
            self.client.publish(lwt_topic, "online", qos=1, retain=True)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.health_server.update_mqtt_status(False)
            return False
    
    def reconnect(self):
        """Attempt to reconnect to the MQTT broker."""
        max_retries = 5
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to reconnect to MQTT broker (attempt {attempt + 1}/{max_retries})...")
                self.client.reconnect()
                self.connected = True
                self.health_server.update_mqtt_status(True)
                logger.info("Successfully reconnected to MQTT broker")
                
                # Re-publish metadata after reconnection
                self.publish_device_metadata()
                return True
            except Exception as e:
                self.health_server.update_mqtt_status(False)
                logger.warning(f"Reconnection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)  # Exponential backoff, max 60s
        
        logger.error("Max reconnection attempts reached. Giving up.")
        return False
    
    def disconnect(self):
        """Disconnect from the MQTT broker."""
        if self.client:
            # Publish offline status
            lwt_topic = f"{self.mqtt_topic}/status/{self.device_id}"
            self.client.publish(lwt_topic, "offline", qos=1, retain=True)
            
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
        
        # Stop the health check server
        self.health_server.stop()
    
    def generate_and_publish(self, timestamp=None):
        """
        Generate a sample and publish it to the MQTT broker.
        
        Args:
            timestamp: Optional timestamp to use (for batch mode)
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker, skipping publish")
            return None
            
        try:
            # Generate sample data
            sample = self.signal_generator.generate()
            
            # Add metadata
            sample.update({
                'device_id': self.device_id,
                'patient_id': self.patient_id,
                'timestamp': timestamp.isoformat() if timestamp else datetime.now(timezone.utc).isoformat(),
                'condition': self.condition if self.condition else 'healthy'
            })
            
            # Publish to MQTT
            result = self.client.publish(
                topic=self.mqtt_topic,
                payload=json.dumps(sample),
                qos=self.mqtt_qos,
                retain=self.mqtt_retain
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published: {sample}")
                return sample
            else:
                logger.error(f"Failed to publish message: {result.rc}")
                self.health_server.update_mqtt_status(False)
                return None
                
        except Exception as e:
            logger.error(f"Error generating/publishing sample: {e}", exc_info=True)
            self.health_server.update_mqtt_status(False)
            return None
    
    def generate_batch(self, batch_size: int, backfill_hours: int = 24):
        """
        Generate a batch of samples at once.
        
        Args:
            batch_size: Number of samples to generate
            backfill_hours: Number of hours to go back for the first sample
        """
        print(f"\n🚀 Iniciando geração de lote de {batch_size} amostras...")
        
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=backfill_hours)
        time_step = (end_time - start_time) / batch_size
        
        start = time.time()
        generated = 0
        
        for i in range(batch_size):
            # Calculate timestamp for this sample
            sample_time = start_time + (i * time_step)
            
            # Generate and publish sample
            if self.generate_and_publish(sample_time):
                generated += 1
            
            # Progress update every 10% or at least every 100 samples
            if (i + 1) % max(1, min(100, batch_size // 10)) == 0:
                print(f"  Geradas {i + 1}/{batch_size} amostras...")
        
        duration = time.time() - start
        success_rate = (generated / batch_size) * 100
        
        print(f"\n✅ Geração de lote concluída!")
        print(f"   • Total de amostras: {batch_size}")
        print(f"   • Amostras geradas com sucesso: {generated} ({success_rate:.1f}%)")
        print(f"   • Período coberto: {backfill_hours} horas")
        print(f"   • Tempo total: {duration:.2f} segundos")
        print(f"   • Média: {batch_size/duration:.1f} amostras/segundo\n")
    
    def run(self, batch_mode: bool = False, batch_size: int = 100, backfill_hours: int = 24):
        """
        Run the simulator.
        
        Args:
            batch_mode: If True, run in batch mode and exit
            batch_size: Number of samples to generate in batch mode
            backfill_hours: Number of hours to go back for batch generation
        """
        logger.info(f"Starting wearable simulator for {self.patient_id} (device: {self.device_id})")
        
        if not self.connect():
            logger.error("Failed to connect to MQTT broker. Exiting.")
            return
        
        # Publish device metadata
        self.publish_device_metadata()
        
        if batch_mode:
            # Run in batch mode
            self.generate_batch(batch_size, backfill_hours)
            logger.info("Batch generation completed. Exiting.")
            self.disconnect()
            return
        
        # Normal streaming mode
        logger.info(f"Publishing to topic: {self.mqtt_topic}")
        logger.info(f"Sample rate: {self.sample_rate} samples/minute")
        logger.info(f"Health check available at: http://localhost:{self.health_check_port}/health")
        
        try:
            while running:
                start_time = time.time()
                
                # Generate and publish a sample
                self.generate_and_publish()
                
                # Calculate sleep time to maintain the desired sample rate
                elapsed = time.time() - start_time
                sleep_time = max(0, self.sample_interval - elapsed)
                
                # Sleep until next sample
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Simulator stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error in simulator loop: {e}", exc_info=True)
        finally:
            logger.info("Shutting down simulator...")
            self.disconnect()
            logger.info("Simulator shutdown complete")

if __name__ == "__main__":
    simulator = WearableSimulator()
    
    # Check if we should run in batch mode
    batch_mode = os.getenv('BATCH_MODE', 'false').lower() == 'true'
    batch_size = int(os.getenv('BATCH_SIZE', '1000'))
    backfill_hours = int(os.getenv('BACKFILL_HOURS', '24'))
    
    if batch_mode:
        logger.info(f"🚀 Starting in BATCH MODE: {batch_size} samples over {backfill_hours} hours")
    
    # Run the simulator with the appropriate parameters
    simulator.run(
        batch_mode=batch_mode,
        batch_size=batch_size,
        backfill_hours=backfill_hours
    )
