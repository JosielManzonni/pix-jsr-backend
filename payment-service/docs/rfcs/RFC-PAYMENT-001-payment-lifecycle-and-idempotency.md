---
id: rfc-payment-001
type: rfc
ontology: openpix-architecture-v1
title: Payment Lifecycle and Idempotency
status: accepted
context: payment
created: 2026-07-29
updated: 2026-08-18
tags: [rfc, payment, lifecycle, idempotency, state-machine]
relations:
  - type: belongs_to
    target: ctx-payment
  - type: decided_by
    target: adr-payment-001
  - type: governed_by
    target: rfc-platform-001
  - type: related_to
    target: ctx-decoding
  - type: observed_by
    target: ctx-observability
---

# RFC-PAYMENT-001: Payment lifecycle and idempotency

## Status

Accepted and implemented by `payment-service`.

## Summary

The Payment context creates a Payment from normalized decoded-instruction data,
queues its execution, and serves caller-scoped retrieval and history. The
service does not parse raw Pix BR Codes or perform DICT operations.

The lifecycle has exactly three states:

```text
created ──> confirmed
       └──> failed
```

The `confirmed` and `failed` outcomes are produced by the asynchronous
Executor path; there are no HTTP confirm or fail commands.

The Payment aggregate is the only component that authorizes these transitions.
`confirmed` and `failed` are terminal.

## Contract and boundary

`payment-service/contracts/openapi.yaml` is the authoritative interface. The
service exposes:

- `POST /payments` to create a Payment;
- `GET /payments/{paymentId}` to retrieve the caller's Payment;
- the runtime HTTP `QUERY /payments/history` operation for caller-scoped,
  keyset-paginated history. The OpenAPI contract declares this operation as
  `post` and records `x-runtime-method: QUERY`, because OpenAPI 3.0.3 cannot
  declare the `QUERY` method;
- `GET /health` and `GET /ready` for operational probes.

Creation accepts normalized fields (`payeePixKey`, `amount`, and an optional
`description`). It does not accept a BR Code field and does not call
`decoding-service` at runtime. A client composes decoding and payment calls at
the contract boundary.

The API key identifies the caller's User. Retrieval and history are scoped to
that User. A payment owned by another User is returned as `404`, without
revealing whether the payment exists.

## Creation and the two idempotency layers

### Creation idempotency

The service requires `Idempotency-Key` on creation and scopes the key to the
caller. Persistence enforces a unique `(user_id, key)` constraint and stores a
request fingerprint.

- The same caller may replay the key with the same request body. The service
  returns the original Payment with `200` and creates no duplicate.
- The same caller may not reuse the key with a different body. The service
  returns `409`.
- A different caller has a separate idempotency-key namespace.

The first creation writes the Payment, its pending Payment Intent, and the
idempotency record in one transaction. The transaction commits all three rows
or none of them. This is the atomic create-plus-enqueue boundary.

### Execution idempotency

The in-process consumer claims a pending Payment Intent with an atomic
conditional update. Only one claimant can change a given intent from
`pending` to `claimed`.

The claim transaction is short and commits before the consumer calls the
Executor. The consumer does not hold a database lock while the Executor runs.
The outcome is then persisted with the terminal Payment transition and the
intent is marked done. The service does not retry a failed Executor call
internally. A caller retry requires a new intent.

## Execution boundary

Execution goes through the `Executor` port. The shipped implementation is the
in-repository Pedro Bank fake. It confirms deterministically by default,
provides failure injection for tests, and makes no network calls.

An Executor failure or exception transitions the Payment to `failed` with a
reason stored for internal intent diagnostics. The reason is not part of the
Payment response contract.

## Money and Pix identity

Amounts are BRL decimal strings matching `^\d+\.\d{2}$`, with
`0 < amount <= 9999999.99`. JSON numbers are rejected so that binary floating
point cannot change the stored value. The service supports BRL only.

The service accepts `payeePixKey` as normalized input. It does not introduce
an Account entity and does not provide DICT operations such as key
registration, portability, claims, or registry access.

## History and response safety

History is newest-first and uses an opaque keyset cursor over the creation
ordering. The default limit is 50 and the allowed range is 1 through 100. The
cursor remains stable when newer payments are inserted. Every result contains
the current Payment status and only the caller's payments.

Every response under `/payments` carries `Cache-Control: no-store`. Pix keys,
account data, Idempotency-Key values, raw payloads, and internal database IDs
must not appear in logs, metrics, or traces. The service carries correlation
and W3C trace context and exposes structured request logging.

Observability is wired directly in the service for this implementation:
health and readiness are served by the application, metrics are exposed by the
separate metrics application, and correlation, W3C trace context, and
structured request logs are handled locally. The shared
`openpix_observability` package remains deferred until an observability service
and shared package exist; this RFC does not add that dependency.

## Superseded lifecycle draft

The earlier graph draft for this RFC is superseded by this accepted decision.
It described a richer lifecycle with `AWAITING_CONFIRMATION`,
`AUTHENTICATING`, `PROCESSING`, `COMPLETED`, `CANCELLED`, and `EXPIRED`. It
also described `POST /payments/{paymentId}/confirm` and
`POST /payments/{paymentId}/cancel` endpoints.

Those states and endpoints are not current behavior. The implemented contract
has only `created`, `confirmed`, and `failed`; no confirm or cancel endpoint
exists. The old draft is recorded here as superseded so it is not mistaken for
an implementation requirement.

## Knowledge graph

- Context: [[CTX-PAYMENT]]
- State-machine decision: [[ADR-PAYMENT-001-aggregate-state-machine]]
- Governed by: [[RFC-PLATFORM-001-contract-first-service-boundaries]]
- Normalized input boundary: [[CTX-DECODING]]
- Observed by: [[CTX-OBSERVABILITY]]

The service-local contract is
[`contracts/openapi.yaml`](../../contracts/openapi.yaml).

> `docs/architecture/generated/knowledge-graph.jsonld` is not rebuilt for this
> note because `scripts/build_knowledge_graph.py` is absent. The generated
> graph is derived and must not be edited by hand.
