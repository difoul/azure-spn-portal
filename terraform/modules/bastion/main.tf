# ---------------------------------------------------------------------------
# VM Subnet
# ---------------------------------------------------------------------------

resource "azurerm_subnet" "vm" {
  name                 = "snet-vm-${var.environment}"
  resource_group_name  = var.resource_group_name
  virtual_network_name = var.vnet_name
  address_prefixes     = [var.vm_subnet_cidr]
}

# ---------------------------------------------------------------------------
# Azure Bastion – Developer SKU (free tier)
# ---------------------------------------------------------------------------

resource "azurerm_bastion_host" "this" {
  name                = "bas-spn-portal-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "Developer"
  virtual_network_id  = var.vnet_id

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Test Linux VM
# ---------------------------------------------------------------------------

resource "azurerm_network_interface" "vm" {
  name                = "nic-vm-test-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.vm.id
    private_ip_address_allocation = "Dynamic"
  }

  tags = var.tags
}

resource "azurerm_linux_virtual_machine" "test" {
  name                            = "vm-test-${var.environment}"
  location                        = var.location
  resource_group_name             = var.resource_group_name
  size                            = "Standard_B1s"
  admin_username                  = var.admin_username
  admin_password                  = var.admin_password
  disable_password_authentication = false

  network_interface_ids = [
    azurerm_network_interface.vm.id,
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }

  tags = var.tags
}
