# API Testing with curl

All requests require a bearer token. Set it up once:

```bash
# Option A — real token
TOKEN=$(az account get-access-token \
  --resource api://8ad3b07f-b141-483c-b7a5-48aac06dc0df \
  --query accessToken -o tsv)

# Option B — LOCAL_AUTH_BYPASS (no token needed, omit -H "Authorization" header)
# Set LOCAL_AUTH_BYPASS=<your-oid> in local.settings.json
```

Base URL:
```bash
BASE=http://localhost:7071/api
```

---

## Health

```bash
curl -s $BASE/v1/health | jq
```

Expected:
```json
{ "status": "ok" }
```

---

## SPNs

### Create SPN

```bash
curl -s -X POST $BASE/v1/spns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "displayName": "my-service-principal",
    "description": "Created via portal API",
    "tags": ["team:platform", "env:dev"]
  }' | jq
```

Save the returned `id` (app object ID) for subsequent requests:
```bash
SPN_ID="<id from response>"
```

### List SPNs (owned by caller)

```bash
curl -s $BASE/v1/spns \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Get SPN

```bash
curl -s $BASE/v1/spns/$SPN_ID \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Update SPN

```bash
curl -s -X PATCH $BASE/v1/spns/$SPN_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "tags": ["team:platform", "env:prod"]
  }' | jq
```

### Delete SPN

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE $BASE/v1/spns/$SPN_ID \
  -H "Authorization: Bearer $TOKEN"
# Expected: 204
```

---

## Secrets

### Add a secret

```bash
curl -s -X POST $BASE/v1/spns/$SPN_ID/secrets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "displayName": "ci-secret",
    "expiresInDays": 90
  }' | jq
```

> The `secretText` is returned **only once** — save it immediately.

Save the returned `keyId`:
```bash
KEY_ID="<keyId from response>"
```

### List secrets (metadata only, no values)

```bash
curl -s $BASE/v1/spns/$SPN_ID/secrets \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Delete a secret

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE $BASE/v1/spns/$SPN_ID/secrets/$KEY_ID \
  -H "Authorization: Bearer $TOKEN"
# Expected: 204
```

---

## Owners

### List owners

```bash
curl -s $BASE/v1/spns/$SPN_ID/owners \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Add an owner

```bash
curl -s -X POST $BASE/v1/spns/$SPN_ID/owners \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "<entra-object-id-of-user-to-add>"
  }' | jq
```

Get a user's object ID:
```bash
az ad user show --id user@example.com --query id -o tsv
```

### Remove an owner

```bash
OWNER_ID="<object-id-of-owner-to-remove>"

curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE $BASE/v1/spns/$SPN_ID/owners/$OWNER_ID \
  -H "Authorization: Bearer $TOKEN"
# Expected: 204
# Note: removing the last owner is rejected with 400
```

---

## Error responses

All errors follow this shape:

```json
{
  "error": {
    "code": "SPN_NOT_FOUND",
    "message": "Service principal 'abc' not found."
  }
}
```

| Code | HTTP | Cause |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing / invalid / expired token |
| `FORBIDDEN` | 403 | Not in the allowed Entra ID group |
| `NOT_OWNER` | 403 | Not an owner of the target SPN |
| `SPN_NOT_FOUND` | 404 | SPN object ID not found |
| `SECRET_NOT_FOUND` | 404 | Key ID not found on SPN |
| `OWNER_NOT_FOUND` | 404 | Owner not found on SPN |
| `DUPLICATE_SPN_NAME` | 400 | Display name already taken |
| `MAX_SECRETS_REACHED` | 400 | SPN already has 2 secrets |
| `CANNOT_REMOVE_LAST_OWNER` | 400 | Would leave SPN ownerless |
| `VALIDATION_ERROR` | 400 | Invalid request body |
| `GRAPH_API_ERROR` | 502 | Microsoft Graph returned an error |
