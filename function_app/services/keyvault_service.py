"""Azure Key Vault service for storing SPN secrets."""

import logging

from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient

from core.config import settings

logger = logging.getLogger(__name__)


class KeyVaultService:
    """Async Key Vault client with lazy initialization."""

    def __init__(self) -> None:
        self._client: SecretClient | None = None
        self._credential: DefaultAzureCredential | None = None

    async def _ensure_initialized(self) -> None:
        if self._client is not None:
            return

        self._credential = DefaultAzureCredential()
        self._client = SecretClient(
            vault_url=settings.KEYVAULT_URI,
            credential=self._credential,
        )

    @staticmethod
    def _make_secret_name(app_id: str, key_id: str) -> str:
        """Build a Key Vault secret name from app_id and key_id."""
        clean_app = app_id.replace("-", "")
        clean_key = key_id.replace("-", "")
        return f"spn-{clean_app}-{clean_key}"

    async def _get_client(self) -> SecretClient:
        await self._ensure_initialized()
        assert self._client is not None
        return self._client

    async def store_secret(self, app_id: str, key_id: str, secret_value: str) -> str:
        """Store a secret in Key Vault. Returns the secret name."""
        name = self._make_secret_name(app_id, key_id)
        await (await self._get_client()).set_secret(name, secret_value)
        logger.info("Stored secret %s in Key Vault", name)
        return name

    async def get_secret(self, secret_name: str) -> str | None:
        """Retrieve a secret value. Returns None if not found."""
        try:
            secret = await (await self._get_client()).get_secret(secret_name)
            return secret.value
        except Exception:
            logger.debug("Secret %s not found in Key Vault", secret_name)
            return None

    async def delete_secret(self, secret_name: str) -> None:
        """Soft-delete a secret. Idempotent — ignores not-found errors."""
        try:
            await (await self._get_client()).delete_secret(secret_name)
            logger.info("Deleted secret %s from Key Vault", secret_name)
        except Exception:
            logger.debug("Secret %s not found for deletion", secret_name)


keyvault_service = KeyVaultService()
