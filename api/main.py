"""
API Gateway for OME Hackathon
Orchestrates multi-model analysis and stores results in PostgreSQL
"""

import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.config import (
    SERVICE_URLS,
    DB_CONFIG,
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    SERVICE_TIMEOUT,
)
from api.database.database_connection import connect_to_db, get_db_session
from api.database.models import (
    CategoryClassifications,
    create_tables,
    upsert_data_optimized,
    create_hash_id,
)
from .deduplication import remove_text_loops
from .classification import classify_from_keywords

# Global database engine
db_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global db_engine
    print("Starting API Gateway...")

    try:
        db_engine = connect_to_db(
            database=str(DB_CONFIG["database"]),
            user=str(DB_CONFIG["user"]),
            password=str(DB_CONFIG["password"]),
            host=str(DB_CONFIG["host"]),
            port=int(DB_CONFIG["port"]),
        )
        create_tables(db_engine)
        print("Database connection established and tables created")
    except Exception as e:
        print(f"Warning: Database connection failed: {e}")
        db_engine = None

    yield

    # Shutdown
    if db_engine:
        db_engine.dispose()
        print("Database connection closed")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title=API_TITLE, description=API_DESCRIPTION, version=API_VERSION, lifespan=lifespan
)

# Add CORS middleware for frontend
from starlette.middleware.cors import CORSMiddleware as StarletteMiddleware
app.add_middleware(
    StarletteMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class SegmentData(BaseModel):
    """Input model for segment analysis"""

    segment_id: str
    channel_title: str
    channel_name: str
    segment_start: datetime
    segment_end: datetime
    duration_seconds: str
    report_text: str
    llm_category: Optional[str] = None
    predicted_category: Optional[str] = None
    agricultural_category: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "segment_id": "12345",
                "channel_title": "France 2",
                "channel_name": "france2",
                "segment_start": "2024-01-15T20:00:00",
                "segment_end": "2024-01-15T20:05:00",
                "duration_seconds": "300",
                "report_text": "Un reportage sur l'agriculture durable en France.",
                "llm_category": "agriculture_alimentation",
            }
        }


class AnalysisResult(BaseModel):
    """Response model for analysis results"""

    id: str
    segment_id: str
    sentiment: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    actor_persons: Optional[List[str]] = None
    actor_organizations: Optional[List[str]] = None
    actor_locations: Optional[List[str]] = None
    actor_misc: Optional[List[str]] = None
    keywords_filtered: Optional[List[str]] = None
    keywords_nouns: Optional[List[str]] = None
    agricultural_category: Optional[str] = None
    status: str = "success"
    message: Optional[str] = None


class BatchAnalysisRequest(BaseModel):
    """Request model for batch analysis"""

    segments: List[SegmentData]


class BatchAnalysisResponse(BaseModel):
    """Response model for batch analysis"""

    processed: int
    successful: int
    failed: int
    results: List[AnalysisResult]


class ServiceHealth(BaseModel):
    """Health status for a service"""

    name: str
    status: str
    url: str


