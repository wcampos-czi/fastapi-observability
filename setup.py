from setuptools import setup, find_packages

setup(
    name="fastapi-observability",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "structlog>=21.1.0",
        "prometheus-client>=0.11.0",
        "opentelemetry-api>=1.7.1",
        "opentelemetry-sdk>=1.7.1",
        "opentelemetry-instrumentation-fastapi>=0.30b1",
        "opentelemetry-exporter-otlp>=1.7.1",
        "opentelemetry-instrumentation-httpx>=0.30b1"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=4.0.0",
            "mypy>=0.900",
        ],
    },
    python_requires=">=3.8",
    description="FastAPI observability library with OpenTelemetry, Prometheus, and structlog",
    author="Your Name",
    author_email="your.email@example.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 