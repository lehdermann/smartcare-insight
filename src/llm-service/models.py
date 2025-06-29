#
# SmartCare Insight - models.py
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

from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    """Enum for types of analysis."""
    TIME_WINDOW = "time_window"
    EVENT_BASED = "event_based"
    COMPARATIVE = "comparative"
    TREND_ANALYSIS = "trend_analysis"


class VitalSign(BaseModel):
    """Model for a vital sign reading."""
    timestamp: datetime
    value: float
    measurement_type: str
    is_anomaly: bool = False


class PatientData(BaseModel):
    """Model for patient data."""
    patient_id: str
    vitals: List[VitalSign]
    start_time: datetime
    end_time: datetime
    
    # Fields for comparative analysis
    comparison_data: Optional[List[VitalSign]] = None
    
    # Fields for trend analysis
    windows: Optional[List[Dict[str, Any]]] = None
    window_count: Optional[int] = None
    window_duration_hours: Optional[float] = None
    window_interval_hours: Optional[float] = None


class AnalysisRequest(BaseModel):
    """Model for an analysis request."""
    analysis_type: AnalysisType
    patient_id: str
    start_time: datetime
    end_time: datetime
    measurement_types: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_type": "time_window",
                "patient_id": "patient-1",
                "start_time": "2025-05-26T12:00:00Z",
                "end_time": "2025-05-26T18:00:00Z",
                "measurement_types": ["hr", "bp_sys", "bp_dia", "oxygen", "glucose", "activity"]
            }
        }


class ComparativeAnalysisRequest(AnalysisRequest):
    """Model for a comparative analysis request."""
    comparison_start_time: datetime
    comparison_end_time: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_type": "comparative",
                "patient_id": "patient-1",
                "start_time": "2025-05-26T12:00:00Z",
                "end_time": "2025-05-26T18:00:00Z",
                "comparison_start_time": "2025-05-25T12:00:00Z",
                "comparison_end_time": "2025-05-25T18:00:00Z",
                "measurement_types": ["hr", "bp_sys", "bp_dia", "oxygen", "glucose", "activity"]
            }
        }


class EventBasedAnalysisRequest(AnalysisRequest):
    """Model for an event-based analysis request."""
    event_type: str
    context_window_minutes: int = 30
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_type": "event_based",
                "patient_id": "patient-1",
                "start_time": "2025-05-26T12:00:00Z",
                "end_time": "2025-05-26T18:00:00Z",
                "event_type": "anomaly",
                "context_window_minutes": 30,
                "measurement_types": ["hr", "bp_sys", "bp_dia", "oxygen", "glucose", "activity"]
            }
        }


class TrendAnalysisRequest(AnalysisRequest):
    """Model for a trend analysis request across multiple time windows."""
    window_count: int = Field(..., description="Number of time windows to analyze")
    window_duration_hours: float = Field(..., description="Duration of each window in hours")
    window_interval_hours: float = Field(0, description="Interval between windows (0 for contiguous windows)")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_type": "trend_analysis",
                "patient_id": "patient-1",
                "start_time": "2025-05-26T00:00:00Z",
                "end_time": "2025-05-26T23:59:59Z",
                "window_count": 5,
                "window_duration_hours": 4,
                "window_interval_hours": 0,
                "measurement_types": ["hr", "bp_sys", "bp_dia", "oxygen", "glucose", "activity"]
            }
        }


class Insight(BaseModel):
    """Model for an insight from the LLM analysis."""
    text: str
    confidence: float = 1.0
    related_measurements: List[str] = []


class Recommendation(BaseModel):
    """Model for a recommendation from the LLM analysis."""
    text: str
    priority: int = 1  # 1-5, with 5 being highest priority
    rationale: str = ""


class AnalysisResponse(BaseModel):
    """Model for analysis response."""
    patient_id: str
    analysis_type: AnalysisType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    summary: str
    insights: List[Insight]
    recommendations: List[Recommendation]
    data_points_analyzed: int
    time_period: str
    windows: Optional[List[Dict[str, Any]]] = None
    time_elapsed: Optional[float] = Field(
        None,
        description="Time taken to perform the analysis in seconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the analysis including processing details"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "patient_id": "patient-1",
                "analysis_type": "time_window",
                "timestamp": "2025-05-26T18:05:00Z",
                "summary": "The patient's vital signs have been stable over the analyzed period. Heart rate showed normal variation with physical activity.",
                "insights": [
                    {
                        "text": "Heart rate peaks correlate with increased activity levels",
                        "confidence": 0.92,
                        "related_measurements": ["hr", "activity"]
                    },
                    {
                        "text": "Blood pressure has been consistently within normal range",
                        "confidence": 0.95,
                        "related_measurements": ["bp_sys", "bp_dia"]
                    }
                ],
                "recommendations": [
                    {
                        "text": "Continue current monitoring regimen",
                        "priority": 2,
                        "rationale": "All vital signs are within normal parameters"
                    }
                ],
                "data_points_analyzed": 120,
                "time_period": "6 hours (12:00-18:00)"
            }
        }


class HealthCheckResponse(BaseModel):
    """Model for a health check response."""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    provider: str
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-05-26T18:05:00Z",
                "provider": "OpenAI"
            }
        }
