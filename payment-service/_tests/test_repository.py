from __future__ import annotations

import base64
import sqlite3
import threading

import pytest

from models import PaymentStatus
from repository import (
    IdempotencyConflictError,
    InvalidCursorError,
    PaymentNotFoundError,
    SqlitePayments,
)

DB = "payments.db"
U1, U2 = "user-1", "user-2"
PIX = "12345678909"


def make_repo(tmp_path) -> SqlitePayments:
    return SqlitePayments(tmp_path / DB)


def create(
    repo: SqlitePayments,
    i: int = 1,
    user: str = U1,
    key: str | None = None,
    fingerprint: str | None = None,
):
    return repo.create_payment(
        user,
        key or f"key-{i}",
        fingerprint or f"fingerprint-{i}",
        PIX,
        "10.00",
        None,
    )


def row_counts(tmp_path, table: str) -> int:
    con = sqlite3.connect(tmp_path / DB)
    try:
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        con.close()


def intent_rows(tmp_path) -> list[tuple]:
    con = sqlite3.connect(tmp_path / DB)
    try:
        return [
            tuple(r)
            for r in con.execute(
                "SELECT intent_id, payment_id, status FROM intents ORDER BY intent_id"
            )
        ]
    finally:
        con.close()


def test_create_returns_created_payment_with_one_pending_intent(tmp_path):
    repo = make_repo(tmp_path)
    result = create(repo)
    assert result.replayed is False
    assert result.payment.status is PaymentStatus.created
    assert result.payment.amount == "10.00"
    assert result.payment.payeePixKey == PIX
    intents = intent_rows(tmp_path)
    assert len(intents) == 1
    _, payment_id, status = intents[0]
    assert payment_id == result.payment.id
    assert status == "pending"


def test_replay_identical_key_returns_same_payment_without_duplicates(tmp_path):
    repo = make_repo(tmp_path)
    first = create(repo, key="key-x", fingerprint="fp-x")
    second = repo.create_payment(U1, "key-x", "fp-x", PIX, "10.00", None)
    assert second.replayed is True
    assert second.payment.id == first.payment.id
    assert row_counts(tmp_path, "payments") == 1
    assert row_counts(tmp_path, "intents") == 1
    assert row_counts(tmp_path, "idempotency_keys") == 1


def test_same_key_different_fingerprint_raises_conflict(tmp_path):
    repo = make_repo(tmp_path)
    create(repo, key="key-x")
    with pytest.raises(IdempotencyConflictError):
        repo.create_payment(U1, "key-x", "different-fingerprint", PIX, "10.00", None)


def test_get_payment_returns_own_payment(tmp_path):
    repo = make_repo(tmp_path)
    created = create(repo)
    fetched = repo.get_payment(U1, created.payment.id)
    assert fetched.id == created.payment.id
    assert fetched.status is PaymentStatus.created


def test_get_payment_of_another_user_or_unknown_id_raises_not_found(tmp_path):
    repo = make_repo(tmp_path)
    created = create(repo)
    with pytest.raises(PaymentNotFoundError):
        repo.get_payment(U2, created.payment.id)
    with pytest.raises(PaymentNotFoundError):
        repo.get_payment(U1, "no-such-payment")


def test_get_by_idempotency_key_returns_payment_or_not_found(tmp_path):
    repo = make_repo(tmp_path)
    created = create(repo, key="key-x", fingerprint="fp-x")
    assert repo.get_by_idempotency_key(U1, "key-x").id == created.payment.id
    with pytest.raises(PaymentNotFoundError):
        repo.get_by_idempotency_key(U1, "no-such-key")


def test_claim_next_pending_intent_single_winner_and_none_when_empty(tmp_path):
    repo = make_repo(tmp_path)
    created = create(repo)
    claimed = repo.claim_next_pending_intent()
    assert claimed is not None
    assert claimed.payment_id == created.payment.id
    assert claimed.status == "claimed"
    assert [r[2] for r in intent_rows(tmp_path)] == ["claimed"]
    assert repo.claim_next_pending_intent() is None


