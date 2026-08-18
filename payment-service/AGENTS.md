# payment-service

Payment lifecycle boundary. It creates a Payment from normalized
decoded-instruction data, confirms or fails it through an Executor port, and
serves per-user retrieval and history. Creation is idempotent per caller and
Idempotency-Key; responses under `/payments` are never cacheable.

## Layout

- `docs/` — decisions owned by this service (ADRs/RFCs land here when they
  arrive). Cross-service context:
  `../docs/architecture/contexts/CTX-PAYMENT.md`.
- `contracts/openapi.yaml` — the authoritative OpenAPI contract (the only
  interface of this service). `models.py` is generated from it. The history
  operation is declared `post` with the `x-runtime-method: QUERY` note, per
  the payment spec (OpenAPI 3.0.3 cannot declare RFC 10008 QUERY).
- `models.py` — pydantic models generated with `datamodel-code-generator`.
  Do not hand-edit; regenerate with:
  `.venv/bin/python -m datamodel_code_generator --input contracts/openapi.yaml --input-file-type openapi --output models.py --strict-nullable`
  (`--strict-nullable` keeps required+nullable fields such as
  `PaymentHistoryPage.nextCursor` typed `str | None`.)
- `main.py` — FastAPI app and Problem Details handling. Serves
  `contracts/openapi.yaml` verbatim via `custom_openapi()`.
- `_tests/` — unit + integration tests. Run with `python -m pytest` from this
  directory (uses `.venv`).

## Rules

- **Documentation:** `docs/adrs/` and `docs/rfcs/` are authoritative for this
  service's payment decisions; `../docs/architecture/contexts/CTX-PAYMENT.md`
  is the cross-service context. The stale richer lifecycle and confirm/cancel
  behavior is superseded and is not implemented.
- **Contract-first:** change the contract, regenerate models, then update the
  endpoint and tests. The served OpenAPI document must equal
  `contracts/openapi.yaml`.
- **No raw payloads:** `POST /payments` accepts normalized fields only; there
  is no BR Code field in the schema and no runtime call to decoding-service.
- **Financial data hygiene:** responses under `/payments` carry
  `Cache-Control: no-store`; Pix keys, account data, Idempotency-Key values,
  raw payloads, and internal database ids never appear in logs, metrics, or
  traces.
- **Auth:** the `X-API-Key` header identifies the User; missing/unknown keys
  are 401 Problem Details. `/health` and `/ready` need no auth.
- **No DICT surface:** no key registration, portability, claim, or
  key-registry operation exists.
- **Persistence:** `PaymentRepository` port; SQLite via stdlib `sqlite3`.
  Never hold a database lock while calling the Executor.
- **Verification:** all tests via `.venv/bin/python -m pytest` from this
  directory; run the sdui-service and decoding-service suites to confirm no
  cross-service regression.