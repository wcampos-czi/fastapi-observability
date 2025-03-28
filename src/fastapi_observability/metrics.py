from prometheus_client import Counter, Histogram, REGISTRY
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST, generate_latest
from fastapi import Response
from opentelemetry import trace

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
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
        )
        
        self.exceptions_total = Counter(
            "http_exceptions_total",
            "Total number of HTTP exceptions",
            ["method", "endpoint", "exception_type", "service"]
        )

    def get_exemplar(self):
        """Get OpenTelemetry trace ID for exemplar"""
        current_span = trace.get_current_span()
        if current_span:
            span_context = current_span.get_span_context()
            return {"trace_id": format(span_context.trace_id, "032x")}
        return {}

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
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
        ).observe(duration, exemplar=self.get_exemplar())

    def record_exception(self, method: str, endpoint: str, exception_type: str):
        """Record exception metrics"""
        self.exceptions_total.labels(
            method=method,
            endpoint=endpoint,
            exception_type=exception_type,
            service=self.service_name
        ).inc()

    def get_metrics(self) -> Response:
        """Get Prometheus metrics with OpenMetrics format"""
        return Response(
            generate_latest(REGISTRY),
            headers={"Content-Type": CONTENT_TYPE_LATEST}
        ) 