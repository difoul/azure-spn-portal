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

variable "address_space" {
  description = "CIDR block for the virtual network (e.g. 10.100.0.0/16)."
  type        = string
}

variable "function_subnet_cidr" {
  description = "CIDR block for the Function App VNet-integration subnet."
  type        = string
}

variable "pe_subnet_cidr" {
  description = "CIDR block for the private-endpoints subnet."
  type        = string
}

variable "corporate_cidr_ranges" {
  description = "List of corporate CIDR ranges allowed inbound through the NSG."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
