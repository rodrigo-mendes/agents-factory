# Function: api-handler

Function serverless de referência — health check / smoke test para validar conectividade do API Gateway.

## Stack

| Componente | Versão |
|---|---|
| Java | 17 |
| Fn FDK | 1.1.11 (fn-events) |
| Jackson | 2.17.2 |
| Build | Maven 3.x |

## Rotas

| Path | Método | Descrição |
|------|--------|-----------|
| `/hello` | GET | Health check / smoke test |

## Estrutura

```
src/main/java/com/brx/serverless/
├── handler/ApiHandler.java       # Entry-point (extends APIGatewayFunction)
└── model/
    ├── ApiRequest.java           # DTO de entrada
    └── ApiResponse.java          # DTO de saída
```

O handler estende `APIGatewayFunction<ApiRequest, ApiResponse>` do módulo `fn-events`, que fornece abstrações tipadas para integração com API Gateway.

## Configuração (func.yaml config keys)

| Key | Description | Default |
|-----|-------------|---------|
| `ENVIRONMENT` | Ambiente de execução | `dev` |
| `LOG_LEVEL` | Nível de log (SLF4J) | `INFO` |
| `APM_DOMAIN_URL` | APM data upload endpoint (injetado via Terraform) | `https://...` |
| `APM_DATA_KEY` | APM private data key para autenticação de spans (injetado via Terraform) | `<private-key>` |
| `COMPARTMENT_OCID` | OCID do compartment | `ocid1.compartment...` |

## Dependências OCI

Nenhuma — esta function é self-contained (não acessa Vault, Object Storage ou APIs externas).

## Build & Test

```bash
cd services/api-handler

# Compilar + testes
mvn clean package

# Apenas testes
mvn test

# Build + push da imagem (automatizado)
./build-push.sh
```

> Para instruções completas de build, push, e deploy: [GETTING-STARTED.md](../../GETTING-STARTED.md#4-build-e-push-de-functions)

## Infraestrutura Terraform

Module instance em `infra/environments/dev/apps.tf`:

```hcl
module "app_api_handler" {
  source           = "../../modules/function-app"
  application_name = "app-api-handler"
  function_name    = "api-handler"
  function_image   = var.api_handler_image
  memory_in_mbs    = 256
  timeout_in_seconds = 60
}
```

## Testes

```bash
mvn test
```

Cobertura:
- Route `GET /hello` — resposta OK (200)
- Route desconhecida — not found (404)
- Route `POST /secret` sem `resource_id` — erro de validação (400)
- Route `POST /store` sem campos obrigatórios — erro de validação (400)
- OCI services indisponível — service unavailable (503)
- Método HTTP inválido — method not allowed (405)
