from __future__ import annotations

import logging
import time
import uuid

from .logging import reset_correlation_id, set_correlation_id
from .metrics import Metrics, get_metrics
from .trace import extract_trace, reset_trace_context, set_trace_context


class ObservabilityMiddleware:
    """ASGI middleware: trace context, correlation, and request metrics.

    Accepts or generates the W3C trace context and the correlation id,
    publishes both to contextvars for the structured formatter, and records
    request counter/duration keyed by the route's OpenAPI operationId.
    """

    def __init__(self, app, metrics: Metrics | None = None) -> None:
        self.app = app
        self.metrics = metrics or get_metrics()
        self._logger = logging.getLogger("openpix.access")
        self._logger.setLevel(logging.INFO)

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope["headers"]
        }
        trace_context = extract_trace(headers)
        trace_token = set_trace_context(trace_context)
        raw_correlation = headers.get("x-correlation-id")
        correlation = (
            raw_correlation
            if raw_correlation is not None and len(raw_correlation) <= 128
            else None
        )
        correlation_token = set_correlation_id(correlation or str(uuid.uuid4()))

        status = 500
        started = time.perf_counter()
        try:

            async def send_wrapper(message) -> None:
                nonlocal status
                if message["type"] == "http.response.start":
                    status = message["status"]
                await send(message)

            await self.app(scope, receive, send_wrapper)
        finally:
            route = scope.get("route")
            operation_id = getattr(route, "operation_id", None) or "unknown"
            self._logger.info(
                "%s %s %s",
                scope.get("method", ""),
                scope.get("path", ""),
                status,
            )
            self.metrics.requests_total.labels(operation_id).inc()
            self.metrics.request_duration.labels(operation_id).observe(
                time.perf_counter() - started
            )
            reset_trace_context(trace_token)
            reset_correlation_id(correlation_token)
