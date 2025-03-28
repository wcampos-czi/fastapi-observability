from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import structlog
from prometheus_client import Counter, Histogram

class FastAPIObservability:
    def __init__(self, app: FastAPI, app_name: str = "fastapi-app"):
        self.app = app
        self.app_name = app_name
        self._setup_tracing()
        self._setup_metrics()
        self._setup_logging()

    def _setup_tracing(self):
        # Configure OpenTelemetry
        resource = Resource.create({"service.name": self.app_name})
        tracer_provider = TracerProvider(resource=resource)
        
        # Set up OTLP exporter
        otlp_exporter = OTLPSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set the tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(self.app)

    def _setup_metrics(self):
        # Define metrics
        self.request_count = Counter(
            "http_requests_total",
            "Total count of HTTP requests",
            ["method", "endpoint", "status"]
        )
        self.request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"]
        )

        # Add middleware for metrics
        @self.app.middleware("http")
        async def metrics_middleware(request, call_next):
            import time
            start_time = time.time()
            response = await call_next(request)
            duration = time.time() - start_time
            
            self.request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            self.request_duration.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            return response

    def _setup_logging(self):
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            wrapper_class=structlog.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger()
        
        # Add middleware for logging
        @self.app.middleware("http")
        async def logging_middleware(request, call_next):
            self.logger.info(
                "request_started",
                method=request.method,
                path=request.url.path,
                client=request.client.host if request.client else None
            )
            
            response = await call_next(request)
            
            self.logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code
            )
            
            return response 