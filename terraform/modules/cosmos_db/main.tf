# ---------------------------------------------------------------------------
# Cosmos DB Account – Serverless, SQL API
# ---------------------------------------------------------------------------

resource "azurerm_cosmosdb_account" "this" {
  name                          = "cosmos-spn-portal-${var.environment}"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  offer_type                    = "Standard"
  kind                          = "GlobalDocumentDB"
  public_network_access_enabled = false

  capabilities {
    name = "EnableServerless"
  }

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  tags = var.tags
}

# ---------------------------------------------------------------------------
# SQL Database
# ---------------------------------------------------------------------------

resource "azurerm_cosmosdb_sql_database" "this" {
  name                = "spn-portal"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.this.name
}

# ---------------------------------------------------------------------------
# Containers
# ---------------------------------------------------------------------------

resource "azurerm_cosmosdb_sql_container" "audit_events" {
  name                = "audit-events"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.this.name
  database_name       = azurerm_cosmosdb_sql_database.this.name
  partition_key_paths = ["/spnId"]
}

resource "azurerm_cosmosdb_sql_container" "spn_metadata" {
  name                = "spn-metadata"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.this.name
  database_name       = azurerm_cosmosdb_sql_database.this.name
  partition_key_paths = ["/spnId"]
}

# ---------------------------------------------------------------------------
# Private endpoint
# ---------------------------------------------------------------------------

resource "azurerm_private_endpoint" "cosmos" {
  name                = "pe-cosmos-spn-portal-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.pe_subnet_id

  private_service_connection {
    name                           = "psc-cosmos-spn-portal-${var.environment}"
    private_connection_resource_id = azurerm_cosmosdb_account.this.id
    subresource_names              = ["Sql"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.private_dns_zone_ids["privatelink.documents.azure.com"]]
  }

  tags = var.tags
}
