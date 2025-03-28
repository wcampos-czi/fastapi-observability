import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_observability import FastAPIObservability
import os

@pytest.fixture
def app():
    """Create a FastAPI application with observability enabled"""
    app = FastAPI()
    observability = FastAPIObservability(
        app=app,
        service_name="test-service",
        enable_structlog=True,
        enable_prometheus=True,
        enable_opentelemetry=True,
    )
    return app

@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application"""
    return TestClient(app)

@pytest.fixture
def minimal_app():
    """Create a FastAPI application with minimal observability"""
    app = FastAPI()
    observability = FastAPIObservability(
        app=app,
        service_name="test-service",
        enable_structlog=False,
        enable_prometheus=True,
        enable_opentelemetry=False,
    )
    return app

@pytest.fixture
def minimal_client(minimal_app):
    """Create a test client for the minimal FastAPI application"""
    return TestClient(minimal_app)

@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables"""
    monkeypatch.setenv("ENABLE_STRUCTLOG", "true")
    monkeypatch.setenv("ENABLE_PROMETHEUS", "true")
    monkeypatch.setenv("ENABLE_OPENTELEMETRY", "true")
    monkeypatch.setenv("ENABLE_LOKI", "false")
    monkeypatch.setenv("OTLP_ENDPOINT", "http://localhost:4317")
    monkeypatch.setenv("LOKI_URL", "http://localhost:3100/loki/api/v1/push") 