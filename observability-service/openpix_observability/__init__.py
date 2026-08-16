"""Shared operational instrumentation for OpenPix JSR services.

Hosted by observability-service; imported by sdui-service and
decoding-service. See SOURCES.md for the verified format constants.
"""

from .logging import StructuredFormatter, configure_logging, get_correlation_id
from .metrics import Metrics, get_metrics
from .server import register_probes, serve
from .middleware import ObservabilityMiddleware
from .trace import TraceContext, extract_trace, get_trace_context

__all__ = [
    "Metrics",
    "ObservabilityMiddleware",
    "StructuredFormatter",
    "TraceContext",
    "configure_logging",
    "get_metrics",
    "extract_trace",
    "get_correlation_id",
    "get_trace_context",
    "register_probes",
    "serve",
]
