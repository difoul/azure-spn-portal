output "bastion_id" {
  description = "Resource ID of the Bastion host."
  value       = azurerm_bastion_host.this.id
}

output "bastion_name" {
  description = "Name of the Bastion host."
  value       = azurerm_bastion_host.this.name
}

output "vm_id" {
  description = "Resource ID of the test VM."
  value       = azurerm_linux_virtual_machine.test.id
}

output "vm_name" {
  description = "Name of the test VM."
  value       = azurerm_linux_virtual_machine.test.name
}

output "vm_private_ip" {
  description = "Private IP address of the test VM."
  value       = azurerm_network_interface.vm.private_ip_address
}
