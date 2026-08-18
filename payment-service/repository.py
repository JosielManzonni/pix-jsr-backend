"""Payment persistence: repository port and SQLite implementation.

Owns the three tables of the payment lifecycle contract: ``payments``
(aggregate state), ``idempotency_keys`` (per-caller idempotent creation),
and ``intents`` (execution queue). Payment creation enqueues one pending
intent in the same transaction as the payment row; the execution layer
later claims that intent with an atomic conditional update that acts as
the single-writer lock (no external coordination).

The initial data source is SQLite via the stdlib ``sqlite3`` module.
Connections are opened per call so threads never share one.
"""

from __future__ import annotations

import base64
import binascii
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import NamedTuple, Protocol

from models import Payment, PaymentStatus
from payment import apply_transition


class IdempotencyConflictError(ValueError):
    """Idempotency-Key reused with a different request body."""


class PaymentNotFoundError(KeyError):
    """Payment does not exist or belongs to another caller."""


class InvalidIntentError(ValueError):
    """An intent is not claimed for the payment being finalized."""


class InvalidCursorError(ValueError):
    """Opaque pagination cursor could not be parsed."""


class Intent(NamedTuple):
    intent_id: int
    payment_id: str
    user_id: str
    status: str
    created_at: str
    claimed_at: str | None


class PaymentOrReplay(NamedTuple):
    payment: Payment
    replayed: bool


class PaymentRepository(Protocol):
    """Port boundary for payment persistence, consumed by the API layer and
    the executor."""

    def create_payment(
        self, user_id: str, idempotency_key: str, fingerprint: str,
        payee_pix_key: str, amount: str, description: str | None,
    ) -> PaymentOrReplay: ...

    def get_payment(self, user_id: str, payment_id: str) -> Payment: ...

    def get_by_idempotency_key(self, user_id: str, key: str) -> Payment: ...

    def claim_next_pending_intent(self) -> Intent | None: ...

    def finalize_intent(
        self, intent_id: int, payment_id: str, new_status: PaymentStatus,
        failure_reason: str | None = None,
    ) -> None: ...

    def list_history(
        self, user_id: str, limit: int, cursor: str | None = None,
    ) -> tuple[list[Payment], str | None]: ...


