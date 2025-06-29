#
# SmartCare Insight - utils.py
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
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8002")
API_TIMEOUT = 10.0  # seconds
TREND_ANALYSIS_TIMEOUT = 300.0  # 5 minutes - extended timeout for trend analysis requests

# Authentication state
auth_token = None
auth_expiry = None

async def login(username: str, password: str) -> bool:
    """
    Authenticate with the API.
    
    Parameters:
    -----------
    username : str
        Username
    password : str
        Password
        
    Returns:
    --------
    bool
        True if authentication was successful, False otherwise
    """
    global auth_token, auth_expiry
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/token",
                data={"username": username, "password": password},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                auth_token = data["access_token"]
                # Set expiry time (subtract 5 minutes for safety margin)
                auth_expiry = datetime.utcnow() + timedelta(seconds=data["expires_in"] - 300)
                
                # Store the token and expiry time in the Streamlit session state
                st.session_state["auth_token"] = auth_token
                st.session_state["auth_expiry"] = auth_expiry
                
                return True
            else:
                return False
                
    except Exception as e:
        print(f"Error during login: {e}")
        return False

def is_authenticated() -> bool:
    """
    Check if the user is authenticated.
    
    Returns:
    --------
    bool
        True if the user is authenticated, False otherwise
    """
    global auth_token, auth_expiry  # Declare global variables at the beginning
    
    # Verify if there is a token in the Streamlit session state
    if "auth_token" in st.session_state and "auth_expiry" in st.session_state:
        # Update global variables
        auth_token = st.session_state.auth_token
        auth_expiry = st.session_state.auth_expiry
        return datetime.utcnow() < auth_expiry
    
    # If there is no token in the session state, verify the global variables
    if auth_token and auth_expiry:
        return datetime.utcnow() < auth_expiry
    
    return False

async def get_headers() -> Dict[str, str]:
    """
    Get headers for API requests.
    
    Returns:
    --------
    Dict[str, str]
        Headers for API requests
    """
    global auth_token  # Declare global variables at the beginning
    
    # First, verify if we have a global token
    if is_authenticated() and auth_token:
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    # Verify if we have a token in the Streamlit session state
    if st.session_state.get("authenticated", False) and "auth_token" in st.session_state:
        # Update global variables
        auth_token = st.session_state.auth_token
        return {
            "Authorization": f"Bearer {st.session_state.auth_token}",
            "Content-Type": "application/json"
        }
    
    # If we don't have a token, return empty headers
    return {"Content-Type": "application/json"}

async def get_patients() -> List[Dict[str, Any]]:
    """
    Get all patients from the API.
    
    Returns:
    --------
    List[Dict[str, Any]]
        List of patients
    """
    if not is_authenticated():
        print("Dashboard: User not authenticated, returning empty patients list")
        return []
    
    url = f"{API_URL}/api/patients"
    headers = await get_headers()
    
    print(f"Dashboard Request - GET {url}")
    print(f"Headers: {headers}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                timeout=API_TIMEOUT
            )
            
            print(f"Dashboard Response - Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            patients = response.json()
            print(f"Dashboard Response - Patients data: {patients}")
            return patients
            
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
        print(f"Dashboard Error - {error_msg}")
    except httpx.RequestError as e:
        error_msg = f"Request failed: {str(e)}"
        print(f"Dashboard Error - {error_msg}")
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"Dashboard Error - {error_msg}")
    
    return []

