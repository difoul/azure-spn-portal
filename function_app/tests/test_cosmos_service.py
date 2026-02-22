"""Tests for CosmosService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.cosmos_service import CosmosService


@pytest.fixture
def cosmos():
    """Create a CosmosService with mocked internals."""
    svc = CosmosService()
    svc._client = MagicMock()  # pretend initialized
    svc._spn_container = MagicMock()
    svc._audit_container = MagicMock()
    return svc


class TestUpsertSpnMetadata:
    async def test_upserts_with_id_and_partition_key(self, cosmos):
        cosmos._spn_container.upsert_item = AsyncMock(return_value={"id": "spn-1"})
        await cosmos.upsert_spn_metadata("spn-1", {"displayName": "Test"})
        cosmos._spn_container.upsert_item.assert_called_once()
        call_arg = cosmos._spn_container.upsert_item.call_args[0][0]
        assert call_arg["id"] == "spn-1"
        assert call_arg["spnId"] == "spn-1"
        assert call_arg["displayName"] == "Test"


class TestGetSpnMetadata:
    async def test_returns_item(self, cosmos):
        cosmos._spn_container.read_item = AsyncMock(return_value={"id": "spn-1", "spnId": "spn-1"})
        result = await cosmos.get_spn_metadata("spn-1")
        assert result is not None
        assert result["id"] == "spn-1"

    async def test_returns_none_on_not_found(self, cosmos):
        cosmos._spn_container.read_item = AsyncMock(side_effect=Exception("NotFound"))
        result = await cosmos.get_spn_metadata("missing")
        assert result is None


class TestDeleteSpnMetadata:
    async def test_deletes_item(self, cosmos):
        cosmos._spn_container.delete_item = AsyncMock()
        await cosmos.delete_spn_metadata("spn-1")
        cosmos._spn_container.delete_item.assert_called_once_with(item="spn-1", partition_key="spn-1")

    async def test_ignores_not_found(self, cosmos):
        cosmos._spn_container.delete_item = AsyncMock(side_effect=Exception("NotFound"))
        await cosmos.delete_spn_metadata("missing")  # should not raise


class TestListSpnMetadataByIds:
    async def test_empty_list_returns_empty(self, cosmos):
        result = await cosmos.list_spn_metadata_by_ids([])
        assert result == {}

    async def test_returns_dict_keyed_by_spn_id(self, cosmos):
        items = [
            {"spnId": "spn-1", "displayName": "A"},
            {"spnId": "spn-2", "displayName": "B"},
        ]

        async def mock_query(*args, **kwargs):
            for item in items:
                yield item

        cosmos._spn_container.query_items = MagicMock(return_value=mock_query())
        result = await cosmos.list_spn_metadata_by_ids(["spn-1", "spn-2"])
        assert "spn-1" in result
        assert "spn-2" in result


class TestKeyvaultMappings:
    async def test_add_mapping_creates_if_no_metadata(self, cosmos):
        cosmos._spn_container.read_item = AsyncMock(side_effect=Exception("NotFound"))
        cosmos._spn_container.upsert_item = AsyncMock()

        await cosmos.add_keyvault_mapping("spn-1", "key-1", "spn-abc-def")
        call_arg = cosmos._spn_container.upsert_item.call_args[0][0]
        assert call_arg["keyvaultMappings"]["key-1"] == "spn-abc-def"

    async def test_remove_mapping_returns_name(self, cosmos):
        metadata = {
            "id": "spn-1",
            "spnId": "spn-1",
            "keyvaultMappings": {"key-1": "spn-abc-def"},
        }
        cosmos._spn_container.read_item = AsyncMock(return_value=metadata)
        cosmos._spn_container.upsert_item = AsyncMock()

        name = await cosmos.remove_keyvault_mapping("spn-1", "key-1")
        assert name == "spn-abc-def"

    async def test_remove_mapping_returns_none_for_missing(self, cosmos):
        metadata = {"id": "spn-1", "spnId": "spn-1", "keyvaultMappings": {}}
        cosmos._spn_container.read_item = AsyncMock(return_value=metadata)

        name = await cosmos.remove_keyvault_mapping("spn-1", "nonexistent")
        assert name is None
