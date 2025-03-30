from fastapi import FastAPI
from fastapi_observability import FastAPIObservability
import httpx
import asyncio
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

app = FastAPI()

# Initialize observability with feature toggles
observability = FastAPIObservability(
    app=app,
    app_name="app1",
    enable_structlog=True,
    enable_prometheus=True,
    enable_opentelemetry=True,
    otlp_endpoint="http://otel-collector:4317",
    excluded_endpoints=["/health"]
)

# Initialize HTTPXClientInstrumentor for tracing between services
HTTPXClientInstrumentor().instrument()

logger = observability.get_logger()

@app.get("/")
async def root():
    logger.info("root_endpoint_called")
    return {"message": "Hello World"}

@app.get("/chain")
async def chain():
    logger.info("Starting chain in app1")
    
    # Call app2 with tracing
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

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 