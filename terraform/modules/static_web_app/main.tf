resource "azurerm_static_web_app" "this" {
  name                = "swa-spn-portal-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku_tier            = var.sku_name
  sku_size            = var.sku_name

  tags = var.tags
}
