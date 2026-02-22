data "azurerm_client_config" "current" {}

data "azuread_service_principal" "msgraph" {
  client_id = "00000003-0000-0000-c000-000000000000" # Microsoft Graph
}

locals {
  # Stable UUID for the access_as_user OAuth2 permission scope.
  # Must be unique within the app registration; can be any valid UUID.
  access_as_user_scope_id = "c7a6e6d8-4b3c-4e9a-a1f2-8d3b5c9e1a2f"
}

# ---------------------------------------------------------------------------
# User-Assigned Managed Identity
# ---------------------------------------------------------------------------

resource "azurerm_user_assigned_identity" "this" {
  name                = "id-spn-portal-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Entra ID Application Registration
# ---------------------------------------------------------------------------

resource "azuread_application" "this" {
  display_name = "spn-portal-${var.environment}"

  owners = [data.azurerm_client_config.current.object_id]

  api {
    requested_access_token_version = 2

    oauth2_permission_scope {
      admin_consent_description  = "Access the SPN portal on behalf of the signed-in user."
      admin_consent_display_name = "access_as_user"
      enabled                    = true
      id                         = local.access_as_user_scope_id
      type                       = "User"
      user_consent_description   = "Access the SPN portal on your behalf."
      user_consent_display_name  = "access_as_user"
      value                      = "access_as_user"
    }
  }

  required_resource_access {
    resource_app_id = "00000003-0000-0000-c000-000000000000" # Microsoft Graph

    resource_access {
      id   = "1bfefb4e-e0b5-418b-a88f-73c46d2cc8e9" # Application.ReadWrite.All (Application)
      type = "Role"
    }

    resource_access {
      id   = "7ab1d382-f21e-4acd-a863-ba3e13f7da61" # Directory.Read.All (Application)
      type = "Role"
    }

    resource_access {
      id   = "98830695-27a2-44f7-8c18-0c3ebc9698f6" # GroupMember.Read.All (Application)
      type = "Role"
    }
  }

  web {
    redirect_uris = var.redirect_uris
  }

  lifecycle {
    ignore_changes = [identifier_uris]
  }
}

# ---------------------------------------------------------------------------
# Service Principal for the Entra ID Application
# ---------------------------------------------------------------------------

resource "azuread_service_principal" "this" {
  client_id = azuread_application.this.client_id
  owners    = [data.azurerm_client_config.current.object_id]
}

# ---------------------------------------------------------------------------
# Admin consent for Graph API application permissions
# ---------------------------------------------------------------------------

# App registration service principal — used locally via EnvironmentCredential
resource "azuread_app_role_assignment" "application_readwrite_all" {
  app_role_id         = "1bfefb4e-e0b5-418b-a88f-73c46d2cc8e9" # Application.ReadWrite.All
  principal_object_id = azuread_service_principal.this.object_id
  resource_object_id  = data.azuread_service_principal.msgraph.object_id
}

resource "azuread_app_role_assignment" "directory_read_all" {
  app_role_id         = "7ab1d382-f21e-4acd-a863-ba3e13f7da61" # Directory.Read.All
  principal_object_id = azuread_service_principal.this.object_id
  resource_object_id  = data.azuread_service_principal.msgraph.object_id
}

resource "azuread_app_role_assignment" "groupmember_read_all" {
  app_role_id         = "98830695-27a2-44f7-8c18-0c3ebc9698f6" # GroupMember.Read.All
  principal_object_id = azuread_service_principal.this.object_id
  resource_object_id  = data.azuread_service_principal.msgraph.object_id
}

# User-assigned managed identity — used in production via ManagedIdentityCredential
resource "azuread_app_role_assignment" "mi_application_readwrite_all" {
  app_role_id         = "1bfefb4e-e0b5-418b-a88f-73c46d2cc8e9" # Application.ReadWrite.All
  principal_object_id = azurerm_user_assigned_identity.this.principal_id
  resource_object_id  = data.azuread_service_principal.msgraph.object_id
}

resource "azuread_app_role_assignment" "mi_directory_read_all" {
  app_role_id         = "7ab1d382-f21e-4acd-a863-ba3e13f7da61" # Directory.Read.All
  principal_object_id = azurerm_user_assigned_identity.this.principal_id
  resource_object_id  = data.azuread_service_principal.msgraph.object_id
}

resource "azuread_app_role_assignment" "mi_groupmember_read_all" {
  app_role_id         = "98830695-27a2-44f7-8c18-0c3ebc9698f6" # GroupMember.Read.All
  principal_object_id = azurerm_user_assigned_identity.this.principal_id
  resource_object_id  = data.azuread_service_principal.msgraph.object_id
}

# ---------------------------------------------------------------------------
# Application ID URI  (api://<client_id>) — required for token acquisition
# Must be a separate resource; self-reference inside azuread_application is
# not supported by Terraform.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pre-authorize the Azure CLI so users can get tokens via
# `az account get-access-token --resource api://<client_id>` without a consent prompt.
resource "azuread_application_pre_authorized" "azure_cli" {
  application_id       = azuread_application.this.id
  authorized_client_id = "04b07795-8ddb-461a-bbee-02f9e1bf7b46" # Microsoft Azure CLI
  permission_ids       = [local.access_as_user_scope_id]
}

resource "azuread_application_identifier_uri" "api" {
  application_id = azuread_application.this.id
  identifier_uri = "api://${azuread_application.this.client_id}"
}

# ---------------------------------------------------------------------------
# Allowed users group
# ---------------------------------------------------------------------------

resource "azuread_group" "portal_users" {
  display_name     = "spn-portal-users-${var.environment}"
  security_enabled = true
  owners           = [data.azurerm_client_config.current.object_id]
}

resource "azuread_group_member" "current_user" {
  group_object_id  = azuread_group.portal_users.object_id
  member_object_id = data.azurerm_client_config.current.object_id
}
