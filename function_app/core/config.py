import os


class Settings:
    TENANT_ID: str = os.environ.get("TENANT_ID", "")
    CLIENT_ID: str = os.environ.get("CLIENT_ID", "")
    CLIENT_SECRET: str = os.environ.get("CLIENT_SECRET", "")
    ALLOWED_GROUP_ID: str = os.environ.get("ALLOWED_GROUP_ID", "")
    COSMOS_ENDPOINT: str = os.environ.get("COSMOS_ENDPOINT", "")
    COSMOS_DATABASE: str = os.environ.get("COSMOS_DATABASE", "spn-portal")
    KEYVAULT_URI: str = os.environ.get("KEYVAULT_URI", "")
    APPINSIGHTS_CONNECTION: str = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

    GRAPH_API_BASE: str = "https://graph.microsoft.com/v1.0"
    ENTRA_JWKS_URI_TEMPLATE: str = "https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    ENTRA_ISSUER_TEMPLATE: str = "https://login.microsoftonline.com/{tenant_id}/v2.0"

    GROUP_MEMBERSHIP_CACHE_TTL_SECONDS: int = 300  # 5 minutes


settings = Settings()
