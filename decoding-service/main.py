from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import uuid4

import yaml
from fastapi import FastAPI, Header, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import StringConstraints

from interpreter import interpret
from models import (
    DecodeErrorCode,
    DecodedInstruction,
    DecodePayloadRequest,
    ProblemDetails,
)
from utils import DecodeError

app = FastAPI(
    title="OpenPix JSR Pix Decoding API",
    version="1.0.0",
    description=(
        "Stateless Pix/BR Code decoding boundary: validates and normalizes a "
        "raw payload into an interpreted payment instruction. It never creates "
        "or persists a payment and never logs payloads or decoded key material."
    ),
    license_info={
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
    servers=[
        {"url": "/", "description": "Host selected by the deployment environment."}
    ],
)

CorrelationHeader = Annotated[str, StringConstraints(min_length=1, max_length=128)]

# The OpenAPI contract is the source of truth. Serve it verbatim so the runtime
# schema can never drift from contracts/openapi.yaml.
CONTRACT_PATH = Path(__file__).resolve().parent / "contracts" / "openapi.yaml"


def custom_openapi() -> dict:
    if app.openapi_schema is None:
        with CONTRACT_PATH.open(encoding="utf-8") as contract_file:
            app.openapi_schema = yaml.safe_load(contract_file)
    return app.openapi_schema


app.openapi = custom_openapi

_TITLE_BY_CODE: dict[DecodeErrorCode, str] = {
    DecodeErrorCode.DECODING_PAYLOAD_TOO_LONG: "Payload too long",
    DecodeErrorCode.DECODING_INVALID_CHARSET: "Invalid character set",
    DecodeErrorCode.DECODING_MALFORMED_TLV: "Malformed TLV",
    DecodeErrorCode.DECODING_CRC_MISMATCH: "CRC mismatch",
    DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD: "Missing mandatory field",
    DecodeErrorCode.DECODING_UNSUPPORTED_CURRENCY: "Unsupported currency",
    DecodeErrorCode.DECODING_INVALID_KEY: "Invalid Pix key",
    DecodeErrorCode.DECODING_INVALID_PAYLOAD: "Invalid payload",
    DecodeErrorCode.CONTEXT_INVALID_REQUEST: "Invalid request context",
}


def _effective_correlation_id(value: str | None) -> str:
    return value or str(uuid4())


def _problem_response(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    code: DecodeErrorCode,
) -> JSONResponse:
    raw = request.headers.get("X-Correlation-ID")
    correlation_id = _effective_correlation_id(
        raw if raw is not None and len(raw) <= 128 else None
    )
    problem = ProblemDetails(
        type=f"https://openpix.dev/problems/{code.value.lower().replace('_', '-')}",
        title=title,
        status=status,
        detail=detail,
        code=code,
        correlationId=correlation_id,
    )
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(mode="json", exclude_none=True),
        media_type="application/problem+json",
        headers={"X-Correlation-ID": correlation_id},
    )


@app.exception_handler(DecodeError)
async def decode_error_handler(request: Request, error: DecodeError) -> JSONResponse:
    return _problem_response(
        request,
        status=422,
        title=_TITLE_BY_CODE.get(error.code, "Decoding failed"),
        detail=error.detail,
        code=error.code,
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
        code=DecodeErrorCode.CONTEXT_INVALID_REQUEST,
    )


@app.post(
    "/decode/v1/pix-payloads",
    response_model=DecodedInstruction,
    responses={422: {"model": ProblemDetails}},
    tags=["Pix payload decoding"],
)
async def decode_pix_payload(
    body: DecodePayloadRequest,
    response: Response,
    correlation_id: Annotated[
        CorrelationHeader | None, Header(alias="X-Correlation-ID")
    ] = None,
) -> DecodedInstruction:
    # Boundary: never log the payload or decoded key material. This endpoint
    # performs no logging at all; structured decoding errors become a 422
    # Problem Details body via the exception handler above.
    response.headers["X-Correlation-ID"] = _effective_correlation_id(correlation_id)
    return interpret(body.payload)