async def get_patient(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific patient from the API.
    
    Parameters:
    -----------
    patient_id : str
        Patient ID
        
    Returns:
    --------
    Optional[Dict[str, Any]]
        Patient data if found, None otherwise
    """
    if not is_authenticated():
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/api/patients/{patient_id}",
                headers=await get_headers(),
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting patient: {response.status_code} {response.text}")
                return None
                
    except Exception as e:
        print(f"Error getting patient: {e}")
        return None

async def get_patient_vitals(
    patient_id: str,
    start_time: datetime,
    end_time: datetime,
    measurement_types: Optional[List[str]] = None,
    interval: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get vital signs for a patient from the API.
    
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
    Dict[str, Any]
        Vital signs data
    """
    if not is_authenticated():
        return {"vitals": [], "count": 0}
    
    # Format dates in ISO 8601 format without timezone
    def format_date(dt):
        # Remove timezone info and microseconds for compatibility with API
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        formatted = dt.replace(microsecond=0).isoformat() + 'Z'
        print(f"Formatted date: {dt} -> {formatted}")
        return formatted
    
    # Build query parameters
    params = {
        "start": format_date(start_time),
        "end": format_date(end_time)
    }
    
    print(f"API request params: {params}")
    
    if measurement_types:
        params["measurement_types"] = measurement_types
    
    if interval:
        params["interval"] = interval
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/api/patients/{patient_id}/vitals",
                params=params,
                headers=await get_headers(),
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting patient vitals: {response.status_code} {response.text}")
                return {"vitals": [], "count": 0}
                
    except Exception as e:
        print(f"Error getting patient vitals: {e}")
        return {"vitals": [], "count": 0}

async def get_latest_vitals(
    patient_id: str,
    measurement_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get the latest vital signs for a patient from the API.
    
    Parameters:
    -----------
    patient_id : str
        Patient ID
    measurement_types : Optional[List[str]]
        List of measurement types to retrieve, or None for all
        
    Returns:
    --------
    Dict[str, Any]
        Latest vital signs data
    """
    if not is_authenticated():
        return {"vitals": [], "count": 0}
    
    # Build query parameters
    params = {}
    if measurement_types:
        params["measurement_types"] = measurement_types
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/api/patients/{patient_id}/vitals/latest",
                params=params,
                headers=await get_headers(),
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting latest vitals: {response.status_code} {response.text}")
                return {"vitals": [], "count": 0}
                
    except Exception as e:
        print(f"Error getting latest vitals: {e}")
        return {"vitals": [], "count": 0}

async def get_alerts(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    measurement_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get alerts from the API.
    
    Parameters:
    -----------
    patient_id : Optional[str]
        Filter alerts by patient ID
    status : Optional[str]
        Filter alerts by status
    severity : Optional[str]
        Filter alerts by severity
    measurement_type : Optional[str]
        Filter alerts by measurement type
    limit : int
        Maximum number of alerts to return
        
    Returns:
    --------
    List[Dict[str, Any]]
        List of alerts
    """
    if not is_authenticated():
        return []
    
    # Build query parameters
    params = {}
    if patient_id:
        params["patient_id"] = patient_id
    if status:
        params["status"] = status
    if severity:
        params["severity"] = severity
    if measurement_type:
        params["measurement_type"] = measurement_type
    params["limit"] = limit
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/api/alerts",
                params=params,
                headers=await get_headers(),
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting alerts: {response.status_code} {response.text}")
                return []
                
    except Exception as e:
        print(f"Error getting alerts: {e}")
        return []

async def update_alert(
    alert_id: str,
    status: str,
    acknowledged_by: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Update an alert's status.
    
    Parameters:
    -----------
    alert_id : str
        Alert ID
    status : str
        New status for the alert
    acknowledged_by : Optional[str]
        User who acknowledged the alert
        
    Returns:
    --------
    Optional[Dict[str, Any]]
        Updated alert if successful, None otherwise
    """
    if not is_authenticated():
        return None
    
    # Build request body
    data = {
        "status": status
    }
    if acknowledged_by:
        data["acknowledged_by"] = acknowledged_by
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{API_URL}/api/alerts/{alert_id}",
                json=data,
                headers=await get_headers(),
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error updating alert: {response.status_code} {response.text}")
                return None
                
    except Exception as e:
        print(f"Error updating alert: {e}")
        return None

async def get_analysis(
    analysis_type: str,
    patient_id: str,
    start_time: datetime,
    end_time: datetime,
    measurement_types: Optional[List[str]] = None,
    comparison_start_time: Optional[datetime] = None,
    comparison_end_time: Optional[datetime] = None,
    event_type: Optional[str] = None,
    context_window_minutes: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Get an analysis from the API.
    
    Parameters:
    -----------
    analysis_type : str
        Type of analysis to perform
    patient_id : str
        Patient ID
    start_time : datetime
        Start time for data retrieval
    end_time : datetime
        End time for data retrieval
    measurement_types : Optional[List[str]]
        List of measurement types to retrieve, or None for all
    comparison_start_time : Optional[datetime]
        Start time for comparison data (for comparative analysis)
    comparison_end_time : Optional[datetime]
        End time for comparison data (for comparative analysis)
    event_type : Optional[str]
        Event type (for event-based analysis)
    context_window_minutes : Optional[int]
        Context window in minutes (for event-based analysis)
        
    Returns:
    --------
    Optional[Dict[str, Any]]
        Analysis response if successful, None otherwise
    """
    if not is_authenticated():
        return None
    
    # Build request body based on analysis type
    data = {
        "analysis_type": analysis_type,
        "patient_id": patient_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    
    if measurement_types:
        data["measurement_types"] = measurement_types
    
    # Add parameters for comparative analysis
    if analysis_type == "comparative" and comparison_start_time and comparison_end_time:
        data["comparison_start_time"] = comparison_start_time.isoformat()
        data["comparison_end_time"] = comparison_end_time.isoformat()
        data["analysis_type"] = "comparative"
    
    # Add parameters for event-based analysis
    if analysis_type == "event_based" and event_type:
        data["event_type"] = event_type
        if context_window_minutes:
            data["context_window_minutes"] = context_window_minutes
        data["analysis_type"] = "event_based"
            
    # Add parameters for time-window analysis
    if analysis_type == "time_window":
        data["window_count"] = 3
        data["window_duration_hours"] = 8.0
        data["window_interval_hours"] = 0.0
        data["analysis_type"] = "time_window"
    
    # Determine the endpoint based on analysis type
    # Convert underscores to dashes in endpoint paths
    analysis_type_path = analysis_type.replace("_", "-")
    
    # Add specific parameters for trend_analysis
    if analysis_type == "trend_analysis":
        data["analysis_type"] = "trend_analysis"
    
    # Use the correct endpoint for each analysis type
    if analysis_type == "time_window":
        endpoint = "/api/analysis/time-window"
    elif analysis_type == "comparative":
        endpoint = "/api/analysis/comparative"
    elif analysis_type == "event_based":
        endpoint = "/api/analysis/event-based"
    elif analysis_type == "trend_analysis":
        endpoint = "/api/analysis/trend-analysis"
    else:
        endpoint = "/api/analysis"
    
    # Log for debugging
    print(f"Send request to {API_URL}{endpoint}")
    print(f"Request data: {data}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}{endpoint}",
                json=data,
                headers=await get_headers(),
                timeout=TREND_ANALYSIS_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting analysis: {response.status_code} {response.text}")
                return None
                
    except Exception as e:
        print(f"Error getting analysis: {e}")
        return None

async def get_trend_analysis(
    patient_id: str,
    start_time: datetime,
    end_time: datetime,
    window_count: int,
    window_duration_hours: float,
    window_interval_hours: float,
    measurement_types: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a trend analysis from the API.
    
    Parameters:
    -----------
    patient_id : str
        Patient ID
    start_time : datetime
        Start time for data retrieval
    end_time : datetime
        End time for data retrieval
    window_count : int
        Number of time windows to analyze
    window_duration_hours : float
        Duration of each window in hours
    window_interval_hours : float
        Interval between windows in hours
    measurement_types : Optional[List[str]]
        List of measurement types to retrieve, or None for all
        
    Returns:
    --------
    Optional[Dict[str, Any]]
        Analysis response if successful, None otherwise
    """
    import streamlit as st
    if not st.session_state.get("authenticated", False):
        print("User is not authenticated (session state)")
        return None
    
    # Build request body
    data = {
        "analysis_type": "trend_analysis",
        "patient_id": patient_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "window_count": window_count,
        "window_duration_hours": window_duration_hours,
        "window_interval_hours": window_interval_hours
    }
    
    if measurement_types:
        data["measurement_types"] = measurement_types
    
    # Log request parameters
    print("\n=== TREND ANALYSIS REQUEST PARAMETERS ===")
    print(f"API URL: {API_URL}")
    print(f"Request data: {json.dumps(data, indent=2, default=str)}")
    print(f"Headers: {await get_headers()}")
    
    # Use the API server's trend analysis endpoint
    endpoint = "/api/analysis/trend-analysis"
    
    try:
        headers = await get_headers()
        
        if not headers and st.session_state.get("authenticated", False):
            if "auth_token" in st.session_state:
                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

        try:
            async with httpx.AsyncClient() as client:
                print(f"Sending request to: {API_URL}{endpoint}")
                try:
                    response = await client.post(
                        f"{API_URL}{endpoint}",
                        json=data,
                        headers=headers,
                        timeout=TREND_ANALYSIS_TIMEOUT
                    )
                    print(f"Request sent successfully. Status: {response.status_code}")
                except httpx.ReadTimeout as e:
                    print(f"TIMEOUT na requisição HTTP: {str(e)}")
                    print(f"A requisição excedeu o tempo limite de {TREND_ANALYSIS_TIMEOUT} segundos")
                    return None
                except httpx.ConnectError as e:
                    print(f"ERRO DE CONEXÃO: {str(e)}")
                    print(f"A conexão com o servidor foi recusada ou não pôde ser estabelecida")
                    return None
                except httpx.RemoteProtocolError as e:
                    print(f"ERRO DE PROTOCOLO REMOTO: {str(e)}")
                    print(f"A conexão foi encerrada prematuramente pelo servidor")
                    return None
                except httpx.RequestError as e:
                    print(f"ERRO na requisição HTTP: {str(e)}, Tipo: {type(e).__name__}")
                    print(f"Detalhes do erro: {repr(e)}")
                    return None
                except Exception as e:
                    print(f"ERRO inesperado ao enviar requisição: {str(e)}, Tipo: {type(e).__name__}")
                    print(f"Detalhes do erro: {repr(e)}")
                    return None
        except Exception as outer_e:
            print(f"ERRO externo: {str(outer_e)}, Tipo: {type(outer_e).__name__}")
            print(f"Detalhes do erro externo: {repr(outer_e)}")
            return None
        
        try:
            if response.status_code == 200:
                response_data = response.json()
                print(f"JSON convertido com sucesso. Tipo: {type(response_data)}")
                print(f"Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Não é um dicionário'}")
                print(f"Has windows: {'windows' in response_data if isinstance(response_data, dict) else 'N/A'}")
                if isinstance(response_data, dict) and 'windows' in response_data:
                    print(f"Windows count: {len(response_data['windows'])}")
                print(f"Response data: {str(response_data)[:300]}...")
                return response_data
            else:
                print(f"Error status code: {response.status_code}")
                print(f"Error response: {response.text}")
                print(f"Error headers: {response.headers}")
                return None
        except Exception as e:
            print(f"Error processing response: {str(e)}")
            return None
                
    except Exception as e:
        print(f"Error getting trend analysis: {e}")
        return None


async def get_system_health() -> Dict[str, Any]:
    """
    Get the health status of the system.
    
    Returns:
    --------
    Dict[str, Any]
        System health status
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/health",
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting system health: {response.status_code} {response.text}")
                return {
                    "status": "error",
                    "message": f"API returned status code {response.status_code}",
                    "components": {}
                }
                
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error when checking system health: {e.response.status_code} {e.response.reason_phrase}"
        print(error_msg)
        print(f"Response: {e.response.text}")
        return {
            "status": "error",
            "message": error_msg,
            "components": {}
        }
    except httpx.RequestError as e:
        error_msg = f"Request failed when checking system health: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "components": {}
        }
    except Exception as e:
        import traceback
        error_msg = f"Unexpected error when checking system health: {str(e)}"
        print(error_msg)
        print("Traceback:")
        traceback.print_exc()
        return {
            "status": "error",
            "message": error_msg,
            "components": {}
        }
