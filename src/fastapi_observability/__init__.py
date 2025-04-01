from fastapi import FastAPI
from .logger import FastAPIObservabilityLogger
from .metrics import FastAPIObservabilityMetrics
from .instrumentation import setup_telemetry, instrument_fastapi, instrument_httpx
from .middleware import ObservabilityMiddleware
from typing import Optional, List, Union, Callable

class FastAPIObservability:
    def __init__(
        self,
        app: FastAPI,
        app_name: str = None,
        service_name: str = None,
        otlp_endpoint: str = "http://localhost:4317",
        enable_structlog: bool = True,
        enable_prometheus: bool = True,
        enable_opentelemetry: bool = True,
        excluded_endpoints: Union[List[str], str] = None,
        disable_default_loggers: bool = False,
    ):
        # For backward compatibility, support both app_name and service_name
        if service_name is None and app_name is not None:
            service_name = app_name
        elif service_name is None and app_name is None:
            service_name = "fastapi-service"
            
        self.app = app
        self.service_name = service_name
        self.enable_structlog = enable_structlog
        self.enable_prometheus = enable_prometheus
        self.enable_opentelemetry = enable_opentelemetry
        self.disable_default_loggers = disable_default_loggers
        
        # Format excluded endpoints for OpenTelemetry
        self.excluded_urls = None
        if excluded_endpoints:
            if isinstance(excluded_endpoints, list):
                # Remove leading slashes and join with commas
                self.excluded_urls = ",".join([ep.lstrip('/') for ep in excluded_endpoints])
            else:
                self.excluded_urls = excluded_endpoints
        
        # Initialize components based on feature flags
        self.logger = FastAPIObservabilityLogger(
            service_name=service_name, 
            disable_default_loggers=disable_default_loggers
        ) if enable_structlog else None
        
        self.metrics = FastAPIObservabilityMetrics(service_name) if enable_prometheus else None
        
        # Setup OpenTelemetry if enabled
        self.tracer_provider = None
        if enable_opentelemetry:
            self.tracer_provider = setup_telemetry(service_name, otlp_endpoint)
            # Instrument FastAPI with OpenTelemetry before adding middleware
            instrument_fastapi(
                self.app, 
                self.tracer_provider, 
                excluded_urls=self.excluded_urls or "health,metrics"
            )
        
        # Add middleware if logging or metrics are enabled
        if enable_structlog or enable_prometheus:
            self.app.add_middleware(
                ObservabilityMiddleware,
                service_name=service_name,
                logger=self.logger,
                metrics=self.metrics,
                excluded_endpoints=excluded_endpoints
            )
        
        # Add metrics endpoint if Prometheus is enabled
        if enable_prometheus:
            self.app.add_route("/metrics", self.metrics.get_metrics)
    
    def get_logger(self):
        """Get the configured logger"""
        if not self.enable_structlog:
            raise RuntimeError("Structlog is not enabled")
        return self.logger.get_logger()
        
    def instrument_httpx_client(self, capture_headers: bool = False, request_hook: Optional[Callable] = None, response_hook: Optional[Callable] = None):
        """Instrument HTTPX client with OpenTelemetry
        
        Args:
            capture_headers: Whether to capture HTTP headers as span attributes
            request_hook: Optional callback function called before the request is sent
            response_hook: Optional callback function called after the response is received
        
        Returns:
            The instrumented HTTPX client
        
        Raises:
            RuntimeError: If OpenTelemetry is not enabled
        """
        if not self.enable_opentelemetry:
            raise RuntimeError("OpenTelemetry is not enabled")
            
        return instrument_httpx(
            tracer_provider=self.tracer_provider,
            capture_headers=capture_headers,
            request_hook=request_hook,
            response_hook=response_hook
        ) 