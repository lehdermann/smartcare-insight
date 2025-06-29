# Configuration Guide

This document provides comprehensive guidance on configuring the SmartCare Insight.

## Table of Contents
- [Environment Variables](#environment-variables)
  - [Core Services](#core-services)
  - [Wearable Simulator](#wearable-simulator)
  - [MQTT Broker](#mqtt-broker)
  - [InfluxDB](#influxdb)
  - [API Server](#api-server)
- [Configuration Files](#configuration-files)
- [Per-Environment Setup](#per-environment-setup)
  - [Development](#development)
  - [Production](#production)
  - [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Environment Variables

### Core Services

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Runtime environment | `development` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Wearable Simulator

| Variable | Description | Default |
|----------|-------------|---------|
| `NUM_PATIENTS` | Number of patients to simulate | `5` |
| `SIMULATION_INTERVAL` | Data generation interval (seconds) | `5` |
| `ABNORMAL_PROBABILITY` | Chance of generating abnormal values | `0.1` |
| `CONDITION` | Default condition to simulate | `hypertension` |
| `USE_CIRCADIAN_RHYTHMS` | Enable daily patterns | `true` |
| `SIMULATE_MEALS` | Simulate meal effects | `true` |
| `SIMULATE_SLEEP` | Simulate sleep cycles | `true` |
| `MEAL_TIMES` | Hours for meal simulation | `7,12,19` |
| `SLEEP_START_HOUR` | Sleep start hour | `23` |
| `SLEEP_DURATION_HOURS` | Sleep duration | `8` |
| `SAMPLE_RATE` | Data sampling rate | `4` |
| `PATIENT_ID` | Default patient ID | `patient-1` |
| `DEVICE_ID` | Default device ID | `wearable-1` |
| `BATCH_MODE` | Enable batch processing | `false` |
| `BATCH_SIZE` | Number of records per batch | `1000` |
| `BACKFILL_HOURS` | Hours of historical data to backfill | `24` |

### MQTT Broker

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_BROKER` | Broker hostname | `mosquitto` |
| `MQTT_PORT` | MQTT port | `1883` |
| `MQTT_WEBSOCKET_PORT` | WebSocket port | `9001` |
| `MQTT_WEBSOCKET_ALT_PORT` | Alternative WebSocket port | `9003` |
| `MQTT_USERNAME` | Authentication username | `healthcare` |
| `MQTT_PASSWORD` | Authentication password | - |
| `MQTT_TOPIC` | Default MQTT topic | `wearables/data` |

### InfluxDB

| Variable | Description | Default |
|----------|-------------|---------|
| `INFLUXDB_URL` | Connection URL | `http://influxdb:8086` |
| `INFLUXDB_TOKEN` | Authentication token | - |
| `INFLUXDB_ORG` | Organization | `healthcare` |
| `INFLUXDB_BUCKET` | Bucket name | `health_metrics` |
| `INFLUXDB_RETENTION` | Data retention policy | `30d` |
| `DOCKER_INFLUXDB_INIT_MODE` | Initialization mode | `setup` |
| `DOCKER_INFLUXDB_INIT_USERNAME` | Admin username | `admin` |
| `DOCKER_INFLUXDB_INIT_PASSWORD` | Admin password | - |
| `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN` | Admin token | - |

### API Server

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | Bind address | `0.0.0.0` |
| `API_PORT` | HTTP port | `8000` |
| `JWT_SECRET_KEY` | Secret for JWT tokens | - |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |
| `CORS_ORIGINS` | Allowed origins | `*` |

### Alert Manager

| Variable | Description | Default |
|----------|-------------|---------|
| `ALERT_MANAGER_PORT` | HTTP port | `8000` |
| `ALERT_THRESHOLDS` | JSON string with alert thresholds | - |
| `NOTIFICATION_ENABLED` | Enable notifications | `false` |
| `SMTP_SERVER` | SMTP server for email alerts | - |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username | - |
| `SMTP_PASSWORD` | SMTP password | - |
| `ALERT_EMAILS` | Comma-separated recipient emails | - |

### LLM Service

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `LLM_MODEL` | Model to use | `gpt-4` |
| `LLM_TEMPERATURE` | Response randomness | `0.7` |
| `LLM_MAX_TOKENS` | Max response length | `1000` |

## Configuration Files

### .env

```env
# Core
ENVIRONMENT=development
LOG_LEVEL=INFO

# Wearable Simulator
NUM_PATIENTS=5
SIMULATION_INTERVAL=5
ABNORMAL_PROBABILITY=0.1
CONDITION=hypertension
SAMPLE_RATE=4
USE_CIRCADIAN_RHYTHMS=true
SIMULATE_MEALS=true
SIMULATE_SLEEP=true
MEAL_TIMES=7,12,19
SLEEP_START_HOUR=23
SLEEP_DURATION_HOURS=8
PATIENT_ID=patient-1
DEVICE_ID=wearable-1
BATCH_MODE=false
# BATCH_SIZE=1000
# BACKFILL_HOURS=24

# MQTT
MQTT_BROKER=mosquitto
MQTT_PORT=1883
MQTT_WEBSOCKET_PORT=9001
MQTT_WEBSOCKET_ALT_PORT=9003
MQTT_USERNAME=healthcare
MQTT_PASSWORD=healthcarepassword
MQTT_TOPIC=wearables/data

# InfluxDB
INFLUXDB_URL=http://influxdb:8086
DOCKER_INFLUXDB_INIT_MODE=setup
DOCKER_INFLUXDB_INIT_USERNAME=admin
DOCKER_INFLUXDB_INIT_PASSWORD=healthcarepassword
DOCKER_INFLUXDB_INIT_ORG=healthcare
DOCKER_INFLUXDB_INIT_BUCKET=health_metrics
DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=healthcareadmintoken
INFLUXDB_TOKEN=healthcareadmintoken
INFLUXDB_ORG=healthcare
INFLUXDB_BUCKET=health_metrics
INFLUXDB_RETENTION=30d

# API
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET_KEY=secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=*

# LLM
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000
```

## Per-Environment Setup

### Development

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your settings

3. Start the development stack:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

### Production

1. Create a production environment file:
   ```bash
   cp .env.example .env.prod
   ```

2. Update `.env.prod` with production values:
   - Set `ENVIRONMENT=production`
   - Use strong passwords and secrets
   - Configure proper CORS_ORIGINS
   - Set appropriate retention policies

3. Start the production stack:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Testing

1. Create a test environment file:
   ```bash
   cp .env.example .env.test
   ```

2. Update `.env.test` for testing:
   ```
   ENVIRONMENT=test
   NUM_PATIENTS=2
   SIMULATION_INTERVAL=1
   ```

3. Run tests:
   ```bash
   docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
   ```

## Data Processor

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INFLUXDB_URL` | InfluxDB connection URL | `http://influxdb:8086` |
| `INFLUXDB_TOKEN` | InfluxDB authentication token | - |
| `INFLUXDB_ORG` | InfluxDB organization | `healthcare` |
| `INFLUXDB_BUCKET` | InfluxDB bucket name | `health_metrics` |
| `MQTT_BROKER` | MQTT broker hostname | `mosquitto` |
| `MQTT_PORT` | MQTT broker port | `1883` |
| `MQTT_USER` | MQTT username | `healthcare` |
| `MQTT_PASSWORD` | MQTT password | - |
| `MQTT_TOPIC` | MQTT topic to subscribe | `wearables/data` |

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Ensure all required variables are set in your `.env` file
   - Check for typos in variable names

2. **Connection Issues**
   - Verify all services are running: `docker-compose ps`
   - Check service logs: `docker-compose logs <service_name>`

3. **Permission Denied**
   - Ensure proper file permissions on `.env` files
   - Check volume mounts in docker-compose files

4. **InfluxDB Setup**
   - First run may require manual setup:
     ```bash
     docker-compose exec influxdb influx setup \
       --org healthcare \
       --bucket health_metrics \
       --username admin \
       --password your_secure_password \
       --token your_secure_token \
       --force
     ```

### Viewing Logs

View logs for all services:
```bash
docker-compose logs -f
```

View logs for a specific service:
```bash
docker-compose logs -f <service_name>
```

### Environment Variable Precedence

1. Variables set in `docker-compose.override.yml`
2. Variables in `.env` file
3. Default values in `docker-compose.yml`
4. System environment variables

### Updating Configuration

After changing configuration:
1. Update the relevant `.env` file
2. Recreate the affected services:
   ```bash
   docker-compose up -d --no-deps <service_name>
   ```
