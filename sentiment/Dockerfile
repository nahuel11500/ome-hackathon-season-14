# Install uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# Copy project files first
COPY pyproject.toml uv.lock ./
COPY sentiment ./sentiment

# Install dependencies and project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

FROM python:3.12-slim

WORKDIR /app

# Copy the environment and source code
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/sentiment /app/sentiment

# Expose port
EXPOSE 8001

# Run the service
CMD ["/app/.venv/bin/python", "sentiment/api.py"]
