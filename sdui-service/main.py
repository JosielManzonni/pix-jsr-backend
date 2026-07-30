from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, Path, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError

from models import (
    AppConfiguration,
    AppUpdateProblem,
    Problem,
    Screen,
    XAppDistribution,
    XAppPlatform,
    XCountryCode,
    XCurrencyCode,
)
from utils import (
    InvalidResourceError,
    ResourceFileNotFoundError,
    ScreenNotFoundError,
    build_etag,
    read_configuration,
    read_screen,
)

AppVersion = Annotated[
    str,
    StringConstraints(
        pattern=r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$",
        min_length=1,
        max_length=32,
    ),
]
AppPackage = Annotated[
    str,
    StringConstraints(
        pattern=r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$",
        min_length=3,
        max_length=255,
    ),
]
TimeZone = Annotated[
    str,
    StringConstraints(
        pattern=r"^[A-Za-z_+-]+(?:/[A-Za-z0-9_+-]+)+$",
        min_length=1,
        max_length=64,
    ),
]
CapabilitiesHeader = Annotated[
    str,
    StringConstraints(
        pattern=r"^[A-Z][A-Z0-9_]*(?:,[A-Z][A-Z0-9_]*){0,31}$",
        max_length=512,
    ),
]
ComponentVersionsHeader = Annotated[
    str,
    StringConstraints(
        pattern=r"^[a-z][a-z0-9_]*=\d+(?:,[a-z][a-z0-9_]*=\d+){0,31}$",
        max_length=512,
    ),
]
CorrelationHeader = Annotated[str, StringConstraints(min_length=1, max_length=128)]
ResourceId = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,63}$"),
]


class MobileRequestContext(BaseModel):
    """Normalized, untrusted mobile context consumed by endpoint logic."""

    model_config = ConfigDict(frozen=True)

    platform: XAppPlatform
    app_version: str
    app_build: int
    package_name: str
    distribution: XAppDistribution | None
    country: XCountryCode
    locale: str
    time_zone: str | None
    currency: XCurrencyCode | None
    capabilities: frozenset[str]
    correlation_id: str
    request_id: str | None
    traceparent: str | None
    tracestate: str | None
    if_none_match: str | None
    if_modified_since: str | None


class SduiRequestContext(MobileRequestContext):
    """Mobile context extended with screen-rendering compatibility."""

    contract_version: int
    component_versions: dict[str, int]


class ApiProblemError(Exception):
    def __init__(self, status: int, title: str, detail: str, code: str) -> None:
        super().__init__(detail)
        self.status = status
        self.title = title
        self.detail = detail
        self.code = code


