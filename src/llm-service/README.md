# LLM Service

The LLM (Large Language Model) Service provides AI-powered analysis of patient health data. It integrates with OpenAI's API to generate insights, detect anomalies, and provide recommendations based on patient vital signs.

## Features

- **Multiple Analysis Types**:
  - Time Window Analysis
  - Event-based Analysis
  - Comparative Analysis
  - Trend Analysis
- **Mock Responses**: Fallback when API key is not available
- **Asynchronous Processing**: Non-blocking API endpoints
- **Extensible Provider Pattern**: Easy to add new LLM providers

## API Endpoints

### `POST /analyze`

Perform analysis on patient data.

**Request Body (AnalysisRequest):**
```json
{
  "analysis_type": "time_window",
  "patient_id": "patient-1",
  "start_time": "2023-01-01T00:00:00Z",
  "end_time": "2023-01-01T23:59:59Z",
  "measurement_types": ["hr", "bp_sys", "bp_dia"]
}
```

**Response (AnalysisResponse):**
```json
{
  "patient_id": "patient-1",
  "analysis_type": "time_window",
  "timestamp": "2023-01-01T12:00:00Z",
  "summary": "Patient shows normal vital signs with occasional spikes...",
  "insights": [
    {
      "text": "Elevated heart rate detected during afternoon hours",
      "confidence": 0.92,
      "related_measurements": ["hr"]
    }
  ],
  "recommendations": [
    {
      "text": "Consider reviewing patient's activity levels in the afternoon",
      "priority": 2,
      "rationale": "Consistent elevation in heart rate may indicate increased activity or stress"
    }
  ],
  "data_points_analyzed": 1440,
  "time_period": "2023-01-01T00:00:00Z to 2023-01-01T23:59:59Z"
}
```

### `GET /health`

Check service health.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2023-01-01T12:00:00Z",
  "provider": "OpenAI"
}
```

## Configuration

Environment Variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `OPENAI_MODEL` | Model to use | `gpt-4` | No |
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

3. Set environment variables:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
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

The service follows a clean architecture with the following components:

- **main.py**: FastAPI application and route handlers
- **models.py**: Pydantic models for request/response validation
- **providers.py**: Abstract base class and implementations for different LLM providers

## Error Handling

The service provides detailed error responses with appropriate HTTP status codes. Common errors include:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid API key
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side error

## Performance Considerations

- Responses are cached for 5 minutes to reduce API calls
- Requests are processed asynchronously to handle high concurrency
- Rate limiting is applied to prevent abuse

## Security

- All API endpoints require authentication
- Sensitive data is never logged
- API keys are stored securely and never exposed in responses

## Dependencies

- FastAPI
- Pydantic
- OpenAI Python client
- python-dotenv
- uvicorn

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.


## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.

### Additional Terms and Conditions

- The "SmartCare Insight" name and logo are trademarks of the original author(s).
- You may not use the "SmartCare Insight" name, logo, or branding in a way that suggests your project is endorsed by or affiliated with the original authors without explicit written permission.
- For commercial use or distribution beyond the terms of the Apache License 2.0, please contact the copyright holders for additional licensing options.
