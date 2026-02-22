"""Secret (password credential) management endpoints."""

import logging

import azure.functions as func

from core.decorators import require_auth, require_owner
from core.error_handler import handle_errors
from core.exceptions import MaxSecretsReachedError, SecretNotFoundError
from core.request_helpers import json_response, parse_request_body
from models.secret import CreateSecretRequest, SecretCreatedResponse, SecretListResponse
from models.spn import SecretSummaryResponse
from services.audit_service import ADD_SECRET, DELETE_SECRET, audit_service
from services.cosmos_service import cosmos_service
from services.graph_service import graph_service
from services.keyvault_service import keyvault_service

logger = logging.getLogger(__name__)

secret_bp = func.Blueprint()

_MAX_SECRETS = 2


# ------------------------------------------------------------------
# POST /v1/spns/{spn_id}/secrets
# ------------------------------------------------------------------


@secret_bp.function_name("CreateSecret")
@secret_bp.route(
    route="v1/spns/{spn_id}/secrets",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@handle_errors
@require_auth
@require_owner
async def create_secret(req: func.HttpRequest) -> func.HttpResponse:
    spn_id = req.route_params["spn_id"]
    user_context: dict = req.user_context  # type: ignore[attr-defined]
    body = parse_request_body(req, CreateSecretRequest)

    # Check max secrets
    app = await graph_service.get_application(spn_id)
    existing_creds = app.get("passwordCredentials", [])
    if len(existing_creds) >= _MAX_SECRETS:
        raise MaxSecretsReachedError()

    # Add password
    credential = await graph_service.add_password(spn_id, body.display_name, body.expires_in_days)

    key_id = credential["keyId"]
    secret_text = credential["secretText"]
    app_id = app.get("appId", "")

    # Store in Key Vault
    kv_secret_name = await keyvault_service.store_secret(app_id, key_id, secret_text)

    # Save Cosmos mapping
    await cosmos_service.add_keyvault_mapping(spn_id, key_id, kv_secret_name)

    # Audit
    await audit_service.log(
        spn_id,
        ADD_SECRET,
        user_context,
        details={"keyId": key_id, "displayName": body.display_name},
    )

    response = SecretCreatedResponse(
        keyId=key_id,
        displayName=credential.get("displayName", body.display_name),
        secretText=secret_text,
        startDateTime=credential.get("startDateTime"),
        endDateTime=credential.get("endDateTime"),
        keyVaultSecretName=kv_secret_name,
    )
    return json_response(response, status_code=201)


# ------------------------------------------------------------------
# GET /v1/spns/{spn_id}/secrets
# ------------------------------------------------------------------


@secret_bp.function_name("ListSecrets")
@secret_bp.route(
    route="v1/spns/{spn_id}/secrets",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@handle_errors
@require_auth
@require_owner
async def list_secrets(req: func.HttpRequest) -> func.HttpResponse:
    spn_id = req.route_params["spn_id"]

    app = await graph_service.get_application(spn_id)
    creds = app.get("passwordCredentials", [])

    items = [
        SecretSummaryResponse(
            keyId=c.get("keyId", ""),
            displayName=c.get("displayName", ""),
            startDateTime=c.get("startDateTime"),
            endDateTime=c.get("endDateTime"),
        ).model_dump(mode="json", by_alias=True)
        for c in creds
    ]

    response = SecretListResponse(value=items, count=len(items))
    return json_response(response)


# ------------------------------------------------------------------
# DELETE /v1/spns/{spn_id}/secrets/{key_id}
# ------------------------------------------------------------------


@secret_bp.function_name("DeleteSecret")
@secret_bp.route(
    route="v1/spns/{spn_id}/secrets/{key_id}",
    methods=["DELETE"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@handle_errors
@require_auth
@require_owner
async def delete_secret(req: func.HttpRequest) -> func.HttpResponse:
    spn_id = req.route_params["spn_id"]
    key_id = req.route_params["key_id"]
    user_context: dict = req.user_context  # type: ignore[attr-defined]

    # Verify key_id exists
    app = await graph_service.get_application(spn_id)
    existing_creds = app.get("passwordCredentials", [])
    if not any(c.get("keyId") == key_id for c in existing_creds):
        raise SecretNotFoundError(key_id)

    # Remove password from Graph
    await graph_service.remove_password(spn_id, key_id)

    # Delete from Key Vault
    kv_secret_name = await cosmos_service.remove_keyvault_mapping(spn_id, key_id)
    if kv_secret_name:
        await keyvault_service.delete_secret(kv_secret_name)

    # Audit
    await audit_service.log(spn_id, DELETE_SECRET, user_context, details={"keyId": key_id})

    return func.HttpResponse(status_code=204)
