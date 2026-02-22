"""Tests for AuditService."""

from unittest.mock import AsyncMock, patch

import pytest

from services.audit_service import CREATE_SPN, AuditService


@pytest.fixture
def audit():
    return AuditService()


@pytest.fixture
def user_context():
    return {
        "oid": "user-oid-1",
        "displayName": "Test User",
        "email": "test@example.com",
    }


class TestLog:
    async def test_creates_audit_event(self, audit, user_context):
        with patch("services.audit_service.cosmos_service") as mock_cosmos:
            mock_cosmos.create_audit_event = AsyncMock()
            await audit.log("spn-1", CREATE_SPN, user_context, details={"key": "val"})

            mock_cosmos.create_audit_event.assert_called_once()
            event = mock_cosmos.create_audit_event.call_args[0][0]
            assert event["spnId"] == "spn-1"
            assert event["action"] == CREATE_SPN
            assert event["actorOid"] == "user-oid-1"
            assert event["details"] == {"key": "val"}
            assert event["result"] == "success"
            assert "id" in event
            assert "timestamp" in event

    async def test_does_not_raise_on_failure(self, audit, user_context):
        with patch("services.audit_service.cosmos_service") as mock_cosmos:
            mock_cosmos.create_audit_event = AsyncMock(side_effect=Exception("DB down"))
            # Should not raise
            await audit.log("spn-1", CREATE_SPN, user_context)


class TestGetEvents:
    async def test_delegates_to_cosmos(self, audit):
        with patch("services.audit_service.cosmos_service") as mock_cosmos:
            mock_cosmos.list_audit_events = AsyncMock(return_value=[{"id": "e1"}])
            result = await audit.get_events("spn-1", limit=10)
            assert len(result) == 1
            mock_cosmos.list_audit_events.assert_called_once_with("spn-1", 10)
