# ---------------------------------------------------------------------------
# Log Analytics Workspace
# ---------------------------------------------------------------------------

resource "azurerm_log_analytics_workspace" "this" {
  name                = "law-spn-portal-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Application Insights
# ---------------------------------------------------------------------------

resource "azurerm_application_insights" "this" {
  name                = "ai-spn-portal-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.this.id
  application_type    = "web"

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Diagnostic Settings – Function App
# ---------------------------------------------------------------------------

resource "azurerm_monitor_diagnostic_setting" "function_app" {
  count = var.enable_function_app_diagnostics ? 1 : 0

  name                       = "diag-func-spn-portal-${var.environment}"
  target_resource_id         = var.function_app_id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  enabled_log {
    category = "FunctionAppLogs"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}

# ---------------------------------------------------------------------------
# Diagnostic Settings – Cosmos DB
# ---------------------------------------------------------------------------

resource "azurerm_monitor_diagnostic_setting" "cosmos_db" {
  count = var.enable_cosmosdb_diagnostics ? 1 : 0

  name                       = "diag-cosmos-spn-portal-${var.environment}"
  target_resource_id         = var.cosmosdb_account_id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  enabled_log {
    category = "DataPlaneRequests"
  }

  enabled_log {
    category = "QueryRuntimeStatistics"
  }

  enabled_log {
    category = "PartitionKeyStatistics"
  }

  enabled_metric {
    category = "Requests"
  }

  enabled_metric {
    category = "SLI"
  }
}

# ---------------------------------------------------------------------------
# Diagnostic Settings – Key Vault
# ---------------------------------------------------------------------------

resource "azurerm_monitor_diagnostic_setting" "key_vault" {
  count = var.enable_key_vault_diagnostics ? 1 : 0

  name                       = "diag-kv-spn-portal-${var.environment}"
  target_resource_id         = var.key_vault_id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  enabled_log {
    category = "AuditEvent"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}
