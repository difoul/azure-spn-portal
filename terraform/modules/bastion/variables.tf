variable "environment" {
  description = "Environment name (e.g. dev, prod)."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group."
  type        = string
}

variable "vnet_id" {
  description = "Resource ID of the virtual network."
  type        = string
}

variable "vnet_name" {
  description = "Name of the virtual network."
  type        = string
}

variable "vm_subnet_cidr" {
  description = "CIDR block for the VM subnet."
  type        = string
}

variable "admin_username" {
  description = "Admin username for the test VM."
  type        = string
  default     = "azureuser"
}

variable "admin_password" {
  description = "Admin password for the test VM."
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
