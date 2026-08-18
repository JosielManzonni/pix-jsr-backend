"""Executor port and the shipped Pedro Bank fake.

The consumer talks to an :class:`Executor` port. The shipped implementation
is an in-repo fake: deterministic confirmation by default, injectable failure
for tests, zero network I/O, and it logs nothing — Pix keys, account data and
ids never leave the process.
"""

from __future__ import annotations

from typing import NamedTuple, Protocol


class ExecutorPayload(NamedTuple):
    """Minimal execution request — no user id, no idempotency key."""

    payment_id: str
    payee_pix_key: str
    amount: str
    description: str | None


class ExecutorResult(NamedTuple):
    ok: bool
    reason: str | None  # present when ok is False


class Executor(Protocol):
    """Execution port called synchronously, outside any database transaction."""

    def execute(self, payload: ExecutorPayload) -> ExecutorResult: ...


class PedroBankFake:
    """Deterministic in-repo fake: confirms unless configured to fail.

    ``fail=True`` injects a failure carrying ``reason``; the default
    configuration always confirms. No network, no logging, no state beyond
    the injected failure.
    """

    def __init__(self, fail: bool = False, reason: str | None = None) -> None:
        self._fail = fail
        self._reason = reason

    def execute(self, payload: ExecutorPayload) -> ExecutorResult:
        if self._fail:
            return ExecutorResult(ok=False, reason=self._reason)
        return ExecutorResult(ok=True, reason=None)