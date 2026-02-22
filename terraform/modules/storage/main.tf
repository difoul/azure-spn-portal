resource "azurerm_storage_account" "this" {
  name                          = "stspnportal${var.environment}"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  account_tier                  = "Standard"
  account_replication_type      = "LRS"
  public_network_access_enabled = false
  min_tls_version               = "TLS1_2"

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Blob container for Function App Flex Consumption deployment
# ---------------------------------------------------------------------------

resource "azurerm_storage_container" "function_deploy" {
  name                  = "function-deploy"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}

# ---------------------------------------------------------------------------
# Private endpoints – one per sub-resource
# ---------------------------------------------------------------------------

locals {
  storage_subresources = toset(["blob", "table", "queue", "file"])
}

resource "azurerm_private_endpoint" "storage" {
  for_each            = local.storage_subresources
  name                = "pe-stspnportal-${each.key}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.pe_subnet_id

  private_service_connection {
    name                           = "psc-stspnportal-${each.key}-${var.environment}"
    private_connection_resource_id = azurerm_storage_account.this.id
    subresource_names              = [each.key]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.private_dns_zone_ids["privatelink.${each.key}.core.windows.net"]]
  }

  tags = var.tags
}
