# Operational Observability Specification

## ADDED Requirements

### Requirement: Liveness probe

Every service SHALL expose `GET /health` on its API port, returning 200 with
a JSON body when the process can serve requests. The probe SHALL NOT be
cached and SHALL NOT depend on other services.

#### Scenario: Process alive

Given a running service, When a client requests `GET /health`, Then the
response is 200 with a JSON body indicating the service is alive.

#### Scenario: No caching and no dependencies

Given a service whose observed downstream services are unavailable, When a
client requests `GET /health`, Then the response is still 200, and the
response SHALL NOT be served from a cache.

### Requirement: Readiness probe

Every service SHALL expose `GET /ready` on its API port, returning 200 with
a JSON body when the process can accept work. Readiness SHALL reflect only
the owning process: it SHALL NOT depend on the readiness of other services,
so an observed-service outage cannot make observability itself not-ready.

#### Scenario: Process ready

Given a running stateless service, When a client requests `GET /ready`, Then
the response is 200 with a JSON body indicating readiness.

#### Scenario: No readiness cascade

Given a service whose observed services are unavailable, When a client
requests `GET /ready`, Then the response remains 200 and does not report the
unavailability of observed services.

### Requirement: Probe safety

Probes SHALL NOT expose addresses, credentials, or sensitive details in
their responses, and SHALL NOT be cached.

#### Scenario: Probe response is safe

Given any service, When a probe endpoint responds, Then its body contains no
addresses, credentials, or sensitive business data.

### Requirement: Metrics exposition on a dedicated port

Every service SHALL expose `GET /metrics` on a metrics port separate from
its API port, serving the Prometheus text exposition format (content type
`text/plain; version=0.0.4; charset=utf-8`). The metrics endpoint SHALL NOT
be part of the service's OpenAPI contract. Responses SHALL NOT be cached.

#### Scenario: Metrics are scrapable on the metrics port

Given a running service, When a collector requests `GET /metrics` on the
metrics port, Then the response is 200 with content type
`text/plain; version=0.0.4; charset=utf-8` and a Prometheus exposition
document.

#### Scenario: Metrics stay out of the contract

Given the service's served OpenAPI document, When it is compared with the
service contract, Then neither contains a `/metrics` path.

### Requirement: Metric label cardinality and data policy

Metrics SHALL NOT use correlation IDs or business identifiers as labels.
Tokens, payloads, Pix keys, accounts, documents, and idempotency IDs SHALL
NOT appear as telemetry attributes. Metric labels SHALL come from a bounded
set (for example, the OpenAPI operationId).

#### Scenario: No correlation IDs as labels

Given a service receiving requests with correlation and trace headers, When
metrics are scraped, Then no metric label carries a correlation ID, trace
ID, or other per-request identifier.

#### Scenario: No sensitive business data in metrics

Given a service processing Pix payloads, When metrics are scraped, Then no
metric name, label, or value contains payload content, keys, accounts,
documents, or idempotency IDs.

### Requirement: Metrics port deployment protection

The metrics port SHALL be protected by network policy and/or a service
credential in deployment. The service SHALL document this requirement in
its AGENTS.md. The API contract SHALL NOT invent an authentication or
credential scheme for metrics.

#### Scenario: Protection requirement is documented

Given any service's AGENTS.md, When it is inspected, Then it states that the
metrics port must be restricted by network policy and/or a service
credential.

### Requirement: W3C Trace Context

Every service SHALL accept incoming `traceparent` and `tracestate` headers
and propagate them. When absent, the service SHALL generate a W3C trace
context (`00-<32 hex trace id>-<16 hex span id>-01`). The effective trace id
SHALL be available to the service's structured logs.

#### Scenario: Incoming trace context is accepted

Given a request carrying a valid `traceparent` header, When the service
processes it, Then the service uses the incoming trace id in its structured
logs and propagates the trace context.

#### Scenario: Missing trace context is generated

Given a request without a `traceparent` header, When the service processes
it, Then the service generates a W3C-conformant trace context and logs the
generated trace id.

### Requirement: Structured logs with correlation and trace identifiers

Structured log lines SHALL include the effective `trace_id` and
`correlation_id`. Logging SHALL NOT emit payload content or decoded key
material.

#### Scenario: Logs carry both identifiers

Given a request with a correlation id and a trace context, When the service
logs, Then each log line contains both `trace_id` and `correlation_id`
fields.

#### Scenario: Sensitive material is never logged

Given a request containing a Pix payload and key material, When the service
logs, Then neither the payload string nor the key material appears in any
log line.

### Requirement: Operational surface uniformity and contract conformance

Every service (sdui, decoding, observability) SHALL expose the same
operational surface: `/health`, `/ready`, and the metrics port. The
`/health` and `/ready` paths SHALL be declared in each service's OpenAPI
contract (additive contract bumps: decoding 1.0.0 → 1.1.0, sdui 1.1.0 → 1.2.0),
and the served OpenAPI document SHALL match the contract.

#### Scenario: All services expose the same operational surface

Given sdui-service, decoding-service, and observability-service, When each
service's contract and metrics port are inspected, Then all expose
`/health`, `/ready`, and a metrics port.

#### Scenario: Served OpenAPI matches the contract

Given any service, When its served OpenAPI document is compared with its
contract, Then it matches, including the `/health` and `/ready` paths and
excluding any `/metrics` path.
