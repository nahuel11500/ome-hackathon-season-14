# API Gateway Documentation

## Overview

This FastAPI gateway orchestrates multi-model analysis for French TV ecological content. It follows a microservices architecture where the gateway coordinates calls to independent model services and stores enriched results in PostgreSQL.

## Architecture

```
Frontend → API Gateway (port 8000) → Model Microservices
                ↓
          PostgreSQL Database
```

### Pipeline Flow

1. **Deduplication**: Remove repetitive text loops from input
2. **NER**: Extract actors (persons, organizations, locations, misc entities)
3. **Sentiment Analysis**: Classify sentiment (positive/negative/neutral)
4. **Storage**: Store enriched results in PostgreSQL

### Services

- **API Gateway** (`api-gateway`): Main orchestration service on port 8000
- **Sentiment Service** (`sentiment-service`): French sentiment analysis microservice on port 8001
- **NER Service** (`ner-service`): Named Entity Recognition microservice on port 8002
- **PostgreSQL**: Database for storing enriched analysis results

## Getting Started

### Start all services

```bash
docker compose up --build api-gateway sentiment-service ner-service postgres
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Root Information
```bash
GET http://localhost:8000/
```

Returns available endpoints and service information.

### 2. Health Check
```bash
GET http://localhost:8000/health
```

Returns health status of the gateway, database, and all downstream model services.

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "services": [
    {
      "name": "sentiment",
      "status": "healthy",
      "url": "http://sentiment-service:8001"
    }
  ]
}
```

### 3. Analyze Single Segment
```bash
POST http://localhost:8000/analyze
Content-Type: application/json

{
  "segment_id": "12345",
  "channel_title": "France 2",
  "channel_name": "france2",
  "segment_start": "2024-01-15T20:00:00",
  "segment_end": "2024-01-15T20:05:00",
  "duration_seconds": "300",
  "report_text": "Un reportage sur l'agriculture durable en France.",
  "llm_category": "agriculture_alimentation"
}
```

**Response:**
```json
{
  "id": "hash_id_12345_france2",
  "segment_id": "12345",
  "sentiment": "positive",
  "sentiment_confidence": 0.95,
  "status": "success"
}
```

### 4. Batch Analysis
```bash
POST http://localhost:8000/analyze/batch
Content-Type: application/json

{
  "segments": [
    {
      "segment_id": "12345",
      "channel_title": "France 2",
      "channel_name": "france2",
      "segment_start": "2024-01-15T20:00:00",
      "segment_end": "2024-01-15T20:05:00",
      "duration_seconds": "300",
      "report_text": "Reportage sur l'agriculture.",
      "llm_category": "agriculture_alimentation"
    },
    {
      "segment_id": "12346",
      "channel_title": "TF1",
      "channel_name": "tf1",
      "segment_start": "2024-01-15T21:00:00",
      "segment_end": "2024-01-15T21:05:00",
      "duration_seconds": "300",
      "report_text": "Reportage sur la mobilité électrique.",
      "llm_category": "mobility_transport"
    }
  ]
}
```

**Response:**
```json
{
  "processed": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "id": "hash_id_12345_france2",
      "segment_id": "12345",
      "sentiment": "positive",
      "sentiment_confidence": 0.95,
      "status": "success"
    },
    {
      "id": "hash_id_12346_tf1",
      "segment_id": "12346",
      "sentiment": "neutral",
      "sentiment_confidence": 0.87,
      "status": "success"
    }
  ]
}
```

### 5. Get Results by Segment ID
```bash
GET http://localhost:8000/results/12345
```

Retrieves stored analysis results from PostgreSQL for a specific segment.

**Response:**
```json
{
  "id": "hash_id_12345_france2",
  "segment_id": "12345",
  "channel_title": "France 2",
  "channel_name": "france2",
  "segment_start": "2024-01-15T20:00:00",
  "segment_end": "2024-01-15T20:05:00",
  "duration_seconds": "300",
  "report_text": "Un reportage sur l'agriculture durable en France.",
  "llm_category": "agriculture_alimentation",
  "predicted_category": null,
  "sentiment": "positive",
  "sentiment_confidence": 0.95
}
```

## Adding New Model Services

The architecture is designed to be easily extensible. Here's how to add a new model service:

### 1. Create the Model Service

