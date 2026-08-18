# Payment Service Implementation Plan

## Implementation Slices

- Slice 1 — Contract and scaffold (1.1–1.3)
- Slice 2 — Domain core (2.1–2.2)
- Slice 3 — Persistence (3.1–3.2)
- Slice 4 — Execution pipeline (4.1–4.2)
- Slice 5 — HTTP API and observability (5.1–5.2)
- Slice 6 — Documentation (6.1–6.5)
- Slice 7 — Final verification (7.1–7.3)

## Review checkpoints

- After Slice 1 — review the contract surface: QUERY-declared-as-post note,
  idempotency semantics, money representation, auth scheme. Record findings.
- After Slice 5 — independent review of the full implementation diff:
  aggregate transition authority, both idempotency layers, claim atomicity,
  lock-free Executor call, sensitive-material hygiene.
- After Slice 6 — reviewer checks docs ↔ spec drift: RFC/ADR/CTX match the
  spec requirements, superseded parts are marked, the root AGENTS.md gate is
  lifted.

## Final verification intent

- `cd payment-service && python -m pytest` — green.
- Contract validation and served-OpenAPI parity — green; QUERY runtime
  integration test — green.
- No diff under `sdui-service/`, `decoding-service/`, or
  `observability-service/`.
- Docs resolve: README payment links work; RFC/ADR/CTX carry correct
  relations and bumped `updated` fields.
- Grilled decisions honored: two-layer idempotency, no internal retries,
  no DICT ops, payer scope, money bounds, per-user keyset history.

## Commit grouping

- Contract + scaffold + generated models.
- Domain core.
- Persistence.
- Execution pipeline.
- HTTP API + observability.
- Documentation + root AGENTS.md gate lift.
