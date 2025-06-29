# Enhanced Wearable Simulator for Healthcare Monitoring

A comprehensive, configurable simulator for generating synthetic health data from wearable devices, designed for IoT and distributed healthcare systems demonstrations.

## ✨ Key Features

- **Multi-parameter Physiological Simulation**:
  - Heart rate (bpm)
  - Blood pressure (systolic/diastolic)
  - Oxygen saturation (SpO2)
  - Blood glucose levels
  - Physical activity (steps, intensity)
  - Body temperature
  - Respiratory rate
  
- **Advanced Simulation Capabilities**:
  - **Circadian Rhythms**: 24-hour patterns that affect all vital signs
  - **Condition Simulation**: Multiple pre-configured health conditions
  - **Meal Simulation**: Realistic post-prandial glucose responses
  - **Sleep-Wake Cycles**: Simulated sleep patterns affecting vital signs
  - **Activity Simulation**: Realistic movement and exercise patterns
  - **Event-based Anomalies**: Simulate acute medical events

- **Technical Features**:
  - **MQTT 3.1.1/5.0 Support**: Seamless IoT integration
  - **Containerized Deployment**: Docker and Docker Compose ready
  - **High Performance**: Optimized for multiple concurrent instances
  - **Deterministic Output**: Optional seed for reproducible results
  - **Configurable Sampling Rates**: Adjustable from 1 to 60 samples/minute
  - **Noise Injection**: Configurable noise levels for realistic data
  - **TLS/SSL Support**: Secure MQTT communication
  - **Health Check Endpoint**: Container health monitoring

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd wearable-simulator
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. (Optional) Edit the `.env` file to customize settings:
   ```bash
   nano .env
   ```

4. Start the system with Docker Compose:
   ```bash
   docker-compose up -d
   ```

5. Access the MQTT Explorer at http://localhost:4000 to monitor the data

## ⚙️ Configuration

### Environment Variables

#### Core Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `PATIENT_ID` | `patient-1` | Unique patient identifier |
| `DEVICE_ID` | `wearable-1` | Device identifier |
| `SAMPLE_RATE` | `4` | Samples per minute (1-60) |
| `NOISE_LEVEL` | `0.02` | Amount of noise (0-1) |
| `SEED` | - | Random seed for reproducible results |

#### Health Simulation
| Variable | Default | Description |
|----------|---------|-------------|
| `CONDITION` | - | Health condition (see below) |
| `USE_CIRCADIAN_RHYTHMS` | `true` | Enable 24-hour patterns |
| `SIMULATE_MEALS` | `true` | Simulate meal effects |
| `SIMULATE_SLEEP` | `true` | Simulate sleep cycles |
| `SIMULATE_ACTIVITY` | `true` | Simulate activity patterns |
| `MEAL_TIMES` | `7,12,19` | Meal times (24h format) |
| `SLEEP_START_HOUR` | `23` | Sleep start (0-23) |
| `SLEEP_DURATION_HOURS` | `8` | Sleep duration (hours) |
| `ACTIVITY_PEAK_HOURS` | `8,12,18` | Peak activity hours |
| `NUM_PATIENTS` | `1` | Number of patients to simulate |
| `PATIENT_ID_PREFIX` | `patient-` | Prefix for patient IDs |
| `DEVICE_ID_PREFIX` | `wearable-` | Prefix for device IDs |
| `ABNORMAL_PROBABILITY` | `0.1` | Probability of abnormal values (0-1) |
| `CONDITION` | - | Health condition (see below) |

## 📊 Configuring Patients and Devices

### Simulating Multiple Patients

1. **Using a Single Instance**
   - Set `NUM_PATIENTS` to the desired number of patients
   - Each patient will receive a unique ID (e.g., patient-1, patient-2, ...)
   - Each patient will have an associated device (e.g., wearable-1, wearable-2, ...)

   ```bash
   docker-compose up -d --scale wearable-simulator=1 \
     -e NUM_PATIENTS=5 \
     -e PATIENT_ID_PREFIX=pt- \
     -e DEVICE_ID_PREFIX=dev-
   ```

