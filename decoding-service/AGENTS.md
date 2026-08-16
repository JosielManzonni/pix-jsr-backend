# decoding-service

Stateless Pix/BR Code decoding boundary. It accepts a raw payload and returns
a normalized, interpreted payment instruction, or a 422 Problem Details body
when the payload fails strict validation.

## Layout

- `contracts/openapi.yaml` — the authoritative OpenAPI contract (the only
  interface of this service). `models.py` is generated from it.
- `models.py` — pydantic models generated with `datamodel-code-generator`.
  Do not hand-edit; regenerate with:
  `.venv/bin/python -m datamodel_code_generator --input contracts/openapi.yaml --input-file-type openapi --output models.py`
- `constants.py` — verified Pix/EMV constants (limits, key regexes, CRC
  parameters, tag maps) with source references to the BACEN Pix manual and
  EMVCo QRCPS.
- `utils.py` — raw EMV TLV parser (`parse_emv_tlv`) and CRC16-CCITT. Parses one
  flat TLV level only.
- `interpreter.py` — `interpret(payload)` performs semantic validation and
  returns a `DecodedInstruction`. Raw parse and interpretation are separate
  modules.
- `main.py` — FastAPI app and Problem Details handling.
- `_tests/` — unit + integration tests. Run with `python -m pytest` from this
  directory (uses `.venv`).

## Rules

- **Boundary:** decoding validates and normalizes only. It never creates or
  persists a payment, and never references another service's internal model.
- **Never log** the payload string or decoded key material.
- **Contract-first:** change the contract, regenerate models, then update the
  endpoint and tests. Error `code` values come from the generated
  `DecodeErrorCode` enum (`DECODING_*`, plus `CONTEXT_INVALID_REQUEST`) and
  must never be hard-coded in `constants.py`.
- **Stateless:** no caching, no ETags, no persistence.
- **Verification:** all tests via `.venv/bin/python -m pytest` from this
  directory; run the sdui-service suite to confirm no cross-service regression.

## Operational surface (observability change)

- `GET /health` and `GET /ready` (contract paths, `ServiceStatus` model) are
  never cached and never depend on other services.
- `GET /metrics` runs on a separate port (`METRICS_PORT`, default 9100),
  Prometheus text exposition format 0.0.4, served by the shared
  `openpix_observability` package hosted in `observability-service/`. It is
  deliberately absent from the OpenAPI contract.
- **Deployment gate:** the metrics port MUST be restricted by network policy;
  no in-app credential scheme exists.
- Runtime: `python main.py` starts both listeners; `uvicorn main:app` starts
  the API only. `APP_PORT`/`APP_HOST`/`METRICS_PORT`/`METRICS_HOST` from env.
- Data policy: correlation IDs never become metric labels; the payload string
  and decoded key material never appear in metrics or logs (covered by
  tests). Labels come from OpenAPI operationIds only.
