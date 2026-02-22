"""Pydantic models for SPN (Service Principal) operations."""

from pydantic import BaseModel, ConfigDict, Field


class CreateSpnRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    display_name: str = Field(..., alias="displayName", min_length=1, max_length=120)
    description: str | None = Field(None, alias="description")
    redirect_uris: list[str] | None = Field(None, alias="redirectUris")
    tags: list[str] | None = Field(None, alias="tags")


class UpdateSpnRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    display_name: str | None = Field(None, alias="displayName", min_length=1, max_length=120)
    description: str | None = Field(None, alias="description")
    redirect_uris: list[str] | None = Field(None, alias="redirectUris")
    tags: list[str] | None = Field(None, alias="tags")


class SecretSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key_id: str = Field(..., alias="keyId")
    display_name: str = Field(..., alias="displayName")
    start_date_time: str | None = Field(None, alias="startDateTime")
    end_date_time: str | None = Field(None, alias="endDateTime")


class SpnResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    app_id: str = Field(..., alias="appId")
    display_name: str = Field(..., alias="displayName")
    description: str | None = Field(None, alias="description")
    created_date_time: str | None = Field(None, alias="createdDateTime")
    password_credentials: list[SecretSummaryResponse] = Field(default_factory=list, alias="passwordCredentials")
    owners: list[dict] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class SpnListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    value: list[SpnResponse]
    count: int
