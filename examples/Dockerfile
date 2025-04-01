FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install fastapi uvicorn \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-exporter-otlp \
    opentelemetry-instrumentation-requests \
    opentelemetry-instrumentation-httpx \
    httpx

# Copy the library files
COPY setup.py .
COPY src/fastapi_observability fastapi_observability/
COPY examples examples/

# Install the library in development mode
RUN pip install -e .

# Run the application using APP_MODULE environment variable
ENV APP_MODULE=examples.feature_demo:app
ENV LOG_LEVEL=warning
ENV UVICORN_LOG_LEVEL=error
ENV UVICORN_ACCESS_LOG=false
CMD uvicorn ${APP_MODULE} --host 0.0.0.0 --port 8000 --log-level ${UVICORN_LOG_LEVEL} --no-access-log 