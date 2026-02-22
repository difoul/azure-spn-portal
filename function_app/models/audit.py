"""Pydantic models for audit events."""

from pydantic import BaseModel, ConfigDict, Field


class AuditEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    spn_id: str = Field(..., alias="spnId")
    action: str
    actor_oid: str = Field(..., alias="actorOid")
    actor_name: str = Field("", alias="actorName")
    actor_email: str = Field("", alias="actorEmail")
    timestamp: str
    details: dict = Field(default_factory=dict)
    result: str = Field("success")
