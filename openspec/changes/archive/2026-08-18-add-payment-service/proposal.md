## Why

The architecture defines a **payment** bounded context — payment lifecycle and
idempotency — but no `payment-service/` exists. The root `AGENTS.md` forbids
creating it ("documented boundary only"), `CTX-PAYMENT.md` is missing, and
`RFC-PAYMENT-001` / `ADR-PAYMENT-001` exist only as stale content embedded in
`knowledge-graph.jsonld` — pre-dating the Python/FastAPI pivot and describing a
lifecycle (confirm/cancel endpoints, seven states) that the domain grilling
(2026-08, see `CONTEXT.md`) deliberately simplified.

The grilling settled the design end-to-end against the BACEN canon
(`docs/reference/bacen/`): the User/PixKey model per Resolution BCB 1/2020 and
the DICT manual, async execution via queued intents, two-layer idempotency,
and a per-user paginated history. The decisions are recorded, the reference
docs are local, and the service is small, self-contained, and fully verifiable
with unit and integration tests.

## What Changes

- New `payment-service/` (Python/FastAPI, mirrors sdui/decoding/observability):
  contract-first OpenAPI with `POST /payments`, `GET /payments/{paymentId}`,
  and the payment history endpoint — **HTTP QUERY at runtime (RFC 10008),
  declared as `post` in the contract** because OpenAPI 3.0.3/3.1 cannot
  express QUERY. Born with the full operational surface (`/health`, `/ready`,
  metrics port, trace context, structured logs via `openpix_observability`).
- Payment aggregate with explicit states `created → confirmed | failed`
  (supersedes the stale graph lifecycle), money as Decimal BRL
  (`0 < amount ≤ 9,999,999.99`, JSON string), and normalized decoded-instruction
  input — the service never parses a raw Pix payload.
- Repository/data-source persistence (SQLite via stdlib `sqlite3` behind a
  repository port): Payment rows, idempotency records with request fingerprint,
  and Payment Intent queue. **Two-layer idempotency**: unique constraint on
  (`Idempotency-Key`, caller scope) at create; atomic intent claim at consume.
- In-process consumer pool: claims an intent atomically (the DB row claim is
  the lock), calls the **Executor** port synchronously (high-latency OK, no DB
  lock held), persists the terminal state. **No internal retries** — a failed
  executor call marks the Payment `failed`; the caller retries via a new intent.
  Pedro Bank is an in-repo fake implementing the Executor port; no HTTP client.
- Auth: API key identifies the User (`401` without a valid key). mTLS/CA is a
  documented deployment gate, not built. No DICT operations — key registry is
  out of scope; account data rides on the PixKey (DICT Entry shape), there is
  no Account entity. Open Finance Brasil is the documented future source for
  user/account data.
- Documentation: write `CTX-PAYMENT.md`, `RFC-PAYMENT-001`, and
  `ADR-PAYMENT-001` as source Markdown (graph content recovered, updated to the
  grilled decisions; superseded lifecycle recorded as such), resolve the README
  index links, lift the root `AGENTS.md` payment gate.

## Capabilities

### New Capabilities

- `payment-lifecycle` — creation with idempotency, retrieval, per-user
  paginated history, asynchronous execution to a terminal state, and the
  operational surface, within the payment bounded context.

### Modified Capabilities

- None. No existing service's business behavior changes.

## Impact

- New service directory `payment-service/`; no changes to `sdui-service/`,
  `decoding-service/`, or `observability-service/` code or contracts.
- `docs/architecture/` gains CTX-PAYMENT, RFC-PAYMENT-001, ADR-PAYMENT-001;
  README index links resolve; root `AGENTS.md` payment gate lifted. The stale
  graph lifecycle (confirm/cancel, seven states) is recorded as superseded.
- `knowledge-graph.jsonld` cannot be regenerated (`scripts/` missing);
  Markdown stays authoritative, the derived graph is not hand-edited.
- No new runtime dependencies beyond the established service stack
  (fastapi/uvicorn/pydantic, `openpix_observability`, prometheus-client);
  persistence is stdlib `sqlite3`. No Kafka, no Redis — the DB row claim is
  the lock, per the grilling.
- Auth is API-key-only by design: no identity system is invented; deployment
  MUST front the service with the documented mTLS/CA gate before real use.
- Executor is a fake by design: no real money movement is possible; the HTTP
  Executor adapter is a future change.
- Risks: QUERY-method tooling drift (mitigated: runtime integration test pins
  QUERY behavior; contract note documents the post declaration); SQLite
  single-writer limits (accepted: repository port allows a Postgres data
  source later; consumer claim uses short transactions); stale-graph
  divergence (mitigated: docs slice records superseded decisions explicitly).
