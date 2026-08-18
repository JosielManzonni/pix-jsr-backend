"""Money domain: decimal BRL amounts.

Amounts are decimal, serialized as JSON strings matching ``^\\d+\\.\\d{2}$``
with ``0 < amount <= 9999999.99``. Only exact ``str`` input is accepted — a
JSON number arriving as int/float is rejected here at the isinstance level,
which is the domain-side rejection line for that case.
"""

from __future__ import annotations

import re
from decimal import Decimal

_AMOUNT_RE = re.compile(r"^\d+\.\d{2}$")
_MAX_AMOUNT = Decimal("9999999.99")


class InvalidAmountError(ValueError):
    """Stable domain error for any amount that fails the money rule."""


def parse_amount(value: object) -> Decimal:
    """Parse ``value`` into an exact decimal BRL amount.

    Rejects anything that is not a ``str``, does not match
    ``^\\d+\\.\\d{2}$``, or falls outside ``0 < amount <= 9999999.99``.
    """
    if not isinstance(value, str):
        raise InvalidAmountError(
            "Amount must be a string matching ^\\d+\\.\\d{2}$ (e.g. \"1234.56\")."
        )
    if not _AMOUNT_RE.fullmatch(value):
        raise InvalidAmountError(
            "Amount must be a string matching ^\\d+\\.\\d{2}$ (e.g. \"1234.56\")."
        )
    amount = Decimal(value)
    if amount <= 0 or amount > _MAX_AMOUNT:
        raise InvalidAmountError("Amount must be greater than 0 and at most 9999999.99.")
    return amount