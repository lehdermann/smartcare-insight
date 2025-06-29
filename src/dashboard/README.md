# Healthcare Monitoring Dashboard

A real-time dashboard for monitoring patient health metrics, built with Streamlit.

## Features

- **Real-time Monitoring**: View live patient data
- **Interactive Visualizations**: Charts and graphs for vital signs
- **Alert Management**: View and acknowledge alerts
- **Patient Overview**: Summary of patient status
- **Responsive Design**: Works on desktop and tablet
- **Dark/Light Mode**: Toggle between themes

## Pages

### 1. Dashboard
- Overview of all patients
- System status
- Recent alerts
- Quick access to patient details

### 2. Patient Details
- Detailed patient information
- Real-time vital signs
- Historical data visualization
- Trends and patterns

### 3. Alerts
- List of active alerts
- Alert details
- Acknowledge/resolve alerts
- Filter and search

### 4. LLM Analysis
- AI-powered insights
- Time window analysis
- Event-based analysis
- Comparative analysis

### 5. Settings
- User preferences
- Notification settings
- System configuration

## Installation

### Prerequisites

- Python 3.8+
- pip
- Node.js (for development)


### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd dashboard
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables in a `.env` file:
   ```
   API_URL=http://localhost:8000/api
   MQTT_BROKER=localhost
   MQTT_PORT=1883
   MQTT_TOPIC=alerts
   ```

## Running the Dashboard

### Development Mode

```bash
streamlit run app.py
```

### Production Mode

```bash
python -m streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_URL` | Base URL for the API server | `http://localhost:8000/api` |
| `MQTT_BROKER` | MQTT broker hostname | `localhost` |
| `MQTT_PORT` | MQTT broker port | `1883` |
| `MQTT_TOPIC` | MQTT topic for real-time updates | `alerts` |
| `THEME` | Color theme (`light` or `dark`) | `light` |
| `DEBUG` | Enable debug mode | `False` |

## Development

### Project Structure

```
dashboard/
├── app.py                 # Main application
├── pages/                 # Streamlit pages
│   ├── 1_🏠_Dashboard.py
│   ├── 2_👤_Patient.py
│   ├── 3_⚠️_Alerts.py
│   ├── 4_🤖_LLM_Analysis.py
│   └── 5_⚙️_Settings.py
├── components/            # Reusable components
│   ├── __init__.py
│   ├── alerts.py
│   ├── charts.py
│   ├── patient_card.py
│   └── sidebar.py
├── services/              # API and MQTT clients
│   ├── __init__.py
│   ├── api_client.py
│   └── mqtt_client.py
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── config.py
│   └── helpers.py
├── assets/                # Static assets
│   ├── css/
│   └── images/
├── tests/                 # Tests
├── .env.example           # Example environment variables
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

### Adding a New Page

1. Create a new file in the `pages` directory with the following naming convention:
   ```
   pages/X_Page_Name.py
   ```
   Where X is the page number (determines order in the sidebar).

2. Add the following code to your page:
   ```python
   import streamlit as st

   st.set_page_config(page_title="Page Title", page_icon="📊")
   st.title("Page Title")
   
   # Your page content here
   ```

### Creating a New Component

1. Create a new file in the `components` directory.
2. Define your component as a function:
   ```python
   import streamlit as st

   def my_component(param1, param2):
       """
       A reusable component.
       
       Args:
           param1: First parameter
           param2: Second parameter
           
       Returns:
           Any: The result
       """
       # Component implementation
       return result
   ```

3. Import and use the component in your pages:
   ```python
   from components.my_component import my_component
   
   result = my_component("value1", "value2")
   ```

## Testing

### Running Tests

```bash
pytest tests/
```

### Testing with Different Screen Sizes

Use the device toolbar in your browser's developer tools to test different screen sizes.

## Deployment

### Docker

```bash
docker build -t healthcare-dashboard .
docker run -p 8501:8501 healthcare-dashboard
```

### Kubernetes

See the `kubernetes/` directory for deployment manifests.

## Performance

- Optimized data fetching
- Client-side caching
- Efficient re-rendering
- Lazy loading of components

## Security

- Secure API communication (HTTPS)
- Input validation
- XSS protection
- CSRF protection
- Secure headers

## Dependencies

- Streamlit
- Plotly
- Pandas
- Paho MQTT Client
- Requests
- python-dotenv
- pytest (for testing)

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.


## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.

### Additional Terms and Conditions

- The "SmartCare Insight" name and logo are trademarks of the original author(s).
- You may not use the "SmartCare Insight" name, logo, or branding in a way that suggests your project is endorsed by or affiliated with the original authors without explicit written permission.
- For commercial use or distribution beyond the terms of the Apache License 2.0, please contact the copyright holders for additional licensing options.
