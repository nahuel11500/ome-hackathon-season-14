# OME Hackathon Season 14

**Text Analysis Microservices for Media Ecology**

Data For Good x L'Observatoire des Médias sur l'Écologie

## 🚀 Quick Start

Be aware that it takes some time to start up !
```bash
# Start all services
docker-compose up --build

# Access the API
open http://localhost:8000

# Access the frontend
open frontend/index.html
```

## 📁 Project Structure

```
├── api/              # API Gateway (orchestrates all services)
├── sentiment/        # Sentiment analysis microservice
├── ner/             # Named Entity Recognition microservice
├── key-words/       # Keywords extraction microservice
├── frontend/        # Web interface
├── analysis/        # Data analysis notebooks
└── docker-compose.yml
```

## 🏗️ Architecture

**Microservices:**
- **API Gateway** (port 8000) - Orchestrates all analysis services
- **Sentiment Service** - Analyzes text sentiment (positive/negative/neutral)
- **NER Service** - Extracts persons, organizations, and locations
- **Keywords Service** - Extracts key themes and topics
- **PostgreSQL** - Stores analysis results

## 🛠️ Development

### Setup

## Easu setup script
```bash
./setup.sh
```

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Code Quality

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
ty check
```

### Run Locally

```bash
# Start services
docker-compose up --build

# Test

# Process all the provided data through the API. (Take somes times)
python process_and_export.py
```

## 📊 Analysis

Jupyter notebook with comprehensive analysis available in `analysis/analysis.ipynb`:
- Agricultural themes representation
- Media actors and organizations
- Sentiment distribution
- Geographic coverage

## 🤝 Team

**Les puissants gardes forestiers** - OME Hackathon Season 14

## 📄 License

See LICENSE file.
