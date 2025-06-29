#
# SmartCare Insight - llm_analysis.py
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
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import utils

# Page configuration
st.set_page_config(
    page_title="AI Analysis - SmartCare Insight",
    page_icon="../assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.warning("Please log in from the home page.")
    st.stop()

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}

if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []

# Data loading functions
async def load_patients():
    """Load patients from the API."""
    if not hasattr(st.session_state, "patients") or not st.session_state.patients:
        patients = await utils.get_patients()
        st.session_state.patients = patients
    
    return st.session_state.patients

async def perform_analysis(
    analysis_type,
    patient_id,
    start_time,
    end_time,
    measurement_types=None,
    comparison_start_time=None,
    comparison_end_time=None,
    event_type=None,
    context_window_minutes=None
):
    """Perform an analysis using the LLM service."""
    analysis = await utils.get_analysis(
        analysis_type=analysis_type,
        patient_id=patient_id,
        start_time=start_time,
        end_time=end_time,
        measurement_types=measurement_types,
        comparison_start_time=comparison_start_time,
        comparison_end_time=comparison_end_time,
        event_type=event_type,
        context_window_minutes=context_window_minutes
    )
    
    if analysis:
        # Add to history
        if analysis not in st.session_state.analysis_history:
            st.session_state.analysis_history.append(analysis)
            # Keep only the 10 most recent analyses
            if len(st.session_state.analysis_history) > 10:
                st.session_state.analysis_history.pop(0)
    
    return analysis

