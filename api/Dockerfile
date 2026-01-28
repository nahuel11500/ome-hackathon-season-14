# Install uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# Copy project files first
COPY pyproject.toml uv.lock ./
COPY api ./api

# Install dependencies and project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

FROM python:3.12-slim

WORKDIR /app

# Copy the environment and source code
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/api /app/api

# Expose port
EXPOSE 8000

# Run the gateway
CMD ["/app/.venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
