from prometheus_client import Counter, Histogram, REGISTRY, CONTENT_TYPE_LATEST
from prometheus_client.openmetrics.exposition import generate_latest
from fastapi import Response, Request
from opentelemetry import trace
import time
from typing import Dict, Any, Optional

class FastAPIObservabilityMetrics:
    def __init__(self, service_name: str):
        self.service_name = service_name
        
        # Define Prometheus metrics
        self.requests_total = Counter(
            "http_requests_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status", "service"]
        )
        
        self.request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint", "service"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
        )
        
        self.exceptions_total = Counter(
            "http_exceptions_total",
            "Total number of HTTP exceptions",
            ["method", "endpoint", "exception_type", "service"]
        )
        
        # Track the start time of requests
        self.request_start_times = {}

    def get_exemplar(self, context: Optional[Dict[str, Any]] = None):
        """Get OpenTelemetry trace ID and request ID for exemplar"""
        exemplar = {}
        
        # Add context data if provided
        if context and "trace_id" in context:
            exemplar["trace_id"] = context["trace_id"]
            
        if context and "request_id" in context:
            exemplar["request_id"] = context["request_id"]
        
        # If no context provided, try to get trace info from current span
        if not exemplar:
            current_span = trace.get_current_span()
            if current_span:
                span_context = current_span.get_span_context()
                if span_context.is_valid:
                    exemplar["trace_id"] = format(span_context.trace_id, "032x")
        
        return exemplar

    def start_timer(self, request_id):
        """Start timing a request"""
        self.request_start_times[request_id] = time.time()
    
    def stop_timer(self, request_id):
        """Stop timing a request and return duration"""
        start_time = self.request_start_times.pop(request_id, None)
        if start_time is None:
            return 0
        return time.time() - start_time

    def record_request(self, method: str, endpoint: str, status: int, duration: float, context: Optional[Dict[str, Any]] = None):
        """Record HTTP request metrics with exemplars"""
        self.requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status),
            service=self.service_name
        ).inc()
        
        self.request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
            service=self.service_name
        ).observe(duration, exemplar=self.get_exemplar(context))

    def record_exception(self, method: str, endpoint: str, exception_type: str, context: Optional[Dict[str, Any]] = None):
        """Record exception metrics"""
        self.exceptions_total.labels(
            method=method,
            endpoint=endpoint,
            exception_type=exception_type,
            service=self.service_name
        ).inc(exemplar=self.get_exemplar(context))

    async def get_metrics(self, request: Request = None) -> Response:
        """Get Prometheus metrics with OpenMetrics format"""
        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        ) 