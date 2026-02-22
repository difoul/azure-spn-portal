variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region for all resources."
  type        = string
}

variable "address_space" {
  description = "CIDR block for the virtual network."
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
  description = "List of corporate CIDR ranges allowed inbound."
  type        = list(string)
  default     = []
}

variable "redirect_uris" {
  description = "Redirect URIs for the Entra ID app registration."
  type        = list(string)
  default     = []
}

variable "log_retention_days" {
  description = "Number of days to retain logs in Log Analytics."
  type        = number
  default     = 30
}

variable "vm_subnet_cidr" {
  description = "CIDR block for the test VM subnet."
  type        = string
  default     = ""
}

variable "admin_password" {
  description = "Admin password for the test VM."
  type        = string
  default     = ""
  sensitive   = true
}

variable "deploy_bastion" {
  description = "Whether to deploy the Bastion + test VM."
  type        = bool
  default     = false
}

variable "swa_sku" {
  description = "SKU for the Static Web App (Free or Standard)."
  type        = string
  default     = "Standard"
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
