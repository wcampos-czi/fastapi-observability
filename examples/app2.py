from fastapi import FastAPI, status
from fastapi_observability import FastAPIObservability
import httpx
import asyncio
import logging

# Silence the root logger before initializing FastAPI
logging.getLogger().setLevel(logging.WARNING)

app = FastAPI(
    # Disable FastAPI default startup and shutdown logs
    openapi_url=None if __name__ == "__main__" else "/openapi.json" 
)

# Initialize observability with feature toggles
# The /metrics, /health, and /success endpoints are excluded from logs (unless 400+ status) and traces
observability = FastAPIObservability(
    app=app,
    service_name="app2",
    enable_structlog=True,
    enable_prometheus=True,
    enable_opentelemetry=True,
    otlp_endpoint="http://otel-collector:4317",
    excluded_endpoints=["/metrics", "/health", "/success"],  # Added /success to exclusions
    disable_default_loggers=True  # Disable default FastAPI/Uvicorn loggers
)

# Get structured logger
logger = observability.get_logger()

# Explicitly instrument HTTPX client
observability.instrument_httpx_client(capture_headers=True)

@app.get("/process")
async def process():
    logger.info("Processing request in app2")
    # Simulate some work
    await asyncio.sleep(0.5)
    return {"message": "Processed by app2"}

@app.get("/success")
async def success():
    # This endpoint is excluded from normal logging and tracing
    # unless the status code is >= 400
    logger.info("success_endpoint_called")
    return {"status": "success"}

@app.get("/health")
async def health():
    # This endpoint is excluded from normal logging and tracing
    return {"status": "healthy"}

@app.get("/debug")
async def debug():
    """Endpoint to debug request_id and trace_id"""
    # Access the raw logger to log everything
    logger.info("debug_endpoint_called")
    
    # Get the current request context
    ctx = {}
    
    # Log OpenTelemetry trace context using proper formatters
    from opentelemetry import trace
    current_span = trace.get_current_span()
    if current_span:
        span_context = current_span.get_span_context()
        if span_context.is_valid:
            ctx["trace_id"] = trace.format_trace_id(span_context.trace_id)
            ctx["span_id"] = trace.format_span_id(span_context.span_id)
    
    logger.info("context_debug", **ctx)
    
    return {
        "message": "Debug info logged",
        "context": ctx
    }

if __name__ == "__main__":
    import uvicorn
    # Configure Uvicorn to use minimal logging
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="error",
        access_log=False
    ) 