"""Tests for Pydantic request/response models."""

import pytest
from pydantic import ValidationError

from models.audit import AuditEvent
from models.owner import AddOwnerRequest, OwnerListResponse, OwnerResponse
from models.secret import CreateSecretRequest, SecretCreatedResponse
from models.spn import (
    CreateSpnRequest,
    SpnResponse,
    UpdateSpnRequest,
)

# ------------------------------------------------------------------
# CreateSpnRequest
# ------------------------------------------------------------------


class TestCreateSpnRequest:
    def test_valid_with_alias(self):
        m = CreateSpnRequest.model_validate({"displayName": "My App"})
        assert m.display_name == "My App"

    def test_valid_with_field_name(self):
        m = CreateSpnRequest(display_name="My App")
        assert m.display_name == "My App"

    def test_all_fields(self):
        m = CreateSpnRequest.model_validate(
            {
                "displayName": "My App",
                "description": "desc",
                "redirectUris": ["https://example.com"],
                "tags": ["tag1"],
            }
        )
        assert m.description == "desc"
        assert m.redirect_uris == ["https://example.com"]
        assert m.tags == ["tag1"]

    def test_missing_display_name_raises(self):
        with pytest.raises(ValidationError):
            CreateSpnRequest.model_validate({})

    def test_empty_display_name_raises(self):
        with pytest.raises(ValidationError):
            CreateSpnRequest.model_validate({"displayName": ""})

    def test_display_name_too_long_raises(self):
        with pytest.raises(ValidationError):
            CreateSpnRequest.model_validate({"displayName": "x" * 121})

    def test_serialization_uses_aliases(self):
        m = CreateSpnRequest(display_name="Test")
        data = m.model_dump(by_alias=True)
        assert "displayName" in data


# ------------------------------------------------------------------
# UpdateSpnRequest
# ------------------------------------------------------------------


class TestUpdateSpnRequest:
    def test_all_optional(self):
        m = UpdateSpnRequest.model_validate({})
        assert m.display_name is None
        assert m.description is None

    def test_partial_update(self):
        m = UpdateSpnRequest.model_validate({"displayName": "New Name"})
        assert m.display_name == "New Name"
        assert m.tags is None


# ------------------------------------------------------------------
# SpnResponse
# ------------------------------------------------------------------


class TestSpnResponse:
    def test_from_graph_data(self):
        m = SpnResponse.model_validate(
            {
                "id": "abc",
                "appId": "def",
                "displayName": "Test",
            }
        )
        assert m.id == "abc"
        assert m.app_id == "def"
        assert m.password_credentials == []
        assert m.owners == []

    def test_serialization_aliases(self):
        m = SpnResponse(id="a", app_id="b", display_name="c")
        data = m.model_dump(by_alias=True)
        assert "appId" in data
        assert "displayName" in data
        assert "passwordCredentials" in data


# ------------------------------------------------------------------
# CreateSecretRequest
# ------------------------------------------------------------------


class TestCreateSecretRequest:
    def test_defaults(self):
        m = CreateSecretRequest.model_validate({"displayName": "key1"})
        assert m.expires_in_days == 90

    def test_custom_expiry(self):
        m = CreateSecretRequest.model_validate({"displayName": "k", "expiresInDays": 365})
        assert m.expires_in_days == 365

    def test_expiry_too_low(self):
        with pytest.raises(ValidationError):
            CreateSecretRequest.model_validate({"displayName": "k", "expiresInDays": 0})

    def test_expiry_too_high(self):
        with pytest.raises(ValidationError):
            CreateSecretRequest.model_validate({"displayName": "k", "expiresInDays": 731})


# ------------------------------------------------------------------
# SecretCreatedResponse
# ------------------------------------------------------------------


class TestSecretCreatedResponse:
    def test_serialization(self):
        m = SecretCreatedResponse(
            key_id="k1",
            display_name="My Secret",
            secret_text="secret",
            key_vault_secret_name="spn-abc-def",
        )
        data = m.model_dump(by_alias=True)
        assert data["keyId"] == "k1"
        assert data["secretText"] == "secret"
        assert data["keyVaultSecretName"] == "spn-abc-def"


# ------------------------------------------------------------------
# Owner models
# ------------------------------------------------------------------


class TestOwnerModels:
    def test_add_owner_request(self):
        m = AddOwnerRequest.model_validate({"userId": "user-1"})
        assert m.user_id == "user-1"

    def test_add_owner_request_missing(self):
        with pytest.raises(ValidationError):
            AddOwnerRequest.model_validate({})

    def test_owner_response(self):
        m = OwnerResponse(id="u1", display_name="User", mail="u@x.com")
        data = m.model_dump(by_alias=True)
        assert data["displayName"] == "User"

    def test_owner_list_response(self):
        owner = OwnerResponse(id="u1")
        resp = OwnerListResponse(value=[owner], count=1)
        assert resp.count == 1


# ------------------------------------------------------------------
# AuditEvent
# ------------------------------------------------------------------


class TestAuditEvent:
    def test_full_event(self):
        m = AuditEvent(
            id="evt-1",
            spn_id="spn-1",
            action="CREATE_SPN",
            actor_oid="user-1",
            actor_name="Test",
            actor_email="t@x.com",
            timestamp="2025-01-01T00:00:00Z",
        )
        data = m.model_dump(by_alias=True)
        assert data["spnId"] == "spn-1"
        assert data["actorOid"] == "user-1"
        assert data["result"] == "success"

    def test_defaults(self):
        m = AuditEvent(id="e", spn_id="s", action="A", actor_oid="u", timestamp="t")
        assert m.details == {}
        assert m.result == "success"
        assert m.actor_name == ""
