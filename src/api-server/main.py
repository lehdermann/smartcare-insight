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
import time
import uuid
import json
import asyncio
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, Path, Security, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_server.log')
    ]
)
logger = logging.getLogger(__name__)

from models import (
    Patient, VitalSign, Alert, AlertUpdate, AnalysisRequest, 
    ComparativeAnalysisRequest, EventBasedAnalysisRequest, TrendAnalysisRequest, AnalysisResponse,
    Token, User, SystemStatus, VitalSignsResponse
)
from auth import (
    authenticate_user, create_access_token, create_refresh_token,
    get_current_user, get_current_active_user, get_scopes_for_role,
    fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES
)
from services import (
    get_alerts, get_alert, update_alert, get_llm_analysis,
    get_trend_analysis, check_service_health
)

# Load environment variables
load_dotenv()

# API Configuration
API_VERSION = "1.0.0"
API_TITLE = "SmartCare Insight API"
API_DESCRIPTION = "API for the SmartCare Insight system"

# InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "healthcare-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "healthcare")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "healthcare_monitoring")

# Service URLs
ALERT_MANAGER_URL = os.getenv("ALERT_MANAGER_URL", "http://localhost:8000")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8001")

# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
influx_client = None
query_api = None

# Mock patients database
patients_db = {
    "patient-1": {
        "id": "patient-1",
        "name": "John Doe",
        "age": 65,
        "gender": "male",
        "location": "Room 101, Bed A",
        "monitoring_start": datetime(2025, 5, 20),
        "location_type": "hospital",
        "primary_condition": "Hypertension",
        "notes": "Patient has a history of heart disease"
    },
    "patient-2": {
        "id": "patient-2",
        "name": "Jane Smith",
        "age": 42,
        "gender": "female",
        "location": "Home",
        "monitoring_start": datetime(2025, 5, 22),
        "location_type": "home",
        "primary_condition": "Diabetes Type 2",
        "notes": "Patient is on insulin therapy"
    },
    "patient-3": {
        "id": "patient-3",
        "name": "Robert Johnson",
        "age": 78,
        "gender": "male",
        "location": "Pneumology Clinic",
        "monitoring_start": datetime(2025, 5, 19),
        "location_type": "clinic",
        "primary_condition": "COPD",
        "notes": "Patient requires oxygen supplementation"
    }
}

# WebSocket connections
websocket_connections = {}

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

async def fetch_patient_vitals(
    patient_id: str,
    start_time: datetime,
    end_time: datetime,
    measurement_types: Optional[List[str]] = None,
    interval: Optional[str] = None
) -> List[VitalSign]:
    """
    Fetch patient vital signs from InfluxDB.
    
    Parameters:
    -----------
    patient_id : str
        Patient ID
    start_time : datetime
        Start time for data retrieval
    end_time : datetime
        End time for data retrieval
    measurement_types : Optional[List[str]]
        List of measurement types to retrieve, or None for all
    interval : Optional[str]
        Aggregation interval (e.g., "1m", "5m", "1h"), or None for raw data
        
    Returns:
    --------
    List[VitalSign]
        List of vital sign readings
    """
    # Format datetime for InfluxDB Flux query with time() function
    def format_for_flux(dt):
        # Ensure datetime is timezone-aware in UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # Format as ISO 8601 string with 'Z' timezone
        iso_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        # Wrap with time() function for Flux
        return f'time(v: "{iso_str}")'
    
    start_rfc = format_for_flux(start_time)
    end_rfc = format_for_flux(end_time)
    
        # Build measurement type filter
    measurement_filter = ""
    if measurement_types:
        if len(measurement_types) == 1:
            measurement_filter = f' and r.measurement_type == "{measurement_types[0]}"'
        else:
            # Create multiple OR conditions for measurement types
            or_conditions = [f'r.measurement_type == "{mt}"' for mt in measurement_types]
            measurement_filter = ' and (' + ' or '.join(or_conditions) + ')'
    
    # Build Flux query
    if interval:
        # Aggregated query with window
        flux_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: {start_rfc}, stop: {end_rfc})
            |> filter(fn: (r) => r._measurement == "vital_signs")
            |> filter(fn: (r) => r.patient_id == "{patient_id}"{measurement_filter})
            |> filter(fn: (r) => r._field != "is_anomaly")
            |> window(every: {interval})
            |> mean()
            |> duplicate(column: "_stop", as: "_time")
            |> yield(name: "mean")
        '''
    else:
        # Raw data query
        flux_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: {start_rfc}, stop: {end_rfc})
            |> filter(fn: (r) => r._measurement == "vital_signs")
            |> filter(fn: (r) => r.patient_id == "{patient_id}"{measurement_filter})
            |> filter(fn: (r) => r._field != "is_anomaly")
        '''
    
    # Log the Flux query for debugging
    print(f"\nFlux Query:\n{flux_query}\n")
    
    try:
        # Execute query
        print("Debug: Executing query")
        result = query_api.query(query=flux_query)
        print(f"Debug: Query returned {len(result)} tables")
        
        # Process results
        vitals = []
        for i, table in enumerate(result):
            if table.records:
                print(f"Table {i} fields: {list(table.records[0].values.keys())}")
            else:
                print(f"Table {i}: No records")
            for j, record in enumerate(table.records[:2]):  # Print first 2 records of each table
                print(f"  Record {j}: {record.values}")
        for table in result:
            for record in table.records:
                # Extract data from the record
                timestamp = record.values.get('_time')
                value = record.values.get('_value')
                measurement_type = record.values.get('measurement_type')
                is_anomaly = record.values.get('is_anomaly', False)
                device_id = record.values.get('device_id')
                
                if all([timestamp, value is not None, measurement_type]):
                    vitals.append(VitalSign(
                        timestamp=timestamp,
                        value=value,
                        measurement_type=measurement_type,
                        is_anomaly=is_anomaly,
                        patient_id=patient_id,
                        device_id=device_id
                    ))
        
        return vitals
        
    except Exception as e:
        import traceback
        error_msg = f"Error fetching patient vitals: {str(e)}\n\nQuery:\n{flux_query}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_msg)
        # Log the error to a file for debugging
        with open("api_errors.log", "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} - {error_msg}\n\n")
        # Return empty list instead of None to avoid breaking the API response
        return []

