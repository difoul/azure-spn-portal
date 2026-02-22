import functools
import json
import logging
import traceback
from collections.abc import Callable, Coroutine
from typing import Any

import azure.functions as func

from core.exceptions import PortalError

logger = logging.getLogger(__name__)


def error_response(error: PortalError) -> func.HttpResponse:
    """Build a standardized error HTTP response from a PortalError."""
    body = {
        "error": {
            "code": error.code,
            "message": error.message,
        }
    }
    if error.target:
        body["error"]["target"] = error.target
    return func.HttpResponse(
        body=json.dumps(body),
        status_code=error.status_code,
        mimetype="application/json",
    )


def handle_errors(fn: Callable[..., Coroutine[Any, Any, func.HttpResponse]]):
    """Decorator that catches PortalError exceptions and returns standardized error responses."""

    @functools.wraps(fn)
    async def wrapper(req: func.HttpRequest) -> func.HttpResponse:
        try:
            return await fn(req)
        except PortalError as e:
            logger.warning("Portal error: %s - %s", e.code, e.message)
            return error_response(e)
        except Exception:
            logger.exception("Unhandled exception:\n%s", traceback.format_exc())
            return error_response(PortalError("INTERNAL_ERROR", "An unexpected error occurred.", 500))

    return wrapper