app = FastAPI(
    title="OpenPix JSR Mobile SDUI API",
    version="1.1.0",
    description=(
        "Mobile read contract for evaluated feature configuration and native "
        "SDUI screen composition."
    ),
    license_info={
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
    servers=[
        {"url": "/", "description": "Host selected by the deployment environment."}
    ],
)


def _effective_correlation_id(value: str | None) -> str:
    return value or str(uuid4())


def _parse_capabilities(value: str | None) -> frozenset[str]:
    return frozenset(value.split(",")) if value else frozenset()


def _parse_component_versions(value: str) -> dict[str, int]:
    return {
        component: int(version)
        for component, version in (item.split("=", 1) for item in value.split(","))
    }


async def get_mobile_request_context(
    platform: Annotated[XAppPlatform, Header(alias="X-App-Platform")],
    app_version: Annotated[AppVersion, Header(alias="X-App-Version")],
    app_build: Annotated[int, Header(alias="X-App-Build", ge=1, le=2147483647)],
    package_name: Annotated[AppPackage, Header(alias="X-App-Package")],
    country: Annotated[XCountryCode, Header(alias="X-Country-Code")],
    locale: Annotated[
        str,
        Header(alias="Accept-Language", min_length=2, max_length=128),
    ],
    distribution: Annotated[
        XAppDistribution | None,
        Header(alias="X-App-Distribution"),
    ] = None,
    time_zone: Annotated[TimeZone | None, Header(alias="X-Time-Zone")] = None,
    currency: Annotated[
        XCurrencyCode | None,
        Header(alias="X-Currency-Code"),
    ] = None,
    capabilities: Annotated[
        CapabilitiesHeader | None,
        Header(alias="X-App-Capabilities"),
    ] = None,
    correlation_id: Annotated[
        CorrelationHeader | None,
        Header(alias="X-Correlation-ID"),
    ] = None,
    request_id: Annotated[
        CorrelationHeader | None,
        Header(alias="X-Request-ID"),
    ] = None,
    traceparent: Annotated[
        str | None,
        Header(pattern=r"^[\da-f]{2}-[\da-f]{32}-[\da-f]{16}-[\da-f]{2}$"),
    ] = None,
    tracestate: Annotated[
        str | None,
        Header(max_length=512),
    ] = None,
    if_none_match: Annotated[
        str | None,
        Header(alias="If-None-Match", max_length=128),
    ] = None,
    if_modified_since: Annotated[
        str | None,
        Header(alias="If-Modified-Since"),
    ] = None,
) -> MobileRequestContext:
    return MobileRequestContext(
        platform=platform,
        app_version=app_version,
        app_build=app_build,
        package_name=package_name,
        distribution=distribution,
        country=country,
        locale=locale,
        time_zone=time_zone,
        currency=currency,
        capabilities=_parse_capabilities(capabilities),
        correlation_id=_effective_correlation_id(correlation_id),
        request_id=request_id,
        traceparent=traceparent,
        tracestate=tracestate,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
    )


async def get_sdui_request_context(
    context: Annotated[MobileRequestContext, Depends(get_mobile_request_context)],
    contract_version: Annotated[
        int,
        Header(alias="X-SDUI-Contract-Version", ge=1),
    ],
    component_versions: Annotated[
        ComponentVersionsHeader,
        Header(alias="X-SDUI-Component-Versions"),
    ],
) -> SduiRequestContext:
    return SduiRequestContext(
        **context.model_dump(),
        contract_version=contract_version,
        component_versions=_parse_component_versions(component_versions),
    )


MobileContext = Annotated[MobileRequestContext, Depends(get_mobile_request_context)]
SduiContext = Annotated[SduiRequestContext, Depends(get_sdui_request_context)]


def _problem_response(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    code: str,
) -> JSONResponse:
    correlation_id = _effective_correlation_id(
        request.headers.get("X-Correlation-ID")
        if len(request.headers.get("X-Correlation-ID", "")) <= 128
        else None
    )
    problem = Problem(
        type=f"https://openpix.dev/problems/{code.lower().replace('_', '-')}",
        title=title,
        status=status,
        detail=detail,
        instance=request.url.path,
        code=code,
        correlationId=correlation_id,
    )
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(mode="json", exclude_none=True),
        media_type="application/problem+json",
        headers={"X-Correlation-ID": correlation_id},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    invalid_fields = ", ".join(
        str(item) for failure in error.errors() for item in failure["loc"][1:]
    )
    return _problem_response(
        request,
        status=400,
        title="Invalid request context",
        detail=f"Invalid or missing request value: {invalid_fields}.",
        code="CONTEXT_INVALID_REQUEST",
    )


@app.exception_handler(ApiProblemError)
async def api_problem_exception_handler(
    request: Request,
    error: ApiProblemError,
) -> JSONResponse:
    return _problem_response(
        request,
        status=error.status,
        title=error.title,
        detail=error.detail,
        code=error.code,
    )


def _load_configuration() -> AppConfiguration:
    try:
        return AppConfiguration.model_validate(read_configuration())
    except ResourceFileNotFoundError as error:
        raise ApiProblemError(
            404,
            "Configuration not found",
            str(error),
            "SDUI_CONFIGURATION_NOT_FOUND",
        ) from error
    except (InvalidResourceError, ValidationError) as error:
        raise ApiProblemError(
            500,
            "Invalid configuration resource",
            "The published configuration resource is invalid.",
            "SDUI_INVALID_CONFIGURATION",
        ) from error


def _load_screen(screen_id: str) -> Screen:
    try:
        return Screen.model_validate(read_screen(screen_id))
    except ScreenNotFoundError as error:
        raise ApiProblemError(
            404,
            "Screen not found",
            "The requested screen does not exist.",
            "SDUI_SCREEN_NOT_FOUND",
        ) from error
    except ResourceFileNotFoundError as error:
        raise ApiProblemError(
            404,
            "Screen not found",
            "No published screen collection is available.",
            "SDUI_SCREEN_NOT_FOUND",
        ) from error
    except (InvalidResourceError, ValidationError) as error:
        raise ApiProblemError(
            500,
            "Invalid screen resource",
            "The published screen resource is invalid.",
            "SDUI_INVALID_SCREEN",
        ) from error


def _representation_headers(
    context: MobileRequestContext,
    *,
    contract_version: int,
    etag: str,
    revision_header: str,
    revision: int,
) -> dict[str, str]:
    return {
        "X-Correlation-ID": context.correlation_id,
        "X-Contract-Version": str(contract_version),
        revision_header: str(revision),
        "Content-Language": "pt-BR",
        "ETag": etag,
        "Cache-Control": "private, max-age=300",
        "Vary": (
            "X-App-Platform, X-App-Build, X-Country-Code, "
            "Accept-Language, X-App-Capabilities"
        ),
    }


def _apply_headers(response: Response, headers: dict[str, str]) -> None:
    for name, value in headers.items():
        response.headers[name] = value


def _validate_component_compatibility(
    screen: Screen,
    context: SduiRequestContext,
) -> None:
    unsupported = sorted(
        {
            component.root.type
            for component in screen.components
            if str(context.component_versions.get(component.root.type))
            not in component.root.compatibilityVersion
        }
    )
    if unsupported:
        raise ApiProblemError(
            406,
            "Unsupported SDUI component",
            "The client cannot render the required component types: "
            + ", ".join(unsupported)
            + ".",
            "SDUI_UNSUPPORTED_COMPONENT",
        )


@app.get(
    "/mobile/v1/configuration",
    response_model=AppConfiguration,
    responses={
        400: {"model": Problem},
        404: {"model": Problem},
        406: {"model": Problem},
        426: {"model": AppUpdateProblem},
        500: {"model": Problem},
    },
    tags=["Mobile configuration"],
)
async def get_mobile_configuration(
    context: MobileContext,
    response: Response,
) -> AppConfiguration | Response:
    """Return the static configuration as its generated contract model."""
    configuration = _load_configuration()
    serialized = configuration.model_dump(mode="json", exclude_none=True)
    etag = build_etag(serialized, "configuration")
    headers = _representation_headers(
        context,
        contract_version=configuration.contractVersion,
        etag=etag,
        revision_header="X-Configuration-Revision",
        revision=configuration.revision or 1,
    )
    if context.if_none_match == etag:
        return Response(status_code=304, headers=headers)

    _apply_headers(response, headers)
    return configuration


@app.get(
    "/mobile/v1/screens/{screenId}",
    response_model=Screen,
    responses={
        400: {"model": Problem},
        404: {"model": Problem},
        406: {"model": Problem},
        426: {"model": AppUpdateProblem},
        500: {"model": Problem},
    },
    tags=["Mobile screens"],
)
async def get_mobile_screen(
    screen_id: Annotated[ResourceId, Path(alias="screenId")],
    context: SduiContext,
    response: Response,
) -> Screen | Response:
    """Return one static screen as its generated contract model."""
    screen = _load_screen(screen_id)
    if context.contract_version < screen.contractVersion:
        raise ApiProblemError(
            406,
            "Unsupported SDUI contract",
            "The client cannot safely interpret this screen contract.",
            "SDUI_UNSUPPORTED_CONTRACT",
        )
    _validate_component_compatibility(screen, context)

    serialized = screen.model_dump(mode="json", exclude_none=True)
    etag = build_etag(serialized, f"screen-{screen_id}")
    headers = _representation_headers(
        context,
        contract_version=screen.contractVersion,
        etag=etag,
        revision_header="X-Screen-Revision",
        revision=screen.revision or 1,
    )
    if context.if_none_match == etag:
        return Response(status_code=304, headers=headers)

    _apply_headers(response, headers)
    return screen
