from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from main import app

CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "openapi.yaml"


def test_served_openapi_matches_contract() -> None:
    """The served /openapi.json must equal contracts/openapi.yaml verbatim."""
    response = TestClient(app).get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))