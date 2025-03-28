from fastapi import FastAPI
from fastapi_observability import FastAPIObservability
from prometheus_client import make_asgi_app

app = FastAPI()
observability = FastAPIObservability(app, "fastapi-demo")

# Add prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/error")
async def error():
    raise ValueError("This is a test error")

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 