from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import httpx
import pytest
import yaml

import main
from fixtures import _dynamic, _dynamic_vector
from openpix_observability import StructuredFormatter, get_metrics

CONTRACT = yaml.safe_load(
    Path(__file__)
    .resolve()
    .parents[1]
    .joinpath("contracts", "openapi.yaml")
    .read_text()
)

VALID_TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


def api_get(path: str, headers: dict[str, str] | None = None) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get(path, headers=headers or {})

    return asyncio.run(request())


def api_post(payload: object, headers: dict[str, str] | None = None) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.post(
                "/decode/v1/pix-payloads",
                json={"payload": payload},
                headers=headers or {},
            )

    return asyncio.run(request())


def api_get_path(app, path: str) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get(path)

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


def test_health_returns_ok_without_headers():
    response = api_get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok_without_headers():
    response = api_get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/health", "/ready"])
def test_probes_never_cached(path):
    response = api_get(path)
    assert "cache-control" not in response.headers
    assert "etag" not in response.headers


def test_contract_declares_probes_and_no_metrics():
    assert CONTRACT["paths"]["/health"]["get"]["operationId"] == "getHealth"
    assert CONTRACT["paths"]["/ready"]["get"]["operationId"] == "getReady"
    assert "/metrics" not in CONTRACT["paths"]


def test_openapi_served_equals_contract_with_probes():
    assert main.app.openapi() == CONTRACT


def test_business_endpoint_unchanged():
    response = api_post(_dynamic_vector("NFeTEST0001", "12.30"))
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "dynamic"
    assert body["crc_valid"] is True
    assert body["key_type"] == "evp"


def test_decode_accepts_trace_headers():
    response = api_post(
        _dynamic_vector("NFeTEST0001", "12.30"),
        headers={
            "traceparent": VALID_TRACEPARENT,
            "tracestate": "vendor=value1",
            "X-Correlation-ID": "corr-dec",
        },
    )
    assert response.status_code == 200
    assert response.headers["x-correlation-id"] == "corr-dec"


def test_metrics_record_decode_operation_id():
    api_post(_dynamic_vector("NFeTEST0001", "12.30"))
    response = api_get_path(get_metrics().app, "/metrics")
    assert 'http_requests_total{operation_id="decodePixPayload"}' in response.text


def test_access_log_carries_trace_and_correlation_ids():
    lines = _capture_access_logs(
        "/health",
        {
            "traceparent": VALID_TRACEPARENT,
            "X-Correlation-ID": "corr-log",
        },
    )
    assert len(lines) == 1
    assert "trace_id=4bf92f3577b34da6a3ce929d0e0e4736" in lines[0]
    assert "correlation_id=corr-log" in lines[0]


def test_payload_and_key_material_never_in_metrics_or_logs():
    payload = _dynamic(key="52998224725")
    captured: list[str] = []
    handler = logging.Handler()
    handler.setFormatter(StructuredFormatter())
    handler.emit = lambda record: captured.append(handler.format(record))
    logger = logging.getLogger("openpix.access")
    logger.handlers = [handler]
    logger.propagate = False
    try:
        response = api_post(payload)
    finally:
        logger.handlers = []
        logger.propagate = True
    assert response.status_code == 200

    metrics_body = api_get_path(get_metrics().app, "/metrics").text
    for artifact in (payload, "52998224725"):
        assert artifact not in " ".join(captured)
        assert artifact not in metrics_body
