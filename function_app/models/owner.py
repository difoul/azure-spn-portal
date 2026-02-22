"""Pydantic models for owner management operations."""

from pydantic import BaseModel, ConfigDict, Field


class AddOwnerRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(..., alias="userId")


class OwnerResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    display_name: str | None = Field(None, alias="displayName")
    mail: str | None = Field(None, alias="mail")
    user_principal_name: str | None = Field(None, alias="userPrincipalName")


class OwnerListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    value: list[OwnerResponse]
    count: int
