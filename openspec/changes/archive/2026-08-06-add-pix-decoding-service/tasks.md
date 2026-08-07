## 1. Spec-constant research

- [x] 1.1 Verify against the official Pix manual / EMVCo QRCPS: CRC16-CCITT parameters (poly, init, scope), allowed charset, maximum payload length, per-field length caps (merchant name, city, description, txid), key format rules (CPF/CNPJ/phone/email/EVP), txid rules for static vs dynamic, currency code `986`
- [x] 1.2 Record each verified constant with its source reference in a notes section of the change (or the constants module stub), including any amount-rule findings

## 2. Service scaffold

- [x] 2.1 Write `decoding-service/contracts/openapi.yaml` (title `OpenPix JSR Pix Decoding API`, version `1.0.0`, `POST /decode/v1/pix-payloads`, request `payload`, response `DecodedInstruction`, 422 `ProblemDetails` with `code` + `correlationId`)
- [x] 2.2 Generate `decoding-service/models.py` from the contract with `datamodel-code-generator` (same as sdui-service)
- [x] 2.3 Create `decoding-service/` layout: `main.py`, `utils.py` (or `decoder/` package per design), `pytest.ini`, `requirements-dev.txt`, `AGENTS.md` mirroring sdui-service
- [x] 2.4 Verify the generated models import and match the contract

## 3. Core domain — CRC16 and TLV parser (test-first)

- [x] 3.1 Write failing unit tests for CRC16-CCITT over known payloads (including a real BR Code fixture with its known CRC)
- [x] 3.2 Implement CRC16-CCITT; tests pass
- [x] 3.3 Write failing unit tests for the EMV TLV chain parser: field splitting, sub-TLV (26 / 62), truncation, invalid length, duplicate tags
- [x] 3.4 Implement the TLV parser; tests pass

## 4. Interpretation and validation rules (test-first)

- [x] 4.1 Write failing unit tests for key-type detection (CPF, CNPJ, phone, email, EVP) and unknown-key rejection
- [x] 4.2 Implement key detection; tests pass
- [x] 4.3 Write failing unit tests for mode classification (PIM 11/absent → static, 12 → dynamic) and txid rules
- [x] 4.4 Implement mode classification; tests pass
- [x] 4.5 Write failing unit tests for mandatory-field, charset, length, and currency validation with structured error codes
- [x] 4.6 Implement validation rules; tests pass

## 5. HTTP layer

- [x] 5.1 Wire the endpoint in `main.py` with typed body model; map decoder errors to 422 Problem Details (`type`, `title`, `status`, `detail`, `code`, `correlationId`)
- [x] 5.2 Add `X-Correlation-Id` accept/reflect + generated fallback (reuse the sdui pattern)
- [x] 5.3 Write integration tests (FastAPI TestClient): valid static, valid dynamic, CRC mismatch, malformed TLV, missing mandatory, non-BRL currency, invalid key, correlation reflection, payload-not-logged
- [x] 5.4 Ensure the OpenAPI runtime exposes exactly one operation on `/decode/v1/pix-payloads` with the 422 schema

## 6. Documentation

- [x] 6.1 Write `docs/architecture/rfcs/RFC-DECODING-001-pix-payload-decoding-boundary.md` (frontmatter + relations to CTX-DECODING, CTX-PLATFORM, RFC/ADR links)
- [x] 6.2 Write `docs/architecture/adrs/ADR-DECODING-001-stateless-payload-decoding.md` (status accepted, verification section)
- [x] 6.3 Update `docs/architecture/contexts/CTX-DECODING.md` links and `docs/architecture/README.md` RFC/ADR index entries
- [x] 6.4 Lift the root `AGENTS.md` gate ("only sdui-service exists…") to reflect decoding-service, keeping the no-invention rule for payment/observability
- [x] 6.5 Note in docs that `knowledge-graph.jsonld` is not rebuilt (scripts missing); do not hand-edit it

## 7. Final verification

- [x] 7.1 Run `python -m pytest` from `decoding-service/` — all unit + integration tests pass
- [x] 7.2 Validate contract YAML and examples against the schema
- [x] 7.3 Confirm `sdui-service/` tests still pass (no regressions)

## 8. Council review cycle

- [x] 8.1 Dynamic location support (26.25): contract nullable key/key_type + location; key XOR location semantics
- [x] 8.2 Strict-validation additions: non-empty 59/60, MCC ^\d{4}$, canonical tag ordering (CRC exempt), CPF/CNPJ check digits, EVP UUID v4 canonical, linear email check
- [x] 8.3 Error consistency: Problem Details type URIs aligned runtime↔contract; parameterized 422 coverage for all DECODING_* codes; 400 correlation tests
- [x] 8.4 Simplifications: stdlib CRC (binascii.crc_hqx), helpers removed, charset generator, model-test cleanup, shared fixtures.py
- [x] 8.5 Oracle re-review cycles until clean (132 tests green)
