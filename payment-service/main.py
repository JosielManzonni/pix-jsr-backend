from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, CollectorRegistry, generate_latest
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from consumer import Consumer
from executor import PedroBankFake
from models import PaymentCreate, PaymentHistoryQuery
from money import InvalidAmountError, parse_amount
from repository import (
    IdempotencyConflictError,
    InvalidCursorError,
    PaymentNotFoundError,
    SqlitePayments,
)

app_logger = logging.getLogger("openpix.payment")

app = FastAPI(
    title="OpenPix JSR Payment API",
    version="1.0.0",
    description=(
        "Payment lifecycle boundary: creates a Payment from normalized "
        "decoded-instruction data, confirms or fails it through an Executor, "
        "and serves per-user retrieval and history. It never accepts a raw "
        "Pix BR Code payload, performs no DICT operations, and never logs "
        "Pix keys, account data, idempotency keys, or internal ids."
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


class PaymentAPIError(Exception):
    def __init__(self, status: int, code: str, title: str, detail: str) -> None:
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail


_TITLES = {
    "PAYMENT_INVALID_REQUEST": "Invalid request context",
    "PAYMENT_UNAUTHENTICATED": "Unauthenticated",
    "PAYMENT_NOT_FOUND": "Payment not found",
    "PAYMENT_IDEMPOTENCY_CONFLICT": "Idempotency conflict",
    "PAYMENT_VALIDATION_FAILED": "Validation failed",
    "PAYMENT_METHOD_NOT_ALLOWED": "Method not allowed",
}
_TRACEPARENT_RE = re.compile(
    r"^(?P<version>[0-9a-fA-F]{2})-(?P<trace>[0-9a-fA-F]{32})-"
    r"(?P<span>[0-9a-fA-F]{16})-(?P<flags>[0-9a-fA-F]{2})$"
)


def _problem_type(code: str) -> str:
    return f"https://openpix.dev/problems/{code.lower().replace('_', '-')}"


def _request_correlation_id(request: Request) -> str:
    value = getattr(request.state, "correlation_id", None)
    if value:
        return value
    header = request.headers.get("X-Correlation-ID")
    return header if header and len(header) <= 128 else str(uuid4())


def _problem_response(request: Request, error: PaymentAPIError) -> JSONResponse:
    correlation_id = _request_correlation_id(request)
    body = {
        "type": _problem_type(error.code),
        "title": error.title,
        "status": error.status,
        "detail": error.detail,
        "code": error.code,
        "correlationId": correlation_id,
    }
    headers = {"X-Correlation-ID": correlation_id}
    if request.url.path.startswith("/payments"):
        headers["Cache-Control"] = "no-store"
    return JSONResponse(
        status_code=error.status,
        content=body,
        media_type="application/problem+json",
        headers=headers,
    )


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id or len(correlation_id) > 128:
            correlation_id = str(uuid4())
        traceparent = _traceparent(request.headers.get("traceparent"))
        request.state.correlation_id = correlation_id
        request.state.traceparent = traceparent
        try:
            response = await call_next(request)
        except Exception:
            # The exception handler still receives the request state. Do not log
            # exception text because it could contain financial request data.
            raise
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["traceparent"] = traceparent
        if request.url.path.startswith("/payments"):
            response.headers["Cache-Control"] = "no-store"
        HTTP_REQUESTS.labels(request.method, str(response.status_code)).inc()
        app_logger.info(
            json.dumps(
                {
                    "event": "http.request",
                    "method": request.method,
                    "status": response.status_code,
                    "correlationId": correlation_id,
                },
                separators=(",", ":"),
            )
        )
        return response


def _traceparent(value: str | None) -> str:
    if value:
        match = _TRACEPARENT_RE.fullmatch(value)
        if (
            match
            and match["version"].lower() != "ff"
            and int(match["trace"], 16) != 0
            and int(match["span"], 16) != 0
        ):
            return value
    return f"00-{uuid4().hex}-{uuid4().hex[:16]}-01"


app.add_middleware(CorrelationMiddleware)


METRICS_REGISTRY = CollectorRegistry()
HTTP_REQUESTS = Counter(
    "openpix_http_requests_total",
    "HTTP requests handled by the payment service.",
    ("method", "status"),
    registry=METRICS_REGISTRY,
)


async def _metrics_response(scope, receive, send):
    body = generate_latest(METRICS_REGISTRY)
    response = Response(content=body, media_type=CONTENT_TYPE_LATEST)
    await response(scope, receive, send)


async def metrics_app(scope, receive, send):
    if scope["type"] != "http":
        await _metrics_response(scope, receive, send)
        return
    if scope["path"] not in {"/", "/metrics"}:
        response = Response(status_code=404)
        await response(scope, receive, send)
        return
    await _metrics_response(scope, receive, send)


# The service can be run with ``uvicorn main:metrics_app --port ...`` on a
# separate port; it is intentionally not mounted in the contract app.


def _configured_db_path() -> str:
    return os.getenv(
        "OPENPIX_DB_PATH",
        str(Path(tempfile.gettempdir()) / "openpix-payment.db"),
    )


def _make_repository(path: str) -> SqlitePayments:
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    return SqlitePayments(path)


_INITIAL_DB_PATH = _configured_db_path()
repository = _make_repository(_INITIAL_DB_PATH)


def _api_keys() -> dict[str, str]:
    raw = os.getenv("OPENPIX_API_KEYS", "")
    keys: dict[str, str] = {}
    for item in raw.split(","):
        key, separator, user = item.partition(":")
        if separator and key and user:
            keys[key] = user
    return keys


def _as_error(status: int, code: str, detail: str) -> PaymentAPIError:
    return PaymentAPIError(status, code, _TITLES[code], detail)


def _authenticate(request: Request) -> str:
    user_id = _api_keys().get(request.headers.get("X-API-Key", ""))
    if user_id is None:
        raise _as_error(
            401,
            "PAYMENT_UNAUTHENTICATED",
            "A valid X-API-Key header is required.",
        )
    return user_id


def _idempotency_key(request: Request) -> str:
    value = request.headers.get("Idempotency-Key")
    if value is None or not 1 <= len(value) <= 128:
        raise _as_error(
            422,
            "PAYMENT_VALIDATION_FAILED",
            "Idempotency-Key must be between 1 and 128 characters.",
        )
    return value


async def _json_body(request: Request, *, missing_is_invalid: bool) -> object:
    raw = await request.body()
    if not raw:
        if missing_is_invalid:
            raise _as_error(
                400,
                "PAYMENT_INVALID_REQUEST",
                "A JSON request body is required.",
            )
        return {}
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _as_error(
            400 if missing_is_invalid else 422,
            "PAYMENT_INVALID_REQUEST" if missing_is_invalid else "PAYMENT_VALIDATION_FAILED",
            "The request body must contain valid JSON."
            if missing_is_invalid
            else "The history query failed validation.",
        ) from None


def _validation_error(fields: list[str], detail: str | None = None) -> PaymentAPIError:
    field_text = ", ".join(dict.fromkeys(fields)) or "request"
    return _as_error(
        422,
        "PAYMENT_VALIDATION_FAILED",
        detail or f"Invalid value for: {field_text}.",
    )


def _validate_create_body(body: object) -> PaymentCreate:
    if not isinstance(body, dict):
        raise _as_error(
            400,
            "PAYMENT_INVALID_REQUEST",
            "The request body must be a JSON object.",
        )
    fields = [
        field
        for field in ("payeePixKey", "amount", "description")
        if field in body
        and not (
            (field in {"payeePixKey", "amount"} and type(body[field]) is str)
            or (field == "description" and (body[field] is None or type(body[field]) is str))
        )
    ]
    if fields:
        raise _validation_error(fields)
    try:
        payment = PaymentCreate.model_validate(body)
    except ValidationError as error:
        fields = [str(location[-1]) for location in (item["loc"] for item in error.errors())]
        raise _validation_error(fields) from None
    try:
        parse_amount(payment.amount)
    except InvalidAmountError as error:
        raise _validation_error(["amount"], str(error)) from None
    return payment


def _fingerprint(payment: PaymentCreate) -> str:
    canonical = json.dumps(
        payment.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _payment_response(payment, status: int) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=payment.model_dump(mode="json"),
        headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(PaymentAPIError)
async def payment_error_handler(request: Request, error: PaymentAPIError):
    return _problem_response(request, error)


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, error: RequestValidationError):
    fields = [str(item["loc"][-1]) for item in error.errors()]
    return _problem_response(request, _validation_error(fields))


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, error: StarletteHTTPException):
    if request.url.path.startswith("/payments") and error.status_code in {404, 405}:
        code = "PAYMENT_NOT_FOUND" if error.status_code == 404 else "PAYMENT_METHOD_NOT_ALLOWED"
        detail = (
            "The requested payment does not exist."
            if error.status_code == 404
            else "The requested HTTP method is not supported."
        )
        return _problem_response(request, _as_error(error.status_code, code, detail))
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})