async def fetch_latest_vitals(
    patient_id: str,
    measurement_types: Optional[List[str]] = None
) -> List[VitalSign]:
    """
    Fetch the latest vital signs for a patient.
    
    Parameters:
    -----------
    patient_id : str
        Patient ID
    measurement_types : Optional[List[str]]
        List of measurement types to retrieve, or None for all
        
    Returns:
    --------
    List[VitalSign]
        List of latest vital sign readings
    """
        # Build measurement type filter
    measurement_filter = ""
    if measurement_types:
        if len(measurement_types) == 1:
            measurement_filter = f' and r.measurement_type == "{measurement_types[0]}"'
        else:
            # Create multiple OR conditions for measurement types
            or_conditions = [f'r.measurement_type == "{mt}"' for mt in measurement_types]
            measurement_filter = ' and (' + ' or '.join(or_conditions) + ')'
    
    # Build Flux query to get the latest reading for each measurement type
    flux_query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -1h)
        |> filter(fn: (r) => r._measurement == "vital_signs")
        |> filter(fn: (r) => r.patient_id == "{patient_id}"{measurement_filter})
        |> filter(fn: (r) => r._field != "is_anomaly")
        |> group(columns: ["measurement_type"])
        |> last()
    '''
    
    try:
        # Execute query
        print("Debug: Executing query")
        result = query_api.query(query=flux_query)
        print(f"Debug: Query returned {len(result)} tables")
        
        # Process results
        vitals = []
        for i, table in enumerate(result):
            if table.records:
                print(f"Table {i} fields: {list(table.records[0].values.keys())}")
            else:
                print(f"Table {i}: No records")
            for j, record in enumerate(table.records[:2]):  # Print first 2 records of each table
                print(f"  Record {j}: {record.values}")
        for table in result:
            for record in table.records:
                # Extract data from the record
                timestamp = record.values.get('_time')
                value = record.values.get('_value')
                measurement_type = record.values.get('measurement_type')
                is_anomaly = record.values.get('is_anomaly', False)
                device_id = record.values.get('device_id')
                
                if all([timestamp, value is not None, measurement_type]):
                    vitals.append(VitalSign(
                        timestamp=timestamp,
                        value=value,
                        measurement_type=measurement_type,
                        is_anomaly=is_anomaly,
                        patient_id=patient_id,
                        device_id=device_id
                    ))
        
        return vitals
        
    except Exception as e:
        print(f"Error fetching latest vitals: {e}")
        return []

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SmartCare Insight API",
        "version": API_VERSION,
        "documentation": "/docs"
    }

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Get an access token."""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get scopes for the user's role
    scopes = get_scopes_for_role(user.role)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": scopes},
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(
        data={"sub": user.username, "scopes": scopes}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.get("/health", response_model=SystemStatus)
async def health_check():
    """Check the health of the system."""
    # Check InfluxDB
    influxdb_health = {"status": "unknown"}
    try:
        if influx_client is None:
            setup_influxdb()
        
        if influx_client:
            health = influx_client.health()
            influxdb_health = {
                "status": "healthy" if health.status == "pass" else "unhealthy",
                "message": health.message
            }
    except Exception as e:
        influxdb_health = {
            "status": "error",
            "message": str(e)
        }
    
    # Check Alert Manager
    alert_manager_health = await check_service_health(ALERT_MANAGER_URL)
    
    # Check LLM Service
    llm_service_health = await check_service_health(LLM_SERVICE_URL)
    
    # Determine overall status
    components_status = [
        influxdb_health["status"],
        alert_manager_health["status"],
        llm_service_health["status"]
    ]
    
    if "error" in components_status:
        overall_status = "error"
    elif "unhealthy" in components_status:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return SystemStatus(
        status=overall_status,
        version=API_VERSION,
        components={
            "influxdb": influxdb_health,
            "alert_manager": alert_manager_health,
            "llm_service": llm_service_health
        },
        timestamp=datetime.utcnow()
    )

# Patient endpoints

@app.get("/api/patients", response_model=List[Patient])
async def get_patients(
    current_user: User = Security(get_current_user, scopes=["patients:read"])
):
    """Get all patients."""
    patients = [Patient(**patient) for patient in patients_db.values()]
    # Log the response
    print(f"API Response - GET /api/patients: {[p.dict() for p in patients]}")
    return patients

@app.get("/api/patients/{patient_id}", response_model=Patient)
async def get_patient(
    patient_id: str = Path(..., description="Patient ID"),
    current_user: User = Security(get_current_user, scopes=["patients:read"])
):
    """Get a specific patient."""
    print(f"API Request - GET /api/patients/{patient_id}")
    if patient_id not in patients_db:
        error_msg = f"Patient not found: {patient_id}"
        print(f"API Error - {error_msg}")
        raise HTTPException(status_code=404, detail=error_msg)
    
    patient = Patient(**patients_db[patient_id])
    print(f"API Response - GET /api/patients/{patient_id}: {patient.dict()}")
    return patient

# Vital signs endpoints

@app.get("/api/patients/{patient_id}/vitals", response_model=VitalSignsResponse)
async def get_patient_vitals(
    patient_id: str = Path(..., description="Patient ID"),
    start: datetime = Query(..., description="Start time (ISO8601)"),
    end: datetime = Query(..., description="End time (ISO8601)"),
    measurement_types: Optional[List[str]] = Query(None, description="Measurement types"),
    interval: Optional[str] = Query(None, description="Aggregation interval"),
    current_user: User = Security(get_current_user, scopes=["vitals:read"]),
    query_api: QueryApi = Depends(get_influxdb_client)
):
    """Get vital signs for a patient."""
    # Check if patient exists
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Fetch vitals
    vitals = await fetch_patient_vitals(
        patient_id=patient_id,
        start_time=start,
        end_time=end,
        measurement_types=measurement_types,
        interval=interval
    )
    
    return VitalSignsResponse(
        patient_id=patient_id,
        vitals=vitals,
        start_time=start,
        end_time=end,
        count=len(vitals)
    )

@app.get("/api/patients/{patient_id}/vitals/latest", response_model=VitalSignsResponse)
async def get_latest_vitals(
    patient_id: str = Path(..., description="Patient ID"),
    measurement_types: Optional[List[str]] = Query(None, description="Measurement types"),
    current_user: User = Security(get_current_user, scopes=["vitals:read"]),
    query_api: QueryApi = Depends(get_influxdb_client)
):
    """Get the latest vital signs for a patient."""
    # Check if patient exists
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Fetch latest vitals
    vitals = await fetch_latest_vitals(
        patient_id=patient_id,
        measurement_types=measurement_types
    )
    
    # Use current time for the response
    now = datetime.utcnow()
    
    return VitalSignsResponse(
        patient_id=patient_id,
        vitals=vitals,
        start_time=now - timedelta(hours=1),  # Last hour
        end_time=now,
        count=len(vitals)
    )

# Alert endpoints

@app.get("/api/alerts", response_model=List[Alert])
async def get_all_alerts(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    measurement_type: Optional[str] = Query(None, description="Filter by measurement type"),
    limit: int = Query(100, description="Maximum number of alerts to return"),
    current_user: User = Security(get_current_user, scopes=["alerts:read"])
):
    """Get all alerts with optional filtering."""
    return await get_alerts(
        patient_id=patient_id,
        status=status,
        severity=severity,
        measurement_type=measurement_type,
        limit=limit
    )

@app.get("/api/patients/{patient_id}/alerts", response_model=List[Alert])
async def get_patient_alerts(
    patient_id: str = Path(..., description="Patient ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of alerts to return"),
    current_user: User = Security(get_current_user, scopes=["alerts:read"])
):
    """Get alerts for a specific patient."""
    # Check if patient exists
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return await get_alerts(
        patient_id=patient_id,
        status=status,
        limit=limit
    )

@app.get("/api/alerts/{alert_id}", response_model=Alert)
async def get_alert_by_id(
    alert_id: str = Path(..., description="Alert ID"),
    current_user: User = Security(get_current_user, scopes=["alerts:read"])
):
    """Get a specific alert by ID."""
    alert = await get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert

@app.put("/api/alerts/{alert_id}", response_model=Alert)
async def update_alert_status(
    alert_id: str = Path(..., description="Alert ID"),
    alert_update: AlertUpdate = None,
    current_user: User = Security(get_current_user, scopes=["alerts:write"])
):
    """Update an alert's status."""
    # Set the user who acknowledged the alert
    if alert_update.status == "acknowledged" and not alert_update.acknowledged_by:
        alert_update.acknowledged_by = current_user.username
    
    updated_alert = await update_alert(alert_id, alert_update)
    if not updated_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return updated_alert

# Analysis endpoints

@app.post("/api/analysis", response_model=AnalysisResponse)
async def analyze_patient_data(
    analysis_request: AnalysisRequest,
    current_user: User = Security(get_current_user, scopes=["analysis:read"])
):
    """Analyze patient data using the LLM service."""
    # Check if patient exists
    if analysis_request.patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    analysis = await get_llm_analysis(analysis_request)
    if not analysis:
        raise HTTPException(status_code=500, detail="Failed to generate analysis")
    
    return analysis

@app.post("/api/analysis/time-window", response_model=AnalysisResponse)
async def analyze_time_window(
    analysis_request: AnalysisRequest,
    current_user: User = Security(get_current_user, scopes=["analysis:read"])
):
    """Analyze patient data over a specific time window."""
    # Force analysis type to time_window
    analysis_request.analysis_type = "time_window"
    
    # Adicionar parâmetros obrigatórios para a análise de janela de tempo
    # Estes são necessários para o LLM service
    analysis_request.window_count = 3
    analysis_request.window_duration_hours = 8.0
    analysis_request.window_interval_hours = 0.0
    
    print(f"Added required parameters for time-window analysis: window_count={analysis_request.window_count}, window_duration_hours={analysis_request.window_duration_hours}")

    
    return await analyze_patient_data(analysis_request, current_user)

@app.post("/api/analysis/event-based", response_model=AnalysisResponse)
async def analyze_event_based(
    analysis_request: EventBasedAnalysisRequest,
    current_user: User = Security(get_current_user, scopes=["analysis:read"])
):
    """Analyze patient data around specific events."""
    # Force analysis type to event_based
    analysis_request.analysis_type = "event_based"
    
    return await analyze_patient_data(analysis_request, current_user)

@app.post("/api/analysis/comparative", response_model=AnalysisResponse)
async def analyze_comparative(
    analysis_request: ComparativeAnalysisRequest,
    current_user: User = Security(get_current_user, scopes=["analysis:read"])
):
    """Compare patient data between two time periods."""
    # Force analysis type to comparative
    analysis_request.analysis_type = "comparative"
    
    return await analyze_patient_data(analysis_request, current_user)

@app.post("/api/analysis/trend-analysis", response_model=AnalysisResponse)
async def analyze_trend(
    analysis_request: TrendAnalysisRequest,
    current_user: User = Security(get_current_user, scopes=["analysis:read"])
):
    """Analyze trends in patient data."""
    # Log the request
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]  # Identificador único para esta requisição
    
    print(f"\n==== TREND ANALYSIS REQUEST [{request_id}] ====")
    print(f"Iniciado em: {datetime.utcnow().isoformat()}")
    print(f"Patient ID: {analysis_request.patient_id}")
    print(f"Analysis Type: {analysis_request.analysis_type}\n")
    
    # Check if patient exists
    if analysis_request.patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Set analysis type to trend_analysis
    analysis_request.analysis_type = "trend_analysis"
    
    # Log the parameters being used for trend analysis
    print(f"\n=== TREND ANALYSIS PARAMETERS ===")
    print(f"Window Count: {analysis_request.window_count}")
    print(f"Window Duration (hours): {analysis_request.window_duration_hours}")
    print(f"Window Interval (hours): {analysis_request.window_interval_hours}")
    print(f"Measurement Types: {analysis_request.measurement_types}")
    
    # Get trend analysis
    analysis = await get_trend_analysis(analysis_request)
    
    if not analysis:
        raise HTTPException(status_code=500, detail="Failed to generate trend analysis")
    
    # Ensure analysis is a dictionary
    if not isinstance(analysis, dict):
        analysis = {"summary": "Analysis completed"}
    
    # Set analysis type in response
    analysis["analysis_type"] = "trend_analysis"
    
    # Log basic response info
    if "insights" in analysis:
        logger.debug(f"Generated {len(analysis.get('recommendations', []))} recommendations")
    
    # Convert to AnalysisResponse model explicitly
    try:
        # Try to create a proper AnalysisResponse object
        from models import AnalysisResponse, AnalysisType, Insight, Recommendation
        
        # Create insights and recommendations objects
        insights = []
        if "insights" in analysis:
            for insight in analysis["insights"]:
                insights.append(Insight(**insight))
        
        recommendations = []
        if "recommendations" in analysis:
            for rec in analysis["recommendations"]:
                recommendations.append(Recommendation(**rec))
        
        # Create the response object
        response = AnalysisResponse(
            patient_id=analysis.get("patient_id", analysis_request.patient_id),
            analysis_type="trend_analysis",  # Use the string value directly
            timestamp=analysis.get("timestamp", datetime.utcnow()),
            summary=analysis.get("summary", "Analysis completed"),
            insights=insights,
            recommendations=recommendations,
            data_points_analyzed=analysis.get("data_points_analyzed", 0),
            time_period=analysis.get("time_period", ""),
            windows=analysis.get("windows", None)
        )
        print(f"Successfully created AnalysisResponse object\n")
        
        # Calcular e registrar o tempo total de processamento
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"==== TREND ANALYSIS COMPLETED [{request_id}] ====")
        print(f"Tempo total de processamento: {processing_time:.2f} segundos")
        print(f"Finalizado em: {datetime.utcnow().isoformat()}\n")
        
        return response
    except Exception as e:
        print(f"Error creating AnalysisResponse: {str(e)}\n")
        # Fall back to returning the dict and let FastAPI handle validation
        return analysis

# WebSocket endpoint

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    
    try:
        # Get client ID and patient ID from query parameters
        query_params = dict(websocket.query_params)
        client_id = query_params.get("client_id", str(id(websocket)))
        patient_id = query_params.get("patient_id")
        
        # Store the connection
        key = f"{client_id}:{patient_id}" if patient_id else client_id
        websocket_connections[key] = websocket
        
        # Send initial data
        if patient_id:
            # Get latest vitals for the patient
            vitals = await fetch_latest_vitals(patient_id)
            await websocket.send_json({
                "type": "vitals",
                "data": [v.dict() for v in vitals]
            })
            
            # Get active alerts for the patient
            alerts = await get_alerts(patient_id=patient_id, status="active")
            await websocket.send_json({
                "type": "alerts",
                "data": alerts
            })
        
        # Keep the connection alive
        while True:
            # Wait for messages (can be used for client requests)
            data = await websocket.receive_text()
            
            # Process client messages if needed
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except json.JSONDecodeError:
                pass
            
    except WebSocketDisconnect:
        # Remove the connection
        keys_to_remove = []
        for key, ws in websocket_connections.items():
            if ws == websocket:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del websocket_connections[key]

@app.on_event("startup")
async def startup_event():
    """Run when the application starts."""
    # Set up InfluxDB
    setup_influxdb()

@app.on_event("shutdown")
async def shutdown_event():
    """Run when the application shuts down."""
    global influx_client
    
    # Close InfluxDB client
    if influx_client:
        influx_client.close()
    
    # Close all WebSocket connections
    for websocket in websocket_connections.values():
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
