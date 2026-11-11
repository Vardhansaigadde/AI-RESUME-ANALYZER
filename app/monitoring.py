"""Error monitoring.

Two parts, both free:

- Browser errors: the frontend reports crashes to POST /api/client-error,
  which logs them here, so they show up in Render's logs next to API errors.
- Sentry (optional): when SENTRY_DSN is set, unhandled API errors and
  error-level logs (including the browser reports above) become Sentry issues
  with alerts. Without it, nothing is sent anywhere.

Privacy: resumes are personal data (India's DPDP Act), so Sentry gets no
request bodies, cookies, headers, query strings or IP addresses, only the
error, its stack trace and the path.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

logger = logging.getLogger("fitlens.client")


def _scrub(event: dict[str, Any], _hint: dict[str, Any]) -> dict[str, Any]:
    request = event.get("request")
    if isinstance(request, dict):
        event["request"] = {k: request[k] for k in ("method", "url") if k in request}
        if "url" in event["request"]:
            event["request"]["url"] = str(event["request"]["url"]).split("?", 1)[0]
    event.pop("user", None)
    return event


def init_sentry() -> bool:
    """Start Sentry when SENTRY_DSN is set. Returns whether it was started."""
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
    except ImportError:  # pragma: no cover - listed in requirements.txt
        logger.warning("SENTRY_DSN is set but sentry-sdk is not installed")
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        send_default_pii=False,
        max_request_body_size="never",
        include_local_variables=False,  # locals could hold resume text
        traces_sample_rate=0.0,
        before_send=_scrub,
    )
    return True


class ClientError(BaseModel):
    kind: Literal["render", "error", "rejection"] = "error"
    message: str = Field(max_length=500)
    stack: str = Field(default="", max_length=4000)
    path: str = Field(default="", max_length=200, description="Page path only, no query string")


router = APIRouter(prefix="/api", tags=["monitoring"])


@router.post("/client-error", status_code=204)
def client_error(report: ClientError) -> Response:
    """Log a crash from the frontend. Rate-limited like every other POST under /api."""
    path = report.path.split("?", 1)[0]
    logger.error("Frontend %s on %s: %s\n%s", report.kind, path or "?", report.message, report.stack)
    return Response(status_code=204)
