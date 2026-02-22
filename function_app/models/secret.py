"""Pydantic models for secret (password credential) operations."""

from pydantic import BaseModel, ConfigDict, Field


class CreateSecretRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    display_name: str = Field(..., alias="displayName", min_length=1)
    expires_in_days: int = Field(90, alias="expiresInDays", ge=1, le=730)


class SecretCreatedResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key_id: str = Field(..., alias="keyId")
    display_name: str = Field(..., alias="displayName")
    secret_text: str = Field(..., alias="secretText")
    start_date_time: str | None = Field(None, alias="startDateTime")
    end_date_time: str | None = Field(None, alias="endDateTime")
    key_vault_secret_name: str = Field(..., alias="keyVaultSecretName")


class SecretListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    value: list[dict]
    count: int
