"""Microsoft Graph API service for all SPN-related operations."""

import logging
from datetime import datetime, timedelta, timezone

import httpx
from azure.identity import DefaultAzureCredential

from core.config import settings
from core.exceptions import GraphApiError, SpnNotFoundError

logger = logging.getLogger(__name__)

_GRAPH_SCOPE = "https://graph.microsoft.com/.default"


class GraphService:
    """Thin async wrapper around the Microsoft Graph REST API.

    Uses ``DefaultAzureCredential`` (client-credentials flow) to obtain
    tokens and ``httpx.AsyncClient`` for all HTTP calls.
    """

    def __init__(self) -> None:
        self._credential = DefaultAzureCredential()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def get_access_token(self) -> str:
        """Obtain an access token for Microsoft Graph using the default credential."""
        token = self._credential.get_token(_GRAPH_SCOPE)
        return token.token

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | list | None = None,
        params: dict | None = None,
        expected_status: set[int] | None = None,
    ) -> httpx.Response:
        """Execute an authenticated request against the Graph API.

        Raises ``GraphApiError`` for unexpected non-2xx responses.
        """
        url = f"{settings.GRAPH_API_BASE}{path}"
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                url,
                headers=headers,
                json=json,
                params=params,
                timeout=30.0,
            )

        if expected_status is not None:
            if resp.status_code not in expected_status:
                await self._raise_graph_error(resp)
            return resp

        if resp.is_success:
            return resp

        await self._raise_graph_error(resp)
        # unreachable, but keeps type checkers happy
        return resp  # pragma: no cover

    @staticmethod
    async def _raise_graph_error(resp: httpx.Response) -> None:
        """Parse a Graph error response and raise ``GraphApiError``."""
        try:
            body = resp.json()
            error_info = body.get("error", {})
            code = error_info.get("code", "UnknownError")
            message = error_info.get("message", resp.text)
        except Exception:
            code = "UnknownError"
            message = resp.text

        logger.error(
            "Graph API error: status=%d code=%s message=%s",
            resp.status_code,
            code,
            message,
        )
        raise GraphApiError(f"Graph API error ({resp.status_code}): {code} - {message}")

    # ------------------------------------------------------------------
    # Group membership
    # ------------------------------------------------------------------

    async def check_member_groups(self, user_oid: str, group_ids: list[str]) -> list[str]:
        """Check which of the supplied *group_ids* the user is a member of.

        Uses ``POST /users/{id}/checkMemberGroups`` when the user object is
        accessible, falling back to ``GET /groups/{id}/members`` for MSA /
        guest accounts whose OID is not directly queryable in the directory.
        Returns the subset of *group_ids* the user belongs to.
        """
        try:
            resp = await self._request(
                "POST",
                f"/users/{user_oid}/checkMemberGroups",
                json={"groupIds": group_ids},
                expected_status={200, 404},
            )
            if resp.status_code == 200:
                return resp.json().get("value", [])
        except GraphApiError:
            pass

        # Fallback: query each group's members directly (handles MSA / guest accounts)
        matched: list[str] = []
        for group_id in group_ids:
            resp = await self._request(
                "GET",
                f"/groups/{group_id}/members",
                params={"$select": "id", "$top": "999"},
            )
            member_ids = {m.get("id") for m in resp.json().get("value", [])}
            if user_oid in member_ids:
                matched.append(group_id)
        return matched

    # ------------------------------------------------------------------
    # Applications (app registrations)
    # ------------------------------------------------------------------

    async def check_duplicate_name(self, display_name: str) -> bool:
        """Return ``True`` if an application with *display_name* already exists."""
        # OData filter — exact match on displayName
        resp = await self._request(
            "GET",
            "/applications",
            params={
                "$filter": f"displayName eq '{display_name}'",
                "$select": "id",
                "$top": "1",
            },
        )
        data = resp.json()
        return len(data.get("value", [])) > 0

    async def create_application(
        self,
        display_name: str,
        description: str | None = None,
        redirect_uris: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """Create a new Entra ID application registration.

        Returns the full application object from Graph.
        """
        body: dict = {"displayName": display_name}
        if description is not None:
            body["description"] = description
        if redirect_uris:
            body["web"] = {"redirectUris": redirect_uris}
        if tags:
            body["tags"] = tags

        resp = await self._request("POST", "/applications", json=body)
        return resp.json()

    async def create_service_principal(self, app_id: str) -> dict:
        """Create a service principal for the given *app_id*.

        Returns the full service principal object from Graph.
        """
        resp = await self._request(
            "POST",
            "/servicePrincipals",
            json={"appId": app_id},
        )
        return resp.json()

    async def get_application(self, app_object_id: str) -> dict:
        """Retrieve an application by its object ID.

        Raises ``SpnNotFoundError`` if not found.
        """
        resp = await self._request(
            "GET",
            f"/applications/{app_object_id}",
            expected_status={200, 404},
        )
        if resp.status_code == 404:
            raise SpnNotFoundError(app_object_id)
        return resp.json()

    async def list_owned_applications(self, user_oid: str) -> list[dict]:
        """List applications owned by the given user.

        Uses ``GET /users/{id}/ownedObjects/microsoft.graph.application``.
        """
        results: list[dict] = []
        next_link: str | None = None

        # First request
        resp = await self._request(
            "GET",
            f"/users/{user_oid}/ownedObjects/microsoft.graph.application",
            params={"$top": "100"},
        )
        data = resp.json()
        results.extend(data.get("value", []))
        next_link = data.get("@odata.nextLink")

        # Follow pagination
        while next_link:
            async with httpx.AsyncClient() as client:
                access_token = self.get_access_token()
                page_resp = await client.get(
                    next_link,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
            if not page_resp.is_success:
                await self._raise_graph_error(page_resp)
            page_data = page_resp.json()
            results.extend(page_data.get("value", []))
            next_link = page_data.get("@odata.nextLink")

        return results

    async def update_application(self, app_object_id: str, updates: dict) -> dict:
        """Update an application registration.

        ``PATCH /applications/{id}`` returns 204 on success, so we re-fetch
        the application to return the updated object.
        """
        await self._request(
            "PATCH",
            f"/applications/{app_object_id}",
            json=updates,
            expected_status={204},
        )
        return await self.get_application(app_object_id)

    async def delete_application(self, app_object_id: str) -> None:
        """Delete an application registration."""
        await self._request(
            "DELETE",
            f"/applications/{app_object_id}",
            expected_status={204},
        )

    # ------------------------------------------------------------------
    # Secrets (password credentials)
    # ------------------------------------------------------------------

    async def add_password(
        self,
        app_object_id: str,
        display_name: str,
        expires_in_days: int,
    ) -> dict:
        """Add a client secret (password credential) to an application.

        Returns the credential object which includes ``secretText`` (the
        plaintext secret, only available at creation time).
        """
        end_date = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        body = {
            "passwordCredential": {
                "displayName": display_name,
                "endDateTime": end_date.isoformat(),
            }
        }
        resp = await self._request(
            "POST",
            f"/applications/{app_object_id}/addPassword",
            json=body,
        )
        return resp.json()

    async def remove_password(self, app_object_id: str, key_id: str) -> None:
        """Remove a client secret from an application."""
        await self._request(
            "POST",
            f"/applications/{app_object_id}/removePassword",
            json={"keyId": key_id},
            expected_status={204},
        )

    # ------------------------------------------------------------------
    # Owners
    # ------------------------------------------------------------------

    async def list_owners(self, app_object_id: str) -> list[dict]:
        """List owners of an application."""
        resp = await self._request(
            "GET",
            f"/applications/{app_object_id}/owners",
        )
        data = resp.json()
        return data.get("value", [])

    async def add_owner(self, app_object_id: str, user_oid: str) -> None:
        """Add *user_oid* as an owner of both the application and its service
        principal."""
        owner_ref = {"@odata.id": f"{settings.GRAPH_API_BASE}/directoryObjects/{user_oid}"}

        # Add owner to the application
        await self._request(
            "POST",
            f"/applications/{app_object_id}/owners/$ref",
            json=owner_ref,
            expected_status={204},
        )

        # Also add owner to the corresponding service principal (best-effort)
        app = await self.get_application(app_object_id)
        app_id = app.get("appId")
        if app_id:
            sp = await self.get_service_principal_by_app_id(app_id)
            if sp:
                try:
                    await self._request(
                        "POST",
                        f"/servicePrincipals/{sp['id']}/owners/$ref",
                        json=owner_ref,
                        expected_status={204},
                    )
                except GraphApiError:
                    logger.warning(
                        "Failed to add owner %s to service principal %s; application owner was added successfully.",
                        user_oid,
                        sp["id"],
                    )

    async def remove_owner(self, app_object_id: str, user_oid: str) -> None:
        """Remove *user_oid* as an owner from both the application and its
        service principal."""
        # Remove from application
        await self._request(
            "DELETE",
            f"/applications/{app_object_id}/owners/{user_oid}/$ref",
            expected_status={204},
        )

        # Also remove from the corresponding service principal (best-effort)
        app = await self.get_application(app_object_id)
        app_id = app.get("appId")
        if app_id:
            sp = await self.get_service_principal_by_app_id(app_id)
            if sp:
                try:
                    await self._request(
                        "DELETE",
                        f"/servicePrincipals/{sp['id']}/owners/{user_oid}/$ref",
                        expected_status={204},
                    )
                except GraphApiError:
                    logger.warning(
                        "Failed to remove owner %s from service principal %s; "
                        "application owner was removed successfully.",
                        user_oid,
                        sp["id"],
                    )

    # ------------------------------------------------------------------
    # Service principals
    # ------------------------------------------------------------------

    async def get_service_principal_by_app_id(self, app_id: str) -> dict | None:
        """Find a service principal by its application (client) ID.

        Returns ``None`` if no service principal exists for the given app.
        """
        resp = await self._request(
            "GET",
            "/servicePrincipals",
            params={"$filter": f"appId eq '{app_id}'", "$top": "1"},
        )
        data = resp.json()
        values = data.get("value", [])
        return values[0] if values else None

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    async def get_user(self, user_oid: str) -> dict:
        """Retrieve a user profile from Entra ID."""
        resp = await self._request(
            "GET",
            f"/users/{user_oid}",
            params={"$select": "id,displayName,mail,userPrincipalName"},
        )
        return resp.json()


# Module-level singleton so other modules can do ``from services.graph_service import graph_service``
graph_service = GraphService()
