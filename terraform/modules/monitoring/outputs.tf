output "log_analytics_workspace_id" {
  description = "Resource ID of the Log Analytics workspace."
  value       = azurerm_log_analytics_workspace.this.id
}

output "log_analytics_workspace_name" {
  description = "Name of the Log Analytics workspace."
  value       = azurerm_log_analytics_workspace.this.name
}

output "appinsights_id" {
  description = "Resource ID of the Application Insights instance."
  value       = azurerm_application_insights.this.id
}

output "appinsights_name" {
  description = "Name of the Application Insights instance."
  value       = azurerm_application_insights.this.name
}

output "appinsights_connection_string" {
  description = "Connection string for Application Insights."
  value       = azurerm_application_insights.this.connection_string
  sensitive   = true
}

output "appinsights_instrumentation_key" {
  description = "Instrumentation key for Application Insights."
  value       = azurerm_application_insights.this.instrumentation_key
  sensitive   = true
}
