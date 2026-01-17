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

# Expose port
EXPOSE 8000

# Run the API
CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
