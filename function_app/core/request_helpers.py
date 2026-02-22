"""Shared request/response helpers for all blueprints."""

import json
import logging
from typing import TypeVar

import azure.functions as func
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from core.exceptions import ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def parse_request_body(req: func.HttpRequest, model_class: type[T]) -> T:
    """Parse the request body as JSON and validate against a Pydantic model.

    Raises ``ValidationError`` if the body is missing, not valid JSON, or
    fails Pydantic validation.
    """
    try:
        body = req.get_json()
    except ValueError as exc:
        raise ValidationError("Request body must be valid JSON.") from exc

    try:
        return model_class.model_validate(body)
    except PydanticValidationError as exc:
        errors = exc.errors()
        if errors:
            first = errors[0]
            loc = ".".join(str(p) for p in first.get("loc", []))
            msg = first.get("msg", "Validation error")
            raise ValidationError(f"{loc}: {msg}", target=loc) from exc
        raise ValidationError("Request validation failed.") from exc


def json_response(
    data: BaseModel | dict | list,
    status_code: int = 200,
) -> func.HttpResponse:
    """Serialize *data* to a JSON ``HttpResponse``.

    Accepts a Pydantic model (serialized with aliases) or a plain dict/list.
    """
    body = data.model_dump(mode="json", by_alias=True) if isinstance(data, BaseModel) else data

    return func.HttpResponse(
        body=json.dumps(body),
        status_code=status_code,
        mimetype="application/json",
    )
