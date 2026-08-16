## Why

The architecture knowledge graph (`docs/architecture/`) defines an
**observability** bounded context: health, metrics, logs and traces that
observe the other contexts without absorbing business rules or sensitive
data. Its RFC (`RFC-OBSERVABILITY-001-operational-observability-interface`)
and ADR (`ADR-OBSERVABILITY-001-pull-based-operational-endpoints`) exist only
as content embedded in the stale `knowledge-graph.jsonld` snapshot; the source
Markdown notes are missing from this repo, no `observability-service/` exists,
and the root `AGENTS.md` still forbids creating the context.

The decoding change explicitly deferred observability ("separate future
change"). The time is right: two services exist that must be observable, the
observability conventions are already documented, and the operational
endpoints are small, stateless and fully verifiable with unit and integration
tests — no Android client or payment service is needed.

## What Changes

- New `observability-service/` (Python/FastAPI, mirrors sdui/decoding):
  contract-first OpenAPI with `GET /health` and `GET /ready`, and `GET
  /metrics` on a **separate metrics port** (Prometheus text exposition
  format 0.0.4, protected by network topology — not in the OpenAPI contract).
  Hosts the shared `openpix_observability` instrumentation package used by
  all services.
- Retrofit the same operational surface onto `sdui-service/` and
  `decoding-service/`: `GET /health`, `GET /ready` (additive contract change,
  contract version 1.0.0 → 1.1.0), metrics port, W3C Trace Context
  (`traceparent`/`tracestate` accept, generate when absent, `trace_id` in
  structured logs alongside the existing `X-Correlation-ID`), and structured
  key=value logging via stdlib formatter — no new logging dependency.
- Documentation: write RFC-OBSERVABILITY-001 and ADR-OBSERVABILITY-001 in
  `docs/architecture/{rfcs,adrs}/` (recovering the graph content, updated to
  record the separate-metrics-port decision), resolve CTX-OBSERVABILITY links,
  and lift the root `AGENTS.md` gate for observability (payment stays
  no-invention).
- Data policy (RFC, enforced in specs and tests): tokens, payloads, Pix keys,
  accounts, documents and idempotency IDs never appear as telemetry
  attributes; correlation IDs never become metric labels.

## Capabilities

### New Capabilities

- `operational-observability` — liveness (`/health`), readiness (`/ready`)
  and platform metrics (`/metrics`) per service, plus structured logs with
  correlation and trace IDs and W3C Trace Context propagation.

### Modified Capabilities

- None. SDUI and pix-payload-decoding business behavior is unchanged; the
  new endpoints and logging are additive and belong to the observability
  capability.

## Impact

- New service directory `observability-service/`; additive changes to
  `sdui-service/` and `decoding-service/` (contracts, generated models,
  endpoints, tests).
- `docs/architecture/` gains RFC-OBSERVABILITY-001 and ADR-OBSERVABILITY-001;
  CTX-OBSERVABILITY links resolve; the root `AGENTS.md` no-invention note
  drops observability, keeps payment.
- `knowledge-graph.jsonld` cannot be regenerated (`scripts/` missing);
  Markdown stays authoritative, the derived graph is not hand-edited.
- One new runtime dependency: `prometheus-client` (exposition format is an
  external grammar; hand-writing it would be reinvention).
- Readiness never depends on other services' readiness (ADR cascade warning):
  `/ready` reflects only the serving process, so an observed-service outage
  cannot kill observability.
- Metrics port ships without in-app auth by design: the docs specify
  network and/or credential protection; a credential scheme would require
  inventing identity behavior that belongs to a future auth/payment context.
  Deployment MUST restrict the metrics port by network policy.
- Risks: retrofit touches working services (mitigated: additive endpoints,
  full test suites, contract regenerated not hand-edited); spec-value drift
  for metrics exposition format version (mitigated: referenced, not
  duplicated).
