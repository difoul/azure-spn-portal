environment          = "dev"
location             = "swedencentral"
address_space        = "10.100.0.0/16"
function_subnet_cidr = "10.100.1.0/24"
pe_subnet_cidr       = "10.100.2.0/24"
corporate_cidr_ranges = [
  "10.0.0.0/8",
]
# allowed_group_id   = "00000000-0000-0000-0000-000000000000"
log_retention_days = 30

deploy_bastion = true
vm_subnet_cidr = "10.100.3.0/24"
# admin_password = "SET_VIA_ENV_VAR_OR_PROMPT"  # Do not commit passwords

tags = {
  Environment = "dev"
  Project     = "spn-portal"
  ManagedBy   = "terraform"
}
