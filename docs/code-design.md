# Code Design & Azure Functions v2

## Azure Functions v2 — Programming Model

Azure Functions v2 drops the `function.json` file. Routes, HTTP methods, and auth level are declared **directly in Python via decorators**. The runtime uses `inspect.signature()` to understand each function — this has one critical constraint: **decorator wrappers must have the exact signature `(req: HttpRequest) -> HttpResponse`**, not `*args, **kwargs`, or the runtime will reject the function at load time.

```python
# function_app.py — single entry point
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app.register_functions(spn_bp)   # Blueprint = logical grouping of routes

# spn_blueprint.py — route declaration
@spn_bp.function_name("CreateSpn")
@spn_bp.route(route="v1/spns", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@handle_errors        # outermost: catches all exceptions → JSON error
@require_auth         # validates JWT + group membership, injects req.user_context
@require_owner        # verifies caller owns the target SPN (spn_id route param)
async def create_spn(req: func.HttpRequest) -> func.HttpResponse: ...
```

**Decorator execution order**: applied bottom-up (standard Python), but called top-down — so `handle_errors` wraps everything, `require_auth` runs before `require_owner`, and the endpoint body runs last. `functools.wraps` is mandatory on every wrapper so the runtime sees the original function name, not `wrapper`.

**Python version gotcha**: The Azure Functions Core Tools worker runs Python 3.10, regardless of what Python you develop with locally. This means:
- No PEP 695 type params (`def f[T: Model]`) → use `TypeVar`
- No `datetime.UTC` (3.11+) → use `timezone.utc`
- These are suppressed in ruff with `ignore = ["UP017", "UP047"]`

---

## Code Architecture

```
function_app/
├── function_app.py          # Entry: FunctionApp + register blueprints
├── blueprints/              # HTTP handlers (thin controllers)
│   ├── spn_blueprint.py     # POST/GET/PATCH/DELETE /v1/spns
│   ├── secret_blueprint.py  # POST/GET/DELETE /v1/spns/{id}/secrets
│   └── owner_blueprint.py   # GET/POST/DELETE /v1/spns/{id}/owners
├── core/                    # Shared infrastructure
│   ├── auth.py              # JWT validation (JWKS), group membership check
│   ├── decorators.py        # @require_auth, @require_owner
│   ├── error_handler.py     # @handle_errors → standardized { error: { code, message } }
│   ├── exceptions.py        # PortalError hierarchy (code, message, HTTP status)
│   ├── request_helpers.py   # parse_request_body(), json_response()
│   └── config.py            # Pydantic Settings (env vars)
├── models/                  # Pydantic v2 request/response schemas
│   ├── spn.py
│   ├── secret.py
│   ├── owner.py
│   └── audit.py
└── services/                # Business logic / external integrations
    ├── graph_service.py     # Microsoft Graph REST API (source of truth for SPNs)
    ├── cosmos_service.py    # Portal metadata + audit events
    ├── keyvault_service.py  # Secret storage
    └── audit_service.py     # Fire-and-forget audit log wrapper
```

---

## Key Patterns

### 1. Exception-driven flow control

All domain errors subclass `PortalError(code, message, status_code)`. Blueprints raise, `@handle_errors` catches and serializes. No `try/except` inside endpoints except for cleanup paths.

```python
class DuplicateSpnNameError(PortalError):
    def __init__(self, name): super().__init__("DUPLICATE_SPN_NAME", f"...", 400, "displayName")

# Blueprint just raises — handle_errors converts to { "error": { "code": ..., "message": ... } }
if await graph_service.check_duplicate_name(body.display_name):
    raise DuplicateSpnNameError(body.display_name)
```

### 2. Module-level singletons with lazy init

Services are instantiated at module import time but delay all I/O (credential acquisition, client creation) until the first call. This avoids cold-start failures when env vars aren't yet available.

```python
class CosmosService:
    def __init__(self): self._client = None  # no I/O here

    async def _ensure_initialized(self):
        if self._client: return
        self._credential = DefaultAzureCredential()
        self._client = CosmosClient(url=settings.COSMOS_ENDPOINT, credential=self._credential)
        ...

cosmos_service = CosmosService()  # singleton imported by blueprints
```

### 3. Pydantic v2 models with camelCase aliases

All models use `ConfigDict(populate_by_name=True)` + `Field(alias="camelCase")`. Fields are accessible by Python name internally, but JSON I/O uses camelCase (matching Graph API convention). **Important**: pyright's pydantic plugin generates `__init__` with alias names, so model constructors in code must use camelCase kwargs.

```python
class SpnResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    display_name: str = Field(..., alias="displayName")

# Construction uses alias (pyright enforcement)
SpnResponse(id=..., displayName=..., appId=...)

# Serialization
json_response(response)  # → model.model_dump(by_alias=True) → camelCase JSON
```

### 4. Auth context propagation via request attribute

`@require_auth` monkey-patches `req.user_context` (a `dict` with `oid`, `displayName`, `email`). Azure's `HttpRequest` doesn't prevent arbitrary attributes, so this is the simplest approach — no thread-locals or contextvars needed in a single-invocation serverless function.

```python
# require_auth sets:
req.user_context = {"oid": "...", "displayName": "...", "email": "..."}

# Endpoint reads:
user_context: dict = req.user_context  # type: ignore[attr-defined]
```

### 5. Microsoft Graph as source of truth

SPN data lives entirely in Entra ID (Graph API). Cosmos DB stores only portal-specific metadata (creator OID, KeyVault secret mappings, audit events). The list endpoint fetches owned apps from Graph then optionally enriches with Cosmos metadata (best-effort, non-fatal).

---

## Request Lifecycle

```
HTTP request
  → Azure Functions host
  → handle_errors (try/except wrapper)
    → require_auth (JWT validation + group check → sets req.user_context)
      → require_owner (Graph API: verify caller owns target SPN)
        → endpoint body
            parse_request_body() → Pydantic validation
            graph_service.*()    → Microsoft Graph REST
            cosmos_service.*()   → Cosmos DB (metadata)
            keyvault_service.()  → Key Vault (secrets)
            audit_service.log()  → fire-and-forget audit
            json_response()      → model.model_dump(by_alias=True) → HttpResponse
```

---

## Testing Notes

The main mock-patching complexity: blueprints import services at module level (`from services.graph_service import graph_service`), which binds the name locally. To intercept in tests, you must patch **both** the service module **and** the blueprint module:

```python
with patch("services.graph_service.graph_service", mock), \
     patch("blueprints.spn_blueprint.graph_service", mock):
    ...
```

Similarly, `@require_auth` imports `validate_token` from `core.auth` at decoration time, so tests patch `core.decorators.validate_token`, not `core.auth.validate_token`.
