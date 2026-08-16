from __future__ import annotations

import os
from threading import Thread

import uvicorn

from .logging import configure_logging
from .metrics import get_metrics


def register_probes(app, *, response_model, ok_value) -> None:
    """Add the contract probe endpoints (GET /health, GET /ready) to a service.

    Endpoints are never cached and never depend on other services. The
    response model is each service's generated contract model.
    """

    @app.get(
        "/health",
        operation_id="getHealth",
        tags=["Operational probes"],
        response_model=response_model,
    )
    async def health():
        """Liveness: process alive and serving. Never cached, no dependencies."""
        return response_model(status=ok_value)

    @app.get(
        "/ready",
        operation_id="getReady",
        tags=["Operational probes"],
        response_model=response_model,
    )
    async def ready():
        """Readiness: this process can accept work. Never depends on other services."""
        return response_model(status=ok_value)


_servers: tuple[uvicorn.Server, uvicorn.Server] | None = None


def get_servers() -> tuple[uvicorn.Server, uvicorn.Server] | None:
    """Running listeners, for shutdown from tests or operators."""
    return _servers


def serve(app) -> None:
    """Run the API port and the metrics port as two listeners in one process.

    Ports come from the environment (APP_PORT default 8000, METRICS_PORT
    default 9100). The metrics port serves only GET /metrics and is protected
    by deployment network policy, never by code in this process.
    """
    global _servers
    configure_logging()
    api_server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=os.environ.get("APP_HOST", "0.0.0.0"),
            port=int(os.environ.get("APP_PORT", "8000")),
        )
    )
    metrics_server = uvicorn.Server(
        uvicorn.Config(
            get_metrics().app,
            host=os.environ.get("METRICS_HOST", "0.0.0.0"),
            port=int(os.environ.get("METRICS_PORT", "9100")),
        )
    )
    _servers = (api_server, metrics_server)
    Thread(target=metrics_server.run, daemon=True).start()
    api_server.run()