2. **Using Multiple Instances**
   - For more control, run multiple simulator instances
   - Each instance can simulate one or more patients
   - Useful for load distribution or simulating different conditions

   ```yaml
   # docker-compose.override.yml
   services:
     wearable-simulator-1:
       extends: wearable-simulator
       environment:
         - NUM_PATIENTS=3
         - PATIENT_ID_PREFIX=ward-a-
         - CONDITION=hypertension
     
     wearable-simulator-2:
       extends: wearable-simulator
       environment:
         - NUM_PATIENTS=2
         - PATIENT_ID_PREFIX=ward-b-
         - CONDITION=diabetes
   ```

### Advanced Configuration

#### Customizing IDs
- `PATIENT_ID_PREFIX`: Sets the prefix for patient IDs
- `DEVICE_ID_PREFIX`: Sets the prefix for device IDs
- Example: `PT-001`, `PT-002`, ...

#### Controlling Behavior
- `ABNORMAL_PROBABILITY`: Adjusts frequency of abnormal values (0 = never, 1 = always)
- `CONDITION`: Sets a health condition for all patients
- `SAMPLE_RATE`: Samples per minute (increase with caution)

#### Complete Example
```bash
docker-compose up -d --scale wearable-simulator=3 \
  -e NUM_PATIENTS=10 \
  -e PATIENT_ID_PREFIX=pt- \
  -e DEVICE_ID_PREFIX=dev- \
  -e ABNORMAL_PROBABILITY=0.2 \
  -e SAMPLE_RATE=2 \
  -e CONDITION=arrhythmia
```

### Resource Monitoring
When increasing the number of patients, monitor resource usage:

```bash
docker stats $(docker ps --format '{{.Names}}' | grep wearable-simulator)
```

It's recommended to start with a small number of patients and gradually increase while monitoring performance.

#### MQTT Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_BROKER` | `mosquitto` | MQTT broker hostname |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_USERNAME` | - | MQTT username |
| `MQTT_PASSWORD` | - | MQTT password |
| `MQTT_TOPIC` | `wearables/data` | MQTT topic |
| `MQTT_QOS` | `1` | QoS level (0-2) |
| `MQTT_RETAIN` | `false` | Retain messages |
| `MQTT_TLS_ENABLED` | `false` | Enable TLS/SSL |
| `MQTT_TLS_INSECURE` | `false` | Skip certificate validation |

#### Advanced Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `HEART_RATE_BASELINE` | `70` | Baseline heart rate |
| `BLOOD_PRESSURE_SYS` | `120` | Baseline systolic BP |
| `BLOOD_PRESSURE_DIA` | `80` | Baseline diastolic BP |
| `SPO2_BASELINE` | `98` | Baseline SpO2 |
| `GLUCOSE_BASELINE` | `90` | Baseline glucose (mg/dL) |
| `TEMPERATURE_BASELINE` | `36.8` | Baseline temperature (°C) |
| `RESPIRATORY_RATE` | `16` | Breaths per minute |
| `ACTIVITY_LEVEL` | `0.3` | Base activity level (0-1) |

### Simulated Conditions

Configure health conditions using the `CONDITION` environment variable:

| Condition | Description | Key Effects |
|-----------|-------------|-------------|
| `hypertension` | High blood pressure | ↑ BP, ↑ HR variability |
| `hypotension` | Low blood pressure | ↓ BP, ↑ HR |
| `tachycardia` | Fast heart rate | ↑ HR, ↓ HRV |
| `bradycardia` | Slow heart rate | ↓ HR, ↑ HRV |
| `diabetes` | Elevated glucose | ↑ Glucose, ↑ variability |
| `hypoglycemia` | Low blood sugar | ↓ Glucose, ↑ HR, ↑ anxiety |
| `copd` | Respiratory condition | ↓ SpO2, ↑ Respiratory rate |
| `fever` | Elevated temperature | ↑ Temp, ↑ HR |
| `sepsis` | Blood infection | ↑ HR, ↑ Temp, ↓ BP |
| `afib` | Irregular heartbeat | Irregular HR, ↓ HRV |
| `healthy` | Normal parameters | All values in range |
| (none) | Randomized | Varies randomly |

### Message Format

Example MQTT message payload:

