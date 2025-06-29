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

import os
import json
import time
import signal
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER", "healthcare")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "healthcare")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "healthcare/patient/+/+")  # Subscribe to all patients and measurements

# InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "healthcare-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "healthcare")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "healthcare_monitoring")

# Vital signs normal ranges for anomaly detection
VITAL_RANGES = {
    'hr': (60, 100),         # Heart rate (bpm)
    'bp_sys': (100, 140),    # Systolic blood pressure (mmHg)
    'bp_dia': (60, 90),      # Diastolic blood pressure (mmHg)
    'oxygen': (95, 100),     # Oxygen saturation (%)
    'glucose': (70, 120),    # Blood glucose (mg/dL)
    'activity': (0, 1)       # Activity level (0-1)
}

# Global variables
running = True
message_count = 0
message_lock = threading.Lock()
influx_client = None
write_api = None

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        print(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        # Subscribe to all healthcare topics
        client.subscribe(MQTT_TOPIC, qos=1)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"Failed to connect to MQTT broker, return code: {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received from the MQTT broker."""
    global message_count
    
    try:
        # Parse the JSON payload
        payload = json.loads(msg.payload.decode('utf-8'))
        
        # Extract common fields
        timestamp = payload.get('timestamp')
        patient_id = payload.get('patient_id')
        device_id = payload.get('device_id')
        
        # Check if this is a valid payload with required fields
        if not all([timestamp, patient_id, device_id]):
            print(f"Invalid payload received: {payload}")
            return
        
        # Process each vital sign measurement in the payload
        vital_signs_processed = 0
        
        # Process each vital sign type if present in the payload
        for measurement_type in ['hr', 'bp_sys', 'bp_dia', 'oxygen', 'glucose', 'activity']:
            if measurement_type in payload:
                value = payload[measurement_type]
                
                # Process the data for this measurement type
                processed_data = process_data(measurement_type, value, timestamp, patient_id, device_id)
                
                # Store the processed data in InfluxDB
                store_data(processed_data)
                vital_signs_processed += 1
        
        # Update message count if we processed at least one vital sign
        if vital_signs_processed > 0:
            with message_lock:
                message_count += 1
                if message_count % 100 == 0:
                    print(f"Processed {message_count} messages")
                    
            # Log the received data (for debugging)
            if message_count % 20 == 0:  # Log every 20th message to avoid console spam
                print(f"Received data with {vital_signs_processed} vital signs: {patient_id}")
        else:
            print(f"No vital signs found in payload: {payload}")
            
    except json.JSONDecodeError:
        print(f"Failed to parse JSON payload: {msg.payload}")
    except Exception as e:
        print(f"Error processing message: {e}")
        print(f"Payload: {msg.payload}")
        import traceback
        traceback.print_exc()

def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects from the MQTT broker."""
    if rc != 0:
        print(f"Unexpected disconnection from MQTT broker, return code: {rc}")
    else:
        print("Disconnected from MQTT broker")

def process_data(measurement_type, value, timestamp, patient_id, device_id):
    """
    Process the raw data from MQTT.
    
    Parameters:
    -----------
    measurement_type : str
        Type of vital sign measurement
    value : float
        Measured value
    timestamp : str
        ISO8601 timestamp
    patient_id : str
        Patient identifier
    device_id : str
        Device identifier
        
    Returns:
    --------
    dict
        Processed data with additional fields
    """
    # Check if the value is anomalous
    is_anomaly = False
    if measurement_type in VITAL_RANGES:
        min_val, max_val = VITAL_RANGES[measurement_type]
        is_anomaly = value < min_val or value > max_val
    
    # Convert timestamp to datetime if it's a string
    if isinstance(timestamp, str):
        try:
            # Parse ISO8601 timestamp
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            # If parsing fails, use current time
            timestamp = datetime.utcnow()
    
    # Create processed data dictionary
    processed_data = {
        'measurement_type': measurement_type,
        'value': value,
        'timestamp': timestamp,
        'patient_id': patient_id,
        'device_id': device_id,
        'is_anomaly': is_anomaly
    }
    
    return processed_data

def store_data(data):
    """
    Store processed data in InfluxDB.
    
    Parameters:
    -----------
    data : dict
        Processed data to store
    """
    global write_api
    
    try:
        # Create a Point
        point = Point("vital_signs") \
            .tag("patient_id", data['patient_id']) \
            .tag("device_id", data['device_id']) \
            .tag("measurement_type", data['measurement_type'])
        
        # Use the measurement type as the field name to avoid type conflicts
        # This way each measurement type gets its own field
        measurement_type = data['measurement_type']
        value = float(data['value'])  # Ensure consistent type (float)
        
        # Add the value with the measurement type as the field name
        point = point.field(measurement_type, value)
        
        # Add the anomaly flag
        point = point.field("is_anomaly", bool(data['is_anomaly']))
        
        # Set the timestamp
        point = point.time(data['timestamp'])
        
        # Write to InfluxDB
        write_api.write(bucket=INFLUXDB_BUCKET, record=point)
        
    except Exception as e:
        print(f"\nError storing data in InfluxDB: {e}")
        print(f"Data: {data}")
        import traceback
        traceback.print_exc()
        print()

def setup_influxdb():
    """Set up the InfluxDB client and create the bucket if it doesn't exist."""
    global influx_client, write_api
    
    try:
        # Create InfluxDB client
        influx_client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        # Create write API
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        
        # Check if the bucket exists, create it if not
        buckets_api = influx_client.buckets_api()
        bucket_list = buckets_api.find_buckets().buckets
        bucket_names = [bucket.name for bucket in bucket_list]
        
        if INFLUXDB_BUCKET not in bucket_names:
            print(f"Creating InfluxDB bucket: {INFLUXDB_BUCKET}")
            buckets_api.create_bucket(bucket_name=INFLUXDB_BUCKET, org=INFLUXDB_ORG)
        
        print(f"Connected to InfluxDB at {INFLUXDB_URL}")
        return True
        
    except Exception as e:
        print(f"Error setting up InfluxDB: {e}")
        return False

def cleanup():
    """Clean up resources before exiting."""
    global influx_client, write_api, running
    
    running = False
    
    # Close InfluxDB client
    if write_api:
        write_api.close()
    if influx_client:
        influx_client.close()
    
    print("Data processor stopped")

def signal_handler(sig, frame):
    """Handle termination signals."""
    print("Received termination signal")
    cleanup()

def main():
    """Main function to run the data processor."""
    global running
    
    print("Starting data processor")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Set up InfluxDB
    if not setup_influxdb():
        print("Failed to set up InfluxDB, exiting...")
        return
    
    # Initialize MQTT client
    client = mqtt.Client()
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Set credentials if provided
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    # Connect to MQTT broker with retry logic
    connected = False
    retry_count = 0
    max_retries = 10
    
    while not connected and retry_count < max_retries:
        try:
            print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            connected = True
        except Exception as e:
            retry_count += 1
            wait_time = min(30, 2 ** retry_count)  # Exponential backoff
            print(f"Failed to connect to MQTT broker: {e}")
            print(f"Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
            time.sleep(wait_time)
    
    if not connected:
        print("Failed to connect to MQTT broker after multiple attempts, exiting...")
        cleanup()
        return
    
    # Start the MQTT loop
    client.loop_start()
    
    # Main loop
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping data processor...")
    finally:
        # Stop the MQTT loop and disconnect
        client.loop_stop()
        client.disconnect()
        cleanup()

if __name__ == "__main__":
    main()
