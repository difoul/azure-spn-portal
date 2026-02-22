"""Owner management endpoints."""

import logging

import azure.functions as func

from core.decorators import require_auth, require_owner
from core.error_handler import handle_errors
from core.exceptions import CannotRemoveLastOwnerError, OwnerNotFoundError
from core.request_helpers import json_response, parse_request_body
from models.owner import AddOwnerRequest, OwnerListResponse, OwnerResponse
from services.audit_service import ADD_OWNER, REMOVE_OWNER, audit_service
from services.graph_service import graph_service

logger = logging.getLogger(__name__)

owner_bp = func.Blueprint()


# ------------------------------------------------------------------
# GET /v1/spns/{spn_id}/owners
# ------------------------------------------------------------------


@owner_bp.function_name("ListOwners")
@owner_bp.route(
    route="v1/spns/{spn_id}/owners",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@handle_errors
@require_auth
@require_owner
async def list_owners(req: func.HttpRequest) -> func.HttpResponse:
    spn_id = req.route_params["spn_id"]

    owners = await graph_service.list_owners(spn_id)
    items = [
        OwnerResponse(
            id=o["id"],
            displayName=o.get("displayName"),
            mail=o.get("mail"),
            userPrincipalName=o.get("userPrincipalName"),
        )
        for o in owners
    ]

    response = OwnerListResponse(value=items, count=len(items))
    return json_response(response)


# ------------------------------------------------------------------
# POST /v1/spns/{spn_id}/owners
# ------------------------------------------------------------------


@owner_bp.function_name("AddOwner")
@owner_bp.route(
    route="v1/spns/{spn_id}/owners",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@handle_errors
@require_auth
@require_owner
async def add_owner(req: func.HttpRequest) -> func.HttpResponse:
    spn_id = req.route_params["spn_id"]
    user_context: dict = req.user_context  # type: ignore[attr-defined]
    body = parse_request_body(req, AddOwnerRequest)

    # Validate user exists
    user = await graph_service.get_user(body.user_id)

    # Add owner
    await graph_service.add_owner(spn_id, body.user_id)

    # Audit
    await audit_service.log(
        spn_id,
        ADD_OWNER,
        user_context,
        details={"userId": body.user_id, "displayName": user.get("displayName", "")},
    )

    owner_response = OwnerResponse(
        id=user["id"],
        displayName=user.get("displayName"),
        mail=user.get("mail"),
        userPrincipalName=user.get("userPrincipalName"),
    )
    return json_response(owner_response, status_code=201)


# ------------------------------------------------------------------
# DELETE /v1/spns/{spn_id}/owners/{owner_id}
# ------------------------------------------------------------------


@owner_bp.function_name("RemoveOwner")
@owner_bp.route(
    route="v1/spns/{spn_id}/owners/{owner_id}",
    methods=["DELETE"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@handle_errors
@require_auth
@require_owner
async def remove_owner(req: func.HttpRequest) -> func.HttpResponse:
    spn_id = req.route_params["spn_id"]
    owner_id = req.route_params["owner_id"]
    user_context: dict = req.user_context  # type: ignore[attr-defined]

    # List current owners
    owners = await graph_service.list_owners(spn_id)

    # Check last-owner protection
    if len(owners) <= 1:
        raise CannotRemoveLastOwnerError()

    # Verify owner_id is in the list
    owner_oids = {o.get("id") for o in owners}
    if owner_id not in owner_oids:
        raise OwnerNotFoundError(owner_id)

    # Remove owner
    await graph_service.remove_owner(spn_id, owner_id)

    # Audit
    await audit_service.log(spn_id, REMOVE_OWNER, user_context, details={"ownerId": owner_id})

    return func.HttpResponse(status_code=204)