@app.post("/payments")
async def create_payment(request: Request):
    user_id = _authenticate(request)
    idempotency_key = _idempotency_key(request)
    body = await _json_body(request, missing_is_invalid=True)
    payment_create = _validate_create_body(body)
    try:
        result = repository.create_payment(
            user_id,
            idempotency_key,
            _fingerprint(payment_create),
            payment_create.payeePixKey,
            payment_create.amount,
            payment_create.description,
        )
    except IdempotencyConflictError:
        raise _as_error(
            409,
            "PAYMENT_IDEMPOTENCY_CONFLICT",
            "This Idempotency-Key was already used with a different request body.",
        ) from None
    return _payment_response(result.payment, 200 if result.replayed else 201)


@app.api_route("/payments/history", methods=["QUERY"])
async def query_payment_history(request: Request):
    user_id = _authenticate(request)
    body = await _json_body(request, missing_is_invalid=False)
    if not isinstance(body, dict):
        raise _validation_error(["body"], "The history query must be a JSON object.")
    if any(
        (key == "limit" and type(value) is not int)
        or (key == "cursor" and value is not None and type(value) is not str)
        for key, value in body.items()
        if key in {"limit", "cursor"}
    ):
        raise _validation_error(["limit", "cursor"])
    try:
        query = PaymentHistoryQuery.model_validate(body)
    except ValidationError as error:
        fields = [str(item["loc"][-1]) for item in error.errors()]
        raise _validation_error(fields) from None
    try:
        items, next_cursor = repository.list_history(
            user_id, query.limit, query.cursor
        )
    except (InvalidCursorError, ValueError):
        raise _validation_error(["cursor"], "The pagination cursor is invalid.") from None
    return JSONResponse(
        status_code=200,
        content={
            "items": [item.model_dump(mode="json") for item in items],
            "nextCursor": next_cursor,
        },
        headers={"Cache-Control": "no-store"},
    )


