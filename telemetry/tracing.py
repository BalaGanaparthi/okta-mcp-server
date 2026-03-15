"""
OpenTelemetry distributed tracing configuration.

This module sets up OpenTelemetry instrumentation for the MCP server.
"""

from typing import Optional
from contextlib import contextmanager
import functools

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.trace import Status, StatusCode, Span

from config import OTelConfig
from utils.logging import LoggerMixin


class TelemetryManager(LoggerMixin):
    """
    Manages OpenTelemetry tracing configuration.

    Provides utilities for instrumenting code with distributed tracing.
    """

    def __init__(self, config: OTelConfig):
        """
        Initialize telemetry manager.

        Args:
            config: OpenTelemetry configuration
        """
        self.config = config
        self.tracer: Optional[trace.Tracer] = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize OpenTelemetry tracing."""
        if not self.config.enabled:
            self.logger.info("telemetry_disabled")
            return

        try:
            # Create resource
            resource = Resource(attributes={
                SERVICE_NAME: self.config.service_name
            })

            # Create tracer provider
            provider = TracerProvider(resource=resource)

            # Create OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.config.exporter_otlp_endpoint,
                insecure=True  # Use insecure for local development
            )

            # Add span processor
            span_processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(span_processor)

            # Set global tracer provider
            trace.set_tracer_provider(provider)

            # Instrument HTTPX
            HTTPXClientInstrumentor().instrument()

            # Get tracer
            self.tracer = trace.get_tracer(__name__)

            self._initialized = True
            self.logger.info(
                "telemetry_initialized",
                service_name=self.config.service_name,
                endpoint=self.config.exporter_otlp_endpoint
            )

        except Exception as e:
            self.logger.error("telemetry_init_failed", error=str(e))
            # Don't fail if telemetry setup fails
            self._initialized = False

    def is_enabled(self) -> bool:
        """
        Check if telemetry is enabled and initialized.

        Returns:
            True if telemetry is active
        """
        return self._initialized and self.tracer is not None

    @contextmanager
    def trace_span(
        self,
        name: str,
        attributes: Optional[dict] = None
    ):
        """
        Context manager for creating a trace span.

        Args:
            name: Span name
            attributes: Span attributes

        Yields:
            Span object
        """
        if not self.is_enabled():
            yield None
            return

        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                span.set_attributes(attributes)

            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def trace_function(self, name: Optional[str] = None):
        """
        Decorator to trace a function.

        Args:
            name: Span name (defaults to function name)

        Returns:
            Decorated function
        """
        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                span_name = name or f"{func.__module__}.{func.__name__}"

                if not self.is_enabled():
                    return await func(*args, **kwargs)

                with self.tracer.start_as_current_span(span_name) as span:
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                span_name = name or f"{func.__module__}.{func.__name__}"

                if not self.is_enabled():
                    return func(*args, **kwargs)

                with self.tracer.start_as_current_span(span_name) as span:
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def add_span_attribute(self, key: str, value: any) -> None:
        """
        Add attribute to current span.

        Args:
            key: Attribute key
            value: Attribute value
        """
        if not self.is_enabled():
            return

        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute(key, value)

    def add_span_event(self, name: str, attributes: Optional[dict] = None) -> None:
        """
        Add event to current span.

        Args:
            name: Event name
            attributes: Event attributes
        """
        if not self.is_enabled():
            return

        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes=attributes or {})


# Global telemetry manager instance
_telemetry_manager: Optional[TelemetryManager] = None


def get_telemetry_manager() -> Optional[TelemetryManager]:
    """
    Get the global telemetry manager instance.

    Returns:
        TelemetryManager instance or None if not initialized
    """
    return _telemetry_manager


def initialize_telemetry(config: OTelConfig) -> TelemetryManager:
    """
    Initialize the global telemetry manager.

    Args:
        config: OpenTelemetry configuration

    Returns:
        Initialized telemetry manager
    """
    global _telemetry_manager
    _telemetry_manager = TelemetryManager(config)
    _telemetry_manager.initialize()
    return _telemetry_manager


def trace_mcp_tool(tool_name: str):
    """
    Decorator specifically for MCP tool tracing.

    Args:
        tool_name: Name of the MCP tool

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_telemetry_manager()
            if not manager or not manager.is_enabled():
                return await func(*args, **kwargs)

            with manager.trace_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": tool_name}
            ):
                return await func(*args, **kwargs)

        return wrapper
    return decorator


def trace_okta_api_call(operation: str):
    """
    Decorator for tracing Okta API calls.

    Args:
        operation: API operation name

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_telemetry_manager()
            if not manager or not manager.is_enabled():
                return await func(*args, **kwargs)

            with manager.trace_span(
                "okta.api.request",
                attributes={"okta.operation": operation}
            ):
                return await func(*args, **kwargs)

        return wrapper
    return decorator


def trace_cache_operation(operation: str):
    """
    Decorator for tracing cache operations.

    Args:
        operation: Cache operation (get, set, delete, etc.)

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_telemetry_manager()
            if not manager or not manager.is_enabled():
                return await func(*args, **kwargs)

            with manager.trace_span(
                "cache.operation",
                attributes={"cache.operation": operation}
            ) as span:
                result = await func(*args, **kwargs)

                # Add hit/miss info for get operations
                if operation == "get" and span:
                    span.set_attribute("cache.hit", result is not None)

                return result

        return wrapper
    return decorator
