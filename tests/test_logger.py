import pytest
from fastapi_observability.logger import FastAPIObservabilityLogger
from unittest.mock import patch, MagicMock

def test_logger_initialization():
    """Test logger initialization"""
    logger = FastAPIObservabilityLogger("test-service")
    assert logger.service_name == "test-service"
    assert logger.logger is not None

def test_get_logger_with_span():
    """Test logger with OpenTelemetry span"""
    logger = FastAPIObservabilityLogger("test-service")
    
    # Mock OpenTelemetry span
    mock_span = MagicMock()
    mock_span.get_span_context.return_value.trace_id = b"\x01" * 16
    mock_span.get_span_context.return_value.span_id = b"\x02" * 8
    
    with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
        bound_logger = logger.get_logger()
        assert bound_logger is not None
        # Test that the logger can be used
        bound_logger.info("test message")

def test_get_logger_without_span():
    """Test logger without OpenTelemetry span"""
    logger = FastAPIObservabilityLogger("test-service")
    
    with patch("opentelemetry.trace.get_current_span", return_value=None):
        bound_logger = logger.get_logger()
        assert bound_logger is not None
        # Test that the logger can be used
        bound_logger.info("test message")

def test_log_request():
    """Test request logging"""
    logger = FastAPIObservabilityLogger("test-service")
    
    # Mock request and response
    mock_request = MagicMock()
    mock_request.method = "GET"
    mock_request.url = "http://test.com"
    mock_request.client.host = "127.0.0.1"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    # Test successful request
    logger.log_request(mock_request, mock_response)
    
    # Test failed request
    logger.log_request(mock_request, mock_response, error="Test error")

def test_log_error():
    """Test error logging"""
    logger = FastAPIObservabilityLogger("test-service")
    
    # Test error logging with context
    logger.log_error("Test error", context={"key": "value"})
    
    # Test error logging without context
    logger.log_error("Test error") 