# Testing Authentication Locally

Two options depending on your situation.

---

## Option 1 — Real token from your Azure tenant

Tests the full auth flow (JWT validation + group membership). Requires a configured app registration.

### 1. Configure `local.settings.json`

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "TENANT_ID": "<your-tenant-id>",
    "CLIENT_ID": "<your-client-id>",
    "CLIENT_SECRET": "<your-client-secret>",
    "ALLOWED_GROUP_ID": "<your-group-id>",
    "COSMOS_ENDPOINT": "https://<your-cosmos>.documents.azure.com:443/",
    "KEYVAULT_URI": "https://<your-kv>.vault.azure.net"
  }
}
```

### 2. Get a token and call the function

```bash
az login

TOKEN=$(az account get-access-token \
  --resource api://<YOUR_CLIENT_ID> \
  --query accessToken -o tsv)

curl -s http://localhost:7071/api/v1/spns \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Option 2 — Local bypass via `LOCAL_AUTH_BYPASS`

Skips JWT validation and injects a fake user context. Useful for fast iteration when you don't need to test the auth flow itself.

The bypass is already implemented in `core/decorators.py`. It activates only when `LOCAL_AUTH_BYPASS` is set in the environment — it is ignored in production where the variable is absent.

> **Note:** `@require_owner` still calls the real Graph API to check SPN ownership. Use your real Entra OID so ownership checks pass.

### 1. Get your Entra Object ID

```bash
az ad signed-in-user show --query id -o tsv
```

### 2. Add to `local.settings.json`

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "TENANT_ID": "<your-tenant-id>",
    "CLIENT_ID": "<your-client-id>",
    "CLIENT_SECRET": "<your-client-secret>",
    "ALLOWED_GROUP_ID": "<your-group-id>",
    "COSMOS_ENDPOINT": "https://<your-cosmos>.documents.azure.com:443/",
    "KEYVAULT_URI": "https://<your-kv>.vault.azure.net",
    "LOCAL_AUTH_BYPASS": "<your-entra-object-id>"
  }
}
```

### 3. Call any endpoint without a token

```bash
curl -s http://localhost:7071/api/v1/spns | jq
```

A warning is logged on every bypassed request:

```
WARNING: LOCAL_AUTH_BYPASS active — skipping auth for oid=<your-oid>
```

---

## Comparison

| | Option 1 (real token) | Option 2 (bypass) |
|---|---|---|
| Tests JWT validation | ✅ | ❌ |
| Tests group membership | ✅ | ❌ |
| Requires app registration | ✅ | ❌ |
| Fast iteration | ❌ | ✅ |
| `@require_owner` enforced | ✅ | ✅ |
| Safe in production | ✅ | ✅ (env var not set) |
