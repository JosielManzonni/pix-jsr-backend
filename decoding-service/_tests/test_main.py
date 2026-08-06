from __future__ import annotations

import asyncio
import logging

import httpx
import pytest
import yaml

import main
from fixtures import (
    P1_STATIC,
    P5_DYNAMIC,
    VALID_CPF,
    _dynamic,
    _dynamic_parts,
    _dynamic_vector,
)
from models import DecodeErrorCode


def _tamper_crc(payload: str) -> str:
    last = payload[-1]
    return payload[:-1] + ("0" if last != "0" else "1")


def api_post(payload: object = None, headers: dict[str, str] | None = None) -> httpx.Response:
    body = {"payload": payload} if payload is not None else {}

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.post(
                "/decode/v1/pix-payloads", json=body, headers=headers or {}
            )

    return asyncio.run(request())


def _problem_type(code: DecodeErrorCode) -> str:
    return f"https://openpix.dev/problems/{code.value.lower().replace('_', '-')}"


# --- Valid decodes ---------------------------------------------------------


def test_valid_dynamic_returns_200():
    response = api_post(_dynamic_vector("NFeTEST0001", "12.30"))
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "dynamic"
    assert body["txid"] == "NFeTEST0001"
    assert body["amount"] == "12.30"
    assert body["key_type"] == "evp"
    assert body["location"] is None
    assert body["crc_valid"] is True


def test_valid_static_pim_11_returns_200():
    response = api_post(P1_STATIC)
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "static"
    assert body["key_type"] == "phone"
    assert body["txid"] == "PIXMP0001"


def test_valid_static_without_pim_returns_200():
    payload = _dynamic(pim=None, txid=None)
    response = api_post(payload)
    assert response.status_code == 200
    assert response.json()["mode"] == "static"
    assert response.json()["txid"] is None


def test_p5_dynamic_location_end_to_end():
    response = api_post(P5_DYNAMIC)
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "dynamic"
    assert body["key"] is None
    assert body["key_type"] is None
    assert body["location"] == "bitsorbyte.com.br/login"
    assert body["txid"] == "***"


# --- Validation errors map to decode codes (Finding 6b) --------------------


@pytest.mark.parametrize(
    ("code", "payload"),
    [
        (DecodeErrorCode.DECODING_PAYLOAD_TOO_LONG, "0" * 513),
        (DecodeErrorCode.DECODING_INVALID_CHARSET, _dynamic(name="Mer\x7fchant")),
        (DecodeErrorCode.DECODING_MALFORMED_TLV, "5A02ab"),
        (DecodeErrorCode.DECODING_CRC_MISMATCH, _tamper_crc(_dynamic())),
        (DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD, _dynamic_parts()),
        (DecodeErrorCode.DECODING_UNSUPPORTED_CURRENCY, _dynamic(currency="999")),
        (DecodeErrorCode.DECODING_INVALID_KEY, _dynamic(key="notakey!")),
        (DecodeErrorCode.DECODING_INVALID_PAYLOAD, _dynamic(pfi="02")),
    ],
)
def test_every_decode_code_returns_consistent_problem_details(code, payload):
    response = api_post(payload)
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == code.value
    assert body["type"] == _problem_type(code)
    assert body["title"] == main._TITLE_BY_CODE[code]
    assert body["status"] == 422
    assert body["correlationId"]


def test_crc_problem_type_uri_is_exact():
    response = api_post(_tamper_crc(_dynamic()))
    assert response.status_code == 422
    assert (
        response.json()["type"]
        == "https://openpix.dev/problems/decoding-crc-mismatch"
    )


# --- Request-shape failures use the context code ---------------------------

# (Finding 6c) 400 CONTEXT_INVALID_REQUEST reflects a provided correlation id
# and generates one when absent.


def test_missing_payload_field_returns_context_code():
    response = api_post(None)
    assert response.status_code == 400
    assert response.json()["code"] == "CONTEXT_INVALID_REQUEST"


def test_non_string_payload_returns_context_code():
    response = api_post(123)
    assert response.status_code == 400
    assert response.json()["code"] == "CONTEXT_INVALID_REQUEST"


def test_context_error_reflects_client_correlation():
    response = api_post(None, headers={"X-Correlation-ID": "abc-123"})
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "CONTEXT_INVALID_REQUEST"
    assert body["correlationId"] == "abc-123"
    assert response.headers["x-correlation-id"] == "abc-123"


def test_context_error_generates_correlation_when_absent():
    response = api_post(None)
    assert response.status_code == 400
    assert response.json()["code"] == "CONTEXT_INVALID_REQUEST"
    assert response.json()["correlationId"]
    assert response.headers["x-correlation-id"]


# --- Correlation -----------------------------------------------------------


def test_client_correlation_reflected_on_error():
    response = api_post("5A02ab", headers={"X-Correlation-ID": "abc-123"})
    assert response.status_code == 422
    assert response.json()["correlationId"] == "abc-123"
    assert response.headers["x-correlation-id"] == "abc-123"


def test_generated_correlation_when_absent():
    response = api_post(_dynamic())
    assert response.status_code == 200
    assert response.headers["x-correlation-id"]


# --- Boundary: payload not logged -----------------------------------------


def test_payload_not_logged(caplog):
    payload = _dynamic()
    with caplog.at_level(logging.DEBUG):
        api_post(payload)
    for record in caplog.records:
        message = record.getMessage()
        assert payload not in message
        assert VALID_CPF not in message


# --- OpenAPI contract (Finding 12) -----------------------------------------


def test_openapi_served_equals_contract():
    with open(main.CONTRACT_PATH, encoding="utf-8") as contract_file:
        contract = yaml.safe_load(contract_file)
    assert main.app.openapi() == contract
