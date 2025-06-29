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
from typing import Optional, List
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


class Alert(BaseModel):
    """Model for an alert."""
    id: Optional[str] = None
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
    
    class Config:
        schema_extra = {
            "example": {
                "id": "alert-123",
                "patient_id": "patient-1",
                "measurement_type": "hr",
                "value": 120,
                "timestamp": "2025-05-26T12:00:00Z",
                "severity": "medium",
                "status": "active",
                "alert_type": "threshold",
                "message": "Heart rate above normal range (120 bpm)",
                "resolved_at": None,
                "acknowledged_at": None,
                "acknowledged_by": None
            }
        }


class AlertUpdate(BaseModel):
    """Model for updating an alert."""
    status: AlertStatus
    acknowledged_by: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "acknowledged",
                "acknowledged_by": "doctor-1"
            }
        }


class AlertThreshold(BaseModel):
    """Model for alert thresholds."""
    measurement_type: str
    patient_id: Optional[str] = None  # If None, applies to all patients
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    
    class Config:
        schema_extra = {
            "example": {
                "measurement_type": "hr",
                "patient_id": "patient-1",
                "min_value": 50,
                "max_value": 120,
                "severity": "medium"
            }
        }


class AlertResponse(BaseModel):
    """Model for alert response."""
    alerts: List[Alert]
    count: int
    
    class Config:
        schema_extra = {
            "example": {
                "alerts": [
                    {
                        "id": "alert-123",
                        "patient_id": "patient-1",
                        "measurement_type": "hr",
                        "value": 120,
                        "timestamp": "2025-05-26T12:00:00Z",
                        "severity": "medium",
                        "status": "active",
                        "alert_type": "threshold",
                        "message": "Heart rate above normal range (120 bpm)",
                        "resolved_at": None,
                        "acknowledged_at": None,
                        "acknowledged_by": None
                    }
                ],
                "count": 1
            }
        }
