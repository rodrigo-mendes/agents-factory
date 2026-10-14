# Module: API Gateway

Provisiona o OCI API Gateway com Deployment, Routes, JWT, CORS e Rate Limiting.

## Recursos Criados

- **API Gateway** — Gateway público ou privado com NSG
- **Deployment** — Deployment com routes, logging, autenticação JWT, CORS e rate limiting
- **Health Check Route** — Rota `/health` sempre anônima com STOCK_RESPONSE_BACKEND

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `compartment_ocid` | OCID do compartment | `string` | - | yes |
| `subnet_id` | OCID da subnet pública | `string` | - | yes |
| `nsg_ids` | Lista de NSG IDs | `list(string)` | `[]` | no |
| `route_backends` | Lista de routes com function_id por rota | `list(object)` | - | yes |
| `gateway_name` | Nome do API Gateway | `string` | `apigw-serverless` | no |
| `endpoint_type` | Tipo de endpoint (PUBLIC, PRIVATE) | `string` | `PUBLIC` | no |
| `deployment_path_prefix` | Path prefix do deployment | `string` | `/v1` | no |
| `rate_limit_requests_per_second` | Rate limit (0-10000, 0=desabilitado) | `number` | `100` | no |
| `cors_allowed_origins` | Origins CORS permitidos | `list(string)` | `[]` | no |
| `jwt_auth_enabled` | Habilitar JWT | `bool` | `false` | no |
| `jwt_issuers` | Issuers JWT válidos | `list(string)` | `[]` | no |
| `jwt_audiences` | Audiences JWT válidos | `list(string)` | `[]` | no |
| `jwt_jwks_uri` | URI do JWKS endpoint | `string` | `""` | no |
| `environment` | Nome do ambiente | `string` | - | yes |
| `project_name` | Nome do projeto | `string` | - | yes |
| `tags` | Tags para os recursos | `map(string)` | `{}` | no |

## Uso

```hcl
module "api_gateway" {
  source = "../../modules/api-gateway"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_public_id
  nsg_ids          = [module.network.nsg_apigw_id]

  route_backends = [
    { path = "/hello", methods = ["GET", "POST"], function_id = module.app_api_handler.function_id, auth_type = "ANONYMOUS" },
    { path = "/users", methods = ["GET"],         function_id = module.app_users.function_id,       auth_type = "AUTHENTICATION_ONLY" },
  ]

  jwt_auth_enabled = false
  environment      = var.environment
  project_name     = var.project_name
  tags             = local.tags
}
```

## Outputs

| Name | Description |
|------|-------------|
| `gateway_id` | OCID do API Gateway |
| `gateway_hostname` | Hostname do API Gateway |
| `gateway_ip_addresses` | IPs do API Gateway |
| `deployment_id` | OCID do Deployment |
| `deployment_endpoint` | Endpoint completo (URL base) |

## Dependências

- **Network** — `subnet_id` (pública) e `nsg_ids` do módulo network
- **Function App** — `function_id` de cada módulo function-app (para `route_backends`)
- **IAM** — Dynamic Group do API Gateway deve existir para invocar Functions
