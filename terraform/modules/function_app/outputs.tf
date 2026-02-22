output "function_app_id" {
  description = "Resource ID of the Function App."
  value       = azurerm_function_app_flex_consumption.this.id
}

output "function_app_name" {
  description = "Name of the Function App."
  value       = azurerm_function_app_flex_consumption.this.name
}

output "function_app_default_hostname" {
  description = "Default hostname of the Function App."
  value       = azurerm_function_app_flex_consumption.this.default_hostname
}

output "function_app_identity_principal_id" {
  description = "Principal ID of the system-assigned managed identity."
  value       = azurerm_function_app_flex_consumption.this.identity[0].principal_id
}

output "function_app_identity_tenant_id" {
  description = "Tenant ID of the system-assigned managed identity."
  value       = azurerm_function_app_flex_consumption.this.identity[0].tenant_id
}
