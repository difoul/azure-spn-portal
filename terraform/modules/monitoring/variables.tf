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

variable "log_retention_days" {
  description = "Number of days to retain logs in the Log Analytics workspace."
  type        = number
  default     = 30
}

variable "enable_function_app_diagnostics" {
  description = "Whether to create diagnostic settings for the Function App."
  type        = bool
  default     = true
}

variable "function_app_id" {
  description = "Resource ID of the Function App for diagnostic settings."
  type        = string
  default     = null
}

variable "enable_cosmosdb_diagnostics" {
  description = "Whether to create diagnostic settings for Cosmos DB."
  type        = bool
  default     = true
}

variable "cosmosdb_account_id" {
  description = "Resource ID of the Cosmos DB account for diagnostic settings."
  type        = string
  default     = null
}

variable "enable_key_vault_diagnostics" {
  description = "Whether to create diagnostic settings for Key Vault."
  type        = bool
  default     = true
}

variable "key_vault_id" {
  description = "Resource ID of the Key Vault for diagnostic settings."
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