def test_claim_concurrent_single_winner(tmp_path):
    repo = make_repo(tmp_path)
    create(repo)
    results: list = []
    barrier = threading.Barrier(2)

    def claim():
        barrier.wait()
        results.append(repo.claim_next_pending_intent())

    threads = [threading.Thread(target=claim) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    winners = [r for r in results if r is not None]
    assert len(winners) == 1
    assert results.count(None) == 1
    assert winners[0].status == "claimed"


def test_finalize_intent_confirms_payment_and_marks_intent_done(tmp_path):
    repo = make_repo(tmp_path)
    created = create(repo)
    claimed = repo.claim_next_pending_intent()
    repo.finalize_intent(claimed.intent_id, claimed.payment_id, PaymentStatus.confirmed)
    payment = repo.get_payment(U1, created.payment.id)
    assert payment.status is PaymentStatus.confirmed
    assert payment.updatedAt >= payment.createdAt
    assert [r[2] for r in intent_rows(tmp_path)] == ["done"]


def test_finalize_requires_the_claimed_intent_for_that_payment(tmp_path):
    repo = make_repo(tmp_path)
    first = create(repo, key="first")
    second = create(repo, key="second")
    claimed = repo.claim_next_pending_intent()
    with pytest.raises(ValueError):
        repo.finalize_intent(claimed.intent_id, second.payment.id, PaymentStatus.confirmed)
    assert repo.get_payment(U1, first.payment.id).status is PaymentStatus.created
    assert repo.get_payment(U1, second.payment.id).status is PaymentStatus.created
    assert intent_rows(tmp_path)[0][2] == "claimed"


def test_history_empty_returns_nothing(tmp_path):
    repo = make_repo(tmp_path)
    items, next_cursor = repo.list_history(U1, 50)
    assert items == []
    assert next_cursor is None


def test_history_newest_first(tmp_path):
    repo = make_repo(tmp_path)
    ids = [
        create(repo, i=n).payment.id for n in range(1, 4)
    ]
    items, next_cursor = repo.list_history(U1, 50)
    assert [p.id for p in items] == list(reversed(ids))
    assert next_cursor is None


def test_history_limit_and_cursor_traverse_all_without_dupes(tmp_path):
    repo = make_repo(tmp_path)
    ids = [create(repo, i=n).payment.id for n in range(1, 6)]
    page1, cursor1 = repo.list_history(U1, 3)
    assert len(page1) == 3
    assert cursor1 is not None
    page2, cursor2 = repo.list_history(U1, 3, cursor1)
    assert len(page2) == 2
    assert cursor2 is None
    seen = [p.id for p in page1] + [p.id for p in page2]
    assert sorted(seen) == sorted(ids)
    assert len(set(seen)) == 5


def test_history_per_user_isolation(tmp_path):
    repo = make_repo(tmp_path)
    id_u1 = create(repo, user=U1, i=1).payment.id
    id_u2 = create(repo, user=U2, i=1).payment.id
    items_u1, _ = repo.list_history(U1, 50)
    items_u2, _ = repo.list_history(U2, 50)
    assert len(items_u1) == 1 and len(items_u2) == 1
    assert items_u1[0].id == id_u1
    assert items_u2[0].id == id_u2


def test_history_cursor_stable_under_new_inserts(tmp_path):
    repo = make_repo(tmp_path)
    ids = [create(repo, i=n).payment.id for n in range(1, 6)]
    page1, cursor1 = repo.list_history(U1, 3)
    assert [p.id for p in page1] == list(reversed(ids))[:3]
    create(repo, i=6)
    create(repo, i=7)
    page2, cursor2 = repo.list_history(U1, 3, cursor1)
    assert [p.id for p in page2] == list(reversed(ids))[3:]
    assert cursor2 is None
    assert len({p.id for p in page1} | {p.id for p in page2}) == 5


def test_history_limit_bounds_rejected(tmp_path):
    repo = make_repo(tmp_path)
    with pytest.raises(ValueError):
        repo.list_history(U1, 0)
    with pytest.raises(ValueError):
        repo.list_history(U1, 101)


def test_history_invalid_cursor_rejected(tmp_path):
    repo = make_repo(tmp_path)
    with pytest.raises(InvalidCursorError):
        repo.list_history(U1, 50, "!!!not-a-cursor!!!")
    with pytest.raises(InvalidCursorError):
        repo.list_history(U1, 50, base64.urlsafe_b64encode(b"no-separator").decode())