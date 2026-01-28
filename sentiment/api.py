"""
Sentiment Analysis Microservice
Simple REST API for French sentiment analysis using Hugging Face transformers.
This serves as a template for adding new model microservices.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from transformers import pipeline
import uvicorn

# Global variable to store model (loaded at startup)
sentiment_analyzer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for model loading"""
    global sentiment_analyzer
    print("Loading French sentiment analysis model...")
    sentiment_analyzer = pipeline(
        "text-classification", model="ac0hik/Sentiment_Analysis_French"
    )
    print("Model loaded successfully!")
    yield
    # Cleanup if needed
    sentiment_analyzer = None


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Sentiment Analysis Service",
    description="Microservice for French sentiment analysis",
    version="1.0.0",
    lifespan=lifespan,
)


class PredictRequest(BaseModel):
    """Request model for sentiment prediction"""

    text: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "C'est un excellent reportage sur l'agriculture durable."
            }
        }
    )


class PredictResponse(BaseModel):
    """Response model for sentiment prediction"""

    sentiment: str
    confidence: float

    model_config = ConfigDict(
        json_schema_extra={"example": {"sentiment": "positive", "confidence": 0.95}}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if sentiment_analyzer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "status": "healthy",
        "service": "sentiment-analysis",
        "model": "ac0hik/Sentiment_Analysis_French",
    }


@app.post("/predict", response_model=PredictResponse)
async def predict_sentiment(request: PredictRequest):
    """
    Predict sentiment for given text.

    Returns sentiment label (positive/negative/neutral) and confidence score.
    """
    if sentiment_analyzer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        # Truncate text to avoid token limit issues (max ~512 tokens)
        text_truncated = request.text[:512]

        # Get prediction
        result = sentiment_analyzer(text_truncated)[0]

        # Normalize label to lowercase
        label = result["label"].upper()
        if "POSITIVE" in label or "POS" in label:
            sentiment = "positive"
        elif "NEGATIVE" in label or "NEG" in label:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        confidence = float(result["score"])

        return PredictResponse(sentiment=sentiment, confidence=confidence)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during prediction: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
