from __future__ import annotations

from executor import ExecutorPayload, ExecutorResult, PedroBankFake

PAYLOAD = ExecutorPayload("p-1", "12345678909", "10.00", "bills")


def test_fake_confirms_by_default_without_side_effects():
    # Default construction is trivial: no network, no setup, no logging.
    fake = PedroBankFake()
    result = fake.execute(PAYLOAD)
    assert isinstance(result, ExecutorResult)
    assert result.ok is True
    assert result.reason is None


def test_fake_failure_injection_returns_injected_reason():
    fake = PedroBankFake(fail=True, reason="bank unavailable")
    result = fake.execute(ExecutorPayload("p-1", "12345678909", "10.00", None))
    assert result.ok is False
    assert result.reason == "bank unavailable"


def test_payload_carries_exactly_the_expected_fields():
    payload = ExecutorPayload("p-1", "12345678909", "10.00", "bills")
    assert payload.payment_id == "p-1"
    assert payload.payee_pix_key == "12345678909"
    assert payload.amount == "10.00"
    assert payload.description == "bills"