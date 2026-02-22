# ---------------------------------------------------------------------------
# App Service Plan – Flex Consumption (FC1)
# ---------------------------------------------------------------------------

resource "azurerm_service_plan" "this" {
  name                = "asp-spn-portal-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  sku_name            = "FC1"

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Linux Function App – Flex Consumption
# ---------------------------------------------------------------------------

resource "azurerm_function_app_flex_consumption" "this" {
  name                = "func-spn-portal-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  service_plan_id     = azurerm_service_plan.this.id

  storage_container_type      = "blobContainer"
  storage_container_endpoint  = var.storage_container_endpoint
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = var.storage_access_key

  runtime_name    = "python"
  runtime_version = "3.12"

  maximum_instance_count = 100
  instance_memory_in_mb  = 2048

  virtual_network_subnet_id     = var.function_subnet_id
  public_network_access_enabled = false

  site_config {
      application_insights_connection_string = var.appinsights_connection_string
  }

  identity {
    type         = var.user_assigned_identity_id != null ? "SystemAssigned, UserAssigned" : "SystemAssigned"
    identity_ids = var.user_assigned_identity_id != null ? [var.user_assigned_identity_id] : []
  }

  app_settings = merge(
    {
      "TENANT_ID"                             = var.tenant_id
      "CLIENT_ID"                             = var.client_id
      "ALLOWED_GROUP_ID"                      = var.allowed_group_id
      "COSMOS_ENDPOINT"                       = var.cosmos_endpoint
      "KEYVAULT_URI"                          = var.keyvault_uri
      #"APPLICATIONINSIGHTS_CONNECTION_STRING" = var.appinsights_connection_string
      "AZURE_CLIENT_ID"                       = var.user_assigned_identity_client_id
    },
    var.extra_app_settings,
  )

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Private endpoint for the Function App
# ---------------------------------------------------------------------------

resource "azurerm_private_endpoint" "function_app" {
  name                = "pe-func-spn-portal-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.pe_subnet_id

  private_service_connection {
    name                           = "psc-func-spn-portal-${var.environment}"
    private_connection_resource_id = azurerm_function_app_flex_consumption.this.id
    subresource_names              = ["sites"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.private_dns_zone_ids["privatelink.azurewebsites.net"]]
  }

  tags = var.tags
}
