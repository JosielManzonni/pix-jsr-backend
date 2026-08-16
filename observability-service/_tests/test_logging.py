from __future__ import annotations

import logging

from openpix_observability import logging as obs_logging
from openpix_observability import trace


def _formatted(trace_id: str | None, correlation_id: str | None) -> str:
    trace_token = (
        trace.set_trace_context(
            trace.TraceContext(
                traceparent=f"00-{trace_id}-{'0' * 16}-01",
                tracestate=None,
                trace_id=trace_id,
                span_id="0" * 16,
            )
        )
        if trace_id
        else None
    )
    correlation_token = (
        obs_logging.set_correlation_id(correlation_id) if correlation_id else None
    )
    try:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="request handled",
            args=(),
            exc_info=None,
        )
        return obs_logging.StructuredFormatter().format(record)
    finally:
        if trace_token is not None:
            trace.reset_trace_context(trace_token)
        if correlation_token is not None:
            obs_logging.reset_correlation_id(correlation_token)


def test_formatter_emits_trace_id_and_correlation_id():
    line = _formatted("4bf92f3577b34da6a3ce929d0e0e4736", "corr-123")
    assert "trace_id=4bf92f3577b34da6a3ce929d0e0e4736" in line
    assert "correlation_id=corr-123" in line
    assert "request handled" in line


def test_formatter_always_emits_both_fields_when_context_absent():
    line = _formatted(None, None)
    assert "trace_id=" in line
    assert "correlation_id=" in line


def test_formatter_does_not_alter_message():
    line = _formatted(None, None)
    assert "request handled" in line


def test_configure_logging_attaches_structured_formatter():
    obs_logging.configure_logging()
    root = logging.getLogger()
    assert any(
        isinstance(handler.formatter, obs_logging.StructuredFormatter)
        for handler in root.handlers
    )
