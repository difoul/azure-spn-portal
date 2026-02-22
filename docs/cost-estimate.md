# Azure SPN Portal — Idle Infrastructure Cost Estimate

Estimated monthly cost when deployed but receiving no traffic (single environment).

## Per-Environment Breakdown

| Resource | Qty | Unit Price | Monthly Cost |
|---|---|---|---|
| **Private Endpoints** | 7 | $7.30/mo each ($0.01/hr) | **$51.10** |
| Storage (blob, table, queue, file) | 4 | | |
| Function App | 1 | | |
| Cosmos DB | 1 | | |
| Key Vault | 1 | | |
| **Private DNS Zones** | 7 | $0.50/mo each | **$3.50** |
| **Function App (Flex Consumption)** | 1 | Pay per execution | **$0** |
| **Cosmos DB (Serverless)** | 1 | Pay per RU | **$0** |
| **Key Vault (Standard)** | 1 | Pay per operation | **$0** |
| **Storage Account (LRS)** | 1 | ~$0.018/GB | **~$0** |
| **Log Analytics + App Insights** | 1 | First 5GB/mo free | **~$0** |
| VNet, Subnets, NSGs | — | Free | **$0** |
| Managed Identity, App Registration | — | Free | **$0** |
| | | | |
| **Total (idle)** | | | **~$55/month** |

## Dev Environment with Bastion + Test VM

| Resource | Monthly Cost |
|---|---|
| Base idle cost | ~$55 |
| Bastion (Developer SKU) | $0 |
| Test VM (Standard_B1s) | ~$8 |
| **Total** | **~$63/month** |

## Both Environments (dev + prod)

| Scenario | Monthly Cost |
|---|---|
| Dev (no Bastion) + Prod | ~$110 |
| Dev (with Bastion + VM) + Prod | ~$118 |

## Notes

- Private endpoints account for ~93% of the idle cost.
- All compute and data services (Functions, Cosmos DB, Key Vault) are serverless/pay-per-use with zero idle cost.
- Log Analytics includes 5 GB/month free ingestion and 31 days free retention.
- Prices based on Sweden Central region, pay-as-you-go, as of 2025. Actual costs may vary.
