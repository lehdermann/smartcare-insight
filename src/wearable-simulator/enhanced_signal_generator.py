#
# SmartCare Insight - enhanced_signal_generator.py
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
Enhanced signal generator with circadian rhythms, meal effects, and sleep patterns.
"""
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Tuple, Optional, Callable

from config import constants as const
from config.settings import settings

class EnhancedSignalGenerator:
    """
    Enhanced signal generator with realistic physiological patterns.
    """
    
    def __init__(self, patient_id: str = None, condition: str = None):
        """
        Initialize the enhanced signal generator.
        
        Args:
            patient_id: Unique identifier for the patient
            condition: Health condition (e.g., 'hypertension', 'diabetes')
        """
        self.patient_id = patient_id or settings.patient_id
        self.condition = condition
        self.rng = np.random.RandomState(settings.seed)
        
        # Initialize base values within normal ranges
        self.baselines = {}
        for signal, (min_val, max_val) in const.NORMAL_RANGES.items():
            if signal == 'oxygen':
                # For oxygen, start at a healthy level (97-99%)
                self.baselines[signal] = 98.0 + self.rng.uniform(-1.0, 1.0)
            else:
                # For other signals, start in the middle of the normal range
                self.baselines[signal] = min_val + (max_val - min_val) * 0.5
        
        # Initialize trends for each signal
        self.trends = {signal: 0 for signal in const.NORMAL_RANGES}
        
        # Time tracking
        self.start_time = datetime.now()
        self.last_meal_time = None
        self.last_sleep_time = None
        
        # Apply condition adjustments
        if self.condition and self.condition in const.CONDITION_ADJUSTMENTS:
            self._apply_condition_adjustments(const.CONDITION_ADJUSTMENTS[self.condition])
    
    def _apply_condition_adjustments(self, adjustments: Dict[str, float]) -> None:
        """Apply condition-specific adjustments to baselines."""
        for signal, factor in adjustments.items():
            if signal in self.baselines:
                self.baselines[signal] *= factor
    
    def _get_circadian_factor(self, timestamp: datetime) -> Dict[str, float]:
        """
        Calculate circadian rhythm factors for different signals.
        
        Returns:
            Dictionary of signal -> circadian factor (0-1)
        """
        if not settings.use_circadian_rhythms:
            return {signal: 0.0 for signal in self.baselines}
        
        # Get hour of day with minute fraction
        hour = timestamp.hour + timestamp.minute / 60.0
        
        # Base circadian rhythm (peaks at 4 PM, lowest at 4 AM)
        phase_shift = 4.0  # Lowest point at 4 AM
        circadian_base = 0.5 * (1 + np.cos(2 * np.pi * (hour - phase_shift) / 24))
        
        # Signal-specific adjustments
        factors = {}
        
        # Heart rate: higher during day, lower at night
        factors['hr'] = 0.2 * (circadian_base - 0.5)
        
        # Blood pressure: morning surge, lower at night
        morning_surge = 0.3 * np.exp(-((hour - 8) ** 2) / 8.0)  # Peaks at 8 AM
        factors['bp_sys'] = 0.1 * (circadian_base - 0.5) + morning_surge
        factors['bp_dia'] = 0.08 * (circadian_base - 0.5) + morning_surge * 0.8
        
        # Glucose: affected by meals
        meal_effect = 0.0
        if settings.simulate_meals:
            for meal_hour in settings.meal_times:
                # Glucose rises after meals, peaks ~1 hour after eating
                hours_since_meal = (hour - meal_hour) % 24
                if 0.5 <= hours_since_meal <= 3.0:  # Effect lasts ~2.5 hours
                    meal_effect += 0.4 * np.exp(-((hours_since_meal - 1.5) ** 2) / 1.0)
        
        factors['glucose'] = 0.1 * (circadian_base - 0.5) + meal_effect
        
        # Oxygen: very slight variation with time of day (healthy people maintain stable SpO2)
        # Only about 1-2% variation between day and night
        factors['oxygen'] = -0.01 * (circadian_base - 0.5)
        
        # Activity: follows circadian rhythm with daytime peaks
        factors['activity'] = 0.4 * (circadian_base - 0.5)
        
        # Sleep effect (reduces activity at night)
        if settings.simulate_sleep:
            sleep_start = settings.sleep_start_hour
            sleep_end = (sleep_start + settings.sleep_duration_hours) % 24
            
            if sleep_start < sleep_end:
                is_sleep = sleep_start <= hour < sleep_end
            else:
                is_sleep = hour >= sleep_start or hour < sleep_end
            
            if is_sleep:
                factors['activity'] -= 0.8  # Drastically reduce activity during sleep
                factors['hr'] -= 0.15  # Lower heart rate during sleep
                factors['bp_sys'] -= 0.1
                factors['bp_dia'] -= 0.1
        
        return factors
    
    def generate(self, timestamp: datetime = None) -> Dict[str, float]:
        """
        Generate a complete set of signals for the current time.
        
        Args:
            timestamp: Optional timestamp to generate signals for
            
        Returns:
            Dictionary of signal values
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Get circadian and other time-based effects
        time_effects = self._get_circadian_factor(timestamp)
        
        # Generate each signal
        signals = {'timestamp': timestamp.isoformat() + 'Z'}
        
        for signal, baseline in self.baselines.items():
            # Update trend (slowly changing direction)
            self.trends[signal] += self.rng.normal(0, 0.05)
            self.trends[signal] *= 0.95  # Dampen trend over time
            
            # Special handling for oxygen to ensure realistic values
            if signal == 'oxygen':
                # Start with baseline value (should be around 97-98 for healthy patients)
                value = baseline + self.trends[signal] * 0.5  # Reduce trend impact for oxygen
                
                # Add time-based effects if available (circadian rhythm is already applied)
                if signal in time_effects:
                    value += time_effects[signal] * 2.0  # Slightly stronger circadian effect
                
                # Calculate maximum allowed noise to prevent exceeding 100%
                max_noise = min(100.0 - value, 1.0)  # Limit noise to prevent exceeding 100%
                
                # Add minimal noise with bounds checking
                noise = self.rng.normal(0, 0.3)  # Reduced noise level for oxygen
                noise = max(-1.0, min(max_noise, noise))  # Constrain noise
                value += noise
                
                # Round to 1 decimal place and ensure within physiological range
                value = round(value, 1)
                value = max(90.0, min(100.0, value))  # Final bounds check
                
                # Log warning if value was adjusted
                if value >= 99.9 or value <= 90.1:
                    import logging
                    logging.warning(
                        f"Oxygen value {'clipped to ' + str(value) + '%' if value in (90.0, 100.0) else str(value) + '%'} - "
                        f"Baseline: {baseline:.1f}, Noise: {noise:.2f}"
                    )
            else:
                # Standard calculation for other signals
                value = baseline + self.trends[signal]
                
                # Add time-based effects if available
                if signal in time_effects:
                    value += baseline * time_effects[signal]
                
                # Add noise
                noise = self.rng.normal(0, settings.noise_level)
                value *= (1 + noise)
            
            # Ensure value stays within reasonable bounds
            min_val, max_val = const.NORMAL_RANGES[signal]
            range_width = max_val - min_val
            
            # Apply different bounds based on signal type
            if signal == 'oxygen':
                # Oxygen is already clamped and rounded above
                pass
            else:
                # For other signals, allow 30% outside normal range
                value = max(min_val - 0.3 * range_width, min(max_val + 0.3 * range_width, value))
                
                # Round to appropriate precision
                if signal in ['hr', 'bp_sys', 'bp_dia', 'glucose']:
                    value = round(value)
                elif signal == 'activity':
                    value = round(value, 2)
                    value = max(0, min(1, value))
            
            signals[signal] = value
        
        return signals
    
    def generate_for_duration(self, duration_minutes: int, sample_rate: float = None) -> List[Dict]:
        """
        Generate signals for a duration with the given sample rate.
        
        Args:
            duration_minutes: Duration in minutes
            sample_rate: Samples per minute (default: from settings)
            
        Returns:
            List of signal dictionaries
        """
        if sample_rate is None:
            sample_rate = settings.sample_rate
            
        interval = 60.0 / sample_rate  # Time between samples in seconds
        n_samples = int(duration_minutes * 60 / interval)
        
        signals = []
        current_time = datetime.now()
        
        for i in range(n_samples):
            sample_time = current_time + timedelta(seconds=i * interval)
            signals.append(self.generate(sample_time))
            
        return signals
