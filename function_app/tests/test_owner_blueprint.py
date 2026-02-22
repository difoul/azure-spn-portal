"""Tests for owner blueprint endpoints."""

import json

import pytest

from blueprints.owner_blueprint import add_owner, list_owners, remove_owner
from tests.conftest import SAMPLE_OWNERS, make_request


@pytest.fixture(autouse=True)
def _auth(bypass_auth):
    pass


SECOND_OWNER = {
    "id": "00000000-0000-0000-0000-000000000002",
    "displayName": "Second User",
    "mail": "second@example.com",
    "userPrincipalName": "second@example.com",
}


# ------------------------------------------------------------------
# GET /v1/spns/{spn_id}/owners — list_owners
# ------------------------------------------------------------------


class TestListOwners:
    async def test_returns_owners(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request("GET", route_params={"spn_id": "app-object-id-1"})
        resp = await list_owners(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["count"] == 1
        assert body["value"][0]["id"] == "00000000-0000-0000-0000-000000000001"
        assert body["value"][0]["displayName"] == "Test User"

    async def test_empty_owners(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        # First call: @require_owner checks ownership (user is owner); second call: endpoint returns []
        mock_graph_service.list_owners.side_effect = [SAMPLE_OWNERS, []]

        req = make_request("GET", route_params={"spn_id": "app-object-id-1"})
        resp = await list_owners(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["count"] == 0

    async def test_multiple_owners(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owners.return_value = [SAMPLE_OWNERS[0], SECOND_OWNER]

        req = make_request("GET", route_params={"spn_id": "app-object-id-1"})
        resp = await list_owners(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["count"] == 2


# ------------------------------------------------------------------
# POST /v1/spns/{spn_id}/owners — add_owner
# ------------------------------------------------------------------


class TestAddOwner:
    async def test_success(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS
        mock_graph_service.get_user.return_value = SECOND_OWNER

        req = make_request(
            "POST",
            route_params={"spn_id": "app-object-id-1"},
            body={"userId": "00000000-0000-0000-0000-000000000002"},
        )
        resp = await add_owner(req)

        assert resp.status_code == 201
        body = json.loads(resp.get_body())
        assert body["id"] == "00000000-0000-0000-0000-000000000002"
        assert body["displayName"] == "Second User"
        mock_graph_service.add_owner.assert_called_once_with("app-object-id-1", "00000000-0000-0000-0000-000000000002")
        mock_audit_service.log.assert_called_once()

    async def test_missing_user_id(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS

        req = make_request(
            "POST",
            route_params={"spn_id": "app-object-id-1"},
            body={},
        )
        resp = await add_owner(req)

        assert resp.status_code == 400

    async def test_user_not_found_in_graph(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        from core.exceptions import GraphApiError

        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS
        mock_graph_service.get_user.side_effect = GraphApiError("User not found")

        req = make_request(
            "POST",
            route_params={"spn_id": "app-object-id-1"},
            body={"userId": "nonexistent-user"},
        )
        resp = await add_owner(req)

        assert resp.status_code == 502


# ------------------------------------------------------------------
# DELETE /v1/spns/{spn_id}/owners/{owner_id} — remove_owner
# ------------------------------------------------------------------


class TestRemoveOwner:
    async def test_success(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owners.return_value = [SAMPLE_OWNERS[0], SECOND_OWNER]

        req = make_request(
            "DELETE",
            route_params={
                "spn_id": "app-object-id-1",
                "owner_id": "00000000-0000-0000-0000-000000000002",
            },
        )
        resp = await remove_owner(req)

        assert resp.status_code == 204
        mock_graph_service.remove_owner.assert_called_once_with(
            "app-object-id-1", "00000000-0000-0000-0000-000000000002"
        )
        mock_audit_service.log.assert_called_once()

    async def test_cannot_remove_last_owner(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owners.return_value = SAMPLE_OWNERS  # only 1 owner

        req = make_request(
            "DELETE",
            route_params={
                "spn_id": "app-object-id-1",
                "owner_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        resp = await remove_owner(req)

        assert resp.status_code == 400
        body = json.loads(resp.get_body())
        assert body["error"]["code"] == "CANNOT_REMOVE_LAST_OWNER"

    async def test_owner_not_in_list(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owners.return_value = [SAMPLE_OWNERS[0], SECOND_OWNER]

        req = make_request(
            "DELETE",
            route_params={
                "spn_id": "app-object-id-1",
                "owner_id": "nonexistent-owner-id",
            },
        )
        resp = await remove_owner(req)

        assert resp.status_code == 404
        body = json.loads(resp.get_body())
        assert body["error"]["code"] == "OWNER_NOT_FOUND"

    async def test_remove_self_when_multiple_owners(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        mock_graph_service.list_owners.return_value = [SAMPLE_OWNERS[0], SECOND_OWNER]

        req = make_request(
            "DELETE",
            route_params={
                "spn_id": "app-object-id-1",
                "owner_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        resp = await remove_owner(req)

        assert resp.status_code == 204

    async def test_empty_owners_prevents_removal(self, mock_graph_service, mock_cosmos_service, mock_audit_service):
        # First call: @require_owner (user is owner); second call: endpoint body sees empty list → 400
        mock_graph_service.list_owners.side_effect = [SAMPLE_OWNERS, []]

        req = make_request(
            "DELETE",
            route_params={
                "spn_id": "app-object-id-1",
                "owner_id": "some-id",
            },
        )
        resp = await remove_owner(req)

        assert resp.status_code == 400
