---
id: adr-payment-001
type: adr
ontology: openpix-architecture-v1
title: Payment Aggregate State Machine
status: accepted
context: payment
created: 2026-07-29
updated: 2026-08-18
tags: [adr, payment, aggregate, state-machine, idempotency]
relations:
  - type: belongs_to
    target: ctx-payment
  - type: resolves
    target: rfc-payment-001
  - type: governed_by
    target: rfc-platform-001
  - type: observed_by
    target: ctx-observability
---

# ADR-PAYMENT-001: Payment aggregate state machine

## Status

Accepted and implemented by `payment-service`.

## Context

Payment creation and asynchronous execution can be repeated or can compete
with another consumer. The Executor outcome, rather than an HTTP command,
produces the terminal state. If a route or persistence helper changes status
directly, it can bypass the lifecycle invariant and create a state that the
contract does not define.

The service also needs two separate idempotency boundaries: one for caller
creation requests and one for competing consumers of a pending Payment Intent.

## Decision

`Payment` is the aggregate that authorizes all status transitions. It has
exactly these states and transitions:

```text
created ──> confirmed
       └──> failed
```

`created` is the initial state. `confirmed` and `failed` are terminal and
immutable. Any other transition raises the stable `InvalidTransitionError`
domain error and leaves the Payment unchanged.

The repository applies the aggregate transition when it finalizes an intent.
The HTTP layer does not expose confirm or cancel commands. The only status
values serialized by the contract are `created`, `confirmed`, and `failed`.

Creation uses a caller-scoped `(caller, Idempotency-Key)` uniqueness rule and a
request fingerprint. The repository writes the Payment, its pending intent,
and its idempotency record atomically. An identical replay returns the original
Payment. A different body for the same caller and key returns an idempotency
conflict.

A consumer claims an intent by an atomic conditional update. The claim commits
before the Executor call, so no database lock is held during execution—even
though the shipped Executor is an in-repository fake. The consumer then
uses the aggregate to persist either `confirmed` or `failed`. It performs no
internal retry.

## Consequences

### Positive

- State invariants are testable without HTTP.
- Terminal states cannot be changed through the aggregate.
- A unique constraint and fingerprint prevent duplicate caller creations.
- A committed conditional claim gives one consumer ownership of an intent.
- Executor latency does not hold a database lock.
- Failed execution has an explicit terminal outcome instead of an implicit
  retry loop.

### Negative

- A failed Payment is terminal; a caller must submit a new intent to try again.
- In-process consumers depend on service uptime.
- SQLite serializes writers and is an initial data source, not a scale-out
  persistence choice.
- The current service wires observability locally. A shared
  `openpix_observability` package is deferred until the observability service
  exists.

## Rejected or superseded alternatives

- **Controller-owned status changes:** rejected because they bypass the
  aggregate invariant.
- **In-memory execution locks:** rejected because they do not coordinate
  across threads, processes, or restarts; the persisted conditional claim is
  the execution idempotency boundary.
- **Internal Executor retries:** rejected for this slice. An Executor failure
  marks the Payment `failed`; retry requires a new intent from the caller.
- **Richer lifecycle and confirm/cancel commands:** superseded. The stale graph
  draft named `AWAITING_CONFIRMATION`, `AUTHENTICATING`, `PROCESSING`,
  `COMPLETED`, `CANCELLED`, and `EXPIRED`, plus confirm and cancel endpoints.
  None is part of the implemented contract.

## Verification evidence

The implementation tests cover the aggregate's allowed transitions, terminal
immutability, stable invalid-transition errors, atomic creation and enqueue,
caller-scoped idempotent replay and conflict, single-winner intent claims, and
execution without a database lock held over the Executor.

## Knowledge graph

- Resolves: [[RFC-PAYMENT-001-payment-lifecycle-and-idempotency]]
- Belongs to: [[CTX-PAYMENT]]
- Governed by: [[RFC-PLATFORM-001-contract-first-service-boundaries]]
- Observed by: [[CTX-OBSERVABILITY]]

> `docs/architecture/generated/knowledge-graph.jsonld` is not rebuilt because
> `scripts/build_knowledge_graph.py` is absent. The generated graph is derived
> and must not be edited by hand.
