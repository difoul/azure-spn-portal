terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

provider "azuread" {}

data "azurerm_client_config" "current" {}

# ---------------------------------------------------------------------------
# Resource Group
# ---------------------------------------------------------------------------

resource "azurerm_resource_group" "this" {
  name     = "rg-spn-portal-${var.environment}"
  location = var.location
  tags     = var.tags
}

# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

module "identity" {
  source = "../../modules/identity"

  environment         = var.environment
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  redirect_uris       = var.redirect_uris
  tags                = var.tags
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

module "networking" {
  source = "../../modules/networking"

  environment           = var.environment
  location              = var.location
  resource_group_name   = azurerm_resource_group.this.name
  address_space         = var.address_space
  function_subnet_cidr  = var.function_subnet_cidr
  pe_subnet_cidr        = var.pe_subnet_cidr
  corporate_cidr_ranges = var.corporate_cidr_ranges
  tags                  = var.tags
}

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

module "storage" {
  source = "../../modules/storage"

  environment          = var.environment
  location             = var.location
  resource_group_name  = azurerm_resource_group.this.name
  pe_subnet_id         = module.networking.pe_subnet_id
  private_dns_zone_ids = module.networking.private_dns_zone_ids
  tags                 = var.tags
}

# ---------------------------------------------------------------------------
# Monitoring
# ---------------------------------------------------------------------------

module "monitoring" {
  source = "../../modules/monitoring"

  environment                     = var.environment
  location                        = var.location
  resource_group_name             = azurerm_resource_group.this.name
  log_retention_days              = var.log_retention_days
  enable_function_app_diagnostics = true
  function_app_id                 = module.function_app.function_app_id
  enable_cosmosdb_diagnostics     = true
  cosmosdb_account_id             = module.cosmos_db.cosmosdb_account_id
  enable_key_vault_diagnostics    = true
  key_vault_id                    = module.key_vault.key_vault_id
  tags                            = var.tags
}

# ---------------------------------------------------------------------------
# Cosmos DB
# ---------------------------------------------------------------------------

module "cosmos_db" {
  source = "../../modules/cosmos_db"

  environment          = var.environment
  location             = var.location
  resource_group_name  = azurerm_resource_group.this.name
  pe_subnet_id         = module.networking.pe_subnet_id
  private_dns_zone_ids = module.networking.private_dns_zone_ids
  tags                 = var.tags
}

# ---------------------------------------------------------------------------
# Key Vault
# ---------------------------------------------------------------------------

module "key_vault" {
  source = "../../modules/key_vault"

  environment                  = var.environment
  location                     = var.location
  resource_group_name          = azurerm_resource_group.this.name
  pe_subnet_id                 = module.networking.pe_subnet_id
  secrets_officer_principal_id = module.identity.user_assigned_identity_principal_id
  private_dns_zone_ids         = module.networking.private_dns_zone_ids
  tags                         = var.tags
}

# ---------------------------------------------------------------------------
# Function App
# ---------------------------------------------------------------------------

module "function_app" {
  source = "../../modules/function_app"

  environment                   = var.environment
  location                      = var.location
  resource_group_name           = azurerm_resource_group.this.name
  function_subnet_id            = module.networking.function_subnet_id
  pe_subnet_id                  = module.networking.pe_subnet_id
  storage_container_endpoint    = module.storage.function_deploy_container_endpoint
  storage_access_key            = module.storage.primary_access_key
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  client_id                     = module.identity.application_client_id
  allowed_group_id              = module.identity.allowed_group_id
  cosmos_endpoint               = module.cosmos_db.cosmosdb_endpoint
  keyvault_uri                  = module.key_vault.key_vault_uri
  appinsights_connection_string = module.monitoring.appinsights_connection_string
  user_assigned_identity_id     = module.identity.user_assigned_identity_id
  private_dns_zone_ids          = module.networking.private_dns_zone_ids
  tags                          = var.tags
}

# ---------------------------------------------------------------------------
# Additional RBAC – give Function App system identity Cosmos DB access
# ---------------------------------------------------------------------------

resource "azurerm_cosmosdb_sql_role_assignment" "func_cosmos_contributor" {
  resource_group_name = azurerm_resource_group.this.name
  account_name        = module.cosmos_db.cosmosdb_account_name
  role_definition_id  = "${module.cosmos_db.cosmosdb_account_id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = module.function_app.function_app_identity_principal_id
  scope               = module.cosmos_db.cosmosdb_account_id
}

resource "azurerm_role_assignment" "func_kv_secrets_user" {
  scope                = module.key_vault.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = module.function_app.function_app_identity_principal_id
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "function_app_name" {
  value = module.function_app.function_app_name
}

output "function_app_default_hostname" {
  value = module.function_app.function_app_default_hostname
}

output "cosmos_endpoint" {
  value = module.cosmos_db.cosmosdb_endpoint
}

output "key_vault_uri" {
  value = module.key_vault.key_vault_uri
}

output "appinsights_connection_string" {
  value     = module.monitoring.appinsights_connection_string
  sensitive = true
}

output "application_client_id" {
  value = module.identity.application_client_id
}

output "managed_identity_principal_id" {
  value = module.identity.user_assigned_identity_principal_id
}
