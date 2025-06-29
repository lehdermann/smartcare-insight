#
# SmartCare Insight - constants.py
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
Constants and default configurations for the wearable simulator.
"""

# Default time step in seconds (1 sample per 15 seconds)
DEFAULT_TIME_STEP = 15

# Default noise level (5% of signal range)
DEFAULT_NOISE_LEVEL = 0.05

# Default monitored signals
DEFAULT_MONITORED_SIGNALS = [
    'hr',          # Heart rate (bpm)
    'bp_sys',      # Systolic blood pressure (mmHg)
    'bp_dia',      # Diastolic blood pressure (mmHg)
    'oxygen',      # Oxygen saturation (%)
    'glucose',     # Blood glucose (mg/dL)
    'activity'     # Activity level (0-1)
]

# Normal ranges for vital signs
NORMAL_RANGES = {
    'hr': (60, 100),         # Heart rate (bpm)
    'bp_sys': (100, 140),    # Systolic blood pressure (mmHg)
    'bp_dia': (60, 90),      # Diastolic blood pressure (mmHg)
    'oxygen': (95, 100),     # Oxygen saturation (%)
    'glucose': (70, 120),    # Blood glucose (mg/dL)
    'activity': (0.3, 0.7)   # Activity level (0-1)
}

# Default MQTT settings
DEFAULT_MQTT_CONFIG = {
    'broker': 'localhost',
    'port': 1883,
    'username': '',
    'password': '',
    'topic': 'wearables/data',
    'qos': 1,
    'retain': False
}

# Default simulation settings
DEFAULT_SIMULATION_CONFIG = {
    'sample_rate': 4,             # Samples per minute
    'noise_level': 0.02,          # 2% noise
    'use_circadian_rhythms': True, # Enable 24-hour patterns
    'simulate_meals': True,       # Simulate meal effects on glucose
    'simulate_sleep': True,       # Simulate sleep/wake cycles
    'meal_times': [7, 12, 19],    # Breakfast, lunch, dinner (24h)
    'sleep_start_hour': 23,       # Sleep time (24h)
    'sleep_duration_hours': 8,    # Sleep duration
}

# Condition-specific adjustments
CONDITION_ADJUSTMENTS = {
    'tachycardia': {
        'hr': 1.3,  # 30% increase in heart rate
    },
    'bradycardia': {
        'hr': 0.7,  # 30% decrease in heart rate
    },
    'hypertension': {
        'bp_sys': 1.2,  # 20% increase in systolic BP
        'bp_dia': 1.2,  # 20% increase in diastolic BP
    },
    'hypotension': {
        'bp_sys': 0.85,  # 15% decrease in systolic BP
        'bp_dia': 0.85,  # 15% decrease in diastolic BP
    },
    'hypoxia': {
        'oxygen': 0.9,  # 10% decrease in oxygen saturation
    },
    'hyperglycemia': {
        'glucose': 1.5,  # 50% increase in glucose
    },
    'hypoglycemia': {
        'glucose': 0.7,  # 30% decrease in glucose
    },
    'sedentary': {
        'activity': 0.5,  # 50% reduction in activity
    },
    'athlete': {
        'activity': 1.3,  # 30% increase in activity
    }
}
