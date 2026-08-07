## Context

- `sdui-service/` is the only implemented service: Python/FastAPI, contract-first
  (`contracts/openapi.yaml` authoritative, `models.py` generated via
  `datamodel-code-generator`), typed request-context dependencies, Problem
  Details with `code` + `correlationId`, ETags, `_tests/` verified with
  `python -m pytest` from the service directory.
- Platform RFC/ADR (accepted) fix the cross-service conventions: each service
  owns its OpenAPI contract, interfaces between services are contracts only,
  HTTP errors use Problem Details, correlation and W3C trace context cross
  boundaries, API/contract/revision versioning are distinct concepts.
- CTX-DECODING (active) fixes the boundary: decoding validates and normalizes
  Pix/BR Code payloads; the output is an *interpreted instruction*; creating or
  persisting a payment belongs to the Payment context; decoding is stateless.
- No decoding RFC/ADR exists yet — they are dangling links in the knowledge
  graph. Root `AGENTS.md` currently instructs agents not to create the other
  contexts.
- No Android client exists, so verification must not depend on a renderer or
  app; unit + integration tests via FastAPI TestClient are the verification
  path (same as SDUI).

## Goals / Non-Goals

**Goals:**

- A runnable `decoding-service` that turns a raw Pix/BR Code payload into a
  normalized, interpreted instruction over one endpoint, strictly validated.
- Contract-first with generated models, matching the sdui-service pattern so
  the monorepo keeps one consistent shape.
- Docs brought in line: RFC-DECODING-001, ADR-DECODING-001, link updates, and
  the root AGENTS.md gate lifted.
- Spec constants (key formats, txid/charset/length rules, CRC algorithm,
  currency) sourced from the official Pix/EMV references, verified during
  implementation.

**Non-Goals:**

- Creating or persisting payments (Payment context, future change).
- Static/dynamic QR *payment initiation* semantics, scheduling, or PSP logic.
- Any UI, renderer, or mobile-facing surface.
- Admin/publishing workflows, persistence, or state of any kind.
- Observability endpoints beyond what FastAPI provides out of the box
  (observability context is a separate future change).

## Decisions

### Decision: Single strict endpoint — `POST /decode/v1/pix-payloads`

One endpoint accepting `{"payload": "<raw BR Code>"}` and returning the
interpreted instruction, or 422 Problem Details on any invalid input
(parse error, CRC mismatch, missing mandatory field, non-BRL currency,
invalid key). Chosen over GET-with-query (payloads exceed URL ergonomics and
may be logged by proxies), over a two-phase validate/interpret split (YAGNI —
payment context can consume the instruction directly), and over lenient
warnings-in-response (a decoding service that says "maybe" is a bug farm;
clients need one deterministic answer).

### Decision: EMV TLV parsing with Pix-specific interpretation

Parse the payload as an EMV TLV chain (`TT` `LL` `data`), including sub-TLV
inside `26` (merchant account info) and `62` (additional data). Interpretation
layer produces: optional key + detected key type (CPF/CNPJ/phone/email/EVP)
and/or a dynamic location (tag 26.25), mode (static = PIM 11/absent,
dynamic = PIM 12), amount (string, 2 decimals), txid, description, merchant
name/city, MCC, and CRC16-CCITT verification result. Dynamic mode requires
exactly one recipient source: a key (26.01) XOR a location (26.25) — carrying
both is invalid, carrying neither is missing-mandatory. Static mode requires a
key and ignores tag 26.25. Raw parse and semantic interpretation are separate
modules so the parser is reusable and testable in isolation.

### Decision: `decoding-service` mirrors the sdui-service layout

`contracts/openapi.yaml` → generated `models.py`, `main.py` (FastAPI app),
`utils.py` (CRC, key validation, TLV helpers), `_tests/` (`test_main.py`
integration via TestClient, `test_utils.py` unit), `AGENTS.md`, pytest.ini,
requirements-dev.txt. Problem Details reuse the sdui shape (`type`, `title`,
`status`, `detail`, `code`, `correlationId`). No ETag/caching (responses are
derived, not stored).

### Decision: Spec limits live in one constants module, sourced from the Pix manual

Key regexes, txid rules, charset, per-field length caps, currency code, and
CRC parameters are constants in a single module with source comments
referencing the BACEN Pix manual / EMVCo QRCPS sections. The implementation
task verifies each constant against the official references before the
contract is finalized — no hard-coded values from memory.

### Decision: Documentation is part of this change

Write RFC-DECODING-001 (`pix-payload-decoding-boundary`) and
ADR-DECODING-001 (`stateless-payload-decoding`) with frontmatter relations,
update CTX-DECODING.md and `docs/architecture/README.md` links, and lift the
root `AGENTS.md` gate. `knowledge-graph.jsonld` is not hand-edited and cannot
be rebuilt (`scripts/` missing) — noted explicitly in the docs.

### Council review amendments

A multi-model review after implementation tightened strictness without changing
the contract shape (dynamic location was added by an explicit scope decision):
canonical non-descending tag ordering at each TLV level (the final CRC tag 63
is exempt from the numeric comparison), CPF/CNPJ check-digit validation
(all-equal-digit keys rejected), EVP as a canonical RFC 4122 version-4 UUID, a
linear email check, `MCC` matching `^\d{4}$` when present, and non-empty
merchant name/city. The CRC uses the stdlib (`binascii.crc_hqx`, same
parameters and scope). Accepted risk: the ordering rule rejects payloads with
ordinary descending unknown tags; leniency is a follow-up if a real issuer
violates it.

## Risks / Trade-offs

- **Spec drift**: wrong key regexes / limits would silently accept invalid
  payloads or reject valid ones. Mitigated: constants centralized with source
  references and verified against official docs in implementation.
- **Strictness rejects real-world payloads**: some issuers produce
  non-conformant BR Codes (bad CRC handling, non-ASCII chars). Accepted:
  strictness is the documented contract; leniency can be added as a follow-up
  if a concrete client needs it.
- **Contract shape churn**: the instruction schema is a first guess; the
  payment context may later need fields. Mitigated: additive evolution is the
  platform rule; breaking changes require a new version.
- **Knowledge graph stays stale**: the derived JSON-LD cannot be regenerated
  in this repo; the graph will not reflect the new notes until the build
  script exists. Accepted and documented.
