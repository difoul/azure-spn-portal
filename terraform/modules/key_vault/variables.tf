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

variable "pe_subnet_id" {
  description = "Resource ID of the private-endpoints subnet."
  type        = string
}

variable "secrets_officer_principal_id" {
  description = "Principal ID that will receive the Key Vault Secrets Officer role."
  type        = string
}

variable "private_dns_zone_ids" {
  description = "Map of private DNS zone name to resource ID (must include privatelink.vaultcore.azure.net)."
  type        = map(string)
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
