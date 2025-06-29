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

import asyncio
from datetime import datetime, timedelta
import streamlit as st
import utils

# Page configuration
st.set_page_config(
    page_title="Settings - SmartCare Insight",
    page_icon="../assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.warning("Please log in from the home page.")
    st.stop()

if "settings" not in st.session_state:
    st.session_state.settings = {
        "refresh_interval": 30,
        "theme": "light",
        "alert_thresholds": {
            "hr": {"min": 60, "max": 100, "severity": "medium"},
            "bp_sys": {"min": 100, "max": 140, "severity": "medium"},
            "bp_dia": {"min": 60, "max": 90, "severity": "medium"},
            "oxygen": {"min": 95, "max": 100, "severity": "high"},
            "glucose": {"min": 70, "max": 120, "severity": "medium"},
            "activity": {"min": 0, "max": 1, "severity": "low"}
        }
    }

# Main function
async def main():
    """Main function for the settings page."""
    st.title("Settings")
    
    # Create tabs for different settings categories
    tab1, tab2, tab3, tab4 = st.tabs(["Display", "Alert Thresholds", "Account", "System"])
    
    with tab1:
        st.header("Display Settings")
        
        # Theme selection
        theme_options = ["light", "dark"]
        selected_theme = st.selectbox(
            "Theme",
            options=theme_options,
            index=theme_options.index(st.session_state.settings["theme"])
        )
        
        # Update theme setting
        if selected_theme != st.session_state.settings["theme"]:
            st.session_state.settings["theme"] = selected_theme
            st.success(f"Theme updated to {selected_theme}.")
        
        # Refresh interval
        refresh_interval = st.slider(
            "Auto-refresh Interval (seconds)",
            min_value=10,
            max_value=120,
            value=st.session_state.settings["refresh_interval"],
            step=5
        )
        
        # Update refresh interval setting
        if refresh_interval != st.session_state.settings["refresh_interval"]:
            st.session_state.settings["refresh_interval"] = refresh_interval
            st.success(f"Refresh interval updated to {refresh_interval} seconds.")
        
        # Chart settings
        st.subheader("Chart Settings")
        
        # Chart height
        chart_height = st.slider(
            "Chart Height (pixels)",
            min_value=200,
            max_value=600,
            value=300,
            step=50
        )
        
        # Save chart height setting
        if st.button("Save Chart Settings"):
            st.session_state.settings["chart_height"] = chart_height
            st.success("Chart settings saved.")
    
    with tab2:
        st.header("Alert Thresholds")
        
        # Vital sign thresholds
        vital_signs = {
            "hr": "Heart Rate (bpm)",
            "bp_sys": "Systolic Blood Pressure (mmHg)",
            "bp_dia": "Diastolic Blood Pressure (mmHg)",
            "oxygen": "Oxygen Saturation (%)",
            "glucose": "Blood Glucose (mg/dL)",
            "activity": "Activity Level (0-1)"
        }
        
        severity_options = ["low", "medium", "high", "critical"]
        
        # Create a form for each vital sign
        for vital_code, vital_name in vital_signs.items():
            st.subheader(vital_name)
            
            # Get current thresholds
            current_thresholds = st.session_state.settings["alert_thresholds"].get(vital_code, {"min": 0, "max": 0, "severity": "medium"})
            
            # Create columns for min, max, and severity
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_value = st.number_input(
                    f"Minimum {vital_name}",
                    value=float(current_thresholds["min"]),
                    step=1.0
                )
            
            with col2:
                max_value = st.number_input(
                    f"Maximum {vital_name}",
                    value=float(current_thresholds["max"]),
                    step=1.0
                )
            
            with col3:
                severity = st.selectbox(
                    f"Severity for {vital_name}",
                    options=severity_options,
                    index=severity_options.index(current_thresholds["severity"])
                )
            
            # Update thresholds if changed
            if (min_value != current_thresholds["min"] or 
                max_value != current_thresholds["max"] or 
                severity != current_thresholds["severity"]):
                
                st.session_state.settings["alert_thresholds"][vital_code] = {
                    "min": min_value,
                    "max": max_value,
                    "severity": severity
                }
                
                st.success(f"Thresholds updated for {vital_name}.")
        
        # Save all thresholds button
        if st.button("Save All Thresholds"):
            # In a real application, this would send the thresholds to the API
            st.success("All thresholds saved.")
    
    with tab3:
        st.header("Account Settings")
        st.subheader("User Information")
        st.markdown(f"**Username:** {st.session_state.username}")
        st.subheader("Change Password")

        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submit = st.form_submit_button("Change Password")
            
            if submit:
                if not current_password:
                    st.error("Please enter your current password.")
                elif not new_password:
                    st.error("Please enter a new password.")
                elif new_password != confirm_password:
                    st.error("New passwords do not match.")
                else:
                    # In a real application, this would verify the current password and update to the new one
                    st.success("Password changed successfully.")
        
        # Notification settings
        st.subheader("Notification Settings")
        
        receive_email = st.checkbox("Receive Email Notifications", value=True)
        receive_sms = st.checkbox("Receive SMS Notifications", value=False)
        
        if st.button("Save Notification Settings"):
            st.session_state.settings["notifications"] = {
                "email": receive_email,
                "sms": receive_sms
            }
            st.success("Notification settings saved.")
    
    with tab4:
        st.header("System Information")
        
        # System health
        st.subheader("System Health")
        
        with st.spinner("Loading system health..."):
            system_health = await utils.get_system_health()
            
            # Display overall status
            status = system_health.get("status", "unknown")
            
            if status == "healthy":
                st.success("System Status: Healthy")
            elif status == "degraded":
                st.warning("System Status: Degraded")
            else:
                st.error(f"System Status: {status.capitalize()}")
            
            # Display component status
            st.markdown("### Components")
            
            components = system_health.get("components", {})
            
            for component_name, component_details in components.items():
                component_status = component_details.get("status", "unknown")
                
                if component_status == "healthy":
                    st.success(f"{component_name.capitalize()}: Healthy")
                elif component_status == "degraded":
                    st.warning(f"{component_name.capitalize()}: Degraded")
                else:
                    st.error(f"{component_name.capitalize()}: {component_status.capitalize()}")
                
                # Display additional details if available
                if "message" in component_details:
                    st.markdown(f"*{component_details['message']}*")
        
        st.subheader("About")
        
        st.markdown("""
        **SmartCare Insight**
        
        Version: 1.0.0
        
        A demonstration of IoT and distributed systems concepts for healthcare monitoring.
        
        © 2025 SmartCare Insight
        """)

if __name__ == "__main__":
    asyncio.run(main())
