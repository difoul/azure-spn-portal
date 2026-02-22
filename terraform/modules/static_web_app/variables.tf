variable "environment" {
  description = "Environment name (e.g. dev, prod)."
  type        = string
}

variable "location" {
  description = "Azure region for the Static Web App."
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group."
  type        = string
}

variable "sku_name" {
  description = "SKU for the Static Web App (Free or Standard)."
  type        = string
  default     = "Standard"

  validation {
    condition     = contains(["Free", "Standard"], var.sku_name)
    error_message = "sku_name must be 'Free' or 'Standard'."
  }
}

variable "tags" {
  description = "Tags to apply to the Static Web App."
  type        = map(string)
  default     = {}
}
