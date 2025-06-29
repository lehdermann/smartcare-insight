#
# SmartCare Insight - signal_generator.py
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

import numpy as np
from datetime import datetime
import time
import os

class SignalGenerator:
    """
    Generates simulated vital sign signals for healthcare monitoring.
    
    Parameters:
    -----------
    patient_id : str
        Identifier for the patient
    device_id : str
        Identifier for the wearable device
    sample_rate : float
        Number of samples per minute (default: 4, or every 15 seconds)
    noise_level : float
        Percentage of noise to add to the signal (default: 0.02 or 2%)
    seed : int
        Random seed for reproducible simulations
    """
    
    # Normal ranges for vital signs
    NORMAL_RANGES = {
        'hr': (60, 100),         # Heart rate (bpm)
        'bp_sys': (100, 140),    # Systolic blood pressure (mmHg)
        'bp_dia': (60, 90),      # Diastolic blood pressure (mmHg)
        'oxygen': (95, 100),     # Oxygen saturation (%)
        'glucose': (70, 120),    # Blood glucose (mg/dL)
        'activity': (0.3, 0.7)   # Activity level (0-1)
    }
    
    def __init__(self, patient_id, device_id, sample_rate=4, noise_level=0.02, seed=None):
        self.patient_id = patient_id
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.noise_level = noise_level
        
        # Set random seed for reproducibility if provided
        if seed is not None:
            np.random.seed(seed)
            
        # Initialize baseline values within normal ranges
        self.baselines = {}
        for signal, (min_val, max_val) in self.NORMAL_RANGES.items():
            # Start with a value in the middle of the normal range
            self.baselines[signal] = min_val + (max_val - min_val) * 0.5
            
        # Initialize trend directions and strengths for each signal
        self.trends = {signal: 0 for signal in self.NORMAL_RANGES.keys()}
        
        # Time between samples in seconds
        self.interval = 60 / self.sample_rate
        
    def generate_value(self, signal_type):
        """
        Generate a realistic value for the specified signal type.
        
        Parameters:
        -----------
        signal_type : str
            Type of vital sign to generate
            
        Returns:
        --------
        float
            Simulated value for the vital sign
        """
        if signal_type not in self.NORMAL_RANGES:
            raise ValueError(f"Unknown signal type: {signal_type}")
            
        min_val, max_val = self.NORMAL_RANGES[signal_type]
        baseline = self.baselines[signal_type]
        
        # Update the trend (slowly changing direction)
        self.trends[signal_type] += np.random.normal(0, 0.1)
        # Dampen the trend to prevent divergence
        self.trends[signal_type] *= 0.95
        
        # Apply the trend to the baseline
        baseline += self.trends[signal_type]
        
        # Ensure baseline stays within a reasonable range
        range_width = max_val - min_val
        baseline = max(min_val - range_width * 0.2, min(max_val + range_width * 0.2, baseline))
        self.baselines[signal_type] = baseline
        
        # Add noise to the signal
        noise = np.random.normal(0, self.noise_level * range_width)
        value = baseline + noise
        
        # Ensure the value is within reasonable bounds
        value = max(min_val - range_width * 0.3, min(max_val + range_width * 0.3, value))
        
        # Round to appropriate precision
        if signal_type in ['hr', 'bp_sys', 'bp_dia', 'glucose']:
            value = round(value)
        elif signal_type == 'oxygen':
            value = round(value, 1)
        elif signal_type == 'activity':
            value = round(value, 2)
            value = max(0, min(1, value))  # Activity must be between 0 and 1
            
        return value
    
    def generate_all_signals(self):
        """
        Generate values for all vital signs.
        
        Returns:
        --------
        dict
            Dictionary with values for all vital signs
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        data = {
            'patient_id': self.patient_id,
            'device_id': self.device_id,
            'timestamp': timestamp
        }
        
        for signal in self.NORMAL_RANGES.keys():
            data[signal] = self.generate_value(signal)
            
        return data
    
    def simulate_abnormal_condition(self, condition_type):
        """
        Simulate an abnormal health condition by adjusting baselines.
        
        Parameters:
        -----------
        condition_type : str
            Type of condition to simulate ('tachycardia', 'hypoxia', etc.)
        """
        if condition_type == 'tachycardia':
            # Elevated heart rate
            self.baselines['hr'] = self.NORMAL_RANGES['hr'][1] * 1.3
            self.trends['hr'] = 2
        elif condition_type == 'hypoxia':
            # Low oxygen saturation
            self.baselines['oxygen'] = self.NORMAL_RANGES['oxygen'][0] * 0.9
            self.trends['oxygen'] = -0.5
        elif condition_type == 'hypertension':
            # High blood pressure
            self.baselines['bp_sys'] = self.NORMAL_RANGES['bp_sys'][1] * 1.2
            self.baselines['bp_dia'] = self.NORMAL_RANGES['bp_dia'][1] * 1.2
            self.trends['bp_sys'] = 2
            self.trends['bp_dia'] = 1
        elif condition_type == 'hypoglycemia':
            # Low blood glucose
            self.baselines['glucose'] = self.NORMAL_RANGES['glucose'][0] * 0.7
            self.trends['glucose'] = -1
        elif condition_type == 'hyperglycemia':
            # High blood glucose
            self.baselines['glucose'] = self.NORMAL_RANGES['glucose'][1] * 1.5
            self.trends['glucose'] = 2
        elif condition_type == 'normal':
            # Reset to normal conditions
            for signal, (min_val, max_val) in self.NORMAL_RANGES.items():
                self.baselines[signal] = min_val + (max_val - min_val) * 0.5
                self.trends[signal] = 0
        else:
            raise ValueError(f"Unknown condition type: {condition_type}")
    
    def run(self, duration=None, callback=None):
        """
        Run the signal generator for the specified duration.
        
        Parameters:
        -----------
        duration : float or None
            Duration in seconds to run the generator, or None for indefinite
        callback : function
            Function to call with the generated data
        """
        start_time = time.time()
        iteration = 0
        
        try:
            while duration is None or time.time() - start_time < duration:
                data = self.generate_all_signals()
                
                if callback:
                    callback(data)
                    
                # Log every 10 iterations to avoid console spam
                if iteration % 10 == 0:
                    print(f"Generated data: {data}")
                    
                iteration += 1
                
                # Sleep until the next sample is due
                next_sample_time = start_time + (iteration * self.interval)
                sleep_time = max(0, next_sample_time - time.time())
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("Signal generator stopped by user")
