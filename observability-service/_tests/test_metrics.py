from __future__ import annotations

import asyncio
import logging

import httpx
from fastapi import FastAPI
from prometheus_client import CollectorRegistry

from openpix_observability import Metrics, ObservabilityMiddleware, StructuredFormatter


def api_get(app, path: str, headers: dict[str, str] | None = None) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get(path, headers=headers or {})

    return asyncio.run(request())


def _scrape(metrics: Metrics) -> str:
    return api_get(metrics.app, "/metrics").text


def _capture_access_logs(app, path: str, headers: dict[str, str]) -> list[str]:
    """Request through middleware, capturing formatted openpix.access lines."""
    captured: list[str] = []
    handler = logging.Handler()
    handler.setFormatter(StructuredFormatter())
    handler.emit = lambda record: captured.append(handler.format(record))
    logger = logging.getLogger("openpix.access")
    logger.handlers = [handler]
    logger.propagate = False
    try:
        api_get(app, path, headers)
    finally:
        logger.handlers = []
        logger.propagate = True
    return captured


def test_metrics_app_serves_exposition_format():
    metrics = Metrics(registry=CollectorRegistry())
    response = api_get(metrics.app, "/metrics")
    assert response.status_code == 200
    assert (
        response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    )


def test_metrics_app_has_default_collectors():
    metrics = Metrics(registry=CollectorRegistry())
    body = _scrape(metrics)
    assert "process_cpu_seconds_total" in body
    assert "python_gc_objects_collected_total" in body


def test_metric_labels_are_bounded_operation_ids():
    metrics = Metrics(registry=CollectorRegistry())
    metrics.requests_total.labels("getHealth").inc()
    body = _scrape(metrics)
    assert 'http_requests_total{operation_id="getHealth"} 1.0' in body


def test_middleware_records_operation_id_and_no_correlation_labels():
    metrics = Metrics(registry=CollectorRegistry())
    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware, metrics=metrics)

    @app.get("/probe", operation_id="getHealth")
    async def probe():
        return {"status": "ok"}

    response = api_get(app, "/probe")
    assert response.status_code == 200

    body = _scrape(metrics)
    assert 'http_requests_total{operation_id="getHealth"} 1.0' in body
    assert 'http_request_duration_seconds_count{operation_id="getHealth"} 1.0' in body
    assert "correlation" not in body
    assert "x-correlation" not in body


def test_middleware_logs_trace_and_correlation_ids():
    metrics = Metrics(registry=CollectorRegistry())
    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware, metrics=metrics)

    @app.get("/probe", operation_id="getHealth")
    async def probe():
        return {"status": "ok"}

    lines = _capture_access_logs(
        app,
        "/probe",
        {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
            "X-Correlation-ID": "corr-456",
        },
    )

    assert len(lines) == 1
    assert "trace_id=4bf92f3577b34da6a3ce929d0e0e4736" in lines[0]
    assert "correlation_id=corr-456" in lines[0]


def test_middleware_log_generates_ids_when_absent():
    metrics = Metrics(registry=CollectorRegistry())
    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware, metrics=metrics)

    @app.get("/probe", operation_id="getHealth")
    async def probe():
        return {"status": "ok"}

    lines = _capture_access_logs(app, "/probe", {})

    assert len(lines) == 1
    assert "trace_id=" in lines[0]
    assert "correlation_id=" in lines[0]
