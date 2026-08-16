from __future__ import annotations

import asyncio
import logging
import os
import socket
import threading
from pathlib import Path

import time

import httpx
import pytest
import yaml

import main
from openpix_observability import StructuredFormatter, get_metrics
from openpix_observability import server as server_module

CONTRACT = yaml.safe_load(
    Path(__file__)
    .resolve()
    .parents[1]
    .joinpath("contracts", "openapi.yaml")
    .read_text()
)


def api_get(app, path: str, headers: dict[str, str] | None = None) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get(path, headers=headers or {})

    return asyncio.run(request())


def _capture_access_logs(path: str, headers: dict[str, str]) -> list[str]:
    captured: list[str] = []
    handler = logging.Handler()
    handler.setFormatter(StructuredFormatter())
    handler.emit = lambda record: captured.append(handler.format(record))
    logger = logging.getLogger("openpix.access")
    logger.handlers = [handler]
    logger.propagate = False
    try:
        api_get(main.app, path, headers)
    finally:
        logger.handlers = []
        logger.propagate = True
    return captured


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_structured_logging_active_at_import():
    """configure_logging() runs at import so uvicorn main:app keeps trace ids."""
    root = logging.getLogger()
    assert any(
        isinstance(handler.formatter, StructuredFormatter) for handler in root.handlers
    )


def test_health_returns_ok():
    response = api_get(main.app, "/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok():
    response = api_get(main.app, "/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/health", "/ready"])
def test_probes_never_cached(path):
    response = api_get(main.app, path)
    assert "cache-control" not in response.headers
    assert "etag" not in response.headers


def test_probes_require_no_headers():
    response = api_get(main.app, "/health")
    assert response.status_code == 200


def test_openapi_served_equals_contract():
    assert main.app.openapi() == CONTRACT


def test_contract_has_no_metrics_path():
    assert "/metrics" not in CONTRACT["paths"]
    assert "/metrics" not in main.app.openapi()["paths"]


def test_metrics_surface_is_separate_and_uncontracted():
    api_get(main.app, "/health")  # middleware records on the default registry
    response = api_get(get_metrics().app, "/metrics")
    assert response.status_code == 200
    assert (
        response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    )
    assert "http_requests_total" in response.text


def test_request_records_operation_id_and_log_trace_ids():
    lines = _capture_access_logs(
        "/health",
        {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
            "X-Correlation-ID": "corr-789",
        },
    )
    assert len(lines) == 1
    assert "trace_id=4bf92f3577b34da6a3ce929d0e0e4736" in lines[0]
    assert "correlation_id=corr-789" in lines[0]


def test_serve_runs_api_and_metrics_listeners():
    api_port, metrics_port = _free_port(), _free_port()
    old = {key: os.environ.get(key) for key in ("APP_HOST", "APP_PORT", "METRICS_PORT")}
    os.environ["APP_HOST"] = "127.0.0.1"
    os.environ["APP_PORT"] = str(api_port)
    os.environ["METRICS_PORT"] = str(metrics_port)

    def run() -> None:
        main.serve(main.app)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        api_ready = False
        metrics_ready = False
        for _ in range(100):
            if not api_ready:
                try:
                    with httpx.Client(timeout=0.5) as client:
                        response = client.get(f"http://127.0.0.1:{api_port}/health")
                    api_ready = response.status_code == 200
                except httpx.HTTPError:
                    pass
            if not metrics_ready:
                try:
                    with httpx.Client(timeout=0.5) as client:
                        response = client.get(
                            f"http://127.0.0.1:{metrics_port}/metrics"
                        )
                    metrics_ready = (
                        response.status_code == 200
                        and "http_requests_total" in response.text
                    )
                except httpx.HTTPError:
                    pass
            if api_ready and metrics_ready:
                break
            time.sleep(0.1)
        assert api_ready, "API listener did not become ready"
        assert metrics_ready, "metrics listener did not become ready"
    finally:
        running = server_module.get_servers()
        assert running is not None
        api, metrics = running
        api.should_exit = True
        metrics.should_exit = True
        thread.join(timeout=5)
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
