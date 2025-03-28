import pytest
from fastapi.testclient import TestClient
import time
import os

def test_root_endpoint(client):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello World"
    assert data["features"]["structlog"] is True
    assert data["features"]["prometheus"] is True
    assert data["features"]["opentelemetry"] is True
    assert data["features"]["loki"] is False

def test_slow_endpoint(client):
    """Test the slow endpoint"""
    start_time = time.time()
    response = client.get("/slow")
    duration = time.time() - start_time
    
    assert response.status_code == 200
    assert response.json()["message"] == "This was slow"
    assert duration >= 2.0  # Should take at least 2 seconds

def test_error_endpoint(client):
    """Test the error endpoint"""
    response = client.get("/error")
    assert response.status_code == 500
    assert response.json()["detail"] == "This is an error"

def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_metrics_endpoint(client):
    """Test the metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_requests_total" in response.text

def test_minimal_app(minimal_client):
    """Test the minimal app configuration"""
    response = minimal_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["features"]["structlog"] is False
    assert data["features"]["prometheus"] is True
    assert data["features"]["opentelemetry"] is False
    assert data["features"]["loki"] is False

def test_feature_toggles(client, monkeypatch):
    """Test feature toggles through environment variables"""
    # Test with only structlog enabled
    monkeypatch.setenv("ENABLE_STRUCTLOG", "true")
    monkeypatch.setenv("ENABLE_PROMETHEUS", "false")
    monkeypatch.setenv("ENABLE_OPENTELEMETRY", "false")
    
    response = client.get("/")
    data = response.json()
    assert data["features"]["structlog"] is True
    assert data["features"]["prometheus"] is False
    assert data["features"]["opentelemetry"] is False
    
    # Test with only prometheus enabled
    monkeypatch.setenv("ENABLE_STRUCTLOG", "false")
    monkeypatch.setenv("ENABLE_PROMETHEUS", "true")
    monkeypatch.setenv("ENABLE_OPENTELEMETRY", "false")
    
    response = client.get("/")
    data = response.json()
    assert data["features"]["structlog"] is False
    assert data["features"]["prometheus"] is True
    assert data["features"]["opentelemetry"] is False
    
    # Test with only opentelemetry enabled
    monkeypatch.setenv("ENABLE_STRUCTLOG", "false")
    monkeypatch.setenv("ENABLE_PROMETHEUS", "false")
    monkeypatch.setenv("ENABLE_OPENTELEMETRY", "true")
    
    response = client.get("/")
    data = response.json()
    assert data["features"]["structlog"] is False
    assert data["features"]["prometheus"] is False
    assert data["features"]["opentelemetry"] is True 