from __future__ import annotations

from datetime import UTC, datetime

import pytest

from models import Payment, PaymentStatus
from payment import InvalidTransitionError, apply_transition


def make_payment(status: PaymentStatus = PaymentStatus.created) -> Payment:
    return Payment(
        id="payment-123",
        status=status,
        payeePixKey="12345678909",
        amount="1234.56",
        description=None,
        createdAt=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        updatedAt=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
    )


def test_payment_starts_created():
    assert make_payment().status is PaymentStatus.created


def test_created_to_confirmed():
    payment = make_payment()
    apply_transition(payment, PaymentStatus.confirmed)
    assert payment.status is PaymentStatus.confirmed


def test_created_to_failed():
    payment = make_payment()
    apply_transition(payment, PaymentStatus.failed)
    assert payment.status is PaymentStatus.failed


def test_confirmed_is_terminal():
    payment = make_payment(PaymentStatus.confirmed)
    with pytest.raises(InvalidTransitionError):
        apply_transition(payment, PaymentStatus.failed)
    assert payment.status is PaymentStatus.confirmed


def test_failed_is_terminal():
    payment = make_payment(PaymentStatus.failed)
    with pytest.raises(InvalidTransitionError):
        apply_transition(payment, PaymentStatus.created)
    assert payment.status is PaymentStatus.failed


def test_unknown_status_rejected():
    payment = make_payment()
    with pytest.raises(InvalidTransitionError):
        apply_transition(payment, "cancelled")
    assert payment.status is PaymentStatus.created


def test_only_payment_status_values_exist():
    values = {status.value for status in PaymentStatus}
    assert values == {"created", "confirmed", "failed"}
    assert len(values) == 3