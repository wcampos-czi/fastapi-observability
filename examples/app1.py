from fastapi import FastAPI, status
from fastapi_observability import FastAPIObservability
import httpx
import asyncio
from fastapi.responses import JSONResponse
import logging

# Silence the root logger before initializing FastAPI
logging.getLogger().setLevel(logging.WARNING)

app = FastAPI(
    # Disable FastAPI default startup and shutdown logs
    openapi_url=None if __name__ == "__main__" else "/openapi.json" 
)

# Initialize observability with feature toggles
# The /metrics and /health endpoints are excluded from logs (unless 400+ status) and traces
observability = FastAPIObservability(
    app=app,
    service_name="app1",
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

@app.get("/")
async def root():
    logger.info("root_endpoint_called")
    return {"message": "Hello World"}

@app.get("/chain")
async def chain():
    logger.info("Starting chain in app1")
    
    # Call app2
    async with httpx.AsyncClient() as client:
        response = await client.get("http://app2:8000/process")
        app2_result = response.json()
    
    # Simulate some work
    await asyncio.sleep(0.5)
    
    logger.info("Chain completed in app1")
    return {"message": "Chain completed successfully", "app2_result": app2_result}

@app.get("/error")
async def error():
    logger.error("error_occurred", error_type="ValueError")
    raise ValueError("This is a test error")

@app.get("/success")
async def success():
    # This endpoint is excluded from normal logging and tracing
    # The next line will still appear in the application logs
    # but the middleware won't log the HTTP request details unless status >= 400
    logger.info("success_endpoint_called") 
    return {"status": "success"}

@app.get("/health")
async def health():
    # This endpoint is excluded from normal logging and tracing
    return {"status": "healthy"}

@app.get("/success-error")
async def success_error():
    # This will be logged because it returns a 400 status code
    # even though the path contains "success" which is excluded
    logger.info("success_error_endpoint_called")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "error"}
    )

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