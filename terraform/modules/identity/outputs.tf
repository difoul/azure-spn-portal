output "user_assigned_identity_id" {
  description = "Resource ID of the user-assigned managed identity."
  value       = azurerm_user_assigned_identity.this.id
}

output "user_assigned_identity_principal_id" {
  description = "Principal ID of the user-assigned managed identity."
  value       = azurerm_user_assigned_identity.this.principal_id
}

output "user_assigned_identity_client_id" {
  description = "Client ID of the user-assigned managed identity."
  value       = azurerm_user_assigned_identity.this.client_id
}

output "application_client_id" {
  description = "Client (application) ID of the Entra ID application registration."
  value       = azuread_application.this.client_id
}

output "application_object_id" {
  description = "Object ID of the Entra ID application registration."
  value       = azuread_application.this.object_id
}

output "service_principal_id" {
  description = "Object ID of the Entra ID service principal."
  value       = azuread_service_principal.this.id
}

output "service_principal_object_id" {
  description = "Object ID of the Entra ID service principal."
  value       = azuread_service_principal.this.object_id
}

output "allowed_group_id" {
  description = "Object ID of the Entra ID group allowed to use the portal."
  value       = azuread_group.portal_users.object_id
}
