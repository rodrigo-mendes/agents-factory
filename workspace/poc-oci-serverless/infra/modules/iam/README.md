# Module: IAM

Provisiona Dynamic Groups e Policies para a stack serverless OCI.

## Recursos Criados

- **Dynamic Group (Functions)** — Agrupa todas as Functions do compartment
- **Dynamic Group (API Gateway)** — Agrupa todos os API Gateways do compartment
- **Policy (FaaS Network)** — Permite FaaS service usar VCN e ler repos
- **Policy (API GW → Functions)** — Permite API Gateway invocar Functions
- **Policy (Functions → Services)** — Permite Functions acessar Vault, Object Storage, Logging

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `tenancy_ocid` | OCID da tenancy | `string` | - | yes |
| `compartment_ocid` | OCID do compartment | `string` | - | yes |
| `compartment_name` | Nome do compartment (usado nas policies) | `string` | - | yes |
| `environment` | Nome do ambiente | `string` | - | yes |
| `project_name` | Nome do projeto | `string` | - | yes |
| `tags` | Tags para os recursos | `map(string)` | `{}` | no |

## Uso

```hcl
module "iam" {
  source = "../../modules/iam"

  tenancy_ocid     = var.tenancy_ocid
  compartment_ocid = var.compartment_ocid
  compartment_name = var.compartment_name
  environment      = var.environment
  project_name     = var.project_name
  tags             = local.tags
}
```

## Outputs

| Name | Description |
|------|-------------|
| `dynamic_group_functions_id` | OCID do Dynamic Group de Functions |
| `dynamic_group_functions_name` | Nome do Dynamic Group de Functions |
| `dynamic_group_apigw_id` | OCID do Dynamic Group do API Gateway |
| `dynamic_group_apigw_name` | Nome do Dynamic Group do API Gateway |

## Dependências

- **Tenancy** — Dynamic Groups são criados no nível tenancy
- **Compartment** — Policies referenciam o compartment por nome
- Nenhum outro módulo — pode ser provisionado em paralelo com network
