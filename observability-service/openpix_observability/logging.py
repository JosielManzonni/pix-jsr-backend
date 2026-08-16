from __future__ import annotations

import contextvars
import logging
from contextvars import Token

from .trace import get_trace_context

_correlation: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "openpix_correlation_id", default=None
)


class StructuredFormatter(logging.Formatter):
    """Key=value formatter attaching trace and correlation identifiers.

    Every formatted line carries trace_id and correlation_id fields (empty
    when no request context is active) plus the stdlib level/name/time/message
    fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        trace_context = get_trace_context()
        line = (
            f"{self.formatTime(record)} {record.levelname} {record.name} "
            f"{record.getMessage()}"
        )
        line += f" trace_id={trace_context.trace_id if trace_context else ''}"
        line += f" correlation_id={_correlation.get() or ''}"
        return line


def configure_logging() -> None:
    """Attach the structured formatter to the root logger handlers."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.INFO)
    for handler in root.handlers:
        handler.setFormatter(StructuredFormatter())


def get_correlation_id() -> str | None:
    return _correlation.get()


def set_correlation_id(value: str) -> Token:
    return _correlation.set(value)


def reset_correlation_id(token: Token) -> None:
    _correlation.reset(token)
