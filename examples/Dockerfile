FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the library files
COPY setup.py .
COPY fastapi_observability fastapi_observability/
COPY examples/ examples/

# Install the library in development mode
RUN pip install -e . 