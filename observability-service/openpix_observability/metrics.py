from __future__ import annotations

from prometheus_client import (
    GCCollector,
    Counter,
    Histogram,
    PlatformCollector,
    ProcessCollector,
    REGISTRY,
    CollectorRegistry,
    make_asgi_app,
)


class Metrics:
    """Bounded metric set: HTTP requests keyed by OpenAPI operation id.

    Labels come from a bounded set (operation_id only); correlation ids and
    business identifiers never become labels (RFC data policy). The default
    registry also carries the process, platform, and GC collectors; tests can
    pass an isolated CollectorRegistry.
    """

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self._registry = registry if registry is not None else REGISTRY
        if registry is not None:
            # A fresh registry has no default collectors; mirror production.
            GCCollector(registry=self._registry)
            PlatformCollector(registry=self._registry)
            ProcessCollector(registry=self._registry)
        self.requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests served",
            ["operation_id"],
            registry=self._registry,
        )
        self.request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["operation_id"],
            registry=self._registry,
        )
        self.app = make_asgi_app(self._registry)


_default: Metrics | None = None


def get_metrics() -> Metrics:
    """Process-wide default metrics instance (prometheus metrics are global)."""
    global _default
    if _default is None:
        _default = Metrics()
    return _default
