# SmartCare Insight - User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [System Requirements](#system-requirements)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Getting Started](#getting-started)
7. [Using the Dashboard](#using-the-dashboard)
8. [API Documentation](#api-documentation)
9. [Troubleshooting](#troubleshooting)
10. [FAQs](#faqs)

## Introduction

Welcome to the SmartCare Insight! This guide will help you set up, configure, and use the system to monitor patient health data in real-time using simulated wearable devices.

## System Architecture

SmartCare Insight is composed of the following main services:

- **Web Dashboard** (Port 8501) - User interface for monitoring
- **API Server** (Port 8000) - Application backend
- **InfluxDB** (Port 8086) - Time-series database
- **Mosquitto MQTT** (Port 1883) - Real-time message broker
- **Wearable Simulator** - Generates simulated patient data
- **Data Processor** - Processes real-time data streams
- **Alert Manager** - Generates alerts based on rules
- **LLM Service** - Provides AI-powered analysis

## System Requirements

- **Docker**: 20.10 ou superior
- **Docker Compose**: 2.0 ou superior
- **Espaço em Disco**: Mínimo de 2GB
- **Memória RAM**: Mínimo 4GB (8GB recomendado)
- **Sistema Operacional**: Linux, macOS ou Windows 10/11 com WSL2
- **Conexão com a Internet**: Necessária para o serviço de IA (OpenAI)

## Installation

### Prerequisites

1. Install [Docker](https://docs.docker.com/get-docker/) (version 20.10 or higher)
2. Install [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0 or higher)
3. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Internet_of_Things.git
   cd Internet_of_Things
   ```

### Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Start the system:
   ```bash
   docker-compose up -d
   ```

4. Access the following services:
   - Web Dashboard: http://localhost:8501
   - API Documentation: http://localhost:8000/docs
   - InfluxDB UI: http://localhost:8086 (username: admin, password: healthcarepassword)

## Configuration

For detailed configuration options, please refer to the [Configuration Guide](./CONFIGURATION.md).

### Quick Configuration

1. Copy and edit the environment file:
   ```bash
   cp .env.example .env
   nano .env  # or your preferred editor
   ```

2. Key settings to adjust:

   ```env
   # Number of patients to simulate (default: 5)
   NUM_PATIENTS=5
   
   # Simulation interval in seconds (default: 5)
   SIMULATION_INTERVAL=5
   
   # MQTT Settings
   MQTT_BROKER=mosquitto
   MQTT_PORT=1883
   MQTT_TOPIC=wearables/data
   
   # InfluxDB Settings
   INFLUXDB_URL=http://influxdb:8086
   INFLUXDB_TOKEN=healthcareadmintoken
   
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Alert Settings
   ALERT_MANAGER_PORT=8000
   NOTIFICATION_ENABLED=false
   ```

### Device Simulator

Advanced configuration options:

```env
# Probability of abnormal readings (0.0 to 1.0)
ABNORMAL_PROBABILITY=0.1

# Base medical condition for simulation
CONDITION=hypertension

# Meal times (in hours, 24h format)
MEAL_TIMES=7,12,19

# Sleep schedule
SLEEP_START_HOUR=23
SLEEP_DURATION_HOURS=8

# Data sampling rate
SAMPLE_RATE=4

# Batch processing (disabled by default)
BATCH_MODE=false
# BATCH_SIZE=1000
# BACKFILL_HOURS=24
```

## Getting Started

### Accessing the Dashboard

1. Open your web browser and navigate to http://localhost:8501
2. The main dashboard will display an overview of all patients and system status

### Key Features

- **Real-time Monitoring**: View live data from all connected wearables
- **Patient Details**: Click on a patient to see detailed metrics and history
- **Alerts**: View and manage health alerts
- **LLM Analysis**: Get AI-powered insights about patient data
- **Settings**: Configure system parameters and preferences

## Using the Dashboard

### Main Dashboard

The main dashboard provides an overview of:
- Number of active patients
- System status
- Recent alerts
- Quick access to patient details

### Patient Monitoring

1. Click on a patient card to view detailed metrics
2. Use the time range selector to view historical data
3. Toggle between different vital signs using the sidebar

### Alert Management

1. View all active alerts in the Alerts section
2. Acknowledge alerts by clicking the checkmark
3. Filter alerts by severity or patient

### LLM Analysis

1. Navigate to the LLM Analysis page
2. Select a patient and time range
3. Choose an analysis type (Time Window, Event-based, Comparative)
4. Click "Generate Analysis" to get AI-powered insights

## API Documentation

The system provides a RESTful API for programmatic access. Interactive documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Authentication

All API requests require JWT authentication. To authenticate:

1. Obtain an access token:
   ```bash
   curl -X 'POST' \
     'http://localhost:8000/api/auth/token' \
     -H 'accept: application/json' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'grant_type=password&username=admin&password=admin&scope='
   ```

2. Use the token in subsequent requests:
   ```
   Authorization: Bearer <your_token>
   ```

### Main Endpoints

- `GET /api/patients` - List all patients
- `GET /api/patients/{patient_id}/vitals` - Get patient vitals
- `GET /api/alerts` - List alerts
- `POST /api/analysis` - Request AI analysis
- `GET /api/health` - Check system health
- `GET /api/metrics` - Get system metrics
- `POST /api/analysis` - Solicita análise de dados
- `GET /api/system/health` - Verifica a saúde do sistema

## Solução de Problemas

### Problemas Comuns

1. **Falha ao iniciar o Docker Compose**
   - Verifique se o Docker está em execução
   - Confira o espaço em disco disponível
   - Verifique se as portas 8002, 8501, 1883, 8086 não estão em uso

2. **Sem dados no Dashboard**
   - Verifique se o simulador está em execução
   - Confira a conexão com o MQTT broker
   - Verifique os logs do InfluxDB
   - Confira se o serviço API está acessível

3. **Falha na Análise de IA**
   - Verifique se a chave da API da OpenAI está correta
   - Confira a conexão com a internet
   - Verifique se há créditos suficientes na API

### Visualização de Logs

Verifique os logs de todos os serviços:
```bash
docker-compose logs -f
```

Logs de serviços específicos:
```bash
# API Server
docker-compose logs -f api-server

# Dashboard
docker-compose logs -f dashboard

# Wearable Simulator
docker-compose logs -f wearable-simulator

# InfluxDB
docker-compose logs -f influxdb

# Mosquitto MQTT
docker-compose logs -f mosquitto
```

### Reiniciando Serviços

Para reiniciar um serviço específico:
```bash
docker-compose restart <nome_do_servico>
```

Exemplo:
```bash
docker-compose restart api-server
```

## Perguntas Frequentes

### Como adicionar mais pacientes?

1. Pare o simulador:
   ```bash
   docker-compose stop wearable-simulator
   ```

2. Atualize a variável `NUM_PATIENTS` no arquivo `.env`

3. Reinicie o simulador:
   ```bash
   docker-compose up -d wearable-simulator
   ```

### Como acessar o banco de dados diretamente?

1. Acesse o container do InfluxDB:
   ```bash
   docker exec -it influxdb influx -precision rfc3339
   ```

2. Comandos úteis:
   ```sql
   -- Listar bancos de dados
   SHOW DATABASES
   
   -- Usar banco de dados
   USE health_metrics
   
   -- Listar medições
   SHOW MEASUREMENTS
   
   -- Consultar dados
   SELECT * FROM vital_signs LIMIT 5
   ```

### Como personalizar os dados simulados?

Edite o arquivo `src/wearable-simulator/patient_profiles.py` para modificar:
- Perfis de pacientes
- Condições médicas
- Padrões de sinais vitais
- Comportamentos de sono e refeições

### Como fazer backup dos dados?

1. Crie um backup do volume do InfluxDB:
   ```bash
   docker run --rm -v influxdb_data:/volume -v $(pwd):/backup alpine tar -cjf /backup/influxdb_backup_$(date +%Y%m%d).tar.bz2 -C /volume ./
   ```

2. Para restaurar:
   ```bash
   docker run --rm -v influxdb_data:/volume -v $(pwd):/backup alpine sh -c "rm -rf /volume/* && tar -xjf /backup/influxdb_backup_YYYYMMDD.tar.bz2 -C /volume"
   ```
### Configuring Patients and Devices

#### Option 1: Using Environment Variables

1. **Number of Patients**
   - Edit the `docker-compose.yml` file
   - Locate the `wearable-simulator` service
   - Update the `NUM_PATIENTS` variable:
     ```yaml
     environment:
       - NUM_PATIENTS=5  # Number of patients to simulate
     ```

2. **Restart the service**
   ```bash
   docker-compose up -d --force-recreate wearable-simulator
   ```

#### Option 2: Using Command Line

```bash
docker-compose up -d --scale wearable-simulator=3 \
  -e NUM_PATIENTS=10 \
  -e PATIENT_ID_PREFIX=pt- \
  -e DEVICE_ID_PREFIX=dev-
```

#### Advanced Configuration

1. **Customizing IDs**
   - `PATIENT_ID_PREFIX`: Sets the prefix for patient IDs
   - `DEVICE_ID_PREFIX`: Sets the prefix for device IDs
   - Example: `PT-001`, `PT-002`, ...

2. **Simulating Different Conditions**
   - Use the `CONDITION` variable to simulate different health conditions
   - Example: `hypertension`, `diabetes`, `arrhythmia`

3. **Resource Monitoring**
   ```bash
   # Check resource usage
   docker stats $(docker ps --format '{{.Names}}' | grep wearable-simulator)
   ```

4. **Performance Tips**
   - Start with a small number of patients and gradually increase
   - Monitor CPU and memory usage
   - Consider distributing load across multiple instances

### How do I change the simulation parameters?
Edit the environment variables in `docker-compose.yml` under the `wearable-simulator` service.

### How do I back up the data?
The data is stored in Docker volumes. To back up:
```bash
docker-compose down
tar -czvf healthcare_data_backup.tar.gz $(docker volume ls -q | grep smarthealthcare_)
```

### How do I update to the latest version?
```bash
git pull origin main
docker-compose down
docker-compose pull
docker-compose up -d
```

### How do I reset the system?
```bash
docker-compose down -v
```
This will remove all data. Use with caution!

---

For additional support, please open an issue in the repository or contact the maintainers.
