# Retrospective

Change: add-pix-decoding-service · Branch: feat/add-pix-decoding-service

## What shipped

- `decoding-service`: contract-first FastAPI service, single `POST /decode/v1/pix-payloads`. Strict Pix BR Code decoding: raw-ASCII EMV TLV, CRC16-CCITT-FALSE via `binascii.crc_hqx`, key detection (CPF/CNPJ check digits, phone, linear email, EVP UUID v4 canonical), dynamic key XOR location, Problem Details with `DECODING_*` codes, `X-Correlation-ID` accept/reflect + generated fallback, no persistence, no payload/key logging. **132 tests green**; served OpenAPI == `contracts/openapi.yaml` verbatim (asserted).
- Docs: RFC-DECODING-001, ADR-DECODING-001, CTX-DECODING links resolved, root `AGENTS.md` gate lifted (payment/observability no-invention kept).
- Change artifacts: proposal, design, specs (incl. dynamic-location scenarios), tasks (**33 checked** incl. council-review group 8), plan, verify.md — all checks PASSED.

## What went well

- Test-first slices held through the whole change; red→green evidence recorded per area.
- Multi-model council review caught a contract-level blocker (dynamic location) that three prior in-house review passes missed — independent seats converged; a user decision resolved the scope.
- CRC correctness anchored to externally verified known-answer vectors; the invented in-memory vector was disproven by recomputation before it could ship.
- Oracle review loops were run until clean (6 passes) before final verification.

## What to watch

- Wire-format lesson: Pix BR Code is raw ASCII TLV with 2-digit DECIMAL lengths — the initial brief wrongly specified hex-encoded values; caught by review. Future Pix work must use the constants module + verified vectors, not memory.
- Ordering strictness (non-descending tags, CRC exempt) may reject real-world payloads from non-conformant issuers; flagged as follow-up if a concrete case appears.
- 512-char envelope limit corroborated by implementations but not scraped from the BCB PDF (JS-rendered site).
- `knowledge-graph.jsonld` remains stale (no rebuild script in repo) — documented in the RFC.
- Root `AGENTS.md` was created on this branch while `chore/agentic-guidance` also adds one — expect a merge conflict at `AGENTS.md`; reconcile at merge time.
- `decoding-service/.venv` and `sdui-service/.venv` were created for test isolation (gitignored).

## Follow-ups

- Payment context (bounded context documented, not implemented) consuming `DecodedInstruction`.
- Audit real-world issuer payloads for ordering/strictness violations.
- Verify the 512-char limit against the current BCB manual text when accessible.
- Restore the knowledge-graph build script so the derived JSON-LD can be regenerated.
- Revisit httpx2 deprecation warning from starlette TestClient (cosmetic).
- Reconcile `chore/agentic-guidance` merge (`AGENTS.md` overlap).
