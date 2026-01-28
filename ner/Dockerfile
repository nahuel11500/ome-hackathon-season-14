# Install uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# Copy project files first
COPY pyproject.toml uv.lock ./
COPY ner ./ner

# Install dependencies and project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

# Download spaCy French model using uv pip
RUN uv pip install --python .venv fr-core-news-sm@https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.7.0/fr_core_news_sm-3.7.0-py3-none-any.whl

FROM python:3.12-slim

WORKDIR /app

# Copy the environment and source code
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/ner /app/ner

# Expose port
EXPOSE 8002

# Run the service
CMD ["/app/.venv/bin/python", "ner/api.py"]
