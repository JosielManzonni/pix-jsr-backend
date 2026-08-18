"""Payment aggregate: the only place that authorizes status transitions.

A Payment exists in exactly one of ``created`` / ``confirmed`` / ``failed``.
The only transitions are ``created -> confirmed`` and ``created -> failed``;
``confirmed`` and ``failed`` are terminal and reject any further transition
without changing state.
"""

from __future__ import annotations

from models import Payment, PaymentStatus


class InvalidTransitionError(ValueError):
    """Stable domain error for any transition the aggregate does not authorize."""


_ALLOWED_TRANSITIONS = {
    PaymentStatus.created: frozenset({PaymentStatus.confirmed, PaymentStatus.failed}),
}


def apply_transition(payment: Payment, new_status: PaymentStatus) -> None:
    """Apply ``new_status`` to ``payment`` in place, or raise without changing
    state when the transition is not authorized."""
    allowed = _ALLOWED_TRANSITIONS.get(payment.status, frozenset())
    if new_status not in allowed:
        target = getattr(new_status, "value", new_status)
        raise InvalidTransitionError(
            f"Transition {payment.status.value} -> {target} is not allowed."
        )
    payment.status = new_status