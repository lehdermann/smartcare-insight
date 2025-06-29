#
# SmartCare Insight - patient_monitoring.py
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
from datetime import datetime, timedelta
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import utils

# Page configuration
st.set_page_config(
    page_title="Patient Monitoring - SmartCare Insight",
    page_icon="../assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.warning("Please log in from the home page.")
    st.stop()

if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None

if "patient_vitals" not in st.session_state:
    st.session_state.patient_vitals = {}

if "patient_alerts" not in st.session_state:
    st.session_state.patient_alerts = []

# Auto-refresh every 30 seconds
refresh_interval = 30
st_autorefresh(interval=refresh_interval * 1000, key="patientrefresh")

# Data loading functions
async def load_patient_data(patient_id):
    """Load patient data from the API."""
    # Get patient details
    patient = await utils.get_patient(patient_id)
    
    # Get patient vitals for the last 24 hours
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    vitals_response = await utils.get_patient_vitals(
        patient_id=patient_id,
        start_time=start_time,
        end_time=end_time
    )
    
    # Get patient alerts
    alerts = await utils.get_alerts(patient_id=patient_id)
    
    return patient, vitals_response, alerts

# Visualization functions
def create_vital_chart(vital_data, measurement_type, title, y_axis_title, normal_range=None):
    """Create a chart for a vital sign."""
    # Filter data for the measurement type
    filtered_data = [v for v in vital_data if v.get("measurement_type") == measurement_type]
    
    if not filtered_data:
        return go.Figure()
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame([
        {
            "timestamp": datetime.fromisoformat(v.get("timestamp").replace("Z", "+00:00")),
            "value": v.get("value"),
            "is_anomaly": v.get("is_anomaly", False)
        }
        for v in filtered_data
    ])
    
    # Sort by timestamp
    df = df.sort_values("timestamp")
    
    # Create figure
    fig = go.Figure()
    
    # Add normal range if provided
    if normal_range:
        min_val, max_val = normal_range
        fig.add_shape(
            type="rect",
            x0=df["timestamp"].min(),
            x1=df["timestamp"].max(),
            y0=min_val,
            y1=max_val,
            fillcolor="rgba(0,255,0,0.1)",
            line=dict(width=0),
            layer="below"
        )
    
    # Add line for normal values
    normal_df = df[~df["is_anomaly"]]
    if not normal_df.empty:
        fig.add_trace(go.Scatter(
            x=normal_df["timestamp"],
            y=normal_df["value"],
            mode="lines",
            name="Normal",
            line=dict(color="blue")
        ))
    
    # Add markers for anomalies
    anomaly_df = df[df["is_anomaly"]]
    if not anomaly_df.empty:
        fig.add_trace(go.Scatter(
            x=anomaly_df["timestamp"],
            y=anomaly_df["value"],
            mode="markers",
            name="Anomaly",
            marker=dict(color="red", size=10)
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title=y_axis_title,
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

# Main function
async def main():
    """Main function for the patient monitoring page."""
    st.title("Patient Monitoring")
    
    # Get patients for the sidebar
    if not hasattr(st.session_state, "patients") or not st.session_state.patients:
        patients = await utils.get_patients()
        st.session_state.patients = patients
    else:
        patients = st.session_state.patients
    
    # Sidebar for patient selection
    with st.sidebar:
        st.header("Patient Selection")
        
        # Create a selectbox for patient selection
        patient_options = {p.get("name", f"Unknown ({p.get('id')})"): p.get("id") for p in patients}
        selected_name = st.selectbox(
            "Select Patient",
            options=list(patient_options.keys()),
            index=0 if not st.session_state.selected_patient else list(patient_options.values()).index(st.session_state.selected_patient)
        )
        
        selected_patient_id = patient_options[selected_name]
        st.session_state.selected_patient = selected_patient_id
        
        # Time window selection
        st.header("Time Window")
        time_window = st.slider(
            "Hours",
            min_value=1,
            max_value=72,
            value=24,
            step=1
        )
        
        # Refresh button
        if st.button("Refresh Data"):
            st.session_state.patient_vitals = {}
            st.session_state.patient_alerts = []
    
    # Load patient data if needed
    if st.session_state.selected_patient:
        if not st.session_state.patient_vitals.get(st.session_state.selected_patient):
            with st.spinner("Loading patient data..."):
                patient, vitals_response, alerts = await load_patient_data(st.session_state.selected_patient)
                
                st.session_state.patient_vitals[st.session_state.selected_patient] = {
                    "patient": patient,
                    "vitals": vitals_response.get("vitals", []),
                    "timestamp": datetime.utcnow()
                }
                
                st.session_state.patient_alerts = alerts
        
        # Get patient data from session state
        patient_data = st.session_state.patient_vitals[st.session_state.selected_patient]
        patient = patient_data["patient"]
        
        # Check if patient is None and provide a default value
        if patient is None:
            patient = {
                "name": "Unknown", 
                "id": st.session_state.selected_patient, 
                "age": "N/A", 
                "gender": "N/A", 
                "location": "N/A",
                "monitoring_start": "N/A"
            }
            st.error("Failed to load patient data. Please refresh the page.")
            
        vitals = patient_data["vitals"]
        alerts = st.session_state.patient_alerts
        
        # Display patient information
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.subheader(patient.get("name", "Unknown"))
            st.markdown(f"**ID:** {patient.get('id', 'Unknown')}")
            st.markdown(f"**Age:** {patient.get('age', 'Unknown')}")
            st.markdown(f"**Gender:** {patient.get('gender', 'Unknown')}")
        
        with col2:
            st.markdown(f"**Location:** {patient.get('location', 'Unknown')}")
            location_type = patient.get('location_type', '').capitalize()
            st.markdown(f"**Type:** {location_type if location_type else 'N/A'}")
            monitoring_start = patient.get('monitoring_start')
            if monitoring_start and monitoring_start != 'N/A':
                if isinstance(monitoring_start, str):
                    monitoring_start = datetime.fromisoformat(monitoring_start)
                st.markdown(f"**Monitoring Since:** {monitoring_start.strftime('%Y-%m-%d')}")
            else:
                st.markdown("**Monitoring Since:** N/A")
        
        with col3:
            st.markdown(f"**Primary Condition:** {patient.get('primary_condition', 'Unknown')}")
            st.markdown(f"**Notes:** {patient.get('notes', 'None')}")
            
            # Display alert count
            active_alerts = [a for a in alerts if a.get("status") == "active"]
            if active_alerts:
                st.error(f"Active Alerts: {len(active_alerts)}")
            else:
                st.success("No Active Alerts")
        
        # Display vital signs charts
        st.header("Vital Signs")
        
        # Heart rate
        st.plotly_chart(
            create_vital_chart(
                vitals,
                "hr",
                "Heart Rate",
                "BPM",
                (60, 100)
            ),
            use_container_width=True,
            key="hr_chart"
        )
        
        # Blood pressure (systolic and diastolic)
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                create_vital_chart(
                    vitals,
                    "bp_sys",
                    "Systolic Blood Pressure",
                    "mmHg",
                    (100, 140)
                ),
                use_container_width=True,
                key="bp_sys_chart"
            )
        
        with col2:
            st.plotly_chart(
                create_vital_chart(
                    vitals,
                    "bp_dia",
                    "Diastolic Blood Pressure",
                    "mmHg",
                    (60, 90)
                ),
                use_container_width=True,
                key="bp_dia_chart"
            )
        
        # Oxygen saturation
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                create_vital_chart(
                    vitals,
                    "oxygen",
                    "Oxygen Saturation",
                    "%",
                    (95, 100)
                ),
                use_container_width=True,
                key="oxygen_chart"
            )
        
        with col2:
            st.plotly_chart(
                create_vital_chart(
                    vitals,
                    "glucose",
                    "Blood Glucose",
                    "mg/dL",
                    (70, 120)
                ),
                use_container_width=True,
                key="glucose_chart"
            )
        
        # Activity level
        st.plotly_chart(
            create_vital_chart(
                vitals,
                "activity",
                "Activity Level",
                "Level",
                (0, 1)
            ),
            use_container_width=True,
            key="activity_chart"
        )
        
        # Display recent alerts
        st.header("Recent Alerts")
        
        if not alerts:
            st.info("No alerts for this patient.")
        else:
            # Create a DataFrame for the alerts
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    "Type": alert.get("measurement_type", "Unknown").upper(),
                    "Value": alert.get("value", 0),
                    "Severity": alert.get("severity", "Unknown").capitalize(),
                    "Time": alert.get("timestamp", "Unknown"),
                    "Status": alert.get("status", "Unknown").capitalize(),
                    "Message": alert.get("message", "Unknown"),
                    "ID": alert.get("id", "Unknown")
                })
            
            alert_df = pd.DataFrame(alert_data)
            
            # Display the alerts
            st.dataframe(
                alert_df,
                column_config={
                    "Type": st.column_config.TextColumn("Type"),
                    "Value": st.column_config.NumberColumn("Value", format="%.1f"),
                    "Severity": st.column_config.TextColumn("Severity"),
                    "Time": st.column_config.DatetimeColumn("Time"),
                    "Status": st.column_config.TextColumn("Status"),
                    "Message": st.column_config.TextColumn("Message"),
                    "ID": st.column_config.TextColumn("ID", width="small")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Add buttons to acknowledge or resolve alerts
            active_alerts = [a for a in alerts if a.get("status") == "active"]
            if active_alerts:
                st.subheader("Manage Alerts")
                
                # Create columns for each alert
                cols = st.columns(len(active_alerts))
                
                for i, alert in enumerate(active_alerts):
                    with cols[i]:
                        st.markdown(f"**{alert.get('measurement_type', '').upper()}:** {alert.get('message', '')}")
                        
                        ack_col, res_col = st.columns(2)
                        
                        with ack_col:
                            if st.button("Acknowledge", key=f"ack_{alert.get('id')}"):
                                try:
                                    await utils.update_alert(
                                        alert_id=alert.get("id"),
                                        status="acknowledged",
                                        acknowledged_by=st.session_state.username
                                    )
                                    st.success("Alert acknowledged")
                                    st.session_state.patient_alerts = []  # Force refresh
                                except Exception as e:
                                    st.error(f"Failed to acknowledge alert: {str(e)}")
                        
                        with res_col:
                            if st.button("Resolve", key=f"res_{alert.get('id')}"):
                                try:
                                    await utils.update_alert(
                                        alert_id=alert.get("id"),
                                        status="resolved",
                                        acknowledged_by=st.session_state.username
                                    )
                                    st.success("Alert resolved")
                                    st.session_state.patient_alerts = []  # Force refresh
                                except Exception as e:
                                    st.error(f"Failed to resolve alert: {str(e)}")
    else:
        st.info("Please select a patient from the sidebar.")

if __name__ == "__main__":
    # Cria um loop de eventos assíncrono e executa a função main
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        loop.close()
