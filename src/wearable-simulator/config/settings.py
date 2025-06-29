#
# SmartCare Insight - settings.py
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
Settings and configuration for the wearable simulator.
"""
import os
import json
from typing import Dict, Any, List, Optional, Union, ClassVar
from pydantic import Field, field_validator, ConfigDict, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

from . import constants

# Load environment variables from .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Configuração do modelo
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        env_prefix=""
    )
    
    # Application settings
    patient_id: str = Field("patient-1", alias="PATIENT_ID")
    device_id: str = Field("wearable-1", alias="DEVICE_ID")
    seed: Optional[int] = Field(None, alias="SEED")
    
    # Simulation settings
    sample_rate: float = Field(
        4.0,
        ge=0.1,
        le=60.0,
        description="Samples per minute",
        alias="SAMPLE_RATE"
    )
    noise_level: float = Field(
        0.02,
        ge=0.0,
        le=1.0,
        description="Amount of noise to add (0-1)",
        alias="NOISE_LEVEL"
    )
    use_circadian_rhythms: bool = Field(
        True,
        description="Enable 24-hour patterns",
        alias="USE_CIRCADIAN_RHYTHMS"
    )
    simulate_meals: bool = Field(
        True,
        description="Simulate meal effects on glucose",
        alias="SIMULATE_MEALS"
    )
    simulate_sleep: bool = Field(
        True,
        description="Simulate sleep/wake cycles",
        alias="SIMULATE_SLEEP"
    )
    # Usando string para MEAL_TIMES e convertendo internamente
    meal_times_str: str = Field(
        default="7,12,19",
        alias="MEAL_TIMES",
        description="Comma-separated list of meal times in 24h format"
    )
    
    @property
    def meal_times(self) -> List[int]:
        """Parse MEAL_TIMES string into a list of integers."""
        try:
            return [int(x.strip()) for x in self.meal_times_str.split(',') if x.strip().isdigit()]
        except (ValueError, AttributeError):
            return [7, 12, 19]  # Default value
    
    sleep_start_hour: int = Field(
        23,
        ge=0,
        le=23,
        description="Sleep start time (0-23)",
        alias="SLEEP_START_HOUR"
    )
    sleep_duration_hours: float = Field(
        8.0,
        ge=4.0,
        le=12.0,
        description="Duration of sleep in hours",
        alias="SLEEP_DURATION_HOURS"
    )
    condition: str = Field(
        "healthy",
        description="Health condition to simulate",
        alias="CONDITION"
    )

    @field_validator('sleep_start_hour', 'sleep_duration_hours', 'noise_level', mode='before')
    @classmethod
    def validate_ranges(cls, v, info):
        field_name = info.field_name
        min_val = 0
        max_val = 24 if field_name == 'sleep_start_hour' else 1000
        
        # Converte para o tipo apropriado
        try:
            if field_name == 'noise_level':
                v = float(v)
                max_val = 1.0
            else:
                v = int(v)
                if field_name == 'sleep_duration_hours':
                    max_val = 24
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid value for {field_name}: {v}. Must be a number.")
            
        if not (min_val <= v <= max_val):
            raise ValueError(f"{field_name} must be between {min_val} and {max_val}")
        return v
    
    # MQTT settings
    mqtt_broker: str = Field("localhost", alias="MQTT_BROKER")
    mqtt_port: int = Field(1883, ge=1, le=65535, alias="MQTT_PORT")
    mqtt_username: Optional[str] = Field(None, alias="MQTT_USERNAME")
    mqtt_password: Optional[str] = Field(None, alias="MQTT_PASSWORD")
    mqtt_topic: str = Field("wearables/data", alias="MQTT_TOPIC")
    mqtt_qos: int = Field(1, ge=0, le=2, alias="MQTT_QOS")
    mqtt_retain: bool = Field(False, alias="MQTT_RETAIN")
    
    # Validate MQTT port
    @field_validator('mqtt_port')
    @classmethod
    def validate_mqtt_port(cls, v):
        if not (0 < v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v

# Create a singleton instance of settings
settings = Settings()

# For backward compatibility
if __name__ == "__main__":
    import json
    print(json.dumps(settings.model_dump(), indent=2))
