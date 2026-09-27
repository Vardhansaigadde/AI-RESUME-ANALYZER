# Use official lightweight Python runtime
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Configure Python execution environment for containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install minimal OS utilities needed for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies without caching wheel files to keep image lightweight
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and serialized ML model artifacts
COPY app/ ./app/
COPY models/ ./models/

# Expose FastAPI listening port
EXPOSE 8000

# Periodic health check against root endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start production uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
