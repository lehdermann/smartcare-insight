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
import uuid
import time
import signal
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from dotenv import load_dotenv

from models import Alert, AlertUpdate, AlertThreshold, AlertResponse, AlertSeverity, AlertStatus, AlertType

# Load environment variables
load_dotenv()

# InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "healthcare-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "healthcare")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "healthcare_monitoring")

# Alert Manager Configuration
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # seconds
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))  # days to keep alerts
PORT = int(os.getenv("PORT", "8000"))  # Porta para o servidor web

# Global variables
running = True
influx_client = None
query_api = None
alerts: Dict[str, Alert] = {}
thresholds: Dict[str, AlertThreshold] = {}
alert_lock = threading.Lock()

# Default thresholds for vital signs based on clinical guidelines
DEFAULT_THRESHOLDS = {
    # Heart Rate (bpm)
    'hr': [
        AlertThreshold(measurement_type='hr', min_value=60, max_value=100, severity=AlertSeverity.MEDIUM),
        AlertThreshold(measurement_type='hr', min_value=50, max_value=110, severity=AlertSeverity.LOW),
        AlertThreshold(measurement_type='hr', min_value=40, max_value=130, severity=AlertSeverity.HIGH)
    ],
    
    # Systolic Blood Pressure (mmHg)
    'bp_sys': [
        AlertThreshold(measurement_type='bp_sys', min_value=100, max_value=120, severity=AlertSeverity.LOW),
        AlertThreshold(measurement_type='bp_sys', min_value=90, max_value=140, severity=AlertSeverity.MEDIUM),
        AlertThreshold(measurement_type='bp_sys', min_value=80, max_value=160, severity=AlertSeverity.HIGH),
        AlertThreshold(measurement_type='bp_sys', min_value=70, max_value=180, severity=AlertSeverity.CRITICAL)
    ],
    
    # Diastolic Blood Pressure (mmHg)
    'bp_dia': [
        AlertThreshold(measurement_type='bp_dia', min_value=60, max_value=80, severity=AlertSeverity.LOW),
        AlertThreshold(measurement_type='bp_dia', min_value=50, max_value=90, severity=AlertSeverity.MEDIUM),
        AlertThreshold(measurement_type='bp_dia', min_value=40, max_value=100, severity=AlertSeverity.HIGH),
        AlertThreshold(measurement_type='bp_dia', min_value=30, max_value=110, severity=AlertSeverity.CRITICAL)
    ],
    
    # Oxygen Saturation (%)
    'oxygen': [
        AlertThreshold(measurement_type='oxygen', min_value=95, max_value=100, severity=AlertSeverity.LOW),
        AlertThreshold(measurement_type='oxygen', min_value=90, max_value=94, severity=AlertSeverity.MEDIUM),
        AlertThreshold(measurement_type='oxygen', min_value=85, max_value=89, severity=AlertSeverity.HIGH),
        AlertThreshold(measurement_type='oxygen', min_value=0, max_value=84, severity=AlertSeverity.CRITICAL)
    ],
    
    # Blood Glucose (mg/dL)
    'glucose': [
        AlertThreshold(measurement_type='glucose', min_value=70, max_value=140, severity=AlertSeverity.LOW),
        AlertThreshold(measurement_type='glucose', min_value=54, max_value=180, severity=AlertSeverity.MEDIUM),
        AlertThreshold(measurement_type='glucose', min_value=0, max_value=250, severity=AlertSeverity.HIGH),
        AlertThreshold(measurement_type='glucose', min_value=0, max_value=50, severity=AlertSeverity.CRITICAL),
        AlertThreshold(measurement_type='glucose', min_value=251, max_value=500, severity=AlertSeverity.CRITICAL)
    ],
    
    # Activity (binary)
    'activity': [
        AlertThreshold(measurement_type='activity', min_value=0, max_value=1, severity=AlertSeverity.LOW)
    ]
}

