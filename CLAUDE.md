# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Azure SPN Self-Service Portal — a self-service application allowing corporate Azure users to create and manage Service Principals (SPNs) independently, without requiring admin intervention. Access is restricted to users in a specific Entra ID group, accessible only from the corporate network.

## Tech Stack

- **Backend:** Python — Azure Functions v2 (decorator-based programming model)
- **Frontend:** React 19 + TypeScript + Vite, TanStack Router (file-based) + TanStack Query v5, MSAL.js (`@azure/msal-browser@^4` + `@azure/msal-react@^3`), Tailwind CSS v4
- **Infrastructure:** Terraform (IaC)
- **Cloud:** Azure, private networking (no public internet exposure)
- **Auth:** Entra ID, single-tenant, application-level permissions (client credentials / managed identity with admin-consented Graph API)
- **Database:** Azure Cosmos DB
- **Secret storage:** Azure Key Vault (secrets also shown once to user at creation time)
- **Audit:** Azure Log Analytics
- **CI/CD:** GitLab CI/CD
- **Hosting:** Backend on Azure Functions (Flex Consumption, private endpoint); Frontend on Azure Static Web Apps (Standard tier)

## Architecture Decisions

- **Serverless:** Azure Functions with VNet integration for private network access only (corporate users on VPN/corporate network)
- **No API Management:** Browser calls the Function App directly at its private DNS hostname. Corporate DNS resolves to the private endpoint IP. CORS is enabled on the Function App (`WEBSITE_CORS_ALLOWED_ORIGINS = "*"` — safe because the Function App has no public network access).
- **Application-level Graph API permissions:** The app operates with its own identity, not delegated user permissions. Admin consent required for Graph API scopes.
- **Role-based access:** Only users in a designated Entra ID security group can use the portal.
- **Secret delivery:** Secrets are shown once in the response AND stored in Azure Key Vault for later retrieval by the owner.
- **SWA serves static files only** — no SWA-managed API routing. The browser (on corporate VPN) calls the Function App directly.

## Key Requirements

- Requestor becomes owner of the created Service Principal
- Owners can designate additional owners
- Owners can manage SPN configuration (secret renewal, redirect URIs, etc.)
- Maximum 2 secrets per service principal
- No duplicate SPN names allowed
- All operations must be auditable (Log Analytics)
- Solution must be cost-efficient

## Build & Dev Commands

```bash
# ---------- Backend ----------
ruff check function_app/          # lint
ruff format --check function_app/ # format check
pyright function_app/             # type check
pytest function_app/tests/        # run tests
pytest function_app/tests/ --cov=function_app    # with coverage
pip install -r function_app/requirements.txt     # install deps
cd function_app && func start                    # run locally (Azure Functions Core Tools)

# ---------- Frontend ----------
cd frontend && npm install        # install deps (first time)
npx msw init public/              # generate MSW service worker (one-time, gitignored)
npm run dev:mock                  # run with mock API + no Azure login required
npm run dev                       # run against real backend (requires VPN or local func start)
npm run typecheck                 # tsc --noEmit
npm run lint                      # eslint
npm run build                     # production build → frontend/dist/

# ---------- Terraform ----------
cd terraform/environments/dev
terraform init && terraform plan && terraform apply
```

## Code Architecture

### Backend (`function_app/`)

- **`function_app.py`** — entry point, registers all blueprints
- **`blueprints/`** — HTTP route groups by domain (spn, secret, owner, health)
- **`core/`** — auth (JWT validation against Entra ID JWKS), decorators (`@require_auth`, `@require_owner`, `@handle_errors`), exceptions, config
- **`services/`** — business logic: `graph_service.py` (Microsoft Graph API via httpx async), `cosmos_service.py`, `keyvault_service.py`, `audit_service.py`
- **`models/`** — Pydantic request/response models

Microsoft Graph is the source of truth for SPN data. Cosmos DB stores only portal metadata and audit events.

### Frontend (`frontend/src/`)

