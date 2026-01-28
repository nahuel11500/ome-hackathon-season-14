"""
Configuration for API Gateway
Centralized service registry and database configuration
"""

import os

# Service URLs - Add new model services here
SERVICE_URLS = {
    "sentiment": os.getenv("SENTIMENT_SERVICE_URL", "http://sentiment-service:8001"),
    "ner": os.getenv("NER_SERVICE_URL", "http://ner-service:8002"),
    "keywords": os.getenv("KEYWORDS_SERVICE_URL", "http://keywords-service:8003"),
    # Example for future services:
    # "classification": os.getenv("CLASSIFICATION_SERVICE_URL", "http://classification-service:8004"),
}

# Database configuration
DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER", "user"),
    "password": os.getenv("POSTGRES_PASSWORD", "ilovedataforgood"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "ome_hackathon"),
}

# API settings
API_TITLE = "OME Analysis API Gateway"
API_DESCRIPTION = "Orchestrates multi-model analysis for French TV ecological content"
API_VERSION = "1.0.0"

# Request timeout for model services (seconds)
SERVICE_TIMEOUT = 30.0
