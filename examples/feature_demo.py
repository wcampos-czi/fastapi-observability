from fastapi import FastAPI, HTTPException
from fastapi_observability import FastAPIObservability
import time
import os
import structlog

app = FastAPI()

# Get feature flags from environment variables
ENABLE_STRUCTLOG = os.getenv("ENABLE_STRUCTLOG", "true").lower() == "true"
ENABLE_PROMETHEUS = os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true"
ENABLE_OPENTELEMETRY = os.getenv("ENABLE_OPENTELEMETRY", "true").lower() == "true"
ENABLE_LOKI = os.getenv("ENABLE_LOKI", "false").lower() == "true"
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100/loki/api/v1/push")

# Configure structlog with Loki if enabled
if ENABLE_LOKI:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(structlog.get_level()),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

# Initialize observability with feature flags
observability = FastAPIObservability(
    app=app,
    service_name="feature-demo-service",
    otlp_endpoint=OTLP_ENDPOINT,
    enable_structlog=ENABLE_STRUCTLOG,
    enable_prometheus=ENABLE_PROMETHEUS,
    enable_opentelemetry=ENABLE_OPENTELEMETRY,
)

# Get logger if structlog is enabled
logger = observability.get_logger() if ENABLE_STRUCTLOG else None

@app.get("/")
async def root():
    if logger:
        logger.info("handling_root_request", loki_enabled=ENABLE_LOKI)
    return {
        "message": "Hello World",
        "features": {
            "structlog": ENABLE_STRUCTLOG,
            "prometheus": ENABLE_PROMETHEUS,
            "opentelemetry": ENABLE_OPENTELEMETRY,
            "loki": ENABLE_LOKI,
        }
    }

@app.get("/slow")
async def slow_endpoint():
    if logger:
        logger.info("handling_slow_request")
    time.sleep(2)  # Simulate slow processing
    return {"message": "This was slow"}

@app.get("/error")
async def error_endpoint():
    if logger:
        logger.info("handling_error_request")
    raise HTTPException(status_code=500, detail="This is an error")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 