```json
{
  "patient_id": "patient-1",
  "device_id": "wearable-1",
  "timestamp": "2023-01-01T12:00:00.000Z",
  "location": {
    "latitude": -23.5505,
    "longitude": -46.6333,
    "altitude": 760
  },
  "vitals": {
    "heart_rate": 75,
    "heart_rate_variability": 45,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "mean_arterial_pressure": 93,
    "oxygen_saturation": 98.5,
    "respiratory_rate": 16,
    "temperature": 36.8,
    "glucose": 95.0
  },
  "activity": {
    "steps": 42,
    "distance": 0.03,
    "calories": 3.2,
    "intensity": 0.15,
    "activity_type": "walking"
  },
  "battery": {
    "level": 85,
    "voltage": 3.8,
    "charging": false
  },
  "metadata": {
    "firmware_version": "1.2.3",
    "signal_strength": -65,
    "condition": "healthy",
    "simulation_timestamp": 1672574400
  }
}
```

### Simulated Conditions

You can simulate various health conditions by setting the `CONDITION` environment variable:

- `hypertension`: Elevated blood pressure
- `hypotension`: Low blood pressure
- `tachycardia`: Elevated heart rate
- `bradycardia`: Low heart rate
- `diabetes`: Elevated glucose levels
- `copd`: Reduced oxygen levels
- (Leave empty for healthy baseline)

## 🏗️ Architecture

The simulator is designed with a modular architecture for flexibility and extensibility:

```mermaid
graph TD
    A[Wearable Simulator] -->|Publishes| B[MQTT Broker]
    B -->|Serves| C[Dashboard/Visualization]
    B -->|Publishes| D[(Data Consumers)]
    D --> E[Data Processor]
    D --> F[Alert Manager]
    D --> G[Storage]
    
    subgraph Simulator Components
    H[Signal Generator] --> I[Condition Modifier]
    I --> J[Circadian Modulator]
    J --> K[Meal Effect Model]
    K --> L[Sleep Model]
    L --> M[Activity Model]
    M --> N[Noise Injector]
    N --> O[MQTT Publisher]
    end
    
    A -->|Uses| Simulator Components
```

### Key Components

1. **Signal Generator**
   - Core physiological signal simulation
   - Multi-parameter correlation
   - Baseline parameter configuration

2. **Condition Modifier**
   - Applies health condition effects
   - Manages condition progression
   - Handles acute events

3. **Circadian Modulator**
   - 24-hour rhythm patterns
   - Parameter-specific variations
   - Seasonal adjustments

4. **Meal Effect Model**
   - Post-prandial glucose response
   - Macronutrient effects
   - Individual variability

5. **Sleep Model**
   - Sleep stage simulation
   - Vital sign variations
   - Sleep quality factors

6. **Activity Model**
   - Physical activity patterns
   - Exercise responses
   - Sedentary behavior

7. **Noise Injector**
   - Realistic sensor noise
   - Artifact simulation
   - Signal dropout handling

8. **MQTT Publisher**
   - Message queuing
   - QoS management
   - Reconnection logic

## 🚀 Getting Started

### Prerequisites

- Python 3.9+ or Docker
- MQTT broker (e.g., Mosquitto, HiveMQ, AWS IoT)
- (Optional) MQTT client for monitoring (MQTT Explorer, MQTT.fx)

### Quick Start with Docker Compose

1. Start a complete test environment:
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```
   This starts:
   - MQTT Broker (Mosquitto)
   - MQTT Explorer (web UI)
   - 5 pre-configured wearable simulators with different conditions

2. Access the MQTT Explorer at http://localhost:4000
   - Connect to `mqtt://localhost:1883`
   - Subscribe to `wearables/#`

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run unit tests
pytest tests/unit

# Run integration tests (requires MQTT broker)
pytest tests/integration

# Generate coverage report
pytest --cov=wearable_simulator --cov-report=html
```

### Running in Development Mode

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

3. Run the simulator:
   ```bash
   python -m wearable_simulator --patient-id demo --condition afib
   ```

### Container Deployment

Build the Docker image:
```bash
docker build -t wearable-simulator .
```

Run a single instance:
```bash
docker run -d \
  --name wearable-1 \
  -e PATIENT_ID=patient-1 \
  -e DEVICE_ID=wearable-1 \
  -e CONDITION=hypertension \
  -e MQTT_BROKER=mosquitto \
  --network iot-network \
  wearable-simulator
