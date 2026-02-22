output "default_host_name" {
  description = "The default hostname of the Static Web App."
  value       = azurerm_static_web_app.this.default_host_name
}

output "api_key" {
  description = "The deployment API key for the Static Web App (used in CI/CD)."
  value       = azurerm_static_web_app.this.api_key
  sensitive   = true
}

output "id" {
  description = "The resource ID of the Static Web App."
  value       = azurerm_static_web_app.this.id
}
