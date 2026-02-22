variable "environment" {
  description = "Environment name (e.g. dev, prod)."
  type        = string
}

variable "location" {
  description = "Azure region for all resources."
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group."
  type        = string
}

variable "function_subnet_id" {
  description = "Resource ID of the Function App VNet-integration subnet."
  type        = string
}

variable "pe_subnet_id" {
  description = "Resource ID of the private-endpoints subnet."
  type        = string
}

variable "storage_container_endpoint" {
  description = "Blob endpoint URL for the Function App deployment container (e.g. https://<account>.blob.core.windows.net/<container>)."
  type        = string
}

variable "storage_access_key" {
  description = "Primary access key for the storage account."
  type        = string
  sensitive   = true
}

variable "tenant_id" {
  description = "Entra ID tenant ID."
  type        = string
}

variable "client_id" {
  description = "Client ID of the Entra ID application registration for the portal."
  type        = string
}

variable "allowed_group_id" {
  description = "Object ID of the Entra ID group allowed to use the portal."
  type        = string
}

variable "cosmos_endpoint" {
  description = "Cosmos DB account endpoint URI."
  type        = string
}

variable "keyvault_uri" {
  description = "Key Vault URI."
  type        = string
}

variable "appinsights_connection_string" {
  description = "Application Insights connection string."
  type        = string
  sensitive   = true
}

variable "user_assigned_identity_id" {
  description = "Resource ID of a user-assigned managed identity to attach. Set to null to use system-assigned only."
  type        = string
  default     = null
}

variable "user_assigned_identity_client_id" {
  description = "Client ID of the user-assigned managed identity. Set to force DefaultAzureCredential to use it over the system-assigned identity."
  type        = string
  default     = null
}

variable "extra_app_settings" {
  description = "Additional app settings to merge into the Function App configuration."
  type        = map(string)
  default     = {}
}

variable "private_dns_zone_ids" {
  description = "Map of private DNS zone name to resource ID (must include privatelink.azurewebsites.net)."
  type        = map(string)
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
