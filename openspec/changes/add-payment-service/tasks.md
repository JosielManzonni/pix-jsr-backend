# Implementation Tasks

## 1. Contract and scaffold

- [ ] 1.1 Write `payment-service/contracts/openapi.yaml` 1.0.0: `post
  /payments` (required `Idempotency-Key` header), `get /payments/{paymentId}`,
  `post /payments/history` (extension note: runtime method is QUERY), `get
  /health`, `get /ready`; components Payment, PaymentCreate,
  PaymentHistoryPage, ProblemDetails, CorrelationId; `ApiKeyAuth` security
  scheme (`X-API-Key`); status enum [created, confirmed, failed]; amount
  pattern `^\d+\.\d{2}$`; `Cache-Control: no-store` on payment responses.
- [ ] 1.2 Scaffold `payment-service/` mirroring decoding-service: `main.py`
  shell, `pytest.ini`, `requirements-dev.txt`, `_tests/`, service `AGENTS.md`
  (contract-first rules + test command).
- [ ] 1.3 Generate `models.py` from the contract (datamodel-code-generator)
  and confirm it imports.

## 2. Domain core (test-first)

- [ ] 2.1 Write tests for money validation (bounds, two-digit precision,
  string form, JSON-number rejection) and for the Payment aggregate
  transitions (`created → confirmed | failed`, terminal immutability, invalid
  transition raises a stable domain error).
- [ ] 2.2 Implement money handling and the Payment aggregate until 2.1 is
  green.

## 3. Persistence (test-first)

- [ ] 3.1 Write tests for the repository: save/get scoped per user; atomic
  create+enqueue in one transaction; idempotency unique constraint (replay
  returns the original, conflicting body errors); atomic intent claim with a
  single winner among concurrent claimants; keyset history (newest-first,
  cursor stability under inserts, limit bounds).
- [ ] 3.2 Implement the `PaymentRepository` port and the SQLite data source
  (stdlib `sqlite3`) until 3.1 is green.

## 4. Execution pipeline (test-first)

- [ ] 4.1 Write tests for the consumer: claims an intent in its own short
  transaction, calls the Executor without holding a DB lock, success →
  `confirmed`, failure → `failed` with reason, no internal retry; Pedro Bank
  fake confirms deterministically and supports failure injection.
- [ ] 4.2 Implement the Executor port, the Pedro Bank fake, and the consumer
  loop until 4.1 is green.

## 5. HTTP API and observability (test-first)

- [ ] 5.1 Write API tests: auth dependency (401), POST /payments (201, replay
  200, conflict 409, validation 422), GET /payments/{paymentId} (200/404/401),
  runtime QUERY /payments/history, `no-store` headers, Problem Details shape
  with `code` + `correlationId`, `X-Correlation-ID` echo, health/ready/metrics
  surface, served OpenAPI equals `contracts/openapi.yaml`, history operation
  declared as `post` with the QUERY note.
- [ ] 5.2 Implement routes, dependencies, QUERY registration
  (`methods=["QUERY"]`), `openpix_observability` wiring, and consumer startup
  until 5.1 is green.

## 6. Documentation

- [ ] 6.1 Write
  `docs/architecture/rfcs/RFC-PAYMENT-001-payment-lifecycle-and-idempotency.md`:
  recover the stale-graph draft, update it to the grilled decisions, mark the
  superseded parts (richer lifecycle, confirm/cancel endpoints).
- [ ] 6.2 Write
  `docs/architecture/adrs/ADR-PAYMENT-001-payment-aggregate-state-machine.md`:
  recover and update to the three-state machine.
- [ ] 6.3 Write `docs/architecture/contexts/CTX-PAYMENT.md` (missing; README
  already links to it) with correct in/out relations including
  `ref-bacen-pix-dict`.
- [ ] 6.4 Verify the payment links in `docs/architecture/README.md` resolve;
  add any missing index entries.
- [ ] 6.5 Update root `AGENTS.md`: payment is now implemented (ownership,
  contract path, test command); note `knowledge-graph.jsonld` is not rebuilt
  (rebuild script absent).

## 7. Final verification

- [ ] 7.1 `cd payment-service && python -m pytest` — green.
- [ ] 7.2 Contract validation, served-OpenAPI parity, and the QUERY runtime
  integration test — green.
- [ ] 7.3 Confirm no changes outside `payment-service/`, `docs/`, and root
  `AGENTS.md`.

## 8. Review cycle

- [ ] 8.1 Independent review of contract + spec semantics after slice 1.
- [ ] 8.2 Independent full-diff review after slice 5.
- [ ] 8.3 Docs ↔ spec drift check after slice 6; resolve findings and re-run
  verification.
