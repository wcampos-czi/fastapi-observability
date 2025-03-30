from prometheus_client import Counter, Histogram
from fastapi import FastAPI, Request, Response
from typing import Callable
import time

# Define metrics
REQUEST_COUNT = Counter(
    "http_request_count",
    "Number of requests received",
    ["app_name", "method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["app_name", "method", "endpoint"]
)

def setup_metrics(app: FastAPI, excluded_endpoints: list = None) -> None:
    """Setup metrics middleware for FastAPI application"""
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable) -> Response:
        # Skip metrics collection for excluded endpoints
        if excluded_endpoints and request.url.path in excluded_endpoints:
            return await call_next(request)
            
        start_time = time.time()
        response = await call_next(request)
        
        # Record request latency
        REQUEST_LATENCY.labels(
            app_name="fastapi-app",
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
        
        # Record request count
        REQUEST_COUNT.labels(
            app_name="fastapi-app",
            method=request.method,
            endpoint=request.url.path,
            http_status=response.status_code
        ).inc()
        
        return response 