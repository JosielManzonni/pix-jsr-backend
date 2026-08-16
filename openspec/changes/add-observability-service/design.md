## Context

- `sdui-service/` and `decoding-service/` are the implemented services:
  Python/FastAPI, contract-first (`contracts/openapi.yaml` authoritative,
  `models.py` generated via `datamodel-code-generator`), Problem Details with
  `code` + `correlationId`, `X-Correlation-ID` accept/reflect with generated
  fallback, `_tests/` verified with `python -m pytest` from the service
  directory. Decoding asserts its served OpenAPI equals the contract
  verbatim.
- RFC-OBSERVABILITY-001 (operational observability interface) and
  ADR-OBSERVABILITY-001 (pull-based operational endpoints) are documented
  only as content inside the stale `knowledge-graph.jsonld` snapshot; no
  source Markdown, no `observability-service/`, no contract exist.
- Platform RFC/ADR fix cross-service conventions: each service owns its
  OpenAPI contract, interfaces between services are contracts only, HTTP
  errors use Problem Details, correlation and W3C trace context cross
  boundaries, API/contract/revision versioning are distinct concepts.
- Root `AGENTS.md` forbids creating the observability context; the decoding
  change explicitly deferred observability to this change.
- No identity/auth system exists anywhere; RFC-PLATFORM-001 states client
  headers are untrusted context and auth must come from validated identity.
  The ADR's metric protection is "rede e/ou credencial" (network and/or
  credential) — network-only is an accepted posture.
- No Android client and no payment service exist; verification is unit +
  integration tests via FastAPI TestClient, same as SDUI/decoding.

## Goals / Non-Goals

**Goals:**

- An `observability-service` that is itself observable and hosts the shared
  instrumentation used by every service.
- `GET /health` and `GET /ready` on the API port of every service, part of
  each service's OpenAPI contract: typed JSON, generated models, never
  cached, no sensitive data.
- `GET /metrics` on a **separate metrics port** of every service, serving
  Prometheus text exposition format 0.0.4, protected by network topology,
  deliberately absent from the OpenAPI contract.
- W3C Trace Context: accept `traceparent`/`tracestate`, generate a fresh
  context when absent, surface `trace_id` (and the existing correlation id)
  in structured logs.
- Structured logging with stdlib formatter emitting key=value fields —
  no logging dependency added.
- Docs brought in line: RFC-OBSERVABILITY-001 and ADR-OBSERVABILITY-001
  written as source Markdown (content recovered from the graph, updated to
  record the separate-port decision), CTX-OBSERVABILITY links resolved,
  root `AGENTS.md` gate lifted for observability.
- Data policy enforced in specs and tests: no tokens, payloads, keys,
  accounts, documents or idempotency IDs as telemetry attributes; correlation
  IDs never become metric labels.

**Non-Goals:**

- Creating or persisting payments (payment context, future change).
- In-app authentication or credential enforcement on `/metrics`: the docs
  specify network and/or credential protection; a credential scheme would
  invent identity behavior that belongs to a future auth/payment context.
  Deployment MUST restrict the metrics port via network policy.
- Aggregated status pages or a central operational dashboard ("visão
  operacional" stays limited to per-service endpoints and the shared
  package; aggregation is a follow-up when a consumer exists).
- The Java side of W3C propagation (payment service, not built); conventions
  are documented so Java can follow them later.
- Any change to SDUI/decoding business behavior, responses, or error codes.
- Rebuilding `knowledge-graph.jsonld` (scripts missing; not hand-edited).

## Decisions

### Decision: `/metrics` on a separate port, out of the OpenAPI contract

Each service runs two listeners in one process: the API port (contract
surface) and a metrics port (operational surface) serving only `GET
/metrics` in Prometheus text exposition format 0.0.4. Rationale:

- The contract stays pure JSON; the runtime==contract invariant (asserted by
  decoding) holds per port without needing a schema-less `text/plain`
  response or a JSON wrapper that would break Prometheus scraping.
- A separate socket is the canonical "protected by network" mechanism from
  the ADR: ops firewalls exactly that port. No auth code ships, and no
  credential scheme is invented.
