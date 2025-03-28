import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logger import FastAPIObservabilityLogger
from .metrics import FastAPIObservabilityMetrics

class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        service_name: str,
        logger: FastAPIObservabilityLogger,
        metrics: FastAPIObservabilityMetrics,
    ):
        super().__init__(app)
        self.service_name = service_name
        self.logger = logger
        self.metrics = metrics

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log request
            self.logger.log_request(request, response)
            
            # Record metrics
            self.metrics.record_request(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            self.logger.log_error(e, context={
                "method": request.method,
                "url": str(request.url),
                "duration": duration
            })
            
            # Record exception metrics
            self.metrics.record_exception(
                method=request.method,
                endpoint=request.url.path,
                exception_type=type(e).__name__
            )
            
            raise 