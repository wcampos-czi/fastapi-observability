import structlog
import logging
import sys
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from typing import Optional, Dict, Any
import traceback

def custom_renderer(_, __, event_dict):
    """
    Custom log formatter that outputs a minimal single-line log format.
    """
    # Get basic values from context
    timestamp = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", "").upper()
    service = event_dict.pop("service_name", "")
    request_id = event_dict.pop("request_id", "")
    trace_id = event_dict.pop("trace_id", "")
    
    # Get message and clean it
    message = event_dict.pop("event", "")
    if isinstance(message, str):
        message = message.replace('\n', ' ').replace('\r', '')
    
    # Format the output as a simple string with only requested fields
    output = f"{timestamp} {level} [{service}]"
    
    if request_id:
        output += f" req_id={request_id}"
    
    if trace_id:
        output += f" trace_id={trace_id}"
        
    if message:
        output += f" - {message}"
    
    return output

class FastAPIObservabilityLogger:
    def __init__(self, service_name: str, disable_default_loggers: bool = False):
        self.service_name = service_name
        
        # Configure logging with minimal format
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=logging.INFO,
        )
        
        # Set root logger to INFO level
        logging.getLogger().setLevel(logging.INFO)
        
        # Disable default loggers if requested
        if disable_default_loggers:
            self._disable_default_loggers()
            
        # Configure structlog with minimal format
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                # Simple timestamp without milliseconds
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                custom_renderer
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True
        )
        
        self.logger = structlog.get_logger()
    
    def _disable_default_loggers(self):
        """Disable default FastAPI/Uvicorn loggers"""
        # Set all loggers to WARNING or higher level
        for logger_name in logging.root.manager.loggerDict:
            if logger_name.startswith(('uvicorn.', 'fastapi.', 'gunicorn.')):
                logging.getLogger(logger_name).setLevel(logging.WARNING)
        
        # Disable standard library loggers that might be noisy
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    def get_logger(self):
        """Get a logger instance with OpenTelemetry context"""
        current_span = trace.get_current_span()
        if current_span:
            span_context = current_span.get_span_context()
            if span_context.is_valid:
                # Use trace.format_trace_id to get properly formatted trace ID
                return self.logger.bind(
                    trace_id=trace.format_trace_id(span_context.trace_id),
                    span_id=trace.format_span_id(span_context.span_id),
                    service=self.service_name
                )
        return self.logger.bind(service=self.service_name)

    def log_request(self, request, response, context=None):
        """Log HTTP request with minimal information"""
        # Get client information
        if request.client:
            client_host = request.client.host
            client_port = request.client.port
        else:
            client_host = "unknown"
            client_port = "0"
        
        # Get HTTP version
        http_version = request.scope.get("http_version", "1.1")
        
        # Log with minimal format
        self.logger.info(
            f"{client_host}:{client_port} - \"{request.method} {request.url.path} HTTP/{http_version}\" {response.status_code}",
            http={
                "url": str(request.url),
                "status_code": response.status_code,
                "method": request.method,
                "version": http_version,
            },
            network={"client": {"ip": client_host, "port": client_port}},
        )

    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with minimal information"""
        error_msg = f"error {type(error).__name__}: {str(error)}"
        self.logger.error(error_msg)

    def _get_current_span_context(self) -> Dict[str, str]:
        """
        Get the current span context from OpenTelemetry.
        
        Returns:
            Dict containing trace_id and span_id if available
        """
        span_context = {}
        current_span = trace.get_current_span()
        
        if current_span:
            ctx = current_span.get_span_context()
            if ctx.is_valid:
                # Use OpenTelemetry's formatters to get the trace and span IDs
                span_context["trace_id"] = trace.format_trace_id(ctx.trace_id)
                span_context["span_id"] = trace.format_span_id(ctx.span_id)
                
        return span_context 