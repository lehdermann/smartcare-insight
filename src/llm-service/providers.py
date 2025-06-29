#
# SmartCare Insight - providers.py
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
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import openai
from dotenv import load_dotenv

from models import PatientData, AnalysisType, AnalysisResponse, Insight, Recommendation

# Load environment variables
load_dotenv()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_analysis(self, analysis_type: AnalysisType, patient_data: PatientData) -> AnalysisResponse:
        """
        Generate an analysis of patient data.
        
        Parameters:
        -----------
        analysis_type : AnalysisType
            Type of analysis to perform
        patient_data : PatientData
            Patient data to analyze
            
        Returns:
        --------
        AnalysisResponse
            Analysis results
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the LLM provider.
        
        Returns:
        --------
        Dict[str, Any]
            Health check results
        """
        pass
    
    @abstractmethod
    def format_prompt(self, analysis_type: AnalysisType, patient_data: PatientData) -> str:
        """
        Format a prompt for the LLM.
        
        Parameters:
        -----------
        analysis_type : AnalysisType
            Type of analysis to perform
        patient_data : PatientData
            Patient data to analyze
            
        Returns:
        --------
        str
            Formatted prompt
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of the LLM provider."""
    
    def __init__(self):
        """Initialize the OpenAI provider."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        if not self.api_key:
            print("WARNING: OPENAI_API_KEY environment variable not set")
        else:
            openai.api_key = self.api_key
    
    async def generate_analysis(self, analysis_type: AnalysisType, patient_data: PatientData) -> AnalysisResponse:
        """Generate an analysis using OpenAI."""
        print("\n\n==== OPENAI API DEBUG ====")
        print(f"API Key configured: {bool(self.api_key)}")
        print(f"API Key value: {self.api_key[:5]}...{self.api_key[-5:] if self.api_key else 'None'}")
        print(f"Model: {self.model}")
        print("===========================\n\n")
        
        if not self.api_key:
            print("No API key provided, using mock response")
            # Return a mock response if no API key is provided
            return self._generate_mock_response(analysis_type, patient_data)
        
        try:
            # Format the prompt based on analysis type
            prompt = self.format_prompt(analysis_type, patient_data)
            print("Prompt formatted, attempting to call OpenAI API...")
            
            # Call OpenAI API
            client = openai.AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a healthcare AI assistant analyzing patient vital signs data. Provide clinical insights and recommendations based on the data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            print("\n\n==== OPENAI API RESPONSE ====")
            print(f"Response object type: {type(response)}")
            print(f"Response object: {response}")
            print(f"Response choices: {response.choices}")
            print(f"Response first choice: {response.choices[0]}")
            print(f"Response message: {response.choices[0].message}")
            print(f"Response content: {response.choices[0].message.content}")
            print("===========================\n\n")
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Check if content is wrapped in a code block and extract the JSON
            if content.startswith('```') and '```' in content[3:]:
                # Extract content between code block markers
                content = content.split('```', 2)[1]
                # Remove language identifier if present (e.g., 'json\n')
                if '\n' in content:
                    content = content.split('\n', 1)[1]
                # Remove trailing code block marker if present
                if content.endswith('```'):
                    content = content[:-3].strip()
            
            print(f"\n\n==== PROCESSED JSON CONTENT ====")
            print(content)
            print("===========================\n\n")
            
            try:
                # Try to parse as JSON
                json_response = json.loads(content)
                
                print(f"\n\n==== PARSED JSON RESPONSE ====")
                print(f"Summary: {json_response.get('summary', 'No summary provided')}")
                print(f"Insights count: {len(json_response.get('insights', []))}")
                print(f"Recommendations count: {len(json_response.get('recommendations', []))}")
                print("===========================\n\n")
                
                # Create insights and recommendations
                insights = [Insight(**insight) for insight in json_response.get("insights", [])]
                recommendations = [Recommendation(**rec) for rec in json_response.get("recommendations", [])]
                
                # Create analysis response
                response = AnalysisResponse(
                    patient_id=patient_data.patient_id,
                    analysis_type=analysis_type,
                    timestamp=datetime.utcnow(),
                    summary=json_response.get("summary", "No summary provided"),
                    insights=insights,
                    recommendations=recommendations,
                    data_points_analyzed=len(patient_data.vitals),
                    time_period=f"{(patient_data.end_time - patient_data.start_time).total_seconds() / 3600:.1f} hours"
                )
                
                # Add windows data for any analysis type that has windows
                if hasattr(patient_data, 'windows') and patient_data.windows:
                    print(f"\n\n==== WINDOWS DATA DEBUG =====")
                    print(f"Analysis type: {analysis_type}")
                    print(f"Number of windows: {len(patient_data.windows)}")
                    print(f"First window keys: {list(patient_data.windows[0].keys()) if patient_data.windows else 'No windows'}")
                    print(f"First window content: {patient_data.windows[0] if patient_data.windows else 'No windows'}")
                    print(f"============================\n\n")
                    
                    # Process each window to ensure all data is properly included
                    processed_windows = []
                    
                    for window in patient_data.windows:
                        # Create a new window dictionary with all the original data
                        processed_window = {}
                        
                        # Copy all fields from the original window
                        for key, value in window.items():
                            # Handle special cases for datetime objects to ensure they're JSON serializable
                            if isinstance(value, datetime):
                                processed_window[key] = value.isoformat()
                            else:
                                processed_window[key] = value
                        
                        # Debug: Log all keys in the window
                        print(f"DEBUG: Window stats keys: {list(processed_window.keys())}")
                        
                        # Debug: Check for statistical fields
                        #has_stats = False
                        #for key in processed_window.keys():
                        #    if key.endswith(('_avg', '_min', '_max', '_values')):
                        #        has_stats = True
                        #        print(f"DEBUG: Found field: {key} = {processed_window[key]}")
                        
                        #if not has_stats:
                        #    print("DEBUG: WARNING - No statistical fields found in window!")
                        
                        # Add the processed window to our list
                        processed_windows.append(processed_window)
                    
                    # Add processed windows to response
                    response.windows = processed_windows
                    
                    print(f"\n\n==== RESPONSE WINDOWS DEBUG =====")
                    print(f"Number of windows in response: {len(response.windows)}")
                    print(f"First window in response: {response.windows[0] if response.windows else 'No windows'}")
                    print(f"============================\n\n")
                
                return response
            except json.JSONDecodeError:
                # If not valid JSON, extract insights and recommendations from text
                insights = []
                recommendations = []
                
                # Simple parsing of non-JSON response
                lines = content.split("\n")
                summary = lines[0] if lines else "No summary provided"
                
                for line in lines[1:]:
                    if line.startswith("Insight:"):
                        insights.append(Insight(text=line[8:].strip()))
                    elif line.startswith("Recommendation:"):
                        recommendations.append(Recommendation(text=line[15:].strip()))
                
                return AnalysisResponse(
                    patient_id=patient_data.patient_id,
                    analysis_type=analysis_type,
                    timestamp=datetime.utcnow(),
                    summary=summary,
                    insights=insights,
                    recommendations=recommendations,
                    data_points_analyzed=len(patient_data.vitals),
                    time_period=f"{(patient_data.end_time - patient_data.start_time).total_seconds() / 3600:.1f} hours"
                )
                
        except Exception as e:
            print(f"\n\n==== OPENAI API ERROR ====")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {e}")
            print(f"Error details: {str(e)}")
            import traceback
            print(f"Error traceback: {traceback.format_exc()}")
            print("===========================\n\n")
            # Return a mock response in case of error
            return self._generate_mock_response(analysis_type, patient_data)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the OpenAI provider."""
        if not self.api_key:
            return {
                "status": "unavailable",
                "version": "1.0.0",
                "timestamp": datetime.utcnow(),
                "provider": "OpenAI",
                "message": "API key not configured"
            }
        
        try:
            # Make a simple API call to check if the service is available
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=5
            )
            
            return {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": datetime.utcnow(),
                "provider": "OpenAI",
                "model": self.model
            }
        except Exception as e:
            return {
                "status": "error",
                "version": "1.0.0",
                "timestamp": datetime.utcnow(),
                "provider": "OpenAI",
                "error": str(e)
            }
    
    def format_prompt(self, analysis_type: AnalysisType, patient_data: PatientData) -> str:
        """Format a prompt for OpenAI based on analysis type."""
        # Basic patient info
        prompt = f"Patient ID: {patient_data.patient_id}\n"
        prompt += f"Time Period: {patient_data.start_time.isoformat()} to {patient_data.end_time.isoformat()}\n"
        prompt += f"Analysis Type: {analysis_type}\n\n"
        
        # Group vitals by measurement type
        vitals_by_type = {}
        for vital in patient_data.vitals:
            if vital.measurement_type not in vitals_by_type:
                vitals_by_type[vital.measurement_type] = []
            vitals_by_type[vital.measurement_type].append(vital)
        
        # Add vital sign data
        prompt += "Vital Signs Data:\n"
        for measurement_type, vitals in vitals_by_type.items():
            prompt += f"\n{measurement_type.upper()}:\n"
            # Sort by timestamp
            vitals.sort(key=lambda v: v.timestamp)
            # Only include a sample of data points to avoid token limits
            sample_size = min(20, len(vitals))
            step = max(1, len(vitals) // sample_size)
            sampled_vitals = vitals[::step]
            
            for vital in sampled_vitals:
                anomaly_flag = " (ANOMALY)" if vital.is_anomaly else ""
                prompt += f"  {vital.timestamp.isoformat()}: {vital.value}{anomaly_flag}\n"
            
            # Add summary statistics
            values = [v.value for v in vitals]
            if values:
                min_val = min(values)
                max_val = max(values)
                avg_val = sum(values) / len(values)
                prompt += f"  Summary: Min={min_val:.1f}, Max={max_val:.1f}, Avg={avg_val:.1f}\n"
        
        # Add specific instructions based on analysis type
        prompt += "\nAnalysis Instructions:\n"
        
        if analysis_type == AnalysisType.TIME_WINDOW:
            prompt += "Analyze the patient's vital signs over the specified time window. "
            prompt += "Identify any patterns, trends, or anomalies. "
            prompt += "Provide clinical insights and recommendations based on the data."
            
        elif analysis_type == AnalysisType.EVENT_BASED:
            prompt += "Analyze the patient's vital signs around anomalous events. "
            prompt += "Focus on the context before and after anomalies. "
            prompt += "Identify potential causes and effects of the anomalies."
            
        elif analysis_type == AnalysisType.COMPARATIVE:
            prompt += "Compare the patient's vital signs in this period with a previous period. "
            prompt += "Identify any significant changes or trends between the periods. "
            prompt += "Assess whether the patient's condition is improving, stable, or deteriorating."
            
        elif analysis_type == AnalysisType.TREND_ANALYSIS:
            prompt += "Analyze trends across multiple time windows to identify patterns and changes over time. "
            prompt += "Evaluate progression or regression in vital signs across the windows. "
            prompt += "Identify any correlations between different measurements. "
            prompt += "Assess the overall trend direction and provide insights on the patient's health trajectory."
            
            # Add windows data if available
            if hasattr(patient_data, 'windows') and patient_data.windows:
                prompt += "\n\nMultiple Time Windows Data:\n"
                prompt += f"Window Count: {patient_data.window_count}\n"
                prompt += f"Window Duration: {patient_data.window_duration_hours} hours\n"
                prompt += f"Window Interval: {patient_data.window_interval_hours} hours\n\n"
                
                # Add data for each window
                for window in patient_data.windows:
                    prompt += f"Window {window['window_index'] + 1}: {window['start_time'].isoformat()} to {window['end_time'].isoformat()}\n"
                    
                    # Group vitals by measurement type within this window
                    window_vitals_by_type = {}
                    for vital in window['vitals']:
                        if vital.measurement_type not in window_vitals_by_type:
                            window_vitals_by_type[vital.measurement_type] = []
                        window_vitals_by_type[vital.measurement_type].append(vital)
                    
                    # Add summary statistics for each measurement type in this window
                    for measurement_type, vitals in window_vitals_by_type.items():
                        values = [v.value for v in vitals]
                        if values:
                            min_val = min(values)
                            max_val = max(values)
                            avg_val = sum(values) / len(values)
                            prompt += f"  {measurement_type.upper()}: Min={min_val:.1f}, Max={max_val:.1f}, Avg={avg_val:.1f}\n"
                    
                    prompt += "\n"
        
        # Request format for the response
        prompt += "\n\nPlease provide your analysis in JSON format with the following structure:\n"
        prompt += "{\n"
        prompt += '  "summary": "Overall assessment of the patient\'s condition",\n'
        prompt += '  "insights": [\n'
        prompt += '    {"text": "Specific insight about the data", "confidence": 0.9, "related_measurements": ["hr", "activity"]},\n'
        prompt += '    ...\n'
        prompt += '  ],\n'
        prompt += '  "recommendations": [\n'
        prompt += '    {"text": "Clinical recommendation", "priority": 3, "rationale": "Reason for this recommendation"},\n'
        prompt += '    ...\n'
        prompt += '  ]\n'
        prompt += '}'
        
        return prompt
    
    def _generate_mock_response(self, analysis_type: AnalysisType, patient_data: PatientData) -> AnalysisResponse:
        """Generate a mock response when the API is unavailable."""
        # Create mock insights based on the data
        insights = []
        recommendations = []
        
        # Group vitals by measurement type
        vitals_by_type = {}
        for vital in patient_data.vitals:
            if vital.measurement_type not in vitals_by_type:
                vitals_by_type[vital.measurement_type] = []
            vitals_by_type[vital.measurement_type].append(vital)
        
        # Generate simple insights based on available data
        if 'hr' in vitals_by_type:
            hr_values = [v.value for v in vitals_by_type['hr']]
            if hr_values:
                avg_hr = sum(hr_values) / len(hr_values)
                if avg_hr > 100:
                    insights.append(Insight(
                        text=f"Elevated average heart rate ({avg_hr:.1f} bpm)",
                        confidence=0.8,
                        related_measurements=["hr"]
                    ))
                    recommendations.append(Recommendation(
                        text="Monitor heart rate closely",
                        priority=3,
                        rationale="Elevated average heart rate"
                    ))
                elif avg_hr < 60:
                    insights.append(Insight(
                        text=f"Low average heart rate ({avg_hr:.1f} bpm)",
                        confidence=0.8,
                        related_measurements=["hr"]
                    ))
                    recommendations.append(Recommendation(
                        text="Evaluate for bradycardia",
                        priority=3,
                        rationale="Low average heart rate"
                    ))
                else:
                    insights.append(Insight(
                        text=f"Normal average heart rate ({avg_hr:.1f} bpm)",
                        confidence=0.9,
                        related_measurements=["hr"]
                    ))
        
        if 'oxygen' in vitals_by_type:
            o2_values = [v.value for v in vitals_by_type['oxygen']]
            if o2_values:
                min_o2 = min(o2_values)
                if min_o2 < 95:
                    insights.append(Insight(
                        text=f"Low oxygen saturation detected (minimum {min_o2:.1f}%)",
                        confidence=0.9,
                        related_measurements=["oxygen"]
                    ))
                    recommendations.append(Recommendation(
                        text="Evaluate respiratory status",
                        priority=4,
                        rationale="Low oxygen saturation"
                    ))
        
        # Always add some basic insights and recommendations, even if no specific patterns were detected
        if not insights:
            insights.append(Insight(
                text="All vital signs appear to be within normal ranges",
                confidence=0.8,
                related_measurements=[k for k in vitals_by_type.keys()]
            ))
            insights.append(Insight(
                text="Patient shows stable health metrics during the monitoring period",
                confidence=0.7,
                related_measurements=[k for k in vitals_by_type.keys()]
            ))
            
            recommendations.append(Recommendation(
                text="Continue regular monitoring schedule",
                priority=1,
                rationale="Maintaining vigilance despite normal readings"
            ))
            recommendations.append(Recommendation(
                text="Review patient's medication adherence at next check-up",
                priority=2,
                rationale="Ensure continued stability of vital signs"
            ))
        
        # Handle trend analysis type specifically
        if analysis_type == AnalysisType.TREND_ANALYSIS and hasattr(patient_data, 'windows') and patient_data.windows:
            # Create insights about trends across windows
            insights = []
            recommendations = []
            
            # Track measurements across windows to identify trends
            measurement_trends = {}
            
            # Process each window's data
            for window in patient_data.windows:
                for vital in window['vitals']:
                    mt = vital.measurement_type
                    if mt not in measurement_trends:
                        measurement_trends[mt] = []
                    
                    # Group by window index
                    while len(measurement_trends[mt]) <= window['window_index']:
                        measurement_trends[mt].append([])
                    
                    measurement_trends[mt][window['window_index']].append(vital.value)
            
            # Analyze trends for each measurement type
            for mt, windows_data in measurement_trends.items():
                # Calculate averages for each window
                window_averages = []
                for window_values in windows_data:
                    if window_values:
                        window_averages.append(sum(window_values) / len(window_values))
                
                if len(window_averages) >= 2:
                    # Determine if there's an increasing or decreasing trend
                    first_avg = window_averages[0]
                    last_avg = window_averages[-1]
                    percent_change = ((last_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
                    
                    # Generate insight based on trend direction
                    if abs(percent_change) > 10:  # Significant change
                        direction = "increasing" if percent_change > 0 else "decreasing"
                        insights.append(Insight(
                            text=f"{mt.upper()} shows a {direction} trend of {abs(percent_change):.1f}% across windows",
                            confidence=0.85,
                            related_measurements=[mt]
                        ))
                        
                        # Add recommendation based on the measurement type and trend
                        if mt == 'hr' and percent_change > 10:
                            recommendations.append(Recommendation(
                                text="Monitor heart rate more frequently",
                                priority=3,
                                rationale=f"Increasing heart rate trend of {percent_change:.1f}%"
                            ))
                        elif mt == 'oxygen' and percent_change < -5:
                            recommendations.append(Recommendation(
                                text="Evaluate respiratory function",
                                priority=4,
                                rationale=f"Decreasing oxygen saturation trend of {abs(percent_change):.1f}%"
                            ))
                        elif mt == 'activity' and percent_change < -15:
                            recommendations.append(Recommendation(
                                text="Assess for mobility issues or fatigue",
                                priority=3,
                                rationale=f"Decreasing activity level trend of {abs(percent_change):.1f}%"
                            ))
                    else:  # Stable trend
                        insights.append(Insight(
                            text=f"{mt.upper()} remains relatively stable across windows (change: {percent_change:.1f}%)",
                            confidence=0.9,
                            related_measurements=[mt]
                        ))
            
            # Add a general insight about overall trends
            if len(measurement_trends) > 1:
                insights.append(Insight(
                    text=f"Analysis of {len(patient_data.windows)} time windows shows multiple vital sign patterns",
                    confidence=0.8,
                    related_measurements=list(measurement_trends.keys())
                ))
                
                # Add a general recommendation
                recommendations.append(Recommendation(
                    text="Continue monitoring with the current window configuration",
                    priority=2,
                    rationale="Multiple time windows provide good trend visibility"
                ))
            
            # Create a summary for trend analysis
            if insights:
                summary = f"Trend analysis across {len(patient_data.windows)} windows spanning {patient_data.window_duration_hours * patient_data.window_count + patient_data.window_interval_hours * (patient_data.window_count - 1):.1f} hours shows {len(insights)} notable patterns."
            else:
                summary = f"Trend analysis across {len(patient_data.windows)} windows shows no significant patterns."
        
        # For other analysis types
        else:
            # Create a summary based on the insights
            if len(insights) > 1:
                summary = "Multiple observations in patient vital signs. See insights for details."
            elif insights:
                summary = insights[0].text
            else:
                summary = "No significant patterns detected in patient vital signs."
        
        # Prepare response
        response_data = {
            "patient_id": patient_data.patient_id,
            "analysis_type": analysis_type,
            "timestamp": datetime.utcnow(),
            "summary": summary,
            "insights": insights,
            "recommendations": recommendations,
            "data_points_analyzed": len(patient_data.vitals),
            "time_period": f"{(patient_data.end_time - patient_data.start_time).total_seconds() / 3600:.1f} hours"
        }
        
        # Add windows data for trend analysis
        if analysis_type == AnalysisType.TREND_ANALYSIS:
            print(f"\n==== PROCESSING TREND ANALYSIS ====")
            print(f"Analysis type: {analysis_type}")
            print(f"Patient data has windows attribute: {hasattr(patient_data, 'windows')}")
            if hasattr(patient_data, 'windows'):
                print(f"Patient data windows is not None: {patient_data.windows is not None}")
                if patient_data.windows:
                    print(f"Patient data windows length: {len(patient_data.windows)}")
            
            # Generate windows data if not already present
            if not hasattr(patient_data, 'windows') or not patient_data.windows:
                print("Generating trend windows data...")
                windows_data = self._generate_trend_windows(patient_data)
                print(f"Generated windows data length: {len(windows_data)}")
                response_data["windows"] = windows_data
            else:
                print("Using existing windows data")
                response_data["windows"] = patient_data.windows
                
            print(f"Response data has windows: {'windows' in response_data}")
            if 'windows' in response_data:
                print(f"Response windows data length: {len(response_data['windows'])}")
            print(f"================================\n")
        
        return AnalysisResponse(**response_data)


    def _generate_trend_windows(self, patient_data):
        """
        Generate trend windows for trend analysis.
        
        Parameters:
        -----------
        patient_data : PatientData
            Patient data to analyze
            
        Returns:
        --------
        List[Dict[str, Any]]
            List of window data dictionaries
        """
        windows = []
        
        # Get window parameters
        window_count = getattr(patient_data, 'window_count', 5)
        window_duration_hours = getattr(patient_data, 'window_duration_hours', 6)
        window_interval_hours = getattr(patient_data, 'window_interval_hours', 0)
        
        # Calculate time span for each window
        total_duration = (patient_data.end_time - patient_data.start_time).total_seconds() / 3600  # in hours
        window_duration = window_duration_hours
        
        # Group vitals by measurement type
        vitals_by_type = {}
        for vital in patient_data.vitals:
            if vital.measurement_type not in vitals_by_type:
                vitals_by_type[vital.measurement_type] = []
            vitals_by_type[vital.measurement_type].append(vital)
        
        # Sort vitals by timestamp
        for mt in vitals_by_type:
            vitals_by_type[mt].sort(key=lambda v: v.timestamp)
        
        # Generate windows
        for i in range(window_count):
            window_start = patient_data.start_time + timedelta(hours=(window_duration + window_interval_hours) * i)
            window_end = window_start + timedelta(hours=window_duration)
            
            # Skip windows that are outside the data range
            if window_end > patient_data.end_time:
                continue
                
            window_vitals = []
            window_data = {
                "window_index": i,
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "window_label": f"Window {i+1}"
            }
            
            # Add values for each measurement type
            for mt, vitals in vitals_by_type.items():
                # Filter vitals for this window
                window_mt_vitals = [v for v in vitals if window_start <= v.timestamp <= window_end]
                
                if window_mt_vitals:
                    # Store all values as a list
                    values = [v.value for v in window_mt_vitals]
                    window_data[f"{mt}_values"] = values
                    
                    # Calculate and store statistics
                    window_data[f"{mt}_avg"] = sum(values) / len(values)
                    window_data[f"{mt}_min"] = min(values)
                    window_data[f"{mt}_max"] = max(values)
                    
                    window_vitals.extend(window_mt_vitals)
            
            # Add window to list if it has data
            if window_vitals:
                window_data["vitals"] = window_vitals
                windows.append(window_data)
        
        return windows


# Factory function to get the appropriate provider
def get_llm_provider() -> LLMProvider:
    """
    Factory function to get the configured LLM provider.
    
    Returns:
    --------
    LLMProvider
        Configured LLM provider instance
    """
    provider_name = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider_name == "openai":
        return OpenAIProvider()
    else:
        print(f"Unknown provider '{provider_name}', falling back to OpenAI")
        return OpenAIProvider()
