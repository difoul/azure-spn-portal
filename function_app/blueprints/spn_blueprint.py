"""SPN (Service Principal) management endpoints."""

import logging

import azure.functions as func

from core.decorators import require_auth, require_owner
from core.error_handler import handle_errors
from core.request_helpers import json_response, parse_request_body
from models.spn import (
    CreateSpnRequest,
    SecretSummaryResponse,
    SpnListResponse,
    SpnResponse,
    UpdateSpnRequest,
)
from services.audit_service import CREATE_SPN, DELETE_SPN, UPDATE_SPN, audit_service
from services.cosmos_service import cosmos_service
from services.graph_service import graph_service
from services.keyvault_service import keyvault_service

logger = logging.getLogger(__name__)

spn_bp = func.Blueprint()


def _build_spn_response(app: dict, owners: list[dict] | None = None) -> SpnResponse:
    """Build an SpnResponse from a Graph API application object."""
    creds = [
        SecretSummaryResponse(
            keyId=c.get("keyId", ""),
            displayName=c.get("displayName", ""),
            startDateTime=c.get("startDateTime"),
            endDateTime=c.get("endDateTime"),
        )
        for c in app.get("passwordCredentials", [])
    ]
    return SpnResponse(
        id=app["id"],
        appId=app.get("appId", ""),
        displayName=app.get("displayName", ""),
        description=app.get("description"),
        createdDateTime=app.get("createdDateTime"),
        passwordCredentials=creds,
        owners=owners or [],
        tags=app.get("tags", []),
    )


# ------------------------------------------------------------------
# POST /v1/spns
# ------------------------------------------------------------------


