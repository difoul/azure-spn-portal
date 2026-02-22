"""Tests for KeyVaultService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.keyvault_service import KeyVaultService


@pytest.fixture
def kv():
    """Create a KeyVaultService with mocked client."""
    svc = KeyVaultService()
    svc._client = MagicMock()
    return svc


class TestMakeSecretName:
    def test_strips_hyphens(self):
        name = KeyVaultService._make_secret_name(
            "12345678-1234-1234-1234-123456789012",
            "abcdef01-2345-6789-abcd-ef0123456789",
        )
        assert name == "spn-12345678123412341234123456789012-abcdef0123456789abcdef0123456789"

    def test_no_hyphens(self):
        name = KeyVaultService._make_secret_name("abc", "def")
        assert name == "spn-abc-def"


class TestStoreSecret:
    async def test_stores_and_returns_name(self, kv):
        kv._client.set_secret = AsyncMock()
        name = await kv.store_secret("app-id-1", "key-id-1", "secret-val")
        assert name.startswith("spn-")
        kv._client.set_secret.assert_called_once()


class TestGetSecret:
    async def test_returns_value(self, kv):
        mock_secret = MagicMock()
        mock_secret.value = "my-secret"
        kv._client.get_secret = AsyncMock(return_value=mock_secret)
        result = await kv.get_secret("spn-abc-def")
        assert result == "my-secret"

    async def test_returns_none_on_not_found(self, kv):
        kv._client.get_secret = AsyncMock(side_effect=Exception("NotFound"))
        result = await kv.get_secret("missing")
        assert result is None


class TestDeleteSecret:
    async def test_deletes_secret(self, kv):
        kv._client.delete_secret = AsyncMock()
        await kv.delete_secret("spn-abc-def")
        kv._client.delete_secret.assert_called_once_with("spn-abc-def")

    async def test_ignores_not_found(self, kv):
        kv._client.delete_secret = AsyncMock(side_effect=Exception("NotFound"))
        await kv.delete_secret("missing")  # should not raise
