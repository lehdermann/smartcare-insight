#
# SmartCare Insight - alert_management.py
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
    page_title="Alerts - SmartCare Insight",
    page_icon="../assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.warning("Please log in from the home page.")
    st.stop()

if "all_alerts" not in st.session_state:
    st.session_state.all_alerts = []

# Auto-refresh every 30 seconds
refresh_interval = 30
st_autorefresh(interval=refresh_interval * 1000, key="alertrefresh")

# Data loading functions
async def load_alerts(patient_id=None, status=None, severity=None, limit=100):
    """Load alerts from the API."""
    alerts = await utils.get_alerts(
        patient_id=patient_id,
        status=status,
        severity=severity,
        limit=limit
    )
    
    return alerts

async def load_patients():
    """Load patients from the API."""
    if not hasattr(st.session_state, "patients") or not st.session_state.patients:
        patients = await utils.get_patients()
        st.session_state.patients = patients
    
    return st.session_state.patients

# Alert management functions
async def acknowledge_alert(alert_id):
    """Acknowledge an alert."""
    result = await utils.update_alert(
        alert_id=alert_id,
        status="acknowledged",
        acknowledged_by=st.session_state.username
    )
    
    if result:
        st.success(f"Alert {alert_id} acknowledged")
        # Refresh alerts
        st.session_state.all_alerts = []
        return True
    else:
        st.error(f"Failed to acknowledge alert {alert_id}")
        return False

async def resolve_alert(alert_id):
    """Resolve an alert."""
    result = await utils.update_alert(
        alert_id=alert_id,
        status="resolved",
        acknowledged_by=st.session_state.username
    )
    
    if result:
        st.success(f"Alert {alert_id} resolved")
        # Refresh alerts
        st.session_state.all_alerts = []
        return True
    else:
        st.error(f"Failed to resolve alert {alert_id}")
        return False