# Main function
async def main():
    """Main function for the LLM analysis page."""
    st.title("LLM Analysis")
    
    # Load patients
    patients = await load_patients()
    
    # Sidebar for analysis configuration
    with st.sidebar:
        st.header("Analysis Configuration")
        
        # Patient selection
        patient_options = {p.get("name", f"Unknown ({p.get('id')})"): p.get("id") for p in patients}
        
        selected_patient_name = st.selectbox(
            "Patient",
            options=list(patient_options.keys()),
            index=0
        )
        
        selected_patient_id = patient_options[selected_patient_name]
        
        # Analysis type selection
        analysis_type_options = {
            "Time Window Analysis": "time_window",
            "Event-Based Analysis": "event_based",
            "Comparative Analysis": "comparative"
        }
        
        selected_analysis_type_name = st.selectbox(
            "Analysis Type",
            options=list(analysis_type_options.keys()),
            index=0
        )
        
        selected_analysis_type = analysis_type_options[selected_analysis_type_name]
        
        # Time window selection
        st.subheader("Time Window")
        
        end_time = datetime.utcnow()
        
        time_window_hours = st.slider(
            "Hours",
            min_value=1,
            max_value=72,
            value=24,
            step=1
        )
        
        start_time = end_time - timedelta(hours=time_window_hours)
        
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
        
        # Additional parameters based on analysis type
        if selected_analysis_type == "comparative":
            st.subheader("Comparison Window")
            
            comparison_window_hours = st.slider(
                "Hours Before Current Window",
                min_value=1,
                max_value=168,  # 1 week
                value=24,
                step=1
            )
            
            comparison_end_time = start_time
            comparison_start_time = comparison_end_time - timedelta(hours=comparison_window_hours)
        
        elif selected_analysis_type == "event_based":
            st.subheader("Event Configuration")
            
            event_type_options = {
                "Anomalies": "anomaly",
                "Threshold Violations": "threshold",
                "Activity Spikes": "activity_spike"
            }
            
            selected_event_type_name = st.selectbox(
                "Event Type",
                options=list(event_type_options.keys()),
                index=0
            )
            
            selected_event_type = event_type_options[selected_event_type_name]
            
            context_window_minutes = st.slider(
                "Context Window (minutes)",
                min_value=5,
                max_value=120,
                value=30,
                step=5
            )
        
        # Run analysis button
        if st.button("Run Analysis"):
            with st.spinner("Running analysis..."):
                # Prepare parameters
                params = {
                    "analysis_type": selected_analysis_type,
                    "patient_id": selected_patient_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "measurement_types": selected_measurement_types
                }
                
                # Add parameters for comparative analysis
                if selected_analysis_type == "comparative":
                    params["comparison_start_time"] = comparison_start_time
                    params["comparison_end_time"] = comparison_end_time
                
                # Add parameters for event-based analysis
                elif selected_analysis_type == "event_based":
                    params["event_type"] = selected_event_type
                    params["context_window_minutes"] = context_window_minutes
                
                # Run analysis
                analysis = await perform_analysis(**params)
                
                # Store analysis results in session state
                if analysis:
                    key = f"{selected_patient_id}_{selected_analysis_type}_{datetime.utcnow().isoformat()}"
                    st.session_state.analysis_results[key] = analysis
                    st.session_state.current_analysis = key
                else:
                    st.error("Failed to perform analysis. Please try again.")
    
    # Main content area
    if hasattr(st.session_state, "current_analysis") and st.session_state.current_analysis in st.session_state.analysis_results:
        # Display current analysis
        analysis = st.session_state.analysis_results[st.session_state.current_analysis]
        
        # Get patient name
        patient_id = analysis.get("patient_id")
        patient_name = next((p.get("name", "Unknown") for p in patients if p.get("id") == patient_id), "Unknown")
        
        # Display analysis header
        st.header(f"Analysis for {patient_name}")
        st.subheader(f"Type: {analysis.get('analysis_type', 'Unknown').replace('_', ' ').title()}")
        st.markdown(f"**Time Period:** {analysis.get('time_period', 'Unknown')}")
        st.markdown(f"**Data Points Analyzed:** {analysis.get('data_points_analyzed', 0)}")
        st.markdown(f"**Generated:** {analysis.get('timestamp', 'Unknown')}")
        
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
                csv_buffer = f"# Analysis for {patient_name}\n"
                csv_buffer += f"Type: {analysis.get('analysis_type', 'Unknown').replace('_', ' ').title()}\n"
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
                
                # Download button
                st.download_button(
                    label="Download CSV",
                    data=csv_buffer,
                    file_name=f"analysis_{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("Generate New Analysis"):
                # Clear current analysis
                if hasattr(st.session_state, "current_analysis"):
                    del st.session_state.current_analysis
                st.experimental_rerun()
    
    else:
        # Display analysis history or instructions
        if st.session_state.analysis_history:
            st.header("Analysis History")
            
            for i, analysis in enumerate(reversed(st.session_state.analysis_history)):
                patient_id = analysis.get("patient_id")
                patient_name = next((p.get("name", "Unknown") for p in patients if p.get("id") == patient_id), "Unknown")
                
                with st.expander(f"{patient_name} - {analysis.get('analysis_type', 'Unknown').replace('_', ' ').title()} - {analysis.get('timestamp', 'Unknown')}", expanded=i==0):
                    st.markdown(f"**Time Period:** {analysis.get('time_period', 'Unknown')}")
                    st.markdown(f"**Summary:** {analysis.get('summary', 'No summary available.')}")
                    
                    if st.button("View Full Analysis", key=f"view_{i}"):
                        # Store in session state
                        key = f"{patient_id}_{analysis.get('analysis_type')}_{datetime.utcnow().isoformat()}"
                        st.session_state.analysis_results[key] = analysis
                        st.session_state.current_analysis = key
                        st.experimental_rerun()
        else:
            st.info("Configure and run an analysis using the sidebar controls.")
            
            st.header("About LLM Analysis")
            
            st.markdown("""
            The LLM Analysis feature uses Large Language Models to provide contextual insights and recommendations based on patient vital signs data. Three types of analysis are available:
            
            1. **Time Window Analysis**: Analyzes patient data over a specific time window to identify patterns, trends, and anomalies.
            
            2. **Event-Based Analysis**: Focuses on the context around specific events such as anomalies or threshold violations.
            
            3. **Comparative Analysis**: Compares patient data between two time periods to identify changes and trends.
            
            To get started, select a patient and analysis type in the sidebar, then click "Run Analysis".
            """)

# Run the app
if __name__ == "__main__":
    asyncio.run(main())
