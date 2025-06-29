# Alert Manager Service

The Alert Manager monitors patient vital signs in real-time, detects anomalies, and generates alerts when thresholds are exceeded or unusual patterns are detected.

## Features

- **Real-time Monitoring**: Continuously analyzes incoming health data
- **Configurable Rules**: Define custom alert rules for different vital signs
- **Multi-level Alerts**: Supports different severity levels (info, warning, critical)
- **Deduplication**: Prevents duplicate alerts for the same condition
- **Webhook Support**: Send alerts to external systems
- **REST API**: Programmatic access to alerts and configurations

## Alert Rules

Alerts are triggered based on multi-level severity thresholds:

### Heart Rate (bpm)
- **Normal**: 60-100 bpm
- **Low**: 50-59 bpm (Warning)
- **Very Low**: 40-49 bpm (High)
- **Critical Low**: <40 bpm (Critical)
- **High**: 101-110 bpm (Warning)
- **Very High**: 111-130 bpm (High)
- **Critical High**: >130 bpm (Critical)

### Blood Pressure (mmHg)
#### Systolic
- **Normal**: 100-120
- **Elevated**: 121-139 (Low)
- **Stage 1 Hypertension**: 140-159 (Medium)
- **Stage 2 Hypertension**: 160-179 (High)
- **Hypertensive Crisis**: ≥180 (Critical)

#### Diastolic
- **Normal**: 60-80
- **Elevated**: 81-89 (Low)
- **Stage 1 Hypertension**: 90-99 (Medium)
- **Stage 2 Hypertension**: 100-109 (High)
- **Hypertensive Crisis**: ≥110 (Critical)

### Oxygen Saturation (%)
- **Normal**: 95-100%
- **Mild Hypoxia**: 90-94% (Low)
- **Moderate Hypoxia**: 85-89% (Medium)
- **Severe Hypoxia**: <85% (Critical)

### Blood Glucose (mg/dL)
- **Normal**: 70-140
- **Mild Hypoglycemia**: 54-69 (Medium)
- **Severe Hypoglycemia**: <54 (Critical)
- **Hyperglycemia**: 141-180 (Low)
- **Severe Hyperglycemia**: 181-250 (High)
- **Critical Hyperglycemia**: >250 (Critical)

## API Endpoints

### `GET /alerts`

List all alerts with optional filters.

**Query Parameters:**
- `patient_id`: Filter by patient ID
- `status`: Filter by status (active, resolved, acknowledged)
- `severity`: Filter by severity (info, warning, critical)
- `limit`: Maximum number of alerts to return
- `offset`: Pagination offset

**Example Response:**
```json
{
  "alerts": [
    {
      "id": "alert-123",
      "patient_id": "patient-1",
      "type": "high_heart_rate",
      "severity": "warning",
      "message": "Elevated heart rate detected: 105 bpm",
      "value": 105,
      "threshold": 100,
      "timestamp": "2023-01-01T12:00:00Z",
      "status": "active"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

### `POST /alerts/acknowledge`

Acknowledge an alert.

**Request Body:**
```json
{
  "alert_id": "alert-123",
  "notes": "Monitoring patient"
}
```

### `GET /alerts/stats`

Get alert statistics.

**Response:**
```json
{
  "total_alerts": 42,
  "active_alerts": 3,
  "by_severity": {
    "info": 20,
    "warning": 15,
    "critical": 7
  },
  "by_type": {
    "high_heart_rate": 10,
    "low_blood_oxygen": 5,
    "high_blood_pressure": 8,
    "high_glucose": 4
  }
}
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `INFLUXDB_URL` | InfluxDB connection URL | `http://influxdb:8086` | Yes |
| `INFLUXDB_TOKEN` | InfluxDB authentication token | - | Yes |
| `INFLUXDB_ORG` | InfluxDB organization | `healthcare` | No |
| `INFLUXDB_BUCKET` | InfluxDB bucket name | `health_metrics` | No |
| `MQTT_BROKER` | MQTT broker hostname | `mosquitto` | No |
| `MQTT_PORT` | MQTT broker port | `1883` | No |
| `MQTT_TOPIC` | MQTT topic for alerts | `alerts` | No |
| `CHECK_INTERVAL` | How often to check for alerts (seconds) | `10` | No |

