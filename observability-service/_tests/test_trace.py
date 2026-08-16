from __future__ import annotations

import re

import pytest

from openpix_observability import trace

VALID_TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
GENERATED_RE = re.compile(r"^00-[\da-f]{32}-[\da-f]{16}-01$")


def test_parse_valid_traceparent_extracts_ids():
    parsed = trace.parse_traceparent(VALID_TRACEPARENT)
    assert parsed is not None
    assert parsed.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert parsed.span_id == "00f067aa0ba902b7"
    assert parsed.traceparent == VALID_TRACEPARENT


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7",  # missing flags
        "01-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",  # unsupported version
        "00-4bf92f3577b34da6a3ce929d0e0e473-00f067aa0ba902b7-01",  # short trace id
        "00-zz92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",  # non-hex
        "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-zz",  # non-hex flags
        "00-00000000000000000000000000000000-00f067aa0ba902b7-01",  # all-zero trace id
        "00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01",  # all-zero span id
    ],
)
def test_parse_invalid_traceparent_returns_none(value):
    assert trace.parse_traceparent(value) is None


def test_generate_fresh_context_is_w3c_conformant():
    generated = trace.generate_trace_context()
    assert GENERATED_RE.fullmatch(generated.traceparent)
    assert len(generated.trace_id) == 32
    assert len(generated.span_id) == 16
    assert generated.tracestate is None


def test_generate_contexts_are_unique():
    first = trace.generate_trace_context()
    second = trace.generate_trace_context()
    assert first.trace_id != second.trace_id


def test_extract_accepts_incoming_and_passes_tracestate():
    result = trace.extract_trace(
        {"traceparent": VALID_TRACEPARENT, "tracestate": "vendor=value1,vendor2=value2"}
    )
    assert result.traceparent == VALID_TRACEPARENT
    assert result.tracestate == "vendor=value1,vendor2=value2"


def test_extract_generates_when_traceparent_absent():
    result = trace.extract_trace({})
    assert GENERATED_RE.fullmatch(result.traceparent)
    assert result.tracestate is None


def test_extract_drops_bare_tracestate_when_generating():
    result = trace.extract_trace({"tracestate": "vendor=value"})
    assert result.tracestate is None


def test_extract_drops_tracestate_for_invalid_traceparent():
    result = trace.extract_trace(
        {"traceparent": "garbage", "tracestate": "vendor=value"}
    )
    assert GENERATED_RE.fullmatch(result.traceparent)
    assert result.tracestate is None


def test_contextvar_holds_context_until_reset():
    context = trace.generate_trace_context()
    token = trace.set_trace_context(context)
    assert trace.get_trace_context() == context
    trace.reset_trace_context(token)
    assert trace.get_trace_context() is None