- **`main.tsx`** — bootstrap: `msalInstance.initialize()` → `handleRedirectPromise()` → render. In mock mode starts MSW worker first.
- **`router.ts`** — `createRouter()`, `RouterContext` interface passes `queryClient` to routes
- **`auth/msalConfig.ts`** — `PublicClientApplication`, scope: `api://${clientId}/access_as_user`
- **`api/`** — `client.ts` (fetch wrapper, token acquisition), `types.ts`, `spns.ts`, `secrets.ts`, `owners.ts`
- **`routes/`** — file-based TanStack Router; `routeTree.gen.ts` auto-generated (gitignored)
  - `__root.tsx` — nav bar, dark mode toggle, MSAL auth guard (bypassed in mock mode)
  - `spns/index.tsx` — SPN list
  - `spns/new.tsx` — create SPN form
  - `spns/$spnId.tsx` — layout: SPN header + Secrets/Owners tab bar
  - `spns/$spnId/secrets.tsx` — secrets tab
  - `spns/$spnId/owners.tsx` — owners tab
- **`components/`** — `SpnList`, `SpnForm`, `SecretList`, `SecretRevealModal` (shows `secretText` once, never persisted), `OwnerList`, `ConfirmDialog`; `ui/` primitives: `Button`, `Input`, `Badge`, `Spinner`
- **`mocks/`** — MSW handlers (`handlers.ts`), in-memory mock data (`data.ts`), browser worker (`browser.ts`). Enabled via `VITE_ENABLE_MOCK=true` — tree-shaken from production builds.
- **`lib/utils.ts`** — `cn()`, `formatDate()`, `isExpired()`, `isExpiringSoon()`

TanStack Query keys: `['spns']`, `['spns', id]`, `['spns', id, 'secrets']`, `['spns', id, 'owners']`

Dark mode: `.dark` class on `<html>`, toggled via `localStorage.theme`, pre-applied in `index.html` before first paint. Tailwind v4 — config via `@import "tailwindcss"` in `main.css`, no `tailwind.config.ts`.

### Terraform (`terraform/`)

**Modules** (`terraform/modules/`):
- `networking` — VNet, subnets, NSGs, private DNS zones
- `storage` — Storage account + containers
- `function_app` — `azurerm_function_app_flex_consumption` (FC1/Linux), private endpoint, CORS settings
- `cosmos_db` — Cosmos DB + private endpoint
- `key_vault` — Key Vault + private endpoint
- `monitoring` — Log Analytics + App Insights
- `identity` — App registration, user-assigned managed identity, Entra group
- `bastion` — Bastion + test VM (dev only)
- `static_web_app` — `azurerm_static_web_app`; outputs: `default_host_name`, `api_key` (sensitive)

**Environments** (`terraform/environments/{dev,prod}/`): both include `swa_sku` variable (default `"Standard"`) and output `swa_default_hostname` / `swa_api_key`.

## Frontend Environment Variables

| Variable | Description |
|---|---|
| `VITE_TENANT_ID` | Entra ID tenant GUID |
| `VITE_CLIENT_ID` | App registration client ID |
| `VITE_API_BASE_URL` | `https://func-spn-portal-{env}.azurewebsites.net/api/v1` (or `http://localhost:7071/api/v1`) |
| `VITE_ENABLE_MOCK` | Set to `true` to enable mock mode (no backend, no Azure login) |

## CI/CD (GitLab)

Stages: `validate → test → build → plan → deploy`

Frontend jobs: `lint:frontend`, `build:frontend` (artifact: `frontend/dist/`), `deploy:frontend:dev` (`az staticwebapp deploy`).

GitLab CI variables needed: `VITE_TENANT_ID`, `VITE_CLIENT_ID_DEV`, `SWA_DEPLOY_TOKEN_DEV`.
Get the deploy token: `cd terraform/environments/dev && terraform output -raw swa_api_key`

## Post-Deploy Steps (first deploy)

1. Run `terraform apply` in dev → note `swa_default_hostname`
2. Add `https://<hostname>.azurestaticapps.net` to `redirect_uris` in `terraform.tfvars`
3. Re-run `terraform apply` to update the Entra ID app registration redirect URIs
4. Set GitLab CI variables and push to trigger the frontend deploy pipeline

## Backend API Endpoints

```
GET    /api/v1/spns
POST   /api/v1/spns
GET    /api/v1/spns/{id}
PATCH  /api/v1/spns/{id}
DELETE /api/v1/spns/{id}
GET    /api/v1/spns/{id}/secrets
POST   /api/v1/spns/{id}/secrets
DELETE /api/v1/spns/{id}/secrets/{keyId}
GET    /api/v1/spns/{id}/owners
POST   /api/v1/spns/{id}/owners
DELETE /api/v1/spns/{id}/owners/{ownerId}
GET    /api/v1/health
```
