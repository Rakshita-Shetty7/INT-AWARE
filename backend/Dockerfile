# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install Python dependencies first for better layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt

# Application code, entrypoint scripts, and the trained ML artifact (under backend/app/ml)
COPY backend/ /app/backend/
COPY scripts/ /app/scripts/

EXPOSE 8000

# Liveness/readiness: API /health returns 200 even when Mongo is degraded
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=3).status==200 else 1)" || exit 1

# Plain uvicorn; the ingestion pipeline starts inside the app lifespan when PIPELINE_ENABLED=true
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
