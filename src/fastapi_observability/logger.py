import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

class FastAPIObservabilityLogger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = structlog.get_logger()
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(structlog.get_level()),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
        )

    def get_logger(self):
        """Get a logger instance with OpenTelemetry context"""
        current_span = trace.get_current_span()
        if current_span:
            span_context = current_span.get_span_context()
            return self.logger.bind(
                trace_id=format(span_context.trace_id, "032x"),
                span_id=format(span_context.span_id, "016x"),
                service=self.service_name
            )
        return self.logger.bind(service=self.service_name)

    def log_request(self, request, response=None, error=None):
        """Log HTTP request details with OpenTelemetry context"""
        logger = self.get_logger()
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
            "status_code": response.status_code if response else None,
        }
        
        if error:
            log_data["error"] = str(error)
            logger.error("request_failed", **log_data)
        else:
            logger.info("request_completed", **log_data)

    def log_error(self, error, context=None):
        """Log error with OpenTelemetry context"""
        logger = self.get_logger()
        log_data = {"error": str(error)}
        if context:
            log_data.update(context)
        logger.error("error_occurred", **log_data) 