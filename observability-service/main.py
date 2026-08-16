from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import FastAPI

from models import ServiceStatus, Status
from openpix_observability import (
    ObservabilityMiddleware,
    configure_logging,
    register_probes,
    serve,
)

app = FastAPI(
    title="OpenPix JSR Observability API",
    version="1.1.0",
    description=(
        "Operational surface shared by OpenPix JSR services: liveness and "
        "readiness probes. The observability service also hosts the shared "
        "instrumentation package used by every service. It exposes no "
        "business data and never processes payments."
    ),
    license_info={
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
    servers=[
        {"url": "/", "description": "Host selected by the deployment environment."}
    ],
)

# The OpenAPI contract is the source of truth. Serve it verbatim so the runtime
# schema can never drift from contracts/openapi.yaml.
CONTRACT_PATH = Path(__file__).resolve().parent / "contracts" / "openapi.yaml"


def custom_openapi() -> dict:
    if app.openapi_schema is None:
        with CONTRACT_PATH.open(encoding="utf-8") as contract_file:
            app.openapi_schema = yaml.safe_load(contract_file)
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(ObservabilityMiddleware)
configure_logging()

register_probes(app, response_model=ServiceStatus, ok_value=Status.ok)


if __name__ == "__main__":
    serve(app)
