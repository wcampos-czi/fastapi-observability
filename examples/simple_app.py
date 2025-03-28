from fastapi import FastAPI, HTTPException
from fastapi_observability import FastAPIObservability
import time

app = FastAPI()

# Initialize observability
observability = FastAPIObservability(
    app=app,
    service_name="example-service",
    otlp_endpoint="http://localhost:4317"
)

# Get logger for custom logging
logger = observability.get_logger()

@app.get("/")
async def root():
    logger.info("handling_root_request")
    return {"message": "Hello World"}

@app.get("/slow")
async def slow_endpoint():
    logger.info("handling_slow_request")
    time.sleep(2)  # Simulate slow processing
    return {"message": "This was slow"}

@app.get("/error")
async def error_endpoint():
    logger.info("handling_error_request")
    raise HTTPException(status_code=500, detail="This is an error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 