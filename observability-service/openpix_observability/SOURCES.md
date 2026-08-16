# Verified constants and sources

Facts below were verified against the installed `prometheus-client` (0.21.1)
and the referenced specifications. They are the ground truth for the tests in
this package; do not change them without re-verifying.

## Prometheus text exposition format 0.0.4

- Media type served by `prometheus_client.make_asgi_app()` and
  `generate_latest()` (verified in installed lib,
  `prometheus_client/exposition.py::CONTENT_TYPE_LATEST`):
  `text/plain; version=0.0.4; charset=utf-8`.
- Metric names match `[a-zA-Z_:][a-zA-Z0-9_:]*`; label values escape
  backslash, double quote, and newline.
- Format spec: https://github.com/prometheus/docs/blob/main/content/docs/instrumenting/exposition_formats.md
  (text format version 0.0.4).
- The default `REGISTRY` auto-registers GC, platform, and process collectors
  (verified: `GCCollector`, `PlatformCollector`, `ProcessCollector`).

## W3C Trace Context Level 1

- `traceparent` grammar: `version "-" trace-id "-" span-id "-" trace-flags`,
  each field `[\da-f]` — version 2 hex, trace-id 32 hex, span-id 16 hex,
  trace-flags 2 hex. Generated contexts use version `00` and flags `01`
  (sampled).
- `tracestate`: comma-separated list of `key=value` entries (max 32 entries,
  512 characters). Propagated only with a valid `traceparent`; a bare
  `tracestate` is dropped when a fresh context is generated.
- Spec: https://www.w3.org/TR/trace-context/ (Level 1 Recommendation).
