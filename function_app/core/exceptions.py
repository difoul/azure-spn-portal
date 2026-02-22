class PortalError(Exception):
    """Base exception for all portal errors."""

    def __init__(self, code: str, message: str, status_code: int = 500, target: str | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.target = target
        super().__init__(message)


class ValidationError(PortalError):
    def __init__(self, message: str, target: str | None = None):
        super().__init__("VALIDATION_ERROR", message, 400, target)


class DuplicateSpnNameError(PortalError):
    def __init__(self, name: str):
        super().__init__(
            "DUPLICATE_SPN_NAME",
            f"A service principal with the name '{name}' already exists.",
            400,
            "displayName",
        )


class MaxSecretsReachedError(PortalError):
    def __init__(self):
        super().__init__("MAX_SECRETS_REACHED", "This service principal already has the maximum of 2 secrets.", 400)


class CannotRemoveLastOwnerError(PortalError):
    def __init__(self):
        super().__init__("CANNOT_REMOVE_LAST_OWNER", "Cannot remove the last owner of a service principal.", 400)


class UnauthorizedError(PortalError):
    def __init__(self, message: str = "Missing or invalid authorization token."):
        super().__init__("UNAUTHORIZED", message, 401)


class ForbiddenError(PortalError):
    def __init__(self, code: str = "FORBIDDEN", message: str = "You do not have permission to perform this action."):
        super().__init__(code, message, 403)


class NotOwnerError(ForbiddenError):
    def __init__(self):
        super().__init__("NOT_OWNER", "You are not an owner of this service principal.")


class SpnNotFoundError(PortalError):
    def __init__(self, spn_id: str):
        super().__init__("SPN_NOT_FOUND", f"Service principal '{spn_id}' not found.", 404)


class SecretNotFoundError(PortalError):
    def __init__(self, key_id: str):
        super().__init__("SECRET_NOT_FOUND", f"Secret '{key_id}' not found.", 404)


class OwnerNotFoundError(PortalError):
    def __init__(self, owner_id: str):
        super().__init__("OWNER_NOT_FOUND", f"Owner '{owner_id}' not found on this service principal.", 404)


class GraphApiError(PortalError):
    def __init__(self, message: str = "Microsoft Graph API returned an error."):
        super().__init__("GRAPH_API_ERROR", message, 502)