- Port numbers are environment configuration (`METRICS_PORT`, default 9100),
  not contract values; documented per service in AGENTS.md.
- Format versioning rides the media type (`text/plain; version=0.0.4`) and
  the referenced exposition-format spec, keeping API version, contract
  version, and content revision distinct per the platform rule.

### Decision: `/health` and `/ready` are contract endpoints of every service

`GET /health` (liveness: process serving) and `GET /ready` (readiness:
process can accept work) are added additively to each service's OpenAPI
contract (1.0.0 → 1.1.0, API version unchanged), typed JSON responses with
generated models and Problem Details on failure. Probes are never cached.
For today's stateless services readiness has no downstream dependencies and
returns OK when the process serves; the health/ready distinction is kept
because the ADR exists precisely to separate restart from traffic removal.

### Decision: Readiness never depends on other services

`/ready` reflects only the owning process. The ADR's cascade warning
("readiness mal projetada pode causar cascata") is applied strictly: an
observed-service outage must never make observability itself not-ready.

### Decision: Shared instrumentation package hosted by observability-service

`observability-service/` hosts `openpix_observability/`, a small local
package (stdlib logging formatter with `trace_id`/`correlation_id` fields,
trace-context middleware, metrics setup with default Prometheus collectors).
sdui and decoding import it. Rationale: the RFC assigns infrastructure to
this context ("O observability-service oferece infraestrutura"), three
copies of the same middleware would be a smell, and the package is
instrumentation — not business models — so it does not violate the
contracts-only integration rule. Fallback if strict service independence is
preferred: copy the module per service.

### Decision: W3C Trace Context accept-and-generate, stdlib structured logs

`traceparent` (and `tracestate`, passed through) are accepted; when absent a
fresh `00-<32 hex trace id>-<16 hex span id>-01` context is generated.
`trace_id` and the effective `correlation_id` are attached to every
structured log line via a stdlib `logging.Formatter` producing key=value
fields. Correlation IDs remain request headers (accept/reflect as today) and
never become metric labels (RFC data policy).

### Decision: `prometheus-client` is the only new runtime dependency

The exposition format is an external grammar; `prometheus-client` is the
stdlib of the Prometheus ecosystem and keeps a bounded metric set (HTTP
request counter and duration histogram keyed by OpenAPI `operationId` —
bounded cardinality — plus default process/platform collectors). Hand-writing
the format would be reinvention.

### Decision: Documentation is part of this change

RFC-OBSERVABILITY-001 and ADR-OBSERVABILITY-001 are written as source
Markdown in `docs/architecture/{rfcs,adrs}/` (following the decoding
precedent; the graph's `observability-service/articles/...` sourcePaths are
stale backstage layout), with frontmatter relations. Content is recovered
from the graph and updated: the ADR's decision text records the separate
metrics port as the accepted form of "protected by network". ADR status:
accepted after implementation. `knowledge-graph.jsonld` is not hand-edited
and cannot be rebuilt — noted in the docs.

## Risks / Trade-offs

- **Retrofit touches working services.** Mitigated: additive endpoints only,
  contracts regenerated not hand-edited, full test suites per service, and
  the decoding suite's runtime==contract assertion extended to the new
  paths.
- **Metrics port unprotected by default.** The service ships no auth; a
  mis-deployment could expose platform telemetry. Accepted by the ADR's
  "rede e/ou credencial"; documented as a deployment gate, and the data
  policy keeps the exposed content non-sensitive.
- **Cardinality drift on metric labels.** Mitigated: labels are bounded
  (`operationId`, method); correlation IDs and business identifiers are
  explicitly forbidden as labels and covered by tests.
- **Shared package couples services at build time.** Accepted: it is the
  infrastructure the RFC assigns to this context; business integration
  remains contract-only.
- **Knowledge graph stays stale.** The derived JSON-LD cannot be regenerated
  in this repo; the graph snapshot already contains the observability notes,
  so it will not regress further. Accepted and documented.
- **Structured logs via key=value, not JSON.** Chosen to avoid a logging
  dependency; JSON logging can be added without breaking consumers if an
  operator needs it.
