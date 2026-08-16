# AGENTS.md — sdui-service/

Guidance for the SDUI service (the only implemented service today).

## Boundary

Python/FastAPI service owning the **sdui** bounded context: mobile
configuration, evaluated feature availability, SDUI screen composition, and
renderer compatibility. It does not execute payments or interpret Pix payloads.

## Runtime sources

- `main.py` — FastAPI app and endpoints.
- `models.py` — Pydantic models; generated from the contract.
- `utils.py` — helpers (resource loading, ETags).
- `resources/configuration.json` and `resources/screens.json` — static runtime
  sources read by the service.
- `resources/assets/` — supporting assets.

## Contract and models

- `contracts/openapi.yaml` is the authoritative service contract.
- `models.py` is generated from it (see `datamodel-code-generator` in
  `requirements-dev.txt`). Keep the contract and models in sync; a contract
  change must be reflected in the generated models.

## Tests

- Tests live in `_tests/` (`test_main.py`, `test_utils.py`, `conftest.py`).
- Verified command — run from this directory:
  `python -m pytest`
- Prerequisite: `requirements-dev.txt` must already be installed in the active
  environment. Do not add installation automation; dependency setup is
  environment-specific and unmanaged here.

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
- Data policy: correlation IDs never become metric labels; labels come from
  OpenAPI operationIds only.
- Note: `models.py` is a legacy artifact (older generator, pre-header style)
  that pinned `datamodel-code-generator` 0.65.1 cannot reproduce without
  dropping the `X*` header-validation enums `main.py` imports. The additive
  `ServiceStatus`/`Status1` models are appended in generator style; a future
  migration should regenerate and update `main.py` header typing together.
