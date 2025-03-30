from fastapi import FastAPI
from fastapi_observability import FastAPIObservability
import httpx
import asyncio
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

app = FastAPI()

# Initialize observability with feature toggles
observability = FastAPIObservability(
    app=app,
    app_name="app2",
    enable_structlog=True,
    enable_prometheus=True,
    enable_opentelemetry=True,
    otlp_endpoint="http://otel-collector:4317",
    excluded_endpoints=["/health"]
)

# Initialize HTTPXClientInstrumentor for tracing between services
HTTPXClientInstrumentor().instrument()

logger = observability.get_logger()

@app.get("/process")
async def process():
    logger.info("Processing request in app2")
    # Simulate some work
    await asyncio.sleep(0.5)
    return {"message": "Processed by app2"}

@app.get("/health")
async def health():
    return {"status": "healthy"} 