# Initialize FastAPI app
app = FastAPI(
    title="SmartCare Insight - Alert Manager",
    description="API for managing health monitoring alerts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_influxdb_client() -> QueryApi:
    """Get the InfluxDB query API client."""
    global query_api
    if query_api is None:
        setup_influxdb()
    return query_api

def setup_influxdb():
    """Set up the InfluxDB client."""
    global influx_client, query_api
    
    try:
        # Create InfluxDB client
        influx_client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        # Create query API
        query_api = influx_client.query_api()
        
        print(f"Connected to InfluxDB at {INFLUXDB_URL}")
        return True
        
    except Exception as e:
        print(f"Error setting up InfluxDB: {e}")
        return False

def initialize_thresholds():
    """Initialize alert thresholds with default values.
    
    Each measurement type can have multiple thresholds with different severity levels.
    The most severe threshold that is exceeded will be used for alerting.
    """
    global thresholds
    
    for measurement_type, threshold_list in DEFAULT_THRESHOLDS.items():
        threshold_key = f"{measurement_type}:global"
        thresholds[threshold_key] = threshold_list
        
        # Log the thresholds for this measurement type
        print(f"Initialized {len(threshold_list)} thresholds for {measurement_type}")
        for t in threshold_list:
            print(f"  - {t.min_value} to {t.max_value}: {t.severity}")
    
    print("All alert thresholds initialized")

def check_for_anomalies():
    """Check for anomalies in the InfluxDB data and generate alerts."""
    global alerts, thresholds
    
    # Process each vital sign type separately to avoid schema collision
    vital_sign_types = ['hr', 'bp_sys', 'bp_dia', 'oxygen', 'glucose', 'activity']
    
    for measurement_type in vital_sign_types:
        try:
            # Get the latest data points for this measurement type
            flux_query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -5m)
                |> filter(fn: (r) => r._measurement == "vital_signs")
                |> filter(fn: (r) => r._field == "{measurement_type}")
                |> group(columns: ["patient_id"])
                |> last()
            '''
            
            result = query_api.query(query=flux_query)
            
            for table in result:
                for record in table.records:
                    # Extract data from the record
                    patient_id = record.values.get('patient_id')
                    value = record.values.get('_value')
                    timestamp = record.values.get('_time')
                    is_anomaly = False
                    
                    if not all([patient_id, value is not None, timestamp]):
                        continue
                    
                    # Get all thresholds for this measurement type
                    threshold_key = f"{measurement_type}:{patient_id}"
                    if threshold_key not in thresholds:
                        threshold_key = f"{measurement_type}:global"
                    
                    thresholds_list = thresholds.get(threshold_key, [])
                    if not thresholds_list:
                        continue
                    
                    # Find the most severe threshold that was exceeded
                    max_severity = None
                    message = ""
                    is_outside_range = False
                    
                    for threshold in sorted(thresholds_list, key=lambda x: x.severity, reverse=True):
                        if ((threshold.min_value is not None and value < threshold.min_value) or
                            (threshold.max_value is not None and value > threshold.max_value)):
                            is_outside_range = True
                            max_severity = max(max_severity, threshold.severity) if max_severity else threshold.severity
                            
                            if value < threshold.min_value:
                                message = f"{measurement_type.upper()} critically low ({value})" if threshold.severity == AlertSeverity.CRITICAL else \
                                         f"{measurement_type.upper()} below normal range ({value})"
                            else:
                                message = f"{measurement_type.upper()} critically high ({value})" if threshold.severity == AlertSeverity.CRITICAL else \
                                         f"{measurement_type.upper()} above normal range ({value})"
                            break  # Stop at the most severe threshold
                    
                    # Generate alert if any threshold was exceeded
                    if is_outside_range or is_anomaly:
                        # Create a unique alert ID
                        alert_id = str(uuid.uuid4())
                        
                        # Create alert with the most severe threshold that was exceeded
                        alert = Alert(
                            id=alert_id,
                            patient_id=patient_id,
                            measurement_type=measurement_type,
                            value=value,
                            timestamp=timestamp,
                            severity=max_severity if max_severity else AlertSeverity.MEDIUM,
                            status=AlertStatus.ACTIVE,
                            alert_type=AlertType.THRESHOLD if is_outside_range else AlertType.ANOMALY,
                            message=message if is_outside_range else f"Anomaly detected in {measurement_type.upper()} ({value})"
                        )
                        
                        # Add alert to the dictionary
                        with alert_lock:
                            alerts[alert_id] = alert
                        
                        print(f"Generated alert: {alert.message} for patient {patient_id}")
                        
        except Exception as e:
            print(f"Error checking for anomalies in {measurement_type}: {e}")
    
    # Clean up old alerts after processing all measurement types
    try:
        cleanup_old_alerts()
    except Exception as e:
        print(f"Error cleaning up old alerts: {e}")


def cleanup_old_alerts():
    """Remove old resolved alerts to prevent memory buildup."""
    global alerts
    
    with alert_lock:
        current_time = datetime.utcnow()
        retention_cutoff = current_time - timedelta(days=RETENTION_DAYS)
        
        # Find alerts to remove
        alerts_to_remove = []
        for alert_id, alert in alerts.items():
            # Remove resolved alerts older than retention period
            if alert.status == AlertStatus.RESOLVED and alert.resolved_at:
                if alert.resolved_at < retention_cutoff:
                    alerts_to_remove.append(alert_id)
        
        # Remove the alerts
        for alert_id in alerts_to_remove:
            del alerts[alert_id]
        
        if alerts_to_remove:
            print(f"Cleaned up {len(alerts_to_remove)} old alerts")

def alert_monitor_thread():
    """Thread function to periodically check for anomalies."""
    global running
    
    print(f"Starting alert monitor thread (checking every {CHECK_INTERVAL} seconds)")
    
    while running:
        try:
            check_for_anomalies()
        except Exception as e:
            print(f"Error in alert monitor thread: {e}")
        
        # Sleep until next check
        time.sleep(CHECK_INTERVAL)
    
    print("Alert monitor thread stopped")

def signal_handler(sig, frame):
    """Handle termination signals."""
    global running
    print("Received termination signal")
    running = False

def cleanup():
    """Clean up resources before exiting."""
    global influx_client, running
    
    running = False
    
    # Close InfluxDB client
    if influx_client:
        influx_client.close()
    
    print("Alert manager stopped")

# API Endpoints

@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Alert Manager API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    # Check if InfluxDB connection is working
    try:
        if not influx_client or not query_api:
            return {"status": "error", "message": "InfluxDB client not initialized"}
            
        # Simple query to check if InfluxDB is responsive
        query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -10s) |> limit(n: 1)'
        query_api.query(query=query)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "influxdb": "connected",
                "alert_monitor": "running" if running else "stopped"
            },
            "alerts_count": len(alerts)
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "message": str(e)
        }

@app.get("/alerts", response_model=AlertResponse)
async def get_alerts(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    status: Optional[AlertStatus] = Query(None, description="Filter by alert status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by alert severity"),
    measurement_type: Optional[str] = Query(None, description="Filter by measurement type"),
    limit: int = Query(100, description="Maximum number of alerts to return"),
    query_api: QueryApi = Depends(get_influxdb_client)
):
    """Get all alerts with optional filtering."""
    with alert_lock:
        filtered_alerts = list(alerts.values())
        
        # Apply filters
        if patient_id:
            filtered_alerts = [a for a in filtered_alerts if a.patient_id == patient_id]
        if status:
            filtered_alerts = [a for a in filtered_alerts if a.status == status]
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.severity == severity]
        if measurement_type:
            filtered_alerts = [a for a in filtered_alerts if a.measurement_type == measurement_type]
        
        # Sort by timestamp (newest first) and limit
        filtered_alerts.sort(key=lambda a: a.timestamp, reverse=True)
        filtered_alerts = filtered_alerts[:limit]
        
        return AlertResponse(alerts=filtered_alerts, count=len(filtered_alerts))

@app.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert(
    alert_id: str = Path(..., description="Alert ID"),
    query_api: QueryApi = Depends(get_influxdb_client)
):
    """Get a specific alert by ID."""
    with alert_lock:
        if alert_id not in alerts:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alerts[alert_id]

@app.put("/alerts/{alert_id}", response_model=Alert)
async def update_alert(
    alert_id: str = Path(..., description="Alert ID"),
    alert_update: AlertUpdate = None,
    query_api: QueryApi = Depends(get_influxdb_client)
):
    """Update an alert's status."""
    with alert_lock:
        if alert_id not in alerts:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert = alerts[alert_id]
        
        alert.status = alert_update.status
        current_time = datetime.utcnow()

        if alert_update.status == AlertStatus.ACKNOWLEDGED:
            alert.acknowledged_at = current_time
            alert.acknowledged_by = alert_update.acknowledged_by
        elif alert_update.status == AlertStatus.RESOLVED:
            alert.resolved_at = current_time
        
        return alert

@app.get("/thresholds", response_model=List[AlertThreshold])
async def get_thresholds(
    measurement_type: Optional[str] = Query(None, description="Filter by measurement type"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    query_api: QueryApi = Depends(get_influxdb_client)
):
    """Get all alert thresholds with optional filtering."""
    filtered_thresholds = list(thresholds.values())
    
    # Apply filters
    if measurement_type:
        filtered_thresholds = [t for t in filtered_thresholds if t.measurement_type == measurement_type]
    if patient_id:
        # Include both patient-specific and global thresholds
        filtered_thresholds = [t for t in filtered_thresholds if t.patient_id == patient_id or t.patient_id is None]
    
    return filtered_thresholds

@app.post("/thresholds", response_model=AlertThreshold)
async def create_threshold(
    threshold: AlertThreshold,
    query_api: QueryApi = Depends(get_influxdb_client)
):
    """Create or update an alert threshold."""
    # Determine the threshold key
    patient_id = threshold.patient_id or "global"
    threshold_key = f"{threshold.measurement_type}:{patient_id}"
    
    # Store the threshold
    thresholds[threshold_key] = threshold
    
    return threshold

@app.on_event("startup")
async def startup_event():
    """Run when the application starts."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Set up InfluxDB
    setup_influxdb()
    
    # Initialize default thresholds
    initialize_thresholds()
    
    # Start the alert monitor thread
    monitor_thread = threading.Thread(target=alert_monitor_thread)
    monitor_thread.daemon = True
    monitor_thread.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Run when the application shuts down."""
    cleanup()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
