"""Tests for secret blueprint endpoints."""

import json

import pytest

from blueprints.secret_blueprint import create_secret, delete_secret, list_secrets
from tests.conftest import SAMPLE_APP, SAMPLE_CREDENTIAL, SAMPLE_OWNERS, make_request


@pytest.fixture(autouse=True)
def _auth(bypass_auth):
    pass


# ------------------------------------------------------------------
# POST /v1/spns/{spn_id}/secrets — create_secret
# ------------------------------------------------------------------


class TestCreateSecret:
    async def test_success(self, mock_graph_service, mock_cosmos_service, mock_keyvault_service, mock_audit_service):
        mock_graph_service.get_application.return_value = SAMPLE_APP
        mock_graph_service.add_password.return_value = SAMPLE_CREDENTIAL
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "POST",
            url="https://localhost/api/v1/spns/app-object-id-1/secrets",
            route_params={"spn_id": "app-object-id-1"},
            body={"displayName": "My Secret"},
        )
        resp = await create_secret(req)

        assert resp.status_code == 201
        body = json.loads(resp.get_body())
        assert body["keyId"] == "key-id-1"
        assert body["secretText"] == "super-secret-value"
        assert "keyVaultSecretName" in body
        mock_keyvault_service.store_secret.assert_called_once()
        mock_cosmos_service.add_keyvault_mapping.assert_called_once()
        mock_audit_service.log.assert_called_once()

    async def test_max_secrets_reached(
        self, mock_graph_service, mock_cosmos_service, mock_keyvault_service, mock_audit_service
    ):
        app_with_secrets = {
            **SAMPLE_APP,
            "passwordCredentials": [
                {"keyId": "k1", "displayName": "s1"},
                {"keyId": "k2", "displayName": "s2"},
            ],
        }
        mock_graph_service.get_application.return_value = app_with_secrets
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "POST",
            route_params={"spn_id": "app-object-id-1"},
            body={"displayName": "Third Secret"},
        )
        resp = await create_secret(req)

        assert resp.status_code == 400
        body = json.loads(resp.get_body())
        assert body["error"]["code"] == "MAX_SECRETS_REACHED"

    async def test_custom_expiry(
        self, mock_graph_service, mock_cosmos_service, mock_keyvault_service, mock_audit_service
    ):
        mock_graph_service.get_application.return_value = SAMPLE_APP
        mock_graph_service.add_password.return_value = SAMPLE_CREDENTIAL
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "POST",
            route_params={"spn_id": "app-object-id-1"},
            body={"displayName": "My Secret", "expiresInDays": 365},
        )
        resp = await create_secret(req)

        assert resp.status_code == 201
        mock_graph_service.add_password.assert_called_once_with("app-object-id-1", "My Secret", 365)

    async def test_missing_display_name(
        self, mock_graph_service, mock_cosmos_service, mock_keyvault_service, mock_audit_service
    ):
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "POST",
            route_params={"spn_id": "app-object-id-1"},
            body={},
        )
        resp = await create_secret(req)

        assert resp.status_code == 400

    async def test_one_secret_allows_second(
        self, mock_graph_service, mock_cosmos_service, mock_keyvault_service, mock_audit_service
    ):
        app_with_one = {
            **SAMPLE_APP,
            "passwordCredentials": [{"keyId": "k1", "displayName": "s1"}],
        }
        mock_graph_service.get_application.return_value = app_with_one
        mock_graph_service.add_password.return_value = SAMPLE_CREDENTIAL
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "POST",
            route_params={"spn_id": "app-object-id-1"},
            body={"displayName": "Second Secret"},
        )
        resp = await create_secret(req)

        assert resp.status_code == 201


# ------------------------------------------------------------------
# GET /v1/spns/{spn_id}/secrets — list_secrets
# ------------------------------------------------------------------


class TestListSecrets:
    async def test_returns_credentials(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        app_with_secrets = {
            **SAMPLE_APP,
            "passwordCredentials": [
                {
                    "keyId": "k1",
                    "displayName": "s1",
                    "startDateTime": "2025-01-01T00:00:00Z",
                    "endDateTime": "2025-04-01T00:00:00Z",
                },
            ],
        }
        mock_graph_service.get_application.return_value = app_with_secrets
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request("GET", route_params={"spn_id": "app-object-id-1"})
        resp = await list_secrets(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["count"] == 1
        assert body["value"][0]["keyId"] == "k1"
        # Should NOT contain secretText
        assert "secretText" not in body["value"][0]

    async def test_empty_credentials(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.get_application.return_value = SAMPLE_APP
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request("GET", route_params={"spn_id": "app-object-id-1"})
        resp = await list_secrets(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["count"] == 0


# ------------------------------------------------------------------
# DELETE /v1/spns/{spn_id}/secrets/{key_id} — delete_secret
# ------------------------------------------------------------------


class TestDeleteSecret:
    async def test_success(self, mock_graph_service, mock_cosmos_service, mock_keyvault_service, mock_audit_service):
        app_with_secret = {
            **SAMPLE_APP,
            "passwordCredentials": [{"keyId": "key-id-1", "displayName": "s1"}],
        }
        mock_graph_service.get_application.return_value = app_with_secret
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS
        mock_cosmos_service.remove_keyvault_mapping.return_value = "spn-abc-def"

        req = make_request(
            "DELETE",
            route_params={"spn_id": "app-object-id-1", "key_id": "key-id-1"},
        )
        resp = await delete_secret(req)

        assert resp.status_code == 204
        mock_graph_service.remove_password.assert_called_once_with("app-object-id-1", "key-id-1")
        mock_keyvault_service.delete_secret.assert_called_once_with("spn-abc-def")
        mock_audit_service.log.assert_called_once()

    async def test_key_not_found(
        self, mock_graph_service, mock_cosmos_service, mock_keyvault_service, mock_audit_service
    ):
        mock_graph_service.get_application.return_value = SAMPLE_APP
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "DELETE",
            route_params={"spn_id": "app-object-id-1", "key_id": "nonexistent"},
        )
        resp = await delete_secret(req)

        assert resp.status_code == 404
        body = json.loads(resp.get_body())
        assert body["error"]["code"] == "SECRET_NOT_FOUND"

    async def test_no_kv_mapping_still_succeeds(
        self, mock_graph_service, mock_cosmos_service, mock_keyvault_service, mock_audit_service
    ):
        app_with_secret = {
            **SAMPLE_APP,
            "passwordCredentials": [{"keyId": "key-id-1", "displayName": "s1"}],
        }
        mock_graph_service.get_application.return_value = app_with_secret
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS
        mock_cosmos_service.remove_keyvault_mapping.return_value = None

        req = make_request(
            "DELETE",
            route_params={"spn_id": "app-object-id-1", "key_id": "key-id-1"},
        )
        resp = await delete_secret(req)

        assert resp.status_code == 204
        mock_keyvault_service.delete_secret.assert_not_called()
