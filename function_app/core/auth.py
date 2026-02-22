"""JWT token validation against Entra ID with JWKS caching and group membership checks."""

import logging
import time

import httpx
import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

from core.config import settings
from core.exceptions import ForbiddenError, UnauthorizedError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JWKS cache
# ---------------------------------------------------------------------------
_jwks_cache: dict | None = None
_jwks_cache_timestamp: float = 0.0
_JWKS_CACHE_TTL_SECONDS: float = 86400.0  # 24 hours

# ---------------------------------------------------------------------------
# Group membership cache  (user_oid -> (is_member, expiry_timestamp))
# ---------------------------------------------------------------------------
_group_membership_cache: dict[str, tuple[bool, float]] = {}


def _clear_caches() -> None:
    """Reset all module-level caches. Useful for testing."""
    global _jwks_cache, _jwks_cache_timestamp, _group_membership_cache
    _jwks_cache = None
    _jwks_cache_timestamp = 0.0
    _group_membership_cache.clear()


# ---------------------------------------------------------------------------
# JWKS helpers
# ---------------------------------------------------------------------------


def _base64url_decode(val: str) -> bytes:
    """Decode a Base64url-encoded string (no padding)."""
    remainder = len(val) % 4
    if remainder:
        val += "=" * (4 - remainder)
    import base64

    return base64.urlsafe_b64decode(val)


def _jwk_to_public_key(jwk: dict):
    """Convert a JWK dict (RSA) to a ``cryptography`` RSAPublicKey."""
    n_bytes = _base64url_decode(jwk["n"])
    e_bytes = _base64url_decode(jwk["e"])

    n_int = int.from_bytes(n_bytes, byteorder="big")
    e_int = int.from_bytes(e_bytes, byteorder="big")

    return RSAPublicNumbers(e_int, n_int).public_key(default_backend())


async def _fetch_jwks() -> dict:
    """Fetch the JWKS document from Entra ID."""
    url = settings.ENTRA_JWKS_URI_TEMPLATE.format(tenant_id=settings.TENANT_ID)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        resp.raise_for_status()
        return resp.json()


async def _get_jwks(force_refresh: bool = False) -> dict:
    """Return the cached JWKS, refreshing if stale or forced."""
    global _jwks_cache, _jwks_cache_timestamp

    now = time.monotonic()
    if _jwks_cache is not None and not force_refresh and (now - _jwks_cache_timestamp) < _JWKS_CACHE_TTL_SECONDS:
        return _jwks_cache

    logger.info("Refreshing JWKS cache (force=%s)", force_refresh)
    _jwks_cache = await _fetch_jwks()
    _jwks_cache_timestamp = now
    return _jwks_cache


def _find_signing_key(jwks: dict, kid: str):
    """Find the JWK matching the given ``kid`` and return a public key."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid and key.get("kty") == "RSA":
            return _jwk_to_public_key(key)
    return None


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------


async def validate_token(token: str) -> dict:
    """Validate a JWT bearer token against Entra ID.

    Returns the decoded claims dict on success.
    Raises ``UnauthorizedError`` on any validation failure.
    """
    try:
        # Decode header to get kid
        unverified_header = jwt.get_unverified_header(token)
    except jwt.exceptions.DecodeError as exc:
        raise UnauthorizedError("Malformed token header.") from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise UnauthorizedError("Token header missing 'kid'.")

    # Attempt to find signing key; refresh JWKS once on miss
    jwks = await _get_jwks()
    public_key = _find_signing_key(jwks, kid)

    if public_key is None:
        # Key rotation may have happened — force refresh once
        jwks = await _get_jwks(force_refresh=True)
        public_key = _find_signing_key(jwks, kid)

    if public_key is None:
        raise UnauthorizedError("Token signing key not found in JWKS.")

    expected_issuer = settings.ENTRA_ISSUER_TEMPLATE.format(tenant_id=settings.TENANT_ID)

    try:
        claims = jwt.decode(
            token,
            key=public_key,  # type: ignore[arg-type]  # PyJWT accepts RSA keys at runtime
            algorithms=["RS256"],
            audience=settings.CLIENT_ID,
            issuer=expected_issuer,
            options={
                "require": ["exp", "nbf", "aud", "iss", "oid"],
            },
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired.") from exc
    except jwt.InvalidAudienceError as exc:
        raise UnauthorizedError("Token audience is invalid.") from exc
    except jwt.InvalidIssuerError as exc:
        raise UnauthorizedError("Token issuer is invalid.") from exc
    except jwt.ImmatureSignatureError as exc:
        raise UnauthorizedError("Token is not yet valid (nbf).") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError(f"Token validation failed: {exc}") from exc

    return claims


def extract_user_context(claims: dict) -> dict:
    """Build a ``user_context`` dict from decoded JWT claims."""
    return {
        "oid": claims["oid"],
        "displayName": claims.get("name", ""),
        "email": claims.get("preferred_username", ""),
    }


# ---------------------------------------------------------------------------
# Group membership check (via Graph API)
# ---------------------------------------------------------------------------


async def check_group_membership(user_oid: str) -> bool:
    """Check whether *user_oid* is a member of the allowed Entra ID group.

    Results are cached for ``GROUP_MEMBERSHIP_CACHE_TTL_SECONDS``.
    """
    now = time.time()

    # Check cache
    cached = _group_membership_cache.get(user_oid)
    if cached is not None:
        is_member, expiry = cached
        if now < expiry:
            return is_member

    group_id = settings.ALLOWED_GROUP_ID
    if not group_id:
        logger.warning("ALLOWED_GROUP_ID is not configured; denying access by default.")
        return False

    # Import here to avoid circular import at module load time
    from services.graph_service import graph_service

    try:
        matched_ids = await graph_service.check_member_groups(user_oid, [group_id])
        is_member = group_id in matched_ids
    except Exception as exc:
        logger.exception("Failed to check group membership for user %s", user_oid)
        # On failure, don't cache, and deny access
        raise ForbiddenError(message="Unable to verify group membership.") from exc

    # Cache the result
    ttl = settings.GROUP_MEMBERSHIP_CACHE_TTL_SECONDS
    _group_membership_cache[user_oid] = (is_member, now + ttl)

    return is_member
