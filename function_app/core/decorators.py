"""Authentication and authorization decorators for Azure Functions v2 endpoints."""

import functools
import logging
from collections.abc import Callable, Coroutine
from typing import Any

import azure.functions as func

from core.auth import check_group_membership, extract_user_context, validate_token
from core.exceptions import ForbiddenError, NotOwnerError, UnauthorizedError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# @require_auth
# ---------------------------------------------------------------------------


def require_auth(
    fn: Callable[..., Coroutine[Any, Any, func.HttpResponse]],
) -> Callable[..., Coroutine[Any, Any, func.HttpResponse]]:
    """Decorator that validates the bearer token and checks group membership.

    On success the decorated function's ``req`` argument is augmented with a
    ``user_context`` attribute containing::

        {
            "oid": "<object-id>",
            "displayName": "<display name>",
            "email": "<preferred_username / UPN>",
        }

    Raises:
        UnauthorizedError: if the token is missing, malformed, or invalid.
        ForbiddenError: if the user is not in the allowed Entra ID group.
    """

    @functools.wraps(fn)
    async def wrapper(req: func.HttpRequest) -> func.HttpResponse:
        # --- Local development bypass ---
        # Set LOCAL_AUTH_BYPASS=<oid> in local.settings.json to skip JWT
        # validation and inject a fake user context. Never set this in production.
        import os

        bypass_oid = os.environ.get("LOCAL_AUTH_BYPASS", "")
        if bypass_oid:
            logger.warning("LOCAL_AUTH_BYPASS active — skipping auth for oid=%s", bypass_oid)
            req.user_context = {  # type: ignore[attr-defined]
                "oid": bypass_oid,
                "displayName": "Local Dev User",
                "email": "localdev@example.com",
            }
            return await fn(req)

        # --- Extract bearer token ---
        auth_header = req.headers.get("Authorization", "")
        if not auth_header:
            raise UnauthorizedError("Missing Authorization header.")

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise UnauthorizedError("Authorization header must use Bearer scheme.")

        token = parts[1]

        # --- Validate token ---
        claims = await validate_token(token)
        user_context = extract_user_context(claims)

        # --- Check group membership ---
        is_member = await check_group_membership(user_context["oid"])
        if not is_member:
            raise ForbiddenError(message="You are not a member of the authorized group.")

        # Attach user_context to the request object.
        # Azure Functions' HttpRequest does not prevent setting arbitrary
        # attributes, so monkey-patching is the simplest approach.
        req.user_context = user_context  # type: ignore[attr-defined]

        logger.info(
            "Authenticated user: oid=%s name=%s",
            user_context["oid"],
            user_context["displayName"],
        )

        return await fn(req)

    return wrapper


# ---------------------------------------------------------------------------
# @require_owner
# ---------------------------------------------------------------------------


def require_owner(
    fn: Callable[..., Coroutine[Any, Any, func.HttpResponse]],
) -> Callable[..., Coroutine[Any, Any, func.HttpResponse]]:
    """Decorator that verifies the authenticated user owns the target SPN.

    **Must** be applied *after* ``@require_auth`` so that ``req.user_context``
    is available.  The SPN is identified by the ``spn_id`` route parameter.

    Example stacking order::

        @bp.route(...)
        @handle_errors
        @require_auth
        @require_owner
        async def my_endpoint(req): ...

    Raises:
        NotOwnerError: if the user is not listed as an owner of the SPN.
    """

    @functools.wraps(fn)
    async def wrapper(req: func.HttpRequest) -> func.HttpResponse:
        user_context: dict = getattr(req, "user_context", None)  # type: ignore[assignment]
        if user_context is None:
            raise UnauthorizedError("Authentication context missing — apply @require_auth first.")

        spn_id = req.route_params.get("spn_id")
        if not spn_id:
            raise UnauthorizedError("Missing spn_id route parameter.")

        user_oid = user_context["oid"]

        # Import here to avoid circular import at module load time
        from services.graph_service import graph_service

        owners = await graph_service.list_owners(spn_id)
        owner_oids = {owner.get("id") for owner in owners}

        if user_oid not in owner_oids:
            logger.warning(
                "User %s is not an owner of SPN %s. Owners: %s",
                user_oid,
                spn_id,
                owner_oids,
            )
            raise NotOwnerError()

        return await fn(req)

    return wrapper