@spn_bp.function_name("CreateSpn")
@spn_bp.route(route="v1/spns", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@handle_errors
@require_auth
async def create_spn(req: func.HttpRequest) -> func.HttpResponse:
    user_context: dict = req.user_context  # type: ignore[attr-defined]
    body = parse_request_body(req, CreateSpnRequest)

    # Check for duplicate name
    from core.exceptions import DuplicateSpnNameError

    if await graph_service.check_duplicate_name(body.display_name):
        raise DuplicateSpnNameError(body.display_name)

    # Create application
    app = await graph_service.create_application(
        display_name=body.display_name,
        description=body.description,
        redirect_uris=body.redirect_uris,
        tags=body.tags,
    )
    app_id = app["appId"]
    app_object_id = app["id"]

    # Create service principal (with cleanup on failure)
    try:
        await graph_service.create_service_principal(app_id)
    except Exception:
        logger.exception("Failed to create SP for app %s; cleaning up app", app_object_id)
        await graph_service.delete_application(app_object_id)
        raise

    # Add caller as owner
    await graph_service.add_owner(app_object_id, user_context["oid"])

    # Save portal metadata
    await cosmos_service.upsert_spn_metadata(
        app_object_id,
        {
            "displayName": body.display_name,
            "createdBy": user_context["oid"],
        },
    )

    # Audit
    await audit_service.log(
        app_object_id,
        CREATE_SPN,
        user_context,
        details={"displayName": body.display_name},
    )

    # Re-fetch to get full object with owner
    owners = await graph_service.list_owners(app_object_id)
    response = _build_spn_response(app, owners)
    return json_response(response, status_code=201)


# ------------------------------------------------------------------
# GET /v1/spns
# ------------------------------------------------------------------


@spn_bp.function_name("ListSpns")
@spn_bp.route(route="v1/spns", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@handle_errors
@require_auth
async def list_spns(req: func.HttpRequest) -> func.HttpResponse:
    user_context: dict = req.user_context  # type: ignore[attr-defined]

    apps = await graph_service.list_owned_applications(user_context["oid"])
    spn_ids = [a["id"] for a in apps]

    # Enrich with Cosmos metadata (best-effort)
    if spn_ids:
        try:
            await cosmos_service.list_spn_metadata_by_ids(spn_ids)
        except Exception:
            logger.warning("Failed to fetch Cosmos metadata for list endpoint")

    items = [_build_spn_response(a) for a in apps]
    response = SpnListResponse(value=items, count=len(items))
    return json_response(response)


# ------------------------------------------------------------------
# GET /v1/spns/{spn_id}
# ------------------------------------------------------------------


@spn_bp.function_name("GetSpn")
@spn_bp.route(route="v1/spns/{spn_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@handle_errors
@require_auth
@require_owner
async def get_spn(req: func.HttpRequest) -> func.HttpResponse:
    spn_id = req.route_params["spn_id"]

    app = await graph_service.get_application(spn_id)
    owners = await graph_service.list_owners(spn_id)
    response = _build_spn_response(app, owners)
    return json_response(response)


# ------------------------------------------------------------------
# PATCH /v1/spns/{spn_id}
# ------------------------------------------------------------------


@spn_bp.function_name("UpdateSpn")
@spn_bp.route(route="v1/spns/{spn_id}", methods=["PATCH"], auth_level=func.AuthLevel.ANONYMOUS)
@handle_errors
@require_auth
@require_owner
async def update_spn(req: func.HttpRequest) -> func.HttpResponse:
    spn_id = req.route_params["spn_id"]
    user_context: dict = req.user_context  # type: ignore[attr-defined]
    body = parse_request_body(req, UpdateSpnRequest)

    from core.exceptions import DuplicateSpnNameError

    # Check duplicate name if changing it
    if body.display_name is not None and await graph_service.check_duplicate_name(body.display_name):
        # Only raise if the duplicate is a different app
        current_app = await graph_service.get_application(spn_id)
        if current_app.get("displayName") != body.display_name:
            raise DuplicateSpnNameError(body.display_name)

    # Build update payload
    updates: dict = {}
    if body.display_name is not None:
        updates["displayName"] = body.display_name
    if body.description is not None:
        updates["description"] = body.description
    if body.redirect_uris is not None:
        updates["web"] = {"redirectUris": body.redirect_uris}
    if body.tags is not None:
        updates["tags"] = body.tags

    if not updates:
        from core.exceptions import ValidationError

        raise ValidationError("No fields to update.")

    updated_app = await graph_service.update_application(spn_id, updates)

    # Update Cosmos metadata
    cosmos_updates = {}
    if body.display_name is not None:
        cosmos_updates["displayName"] = body.display_name
    if cosmos_updates:
        await cosmos_service.upsert_spn_metadata(spn_id, cosmos_updates)

    # Audit
    await audit_service.log(spn_id, UPDATE_SPN, user_context, details=updates)

    owners = await graph_service.list_owners(spn_id)
    response = _build_spn_response(updated_app, owners)
    return json_response(response)


# ------------------------------------------------------------------
# DELETE /v1/spns/{spn_id}
# ------------------------------------------------------------------


@spn_bp.function_name("DeleteSpn")
@spn_bp.route(route="v1/spns/{spn_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
@handle_errors
@require_auth
@require_owner
async def delete_spn(req: func.HttpRequest) -> func.HttpResponse:
    spn_id = req.route_params["spn_id"]
    user_context: dict = req.user_context  # type: ignore[attr-defined]

    # Cleanup KeyVault secrets for this SPN
    metadata = await cosmos_service.get_spn_metadata(spn_id)
    if metadata:
        mappings = metadata.get("keyvaultMappings", {})
        for kv_secret_name in mappings.values():
            try:
                await keyvault_service.delete_secret(kv_secret_name)
            except Exception:
                logger.warning("Failed to delete KV secret %s during SPN cleanup", kv_secret_name)

    # Delete the application (also deletes associated SP)
    await graph_service.delete_application(spn_id)

    # Delete Cosmos metadata
    await cosmos_service.delete_spn_metadata(spn_id)

    # Audit
    await audit_service.log(spn_id, DELETE_SPN, user_context)

    return func.HttpResponse(status_code=204)
