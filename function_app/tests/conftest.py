import json
from unittest.mock import AsyncMock, MagicMock, patch

import azure.functions as func
import pytest


@pytest.fixture
def mock_user_context():
    """A mock authenticated user context."""
    return {
        "oid": "00000000-0000-0000-0000-000000000001",
        "displayName": "Test User",
        "email": "testuser@example.com",
    }


@pytest.fixture
def mock_settings(monkeypatch):
    """Set required environment variables for tests."""
    monkeypatch.setenv("TENANT_ID", "00000000-0000-0000-0000-000000000000")
    monkeypatch.setenv("CLIENT_ID", "11111111-1111-1111-1111-111111111111")
    monkeypatch.setenv("CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("ALLOWED_GROUP_ID", "22222222-2222-2222-2222-222222222222")
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://localhost:8081")
    monkeypatch.setenv("KEYVAULT_URI", "https://test-kv.vault.azure.net")


def make_request(
    method: str = "GET",
    url: str = "https://localhost/api/v1/spns",
    body: dict | None = None,
    route_params: dict | None = None,
    headers: dict | None = None,
) -> func.HttpRequest:
    """Build a mock HttpRequest for blueprint tests."""
    req = func.HttpRequest(
        method=method,
        url=url,
        headers=headers or {"Authorization": "Bearer fake-token"},
        route_params=route_params or {},
        body=json.dumps(body).encode() if body else b"",
    )
    return req


@pytest.fixture
def bypass_auth():
    """Patch auth decorators to bypass token validation and group checks."""
    mock_claims = {
        "oid": "00000000-0000-0000-0000-000000000001",
        "name": "Test User",
        "preferred_username": "testuser@example.com",
    }
    with (
        patch("core.decorators.validate_token", new_callable=AsyncMock, return_value=mock_claims),
        patch("core.decorators.check_group_membership", new_callable=AsyncMock, return_value=True),
    ):
        yield mock_claims


def _make_graph_mock() -> MagicMock:
    mock = MagicMock()
    mock.check_duplicate_name = AsyncMock(return_value=False)
    mock.create_application = AsyncMock()
    mock.create_service_principal = AsyncMock()
    mock.get_application = AsyncMock()
    mock.list_owned_applications = AsyncMock(return_value=[])
    mock.update_application = AsyncMock()
    mock.delete_application = AsyncMock()
    mock.add_password = AsyncMock()
    mock.remove_password = AsyncMock()
    mock.list_owners = AsyncMock(return_value=[])
    mock.add_owner = AsyncMock()
    mock.remove_owner = AsyncMock()
    mock.get_user = AsyncMock()
    return mock


@pytest.fixture
def mock_graph_service():
    """Mock the graph_service singleton in all locations it is imported."""
    mock = _make_graph_mock()
    with (
        patch("services.graph_service.graph_service", mock),
        patch("blueprints.spn_blueprint.graph_service", mock),
        patch("blueprints.secret_blueprint.graph_service", mock),
        patch("blueprints.owner_blueprint.graph_service", mock),
    ):
        yield mock


@pytest.fixture
def mock_cosmos_service():
    """Mock the cosmos_service singleton in all locations it is imported."""
    mock = MagicMock()
    mock.upsert_spn_metadata = AsyncMock()
    mock.get_spn_metadata = AsyncMock(return_value=None)
    mock.delete_spn_metadata = AsyncMock()
    mock.list_spn_metadata_by_ids = AsyncMock(return_value={})
    mock.create_audit_event = AsyncMock()
    mock.list_audit_events = AsyncMock(return_value=[])
    mock.add_keyvault_mapping = AsyncMock()
    mock.remove_keyvault_mapping = AsyncMock(return_value=None)
    with (
        patch("services.cosmos_service.cosmos_service", mock),
        patch("blueprints.spn_blueprint.cosmos_service", mock),
        patch("blueprints.secret_blueprint.cosmos_service", mock),
    ):
        yield mock


@pytest.fixture
def mock_keyvault_service():
    """Mock the keyvault_service singleton in all locations it is imported."""
    mock = MagicMock()
    mock.store_secret = AsyncMock(return_value="spn-abc-def")
    mock.get_secret = AsyncMock(return_value="secret-value")
    mock.delete_secret = AsyncMock()
    with (
        patch("services.keyvault_service.keyvault_service", mock),
        patch("blueprints.spn_blueprint.keyvault_service", mock),
        patch("blueprints.secret_blueprint.keyvault_service", mock),
    ):
        yield mock


@pytest.fixture
def mock_audit_service():
    """Mock the audit_service singleton in all locations it is imported."""
    mock = MagicMock()
    mock.log = AsyncMock()
    mock.get_events = AsyncMock(return_value=[])
    with (
        patch("services.audit_service.audit_service", mock),
        patch("blueprints.spn_blueprint.audit_service", mock),
        patch("blueprints.secret_blueprint.audit_service", mock),
        patch("blueprints.owner_blueprint.audit_service", mock),
    ):
        yield mock


SAMPLE_APP = {
    "id": "app-object-id-1",
    "appId": "app-client-id-1",
    "displayName": "Test SPN",
    "description": "A test service principal",
    "createdDateTime": "2025-01-01T00:00:00Z",
    "passwordCredentials": [],
    "tags": ["test"],
}

SAMPLE_OWNERS = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "displayName": "Test User",
        "mail": "testuser@example.com",
        "userPrincipalName": "testuser@example.com",
    }
]

SAMPLE_CREDENTIAL = {
    "keyId": "key-id-1",
    "displayName": "My Secret",
    "secretText": "super-secret-value",
    "startDateTime": "2025-01-01T00:00:00Z",
    "endDateTime": "2025-04-01T00:00:00Z",
}
