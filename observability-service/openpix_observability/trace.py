from __future__ import annotations

import contextvars
import re
import secrets
from dataclasses import dataclass, replace
from typing import Mapping
from contextvars import Token

_TRACEPARENT = re.compile(r"^[\da-f]{2}-[\da-f]{32}-[\da-f]{16}-[\da-f]{2}$")

_current: contextvars.ContextVar[TraceContext | None] = contextvars.ContextVar(
    "openpix_trace_context", default=None
)


@dataclass(frozen=True)
class TraceContext:
    """Effective W3C trace context for the current request."""

    traceparent: str
    trace_id: str
    span_id: str
    tracestate: str | None


def parse_traceparent(value: str | None) -> TraceContext | None:
    """Parse a valid traceparent; return None for absent or malformed values."""
    if not value or not _TRACEPARENT.fullmatch(value) or not value.startswith("00-"):
        return None
    _, trace_id, span_id, _ = value.split("-")
    if trace_id == "0" * 32 or span_id == "0" * 16:
        # W3C Trace Context: all-zero trace-id/span-id are invalid.
        return None
    return TraceContext(
        traceparent=value, trace_id=trace_id, span_id=span_id, tracestate=None
    )


def generate_trace_context() -> TraceContext:
    """Generate a fresh W3C-conformant context (version 00, sampled)."""
    trace_id = secrets.token_hex(16)
    span_id = secrets.token_hex(8)
    return TraceContext(
        traceparent=f"00-{trace_id}-{span_id}-01",
        trace_id=trace_id,
        span_id=span_id,
        tracestate=None,
    )


def extract_trace(headers: Mapping[str, str]) -> TraceContext:
    """Accept an incoming trace context, else generate a fresh one.

    tracestate is propagated only with a valid traceparent (W3C rule); a bare
    tracestate is dropped when a fresh context is generated.
    """
    incoming = parse_traceparent(headers.get("traceparent"))
    if incoming is not None:
        return replace(incoming, tracestate=headers.get("tracestate") or None)
    return generate_trace_context()


def get_trace_context() -> TraceContext | None:
    return _current.get()


def set_trace_context(context: TraceContext | None) -> Token:
    return _current.set(context)


def reset_trace_context(token: Token) -> None:
    _current.reset(token)
