## 1. Spec and format research

- [x] 1.1 Verify against official sources: Prometheus text exposition format version 0.0.4 (media type `text/plain; version=0.0.4; charset=utf-8`, escaping rules) and W3C Trace Context (traceparent/tracestate grammar, version 00, trace/span id generation rules)
- [x] 1.2 Record each verified constant/rule with its source reference in the change notes (or the package docs), including any findings on exposition-format versioning

## 2. Shared instrumentation package (test-first)

- [x] 2.1 Scaffold `observability-service/openpix_observability/` package (logging formatter, trace middleware, metrics setup) with `prometheus-client` added to `requirements-dev.txt`; document import path for sibling services
- [x] 2.2 Write failing unit tests for the logging formatter: `trace_id` and `correlation_id` fields on every line, no payload/key material
- [x] 2.3 Implement the formatter; tests pass
- [x] 2.4 Write failing unit tests for trace-context handling: incoming `traceparent` accepted and used, `tracestate` passed through, fresh `00-<32hex>-<16hex>-01` generated when absent
- [x] 2.5 Implement trace-context handling; tests pass
- [x] 2.6 Write failing unit tests for metrics setup: counter/histogram keyed by OpenAPI `operationId`, no correlation-ID or per-request labels, default process/platform collectors present
- [x] 2.7 Implement metrics setup; tests pass

## 3. observability-service scaffold

- [x] 3.1 Write `observability-service/contracts/openapi.yaml` (title `OpenPix JSR Observability API`, version `1.1.0`, `GET /health`, `GET /ready`, ProblemDetails + CorrelationId components following the decoding shape, **no** `/metrics` path)
- [x] 3.2 Generate `models.py` from the contract with `datamodel-code-generator` (same as sdui/decoding)
- [x] 3.3 Create layout: `main.py`, metrics app, `pytest.ini`, `requirements-dev.txt`, `AGENTS.md` (mirroring sdui-service, incl. metrics-port protection note)
- [x] 3.4 Two-listener startup: API app on the API port + metrics app on `METRICS_PORT` (default 9100) in one process; port from environment
- [x] 3.5 Write integration tests (TestClient): `/health` 200, `/ready` 200, metrics port returns exposition format with correct content type, served OpenAPI matches contract (no `/metrics`)

## 4. Retrofit sdui-service (test-first)

- [x] 4.1 Add `GET /health` and `GET /ready` to `sdui-service/contracts/openapi.yaml` (version 1.0.0 → 1.1.0); regenerate `models.py`
- [x] 4.2 Write failing tests: new endpoints return 200, metrics port serves exposition, trace headers accepted/generated, logs carry `trace_id`/`correlation_id`
- [x] 4.3 Implement (wire endpoints, metrics listener, middleware, formatter); new tests pass and the existing sdui suite stays green
- [x] 4.4 Update `sdui-service/AGENTS.md` with the metrics-port protection requirement

## 5. Retrofit decoding-service (test-first)

- [x] 5.1 Add `GET /health` and `GET /ready` to `decoding-service/contracts/openapi.yaml` (version 1.0.0 → 1.1.0); regenerate `models.py`
- [x] 5.2 Write failing tests: new endpoints return 200, metrics port serves exposition, trace headers accepted/generated, logs carry `trace_id`/`correlation_id`, data-policy checks (no correlation-ID labels, no payload/key material in metrics or logs)
- [x] 5.3 Implement; new tests pass and the existing decoding suite stays green (including the served-OpenAPI==contract assertion extended to the new paths)
- [x] 5.4 Update `decoding-service/AGENTS.md` with the metrics-port protection requirement

## 6. Documentation

- [x] 6.1 Write `docs/architecture/rfcs/RFC-OBSERVABILITY-001-operational-observability-interface.md` (frontmatter + relations to CTX-OBSERVABILITY, CTX-PLATFORM, ADR link), content recovered from the knowledge graph
- [x] 6.2 Write `docs/architecture/adrs/ADR-OBSERVABILITY-001-pull-based-operational-endpoints.md` (status accepted, separate-metrics-port decision recorded as the accepted form of network protection)
- [x] 6.3 Confirm `docs/architecture/contexts/CTX-OBSERVABILITY.md` links and `docs/architecture/README.md` RFC/ADR index entries resolve to the new notes
- [x] 6.4 Lift the root `AGENTS.md` gate: observability now implemented; keep the no-invention rule for payment
- [x] 6.5 Note in docs that `knowledge-graph.jsonld` is not rebuilt (scripts missing); do not hand-edit it

## 7. Final verification

- [x] 7.1 Run `python -m pytest` from each of `sdui-service/`, `decoding-service/`, `observability-service/` — all unit + integration tests pass
- [x] 7.2 Validate each contract YAML and examples against the OpenAPI schema
- [x] 7.3 Confirm no business behavior regressions: sdui and decoding response shapes and error codes unchanged

## 8. Review cycle

- [x] 8.1 Council review: contract shape (health/ready only), data policy enforcement, metrics-port separation, trace-context handling
- [x] 8.2 Oracle re-review cycles until clean
- [x] 8.3 Reconcile review findings into specs/tasks; re-run affected tests
