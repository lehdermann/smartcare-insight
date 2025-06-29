#
# SmartCare Insight - Home.py
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
import asyncio
from datetime import datetime, timedelta
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import utils

# Page configuration
st.set_page_config(
    page_title="SmartCare Insight",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "patients" not in st.session_state:
    st.session_state.patients = []
if "alerts" not in st.session_state:
    st.session_state.alerts = []
if "system_health" not in st.session_state:
    st.session_state.system_health = {}

# Auto-refresh every 30 seconds
refresh_interval = 30
st_autorefresh(interval=refresh_interval * 1000, key="datarefresh")

# Authentication function
async def authenticate(username, password):
    """Authenticate with the API."""
    success = await utils.login(username, password)
    if success:
        st.session_state.authenticated = True
        st.session_state.username = username
        # Load initial data
        await load_data()
        st.rerun()
    else:
        st.error("Invalid username or password")

# Data loading function
async def load_data():
    """Load data from the API."""
    # Get patients
    patients = await utils.get_patients()
    st.session_state.patients = patients
    
    # Get active alerts
    alerts = await utils.get_alerts(status="active")
    st.session_state.alerts = alerts
    
    # Get system health
    system_health = await utils.get_system_health()
    st.session_state.system_health = system_health

# Login form
def show_login_form():
    """Show the login form."""
    st.title("SmartCare Insight")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            asyncio.run(authenticate(username, password))

# Main dashboard
def show_dashboard():
    """Show the main dashboard."""
    st.title("SmartCare Insight Dashboard")
    
    # System health indicator
    system_health = st.session_state.system_health
    health_status = system_health.get("status", "unknown")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if health_status == "healthy":
            st.success("System Status: Healthy")
        elif health_status == "degraded":
            st.warning("System Status: Degraded")
        else:
            st.error("System Status: Error")
    
    with col3:
        if st.button("Refresh Data"):
            asyncio.run(load_data())
            st.rerun()
    
    # Patient overview
    st.header("Patient Overview")
    
    # Create patient cards
    patients = st.session_state.patients
    alerts = st.session_state.alerts
    
    if not patients:
        st.info("No patients found.")
    else:
        # Group alerts by patient
        alerts_by_patient = {}
        for alert in alerts:
            patient_id = alert.get("patient_id")
            if patient_id not in alerts_by_patient:
                alerts_by_patient[patient_id] = []
            alerts_by_patient[patient_id].append(alert)
        
        # Create a row of cards for every 3 patients
        for i in range(0, len(patients), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(patients):
                    patient = patients[i + j]
                    patient_id = patient.get("id")
                    patient_alerts = alerts_by_patient.get(patient_id, [])
                    
                    with cols[j]:
                        st.subheader(patient.get("name", "Unknown"))
                        
                        # Patient info
                        st.markdown(f"**ID:** {patient_id}")
                        st.markdown(f"**Age:** {patient.get('age', 'Unknown')}")
                        st.markdown(f"**Location:** {patient.get('location', 'Unknown')}")
                        location_type = patient.get('location_type', '').capitalize()
                        if location_type:
                            st.markdown(f"**Type:** {location_type}")
                        
                        # Alert count
                        alert_count = len(patient_alerts)
                        if alert_count > 0:
                            st.error(f"Active Alerts: {alert_count}")
                        else:
                            st.success("No Active Alerts")
                        
                        # View patient button
                        if st.button("View Details", key=f"view_{patient_id}"):
                            st.session_state.selected_patient = patient_id
                            st.rerun()
    
    # Alert summary
    st.header("Active Alerts")
    
    if not alerts:
        st.info("No active alerts.")
    else:
        # Create a DataFrame for the alerts
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "Patient": next((p.get("name", "Unknown") for p in patients if p.get("id") == alert.get("patient_id")), "Unknown"),
                "Type": alert.get("measurement_type", "Unknown").upper(),
                "Value": alert.get("value", 0),
                "Severity": alert.get("severity", "Unknown").capitalize(),
                "Time": alert.get("timestamp", "Unknown"),
                "Message": alert.get("message", "Unknown"),
                "ID": alert.get("id", "Unknown")
            })
        
        alert_df = pd.DataFrame(alert_data)
        
        # Display the alerts
        st.dataframe(
            alert_df,
            column_config={
                "Patient": st.column_config.TextColumn("Patient"),
                "Type": st.column_config.TextColumn("Type"),
                "Value": st.column_config.NumberColumn("Value", format="%.1f"),
                "Severity": st.column_config.TextColumn("Severity"),
                "Time": st.column_config.DatetimeColumn("Time"),
                "Message": st.column_config.TextColumn("Message"),
                "ID": st.column_config.TextColumn("ID", width="small")
            },
            hide_index=True,
            use_container_width=True
        )
    
    # System health details
    st.header("System Health")
    
    components = system_health.get("components", {})
    
    # Create a DataFrame for the components
    component_data = []
    for name, details in components.items():
        component_data.append({
            "Component": name.capitalize(),
            "Status": details.get("status", "Unknown").capitalize(),
            "Details": details.get("message", "")
        })
    
    component_df = pd.DataFrame(component_data)
    
    # Display the components
    st.dataframe(
        component_df,
        column_config={
            "Component": st.column_config.TextColumn("Component"),
            "Status": st.column_config.TextColumn("Status"),
            "Details": st.column_config.TextColumn("Details")
        },
        hide_index=True,
        use_container_width=True
    )

# Main app logic
def main():
    """Main application logic."""
    # Show login form if not authenticated
    if not st.session_state.authenticated:
        show_login_form()
    else:
        # Show dashboard
        show_dashboard()
        
        # Sidebar
        with st.sidebar:
            st.header(f"Welcome, {st.session_state.username}")
            st.divider()
            
            st.subheader("Navigation")
            st.page_link("Home.py", label="Dashboard", icon="🏠")
            st.page_link("pages/patient_monitoring.py", label="Patient Monitoring", icon="👤")
            st.page_link("pages/alert_management.py", label="Alert Management", icon="🚨")
            st.page_link("pages/llm_analysis.py", label="LLM Analysis", icon="🧠")
            st.page_link("pages/settings.py", label="Settings", icon="⚙️")
            
            st.divider()
            
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.rerun()

if __name__ == "__main__":
    main()
