FROM python:3.11-slim

WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY . .

# Install dependencies
RUN uv sync --frozen

# Create data directory
RUN mkdir -p /app/data

# Render and most PaaS set PORT at runtime; default 8000 for local Docker
EXPOSE 8000

# Must bind to 0.0.0.0 and to $PORT so Render detects the open port
CMD ["/bin/sh", "-c", "uv run uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
