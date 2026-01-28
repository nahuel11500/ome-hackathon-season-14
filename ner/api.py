"""
Named Entity Recognition (NER) Microservice
Simple REST API for French NER using spaCy.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List
import spacy
import re
import uvicorn

# Global variable to store model (loaded at startup)
nlp = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for model loading"""
    global nlp
    print("Loading French NER model...")
    try:
        nlp = spacy.load("fr_core_news_sm")
        print("Model loaded successfully!")
    except OSError:
        print("Error: spaCy French model not found.")
        print("Please install with: python -m spacy download fr_core_news_sm")
        raise
    yield
    # Cleanup if needed
    nlp = None


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="NER Service",
    description="Microservice for French Named Entity Recognition",
    version="1.0.0",
    lifespan=lifespan,
)


class PredictRequest(BaseModel):
    """Request model for NER prediction"""

    text: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Emmanuel Macron a rencontré le ministre de l'Agriculture à Paris hier."
            }
        }
    )


class PredictResponse(BaseModel):
    """Response model for NER prediction"""

    persons: List[str]
    organizations: List[str]
    locations: List[str]
    misc: List[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "persons": ["emmanuel macron"],
                "organizations": [],
                "locations": ["paris"],
                "misc": [],
            }
        }
    )


def clean_text(text: str) -> str:
    """Clean text before NER processing"""
    if not isinstance(text, str):
        return ""
    # Remove extra whitespace and special chars
    text = re.sub(r"\s+", " ", text).strip()
    return text


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if nlp is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "status": "healthy",
        "service": "ner",
        "model": "fr_core_news_sm",
    }


@app.post("/predict", response_model=PredictResponse)
async def predict_entities(request: PredictRequest):
    """
    Extract named entities from given text.

    Returns lists of persons, organizations, locations, and miscellaneous entities.
    """
    if nlp is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        # Clean text
        text = clean_text(request.text)

        # Initialize entity lists
        persons = []
        organizations = []
        locations = []
        misc = []

        # Process text in chunks if it's very long (max 5000 chars per chunk)
        chunk_size = 5000
        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]

            # Ensure we don't cut in the middle of a word
            if i + chunk_size < len(text):
                last_space = chunk.rfind(" ")
                if last_space > chunk_size * 0.8:
                    chunk = chunk[:last_space]

            # Process chunk with spaCy
            doc = nlp(chunk)

            # Extract named entities
            for ent in doc.ents:
                entity_text = ent.text.strip().lower()
                # Filter out very short entities, numbers, and common false positives
                if (
                    len(entity_text) > 2
                    and not entity_text.isdigit()
                    and len(entity_text.split()) <= 4
                ):
                    if ent.label_ == "PER":
                        persons.append(entity_text)
                    elif ent.label_ == "ORG":
                        organizations.append(entity_text)
                    elif ent.label_ == "LOC":
                        locations.append(entity_text)
                    elif ent.label_ == "MISC":
                        misc.append(entity_text)

        # Return unique entities
        return PredictResponse(
            persons=list(set(persons)),
            organizations=list(set(organizations)),
            locations=list(set(locations)),
            misc=list(set(misc)),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during NER extraction: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
