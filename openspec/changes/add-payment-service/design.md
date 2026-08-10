# Payment Service Design

## Context

- `payment` is a documented boundary only (CTX-PLATFORM, CTX-PAYMENT links);
  root `AGENTS.md` says do not create it. This change lifts that gate.
- The grilling (2026-08-08/09) established the product decisions; BACEN canon
  lives at `docs/reference/bacen/` (memory #125/#126).
- The stale `docs/architecture/generated/knowledge-graph.jsonld` embeds an
  earlier RFC-PAYMENT-001/ADR-PAYMENT-001 (2026-07-29): a richer lifecycle
  (AWAITING_CONFIRMATION, AUTHENTICATING, PROCESSING, COMPLETED, CANCELLED,
  EXPIRED), confirm/cancel endpoints, Java-era notes. The grilling simplified
  this; the recovered docs must be updated and the narrowing recorded.
- Conventions: contract-first (`contracts/openapi.yaml` authoritative,
  `models.py` generated via datamodel-code-generator), Problem Details with
  `code` + `correlationId`, `X-Correlation-ID`, operational surface
  (health/ready + metrics port via `openpix_observability`).

## Goals

- Scaffold `payment-service/` (Python/FastAPI) per repo conventions.
- POST /payments with Idempotency-Key; GET /payments/{id}; QUERY
  /payments/history (declared as post in the contract).
- Repository/data source persistence with two-layer idempotency.
- In-process consumer; Executor port with in-repo Pedro Bank fake.
- Domain model User → PixKey with account data on the key; payer-only scope.
- Full operational surface from day one.
- Recover/write the payment docs (CTX, RFC, ADR) and lift the root gate.

## Non-Goals

- Kafka or any external broker; outbox/event sourcing.
- Real bank integration (HTTP Executor), mTLS/CA validation infrastructure.
- DICT operations (key registration, portability, claims, registry).
- Open Finance Brasil client implementation (documented future data source).
- Payee-side flows; cancel/expire/refund; webhooks; richer lifecycle states.
- Any change to sdui-service, decoding-service, or observability-service.

## Decisions

- **Own service, contract-first.** `payment-service/contracts/openapi.yaml`
  1.0.0 is authoritative; `models.py` generated. Mirrors the other services.
- **Consumes decoded instruction data, never raw payloads.** POST /payments
  carries normalized fields (payee key, amount, ...); no BR Code field exists
  in the schema and no runtime call to decoding-service is made — the client
  composes the two calls.
- **Repository/data source boundary.** `PaymentRepository` port; initial data
  source is SQLite via stdlib `sqlite3` (transactional file, zero infra).
  Alternatives rejected: in-memory (fails restart safety), Postgres (infra
  stack the grilling deferred). The port keeps the swap open.
- **Two-layer idempotency.** (a) Create: Idempotency-Key + request
  fingerprint with a unique constraint per caller; replay returns the original
  Payment; same key with a different body → 409. (b) Execution: atomic
  conditional claim on the intent row (single `UPDATE ... WHERE
  status='pending'`) is the lock; no Redis.
- **In-process consumer pool.** Claim in its own short transaction → Executor
  called synchronously with no DB lock held (high latency tolerated) →
  terminal state persisted. No internal retries: executor failure → `failed`
  with reason; the caller retries by submitting a new intent.
- **Executor port + Pedro Bank fake.** In-repo fake, deterministic confirm by
  default, failure injection for tests, no network. HTTP adapter later.
- **State machine: created → confirmed | failed.** Terminal states immutable.
  Supersedes the graph draft's richer lifecycle: no confirm/cancel endpoints,
  no AWAITING/AUTHENTICATING/PROCESSING/CANCELLED/EXPIRED yet.
- **Money.** Decimal, BRL only, `0 < amount ≤ 9,999,999.99`, serialized as a
  JSON string matching `^\d+\.\d{2}$`. JSON numbers rejected (float loss).
- **History via HTTP QUERY (RFC 10008, June 2026).** FastAPI
  `methods=["QUERY"]` at runtime; OpenAPI 3.0.3/3.1 cannot declare `query`,
  so the contract declares `post` with an extension note stating the runtime
  method (memory #127). Keyset pagination, newest-first, opaque cursor over
  (created_at, id), limit default 50 / max 100, response `{items,
  nextCursor}`, per-user scope, every item carries `status`, no filters yet.
- **Auth: API key identifies the User.** Static configured key→user map; 401
  Problem Details otherwise. mTLS + CA root is a documented deployment gate;
  no validation infra is built.
- **Pix identity model per canon.** User (person, CPF/CNPJ) 1→N PixKey;
  account data (participant, branch, number, type — DICT Entry shape) carried
  as data on the key; no Account entity; no DICT ops.
- **Operational surface from day one.** /health + /ready in the contract,
  metrics on a separate port, structured logs without sensitive material,
  W3C trace context, build info — via the shared `openpix_observability`
  package.
- **Financial response safety.** `Cache-Control: no-store` on /payments
  responses; Pix keys, account data, idempotency keys, and internal ids never
  appear in logs, metrics, or traces.
- **Docs.** Write RFC-PAYMENT-001 and ADR-PAYMENT-001 as source Markdown,
  recovered from the stale graph and updated to these decisions, with the
  graph draft's superseded parts marked. Write CTX-PAYMENT.md (currently
  missing; the README links to it). Lift the root AGENTS.md payment gate.
  `knowledge-graph.jsonld` is not rebuilt (rebuild script absent — known gap).

## Risks / Trade-offs

- QUERY support across proxies/clients → the contract keeps the `post`
  declaration so codegen and gateways keep working; runtime QUERY is covered
  by an integration test.
- In-process consumer couples execution to service uptime → acceptable for
  the first slice; the intent table + Executor port keep the Kafka/outbox
  migration path open.
- SQLite single-writer → fine for dev/early load; the repository port
  isolates the swap.
- Static API keys → dev-grade auth; mTLS/CA remains the deployment gate.
