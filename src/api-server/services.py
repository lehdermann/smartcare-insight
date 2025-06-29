#
# SmartCare Insight - services.py
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
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

from models import Alert, AlertUpdate, AnalysisRequest, AnalysisResponse

# Load environment variables
load_dotenv()

# Service URLs
ALERT_MANAGER_URL = os.getenv("ALERT_MANAGER_URL", "http://localhost:8000")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8001")

# Timeout for API requests
REQUEST_TIMEOUT = 10.0  # seconds


async def get_alerts(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    measurement_type: Optional[str] = None,
    limit: int = 100
) -> List[Alert]:
    """
    Get alerts from the Alert Manager service.
    
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
    List[Alert]
        List of alerts
    """
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
                f"{ALERT_MANAGER_URL}/alerts",
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("alerts", [])
            else:
                print(f"Error getting alerts: {response.status_code} {response.text}")
                return []
                
    except Exception as e:
        print(f"Error communicating with Alert Manager: {e}")
        return []


async def get_alert(alert_id: str) -> Optional[Alert]:
    """
    Get a specific alert from the Alert Manager service.
    
    Parameters:
    -----------
    alert_id : str
        Alert ID
        
    Returns:
    --------
    Optional[Alert]
        Alert if found, None otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ALERT_MANAGER_URL}/alerts/{alert_id}",
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting alert: {response.status_code} {response.text}")
                return None
                
    except Exception as e:
        print(f"Error communicating with Alert Manager: {e}")
        return None


async def update_alert(alert_id: str, alert_update: AlertUpdate) -> Optional[Alert]:
    """
    Update an alert in the Alert Manager service.
    
    Parameters:
    -----------
    alert_id : str
        Alert ID
    alert_update : AlertUpdate
        Alert update data
        
    Returns:
    --------
    Optional[Alert]
        Updated alert if successful, None otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{ALERT_MANAGER_URL}/alerts/{alert_id}",
                json=alert_update.dict(),
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error updating alert: {response.status_code} {response.text}")
                return None
                
    except Exception as e:
        print(f"Error communicating with Alert Manager: {e}")
        return None


async def get_llm_analysis(analysis_request: AnalysisRequest) -> Optional[AnalysisResponse]:
    """
    Get an analysis from the LLM service.
    
    Parameters:
    -----------
    analysis_request : AnalysisRequest
        Analysis request data
        
    Returns:
    --------
    Optional[AnalysisResponse]
        Analysis response if successful, None otherwise
    """
    try:
        # Convert the Pydantic model to a dict and handle datetime serialization
        request_dict = analysis_request.dict()
        
        # Convert datetime objects to ISO format strings
        for key, value in request_dict.items():
            if isinstance(value, datetime):
                request_dict[key] = value.isoformat()
                
        # Handle nested datetime objects in comparison fields
        if "comparison_start_time" in request_dict and isinstance(request_dict["comparison_start_time"], datetime):
            request_dict["comparison_start_time"] = request_dict["comparison_start_time"].isoformat()
            
        if "comparison_end_time" in request_dict and isinstance(request_dict["comparison_end_time"], datetime):
            request_dict["comparison_end_time"] = request_dict["comparison_end_time"].isoformat()
        
        # Determine the correct endpoint based on analysis type
        analysis_type = request_dict.get("analysis_type")
        if not analysis_type:
            print("Error: analysis_type is required for LLM analysis")
            return None
            
        # Convert underscores to hyphens in the endpoint path
        analysis_type_path = analysis_type.replace("_", "-")
        endpoint = f"/analyze/{analysis_type_path}"
            
        print(f"Sending LLM analysis request to endpoint: {endpoint}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLM_SERVICE_URL}{endpoint}",
                json=request_dict,
                timeout=REQUEST_TIMEOUT * 3  # LLM requests may take longer
            )
            
            print(f"LLM service response status: {response.status_code}")
            if response.status_code == 200:
                response_data = response.json()
                print(f"LLM service response type: {response_data.get('analysis_type', 'unknown')}")
                return response_data
            else:
                print(f"Error getting LLM analysis: {response.status_code} {response.text}")
                return None
                
    except Exception as e:
        print(f"Error communicating with LLM service: {e}")
        return None


async def get_trend_analysis(analysis_request: AnalysisRequest) -> Optional[AnalysisResponse]:
    """
    Get a trend analysis from the LLM service.
    
    This function is specifically for trend analysis and will override any analysis_type
    in the request to ensure it's processed as a trend analysis.
    
    Parameters:
    -----------
    analysis_request : AnalysisRequest
        Analysis request data with trend analysis parameters
        
    Returns:
    --------
    Optional[AnalysisResponse]
        Analysis response if successful, None otherwise
    """
    try:
        # Convert the Pydantic model to a dict and handle datetime serialization
        request_dict = analysis_request.dict()
        
        # Convert datetime objects to ISO format strings
        for key, value in request_dict.items():
            if isinstance(value, datetime):
                request_dict[key] = value.isoformat()
        
        # Set the analysis type to be trend_analysis
        request_dict["analysis_type"] = "trend_analysis"
        
        print("Sending trend analysis request to LLM service...")
        
        async with httpx.AsyncClient() as client:
            # Use the specific trend analysis endpoint
            endpoint = "/analyze/trend-analysis"
            print(f"Sending request to {LLM_SERVICE_URL}{endpoint}")

            response = await client.post(
                f"{LLM_SERVICE_URL}{endpoint}",
                json=request_dict,
                timeout=300.0
            )
            
            print(f"LLM service trend analysis response status: {response.status_code}")
            if response.status_code == 200:
                response_data = response.json()
                
                # Ensure the response has the correct analysis type
                if "analysis_type" in response_data:
                    print(f"Received trend analysis response for type: {response_data['analysis_type']}")
                
                # Normalize the windows data structure if present
                if "windows" in response_data and isinstance(response_data["windows"], list):
                    for window in response_data["windows"]:
                        # Ensure all _values fields are lists
                        for key in list(window.keys()):
                            if key.endswith("_values") and not isinstance(window[key], list):
                                window[key] = [window[key]]
                
                return response_data
            else:
                print(f"Error getting trend analysis: {response.status_code} {response.text}")
                return None
                
    except Exception as e:
        print(f"Error communicating with LLM service for trend analysis: {e}")
        return None


async def check_service_health(service_url: str, endpoint: str = "/health") -> Dict[str, Any]:
    """
    Check the health of a service.
    
    Parameters:
    -----------
    service_url : str
        Base URL of the service
    endpoint : str
        Health check endpoint
        
    Returns:
    --------
    Dict[str, Any]
        Health check response
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{service_url}{endpoint}",
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "details": response.json()
                }
            else:
                return {
                    "status": "unhealthy",
                    "details": {
                        "status_code": response.status_code,
                        "message": response.text
                    }
                }
                
    except Exception as e:
        return {
            "status": "error",
            "details": {
                "message": str(e)
            }
        }