class HealthResponse(BaseModel):
    """Overall health check response"""

    status: str
    database: str
    services: List[ServiceHealth]


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OME Analysis API Gateway",
        "version": API_VERSION,
        "endpoints": {
            "analyze": "/analyze",
            "batch": "/analyze/batch",
            "results": "/results/{segment_id}",
            "health": "/health",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check health of API gateway and all downstream services
    """
    # Check database
    db_status = "healthy" if db_engine else "unavailable"

    # Check all model services
    service_health = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in SERVICE_URLS.items():
            try:
                response = await client.get(f"{service_url}/health")
                if response.status_code == 200:
                    status = "healthy"
                else:
                    status = "unhealthy"
            except Exception:
                status = "unavailable"

            service_health.append(
                ServiceHealth(name=service_name, status=status, url=service_url)
            )

    # Overall status
    all_healthy = db_status == "healthy" and all(
        s.status == "healthy" for s in service_health
    )
    overall_status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=overall_status, database=db_status, services=service_health
    )


async def call_sentiment_service(text: str) -> tuple[Optional[str], Optional[float]]:
    """
    Call sentiment analysis service
    Returns (sentiment, confidence) tuple
    """
    if "sentiment" not in SERVICE_URLS:
        return None, None

    try:
        async with httpx.AsyncClient(timeout=SERVICE_TIMEOUT) as client:
            response = await client.post(
                f"{SERVICE_URLS['sentiment']}/predict", json={"text": text}
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("sentiment"), result.get("confidence")
            else:
                print(f"Sentiment service returned status {response.status_code}")
                return None, None

    except Exception as e:
        print(f"Error calling sentiment service: {e}")
        return None, None


async def call_ner_service(text: str) -> dict:
    """
    Call NER service to extract entities
    Returns dictionary with persons, organizations, locations, misc
    """
    if "ner" not in SERVICE_URLS:
        return {"person": [], "organization": [], "location": [], "misc": []}

    try:
        async with httpx.AsyncClient(timeout=SERVICE_TIMEOUT) as client:
            response = await client.post(
                f"{SERVICE_URLS['ner']}/predict", json={"text": text}
            )

            if response.status_code == 200:
                result = response.json()
                # Convert response keys to match our database schema
                return {
                    "person": result.get("persons", []),
                    "organization": result.get("organizations", []),
                    "location": result.get("locations", []),
                    "misc": result.get("misc", []),
                }
            else:
                print(f"NER service returned status {response.status_code}")
                return {"person": [], "organization": [], "location": [], "misc": []}

    except Exception as e:
        print(f"Error calling NER service: {e}")
        return {"person": [], "organization": [], "location": [], "misc": []}


async def call_keywords_service(text: str) -> dict:
    """
    Call keywords service to extract keywords and nouns
    Returns dictionary with keywords and keywords_nouns
    """
    if "keywords" not in SERVICE_URLS:
        return {"keywords": [], "nouns": []}

    try:
        async with httpx.AsyncClient(timeout=SERVICE_TIMEOUT) as client:
            response = await client.post(
                f"{SERVICE_URLS['keywords']}/predict", json={"texts": [text]}
            )

            if response.status_code == 200:
                result = response.json()
                # Response is a list with one element containing the result dict
                if isinstance(result, list) and len(result) > 0:
                    kw_data = result[0]
                    return {
                        "keywords": kw_data.get("keywords_filtered", []),
                        "nouns": kw_data.get("nouns_found", []),
                    }
                return {"keywords": [], "nouns": []}
            else:
                print(f"Keywords service returned status {response.status_code}")
                return {"keywords": [], "nouns": []}

    except Exception as e:
        print(f"Error calling keywords service: {e}")
        return {"keywords": [], "nouns": []}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_segment(segment: SegmentData):
    """
    Analyze a single segment by querying all available model services
    and storing the enriched results in PostgreSQL

    Pipeline:
    1. Deduplication - Remove repetitive text loops
    2. NER - Extract actors (persons, organizations, locations, misc)
    3. Sentiment Analysis - Classify sentiment
    4. Store results in PostgreSQL
    """
    if not db_engine:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        # Step 1: Deduplication - Remove repetitive loops from text
        deduplicated_text = remove_text_loops(segment.report_text)

        # Step 2, 3 & 4: Call NER, Sentiment and Keywords services in parallel
        actors, (sentiment, sentiment_confidence), keywords_data = await asyncio.gather(
            call_ner_service(deduplicated_text),
            call_sentiment_service(deduplicated_text),
            call_keywords_service(deduplicated_text),
        )

        # Step 5: Classify agricultural discourse based on keywords
        keywords_nouns = keywords_data.get("nouns", [])
        agricultural_category = classify_from_keywords(keywords_nouns)

        # Prepare data for database
        segment_dict = segment.model_dump()
        segment_dict["sentiment"] = sentiment
        segment_dict["sentiment_confidence"] = sentiment_confidence
        segment_dict["actor_persons"] = actors.get("person", [])
        segment_dict["actor_organizations"] = actors.get("organization", [])
        segment_dict["actor_locations"] = actors.get("location", [])
        segment_dict["actor_misc"] = actors.get("misc", [])
        segment_dict["keywords_filtered"] = keywords_data.get("keywords", [])
        segment_dict["keywords_nouns"] = keywords_nouns
        segment_dict["agricultural_category"] = agricultural_category

        # Create DataFrame and add hash ID
        df = pd.DataFrame([segment_dict])
        df = create_hash_id(df, column_name="id", id_column="segment_id", position=0)

        # Upsert to database
        session = get_db_session(db_engine)
        try:
            upsert_data_optimized(
                session=session,
                df=df,
                table_class=CategoryClassifications,
                primary_key="id",
            )
        finally:
            session.close()

        return AnalysisResult(
            id=df["id"].iloc[0],
            segment_id=segment.segment_id,
            sentiment=sentiment,
            sentiment_confidence=sentiment_confidence,
            actor_persons=actors.get("person", []),
            actor_organizations=actors.get("organization", []),
            actor_locations=actors.get("location", []),
            actor_misc=actors.get("misc", []),
            keywords_filtered=keywords_data.get("keywords", []),
            keywords_nouns=keywords_nouns,
            agricultural_category=agricultural_category,
            status="success",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during analysis: {str(e)}")


@app.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(request: BatchAnalysisRequest):
    """
    Analyze multiple segments in parallel using async processing
    """
    if not db_engine:
        raise HTTPException(status_code=503, detail="Database unavailable")

    results = []
    successful = 0
    failed = 0

    # Process all segments concurrently
    async def process_segment(segment: SegmentData) -> AnalysisResult:
        try:
            result = await analyze_segment(segment)
            return result
        except Exception as e:
            return AnalysisResult(
                id="", segment_id=segment.segment_id, status="failed", message=str(e)
            )

    # Use asyncio.gather to process in parallel
    results = await asyncio.gather(
        *[process_segment(seg) for seg in request.segments], return_exceptions=False
    )

    # Count successes and failures
    for result in results:
        if result.status == "success":
            successful += 1
        else:
            failed += 1

    return BatchAnalysisResponse(
        processed=len(request.segments),
        successful=successful,
        failed=failed,
        results=results,
    )


@app.get("/results/{segment_id}")
async def get_results(segment_id: str):
    """
    Retrieve analysis results for a specific segment from PostgreSQL
    """
    if not db_engine:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        session = get_db_session(db_engine)
        try:
            # Query by segment_id
            result = (
                session.query(CategoryClassifications)
                .filter(CategoryClassifications.segment_id == segment_id)
                .first()
            )

            if not result:
                raise HTTPException(status_code=404, detail="Segment not found")

            # Convert to dict
            result_dict = {
                "id": result.id,
                "segment_id": result.segment_id,
                "channel_title": result.channel_title,
                "channel_name": result.channel_name,
                "segment_start": result.segment_start,
                "segment_end": result.segment_end,
                "duration_seconds": result.duration_seconds,
                "report_text": result.report_text,
                "llm_category": result.llm_category,
                "predicted_category": result.predicted_category,
                "agricultural_category": result.agricultural_category,
                "sentiment": result.sentiment,
                "sentiment_confidence": result.sentiment_confidence,
                "actor_persons": result.actor_persons,
                "actor_organizations": result.actor_organizations,
                "actor_locations": result.actor_locations,
                "actor_misc": result.actor_misc,
                "keywords_filtered": result.keywords_filtered,
                "keywords_nouns": result.keywords_nouns,
            }

            return result_dict

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving results: {str(e)}"
        )
