from __future__ import annotations

import hashlib
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

RESOURCES_DIRECTORY = Path(__file__).resolve().parent / "resources"
CONFIGURATION_FILE = RESOURCES_DIRECTORY / "configuration.json"
SCREENS_FILE = RESOURCES_DIRECTORY / "screens.json"


class ResourceFileNotFoundError(FileNotFoundError):
    """Raised when a configured static resource does not exist."""


class InvalidResourceError(ValueError):
    """Raised when a configured static resource is not valid JSON."""


class ScreenNotFoundError(LookupError):
    """Raised when a screen identifier is absent from the published document."""


def read_json_file(file_path: Path) -> dict[str, Any]:
    """Read one JSON object without coupling the data layer to FastAPI."""
    if not file_path.is_file():
        raise ResourceFileNotFoundError(f"Resource {file_path.name} was not found.")

    try:
        with file_path.open(encoding="utf-8") as file:
            value = json.load(file)
    except JSONDecodeError as error:
        raise InvalidResourceError(
            f"Resource {file_path.name} contains invalid JSON."
        ) from error

    if not isinstance(value, dict):
        raise InvalidResourceError(
            f"Resource {file_path.name} must contain a JSON object."
        )
    return value


def read_configuration() -> dict[str, Any]:
    """Return the published configuration document."""
    return read_json_file(CONFIGURATION_FILE)


def read_screens() -> dict[str, Any]:
    """Return the published screens collection."""
    return read_json_file(SCREENS_FILE)


def read_screen(screen_id: str) -> dict[str, Any]:
    """Return one screen with the collection contract metadata attached."""
    document = read_screens()
    screens = document.get("screens")
    if not isinstance(screens, list):
        raise InvalidResourceError(
            "Resource screens.json must contain a screens array."
        )

    screen = next(
        (
            candidate
            for candidate in screens
            if isinstance(candidate, dict) and candidate.get("id") == screen_id
        ),
        None,
    )
    if screen is None:
        raise ScreenNotFoundError(f"Screen {screen_id} was not found.")

    return {
        "contractVersion": document.get("contractVersion"),
        **screen,
    }


def build_etag(value: dict[str, Any], resource_name: str) -> str:
    """Build a stable validator from the representation rather than file metadata."""
    canonical_json = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(canonical_json).hexdigest()[:16]
    return f'"{resource_name}-{digest}"'
