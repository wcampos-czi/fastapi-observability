.PHONY: install test lint format clean run-demo stop-demo run-full-demo run-minimal-demo build demo

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src/fastapi_observability

lint:
	flake8 src/fastapi_observability
	mypy src/fastapi_observability
	isort --check-only src/fastapi_observability
	black --check src/fastapi_observability

format:
	isort src/fastapi_observability
	black src/fastapi_observability

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

run-demo:
	docker-compose up -d

run-full-demo:
	ENABLE_LOKI=true docker-compose up -d

run-minimal-demo:
	ENABLE_LOKI=false docker-compose up -d app prometheus grafana

stop-demo:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec app /bin/bash

grafana:
	open http://localhost:3000

prometheus:
	open http://localhost:9090

tempo:
	open http://localhost:3200

loki:
	open http://localhost:3100

# Build Docker images
build:
	docker-compose build

# Run the demo environment
demo: build
	docker-compose up -d

# Clean up containers and volumes
clean:
	docker-compose down -v
	docker system prune -f

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Format code
format:
	black .
	isort .

# Run linting
lint:
	flake8 .
	mypy .
	black . --check
	isort . --check 