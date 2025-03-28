FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY setup.py .
COPY src/ src/

RUN pip install -e .

# Copy example application
COPY examples/feature_demo.py .

# Run the application
CMD ["python", "feature_demo.py"] 