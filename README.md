# FastAPI Observability

A comprehensive observability library for FastAPI applications that integrates structlog, Prometheus metrics, and OpenTelemetry tracing.

## Features

- Structured logging with structlog
- Prometheus metrics with OpenMetrics format
- OpenTelemetry tracing with OTLP exporter
- Automatic request/response logging
- Request duration metrics
- Exception tracking
- Correlation between logs, metrics, and traces
- Feature toggles for each component

## Installation

```bash
pip install fastapi-observability
```

## Usage

Here's a simple example of how to use the library:

```python
from fastapi import FastAPI
from fastapi_observability import FastAPIObservability

app = FastAPI()

# Initialize observability with feature toggles
observability = FastAPIObservability(
    app=app,
    service_name="my-service",
    enable_structlog=True,      # Enable structured logging
    enable_prometheus=True,     # Enable Prometheus metrics
    enable_opentelemetry=True,  # Enable OpenTelemetry tracing
    otlp_endpoint="http://localhost:4317"  # Optional, defaults to localhost
)

# Get logger for custom logging
logger = observability.get_logger()

@app.get("/")
async def root():
    logger.info("handling_root_request")
    return {"message": "Hello World"}
```

## Feature Toggles

You can enable or disable each component independently:

```python
# Only enable logging
observability = FastAPIObservability(
    app=app,
    service_name="my-service",
    enable_structlog=True,
    enable_prometheus=False,
    enable_opentelemetry=False
)

# Only enable metrics
observability = FastAPIObservability(
    app=app,
    service_name="my-service",
    enable_structlog=False,
    enable_prometheus=True,
    enable_opentelemetry=False
)

# Only enable tracing
observability = FastAPIObservability(
    app=app,
    service_name="my-service",
    enable_structlog=False,
    enable_prometheus=False,
    enable_opentelemetry=True
)
```

## Configuration

### OpenTelemetry

The library automatically sets up OpenTelemetry with the following features:

- Automatic instrumentation of FastAPI
- Request/response body recording
- Request/response headers recording
- Excluded URLs (health check and metrics endpoints)
- OTLP exporter for sending traces

### Prometheus Metrics

The following metrics are automatically collected:

- `http_requests_total`: Counter of total HTTP requests
- `http_request_duration_seconds`: Histogram of request durations
- `http_exceptions_total`: Counter of exceptions

Metrics are exposed at the `/metrics` endpoint in OpenMetrics format.

### Structured Logging

Logs are automatically structured with:

- Timestamp
- Log level
- Service name
- Trace ID (when available)
- Span ID (when available)
- Request details (method, URL, status code)
- Exception details (when applicable)

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fastapi-observability.git
cd fastapi-observability
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install development dependencies:
```bash
make install
```

### Running Tests

```bash
make test
```

### Code Formatting

```bash
make format
```

### Linting

```bash
make lint
```

### Running the Demo

The repository includes a complete demo environment with Prometheus, Grafana, and OpenTelemetry Collector.

1. Start the demo environment:
```bash
make run-demo
```

2. Access the services:
- FastAPI application: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

3. Stop the demo environment:
```bash
make stop-demo
```

### Useful Make Commands

- `make install`: Install development dependencies
- `make test`: Run tests
- `make lint`: Run linters
- `make format`: Format code
- `make clean`: Clean up temporary files
- `make run-demo`: Start the demo environment
- `make stop-demo`: Stop the demo environment
- `make logs`: View container logs
- `make shell`: Open a shell in the app container
- `make grafana`: Open Grafana in browser
- `make prometheus`: Open Prometheus in browser

## Integration with Observability Stack

### Prometheus

Add the following to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'fastapi-service'
    scrape_interval: 15s
    static_configs:
      - targets: ['your-service:8000']
```

### Grafana

1. Add Prometheus as a data source
2. Add Tempo as a data source
3. Configure trace-to-metrics correlation
4. Configure trace-to-logs correlation

### OpenTelemetry Collector

Configure your OpenTelemetry Collector to receive traces from the service:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 