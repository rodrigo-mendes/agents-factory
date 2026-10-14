# Module: Vault

Provisions OCI Vault (KMS) with a Master Encryption Key and an optional Object Storage bucket for the API Facade pattern.

## Usage

```hcl
module "vault" {
  source = "./modules/vault"

  compartment_ocid    = var.compartment_ocid
  project_name        = var.project_name
  environment         = var.environment
  key_protection_mode = "SOFTWARE"  # Use "HSM" in production
  create_bucket       = true
  bucket_name         = "api-facade"
  tags                = local.tags
}
```

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `compartment_ocid` | OCID do compartment | `string` | — |
| `project_name` | Nome do projeto | `string` | `"serverless"` |
| `environment` | Ambiente | `string` | `"dev"` |
| `key_protection_mode` | SOFTWARE ou HSM | `string` | `"SOFTWARE"` |
| `create_bucket` | Criar bucket | `bool` | `true` |
| `bucket_name` | Nome base do bucket | `string` | `"api-facade"` |
| `tags` | Freeform tags | `map(string)` | `{}` |

## Outputs

| Name | Description |
|------|-------------|
| `vault_id` | OCID do Vault |
| `vault_crypto_endpoint` | Endpoint de criptografia |
| `vault_management_endpoint` | Endpoint de gerenciamento |
| `key_id` | OCID da Master Encryption Key |
| `bucket_name` | Nome do bucket criado |
## Dependências

- **Compartment** — Deve existir previamente
- Nenhum outro módulo — pode ser provisionado em paralelo com network e IAM

## Notas

- Use `key_protection_mode = "SOFTWARE"` em dev e `"HSM"` em produção
- O bucket é criado com versioning habilitado e auto-tiering para InfrequentAccess
- Acesso público é bloqueado (`ObjectReadWithoutList` removido)
