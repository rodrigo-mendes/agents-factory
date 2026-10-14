# Module: Network

Provisiona a infraestrutura de rede para a stack serverless OCI.

## Recursos Criados

- **VCN** — Virtual Cloud Network com DNS label
- **Internet Gateway** — Acesso público para API Gateway
- **NAT Gateway** (opcional) — Acesso internet para Functions (APIs externas)
- **Service Gateway** — Acesso a serviços OCI sem tráfego pela internet
- **Route Tables** — Rotas públicas (IGW) e privadas (NAT/SGW)
- **Security Lists** — Regras de ingress/egress por subnet
- **Subnets** — Pública (API Gateway) e privada (Functions)
- **NSGs** (opcional) — Micro-segmentação API Gateway ↔ Functions

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `compartment_ocid` | OCID do compartment | `string` | - | yes |
| `vcn_cidr_block` | CIDR block para a VCN | `string` | - | yes |
| `subnet_public_cidr` | CIDR block para a subnet pública | `string` | - | yes |
| `subnet_private_cidr` | CIDR block para a subnet privada | `string` | - | yes |
| `create_nat_gateway` | Criar NAT Gateway | `bool` | `true` | no |
| `use_nsg` | Criar Network Security Groups | `bool` | `true` | no |
| `environment` | Nome do ambiente | `string` | - | yes |
| `project_name` | Nome do projeto | `string` | - | yes |
| `tags` | Tags para os recursos | `map(string)` | `{}` | no |

## Uso

```hcl
module "network" {
  source = "../../modules/network"

  compartment_ocid   = var.compartment_ocid
  vcn_cidr_block     = "10.0.0.0/16"
  subnet_public_cidr = "10.0.1.0/24"
  subnet_private_cidr = "10.0.2.0/24"
  create_nat_gateway = true
  use_nsg            = true
  environment        = var.environment
  project_name       = var.project_name
  tags               = local.tags
}
```

## Outputs

| Name | Description |
|------|-------------|
| `vcn_id` | OCID da VCN |
| `subnet_public_id` | OCID da subnet pública |
| `subnet_private_id` | OCID da subnet privada |
| `nsg_apigw_id` | OCID do NSG do API Gateway (null se desabilitado) |
| `nsg_functions_id` | OCID do NSG de Functions (null se desabilitado) |

## Dependências

- **Compartment** — Deve existir previamente (módulos não criam compartments)
- Nenhum outro módulo — é a base da stack
