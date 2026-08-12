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
- `resources/assets/` — supporting assets actually read at runtime (e.g.
  `pix_home` mockup assets). Architecture diagrams do not belong here — see
  `docs/diagrams/`.

## Docs

- `docs/adrs/`, `docs/rfcs/` — decisions owned by this service.
- `docs/diagrams/` — Mermaid/Excalidraw sources for this service.
- `docs/medium/` — brief context for regenerating the Medium articles that
  live in `pix-jsr-publication` (not duplicated here).
- Cross-service context: `../docs/architecture/contexts/CTX-SDUI.md`.

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
