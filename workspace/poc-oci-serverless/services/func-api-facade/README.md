# Function: func-api-facade

OCI Function implementing the **API Facade** pattern (Pattern 03) — transformation layer between API Gateway and OCI backend services (Vault Secrets, Object Storage).

## Architecture

```
API Gateway → func-api-facade → OCI Vault (read secrets)
                               → OCI Object Storage (write objects)
```

## Rotas

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hello` | Health check — retorna mensagem com environment |
| POST | `/secret` | Lê um secret do OCI Vault (requer `resource_id` no body) |
| POST | `/store` | Grava objeto no Object Storage (requer `bucket_name`, `object_name`, `data`) |

## Stack

| Componente | Versão |
|---|---|
| Java | 21 (Amazon Corretto) |
| Fn FDK | 1.1.11 (fn-events) |
| OCI SDK | 3.86.x |
| Auth | Resource Principal (zero credentials) |

## Configuração (func.yaml config keys)

| Key | Description | Example |
|-----|-------------|---------|
| `ENVIRONMENT` | Ambiente de execução | `dev` |
| `LOG_LEVEL` | Nível de log (SLF4J) | `INFO` |
| `APM_DOMAIN_URL` | APM data upload endpoint (injetado via Terraform) | `https://...apm.us-ashburn-1.oci.oraclecloud.com` |
| `APM_DATA_KEY` | APM private data key para autenticação de spans (injetado via Terraform) | `<private-key>` |
| `METRIC_NAMESPACE` | Namespace para métricas customizadas via PostMetricData | `app_analytics` |
| `COMPARTMENT_OCID` | OCID do compartment (necessário para PostMetricData) | `ocid1.compartment...` |

## Dependências OCI

| Serviço | Uso | Permissão necessária |
|---------|-----|---------------------|
| OCI Vault | Leitura de secrets | `read secret-bundles in compartment` |
| Object Storage | Gravação de objetos | `manage objects in compartment` |

Autenticação: **Resource Principal** (configurado via IAM Dynamic Group + Policy).

## Build & Test

```bash
cd services/func-api-facade

# Requer Java 21
java -version  # Must show Java 21

# Compilar + testes
mvn clean package

# Build + push (automatizado)
./build-push.sh
```

> Para instruções completas de build, push, e deploy: [GETTING-STARTED.md](../../GETTING-STARTED.md#4-build-e-push-de-functions)

## Infraestrutura Terraform

Module instance em `infra/environments/dev/apps.tf`:

```hcl
module "app_api_facade" {
  source           = "../../modules/function-app"
  application_name = "app-api-facade"
  function_name    = "func-api-facade"
  function_image   = var.api_facade_image
  memory_in_mbs    = 256
  timeout_in_seconds = 60
  function_config  = { LOG_LEVEL = "INFO" }
}
```

Requer também o módulo `vault` (KMS + Bucket) provisionado em `main.tf`.

## Testes

```bash
mvn test
```

Cobertura:
- Route `GET /hello` — health check (200)
- Route `POST /secret` — leitura de secret (200, mock Vault)
- Route `POST /store` — gravação de objeto (200, mock Object Storage)
- Route desconhecida — not found (404)
- Erro de serviço — error response (500)
