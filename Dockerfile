# Same Python minor version as the environment the models were trained and
# tested in (see requirements.txt).
FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# curl is used by the container health check
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first so code edits don't invalidate this layer
COPY requirements.txt .
RUN pip install -r requirements.txt

# Application code and the serialized model artifacts it loads at startup
COPY app/ ./app/
COPY models/ ./models/

# Run as an unprivileged user
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/" || exit 1

# Shell form so ${PORT} (injected by Render and other platforms) is honoured.
# --proxy-headers: Render/Vercel terminate TLS in front of the container.
CMD uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --proxy-headers --forwarded-allow-ips="*"
