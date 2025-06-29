# API Server

The API Server provides a RESTful interface for accessing and managing patient health data, alerts, and system configuration.

## Features

- **RESTful API**: JSON-based API following REST principles
- **Authentication**: JWT-based authentication and authorization
- **Documentation**: Interactive API documentation with Swagger UI and ReDoc
- **Data Access**: Query patient data with filtering and pagination
- **Alert Management**: View and manage health alerts
- **System Configuration**: Manage system settings and parameters

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Authentication

All API endpoints (except `/auth/token`) require authentication using a JWT token.

### Getting an Access Token

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Access Token

Include the token in the `Authorization` header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## API Endpoints

### Patients

- `GET /api/patients` - List all patients
- `GET /api/patients/{patient_id}` - Get patient details
- `GET /api/patients/{patient_id}/measurements` - Get patient measurements
- `GET /api/patients/{patient_id}/alerts` - Get patient alerts

### Alerts

- `GET /api/alerts` - List all alerts
- `GET /api/alerts/{alert_id}` - Get alert details
- `PATCH /api/alerts/{alert_id}/acknowledge` - Acknowledge an alert
- `GET /api/alerts/stats` - Get alert statistics

### Data

- `GET /api/data/measurements` - Query measurements
- `GET /api/data/measurements/latest` - Get latest measurements
- `GET /api/data/trends` - Get trends data

### System

- `GET /system/health` - System health status
- `GET /system/version` - Get system version
- `GET /system/config` - Get system configuration

## Data Models

### Patient
```json
{
  "id": "patient-1",
  "name": "John Doe",
  "date_of_birth": "1980-01-01",
  "gender": "male",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Measurement
```json
{
  "patient_id": "patient-1",
  "timestamp": "2023-01-01T12:00:00Z",
  "heart_rate": 75,
  "systolic_bp": 120,
  "diastolic_bp": 80,
  "oxygen_saturation": 98.5,
  "glucose": 95.0,
  "activity": 15.2
}
```

### Alert
```json
{
  "id": "alert-123",
  "patient_id": "patient-1",
  "type": "high_heart_rate",
  "severity": "warning",
  "message": "Elevated heart rate detected: 105 bpm",
  "value": 105,
  "threshold": 100,
  "timestamp": "2023-01-01T12:00:00Z",
  "status": "active",
  "acknowledged_at": null,
  "acknowledged_by": null,
  "notes": null
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
| `JWT_SECRET_KEY` | Secret key for JWT token generation | - | Yes |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` | No |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `30` | No |
| `API_PREFIX` | API URL prefix | `/api` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` | No |
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
   INFLUXDB_URL=http://localhost:8086
   INFLUXDB_TOKEN=your_influxdb_token
   JWT_SECRET_KEY=your_jwt_secret
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

## Architecture

The API Server is built with FastAPI and follows a clean architecture with:

- **Routes**: Define API endpoints and handle HTTP requests
- **Services**: Implement business logic
- **Repositories**: Handle data access
- **Models**: Define data structures and validation
- **Dependencies**: Handle dependency injection
- **Utils**: Utility functions and helpers

## Security

- JWT-based authentication
- Secure password hashing
- CORS protection
- Input validation
- Rate limiting
- HTTPS support

## Performance

- Asynchronous request handling
- Connection pooling for database access
- Response caching
- Query optimization

## Dependencies

- FastAPI
- Uvicorn
- Pydantic
- Python-jose (JWT)
- Passlib (password hashing)
- Python-multipart (file uploads)
- InfluxDB Client
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
