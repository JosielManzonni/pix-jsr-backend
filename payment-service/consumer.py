"""Payment execution consumer: claims intents and drives them to a terminal state.

``run_once`` is the single-winner loop step: it claims exactly one pending
intent (the claim transaction has already committed when the repository call
returns — no database lock survives it), executes OUTSIDE any transaction-
holding window, then persists the outcome. A failed or raising executor call
is finalized as ``failed`` with an internal reason stored on the intent row;
there is NO internal retry — re-running the consumer picks up the next intent.
"""

from __future__ import annotations

from enum import Enum

from models import PaymentStatus
from executor import Executor, ExecutorPayload


class Outcome(Enum):
    empty = "empty"  # no pending intent
    confirmed = "confirmed"
    failed = "failed"


class Consumer:
    """One claim-execute-finalize cycle per ``run_once`` call."""

    def __init__(self, repository, executor: Executor) -> None:
        self._repository = repository
        self._executor = executor

    def run_once(self) -> Outcome:
        intent = self._repository.claim_next_pending_intent()
        if intent is None:
            return Outcome.empty
        payment = self._repository.get_payment(intent.user_id, intent.payment_id)
        payload = ExecutorPayload(
            payment.id, payment.payeePixKey, payment.amount, payment.description
        )
        try:
            result = self._executor.execute(payload)
        except Exception as exc:  # executor out of contract: treat as failure
            ok, reason = False, f"executor error: {type(exc).__name__}"
        else:
            ok, reason = result.ok, result.reason
        if ok:
            self._repository.finalize_intent(
                intent.intent_id, intent.payment_id, PaymentStatus.confirmed
            )
            return Outcome.confirmed
        self._repository.finalize_intent(
            intent.intent_id, intent.payment_id, PaymentStatus.failed,
            failure_reason=reason,
        )
        return Outcome.failed