## Development

### Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables in a `.env` file:
   ```
   INFLUXDB_URL=http://localhost:8086
   INFLUXDB_TOKEN=your_influxdb_token
   ```

### Running Locally

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

Run tests:
```bash
pytest tests/
```

## 🏥 Medical Context and Alerting Principles

### Multi-Level Alerting System

The alert manager implements a sophisticated multi-level alerting system that categorizes physiological measurements into different severity levels based on clinical guidelines. This approach allows for:

1. **Graduated Response**: Different severity levels (Low, Medium, High, Critical) enable appropriate clinical responses
2. **Reduced Alert Fatigue**: By categorizing alerts by severity, clinicians can prioritize their attention
3. **Early Warning**: Subtle deviations from normal ranges trigger lower-severity alerts, enabling early intervention

### Clinical Basis for Thresholds

#### Heart Rate Monitoring
- **Bradycardia Spectrum**:
  - Mild: 50-59 bpm (Low severity)
  - Moderate: 40-49 bpm (High severity)
  - Severe: <40 bpm (Critical)
  
- **Tachycardia Spectrum**:
  - Mild: 101-110 bpm (Low severity)
  - Moderate: 111-130 bpm (High severity)
  - Severe: >130 bpm (Critical)

#### Blood Pressure Management
- **Hypertension Staging**:
  - Elevated: 121-139/81-89 mmHg (Low)
  - Stage 1: 140-159/90-99 mmHg (Medium)
  - Stage 2: 160-179/100-109 mmHg (High)
  - Hypertensive Crisis: ≥180/110 mmHg (Critical)

#### Oxygen Saturation
- **Hypoxia Classification**:
  - Mild: 90-94% (Low)
  - Moderate: 85-89% (Medium)
  - Severe: <85% (Critical)

#### Glucose Monitoring
- **Hypoglycemia**:
  - Level 1: <70 mg/dL (Medium)
  - Level 2: <54 mg/dL (Critical)
  
- **Hyperglycemia**:
  - Elevated: 141-180 mg/dL (Low)
  - High: 181-250 mg/dL (High)
  - Critical: >250 mg/dL (Critical)

## ⚠️ Medical Assumptions and Limitations

### Clinical Assumptions

1. **Fixed Thresholds**
   - Uses population-based thresholds that may not account for individual patient baselines
   - Does not adjust for age, comorbidities, or medications

2. **Single-Parameter Alerts**
   - Alerts are generated based on individual parameter thresholds
   - No correlation between related parameters (e.g., heart rate and blood pressure)

3. **Response Time**
   - Assumes immediate clinical significance when thresholds are crossed
   - Does not account for duration of abnormal values

### Technical Limitations

1. **Data Interpretation**
   - No distinction between artifact and true physiological changes
   - Limited ability to detect trends over time

2. **Clinical Context**
   - Lacks patient history for contextual alerting
   - No integration with medication schedules or care plans

3. **Alert Fatigue**
   - Basic threshold-based system may generate excessive alerts
   - No sophisticated alert suppression or prioritization

## 🏗️ Architecture

The Alert Manager consists of the following components:

- **Alert Engine**: Processes incoming data and evaluates alert rules
- **Rule Engine**: Manages alert rules and conditions
- **Notification Service**: Handles alert notifications
- **API Server**: Provides REST endpoints for alert management
- **InfluxDB Client**: Fetches and stores time-series data

## Performance Considerations

- The service is designed to handle high volumes of data points
- Alert evaluation is optimized for performance
- In-memory caching is used for frequently accessed data

