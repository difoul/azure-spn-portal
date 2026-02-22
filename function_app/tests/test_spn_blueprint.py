"""Tests for SPN blueprint endpoints."""

import json

import pytest

from blueprints.spn_blueprint import create_spn, delete_spn, get_spn, list_spns, update_spn
from tests.conftest import SAMPLE_APP, SAMPLE_OWNERS, make_request


@pytest.fixture(autouse=True)
def _auth(bypass_auth):
    pass


# ------------------------------------------------------------------
# POST /v1/spns — create_spn
# ------------------------------------------------------------------


class TestCreateSpn:
    async def test_success(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.create_application.return_value = SAMPLE_APP
        mock_graph_service.create_service_principal.return_value = {"id": "sp-1"}
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request("POST", body={"displayName": "Test SPN"})
        resp = await create_spn(req)

        assert resp.status_code == 201
        body = json.loads(resp.get_body())
        assert body["displayName"] == "Test SPN"
        mock_graph_service.create_application.assert_called_once()
        mock_graph_service.create_service_principal.assert_called_once()
        mock_cosmos_service.upsert_spn_metadata.assert_called_once()
        mock_audit_service.log.assert_called_once()

    async def test_duplicate_name_returns_400(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.check_duplicate_name.return_value = True

        req = make_request("POST", body={"displayName": "Duplicate"})
        resp = await create_spn(req)

        assert resp.status_code == 400
        body = json.loads(resp.get_body())
        assert body["error"]["code"] == "DUPLICATE_SPN_NAME"

    async def test_missing_display_name_returns_400(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        req = make_request("POST", body={})
        resp = await create_spn(req)

        assert resp.status_code == 400
        body = json.loads(resp.get_body())
        assert body["error"]["code"] == "VALIDATION_ERROR"

    async def test_cleanup_on_sp_creation_failure(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.create_application.return_value = SAMPLE_APP
        mock_graph_service.create_service_principal.side_effect = Exception("SP failed")

        req = make_request("POST", body={"displayName": "Test SPN"})
        resp = await create_spn(req)

        assert resp.status_code == 500
        mock_graph_service.delete_application.assert_called_once_with("app-object-id-1")

    async def test_with_all_optional_fields(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.create_application.return_value = SAMPLE_APP
        mock_graph_service.create_service_principal.return_value = {"id": "sp-1"}
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "POST",
            body={
                "displayName": "Full SPN",
                "description": "A description",
                "redirectUris": ["https://example.com"],
                "tags": ["tag1", "tag2"],
            },
        )
        resp = await create_spn(req)

        assert resp.status_code == 201
        call_kwargs = mock_graph_service.create_application.call_args
        assert call_kwargs.kwargs["description"] == "A description"
        assert call_kwargs.kwargs["redirect_uris"] == ["https://example.com"]
        assert call_kwargs.kwargs["tags"] == ["tag1", "tag2"]


# ------------------------------------------------------------------
# GET /v1/spns — list_spns
# ------------------------------------------------------------------


class TestListSpns:
    async def test_returns_owned_apps(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owned_applications.return_value = [SAMPLE_APP]

        req = make_request("GET")
        resp = await list_spns(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["count"] == 1
        assert body["value"][0]["displayName"] == "Test SPN"

    async def test_empty_list(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owned_applications.return_value = []

        req = make_request("GET")
        resp = await list_spns(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["count"] == 0
        assert body["value"] == []

    async def test_cosmos_failure_degrades_gracefully(
        self, mock_graph_service, mock_cosmos_service, mock_audit_service
    ):
        mock_graph_service.list_owned_applications.return_value = [SAMPLE_APP]
        mock_cosmos_service.list_spn_metadata_by_ids.side_effect = Exception("DB error")

        req = make_request("GET")
        resp = await list_spns(req)

        assert resp.status_code == 200  # still works


# ------------------------------------------------------------------
# GET /v1/spns/{spn_id} — get_spn
# ------------------------------------------------------------------


class TestGetSpn:
    async def test_returns_spn_details(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.get_application.return_value = SAMPLE_APP
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request("GET", route_params={"spn_id": "app-object-id-1"})
        resp = await get_spn(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["id"] == "app-object-id-1"
        assert len(body["owners"]) == 1

    async def test_not_found(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        from core.exceptions import SpnNotFoundError

        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS
        mock_graph_service.get_application.side_effect = SpnNotFoundError("bad-id")

        req = make_request("GET", route_params={"spn_id": "bad-id"})
        resp = await get_spn(req)

        assert resp.status_code == 404


# ------------------------------------------------------------------
# PATCH /v1/spns/{spn_id} — update_spn
# ------------------------------------------------------------------


class TestUpdateSpn:
    async def test_update_display_name(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        updated_app = {**SAMPLE_APP, "displayName": "New Name"}
        mock_graph_service.update_application.return_value = updated_app
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "PATCH",
            route_params={"spn_id": "app-object-id-1"},
            body={"displayName": "New Name"},
        )
        resp = await update_spn(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["displayName"] == "New Name"
        mock_audit_service.log.assert_called_once()

    async def test_duplicate_name_on_update(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.check_duplicate_name.return_value = True
        mock_graph_service.get_application.return_value = SAMPLE_APP
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "PATCH",
            route_params={"spn_id": "app-object-id-1"},
            body={"displayName": "Other App"},
        )
        resp = await update_spn(req)

        assert resp.status_code == 400
        body = json.loads(resp.get_body())
        assert body["error"]["code"] == "DUPLICATE_SPN_NAME"

    async def test_same_name_not_flagged_as_duplicate(
        self, mock_graph_service, mock_cosmos_service, mock_audit_service
    ):
        mock_graph_service.check_duplicate_name.return_value = True
        mock_graph_service.get_application.return_value = SAMPLE_APP
        updated_app = {**SAMPLE_APP}
        mock_graph_service.update_application.return_value = updated_app
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "PATCH",
            route_params={"spn_id": "app-object-id-1"},
            body={"displayName": "Test SPN"},
        )
        resp = await update_spn(req)

        assert resp.status_code == 200

    async def test_empty_update_returns_400(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "PATCH",
            route_params={"spn_id": "app-object-id-1"},
            body={},
        )
        resp = await update_spn(req)

        assert resp.status_code == 400

    async def test_update_description_only(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        updated_app = {**SAMPLE_APP, "description": "Updated desc"}
        mock_graph_service.update_application.return_value = updated_app
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "PATCH",
            route_params={"spn_id": "app-object-id-1"},
            body={"description": "Updated desc"},
        )
        resp = await update_spn(req)

        assert resp.status_code == 200
        mock_graph_service.update_application.assert_called_once()


# ------------------------------------------------------------------
# DELETE /v1/spns/{spn_id} — delete_spn
# ------------------------------------------------------------------


class TestDeleteSpn:
    async def test_success(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request("DELETE", route_params={"spn_id": "app-object-id-1"})
        resp = await delete_spn(req)

        assert resp.status_code == 204
        mock_graph_service.delete_application.assert_called_once_with("app-object-id-1")
        mock_cosmos_service.delete_spn_metadata.assert_called_once_with("app-object-id-1")
        mock_audit_service.log.assert_called_once()

    async def test_cleans_up_keyvault_secrets(
        self,
        mock_graph_service,
        mock_cosmos_service,
        mock_audit_service,
        mock_keyvault_service,
    ):
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS
        mock_cosmos_service.get_spn_metadata.return_value = {
            "id": "app-object-id-1",
            "spnId": "app-object-id-1",
            "keyvaultMappings": {"key-1": "spn-abc-def", "key-2": "spn-xyz-123"},
        }

        req = make_request("DELETE", route_params={"spn_id": "app-object-id-1"})
        resp = await delete_spn(req)

        assert resp.status_code == 204
        assert mock_keyvault_service.delete_secret.call_count == 2

    async def test_keyvault_cleanup_failure_continues(
        self,
        mock_graph_service,
        mock_cosmos_service,
        mock_audit_service,
        mock_keyvault_service,
    ):
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS
        mock_cosmos_service.get_spn_metadata.return_value = {
            "id": "app-object-id-1",
            "spnId": "app-object-id-1",
            "keyvaultMappings": {"key-1": "spn-abc-def"},
        }
        mock_keyvault_service.delete_secret.side_effect = Exception("KV error")

        req = make_request("DELETE", route_params={"spn_id": "app-object-id-1"})
        resp = await delete_spn(req)

        # Should still complete the deletion
        assert resp.status_code == 204
        mock_graph_service.delete_application.assert_called_once()
