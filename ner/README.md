# NER Microservice

Named Entity Recognition microservice for extracting persons, organizations, locations, and miscellaneous entities from French text.

## Model

Uses spaCy's `fr_core_news_sm` model for French NER.

## API Endpoints

### Health Check
```bash
GET /health
```

### Extract Entities
```bash
POST /predict
Content-Type: application/json

{
  "text": "Emmanuel Macron a rencontré le ministre de l'Agriculture à Paris hier."
}
```

Response:
```json
{
  "persons": ["emmanuel macron"],
  "organizations": [],
  "locations": ["paris"],
  "misc": []
}
```

## Running Locally

```bash
python ner/api.py
```

Service will be available at http://localhost:8002

## Testing

```bash
curl -X POST http://localhost:8002/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Emmanuel Macron a visité Paris."}'
```
