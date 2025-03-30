from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, List
import time
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from .logger import setup_logger
from .metrics import REQUEST_COUNT, REQUEST_LATENCY

class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, app_name: str = "fastapi-app", logger=None, excluded_endpoints: Optional[List[str]] = None):
        super().__init__(app)
        self.app_name = app_name
        self.logger = logger or setup_logger(app_name)
        self.tracer = trace.get_tracer(__name__)
        self.propagator = TraceContextTextMapPropagator()
        self.excluded_endpoints = excluded_endpoints or []

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip excluded endpoints
        if request.url.path in self.excluded_endpoints:
            return await call_next(request)

        start_time = time.time()
        
        # Extract trace context from request headers
        context = self.propagator.extract(carrier=dict(request.headers))
        
        # Start a new span
        with self.tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            context=context,
            kind=trace.SpanKind.SERVER,
        ) as span:
            # Add request attributes to span
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            
            try:
                response = await call_next(request)
                
                # Record metrics
                REQUEST_COUNT.labels(
                    app_name=self.app_name,
                    method=request.method,
                    endpoint=request.url.path,
                    http_status=response.status_code
                ).inc()
                
                REQUEST_LATENCY.labels(
                    app_name=self.app_name,
                    method=request.method,
                    endpoint=request.url.path
                ).observe(time.time() - start_time)
                
                # Add response attributes to span
                span.set_attribute("http.status_code", response.status_code)
                
                # Log request details
                self.logger.info(
                    "Request processed",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration=time.time() - start_time,
                    trace_id=format(span.get_span_context().trace_id, "032x"),
                    span_id=format(span.get_span_context().span_id, "016x")
                )
                
                return response
                
            except Exception as e:
                # Record error metrics
                REQUEST_COUNT.labels(
                    app_name=self.app_name,
                    method=request.method,
                    endpoint=request.url.path,
                    http_status=500
                ).inc()
                
                # Record error in span
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(e)
                
                # Log error
                self.logger.error(
                    "Request failed",
                    method=request.method,
                    path=request.url.path,
                    error=str(e),
                    trace_id=format(span.get_span_context().trace_id, "032x"),
                    span_id=format(span.get_span_context().span_id, "016x")
                )
                raise 