from __future__ import annotations

import sqlite3
import threading

from models import PaymentStatus
from repository import SqlitePayments
from executor import PedroBankFake
from consumer import Consumer, Outcome

DB = "payments.db"
U1 = "user-1"
PIX = "12345678909"


def make_repo(tmp_path) -> SqlitePayments:
    return SqlitePayments(tmp_path / DB)


def create_payment(repo, key="key-1", fingerprint="fingerprint-1"):
    return repo.create_payment(U1, key, fingerprint, PIX, "10.00", None)


def intent_status_and_reason(tmp_path) -> tuple | None:
    con = sqlite3.connect(tmp_path / DB)
    try:
        return con.execute(
            "SELECT status, reason FROM intents ORDER BY intent_id"
        ).fetchone()
    finally:
        con.close()


class _RecordingExecutor:
    """Logs every execute into ``events``; optionally blocks mid-call."""

    def __init__(self, events, fail=False, reason=None, started=None, release=None):
        self.events = events
        self.fake = PedroBankFake(fail=fail, reason=reason)
        self.started = started
        self.release = release

    def execute(self, payload):
        self.events.append("execute")
        if self.started is not None:
            self.started.set()
        if self.release is not None:
            self.release.wait(timeout=5)
        return self.fake.execute(payload)

    @property
    def calls(self):
        return self.events.count("execute")


class _RecordingRepo:
    """Logs claim (after the claim tx committed) and finalize around the repo."""

    def __init__(self, repo, events):
        self.repo = repo
        self.events = events

    def claim_next_pending_intent(self):
        intent = self.repo.claim_next_pending_intent()
        self.events.append("claim")  # appends only after claim tx committed+closed
        return intent

    def get_payment(self, user_id, payment_id):
        return self.repo.get_payment(user_id, payment_id)

    def finalize_intent(self, *args, **kwargs):
        self.events.append("finalize")
        return self.repo.finalize_intent(*args, **kwargs)


class ExecutiveFailure(RuntimeError):
    pass


class _RaisingExecutor:
    def execute(self, payload):
        raise ExecutiveFailure("third-party outage")


def test_run_once_with_nothing_pending_reports_empty_and_skips_executor(tmp_path):
    repo = make_repo(tmp_path)
    executor = _RecordingExecutor([])
    assert Consumer(repo, executor).run_once() is Outcome.empty
    assert executor.events == []


def test_run_once_confirms_payment_and_consumes_intent(tmp_path):
    repo = make_repo(tmp_path)
    created = create_payment(repo)
    executor = _RecordingExecutor([])
    consumer = Consumer(repo, executor)
    assert consumer.run_once() is Outcome.confirmed
    assert executor.calls == 1
    assert repo.get_payment(U1, created.payment.id).status is PaymentStatus.confirmed
    assert intent_status_and_reason(tmp_path) == ("done", None)


def test_run_once_with_failure_fails_payment_consumes_intent_no_retry(tmp_path):
    repo = make_repo(tmp_path)
    created = create_payment(repo)
    consumer = Consumer(repo, _RecordingExecutor([], fail=True, reason="bank unavailable"))
    assert consumer.run_once() is Outcome.failed
    assert repo.get_payment(U1, created.payment.id).status is PaymentStatus.failed
    assert intent_status_and_reason(tmp_path) == ("done", "bank unavailable")
    # Intent consumed: a follow-up run must report empty, no internal retry.
    assert Consumer(repo, _RecordingExecutor([])).run_once() is Outcome.empty


def test_run_once_treats_executor_exception_as_failure(tmp_path):
    repo = make_repo(tmp_path)
    created = create_payment(repo)
    assert Consumer(repo, _RaisingExecutor()).run_once() is Outcome.failed
    assert repo.get_payment(U1, created.payment.id).status is PaymentStatus.failed
    status, reason = intent_status_and_reason(tmp_path)
    assert status == "done"
    assert "ExecutiveFailure" in reason  # generic class name, no sensitive data
    assert Consumer(repo, _RaisingExecutor()).run_once() is Outcome.empty


def test_run_once_executes_after_claim_without_holding_db_lock(tmp_path):
    repo = make_repo(tmp_path)
    created = create_payment(repo)
    events = []
    started = threading.Event()
    release = threading.Event()
    consumer = Consumer(_RecordingRepo(repo, events), _RecordingExecutor(
        events, started=started, release=release
    ))
    results = []

    def consume():
        results.append(consumer.run_once())

    thread = threading.Thread(target=consume)
    thread.start()
    assert started.wait(timeout=5)  # execute() is in flight
    # A concurrent writer must proceed: the claim transaction is already
    # committed, so the consumer holds no database lock during execute.
    concurrent = create_payment(repo, key="key-2", fingerprint="fingerprint-2")
    assert concurrent.payment.status is PaymentStatus.created
    release.set()
    thread.join(timeout=5)
    assert results == [Outcome.confirmed]
    assert repo.get_payment(U1, created.payment.id).status is PaymentStatus.confirmed
    assert events.index("claim") < events.index("execute") < events.index("finalize")