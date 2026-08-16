from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import httpx
import pytest
import yaml

import main
from openpix_observability import StructuredFormatter, get_metrics

BASE_HEADERS = {
    "X-App-Platform": "android",
    "X-App-Version": "1.4.2",
    "X-App-Build": "10402",
    "X-App-Package": "com.openpix.jsr",
    "X-Country-Code": "BR",
    "Accept-Language": "pt-BR",
}

CONTRACT = yaml.safe_load(
    Path(__file__)
    .resolve()
    .parents[1]
    .joinpath("contracts", "openapi.yaml")
    .read_text()
)


def api_get(path: str, headers: dict[str, str] | None = None) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
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
        api_get(path, headers)
    finally:
        logger.handlers = []
        logger.propagate = True
    return captured


def test_health_returns_ok_without_context_headers():
    response = api_get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok_without_context_headers():
    response = api_get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/health", "/ready"])
def test_probes_never_cached(path):
    response = api_get(path)
    assert "cache-control" not in response.headers
    assert "etag" not in response.headers


def test_contract_declares_probe_paths():
    assert "getHealth" in str(CONTRACT["paths"]["/health"]["get"]["operationId"])
    assert "getReady" in str(CONTRACT["paths"]["/ready"]["get"]["operationId"])
    assert "/metrics" not in CONTRACT["paths"]


def test_served_openapi_includes_probe_paths():
    served = main.app.openapi()
    assert "/health" in served["paths"]
    assert "/ready" in served["paths"]
    assert "/metrics" not in served["paths"]


def test_business_endpoint_unchanged():
    response = api_get(
        "/mobile/v1/configuration", BASE_HEADERS | {"X-Correlation-ID": "corr-sdui"}
    )
    assert response.status_code == 200
    assert response.json()["contractVersion"] == 1
    assert response.headers["x-correlation-id"] == "corr-sdui"
    assert response.headers["cache-control"] == "private, max-age=300"


def test_metrics_record_business_operation_id():
    api_get("/mobile/v1/configuration", BASE_HEADERS)
    body = get_metrics().app
    response = api_get_path(body, "/metrics")
    assert 'http_requests_total{operation_id="getMobileConfiguration"}' in response.text


def api_get_path(app, path: str) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get(path)

    return asyncio.run(request())


def test_access_log_carries_trace_and_correlation_ids():
    lines = _capture_access_logs(
        "/mobile/v1/configuration",
        BASE_HEADERS
        | {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
            "X-Correlation-ID": "corr-trace",
        },
    )
    assert len(lines) == 1
    assert "trace_id=4bf92f3577b34da6a3ce929d0e0e4736" in lines[0]
    assert "correlation_id=corr-trace" in lines[0]


def test_metrics_contain_no_correlation_or_request_ids():
    api_get(
        "/mobile/v1/configuration", BASE_HEADERS | {"X-Correlation-ID": "secret-corr"}
    )
    response = api_get_path(get_metrics().app, "/metrics")
    assert "secret-corr" not in response.text