```

### Kubernetes Deployment

Example deployment for Kubernetes:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wearable-simulator
  labels:
    app: wearable-simulator
spec:
  replicas: 5
  selector:
    matchLabels:
      app: wearable-simulator
  template:
    metadata:
      labels:
        app: wearable-simulator
    spec:
      containers:
      - name: wearable-simulator
        image: wearable-simulator:latest
        env:
        - name: PATIENT_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: DEVICE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.uid
        - name: MQTT_BROKER
          value: "mqtt-broker"
        - name: CONDITION
          value: "healthy"
        resources:
          limits:
            cpu: "1"
            memory: "128Mi"
          requests:
            cpu: "100m"
            memory: "64Mi"
```

## 📊 Performance

- Single instance uses < 50MB RAM
- Supports 1000+ concurrent simulated devices per host
- Configurable sampling rate (1-60 samples/minute)
- Efficient MQTT message batching

## 🔒 Security

- MQTT over TLS/SSL support
- Authentication via username/password or client certificates
- No sensitive data in logs
- Minimal container privileges

## 📈 Monitoring

The simulator exposes Prometheus metrics at `/metrics`:

- Messages published/s
- Message size distribution
- Error rates
- Resource usage
- Simulation parameters

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Dependencies

- `pytest`: Testing framework
- `black`: Code formatting
- `mypy`: Static type checking
- `flake8`: Linting
- `pytest-cov`: Test coverage
- `pytest-asyncio`: Async test support

## 📚 Resources

