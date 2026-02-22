"""Audit service — convenience wrapper around Cosmos DB audit events."""

import logging
import uuid
from datetime import datetime, timezone

from services.cosmos_service import cosmos_service

logger = logging.getLogger(__name__)

# Standard audit actions
CREATE_SPN = "CREATE_SPN"
UPDATE_SPN = "UPDATE_SPN"
DELETE_SPN = "DELETE_SPN"
ADD_SECRET = "ADD_SECRET"
DELETE_SECRET = "DELETE_SECRET"
ADD_OWNER = "ADD_OWNER"
REMOVE_OWNER = "REMOVE_OWNER"


class AuditService:
    """Thin wrapper that builds audit event dicts and delegates to Cosmos."""

    async def log(
        self,
        spn_id: str,
        action: str,
        user_context: dict,
        details: dict | None = None,
        result: str = "success",
    ) -> None:
        """Record an audit event. Fire-and-forget safe — catches all exceptions."""
        try:
            event = {
                "id": str(uuid.uuid4()),
                "spnId": spn_id,
                "action": action,
                "actorOid": user_context.get("oid", ""),
                "actorName": user_context.get("displayName", ""),
                "actorEmail": user_context.get("email", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": details or {},
                "result": result,
            }
            await cosmos_service.create_audit_event(event)
        except Exception:
            logger.exception("Failed to log audit event: action=%s spn_id=%s", action, spn_id)

    async def get_events(self, spn_id: str, limit: int = 50) -> list[dict]:
        """Retrieve recent audit events for an SPN."""
        return await cosmos_service.list_audit_events(spn_id, limit)


audit_service = AuditService()
