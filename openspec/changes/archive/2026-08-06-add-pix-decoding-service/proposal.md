## Why

The architecture knowledge graph (`docs/architecture/`) defines a **decoding**
bounded context: validation and normalization of Pix/BR Code payloads into an
interpreted instruction. Only `sdui-service` is implemented today; decoding,
payment, and observability remain documented boundaries with dangling RFC/ADR
links in the graph.

Decoding is the natural next build: it is small, self-contained, stateless,
and fully verifiable with unit and integration tests — no Android client is
needed (the SDUI app that would consume these services is not built yet).
The payment context's documented behavior already assumes decoding exists as
an upstream dependency.

## What Changes

- New `decoding-service/` (Python/FastAPI), mirroring the `sdui-service`
  pattern: contract-first OpenAPI, generated Pydantic models, Problem Details
  with `code` + `correlationId`, `_tests/` with unit and integration tests.
- `POST /decode/v1/pix-payloads` — accepts a raw BR Code payload and returns a
  normalized, interpreted instruction (recipient key + type, static/dynamic
  mode, amount, txid, merchant info, CRC validity). Strict validation:
  malformed TLV, CRC mismatch, missing mandatory fields, non-BRL currency, or
  invalid keys → 422 Problem Details with a structured `code`.
- Documentation: write RFC-DECODING-001 (decoding boundary) and
  ADR-DECODING-001 (stateless payload decoding), update CTX-DECODING links and
  the architecture README index, and lift the root `AGENTS.md` gate that
  currently forbids creating the other three contexts.
- Exact BACEN/EMV limits (key formats, txid rules, charset, length caps,
  amount rules) are verified against the Pix manual before being hard-coded
  into the contract.

## Capabilities

### New Capabilities

- `pix-payload-decoding` — validate and normalize Pix/BR Code payloads into an
  interpreted payment instruction, without creating or persisting payments.

### Modified Capabilities

- None (SDUI and platform behavior unchanged).

## Impact

- New service directory `decoding-service/`; no changes to `sdui-service/`.
- `docs/architecture/` gains RFC-DECODING-001 and ADR-DECODING-001; the
  root `AGENTS.md` "do not create the other contexts" note is replaced with
  the new reality.
- `docs/architecture/generated/knowledge-graph.jsonld` cannot be regenerated
  (`scripts/` does not exist); Markdown stays authoritative, the derived graph
  is not rebuilt by hand.
- No persistence, no payment execution, no client authentication — decoding is
  a pure, stateless read/interpret operation. Payload contents are never
  logged.
- Risks: spec-value drift from the official Pix manual; mitigated by the
  verification step above and by keeping limits in one explicit module.
