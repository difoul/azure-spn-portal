environment          = "prod"
location             = "swedencentral"
address_space        = "10.101.0.0/16"
function_subnet_cidr = "10.101.1.0/24"
pe_subnet_cidr       = "10.101.2.0/24"
corporate_cidr_ranges = [
  "10.0.0.0/8",
]
allowed_group_id   = "00000000-0000-0000-0000-000000000000"
log_retention_days = 90

tags = {
  Environment = "prod"
  Project     = "spn-portal"
  ManagedBy   = "terraform"
}
