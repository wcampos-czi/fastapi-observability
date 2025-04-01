from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

def setup_telemetry(service_name: str, otlp_endpoint: str = "http://localhost:4317"):
    """Setup OpenTelemetry instrumentation for FastAPI"""
    
    # Create a resource with service name
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_NAMESPACE: "fastapi-observability",
    })
    
    # Create a tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Create an OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    
    # Create span processors
    otlp_processor = BatchSpanProcessor(otlp_exporter)
    console_processor = BatchSpanProcessor(ConsoleSpanExporter())
    
    # Add the span processors to the tracer provider
    tracer_provider.add_span_processor(otlp_processor)
    tracer_provider.add_span_processor(console_processor)
    
    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    # Instrument common HTTP libraries
    RequestsInstrumentor().instrument()
    instrument_httpx(tracer_provider=tracer_provider)
    
    return tracer_provider

def instrument_fastapi(app, tracer_provider=None, excluded_urls="health,metrics"):
    """Instrument FastAPI application with OpenTelemetry"""
    # Check if the app is already instrumented
    if not hasattr(app, "_is_instrumented"):
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=tracer_provider,
            excluded_urls=excluded_urls,
        )
        # Mark the app as instrumented
        setattr(app, "_is_instrumented", True)

def instrument_httpx(tracer_provider=None, capture_headers=False, request_hook=None, response_hook=None):
    """Instrument HTTPX client with OpenTelemetry
    
    Args:
        tracer_provider: Optional tracer provider
        capture_headers: Whether to capture HTTP headers as span attributes
        request_hook: Optional callback function called before the request is sent
        response_hook: Optional callback function called after the response is received
    """
    # Use default response hook if none provided
    if response_hook is None:
        response_hook = _client_response_hook
        
    return HTTPXClientInstrumentor().instrument(
        tracer_provider=tracer_provider,
        capture_headers=capture_headers,
        request_hook=request_hook,
        response_hook=response_hook,
    )

def _server_request_hook(span, scope):
    """Hook for adding custom attributes to server spans"""
    if span and scope:
        span.set_attribute("http.method", scope.get("method", ""))
        span.set_attribute("http.route", scope.get("path", ""))
        query_string = scope.get("query_string", b"").decode("utf-8")
        if query_string:
            span.set_attribute("http.query_string", query_string)

def _client_response_hook(span, response):
    """Hook for adding custom attributes to client spans"""
    if span and response:
        span.set_attribute("http.status_code", response.status_code)
        span.set_attribute("http.response_content_length", len(response.content) if hasattr(response, "content") else 0)
        # Add service name from response headers if available
        if hasattr(response, "headers") and "x-service-name" in response.headers:
            span.set_attribute("peer.service", response.headers["x-service-name"]) 