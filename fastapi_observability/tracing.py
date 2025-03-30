from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

def setup_tracing(app: FastAPI, service_name: str = "fastapi-app", otlp_endpoint: str = "http://otel-collector:4317", excluded_endpoints: list = None) -> None:
    """Setup OpenTelemetry tracing for FastAPI application"""
    # Create a TracerProvider
    resource = Resource.create({"service.name": service_name})
    tracer_provider = TracerProvider(resource=resource)
    
    # Create an OTLP Span Exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    
    # Add BatchSpanProcessor to the TracerProvider
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set the TracerProvider as the global tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    # Convert excluded_endpoints list to comma-separated string
    excluded_urls = ",".join(excluded_endpoints) if excluded_endpoints else ""
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, excluded_urls=excluded_urls) 