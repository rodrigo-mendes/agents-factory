# Function: func-rr-rest-proxy

OCI Function implementing the **Request-Reply REST Proxy** pattern (Pattern 01a) — proxies between Oracle RMS (JSON + OAuth2) and BrxServices (XML/SOAP).

## Architecture

```
API Gateway → func-rr-rest-proxy → Oracle RMS (OAuth2, JSON)
                                  → BrxServices (XML)
```

## Rotas

| Method | Path | Description |
|--------|------|-------------|
| POST | `/store/create` | Create store in BrxServices from RMS data |
| POST | `/store/update` | Update store in BrxServices from RMS data |

## Stack

| Componente | Versão |
|---|---|
| Java | 21 (Amazon Corretto) |
| Fn FDK | 1.1.11 (fn-events) |
| OCI SDK | 3.86.x |
| HTTP Client | Jersey3 (`oci-java-sdk-common-httpclient-jersey3`) |
| Auth | Resource Principal + OAuth2 Client Credentials (IDCS) |

## Configuração (func.yaml config keys)

| Key | Description | Example |
|-----|-------------|---------|
| `STORE_SOURCE_BASE_URL` | RMS API base URL | `https://rms.example.com/api/v1` |
| `STORE_DESTINATION_BASE_URL` | BrxServices endpoint | `https://brx.example.com/services` |
| `STORE_OAUTH_TOKEN_URL` | IDCS token endpoint | `https://idcs.example.com/oauth2/v1/token` |
| `STORE_OAUTH_SCOPE` | OAuth scope | `https://rms.example.com/.default` |
| `STORE_CLIENT_ID_SECRET_OCID` | Vault secret OCID for client ID | `ocid1.vaultsecret...` |
| `STORE_CLIENT_SECRET_SECRET_OCID` | Vault secret OCID for client secret | `ocid1.vaultsecret...` |
| `STORE_TIMEOUT_MS` | HTTP timeout (ms) | `10000` |
| `APM_DOMAIN_URL` | APM data upload endpoint (injetado via Terraform) | `https://...apm.us-ashburn-1.oci.oraclecloud.com` |
| `APM_DATA_KEY` | APM private data key para autenticação de spans (injetado via Terraform) | `<private-key>` |
| `METRIC_NAMESPACE` | Namespace para métricas customizadas via PostMetricData | `app_analytics` |
| `COMPARTMENT_OCID` | OCID do compartment (necessário para PostMetricData) | `ocid1.compartment...` |

## Dependências OCI

| Serviço | Uso | Permissão necessária |
|---------|-----|---------------------|
| OCI Vault | Leitura de OAuth2 credentials | `read secret-bundles in compartment` |
| External (RMS) | API source (OAuth2 protected) | Egress via NAT Gateway |
| External (BrxServices) | API destination (XML) | Egress via NAT Gateway |

Autenticação: **Resource Principal** para Vault + **OAuth2 Client Credentials** para RMS.

## Build & Test

```bash
cd services/func-rr-rest-proxy

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
module "app_rest_proxy" {
  source           = "../../modules/function-app"
  application_name = "app-rest-proxy"
  function_name    = "func-rr-rest-proxy"
  function_image   = var.rest_proxy_image
  memory_in_mbs    = 256
  timeout_in_seconds = 60
  function_config  = {
    STORE_SOURCE_BASE_URL          = var.rest_proxy_store_source_base_url
    STORE_DESTINATION_BASE_URL     = var.rest_proxy_store_destination_base_url
    STORE_OAUTH_TOKEN_URL          = var.rest_proxy_store_oauth_token_url
    STORE_OAUTH_SCOPE              = var.rest_proxy_store_oauth_scope
    STORE_CLIENT_ID_SECRET_OCID    = var.rest_proxy_store_oauth_client_id_ocid
    STORE_CLIENT_SECRET_SECRET_OCID = var.rest_proxy_store_oauth_client_secret_ocid
    STORE_TIMEOUT_MS               = var.rest_proxy_store_timeout_ms
  }
}
```

### Criar Vault Secrets (pré-requisito)

Os OAuth2 credentials devem ser criados como secrets no OCI Vault **antes** do deploy:

```bash
VAULT_ID=$(terraform output -raw vault_id)
KEY_ID=$(terraform output -raw key_id)

oci vault secret create-base64 \
  --compartment-id "<compartment-ocid>" \
  --vault-id "$VAULT_ID" \
  --key-id "$KEY_ID" \
  --secret-name "rms-oauth-client-id-dev" \
  --secret-content-content "$(echo -n '<client-id>' | base64)"

oci vault secret create-base64 \
  --compartment-id "<compartment-ocid>" \
  --vault-id "$VAULT_ID" \
  --key-id "$KEY_ID" \
  --secret-name "rms-oauth-client-secret-dev" \
  --secret-content-content "$(echo -n '<client-secret>' | base64)"
```

Use os OCIDs retornados nas variáveis `*_ocid` do Terraform.

## Testes

```bash
mvn test
```

Cobertura:
- Store create — proxy completo (200, mock HttpClient)
- Store update — proxy completo (200, mock HttpClient)
- OAuth2 token acquisition — mock token endpoint
- Error handling — backend failure (502), timeout (504)
- XML transformation — JSON → XML mapping
