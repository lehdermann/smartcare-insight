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


class AlertSeverity(str, Enum):
    """Enum for alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Enum for alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertType(str, Enum):
    """Enum for alert types."""
    ANOMALY = "anomaly"
    TREND = "trend"
    THRESHOLD = "threshold"
    CORRELATION = "correlation"


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
    patient_id: str
    device_id: Optional[str] = None


class Patient(BaseModel):
    """Model for a patient."""
    id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = Field(
        None,
        description="Patient's current location (e.g., 'Room 101', 'Home', 'Clinic X')"
    )
    monitoring_start: Optional[datetime] = Field(
        None,
        description="When the patient started being monitored"
    )
    location_type: Optional[str] = Field(
        None,
        description="Type of location (e.g., 'hospital', 'home', 'clinic')",
        regex=r"^(hospital|home|clinic|other)$"
    )
    primary_condition: Optional[str] = None
    notes: Optional[str] = None


class Alert(BaseModel):
    """Model for an alert."""
    id: str
    patient_id: str
    measurement_type: str
    value: float
    timestamp: datetime
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    alert_type: AlertType
    message: str
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


class AlertUpdate(BaseModel):
    """Model for updating an alert."""
    status: AlertStatus
    acknowledged_by: Optional[str] = None


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
    """Model for an analysis response."""
    patient_id: str
    analysis_type: AnalysisType
    timestamp: datetime
    summary: str
    insights: List[Insight]
    recommendations: List[Recommendation]
    data_points_analyzed: int
    time_period: str
    windows: Optional[List[Dict[str, Any]]] = None


class AnalysisRequest(BaseModel):
    """Model for an analysis request."""
    analysis_type: AnalysisType
    patient_id: str
    start_time: datetime
    end_time: datetime
    measurement_types: Optional[List[str]] = None
    # Campos adicionais para análise de janela de tempo
    window_count: Optional[int] = None
    window_duration_hours: Optional[float] = None
    window_interval_hours: Optional[float] = None


class ComparativeAnalysisRequest(AnalysisRequest):
    """Model for a comparative analysis request."""
    comparison_start_time: datetime
    comparison_end_time: datetime


class EventBasedAnalysisRequest(AnalysisRequest):
    """Model for an event-based analysis request."""
    event_type: str
    context_window_minutes: int = 30


class TrendAnalysisRequest(AnalysisRequest):
    """Model for a trend analysis request across multiple time windows."""
    # Tornando os campos opcionais com valores padrão
    window_count: int = Field(5, description="Number of time windows to analyze")
    window_duration_hours: float = Field(6.0, description="Duration of each window in hours")
    window_interval_hours: float = Field(0.0, description="Interval between windows (0 for contiguous windows)")


class Token(BaseModel):
    """Model for an authentication token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class TokenData(BaseModel):
    """Model for token data."""
    username: Optional[str] = None
    scopes: List[str] = []


class User(BaseModel):
    """Model for a user."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    role: str = "user"


class UserInDB(User):
    """Model for a user in the database."""
    hashed_password: str


class SystemStatus(BaseModel):
    """Model for system status."""
    status: str
    version: str
    components: Dict[str, Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VitalSignsResponse(BaseModel):
    """Model for vital signs response."""
    patient_id: str
    vitals: List[VitalSign]
    start_time: datetime
    end_time: datetime
    count: int
