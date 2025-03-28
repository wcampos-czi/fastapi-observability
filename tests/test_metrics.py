import pytest
from fastapi_observability.metrics import FastAPIObservabilityMetrics
from unittest.mock import patch, MagicMock
from prometheus_client import REGISTRY, CollectorRegistry

@pytest.fixture
def metrics():
    """Create a metrics instance with a fresh registry"""
    registry = CollectorRegistry()
    return FastAPIObservabilityMetrics("test-service", registry)

def test_metrics_initialization(metrics):
    """Test metrics initialization"""
    assert metrics.service_name == "test-service"
    assert metrics.requests_total is not None
    assert metrics.request_duration_seconds is not None
    assert metrics.exceptions_total is not None

def test_get_exemplar_with_span(metrics):
    """Test getting exemplar with OpenTelemetry span"""
    # Mock OpenTelemetry span
    mock_span = MagicMock()
    mock_span.get_span_context.return_value.trace_id = b"\x01" * 16
    
    with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
        exemplar = metrics.get_exemplar()
        assert exemplar == {"trace_id": "01010101010101010101010101010101"}

def test_get_exemplar_without_span(metrics):
    """Test getting exemplar without OpenTelemetry span"""
    with patch("opentelemetry.trace.get_current_span", return_value=None):
        exemplar = metrics.get_exemplar()
        assert exemplar == {}

def test_record_request(metrics):
    """Test recording request metrics"""
    metrics.record_request("GET", "/test", 200, 0.1)
    
    # Check if metrics were recorded
    assert metrics.requests_total.labels(
        method="GET",
        endpoint="/test",
        status="200",
        service="test-service"
    )._value.get() == 1.0
    
    assert metrics.request_duration_seconds.labels(
        method="GET",
        endpoint="/test",
        service="test-service"
    )._sum.get() == 0.1

def test_record_exception(metrics):
    """Test recording exception metrics"""
    metrics.record_exception("GET", "/test", "ValueError")
    
    # Check if metrics were recorded
    assert metrics.exceptions_total.labels(
        method="GET",
        endpoint="/test",
        exception_type="ValueError",
        service="test-service"
    )._value.get() == 1.0

def test_get_metrics(metrics):
    """Test getting metrics endpoint"""
    response = metrics.get_metrics()
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_requests_total" in response.body.decode() 