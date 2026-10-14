# OCI Serverless Infrastructure

Infraestrutura Terraform modular para provisionar workloads serverless na Oracle Cloud Infrastructure (OCI). Segue o padrão **module composition** com directory-per-environment.

## Arquitetura

```
Internet → [API Gateway (subnet pública)] → [Functions (subnet privada)] → OCI Services
                                                                          ↓
                                                              [Vault, Object Storage, DB]
```

Cada função roda em sua própria **Application isolada**, com routing centralizado no API Gateway via `route_backends`.

## Estrutura

```
infra/
├── modules/                        # Módulos reutilizáveis
│   ├── network/                    # VCN, Subnets, Gateways, NSGs
│   ├── iam/                        # Dynamic Groups + Policies
│   ├── function-app/               # 1 Application + 1 Function (per instance)
│   ├── api-gateway/                # Gateway + Deployment + Routes
│   ├── vault/                      # KMS Vault, Key, Object Storage Bucket
│   ├── observability/              # Logging + Monitoring Alarms
│   └── apm/                        # APM Domain + Data Keys (tracing)
├── environments/
│   ├── dev/                        # Composição para dev
│   │   ├── main.tf                 # Infra compartilhada (network, iam, vault)
│   │   ├── apps.tf                 # Function apps + API Gateway + secrets
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── versions.tf
│   │   └── terraform.tfvars
│   └── prod/                       # Composição para prod
├── tests/                          # Testes nativos terraform test
└── README.md
```

## Módulos

| Módulo | Responsabilidade | Docs |
|--------|-----------------|------|
| `modules/network` | VCN, subnets, IGW, NAT GW, Service GW, route tables, security lists, NSGs | [README](modules/network/README.md) |
| `modules/iam` | Dynamic Groups (Functions + API GW), IAM Policies | [README](modules/iam/README.md) |
| `modules/function-app` | 1 Functions Application + 1 Function por instância (isolamento per-app) | [README](modules/function-app/README.md) |
| `modules/api-gateway` | Gateway, Deployment com `route_backends`, JWT, CORS, rate limiting, health check | [README](modules/api-gateway/README.md) |
| `modules/vault` | KMS Vault, Key (AES-256), Object Storage Bucket (versionado) | [README](modules/vault/README.md) |
| `modules/observability` | Log Group, Service Logs, Notification Topic, Alarms (errors, duration, throttle, 5xx) | [README](modules/observability/README.md) |
| `modules/apm` | APM Domain (free tier), Data Keys — habilita `trace_config.domain_id` nas Applications | — |

## Uso Rápido

Cada environment compõe os módulos diretamente. Para adicionar uma nova função, adicione um bloco `module` em `apps.tf`:

```hcl
# environments/dev/apps.tf

module "app_api_handler" {
  source = "../../modules/function-app"

  compartment_ocid   = var.compartment_ocid
  subnet_id          = module.network.subnet_private_id
  nsg_ids            = [module.network.nsg_functions_id]
  application_name   = "app-api-handler"
  function_name      = "api-handler"
  function_image     = var.api_handler_image
  memory_in_mbs      = 256
  timeout_in_seconds = 60
  function_config    = { LOG_LEVEL = "INFO" }
  environment        = var.environment
  tags               = local.tags

  depends_on = [module.iam]
}

# API Gateway com routing multi-function
module "api_gateway" {
  source = "../../modules/api-gateway"

  route_backends = [
    { path = "/hello", methods = ["GET", "POST"], function_id = module.app_api_handler.function_id, auth_type = "ANONYMOUS" },
    { path = "/users", methods = ["GET"],         function_id = module.app_api_handler.function_id, auth_type = "AUTHENTICATION_ONLY" },
  ]
  # ...
}
```

## Pré-requisitos

1. **OCI CLI configurado** — `~/.oci/config` com API key ou SecurityToken
2. **Compartment existente** — Os módulos não criam compartments
3. **Imagens Docker no OCIR** — Cada Function image deve estar publicada no OCI Container Registry
4. **Terraform >= 1.11** e **OCI Provider ~> 8.13**

## Inputs (por environment)

