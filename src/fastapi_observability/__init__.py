from fastapi import FastAPI
from .logger import FastAPIObservabilityLogger
from .metrics import FastAPIObservabilityMetrics
from .instrumentation import setup_telemetry, instrument_fastapi
from .middleware import ObservabilityMiddleware
from typing import Optional

class FastAPIObservability:
    def __init__(
        self,
        app: FastAPI,
        service_name: str,
        otlp_endpoint: str = "http://localhost:4317",
        enable_structlog: bool = True,
        enable_prometheus: bool = True,
        enable_opentelemetry: bool = True,
    ):
        self.app = app
        self.service_name = service_name
        self.enable_structlog = enable_structlog
        self.enable_prometheus = enable_prometheus
        self.enable_opentelemetry = enable_opentelemetry
        
        # Initialize components based on feature flags
        self.logger = FastAPIObservabilityLogger(service_name) if enable_structlog else None
        self.metrics = FastAPIObservabilityMetrics(service_name) if enable_prometheus else None
        
        # Setup OpenTelemetry if enabled
        self.tracer_provider = None
        if enable_opentelemetry:
            self.tracer_provider = setup_telemetry(service_name, otlp_endpoint)
            instrument_fastapi(self.app, self.tracer_provider)
        
        # Add middleware if logging or metrics are enabled
        if enable_structlog or enable_prometheus:
            self.app.add_middleware(
                ObservabilityMiddleware,
                service_name=service_name,
                logger=self.logger,
                metrics=self.metrics
            )
        
        # Add metrics endpoint if Prometheus is enabled
        if enable_prometheus:
            self.app.add_route("/metrics", self.metrics.get_metrics)
    
    def get_logger(self):
        """Get the configured logger"""
        if not self.enable_structlog:
            raise RuntimeError("Structlog is not enabled")
        return self.logger.get_logger() 