## Security

- All API endpoints require authentication
- Sensitive data is encrypted at rest and in transit
- Rate limiting is implemented to prevent abuse

## Dependencies

- FastAPI
- Pydantic
- InfluxDB Client
- Paho MQTT Client
- python-dotenv
- uvicorn

## 📚 Clinical Alert Threshold References

### Vital Sign Monitoring and Alert Thresholds
- Drew, B. J., et al. (2004). *Practice Standards for Electrocardiographic Monitoring in Hospital Settings: An American Heart Association Scientific Statement*. Circulation, 110(17), 2721-2746. https://doi.org/10.1161/01.CIR.0000145144.56673.59
  - Estabelece padrões baseados em evidências para monitoramento cardíaco e limiares de alerta

- Taenzer, A. H., et al. (2010). *Impact of Pulse Oximetry Surveillance on Rescue Events and Intensive Care Unit Transfers: A Before-and-After Concurrence Study*. Anesthesiology, 112(2), 282-287. https://doi.org/10.1097/ALN.0b013e3181ca7a9b
  - Define limiares ótimos de SpO2 para alertas baseados em desfechos clínicos

### Blood Pressure Alert Parameters
- Pickering, T. G., et al. (2005). *Recommendations for Blood Pressure Measurement in Humans and Experimental Animals: Part 1: Blood Pressure Measurement in Humans: A Statement for Professionals From the Subcommittee of Professional and Public Education of the American Heart Association Council on High Blood Pressure Research*. Hypertension, 45(1), 142-161. https://doi.org/10.1161/01.HYP.0000150859.47929.8e
  - Estabelece parâmetros baseados em evidências para alertas de hipertensão

### Hypoglycemia Alert Thresholds
- Seaquist, E. R., et al. (2013). *Hypoglycemia and Diabetes: A Report of a Workgroup of the American Diabetes Association and The Endocrine Society*. Diabetes Care, 36(5), 1384-1395. https://doi.org/10.2337/dc12-2480
  - Define limiares clínicos para alertas de hipoglicemia baseados em risco

### Alarm Management and Clinical Impact
- Cvach, M. (2012). *Monitor Alarm Fatigue: An Integrative Review*. Biomedical Instrumentation & Technology, 46(4), 268-277. https://doi.org/10.2345/0899-8205-46.4.268
  - Estudo sobre o impacto dos limiares de alerta na fadiga de alarme

- Paine, C. W., et al. (2016). *Systematic Review of Physiologic Monitor Alarm Characteristics and Pragmatic Interventions to Reduce Alarm Frequency*. Journal of Hospital Medicine, 11(2), 136-144. https://doi.org/10.1002/jhm.2520
  - Revisão sistemática sobre otimização de limiares de alerta

### Evidence-Based Alert Thresholds
- Winters, B. D., et al. (2018). *Technologic Distractions (Part 2): A Summary of Approaches to Manage Clinical Alarms with Intent to Reduce Alarm Fatigue*. Critical Care Medicine, 46(1), 130-137. https://doi.org/10.1097/CCM.0000000000002803
  - Abordagens baseadas em evidências para gestão de alertas clínicos

- Sendelbach, S., & Funk, M. (2013). *Alarm Fatigue: A Patient Safety Concern*. AACN Advanced Critical Care, 24(4), 378-386. https://doi.org/10.1097/NCI.0b013e3182a903f9
  - Análise do impacto dos limiares de alerta na segurança do paciente

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.


## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.

### Additional Terms and Conditions

- The "SmartCare Insight" name and logo are trademarks of the original author(s).
- You may not use the "SmartCare Insight" name, logo, or branding in a way that suggests your project is endorsed by or affiliated with the original authors without explicit written permission.
- For commercial use or distribution beyond the terms of the Apache License 2.0, please contact the copyright holders for additional licensing options.
