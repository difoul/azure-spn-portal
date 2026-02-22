"""Cosmos DB service for portal metadata and audit events."""

import logging
from typing import Any

from azure.cosmos.aio import ContainerProxy, CosmosClient
from azure.identity.aio import DefaultAzureCredential

from core.config import settings

logger = logging.getLogger(__name__)

_SPN_METADATA_CONTAINER = "spn-metadata"
_AUDIT_EVENTS_CONTAINER = "audit-events"


class CosmosService:
    """Async Cosmos DB client with lazy initialization."""

    def __init__(self) -> None:
        self._client: CosmosClient | None = None
        self._credential: DefaultAzureCredential | None = None
        self._spn_container: ContainerProxy | None = None
        self._audit_container: ContainerProxy | None = None

    async def _ensure_initialized(self) -> None:
        if self._client is not None:
            return

        self._credential = DefaultAzureCredential()
        self._client = CosmosClient(
            url=settings.COSMOS_ENDPOINT,
            credential=self._credential,
        )
        database = self._client.get_database_client(settings.COSMOS_DATABASE)
        self._spn_container = database.get_container_client(_SPN_METADATA_CONTAINER)
        self._audit_container = database.get_container_client(_AUDIT_EVENTS_CONTAINER)

    # ------------------------------------------------------------------
    # SPN metadata (partition key: /spnId)
    # ------------------------------------------------------------------

    async def _spn(self) -> ContainerProxy:
        await self._ensure_initialized()
        assert self._spn_container is not None
        return self._spn_container

    async def _audit(self) -> ContainerProxy:
        await self._ensure_initialized()
        assert self._audit_container is not None
        return self._audit_container

    async def upsert_spn_metadata(self, spn_id: str, metadata: dict) -> dict:
        """Create or update portal metadata for an SPN."""
        item = {**metadata, "id": spn_id, "spnId": spn_id}
        return await (await self._spn()).upsert_item(item)

    async def get_spn_metadata(self, spn_id: str) -> dict | None:
        """Get metadata for an SPN. Returns None if not found."""
        try:
            return await (await self._spn()).read_item(item=spn_id, partition_key=spn_id)
        except Exception:
            logger.debug("SPN metadata not found for %s", spn_id)
            return None

    async def delete_spn_metadata(self, spn_id: str) -> None:
        """Delete metadata for an SPN."""
        try:
            await (await self._spn()).delete_item(item=spn_id, partition_key=spn_id)
        except Exception:
            logger.debug("SPN metadata not found for deletion: %s", spn_id)

    async def list_spn_metadata_by_ids(self, spn_ids: list[str]) -> dict[str, dict]:
        """Batch fetch metadata for multiple SPNs. Returns a dict keyed by spnId."""
        if not spn_ids:
            return {}

        placeholders = ", ".join(f"@id{i}" for i in range(len(spn_ids)))
        params: list[dict[str, Any]] = [{"name": f"@id{i}", "value": sid} for i, sid in enumerate(spn_ids)]
        query = f"SELECT * FROM c WHERE c.spnId IN ({placeholders})"

        results: dict[str, dict] = {}
        async for item in (await self._spn()).query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=True,
        ):
            results[item["spnId"]] = item
        return results

    # ------------------------------------------------------------------
    # Audit events (partition key: /spnId)
    # ------------------------------------------------------------------

    async def create_audit_event(self, event: dict) -> dict:
        """Write an audit record."""
        return await (await self._audit()).create_item(event)

    async def list_audit_events(self, spn_id: str, limit: int = 50) -> list[dict]:
        """List recent audit events for an SPN, newest first."""
        query = "SELECT * FROM c WHERE c.spnId = @spnId ORDER BY c.timestamp DESC OFFSET 0 LIMIT @limit"
        params: list[dict[str, Any]] = [
            {"name": "@spnId", "value": spn_id},
            {"name": "@limit", "value": limit},
        ]
        results: list[dict] = []
        async for item in (await self._audit()).query_items(
            query=query,
            parameters=params,
            partition_key=spn_id,
        ):
            results.append(item)
        return results

    # ------------------------------------------------------------------
    # KeyVault mappings (stored as sub-document in spn-metadata)
    # ------------------------------------------------------------------

    async def add_keyvault_mapping(self, spn_id: str, key_id: str, kv_secret_name: str) -> None:
        """Track a KeyVault secret name for a credential key_id."""
        metadata = await self.get_spn_metadata(spn_id) or {"id": spn_id, "spnId": spn_id}
        mappings = metadata.get("keyvaultMappings", {})
        mappings[key_id] = kv_secret_name
        metadata["keyvaultMappings"] = mappings
        await (await self._spn()).upsert_item(metadata)

    async def remove_keyvault_mapping(self, spn_id: str, key_id: str) -> str | None:
        """Remove a KeyVault mapping and return the secret name, or None."""
        metadata = await self.get_spn_metadata(spn_id)
        if not metadata:
            return None
        mappings = metadata.get("keyvaultMappings", {})
        kv_secret_name = mappings.pop(key_id, None)
        if kv_secret_name is not None:
            metadata["keyvaultMappings"] = mappings
            await (await self._spn()).upsert_item(metadata)
        return kv_secret_name


cosmos_service = CosmosService()
