from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

import main
from repository import SqlitePayments

CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "openapi.yaml"
API_KEY = "test-key"
HEADERS = {"X-API-Key": API_KEY, "Idempotency-Key": "request-1"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENPIX_API_KEYS", f"{API_KEY}:user-1,other-key:user-2")
    monkeypatch.setenv("OPENPIX_CONSUMER_ENABLED", "0")
    main.repository = SqlitePayments(tmp_path / "payments.db")
    with TestClient(main.app) as test_client:
        yield test_client


def assert_problem(response, status: int, code: str) -> None:
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == status
    assert body["code"] == code
    assert body["type"].startswith("https://openpix.dev/problems/")
    assert body["title"]
    assert body["detail"]
    assert body["correlationId"] == response.headers["X-Correlation-ID"]
    assert response.headers["Cache-Control"] == "no-store"


def create(client, *, key="request-1", user_key=API_KEY, amount="12.34"):
    return client.post(
        "/payments",
        headers={"X-API-Key": user_key, "Idempotency-Key": key},
        json={"payeePixKey": "pix@example.com", "amount": amount},
    )


def test_payment_auth_rejects_missing_and_unknown_api_keys(client):
    missing = client.post("/payments", headers={"Idempotency-Key": "k"}, json={})
    assert_problem(missing, 401, "PAYMENT_UNAUTHENTICATED")

    unknown = client.post(
        "/payments",
        headers={"X-API-Key": "unknown", "Idempotency-Key": "k"},
        json={},
    )
    assert_problem(unknown, 401, "PAYMENT_UNAUTHENTICATED")


def test_create_fingerprint_is_canonical_across_json_field_order(client):
    first = client.post(
        "/payments",
        headers={"X-API-Key": API_KEY, "Idempotency-Key": "canonical"},
        json={"amount": "12.34", "payeePixKey": "pix@example.com"},
    )
    replay = client.post(
        "/payments",
        headers={"X-API-Key": API_KEY, "Idempotency-Key": "canonical"},
        json={"payeePixKey": "pix@example.com", "amount": "12.34", "description": None},
    )
    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.json() == first.json()


def test_create_replay_conflict_and_no_store(client):
    first = create(client)
    assert first.status_code == 201
    assert first.headers["Cache-Control"] == "no-store"
    payment = first.json()
    assert payment["status"] == "created"
    assert payment["amount"] == "12.34"
    assert payment["id"] and payment["createdAt"] and payment["updatedAt"]

    replay = create(client)
    assert replay.status_code == 200
    assert replay.json() == payment

    conflict = create(client, amount="12.35")
    assert_problem(conflict, 409, "PAYMENT_IDEMPOTENCY_CONFLICT")


def test_create_validates_headers_body_shape_and_strict_money(client):
    missing_key = client.post(
        "/payments", headers={"X-API-Key": API_KEY}, json={"amount": "1.00"}
    )
    assert_problem(missing_key, 422, "PAYMENT_VALIDATION_FAILED")

    missing_body = client.post("/payments", headers=HEADERS)
    assert_problem(missing_body, 400, "PAYMENT_INVALID_REQUEST")

    malformed = client.post(
        "/payments",
        headers={**HEADERS, "Content-Type": "application/json"},
        content='{"amount":',
    )
    assert_problem(malformed, 400, "PAYMENT_INVALID_REQUEST")

    for body in (
        {"payeePixKey": "pix@example.com", "amount": 12.34},
        {"payeePixKey": "pix@example.com", "amount": "0.00"},
        {"payeePixKey": "pix@example.com", "amount": "10000000.00"},
        {"payeePixKey": "pix@example.com", "amount": "12.3"},
        {
            "payeePixKey": "pix@example.com",
            "amount": "12.34",
            "brCode": "000201010212",
        },
    ):
        response = client.post(
            "/payments", headers={**HEADERS, "Idempotency-Key": json.dumps(body)}, json=body
        )
        assert_problem(response, 422, "PAYMENT_VALIDATION_FAILED")


def test_get_payment_is_authenticated_and_scoped(client):
    created = create(client).json()
    payment_id = created["id"]

    fetched = client.get(f"/payments/{payment_id}", headers={"X-API-Key": API_KEY})
    assert fetched.status_code == 200
    assert fetched.json() == created
    assert fetched.headers["Cache-Control"] == "no-store"

    other = client.get(f"/payments/{payment_id}", headers={"X-API-Key": "other-key"})
    assert_problem(other, 404, "PAYMENT_NOT_FOUND")

    missing = client.get("/payments/no-such-payment", headers={"X-API-Key": API_KEY})
    assert_problem(missing, 404, "PAYMENT_NOT_FOUND")

    unauthenticated = client.get(f"/payments/{payment_id}")
    assert_problem(unauthenticated, 401, "PAYMENT_UNAUTHENTICATED")


def test_query_history_page_scope_and_limit_validation(client):
    first = create(client, key="first").json()
    second = create(client, key="second").json()
    create(client, key="other", user_key="other-key")

    page = client.request("QUERY", "/payments/history", headers={"X-API-Key": API_KEY})
    assert page.status_code == 200
    assert page.headers["Cache-Control"] == "no-store"
    assert set(page.json()) == {"items", "nextCursor"}
    assert [item["id"] for item in page.json()["items"]] == [second["id"], first["id"]]
    assert all(item["status"] == "created" for item in page.json()["items"])

    for limit in (0, 101):
        response = client.request(
            "QUERY",
            "/payments/history",
            headers={"X-API-Key": API_KEY},
            json={"limit": limit},
        )
        assert_problem(response, 422, "PAYMENT_VALIDATION_FAILED")

    unauthenticated = client.request("QUERY", "/payments/history")
    assert_problem(unauthenticated, 401, "PAYMENT_UNAUTHENTICATED")


def test_history_declared_post_is_not_served(client):
    response = client.post("/payments/history", headers={"X-API-Key": API_KEY})
    assert_problem(response, 405, "PAYMENT_METHOD_NOT_ALLOWED")


def test_correlation_trace_health_ready_and_metrics_surface(client):
    response = client.get(
        "/health",
        headers={
            "X-Correlation-ID": "client-correlation",
            "traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Correlation-ID"] == "client-correlation"
    assert response.headers["traceparent"].startswith("00-0123456789abcdef0123456789abcdef-")

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}

    metrics = TestClient(main.metrics_app).get("/")
    assert metrics.status_code == 200
    assert "openpix_http_requests_total" in metrics.text
    assert "/metrics" not in {route.path for route in main.app.routes}


def test_payment_logs_do_not_contain_sensitive_values(client, caplog):
    caplog.set_level("INFO", logger="openpix.payment")
    response = client.post(
        "/payments",
        headers={
            "X-API-Key": API_KEY,
            "Idempotency-Key": "secret-idempotency-key",
            "X-Correlation-ID": "safe-correlation-id",
        },
        json={"payeePixKey": "secret-pix-key", "amount": "12.34"},
    )
    assert response.status_code == 201
    logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "secret-idempotency-key" not in logs
    assert "secret-pix-key" not in logs
    assert response.json()["id"] not in logs
    assert "safe-correlation-id" in logs
    assert "12.34" not in logs
    assert "user-1" not in logs


def test_served_openapi_is_the_contract_and_history_is_query_at_runtime():
    response = TestClient(main.app).get("/openapi.json")
    assert response.status_code == 200
    served = response.json()
    assert served == yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert served["paths"]["/payments/history"]["post"]["x-runtime-method"] == "QUERY"
