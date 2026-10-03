"""FastAPI application entry point.

Scaffolds the primary FastAPI app instance, middleware configuration,
and route registration for resume parsing, analysis, and ML scoring endpoints.
"""

from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.routers.analyze import router as analyze_router
from app.services.pipeline import MAX_FILE_SIZE

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

docs_enabled = os.getenv("ENABLE_DOCS", "false").lower() in ("true", "1", "yes")

# Whole request body cap: the 5MB resume plus job description text and
# multipart overhead. Larger bodies are rejected before they are buffered.
MAX_REQUEST_BODY_BYTES = MAX_FILE_SIZE + 1024 * 1024


def _warm_up_models() -> None:
    """Load model artifacts and compile skill patterns once at startup.

    Without this, the first user request after a (Render free tier) cold start
    also pays for unpickling every model.
    """
    try:
        from app.ml.features import get_tfidf_vectorizer
        from app.services.matcher import get_feature_scaler, get_match_model
        from app.services.role_predictor import (
            _load_classifier,
            _load_role_profiles,
            _load_vectorizer,
        )
        from app.services.skill_extractor import _load_skill_patterns
        from app.services.suggestions import load_skill_rank_map

        get_tfidf_vectorizer()
        get_match_model()
        get_feature_scaler()
        _load_classifier()
        _load_vectorizer()
        _load_role_profiles()
        _load_skill_patterns()
        load_skill_rank_map()
        logger.info("Model artifacts warmed up.")
    except Exception:  # Never block startup; endpoints report missing models with 503
        logger.exception("Model warm-up failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    _warm_up_models()
    yield


app = FastAPI(
    title="Resume Analyzer API",
    description="API for parsing resumes and analyzing job-resume fit with machine learning.",
    version="0.2.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
    lifespan=lifespan,
)


class _BodyTooLarge(Exception):
    pass


class BodySizeLimitMiddleware:
    """Reject request bodies larger than max_bytes with HTTP 413.

    Checks Content-Length up front and also counts streamed bytes, so chunked
    uploads without a Content-Length are capped too.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                too_large = int(content_length) > self.max_bytes
            except ValueError:
                too_large = False
            if too_large:
                await self._reject(scope, receive, send)
                return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _BodyTooLarge()
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _BodyTooLarge:
            if not response_started:
                await self._reject(scope, receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content={"detail": "Request is too large. Resume files must be 5MB or smaller."},
        )
        await response(scope, receive, send)


# CORS: the production frontend (resumefitlens.vercel.app) calls this API
# directly via VITE_API_BASE_URL, so its origin must be listed in CORS_ORIGINS.
# No cookies or auth headers are used, so credentials are never allowed.
default_dev_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env.strip():
    allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
else:
    allowed_origins = default_dev_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_REQUEST_BODY_BYTES)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions and return safe JSON response without leaking internals."""
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    logger.exception("Unhandled server exception at %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again."},
    )


app.include_router(analyze_router)


@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    """Health check and welcome endpoint."""
    return {"message": "Welcome to Resume Analyzer API", "status": "active"}
