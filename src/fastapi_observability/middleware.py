import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import List, Optional, Union
from opentelemetry import trace
import structlog
from starlette.datastructures import URL
from starlette.types import ASGIApp, Receive, Scope, Send

from .logger import FastAPIObservabilityLogger
from .metrics import FastAPIObservabilityMetrics

def get_path_with_query_string(scope):
    """Get the path with query string from the scope."""
    path = scope.get("path", "")
    query_string = scope.get("query_string", b"").decode()
    if query_string:
        path = f"{path}?{query_string}"
    return path

class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        service_name: str,
        logger: FastAPIObservabilityLogger = None,
        metrics: FastAPIObservabilityMetrics = None,
        excluded_endpoints: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.service_name = service_name
        self.logger = logger
        self.metrics = metrics
        self.excluded_endpoints = excluded_endpoints or []
        
        # Normalize excluded endpoints for easier comparison
        self.normalized_excluded_endpoints = [
            endpoint.lstrip('/') for endpoint in self.excluded_endpoints
        ] if self.excluded_endpoints else []

    def is_excluded(self, path: str) -> bool:
        """Check if the path is in the excluded endpoints list"""
        # Normalize the path for comparison
        normalized_path = path.lstrip('/')
        return normalized_path in self.normalized_excluded_endpoints

    async def dispatch(self, request: Request, call_next):
        # Clear any existing context variables
        structlog.contextvars.clear_contextvars()
        
        # Generate request ID and bind context variables
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(
            request_id=request_id
        )
        
        # Get trace context from current span
        current_span = trace.get_current_span()
        trace_context = {}
        if current_span:
            span_context = current_span.get_span_context()
            if span_context.is_valid:
                trace_context = {
                    "trace_id": trace.format_trace_id(span_context.trace_id),
                    "span_id": trace.format_span_id(span_context.span_id)
                }
        
        # Start request timing
        start_time = time.time()
        
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            if self.logger:
                self.logger.log_error(e, context={
                    "request_id": request_id,
                    **trace_context
                })
            raise
        finally:
            status_code = response.status_code
            url = get_path_with_query_string(request.scope).removeprefix(request.scope.get('root_path', ''))
            
            # Get client information
            if request.client:
                client_host = request.client.host
                client_port = request.client.port
            else:
                client_host = "unknown"
                client_port = "0"
            
            http_method = request.method
            http_version = request.scope.get("http_version", "1.1")
            
            # Only log if endpoint is not excluded or if it's an error response
            if not self.is_excluded(url) or status_code >= 400:
                # Log request with all context
                if self.logger:
                    self.logger.log_request(request, response, context={
                        "request_id": request_id,
                        **trace_context,
                        "client_host": client_host,
                        "client_port": client_port,
                        "http_version": http_version
                    })
            
            # Record metrics if enabled
            if self.metrics:
                duration = time.time() - start_time
                self.metrics.record_request(
                    method=http_method,
                    endpoint=url,
                    status=status_code,
                    duration=duration,
                    context={
                        "request_id": request_id,
                        **trace_context
                    }
                )
        
        return response 