- [MQTT Specification](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)
- [InfluxDB Line Protocol](https://docs.influxdata.com/influxdb/v2.0/reference/syntax/line-protocol/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)

## 📚 Medical References

### Implemented Physiological Models

#### 1. Normal Vital Sign Ranges
- **Heart Rate (60-100 bpm)**
  - Based on standard clinical ranges for adults at rest
  - Aligns with American Heart Association guidelines for normal sinus rhythm

- **Blood Pressure**
  - Systolic: 100-140 mmHg
  - Diastolic: 60-90 mmHg
  - Follows standard clinical definitions of normal and pre-hypertensive ranges

- **Oxygen Saturation (95-100%)**
  - Represents normal SpO2 levels for healthy individuals at sea level

- **Blood Glucose (70-120 mg/dL)**
  - Covers normal fasting and postprandial ranges for non-diabetic adults

#### 2. Condition-Specific Adjustments
Implemented as simple percentage-based modifications to baseline values:

- **Tachycardia/Bradycardia**
  - 30% increase/decrease from normal heart rate range

- **Hypertension/Hypotension**
  - 20% increase for hypertension
  - 15% decrease for hypotension
  - Applied uniformly to systolic and diastolic pressures

- **Glucose Abnormalities**
  - Hyperglycemia: 50% increase from baseline
  - Hypoglycemia: 30% decrease from baseline

#### 3. Circadian Rhythms
- Basic 24-hour pattern with:
  - Day/night variations in heart rate and blood pressure
  - Morning surge in blood pressure
  - Reduced activity and vital signs during sleep hours

## 🏥 Medical Assumptions and Premises

### 1. Physiological Foundations

#### Respected Medical Principles
- **Circadian Rhythms**
  - Follows the natural 24-hour cycle for vital signs
  - Implements the expected dip in blood pressure during sleep (nocturnal dipping)
  - Simulates the morning surge in blood pressure

- **Vital Sign Relationships**
  - Maintains the physiological relationship between heart rate and blood pressure
  - Simulates the expected increase in respiratory rate with activity
  - Models the basic oxygen saturation curve (SpO2) in relation to respiratory function

- **Response to Activity**
  - Implements the expected heart rate increase with activity
  - Simulates the return to baseline during recovery periods

### 2. Simulation Premises

#### Simplified Models
- **Linear Responses**
  - Uses fixed percentage changes for conditions (e.g., +30% for tachycardia)
  - Assumes linear relationships between physiological parameters

- **Independent Systems**
  - Models each vital sign independently
  - Does not fully simulate complex feedback loops between systems

- **Fixed Baselines**
  - Uses population averages as starting points
  - Limited adaptation to individual baseline variations

#### Time Considerations
- **Sampling Rate**
  - Assumes that sampling every 15 seconds is sufficient for trend detection
  - Does not model high-frequency physiological variations

- **Response Times**
  - Implements immediate effects of conditions
  - Simplifies the time course of physiological responses

### 3. Clinical Scenarios

#### Realistic Patterns
- **Meal Effects**
  - Simulates postprandial glucose elevation
  - Models the typical timing of glucose peaks after meals

- **Sleep-Wake Cycle**
  - Implements expected nocturnal dip in blood pressure and heart rate
  - Models reduced activity levels during sleep hours

#### Simplified Pathology
- **Condition Modeling**
  - Represents conditions through isolated parameter adjustments
  - Does not simulate the full pathophysiology of diseases

- **Comorbidity Limitation**
  - Models single conditions at a time
  - Limited ability to simulate interactions between multiple conditions

### Important Limitations

These medical assumptions represent simplifications necessary for a general-purpose simulation. Actual clinical conditions may exhibit more complex behaviors and individual variations.

1. **Simplified Models**
   - Physiological responses are linear approximations
   - No complex interactions between different physiological systems
   - Fixed percentage adjustments don't capture individual variability

2. **Not Clinically Validated**
   - These models are for demonstration purposes only
   - Not intended for clinical decision-making
   - Lack validation against real patient data

3. **Missing Complexities**
   - No accounting for:
     - Age-related changes
     - Comorbid conditions
     - Medication effects
     - Individual physiological variations

For educational and demonstration purposes only. Not for clinical use.

## 🚀 Future Enhancement Recommendations

### 1. Physiological Correlations
- **Interdependent Vital Signs**: Implement realistic correlations between heart rate, blood pressure, and respiratory rate
- **Context-Aware Simulation**: Adjust vital sign relationships based on activity state (rest, exercise, sleep)
- **Delayed Responses**: Model physiological response delays (e.g., blood pressure changes after heart rate changes)

### 2. Advanced Simulation Models
- **Individual Baselines**: Learn and adapt to individual patient baselines over time
- **Multi-Organ System Modeling**: Simulate interactions between different physiological systems
- **Condition Progression**: Model disease progression and recovery trajectories

### 3. Enhanced Realism
- **Signal Artifacts**: Add realistic sensor noise and motion artifacts
- **Missing Data**: Simulate temporary sensor disconnections or signal loss
- **Device-Specific Characteristics**: Model differences between various wearable device models

### 4. Integration & Interoperability
- **HL7/FHIR Support**: Export data in standard healthcare formats
- **EHR Integration**: Simulate integration with Electronic Health Record systems
- **Standard Protocols**: Support for additional IoT protocols beyond MQTT

### 5. Clinical Scenarios
- **Emergency Situations**: Simulate acute medical events with coordinated vital sign changes
- **Treatment Response**: Model vital sign responses to common treatments
- **Risk Stratification**: Generate data for different risk categories

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Implements simplified models inspired by real-world healthcare monitoring systems and clinical guidelines
- Uses the Eclipse Mosquitto MQTT broker
- Built with Python, FastAPI, and Docker
- Special thanks to the open-source community for valuable tools and libraries

## 📬 Contact

For questions, suggestions, or support, please [open an issue](https://github.com/yourusername/wearable-simulator/issues) or contact the maintainers.

---

<div align="center">
  <p>Made with ❤️ for better healthcare technology</p>
  <img src="https://img.shields.io/badge/status-active-success.svg" alt="Status">
  <img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/docker/pulls/yourusername/wearable-simulator" alt="Docker Pulls">
</div>


## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.

### Additional Terms and Conditions

- The "SmartCare Insight" name and logo are trademarks of the original author(s).
- You may not use the "SmartCare Insight" name, logo, or branding in a way that suggests your project is endorsed by or affiliated with the original authors without explicit written permission.
- For commercial use or distribution beyond the terms of the Apache License 2.0, please contact the copyright holders for additional licensing options.
