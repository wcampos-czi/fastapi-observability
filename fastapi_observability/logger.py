import logging
import sys
import structlog
from typing import Optional

def setup_logger(name: str, log_level: Optional[str] = None) -> structlog.BoundLogger:
    """
    Set up a structured logger with the specified name and log level.
    
    Args:
        name: The name of the logger
        log_level: The log level to use (defaults to INFO if not specified)
        
    Returns:
        structlog.BoundLogger: The configured structured logger instance
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()) if log_level else logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger(name) 