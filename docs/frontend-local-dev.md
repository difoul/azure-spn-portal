# Frontend — Local Development Guide

## Prerequisites

- Node.js 22+
- npm 10+

---

## 1. Install dependencies

```bash
cd frontend
npm install
npx msw init public/   # generates public/mockServiceWorker.js (one-time, gitignored)
```

---

## 2. Environment variables

Copy the example file and fill in your values:

```bash
cp frontend/.env.example frontend/.env.local
```

`.env.local` values:

| Variable | Description |
|---|---|
| `VITE_TENANT_ID` | Entra ID tenant GUID |
| `VITE_CLIENT_ID` | App registration client ID |
| `VITE_API_BASE_URL` | API base URL (see options below) |

---

## 3. Run modes

### Option A — Mock mode (no backend, no Azure login required)

Uses [MSW (Mock Service Worker)](https://mswjs.io/) to intercept API calls and return in-memory data. The MSAL auth guard is bypassed entirely — no Entra ID app registration needed.

```bash
cd frontend && npm run dev:mock
```

Open **http://localhost:5173**

The mock data includes:
- 3 pre-populated SPNs (one at max secrets, one with an expiring secret, one with no secrets)
- Working mutations — create/delete SPN, add/delete secret (with reveal modal), add/remove owner
- Simulated network delay (200–600ms) so loading states are visible

### Option B — Real backend, local Function App

Run the Function App on `localhost:7071`, then point the frontend at it.

Set in `.env.local`:
```
VITE_TENANT_ID=<tenant-id>
VITE_CLIENT_ID=<client-id>
VITE_API_BASE_URL=http://localhost:7071/api/v1
```

Start the Function App (requires [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)):

```bash
# function_app/local.settings.json must exist — see docs/local-auth-testing.md
cd function_app && func start
```

Then start the frontend:

```bash
cd frontend && npm run dev
```

MSAL will redirect to `login.microsoftonline.com` and back to `http://localhost:5173`. You must be a member of the allowed Entra ID group.

### Option C — Real backend, deployed dev Function App

Requires corporate VPN (Function App is private-endpoint-only).

Set in `.env.local`:
```
VITE_TENANT_ID=<tenant-id>
VITE_CLIENT_ID=<client-id>
VITE_API_BASE_URL=https://func-spn-portal-dev.azurewebsites.net/api/v1
```

```bash
cd frontend && npm run dev
```

---

## 4. Other commands

```bash
npm run typecheck   # TypeScript type check (tsc --noEmit)
npm run lint        # ESLint
npm run build       # Production build → frontend/dist/
```

---

## 5. How mock mode works

| Concern | Mock mode | Real mode |
|---|---|---|
| Auth guard | Bypassed in `__root.tsx` | MSAL `AuthenticatedTemplate` |
| Token acquisition | Returns `'mock-token'` immediately | `acquireTokenSilent` → redirect fallback |
| API calls | MSW service worker intercepts `fetch` | Real Function App via private DNS |

The `VITE_ENABLE_MOCK=true` flag is compiled at build time. A production `vite build` (without the flag) tree-shakes all mock imports — MSW is never included in the production bundle.

Mock state is in-memory and resets on page refresh.