| Nome | Tipo | Obrigatório | Default | Descrição |
|------|------|:-----------:|---------|-----------|
| `tenancy_ocid` | string | ✅ | — | OCID da tenancy |
| `compartment_ocid` | string | ✅ | — | OCID do compartment |
| `compartment_name` | string | ✅ | — | Nome do compartment (para policies) |
| `region` | string | ✅ | — | OCI region |
| `api_handler_image` | string | ✅ | — | URI OCIR da função api-handler |
| `api_facade_image` | string | ✅ | — | URI OCIR da função func-api-facade |
| `rest_proxy_image` | string | ✅ | — | URI OCIR da função func-rr-rest-proxy |
| `function_shape` | string | | `GENERIC_X86` | Arquitetura (X86/ARM) |
| `trace_enabled` | bool | | `true` | Habilitar tracing nas Functions |
| `api_gateway_name` | string | | `apigw-serverless` | Nome do API Gateway |
| `deployment_path_prefix` | string | | `/v1` | Path prefix das APIs |
| `rate_limit_requests_per_second` | number | | `100` | Rate limit (0=off) |
| `cors_allowed_origins` | list(string) | | `[]` | Origins CORS |
| `jwt_auth_enabled` | bool | | `false` | JWT authentication |
| `environment` | string | | `dev` | dev/prod |
| `create_nat_gateway` | bool | | `true` | NAT GW para egress |
| `use_nsg` | bool | | `true` | Network Security Groups |
| `vault_key_protection_mode` | string | | `SOFTWARE` | SOFTWARE (dev) ou HSM (prod) |

## Outputs (por environment)

| Nome | Descrição |
|------|-----------|
| `api_base_url` | URL base da API (gateway endpoint + path prefix) |
| `health_check_url` | URL do health check |
| `api_gateway_hostname` | Hostname do API Gateway |
| `api_gateway_id` | OCID do API Gateway |
| `api_handler_function_id` | OCID da Function api-handler |
| `api_facade_function_id` | OCID da Function func-api-facade |
| `rest_proxy_function_id` | OCID da Function func-rr-rest-proxy |
| `vcn_id` | OCID da VCN |
| `subnet_private_id` | OCID da subnet privada |
| `subnet_public_id` | OCID da subnet pública |
| `vault_id` | OCID do KMS Vault |
| `vault_key_id` | OCID da KMS Key |

## Notas

### Imagem Docker vs Function Shape

| Shape | Arquitetura da Imagem |
|-------|----------------------|
| `GENERIC_X86` | `linux/amd64` (padrão de `docker build`) |
| `GENERIC_ARM` | `linux/arm64` (requer `docker buildx build --platform linux/arm64`) |

### Security

- Functions em subnet privada (sem IP público)
- API Gateway como único ponto de entrada público
- NSGs granulares por resource type
- Dynamic Groups + Resource Principals (zero credentials)
- Rate limiting + JWT authentication no API Gateway
- OCI Logging + Monitoring Alarms habilitados por default

## Dependências entre Módulos

```
network ──────┐
              ├──→ function-app (×N) ──┐
iam ──────────┤                        ├──→ observability
              ├──→ vault               │
              ├──→ api-gateway ────────┘
              └──→ apm (APM Domain → trace_config.domain_id em function-app)
```

- `function-app` depende de `network` (subnet) e `iam` (policies)
- `api-gateway` depende de `network` (subnet), `iam` (policies), e `function-app` (function_ids para route_backends)
- `vault` depende de nada (standalone)
- `observability` depende de `function-app` (application_id) e `api-gateway` (deployment_id)

## Destruição e Cleanup

### Via Terraform (caminho feliz)

```bash
cd infra/environments/dev
terraform destroy -var-file="terraform.tfvars"
```

### Via OCI CLI (fallback para problemas no destroy)

Se `terraform destroy` falhar parcialmente (state corrompido, timeout, recursos órfãos, profile inválido durante destroy), use o script de cleanup:

```bash
# Dry-run: lista recursos sem deletar
./scripts/oci-cleanup.sh --dry-run

# Execução real (pede confirmação)
./scripts/oci-cleanup.sh
```

**Pré-requisitos:**
- `jq` instalado (`brew install jq`)
- Sessão OCI válida: `oci session authenticate --profile poc`

**O que o script faz:**
1. Lista todos os recursos no compartment via OCI CLI
2. Deleta na ordem reversa de dependências (observability → API GW → functions → vault → storage → networking → IAM → OCIR)
3. Retry automático em subnets (VNICs podem levar até 10min para liberar)
4. Vault/Secrets são agendados para pending-deletion (mínimo 7d/2d — imposição OCI)

**Ordem de remoção (respeita dependências):**
```
1. Alarms, Logs, Notifications    (nenhuma dependência)
2. API Gateway Deployment/Gateway  (referencia Function IDs)
3. Functions/Applications           (usa subnet + NSG)
4. Vault Secrets + Vault            (schedule deletion — 7 dias)
5. Object Storage Bucket            (standalone)
6. NSGs → Subnets → Route Tables → Security Lists → Gateways → VCN
7. Policies + Dynamic Groups        (tenancy + compartment level)
8. OCIR Images + Repositories       (standalone)
```

**Cenários de uso:**
- `terraform destroy` deu timeout e deixou recursos pendentes
- State local apagado/corrompido sem backup
- Profile OCI mudou entre apply e destroy
- Recursos criados manualmente fora do Terraform
- Limpeza final pós-terraform-destroy que não removeu tudo
