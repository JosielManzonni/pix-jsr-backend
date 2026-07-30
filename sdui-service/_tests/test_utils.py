from __future__ import annotations

import json

import pytest

import utils


def test_read_json_file_returns_object(tmp_path):
    resource = tmp_path / "resource.json"
    resource.write_text('{"contractVersion": 1}', encoding="utf-8")

    assert utils.read_json_file(resource) == {"contractVersion": 1}


def test_read_json_file_rejects_missing_file(tmp_path):
    with pytest.raises(utils.ResourceFileNotFoundError, match="missing.json"):
        utils.read_json_file(tmp_path / "missing.json")


def test_read_json_file_rejects_invalid_json(tmp_path):
    resource = tmp_path / "invalid.json"
    resource.write_text("{", encoding="utf-8")

    with pytest.raises(utils.InvalidResourceError, match="invalid JSON"):
        utils.read_json_file(resource)


def test_read_json_file_rejects_non_object_json(tmp_path):
    resource = tmp_path / "array.json"
    resource.write_text("[]", encoding="utf-8")

    with pytest.raises(utils.InvalidResourceError, match="JSON object"):
        utils.read_json_file(resource)


def test_read_configuration_uses_configured_resource(monkeypatch, tmp_path):
    resource = tmp_path / "configuration.json"
    resource.write_text('{"contractVersion": 7}', encoding="utf-8")
    monkeypatch.setattr(utils, "CONFIGURATION_FILE", resource)

    assert utils.read_configuration()["contractVersion"] == 7


def test_read_screen_attaches_collection_contract_version(monkeypatch):
    monkeypatch.setattr(
        utils,
        "read_screens",
        lambda: {
            "contractVersion": 2,
            "screens": [{"id": "pix_home", "components": []}],
        },
    )

    assert utils.read_screen("pix_home") == {
        "contractVersion": 2,
        "id": "pix_home",
        "components": [],
    }


def test_read_screen_rejects_unknown_screen(monkeypatch):
    monkeypatch.setattr(
        utils,
        "read_screens",
        lambda: {"contractVersion": 1, "screens": []},
    )

    with pytest.raises(utils.ScreenNotFoundError, match="missing"):
        utils.read_screen("missing")


def test_read_screen_rejects_invalid_collection(monkeypatch):
    monkeypatch.setattr(
        utils,
        "read_screens",
        lambda: {"contractVersion": 1, "screens": {}},
    )

    with pytest.raises(utils.InvalidResourceError, match="screens array"):
        utils.read_screen("pix_home")


def test_build_etag_is_stable_and_representation_sensitive():
    first = {"b": 2, "a": 1}
    same_content = json.loads('{"a": 1, "b": 2}')

    first_etag = utils.build_etag(first, "configuration")

    assert first_etag == utils.build_etag(same_content, "configuration")
    assert first_etag != utils.build_etag({"a": 2, "b": 2}, "configuration")
    assert first_etag.startswith('"configuration-')