Following the `sentiment/` example:

```python
# my_model/api.py
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI(title="My Model Service")
model = None

@app.on_event("startup")
async def load_model():
    global model
    model = pipeline("task-name", model="model-name")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "my-model"}

@app.post("/predict")
async def predict(request: PredictRequest):
    result = model(request.text)
    return {"prediction": result}
```

### 2. Create Dockerfile

```dockerfile
# my_model/Dockerfile
FROM python:3.12-bookworm
WORKDIR /app
RUN pip install fastapi uvicorn transformers torch
COPY my_model/api.py .
EXPOSE 8002
CMD ["python", "api.py"]
```

### 3. Register in Config

Add to `api/config.py`:

```python
SERVICE_URLS = {
    "sentiment": "http://sentiment-service:8001",
    "my_model": "http://my-model-service:8002",  # Add new service
}
```

### 4. Update Docker Compose

Add to `docker-compose.yml`:

```yaml
my-model-service:
  build:
    context: ./
    dockerfile: my_model/Dockerfile
  expose:
    - "8002"
  networks:
    - metanet1
```

Update `api-gateway` dependencies:

```yaml
api-gateway:
  depends_on:
    - postgres
    - sentiment-service
    - my-model-service  # Add dependency
  environment:
    MY_MODEL_SERVICE_URL: http://my-model-service:8002  # Add URL
```

### 5. Update Gateway Logic

In `api/main.py`, add call function:

```python
async def call_my_model_service(text: str):
    if "my_model" not in SERVICE_URLS:
        return None
    
    async with httpx.AsyncClient(timeout=SERVICE_TIMEOUT) as client:
        response = await client.post(
            f"{SERVICE_URLS['my_model']}/predict",
            json={"text": text}
        )
        if response.status_code == 200:
            return response.json().get("prediction")
    return None
```

Add to `/analyze` endpoint:

```python
@app.post("/analyze")
async def analyze_segment(segment: SegmentData):
    # Call all services in parallel
    sentiment, my_result = await asyncio.gather(
        call_sentiment_service(segment.report_text),
        call_my_model_service(segment.report_text)
    )
    
    # Store in database...
```

### 6. Extend Database Schema

Add columns to `inference/models.py`:

```python
class CategoryClassifications(Base):
    # ... existing columns ...
    sentiment = Column(Text)
    sentiment_confidence = Column(Double)
    my_model_result = Column(Text)  # Add new column
```

## Database Schema

The `category_classification` table stores enriched segment data:

| Column | Type | Description |
|--------|------|-------------|
| id | Text (PK) | Hash of segment_id + channel_name |
| segment_id | Text | Original segment identifier |
| channel_title | String | Display name of TV channel |
| channel_name | Text | Channel code name |
| segment_start | DateTime | Segment start timestamp |
| segment_end | DateTime | Segment end timestamp |
| duration_seconds | Text | Duration in seconds |
| report_text | Text | Full report text content |
| llm_category | Text | LLM-assigned category |
| predicted_category | Text | Model-predicted category |
| sentiment | Text | Sentiment label (positive/negative/neutral) |
| sentiment_confidence | Double | Confidence score for sentiment |

## Development

### Run Gateway Locally

```bash
# Activate virtual environment
source .venv/bin/activate

# Start dependencies
docker compose up postgres sentiment-service

# Run gateway locally
uvicorn api.main:app --reload --port 8000
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Analyze segment
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "segment_id": "test123",
    "channel_title": "France 2",
    "channel_name": "france2",
    "segment_start": "2024-01-15T20:00:00",
    "segment_end": "2024-01-15T20:05:00",
    "duration_seconds": "300",
    "report_text": "Un excellent reportage sur les énergies renouvelables."
  }'
```

## Error Handling

- **503 Service Unavailable**: Database or model service not available
- **400 Bad Request**: Invalid input data
- **404 Not Found**: Segment not found in database
- **500 Internal Server Error**: Unexpected error during processing

If a model service is unavailable, the gateway will store `null` values for those fields and continue processing.

## Future Enhancements

- Add classification service for category prediction
- Add keyword extraction service
- Implement WebSocket for real-time batch processing updates
- Add API authentication and rate limiting
- Add caching layer for frequent queries
- Add retry logic for transient service failures
