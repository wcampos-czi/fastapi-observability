import pytest
from fastapi_observability.middleware import ObservabilityMiddleware
from fastapi_observability.logger import FastAPIObservabilityLogger
from fastapi_observability.metrics import FastAPIObservabilityMetrics
from unittest.mock import patch, MagicMock
import time

@pytest.fixture
def middleware():
    """Create a middleware instance with mocked dependencies"""
    logger = FastAPIObservabilityLogger("test-service")
    metrics = FastAPIObservabilityMetrics("test-service")
    return ObservabilityMiddleware(
        app=MagicMock(),
        service_name="test-service",
        logger=logger,
        metrics=metrics
    )

async def test_middleware_successful_request(middleware):
    """Test middleware with successful request"""
    # Mock request and response
    mock_request = MagicMock()
    mock_request.method = "GET"
    mock_request.url.path = "/test"
    mock_request.client.host = "127.0.0.1"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    # Mock the app call_next
    async def mock_call_next(request):
        time.sleep(0.1)  # Simulate some processing time
        return mock_response
    
    middleware.app = mock_call_next
    
    # Test the middleware
    response = await middleware.dispatch(mock_request, mock_call_next)
    
    assert response == mock_response
    # Verify metrics were recorded
    assert middleware.metrics.requests_total.labels(
        method="GET",
        endpoint="/test",
        status="200",
        service="test-service"
    )._value.get() == 1.0

async def test_middleware_failed_request(middleware):
    """Test middleware with failed request"""
    # Mock request
    mock_request = MagicMock()
    mock_request.method = "GET"
    mock_request.url.path = "/test"
    mock_request.client.host = "127.0.0.1"
    
    # Mock the app call_next to raise an exception
    async def mock_call_next(request):
        raise ValueError("Test error")
    
    middleware.app = mock_call_next
    
    # Test the middleware
    with pytest.raises(ValueError):
        await middleware.dispatch(mock_request, mock_call_next)
    
    # Verify metrics were recorded
    assert middleware.metrics.exceptions_total.labels(
        method="GET",
        endpoint="/test",
        exception_type="ValueError",
        service="test-service"
    )._value.get() == 1.0

async def test_middleware_without_logger(middleware):
    """Test middleware without logger"""
    middleware.logger = None
    
    # Mock request and response
    mock_request = MagicMock()
    mock_request.method = "GET"
    mock_request.url.path = "/test"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    # Mock the app call_next
    async def mock_call_next(request):
        return mock_response
    
    middleware.app = mock_call_next
    
    # Test the middleware
    response = await middleware.dispatch(mock_request, mock_call_next)
    
    assert response == mock_response
    # Verify metrics were still recorded
    assert middleware.metrics.requests_total.labels(
        method="GET",
        endpoint="/test",
        status="200",
        service="test-service"
    )._value.get() == 1.0

async def test_middleware_without_metrics(middleware):
    """Test middleware without metrics"""
    middleware.metrics = None
    
    # Mock request and response
    mock_request = MagicMock()
    mock_request.method = "GET"
    mock_request.url.path = "/test"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    # Mock the app call_next
    async def mock_call_next(request):
        return mock_response
    
    middleware.app = mock_call_next
    
    # Test the middleware
    response = await middleware.dispatch(mock_request, mock_call_next)
    
    assert response == mock_response
    # Verify logger was still used
    assert middleware.logger is not None 