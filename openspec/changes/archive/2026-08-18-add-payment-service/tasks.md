# Implementation Tasks

## 1. Contract and scaffold

- [x] 1.1 Write `payment-service/contracts/openapi.yaml` 1.0.0: `post
  /payments` (required `Idempotency-Key` header), `get /payments/{paymentId}`,
  `post /payments/history` (extension note: runtime method is QUERY), `get
  /health`, `get /ready`; components Payment, PaymentCreate,
  PaymentHistoryPage, ProblemDetails, CorrelationId; `ApiKeyAuth` security
  scheme (`X-API-Key`); status enum [created, confirmed, failed]; amount
  pattern `^\d+\.\d{2}$`; `Cache-Control: no-store` on payment responses.
- [x] 1.2 Scaffold `payment-service/` mirroring decoding-service: `main.py`
  shell, `pytest.ini`, `requirements-dev.txt`, `_tests/`, service `AGENTS.md`
  (contract-first rules + test command).
- [x] 1.3 Generate `models.py` from the contract (datamodel-code-generator)
  and confirm it imports.

## 2. Domain core (test-first)

- [x] 2.1 Write tests for money validation (bounds, two-digit precision,
  string form, JSON-number rejection) and for the Payment aggregate
  transitions (`created → confirmed | failed`, terminal immutability, invalid
  transition raises a stable domain error).
- [x] 2.2 Implement money handling and the Payment aggregate until 2.1 is
  green.

## 3. Persistence (test-first)

- [x] 3.1 Write tests for the repository: save/get scoped per user; atomic
  create+enqueue in one transaction; idempotency unique constraint (replay
  returns the original, conflicting body errors); atomic intent claim with a
  single winner among concurrent claimants; keyset history (newest-first,
  cursor stability under inserts, limit bounds).
- [x] 3.2 Implement the `PaymentRepository` port and the SQLite data source
  (stdlib `sqlite3`) until 3.1 is green.

## 4. Execution pipeline (test-first)

- [x] 4.1 Write tests for the consumer: claims an intent in its own short
  transaction, calls the Executor without holding a DB lock, success →
  `confirmed`, failure → `failed` with reason, no internal retry; Pedro Bank
  fake confirms deterministically and supports failure injection.
- [x] 4.2 Implement the Executor port, the Pedro Bank fake, and the consumer
  loop until 4.1 is green.

## 5. HTTP API and observability (test-first)

- [x] 5.1 Write API tests: auth dependency (401), POST /payments (201, replay
  200, conflict 409, validation 422, malformed/missing body 400), GET
  /payments/{paymentId} (200/404/401), runtime QUERY /payments/history
  (200 page shape, 422 limit bounds, 405 when POSTed per the contract's
  declared verb), `no-store` headers, Problem Details shape with `code` +
  `correlationId`, `X-Correlation-ID` echo, health/ready/metrics surface,
  served OpenAPI equals `contracts/openapi.yaml`, history operation
  declared as `post` with the QUERY note.
- [x] 5.2 Implement routes, dependencies, QUERY registration
  (`methods=["QUERY"]`), direct observability wiring (health/ready, metrics
  port, structured logs, correlation), and consumer startup until 5.1 is
  green. The shared `openpix_observability` package is deferred until
  observability-service exists (see design.md); do not add it to
  requirements.* yet.

## 6. Documentation

- [x] 6.1 Write
  `payment-service/docs/rfcs/RFC-PAYMENT-001-payment-lifecycle-and-idempotency.md`:
  recover the stale-graph draft, update it to the grilled decisions, mark the
  superseded parts (richer lifecycle, confirm/cancel endpoints). Owned by
  this service, mirroring `decoding-service/docs/rfcs/`.
- [x] 6.2 Write
  `payment-service/docs/adrs/ADR-PAYMENT-001-aggregate-state-machine.md`:
  recover and update to the three-state machine (filename matches the
  existing `[[ADR-PAYMENT-001-aggregate-state-machine]]` link in
  CTX-PAYMENT.md).
- [x] 6.3 Verify `docs/architecture/contexts/CTX-PAYMENT.md` (already exists,
  updated 2026-08-09; this is the only payment doc in
  `docs/architecture/`): confirm its relations still match the spec
  (depends_on ctx-platform, observed_by ctx-observability, related_to
  ctx-decoding/sdui, related_to ref-bacen-pix-dict) and that its RFC/ADR
  links match the titles written in 6.1/6.2; bump `updated` if the docs
  changed anything.
- [x] 6.4 Verify the payment links in `docs/architecture/README.md` resolve;
  add any missing index entries.
- [x] 6.5 Update root `AGENTS.md`: payment is now implemented (ownership,
  contract path, test command); note `knowledge-graph.jsonld` is not rebuilt
  (rebuild script absent).

## 7. Final verification

- [x] 7.1 `cd payment-service && python -m pytest` — green.
- [x] 7.2 Contract validation, served-OpenAPI parity, and the QUERY runtime
  integration test — green.
- [x] 7.3 Confirm no changes outside `payment-service/`, `docs/`, and root
  `AGENTS.md`.

## 8. Review cycle

- [x] 8.1 Independent review of contract + spec semantics after slice 1.
- [x] 8.2 Independent full-diff review after slice 5.
- [x] 8.3 Docs ↔ spec drift check after slice 6; resolve findings and re-run
  verification.