_PAYMENT_COLUMNS = (
    "payment_id, user_id, status, payee_pix_key, amount, description, "
    "created_at, updated_at"
)
_INTENT_COLUMNS = "intent_id, payment_id, user_id, status, created_at, claimed_at"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('created','confirmed','failed')),
    payee_pix_key TEXT NOT NULL,
    amount TEXT NOT NULL,
    description TEXT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency_keys (
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    payment_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, key)
);
CREATE TABLE IF NOT EXISTS intents (
    intent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','claimed','done')),
    created_at TEXT NOT NULL,
    claimed_at TEXT NULL,
    reason TEXT NULL
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _open(db_path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=5.0)
    con.isolation_level = None  # explicit BEGIN/COMMIT; single statements auto-commit
    con.row_factory = sqlite3.Row
    return con


def _encode_cursor(created_at: str, payment_id: str) -> str:
    return base64.urlsafe_b64encode(f"{created_at}|{payment_id}".encode()).decode("ascii")


_SCHEMA_DDL = _SCHEMA


class SqlitePayments:
    """SQLite implementation of :class:`PaymentRepository`.

    ``db_path`` is a file path; ``:memory:`` is accepted but useless here
    because every operation opens its own connection (a fresh empty
    database each time). Tests must use a temporary file.
    """

    def __init__(self, db_path) -> None:
        self.db_path = db_path
        con = _open(db_path)
        try:
            con.executescript(_SCHEMA_DDL)
        finally:
            con.close()

    def create_payment(
        self, user_id: str, idempotency_key: str, fingerprint: str,
        payee_pix_key: str, amount: str, description: str | None,
    ) -> PaymentOrReplay:
        """Create a payment and enqueue its intent in one transaction.

        First use of ``(user_id, idempotency_key)`` persists the payment,
        the pending intent, and the idempotency row atomically. Replaying
        the same key with the same fingerprint returns the original payment
        with ``replayed=True``; a different fingerprint raises
        :class:`IdempotencyConflictError`.
        """
        now = _now()
        payment_id = uuid.uuid4().hex
        con = _open(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            existing = con.execute(
                "SELECT fingerprint, payment_id FROM idempotency_keys "
                "WHERE user_id = ? AND key = ?",
                (user_id, idempotency_key),
            ).fetchone()
            if existing is not None:
                con.rollback()
                if existing["fingerprint"] != fingerprint:
                    raise IdempotencyConflictError(
                        "Idempotency-Key already used with a different request."
                    )
                row = con.execute(
                    f"SELECT {_PAYMENT_COLUMNS} FROM payments "
                    "WHERE payment_id = ? AND user_id = ?",
                    (existing["payment_id"], user_id),
                ).fetchone()
                return PaymentOrReplay(self._row_to_payment(row), replayed=True)
            con.execute(
                f"INSERT INTO payments ({_PAYMENT_COLUMNS}) "
                "VALUES (?, ?, 'created', ?, ?, ?, ?, ?)",
                (payment_id, user_id, payee_pix_key, amount, description, now, now),
            )
            con.execute(
                "INSERT INTO intents (payment_id, user_id, status, created_at, claimed_at) "
                "VALUES (?, ?, 'pending', ?, NULL)",
                (payment_id, user_id, now),
            )
            con.execute(
                "INSERT INTO idempotency_keys (user_id, key, fingerprint, payment_id, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, idempotency_key, fingerprint, payment_id, now),
            )
            con.commit()
        except sqlite3.Error:
            con.rollback()
            raise
        finally:
            con.close()
        return PaymentOrReplay(
            Payment(
                id=payment_id,
                status=PaymentStatus.created,
                payeePixKey=payee_pix_key,
                amount=amount,
                description=description,
                createdAt=datetime.fromisoformat(now),
                updatedAt=datetime.fromisoformat(now),
            ),
            replayed=False,
        )

    def get_payment(self, user_id: str, payment_id: str) -> Payment:
        """Return ``user_id``'s payment, invisibly scoped to the caller."""
        con = _open(self.db_path)
        try:
            row = con.execute(
                f"SELECT {_PAYMENT_COLUMNS} FROM payments "
                "WHERE payment_id = ? AND user_id = ?",
                (payment_id, user_id),
            ).fetchone()
        finally:
            con.close()
        if row is None:
            raise PaymentNotFoundError("Payment not found.")
        return self._row_to_payment(row)

    def get_by_idempotency_key(self, user_id: str, key: str) -> Payment:
        """Return the payment created with ``key`` by ``user_id``."""
        con = _open(self.db_path)
        try:
            row = con.execute(
                f"SELECT p.{_PAYMENT_COLUMNS.replace(', ', ', p.')} FROM payments p "
                "JOIN idempotency_keys i ON i.payment_id = p.payment_id "
                "WHERE p.user_id = ? AND i.key = ?",
                (user_id, key),
            ).fetchone()
        finally:
            con.close()
        if row is None:
            raise PaymentNotFoundError("Payment not found.")
        return self._row_to_payment(row)

    def claim_next_pending_intent(self) -> Intent | None:
        """Atomically claim the oldest pending intent (single winner).

        ``BEGIN IMMEDIATE`` serializes writers: the loser blocks until the
        winner commits, then observes no pending rows and returns ``None``.
        """
        now = _now()
        con = _open(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT intent_id FROM intents WHERE status = 'pending' "
                "ORDER BY created_at, intent_id LIMIT 1"
            ).fetchone()
            if row is None:
                con.rollback()
                return None
            intent_id = row["intent_id"]
            updated = con.execute(
                "UPDATE intents SET status = 'claimed', claimed_at = ? "
                "WHERE intent_id = ? AND status = 'pending'",
                (now, intent_id),
            ).rowcount
            if updated != 1:
                con.rollback()
                return None
            claimed = con.execute(
                f"SELECT {_INTENT_COLUMNS} FROM intents WHERE intent_id = ?",
                (intent_id,),
            ).fetchone()
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
        return Intent(*claimed)

    def finalize_intent(
        self, intent_id: int, payment_id: str, new_status: PaymentStatus,
        failure_reason: str | None = None,
    ) -> None:
        """Apply an execution outcome to the payment and mark the intent done.

        One transaction: the transition goes through the payment aggregate
        (``payment.apply_transition``); an unauthorized transition raises
        :class:`payment.InvalidTransitionError` and rolls everything back.
        ``failure_reason`` is stored on the intent row for internal
        diagnostics only — it never crosses the API contract or the logs.
        """
        con = _open(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            intent = con.execute(
                "SELECT payment_id, status FROM intents WHERE intent_id = ?",
                (intent_id,),
            ).fetchone()
            if (
                intent is None
                or intent["payment_id"] != payment_id
                or intent["status"] != "claimed"
            ):
                raise InvalidIntentError("Intent is not claimed for this payment.")
            row = con.execute(
                f"SELECT {_PAYMENT_COLUMNS} FROM payments WHERE payment_id = ?",
                (payment_id,),
            ).fetchone()
            if row is None:
                raise PaymentNotFoundError("Payment not found.")
            payment = self._row_to_payment(row)
            apply_transition(payment, new_status)
            now = _now()
            con.execute(
                "UPDATE payments SET status = ?, updated_at = ? WHERE payment_id = ?",
                (new_status.value, now, payment_id),
            )
            updated = con.execute(
                "UPDATE intents SET status = 'done', reason = ? "
                "WHERE intent_id = ? AND payment_id = ? AND status = 'claimed'",
                (failure_reason, intent_id, payment_id),
            ).rowcount
            if updated != 1:
                raise InvalidIntentError("Intent is not claimed for this payment.")
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def list_history(
        self, user_id: str, limit: int, cursor: str | None = None,
    ) -> tuple[list[Payment], str | None]:
        """Newest-first keyset page of ``user_id``'s payments.

        ``cursor`` is the opaque token from the previous page (``None`` for
        the first page). Ordering is ``(created_at, payment_id)`` descending,
        which stays stable while newer payments are inserted.
        """
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer between 1 and 100.")
        after = self._decode_cursor(cursor) if cursor is not None else None
        sql = f"SELECT {_PAYMENT_COLUMNS} FROM payments WHERE user_id = ?"
        params: list = [user_id]
        if after is not None:
            created_at, payment_id = after
            sql += " AND (created_at < ? OR (created_at = ? AND payment_id < ?))"
            params += [created_at, created_at, payment_id]
        sql += " ORDER BY created_at DESC, payment_id DESC LIMIT ?"
        params.append(limit + 1)
        con = _open(self.db_path)
        try:
            rows = con.execute(sql, params).fetchall()
        finally:
            con.close()
        has_more = len(rows) > limit
        items = [self._row_to_payment(row) for row in rows[:limit]]
        next_cursor: str | None = None
        if has_more:
            last = rows[limit - 1]
            next_cursor = _encode_cursor(last["created_at"], last["payment_id"])
        return items, next_cursor

    @staticmethod
    def _row_to_payment(row) -> Payment:
        return Payment(
            id=row["payment_id"],
            status=PaymentStatus(row["status"]),
            payeePixKey=row["payee_pix_key"],
            amount=row["amount"],
            description=row["description"],
            createdAt=datetime.fromisoformat(row["created_at"]),
            updatedAt=datetime.fromisoformat(row["updated_at"]),
        )

    @staticmethod
    def _decode_cursor(cursor: str) -> tuple[str, str]:
        if type(cursor) is not str:
            raise InvalidCursorError("Invalid pagination cursor.")
        try:
            raw = base64.b64decode(cursor, altchars=b"-_", validate=True).decode("utf-8")
            created_at, payment_id = raw.split("|", 1)
            parsed = datetime.fromisoformat(created_at)
            if parsed.tzinfo is None or not payment_id:
                raise ValueError
        except (binascii.Error, UnicodeDecodeError, ValueError) as exc:
            raise InvalidCursorError("Invalid pagination cursor.") from exc
        return created_at, payment_id