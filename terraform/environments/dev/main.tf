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
# Resource Provider Registration – required for Flex Consumption VNet integration
# ---------------------------------------------------------------------------

resource "azurerm_resource_provider_registration" "microsoft_app" {
  name = "Microsoft.App"
}

# ---------------------------------------------------------------------------
# Microsoft Azure Legion – grant Reader on VNet for Function App VNet integration
# ---------------------------------------------------------------------------

data "azuread_service_principal" "azure_legion" {
  client_id = "55ebbb62-3b9c-49fd-9b87-9595226dd4ac"
}

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

  environment         = var.environment
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  pe_subnet_id        = module.networking.pe_subnet_id
  private_dns_zone_ids = module.networking.private_dns_zone_ids
  tags                = var.tags
}

# ---------------------------------------------------------------------------
# Monitoring (created early so IDs are available for other modules)
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
# Grant Microsoft Azure Legion Reader on VNet (required for VNet integration)
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "azure_legion_vnet_reader" {
  scope                = module.networking.vnet_id
  role_definition_name = "Reader"
  principal_id         = data.azuread_service_principal.azure_legion.object_id
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
  user_assigned_identity_id        = module.identity.user_assigned_identity_id
  user_assigned_identity_client_id = module.identity.user_assigned_identity_client_id
  private_dns_zone_ids          = module.networking.private_dns_zone_ids
  tags                          = var.tags

  depends_on = [
    azurerm_resource_provider_registration.microsoft_app,
    azurerm_role_assignment.azure_legion_vnet_reader,
  ]
}

# ---------------------------------------------------------------------------
# Additional RBAC – give Function App system identity Cosmos DB access
# ---------------------------------------------------------------------------

resource "azurerm_cosmosdb_sql_role_assignment" "func_cosmos_contributor" {
  resource_group_name = azurerm_resource_group.this.name
  account_name        = module.cosmos_db.cosmosdb_account_name
  role_definition_id  = "${module.cosmos_db.cosmosdb_account_id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = module.identity.user_assigned_identity_principal_id
  scope               = module.cosmos_db.cosmosdb_account_id
}

# Grant the portal service principal Key Vault Secrets Officer for local development.
# In production the managed identity (already Secrets Officer via the key_vault module) is used instead.
resource "azurerm_role_assignment" "sp_kv_secrets_officer" {
  scope                = module.key_vault.key_vault_id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = module.identity.service_principal_object_id
}

# ---------------------------------------------------------------------------
# Bastion + Test VM (dev only)
# ---------------------------------------------------------------------------

module "bastion" {
  source = "../../modules/bastion"
  count  = var.deploy_bastion ? 1 : 0

  environment         = var.environment
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  vnet_id             = module.networking.vnet_id
  vnet_name           = module.networking.vnet_name
  vm_subnet_cidr      = var.vm_subnet_cidr
  admin_password      = var.admin_password
  tags                = var.tags
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

output "allowed_group_id" {
  value = module.identity.allowed_group_id
}

output "bastion_name" {
  value = var.deploy_bastion ? module.bastion[0].bastion_name : null
}

output "test_vm_name" {
  value = var.deploy_bastion ? module.bastion[0].vm_name : null
}

output "test_vm_private_ip" {
  value = var.deploy_bastion ? module.bastion[0].vm_private_ip : null
}
