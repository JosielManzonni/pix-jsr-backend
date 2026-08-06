# Verification

Change: add-pix-decoding-service · Branch: feat/add-pix-decoding-service
Updated: 2026-08-06 (post council-review cycle)

Environment note: this workspace has no "Runner" agent; every check was
executed by the orchestrator directly, with the exact command and observed
pytest summary recorded. Exit code 0 is implied by a passing summary.

## Planned checks (plan.md "Final verification intent")

| # | Type | Command (workdir) | Exit | Outcome |
|---|------|-------------------|------|---------|
| 1 | Unit + integration | `.venv/bin/python -m pytest` (decoding-service/) | 0 | PASSED — 132 passed (test_utils 25→31, test_models, test_interpreter, test_main, fixtures) |
| 2 | Contract validation | `main.app.openapi() == yaml.safe_load(contracts/openapi.yaml)` (asserted in test_main) | 0 | PASSED — True; responses 200/400/422; key/key_type nullable; location added |
| 3 | Regression | `.venv/bin/python -m pytest` (sdui-service/) | 0 | PASSED — 27 passed |
| 4 | Spec-scenario coverage | Oracle + council scenario walks vs tests | n/a | PASSED — all delta-spec scenarios incl. new location scenarios mapped to ≥1 passing test |
| 5 | Independent spot checks | Orchestrator TestClient probes | n/a | PASSED — valid CPF 200/cpf; bad-checksum + repeated-digit CPF → INVALID_KEY; p5 location dynamic → 200; unknown tag 64 before CRC → 200 |

## Review checkpoints

| Checkpoint | Review pass | Outcome |
|------------|-------------|---------|
| Slice 3 core | ora-1 pass 1 | 1 blocker (hex wire format) + 5 majors + 2 minors → fixed |
| Core rework | ora-1 pass 2 | 4 majors → fixed |
| HTTP layer | ora-1 pass 3 | 1 major (OpenAPI drift) → fixed; served==contract asserted |
| Docs | ora-1 pass 4 | 3 minors + 1 nit → fixed |
| Council (multi-model) | beta + gamma (alpha failed twice, dropped) | Blocker (dynamic location scope) + 2 majors + 5 minors + 5 nits → user decided: SUPPORT dynamic location; all findings addressed |
| Council cycle re-review | ora-1 pass 5 | 2 majors (repeated-digit CPF/CNPJ; ordering vs CRC tag) + 1 minor + 1 dead branch + UUID canonical note → fixed |
| Final re-review | ora-1 pass 6 | **CLEAN** — no findings remaining |

## CRC known-answer vectors

Verified externally against `binascii.crc_hqx(data, 0xFFFF)` and by the test
suite: A5C7 (V1), F1E4 (V2), 90CA (V3), B659 (p1 — extracted literal's
claimed 325F disproven by recomputation), 9182 (p2), 2D75 (p5 — decodes as
location-based dynamic instruction, 26.25, no key). Initial in-memory vector
(A5C7 on reconstructed string) disproven (BCF2) and removed.

## Council review record

Multi-model council (2026-08-06): verdict Rework before archive. Dynamic
location (26.25) support implemented per user decision; strict validation
additions (non-empty 59/60, MCC ^\d{4}$, canonical ordering with CRC exempt,
CPF/CNPJ check digits, EVP UUID v4 canonical, linear email); error-consistency
(type URIs, parameterized 422 for all DECODING_* codes, 400 correlation);
simplifications (stdlib CRC, helper removal, charset generator, model-test
cleanup, shared fixtures.py). All 12 findings + 5 follow-up items addressed;
two oracle re-review cycles until clean. Complexity: all paths O(n) time /
O(n) space worst-case, no superlinear behavior; negligible at the 512-char
envelope.

## Remaining uncertainty

- 512-char envelope from the manual (not scraped directly from the BCB PDF;
  corroborated by multiple implementations).
- Ordering strictness rejects ordinary descending unknown tags — accepted,
  documented in design.md (follow-up if a real issuer violates it).
- knowledge-graph.jsonld intentionally stale (no rebuild script); documented
  in RFC-DECODING-001.

## Result

All planned checks PASSED; review loops clean; docs synced to final
implementation (spec.md location scenarios, design.md amendments, RFC/ADR
updates, tasks.md group 8). Change is archive-ready.