# Visualization functions
def create_alert_trend_chart(alerts):
    """Create a chart showing alert trends over time."""
    if not alerts:
        return go.Figure()
    
    # Convert timestamps to datetime
    for alert in alerts:
        if isinstance(alert.get("timestamp"), str):
            alert["timestamp"] = datetime.fromisoformat(alert.get("timestamp").replace("Z", "+00:00"))
    
    # Group alerts by day and severity
    alert_counts = {}
    for alert in alerts:
        day = alert.get("timestamp").date()
        severity = alert.get("severity", "unknown")
        
        if day not in alert_counts:
            alert_counts[day] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        alert_counts[day][severity] += 1
    
    # Sort days
    days = sorted(alert_counts.keys())
    # Create figure
    fig = go.Figure()
    
    # Add traces for each severity
    severities = ["low", "medium", "high", "critical"]
    colors = ["green", "yellow", "orange", "red"]
    
    for severity, color in zip(severities, colors):
        fig.add_trace(go.Bar(
            x=days,
            y=[alert_counts[day][severity] for day in days],
            name=severity.capitalize(),
            marker_color=color
        ))
    
    # Update layout
    fig.update_layout(
        title="Alert Trends by Day and Severity",
        xaxis_title="Date",
        yaxis_title="Number of Alerts",
        barmode="stack",
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

# Main function
async def main():
    """Main function for the alert management page."""
    st.title("Alert Management")
    
    # Load patients
    patients = await load_patients()
    
    # Sidebar for filters
    with st.sidebar:
        st.header("Alert Filters")
        
        # Patient filter
        patient_options = {"All Patients": None}
        patient_options.update({p.get("name", f"Unknown ({p.get('id')})"): p.get("id") for p in patients})
        
        selected_patient_name = st.selectbox(
            "Patient",
            options=list(patient_options.keys()),
            index=0
        )
        
        selected_patient_id = patient_options[selected_patient_name]
        
        # Status filter
        status_options = {
            "All Statuses": None,
            "Active": "active",
            "Acknowledged": "acknowledged",
            "Resolved": "resolved"
        }
        
        selected_status_name = st.selectbox(
            "Status",
            options=list(status_options.keys()),
            index=0
        )
        
        selected_status = status_options[selected_status_name]
        
        # Severity filter
        severity_options = {
            "All Severities": None,
            "Low": "low",
            "Medium": "medium",
            "High": "high",
            "Critical": "critical"
        }
        
        selected_severity_name = st.selectbox(
            "Severity",
            options=list(severity_options.keys()),
            index=0
        )
        
        selected_severity = severity_options[selected_severity_name]
        
        # Limit filter
        limit = st.slider(
            "Maximum Alerts",
            min_value=10,
            max_value=500,
            value=100,
            step=10
        )
        
        # Refresh button
        if st.button("Refresh Alerts"):
            st.session_state.all_alerts = []
    
    # Load alerts if needed
    if not st.session_state.all_alerts:
        with st.spinner("Loading alerts..."):
            alerts = await load_alerts(
                patient_id=selected_patient_id,
                status=selected_status,
                severity=selected_severity,
                limit=limit
            )
            
            st.session_state.all_alerts = alerts
    else:
        alerts = st.session_state.all_alerts

    st.header("Alert Summary")
    # Create summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_count = len([a for a in alerts if a.get("status") == "active"])
        st.metric("Active Alerts", active_count)
    
    with col2:
        acknowledged_count = len([a for a in alerts if a.get("status") == "acknowledged"])
        st.metric("Acknowledged Alerts", acknowledged_count)
    
    with col3:
        resolved_count = len([a for a in alerts if a.get("status") == "resolved"])
        st.metric("Resolved Alerts", resolved_count)
    
    with col4:
        total_count = len(alerts)
        st.metric("Total Alerts", total_count)
    
    # Display alert trend chart
    st.plotly_chart(create_alert_trend_chart(alerts), use_container_width=True)
    
    # Display alert table
    st.header("Alert List")
    
    if not alerts:
        st.info("No alerts found matching the selected filters.")
    else:
        # Create a DataFrame for the alerts
        alert_data = []
        for alert in alerts:
            # Find patient name
            patient_id = alert.get("patient_id")
            patient_name = next((p.get("name", "Unknown") for p in patients if p.get("id") == patient_id), "Unknown")
            
            # Format timestamp
            timestamp = alert.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            
            alert_data.append({
                "ID": alert.get("id", "Unknown"),
                "Patient": patient_name,
                "Type": alert.get("measurement_type", "Unknown").upper(),
                "Value": alert.get("value", 0),
                "Severity": alert.get("severity", "Unknown").capitalize(),
                "Time": timestamp,
                "Status": alert.get("status", "Unknown").capitalize(),
                "Message": alert.get("message", "Unknown"),
                "Acknowledged By": alert.get("acknowledged_by", ""),
                "Acknowledged At": alert.get("acknowledged_at", ""),
                "Resolved At": alert.get("resolved_at", "")
            })
        
        alert_df = pd.DataFrame(alert_data)
        
        # Display the alerts
        st.dataframe(
            alert_df,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Patient": st.column_config.TextColumn("Patient"),
                "Type": st.column_config.TextColumn("Type"),
                "Value": st.column_config.NumberColumn("Value", format="%.1f"),
                "Severity": st.column_config.TextColumn("Severity"),
                "Time": st.column_config.DatetimeColumn("Time"),
                "Status": st.column_config.TextColumn("Status"),
                "Message": st.column_config.TextColumn("Message"),
                "Acknowledged By": st.column_config.TextColumn("Acknowledged By"),
                "Acknowledged At": st.column_config.DatetimeColumn("Acknowledged At"),
                "Resolved At": st.column_config.DatetimeColumn("Resolved At")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Alert management section
        st.header("Manage Alerts")
        
        # Only show active alerts for management
        active_alerts = [a for a in alerts if a.get("status") == "active"]
        
        if not active_alerts:
            st.info("No active alerts to manage.")
        else:
            # Create a selection for the alert to manage
            alert_options = {f"{a.get('measurement_type', '').upper()} - {a.get('message', '')} ({a.get('patient_id', '')})": a.get("id") for a in active_alerts}
            
            selected_alert_desc = st.selectbox(
                "Select Alert to Manage",
                options=list(alert_options.keys()),
                index=0
            )
            
            selected_alert_id = alert_options[selected_alert_desc]
            
            # Create buttons for actions
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Acknowledge Alert"):
                    asyncio.run(acknowledge_alert(selected_alert_id))
            
            with col2:
                if st.button("Resolve Alert"):
                    asyncio.run(resolve_alert(selected_alert_id))
        
        # Bulk actions
        st.header("Bulk Actions")
        
        # Only enable if there are active alerts
        if not active_alerts:
            st.info("No active alerts for bulk actions.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Acknowledge All Active Alerts"):
                    with st.spinner("Acknowledging alerts..."):
                        success_count = 0
                        for alert in active_alerts:
                            result = await acknowledge_alert(alert.get("id"))
                            if result:
                                success_count += 1
                        
                        st.success(f"Acknowledged {success_count} of {len(active_alerts)} alerts")
            
            with col2:
                if st.button("Resolve All Active Alerts"):
                    with st.spinner("Resolving alerts..."):
                        success_count = 0
                        for alert in active_alerts:
                            result = await resolve_alert(alert.get("id"))
                            if result:
                                success_count += 1
                        
                        st.success(f"Resolved {success_count} of {len(active_alerts)} alerts")
        
        # Export options
        st.header("Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export to CSV"):
                csv = alert_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("Export to Excel"):
                # Create Excel file in memory
                excel_buffer = pd.ExcelWriter(f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", engine="xlsxwriter")
                alert_df.to_excel(excel_buffer, index=False, sheet_name="Alerts")
                excel_buffer.save()
                
                with open(excel_buffer.path, "rb") as f:
                    excel_data = f.read()
                
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name=f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    asyncio.run(main())
