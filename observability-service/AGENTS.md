# observability-service

Operational surface shared by OpenPix JSR services: liveness and readiness
probes, plus the host of the shared instrumentation package
(`openpix_observability/`) used by every service. It exposes no business data
and never processes payments.

## Layout

- `contracts/openapi.yaml` — the authoritative OpenAPI contract (probes only;
  the metrics surface is deliberately absent). `models.py` is generated from
  it.
- `models.py` — pydantic models generated with `datamodel-code-generator`.
  Do not hand-edit; regenerate with:
  `.venv/bin/python -m datamodel_code_generator --input contracts/openapi.yaml --input-file-type openapi --output models.py`
- `openpix_observability/` — shared instrumentation package: W3C trace
  context accept-and-generate (`trace.py`), structured key=value log
  formatter with `trace_id`/`correlation_id` fields (`logging.py`), bounded
  metrics (`metrics.py`), and the ASGI middleware wiring them per request
  (`middleware.py`). Verified format constants in `SOURCES.md`.
- `main.py` — FastAPI app (probes), contract served verbatim, and `serve()`
  which runs two listeners in one process: the API port and the metrics port.
- `_tests/` — unit + integration tests. Run with `python -m pytest` from
  this directory (uses `.venv`).

## Runtime

- API port: `APP_PORT` (default 8000). Metrics port: `METRICS_PORT` (default
  9100), serving only `GET /metrics` in Prometheus text exposition format
  0.0.4. Start with `python main.py` (or `uvicorn main:app` for the API only).
- **Deployment gate:** the metrics port MUST be restricted by network policy
  (firewall/topology). No in-app credential scheme exists; a mis-exposed
  metrics port would leak platform telemetry, so the network restriction is
  mandatory, not optional.

## Rules

- **Contract-first:** change the contract, regenerate models, then update
  endpoints and tests. The served OpenAPI equals the contract verbatim.
- **Probes never cached** and never depend on other services' readiness.
- **Data policy:** no tokens, payloads, Pix keys, accounts, documents, or
  idempotency IDs as telemetry attributes; correlation IDs never become
  metric labels. Labels come from the bounded set of OpenAPI operationIds.
- **Sibling services** (sdui, decoding) import `openpix_observability` from
  this directory; business integration between services remains contract-only.
- **Verification:** all tests via `.venv/bin/python -m pytest` from this
  directory.
