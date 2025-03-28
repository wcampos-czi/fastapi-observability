from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentation
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

def setup_telemetry(service_name: str, otlp_endpoint: str = "http://localhost:4317"):
    """Setup OpenTelemetry instrumentation for FastAPI"""
    
    # Create a resource with service name
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
    })
    
    # Create a tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Create an OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    
    # Create a span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    
    # Add the span processor to the tracer provider
    tracer_provider.add_span_processor(span_processor)
    
    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    return tracer_provider

def instrument_fastapi(app, tracer_provider=None):
    """Instrument FastAPI application with OpenTelemetry"""
    FastAPIInstrumentation.instrument(
        app,
        tracer_provider=tracer_provider,
        excluded_urls="health,metrics",  # Exclude health check and metrics endpoints
        record_request_body=True,  # Record request body in spans
        record_response_body=True,  # Record response body in spans
        record_request_headers=True,  # Record request headers in spans
        record_response_headers=True,  # Record response headers in spans
    ) 