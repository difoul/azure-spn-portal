output "cosmosdb_account_id" {
  description = "Resource ID of the Cosmos DB account."
  value       = azurerm_cosmosdb_account.this.id
}

output "cosmosdb_account_name" {
  description = "Name of the Cosmos DB account."
  value       = azurerm_cosmosdb_account.this.name
}

output "cosmosdb_endpoint" {
  description = "Endpoint URI of the Cosmos DB account."
  value       = azurerm_cosmosdb_account.this.endpoint
}

output "cosmosdb_database_name" {
  description = "Name of the SQL database."
  value       = azurerm_cosmosdb_sql_database.this.name
}
