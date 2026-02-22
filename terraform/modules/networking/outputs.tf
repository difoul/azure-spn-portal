output "vnet_id" {
  description = "Resource ID of the virtual network."
  value       = azurerm_virtual_network.this.id
}

output "vnet_name" {
  description = "Name of the virtual network."
  value       = azurerm_virtual_network.this.name
}

output "function_subnet_id" {
  description = "Resource ID of the Function App integration subnet."
  value       = azurerm_subnet.function.id
}

output "pe_subnet_id" {
  description = "Resource ID of the private-endpoints subnet."
  value       = azurerm_subnet.private_endpoints.id
}

output "nsg_id" {
  description = "Resource ID of the network security group."
  value       = azurerm_network_security_group.this.id
}

output "private_dns_zone_ids" {
  description = "Map of private DNS zone name to resource ID."
  value = {
    for zone_name, zone in azurerm_private_dns_zone.this : zone_name => zone.id
  }
}
