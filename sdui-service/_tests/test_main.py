from __future__ import annotations

import asyncio

import httpx
import pytest

import main
from models import Screen
from utils import InvalidResourceError, ResourceFileNotFoundError

BASE_HEADERS = {
    "X-App-Platform": "android",
    "X-App-Version": "1.4.2",
    "X-App-Build": "10402",
    "X-App-Package": "com.openpix.jsr",
    "X-Country-Code": "BR",
    "Accept-Language": "pt-BR",
}
SDUI_HEADERS = {
    "X-SDUI-Contract-Version": "1",
    "X-SDUI-Component-Versions": "text=1,spacer=1,feature=1",
}


def api_get(path: str, headers: dict[str, str]) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(path, headers=headers)

    return asyncio.run(request())


def test_get_mobile_configuration_converts_json_to_contract_model():
    response = api_get(
        "/mobile/v1/configuration",
        BASE_HEADERS | {"X-Correlation-ID": "correlation-123"},
    )

    assert response.status_code == 200
    assert response.json()["contractVersion"] == 1
    assert response.json()["features"][0]["id"] == "pix_qr"
    assert response.headers["x-correlation-id"] == "correlation-123"
    assert response.headers["x-contract-version"] == "1"
    assert response.headers["x-configuration-revision"] == "1"
    assert response.headers["content-language"] == "pt-BR"
    assert response.headers["cache-control"] == "private, max-age=300"
    assert "X-App-Build" in response.headers["vary"]
    assert response.headers["etag"].startswith('"configuration-')


def test_get_mobile_configuration_returns_304_for_matching_etag():
    initial = api_get("/mobile/v1/configuration", BASE_HEADERS)

    response = api_get(
        "/mobile/v1/configuration",
        BASE_HEADERS | {"If-None-Match": initial.headers["etag"]},
    )

    assert response.status_code == 304
    assert response.content == b""
    assert response.headers["etag"] == initial.headers["etag"]


def test_get_mobile_configuration_generates_correlation_id():
    response = api_get("/mobile/v1/configuration", BASE_HEADERS)

    assert response.status_code == 200
    assert response.headers["x-correlation-id"]


def test_get_mobile_configuration_rejects_missing_required_header():
    headers = BASE_HEADERS.copy()
    headers.pop("X-App-Build")

    response = api_get("/mobile/v1/configuration", headers)

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "CONTEXT_INVALID_REQUEST"
    assert "X-App-Build" in response.json()["detail"]


def test_get_mobile_configuration_maps_missing_resource(monkeypatch):
    def missing_configuration():
        raise ResourceFileNotFoundError("Resource configuration.json was not found.")

    monkeypatch.setattr(main, "read_configuration", missing_configuration)

    response = api_get("/mobile/v1/configuration", BASE_HEADERS)

    assert response.status_code == 404
    assert response.json()["code"] == "SDUI_CONFIGURATION_NOT_FOUND"


def test_get_mobile_configuration_maps_invalid_resource(monkeypatch):
    def invalid_configuration():
        raise InvalidResourceError("invalid")

    monkeypatch.setattr(main, "read_configuration", invalid_configuration)

    response = api_get("/mobile/v1/configuration", BASE_HEADERS)

    assert response.status_code == 500
    assert response.json()["code"] == "SDUI_INVALID_CONFIGURATION"


def test_get_mobile_screen_converts_selected_json_to_contract_model():
    response = api_get(
        "/mobile/v1/screens/pix_home",
        BASE_HEADERS | SDUI_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["id"] == "pix_home"
    assert response.json()["contractVersion"] == 1
    assert response.json()["components"][0]["type"] == "text"
    assert response.json()["components"][0]["compatibilityVersion"] == ["1"]
    assert response.headers["x-screen-revision"] == "1"
    assert response.headers["etag"].startswith('"screen-pix_home-')


def test_get_mobile_screen_returns_304_for_matching_etag():
    headers = BASE_HEADERS | SDUI_HEADERS
    initial = api_get("/mobile/v1/screens/pix_home", headers)

    response = api_get(
        "/mobile/v1/screens/pix_home",
        headers | {"If-None-Match": initial.headers["etag"]},
    )

    assert response.status_code == 304
    assert response.content == b""


def test_get_mobile_screen_returns_problem_for_unknown_screen():
    response = api_get(
        "/mobile/v1/screens/unknown",
        BASE_HEADERS | SDUI_HEADERS | {"X-Correlation-ID": "screen-request"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "SDUI_SCREEN_NOT_FOUND"
    assert response.json()["correlationId"] == "screen-request"


def test_get_mobile_screen_rejects_unsupported_contract(monkeypatch):
    screen = Screen.model_validate(
        {
            "contractVersion": 2,
            "id": "pix_home",
            "components": [],
        }
    )
    monkeypatch.setattr(main, "_load_screen", lambda _: screen)

    response = api_get(
        "/mobile/v1/screens/pix_home",
        BASE_HEADERS | SDUI_HEADERS,
    )

    assert response.status_code == 406
    assert response.json()["code"] == "SDUI_UNSUPPORTED_CONTRACT"


def test_get_mobile_screen_rejects_unsupported_component():
    response = api_get(
        "/mobile/v1/screens/pix_home",
        BASE_HEADERS
        | {
            "X-SDUI-Contract-Version": "1",
            "X-SDUI-Component-Versions": "text=1",
        },
    )

    assert response.status_code == 406
    assert response.json()["code"] == "SDUI_UNSUPPORTED_COMPONENT"
    assert "feature" in response.json()["detail"]
    assert "spacer" in response.json()["detail"]


def test_get_mobile_screen_rejects_incompatible_component_version():
    response = api_get(
        "/mobile/v1/screens/pix_home",
        BASE_HEADERS
        | {
            "X-SDUI-Contract-Version": "1",
            "X-SDUI-Component-Versions": "text=2,spacer=1,feature=1",
        },
    )

    assert response.status_code == 406
    assert response.json()["code"] == "SDUI_UNSUPPORTED_COMPONENT"
    assert "text" in response.json()["detail"]


@pytest.mark.parametrize(
    ("header", "value"),
    [
        ("X-App-Version", "version-one"),
        ("X-App-Platform", "ios"),
        ("X-Country-Code", "US"),
        ("X-App-Capabilities", "pix_qr"),
        ("X-SDUI-Component-Versions", "text:1"),
    ],
)
def test_get_mobile_screen_rejects_invalid_context(header, value):
    response = api_get(
        "/mobile/v1/screens/pix_home",
        (BASE_HEADERS | SDUI_HEADERS) | {header: value},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "CONTEXT_INVALID_REQUEST"


def test_context_normalizes_capabilities_and_component_versions():
    mobile_context = asyncio.run(
        main.get_mobile_request_context(
            platform=main.XAppPlatform.android,
            app_version="1.4.2",
            app_build=10402,
            package_name="com.openpix.jsr",
            country=main.XCountryCode.BR,
            locale="pt-BR",
            capabilities="PIX_QR,PAYMENT",
            correlation_id="correlation",
        )
    )
    sdui_context = asyncio.run(
        main.get_sdui_request_context(
            context=mobile_context,
            contract_version=1,
            component_versions="text=1,feature=2",
        )
    )

    assert mobile_context.capabilities == frozenset({"PIX_QR", "PAYMENT"})
    assert sdui_context.component_versions == {"text": 1, "feature": 2}
    assert sdui_context.correlation_id == "correlation"
