# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Azure SPN Self-Service Portal — a self-service application allowing corporate Azure users to create and manage Service Principals (SPNs) independently, without requiring admin intervention. Access is restricted to users in a specific Entra ID group, accessible only from the corporate network.

## Tech Stack

- **Backend:** Python — Azure Functions v2 (decorator-based programming model)
- **Infrastructure:** Terraform (IaC)
- **Cloud:** Azure, private networking (no public internet exposure)
- **Auth:** Entra ID, single-tenant, application-level permissions (client credentials / managed identity with admin-consented Graph API)
- **Database:** Azure Cosmos DB
- **Secret storage:** Azure Key Vault (secrets also shown once to user at creation time)
- **Audit:** Azure Log Analytics
- **CI/CD:** GitLab CI/CD
- **Frontend:** Deferred — will be built later using a modern framework (API-first approach for now)

## Architecture Decisions

- **Serverless:** Azure Functions with VNet integration for private network access only (corporate users on VPN/corporate network)
- **No API Management:** Direct Function App access via private endpoint — cost-efficient approach
- **Application-level Graph API permissions:** The app operates with its own identity, not delegated user permissions. Admin consent required for Graph API scopes
- **Role-based access:** Only users in a designated Entra ID security group can use the portal
- **Secret delivery:** Secrets are shown once in the response AND stored in Azure Key Vault for later retrieval by the owner

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
# Lint and format
ruff check function_app/
ruff format --check function_app/

# Type checking
pyright function_app/

# Run tests
pytest function_app/tests/
pytest function_app/tests/ --cov=function_app    # with coverage
pytest function_app/tests/test_auth.py            # single test file
pytest function_app/tests/test_auth.py::test_name # single test

# Install dependencies (for local dev)
pip install -r function_app/requirements.txt

# Run locally (requires Azure Functions Core Tools)
cd function_app && func start

# Terraform (from an environment directory)
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

## Code Architecture

- **`function_app/function_app.py`** — entry point, registers all blueprints
- **`function_app/blueprints/`** — HTTP route groups by domain (spn, secret, owner, health)
- **`function_app/core/`** — shared infrastructure: auth (JWT validation against Entra ID JWKS), decorators (`@require_auth`, `@require_owner`, `@handle_errors`), exceptions, config
- **`function_app/services/`** — business logic layer: `graph_service.py` (Microsoft Graph API via httpx async), `cosmos_service.py`, `keyvault_service.py`, `audit_service.py`
- **`function_app/models/`** — Pydantic request/response models
- **`terraform/modules/`** — 7 Terraform modules (networking, storage, function_app, cosmos_db, key_vault, monitoring, identity)
- **`terraform/environments/`** — per-environment configs (dev, prod), region: Sweden Central

Microsoft Graph is the source of truth for SPN data. Cosmos DB stores only portal metadata and audit events.
