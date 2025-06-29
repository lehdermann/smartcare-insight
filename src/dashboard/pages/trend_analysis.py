#
# SmartCare Insight - trend_analysis.py
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

import asyncio
import json
from datetime import datetime, timedelta
import importlib
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Import and reload utils module
import utils
importlib.reload(utils)

# Page configuration
st.set_page_config(
    page_title="Trend Analysis - SmartCare Insight",
    page_icon="../assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.warning("Please log in from the home page.")
    st.stop()

if "trend_analysis_results" not in st.session_state:
    st.session_state.trend_analysis_results = {}

if "trend_analysis_history" not in st.session_state:
    st.session_state.trend_analysis_history = []

# Data loading functions
async def load_patients():
    """Load patients from the API."""
    if not hasattr(st.session_state, "patients") or not st.session_state.patients:
        patients = await utils.get_patients()
        st.session_state.patients = patients
    
    return st.session_state.patients

async def perform_trend_analysis(
    patient_id,
    end_time,
    window_count=5,
    window_duration_hours=6,
    window_interval_hours=6,  # Interval between windows (same as duration for non-overlapping windows)
    measurement_types=None
):
    """Perform a trend analysis using the LLM service."""
    # Calculate start time based on window parameters
    # Calculate total time span needed for all windows and intervals
    total_hours = (window_count * window_duration_hours) + ((window_count - 1) * window_interval_hours)
    start_time = end_time - timedelta(hours=total_hours)
    
    # Debug: Log the time range and window parameters
    print(f"\n=== TIME RANGE CALCULATION ===")
    print(f"End Time: {end_time}")
    print(f"Window Count: {window_count}")
    print(f"Window Duration: {window_duration_hours} hours")
    print(f"Window Interval: {window_interval_hours} hours")
    print(f"Total Time Span: {total_hours} hours")
    print(f"Calculated Start Time: {start_time}")
    print(f"Time Range: {end_time - start_time}")
    print(f"Expected Windows: {window_count} windows of {window_duration_hours}h each")

    # Log dos parâmetros da requisição
    print("\n=== PARÂMETROS DA REQUISIÇÃO ===")
    print(f"Patient ID: {patient_id}")
    print(f"Start Time: {start_time} (type: {type(start_time)})")
    print(f"End Time: {end_time} (type: {type(end_time)})")
    print(f"Window Count: {window_count} (type: {type(window_count)})")
    print(f"Window Duration (hours): {window_duration_hours} (type: {type(window_duration_hours)})")
    print(f"Window Interval (hours): {window_interval_hours} (type: {type(window_interval_hours)})")
    print(f"Measurement Types: {measurement_types} (type: {type(measurement_types)})")

    # Perform trend analysis
    analysis = await utils.get_trend_analysis(
        patient_id=patient_id,
        start_time=start_time,
        end_time=end_time,
        window_count=window_count,
        window_duration_hours=window_duration_hours,
        window_interval_hours=window_interval_hours,
        measurement_types=measurement_types
    )

    # Process analysis results
    if analysis:
        # Add to history
        if analysis not in st.session_state.trend_analysis_history:
            st.session_state.trend_analysis_history.append(analysis)
            # Keep only the 10 most recent analyses
            if len(st.session_state.trend_analysis_history) > 10:
                st.session_state.trend_analysis_history.pop(0)
    
    return analysis


# Main function
async def main():
    """Main function for the trend analysis page."""
    st.title("Trend Analysis")
    st.markdown("Analyze trends across multiple time windows to identify patterns and changes over time.")
    
    # Load patients
    patients = await load_patients()
    
    # Sidebar for analysis configuration
    with st.sidebar:
        st.header("Analysis Configuration")
        
        # Patient selection
        patient_options = {p.get("name", f"Unknown ({p.get('id')})") : p.get("id") for p in patients}
        
        selected_patient_name = st.selectbox(
            "Patient",
            options=list(patient_options.keys()),
            index=0
        )
        
        selected_patient_id = patient_options[selected_patient_name]
        
        # Time window configuration
        st.subheader("Time Windows")
        
        end_time = datetime.utcnow()
        
        window_count = st.slider(
            "Number of Windows",
            min_value=2,
            max_value=10,
            value=5,
            step=1
        )
        
        window_duration_hours = st.slider(
            "Window Duration (hours)",
            min_value=1,
            max_value=24,
            value=6,
            step=1
        )
        
        window_interval_hours = st.slider(
            "Interval Between Windows (hours)",
            min_value=0,
            max_value=12,
            value=6,
            step=1,
            help="Set to 0 for contiguous windows, or specify the interval in hours"
        )
        # Calculate total time span
        # Calculate and display total time span
        total_hours = window_count * window_duration_hours + (window_count - 1) * window_interval_hours
        st.info(f"Total time span: {total_hours} hours")
        
        # Measurement types selection
        st.subheader("Vital Signs")
        
        all_measurement_types = ["hr", "bp_sys", "bp_dia", "oxygen", "glucose", "activity"]
        measurement_type_labels = {
            "hr": "Heart Rate",
            "bp_sys": "Systolic Blood Pressure",
            "bp_dia": "Diastolic Blood Pressure",
            "oxygen": "Oxygen Saturation",
            "glucose": "Blood Glucose",
            "activity": "Activity Level"
        }
        
        selected_measurement_types = []
        for mt in all_measurement_types:
            if st.checkbox(measurement_type_labels[mt], value=True):
                selected_measurement_types.append(mt)
        
        # Run analysis button
        if st.button("Run Analysis", type="primary"):
            with st.spinner("Running trend analysis..."):
                # Prepare parameters
                params = {
                    "patient_id": selected_patient_id,
                    "end_time": end_time,
                    "window_count": window_count,
                    "window_duration_hours": window_duration_hours,
                    "window_interval_hours": window_interval_hours,
                    "measurement_types": selected_measurement_types
                }
                
                # Run analysis
                analysis = await perform_trend_analysis(**params)

                # Store analysis results in session state
                if analysis:
                    # Store in session state
                    key = f"{selected_patient_id}_trend_{datetime.utcnow().isoformat()}"
                    st.session_state.trend_analysis_results[key] = analysis
                    st.session_state.current_trend_analysis = key
                else:
                    st.error("Failed to perform trend analysis. Please try again.")
    
    # Main content area
    if hasattr(st.session_state, "current_trend_analysis") and st.session_state.current_trend_analysis in st.session_state.trend_analysis_results:
        # Display current analysis
        analysis = st.session_state.trend_analysis_results[st.session_state.current_trend_analysis]
        
        # Get patient name
        patient_id = analysis.get("patient_id")
        patient_name = next((p.get("name", "Unknown") for p in patients if p.get("id") == patient_id), "Unknown")
        
        # Display analysis header
        st.header(f"Trend Analysis for {patient_name}")
        st.markdown(f"**Time Period:** {analysis.get('time_period', 'Unknown')}")
        st.markdown(f"**Data Points Analyzed:** {analysis.get('data_points_analyzed', 0)}")
        st.markdown(f"**Generated:** {analysis.get('timestamp', 'Unknown')}")
        
        # Display trend visualization if windows data is available
        if "windows" in analysis:
            st.header("Trend Visualization")
            
            # Get windows data for visualization
            windows = analysis.get("windows", [])
            
            # Convert windows data to DataFrame
            windows_data = pd.DataFrame(windows)
            
            # Debug: Log the structure of the first window
            if len(windows) > 0:
                first_window = windows[0]
                print("\n=== WINDOW DATA STRUCTURE ===")
                print(f"Window keys: {list(first_window.keys())}")
                
                # Log available metrics
                metrics = [k.replace('_values', '') for k in first_window.keys() if k.endswith('_values')]
                print(f"\nAvailable metrics: {metrics}")
                
                # Log sample values for each metric
                for metric in metrics:
                    if f"{metric}_values" in first_window:
                        values = first_window[f"{metric}_values"]
                        print(f"\nMetric: {metric}")
                        print(f"  Values type: {type(values)}")
                        if isinstance(values, (list, np.ndarray)):
                            print(f"  Values length: {len(values)}")
                            if len(values) > 0:
                                print(f"  First value type: {type(values[0])}")
                                if isinstance(values[0], (list, np.ndarray)) and len(values[0]) > 0:
                                    print(f"  First sub-value type: {type(values[0][0])}")
                        
                        # Log available stats for this metric
                        for stat in ['avg', 'min', 'max']:
                            stat_key = f"{metric}_{stat}"
                            if stat_key in first_window:
                                print(f"  {stat.upper()}: {first_window[stat_key]}")
            
            print("\n=== WINDOWS DATAFRAME COLUMNS ===")
            print(windows_data.columns.tolist())
            print("\n=== WINDOWS DATAFRAME HEAD ===")
            print(windows_data.head().to_string())
            
            # Create tabs for different visualizations
            tab1, tab2, tab3 = st.tabs(["Individual Trends", "Combined Trends", "Data Table"])
            
            with tab1:
                # Create individual trend charts for each measurement type
                for mt in selected_measurement_types:
                    if f"{mt}_values" in windows_data.columns:
                        fig = go.Figure()
                        
                        print(f"\n=== PROCESSING METRIC: {mt} ===")
                        print(f"Available columns: {[col for col in windows_data.columns if mt in col]}")
                        
                        # Check for both _values and _avg fields
                        if f"{mt}_avg" in windows_data.columns:
                            print(f"Using pre-calculated average for {mt}")
                            numeric_values = windows_data[f"{mt}_avg"].tolist()
                            print(f"Numeric values: {numeric_values}")
                        elif f"{mt}_values" in windows_data.columns:
                            print(f"Calculating average from values for {mt}")
                            # Fall back to calculating average from values if _avg is not available
                            values = windows_data[f"{mt}_values"]
                            numeric_values = []
                            for v in values:
                                if isinstance(v, list) and v:
                                    valid_values = [item for item in v if isinstance(item, (int, float))]
                                    if valid_values:
                                        avg_value = sum(valid_values) / len(valid_values)
                                        numeric_values.append(avg_value)
                                    else:
                                        numeric_values.append(0)
                                elif isinstance(v, (int, float)):
                                    numeric_values.append(v)
                                else:
                                    numeric_values.append(0)
                        else:
                            # If no data is available, use zeros
                            numeric_values = [0] * len(windows_data)
                        
                        # Add line for values
                        fig.add_trace(go.Scatter(
                            x=windows_data["window_label"],
                            y=numeric_values,
                            mode="lines+markers",
                            name=measurement_type_labels.get(mt, mt),
                            line=dict(width=3)
                        ))
                        
                        # Add min and max as shaded area if available
                        if f"{mt}_min" in windows_data.columns and f"{mt}_max" in windows_data.columns:
                            fig.add_trace(go.Scatter(
                                x=windows_data["window_label"].tolist() + windows_data["window_label"].tolist()[::-1],
                                y=windows_data[f"{mt}_max"].tolist() + windows_data[f"{mt}_min"].tolist()[::-1],
                                fill='toself',
                                fillcolor='rgba(0,100,80,0.2)',
                                line=dict(color='rgba(255,255,255,0)'),
                                hoverinfo="skip",
                                showlegend=False,
                                name='Range'
                            ))
                        
                        fig.update_layout(
                            title=f"{measurement_type_labels.get(mt, mt)} Trend",
                            xaxis_title="Time Window",
                            yaxis_title="Value",
                            height=300
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                # Create combined trend chart with normalized values
                fig = go.Figure()
                
                for mt in selected_measurement_types:
                    if f"{mt}_values" in windows_data.columns and len(windows_data[f"{mt}_values"]) > 0:
                        print(f"\n=== NORMALIZING METRIC: {mt} ===")
                        
                        # Get values for normalization - prefer _avg if available
                        if f"{mt}_avg" in windows_data.columns:
                            print(f"Using pre-calculated average for normalization: {mt}")
                            numeric_values = windows_data[f"{mt}_avg"].tolist()
                            print(f"Numeric values: {numeric_values}")
                        elif f"{mt}_values" in windows_data.columns:
                            print(f"Calculating average from values for normalization: {mt}")
                            values = windows_data[f"{mt}_values"]
                            numeric_values = []
                            for v in values:
                                if isinstance(v, list) and v:
                                    valid_values = [item for item in v if isinstance(item, (int, float))]
                                    if valid_values:
                                        avg_value = sum(valid_values) / len(valid_values)
                                        numeric_values.append(avg_value)
                                    else:
                                        numeric_values.append(0)
                                elif isinstance(v, (int, float)):
                                    numeric_values.append(v)
                                else:
                                    numeric_values.append(0)
                        else:
                            # Skip this measurement type if no data is available
                            continue
                        
                        if numeric_values:
                            min_val = min(numeric_values)
                            max_val = max(numeric_values)
                            
                            if max_val > min_val:  # Avoid division by zero
                                normalized = [(v - min_val) / (max_val - min_val) for v in numeric_values]
                                
                                fig.add_trace(go.Scatter(
                                    x=windows_data["window_label"],
                                    y=normalized,
                                    mode="lines+markers",
                                    name=measurement_type_labels.get(mt, mt)
                                ))
                            else:
                                fig.add_trace(go.Scatter(
                                    x=windows_data["window_label"],
                                    y=[0.5] * len(numeric_values),  # Normalize constants
                                    mode="lines+markers",
                                    name=measurement_type_labels.get(mt, mt)
                                ))
                
                fig.update_layout(
                    title="Combined Trends (Normalized)",
                    xaxis_title="Time Window",
                    yaxis_title="Normalized Value (0-1)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                # Display data table
                st.dataframe(windows_data)
        
        # Display summary
        st.header("Summary")
        st.markdown(analysis.get("summary", "No summary available."))
        
        # Display insights
        st.header("Insights")
        
        insights = analysis.get("insights", [])
        if not insights:
            st.info("No insights available.")
        else:
            for i, insight in enumerate(insights):
                with st.expander(f"Insight {i+1}: {insight.get('text', 'Unknown')}", expanded=i==0):
                    st.markdown(f"**Confidence:** {insight.get('confidence', 0) * 100:.1f}%")
                    st.markdown(f"**Related Measurements:** {', '.join(insight.get('related_measurements', ['None']))}")
        
        # Display recommendations
        st.header("Recommendations")
        
        recommendations = analysis.get("recommendations", [])
        if not recommendations:
            st.info("No recommendations available.")
        else:
            # Sort by priority (highest first)
            recommendations.sort(key=lambda r: r.get("priority", 0), reverse=True)
            
            for i, recommendation in enumerate(recommendations):
                with st.expander(f"Recommendation {i+1}: {recommendation.get('text', 'Unknown')}", expanded=i==0):
                    st.markdown(f"**Priority:** {recommendation.get('priority', 0)}/5")
                    st.markdown(f"**Rationale:** {recommendation.get('rationale', 'None')}")
        
        # Actions
        st.header("Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Analysis"):
                # Convert analysis to CSV
                insights_df = pd.DataFrame(insights)
                recommendations_df = pd.DataFrame(recommendations)
                
                # Create a buffer
                csv_buffer = f"# Trend Analysis for {patient_name}\n"
                csv_buffer += f"Time Period: {analysis.get('time_period', 'Unknown')}\n"
                csv_buffer += f"Data Points Analyzed: {analysis.get('data_points_analyzed', 0)}\n"
                csv_buffer += f"Generated: {analysis.get('timestamp', 'Unknown')}\n\n"
                
                csv_buffer += "# Summary\n"
                csv_buffer += f"{analysis.get('summary', 'No summary available.')}\n\n"
                
                csv_buffer += "# Insights\n"
                if not insights:
                    csv_buffer += "No insights available.\n\n"
                else:
                    csv_buffer += insights_df.to_csv(index=False)
                    csv_buffer += "\n\n"
                
                csv_buffer += "# Recommendations\n"
                if not recommendations:
                    csv_buffer += "No recommendations available.\n\n"
                else:
                    csv_buffer += recommendations_df.to_csv(index=False)
                
                # Provide download link
                st.download_button(
                    label="Download CSV",
                    data=csv_buffer,
                    file_name=f"trend_analysis_{patient_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("Generate Report"):
                st.info("Report generation feature coming soon.")
    else:
        # Show placeholder when no analysis is available
        st.info("Configure the analysis parameters in the sidebar and click 'Run Analysis' to start.")
        
        # Example image or description
        st.markdown("""
        ### About Trend Analysis
        
        Trend analysis examines patient data across multiple time windows to identify:
        
        - **Progressive changes** in vital signs over time
        - **Response to treatments** or interventions
        - **Circadian patterns** in physiological measurements
        - **Correlation between different measurements** across time periods
        
        Configure the parameters in the sidebar to begin analyzing patient trends.
        """)


if __name__ == "__main__" or "main" not in locals():
    asyncio.run(main())
