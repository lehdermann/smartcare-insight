# Data Processor Service

The Data Processor is a critical component that receives, processes, validates, and stores health metrics from wearable devices in real-time.

## Features

- **MQTT Subscriber**: Listens for incoming health data from wearables
- **Data Validation**: Ensures data quality and consistency
- **Data Enrichment**: Adds metadata and timestamps
- **Time-series Storage**: Stores data in InfluxDB
- **Real-time Processing**: Processes data with minimal latency
- **Error Handling**: Robust error handling and retry mechanisms

## Data Flow

1. Receives JSON messages from MQTT broker
2. Validates message structure and content
3. Enriches data with metadata
4. Transforms data into InfluxDB line protocol format
5. Writes data to InfluxDB
6. Publishes processed data to MQTT for other services

## Message Format

### Input (MQTT Message)

```json
{
  "patient_id": "patient-1",
  "device_id": "wearable-1",
  "timestamp": "2023-01-01T12:00:00Z",
  "measurements": {
    "heart_rate": 75,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "oxygen_saturation": 98.5,
    "glucose": 95.0,
    "activity": 15.2
  },
  "metadata": {
    "battery_level": 85,
    "firmware_version": "1.2.3"
  }
}
```

### Output (InfluxDB Line Protocol)

```
health_metrics,patient_id=patient-1,device_id=wearable-1 heart_rate=75i,systolic_bp=120i,diastolic_bp=80i,oxygen_saturation=98.5,glucose=95.0,activity=15.2,battery_level=85i 1672574400000000000
```

## API Endpoints

### `GET /health`

Check service health.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2023-01-01T12:00:00Z",
  "processed_messages": 12345,
  "last_processed": "2023-01-01T11:59:58Z"
}
```

### `GET /metrics`

Get processing metrics in Prometheus format.

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MQTT_BROKER` | MQTT broker hostname | `mosquitto` | No |
| `MQTT_PORT` | MQTT broker port | `1883` | No |
| `MQTT_USER` | MQTT username | - | No |
| `MQTT_PASSWORD` | MQTT password | - | No |
| `MQTT_TOPIC` | MQTT topic to subscribe to | `wearables/data` | No |
| `INFLUXDB_URL` | InfluxDB connection URL | `http://influxdb:8086` | Yes |
| `INFLUXDB_TOKEN` | InfluxDB authentication token | - | Yes |
| `INFLUXDB_ORG` | InfluxDB organization | `healthcare` | No |
| `INFLUXDB_BUCKET` | InfluxDB bucket name | `health_metrics` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

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
   MQTT_BROKER=localhost
   INFLUXDB_URL=http://localhost:8086
   INFLUXDB_TOKEN=your_influxdb_token
   ```

### Running Locally

```bash
python main.py
```

### Testing

Run tests:
```bash
pytest tests/
```

## Architecture

The Data Processor consists of the following components:

- **MQTT Client**: Subscribes to MQTT topics and receives messages
- **Message Validator**: Validates incoming messages
- **Data Transformer**: Converts messages to InfluxDB line protocol
- **InfluxDB Client**: Writes data to InfluxDB
- **Metrics Collector**: Tracks processing metrics
- **Health Check**: Provides health status endpoint

## Performance Considerations

- Uses asynchronous I/O for high throughput
- Batches writes to InfluxDB for better performance
- Implements backpressure handling
- Includes rate limiting and retry logic

## Security

- MQTT connection can be secured with TLS and authentication
- Sensitive configuration is passed via environment variables
- Input validation prevents injection attacks

## Monitoring

- Prometheus metrics endpoint at `/metrics`
- Structured logging in JSON format
- Health check endpoint at `/health`

## Dependencies

- Paho MQTT Client
- InfluxDB Client
- Pydantic
- python-dotenv
- prometheus-client
- pytest (for testing)

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.


## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.

### Additional Terms and Conditions

- The "SmartCare Insight" name and logo are trademarks of the original author(s).
- You may not use the "SmartCare Insight" name, logo, or branding in a way that suggests your project is endorsed by or affiliated with the original authors without explicit written permission.
- For commercial use or distribution beyond the terms of the Apache License 2.0, please contact the copyright holders for additional licensing options.