@app.get("/payments/{paymentId}")
async def get_payment(paymentId: str, request: Request):
    user_id = _authenticate(request)
    try:
        payment = repository.get_payment(user_id, paymentId)
    except PaymentNotFoundError:
        raise _as_error(
            404,
            "PAYMENT_NOT_FOUND",
            "The requested payment does not exist.",
        ) from None
    return _payment_response(payment, 200)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


# ponytail: one daemon consumer loop is enough for this in-process slice; move
# to a worker pool or broker when throughput and delivery guarantees require it.
def _consumer_loop(stop: threading.Event, executor: PedroBankFake) -> None:
    consumer = Consumer(repository, executor)
    try:
        interval = max(0.01, float(os.getenv("OPENPIX_CONSUMER_INTERVAL", "0.1")))
    except ValueError:
        interval = 0.1
    while not stop.is_set():
        try:
            consumer.run_once()
        except Exception:
            app_logger.error(
                json.dumps({"event": "consumer.failure"}, separators=(",", ":"))
            )
        stop.wait(interval)


def _consumer_enabled() -> bool:
    return os.getenv("OPENPIX_CONSUMER_ENABLED", "1").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global repository
    if (
        isinstance(repository, SqlitePayments)
        and os.fspath(repository.db_path) == os.fspath(_INITIAL_DB_PATH)
        and _configured_db_path() != _INITIAL_DB_PATH
    ):
        repository = _make_repository(_configured_db_path())

    stop = threading.Event()
    thread = None
    if _consumer_enabled():
        failure = os.getenv("OPENPIX_EXECUTOR_FAIL", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        executor = PedroBankFake(
            fail=failure,
            reason=os.getenv("OPENPIX_EXECUTOR_FAILURE_REASON", "executor failure"),
        )
        thread = threading.Thread(
            target=_consumer_loop,
            args=(stop, executor),
            name="payment-consumer",
            daemon=True,
        )
        thread.start()
    _app.state.consumer_stop = stop
    _app.state.consumer_thread = thread
    try:
        yield
    finally:
        stop.set()
        if thread is not None:
            thread.join(timeout=1)


app.router.lifespan_context = lifespan
