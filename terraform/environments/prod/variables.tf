variable "environment" {
  description = "Environment name."
  type        = string
  default     = "prod"
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
  default     = 90
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
