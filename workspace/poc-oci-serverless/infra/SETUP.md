# Guia de Setup — OCI Serverless (Functions + API Gateway)

Passo a passo para configurar e provisionar o ambiente serverless na Oracle Cloud.

---

## 1. Pré-requisitos

### 1.1 Instalar ferramentas

```bash
# Terraform
brew install terraform

# OCI CLI
brew install oci-cli
```

### 1.2 Configurar OCI CLI

```bash
oci setup config
```

O wizard solicitará:

| Campo | Onde encontrar |
|-------|---------------|
| User OCID | OCI Console → Profile (canto superior direito) → **My Profile** → copiar OCID |
| Tenancy OCID | OCI Console → Profile → **Tenancy: \<nome\>** → copiar OCID |
| Region | Região da console (ex: `sa-saopaulo-1`) |
| API Key | O wizard gera automaticamente o par de chaves |

Após finalizar, faça upload da chave pública na console:
**Profile → My Profile → API Keys → Add API Key → Paste Public Key**

Resultado: arquivo `~/.oci/config` configurado.

---

## 2. Informações necessárias

| Variável | Onde encontrar na OCI Console |
|----------|-------------------------------|
| `tenancy_ocid` | Profile → **Tenancy: \<nome\>** → OCID |
| `compartment_ocid` | **Identity & Security** → **Compartments** → selecionar compartment → OCID |
| `compartment_name` | Mesmo lugar acima — é o nome que aparece na lista |
| `region` | Canto superior direito — identifier (ex: `sa-saopaulo-1`) |
| `*_image` | Após push no OCIR — formato: `<region-key>.ocir.io/<namespace>/<repo>/<image>:<tag>` (uma por função) |

### Descobrir o namespace do OCIR

```bash
oci os ns get
```

Ou na console: **Developer Services → Container Registry** — namespace aparece no topo.

### Region keys para OCIR

| Region | Identifier | OCIR Key |
|--------|-----------|----------|
| São Paulo | `sa-saopaulo-1` | `gru` |
| Vinhedo | `sa-vinhedo-1` | `vcp` |
| Ashburn | `us-ashburn-1` | `iad` |
| Phoenix | `us-phoenix-1` | `phx` |

---

## 3. Publicar a Function no OCIR

### 3.1 Gerar Auth Token

OCI Console → **Profile → Auth Tokens → Generate Token**

> Copie o token imediatamente — ele não será exibido novamente.

### 3.2 Login no Container Registry

```bash
docker login gru.ocir.io \
  -u '<namespace>/oracleidentitycloudservice/<email>' \
  -p '<auth-token>'
```

### 3.3 Build e Push da imagem

**Método automatizado (recomendado):**

Cada serviço possui um script `build-push.sh` que lê credenciais de `services/.env`:

```bash
# Setup inicial (uma vez)
cp services/.env.example services/.env
# Editar services/.env com OCIR_USERNAME e OCIR_PASSWORD (Auth Token)

# Build + push de qualquer function
cd services/api-handler && ./build-push.sh
cd services/func-rr-rest-proxy && ./build-push.sh
cd services/func-api-facade && ./build-push.sh

# Override de tag
./build-push.sh 0.0.2
```

**Método manual:**

```bash
# Build (imagem x86 — compatível com GENERIC_X86, default do módulo)
docker build -t gru.ocir.io/<namespace>/serverless-app/api-handler:0.0.1 .

# Build para ARM (se usar function_shape = GENERIC_ARM)
# docker buildx build --platform linux/arm64 -t gru.ocir.io/<namespace>/serverless-app/api-handler:0.0.1 .

# Push
docker push gru.ocir.io/<namespace>/serverless-app/api-handler:0.0.1
```

> Substitua `<namespace>` pelo valor obtido com `oci os ns get`.

---

## 4. Configurar variáveis do Terraform

```bash
cd infra/environments/dev

# Editar terraform.tfvars com seus valores
```

Editar `terraform.tfvars` com seus valores reais:

```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..aaa..."
compartment_ocid = "ocid1.compartment.oc1..aaa..."
compartment_name = "meu-compartment"
region           = "sa-saopaulo-1"

# Function images (uma por função)
api_handler_image = "gru.ocir.io/<namespace>/serverless-app/api-handler:0.0.5"
api_facade_image  = "gru.ocir.io/<namespace>/serverless-app/func-api-facade:0.0.2"
rest_proxy_image  = "gru.ocir.io/<namespace>/serverless-app/func-rr-rest-proxy:0.0.14"
```

### 4.1 Variáveis opcionais relevantes

O módulo já possui defaults seguros para observabilidade e segurança. Opcionalmente configure:

```hcl
# Observabilidade (habilitados por default)
enable_logging           = true   # Logs de Functions + API Gateway
enable_monitoring_alarms = true   # Alarmes de errors, latência, 5xx
alarm_duration_threshold_ms = 25000  # P95 latência threshold (80% de 60s)

# JWT Authentication (desabilitado por default)
jwt_auth_enabled = true
jwt_issuers      = ["https://identity.oraclecloud.com/"]
jwt_audiences    = ["https://minha-api.example.com"]
jwt_jwks_uri     = "https://idcs-<id>.identity.oraclecloud.com/admin/v1/SigningCert/jwk"

# Network Security Groups (habilitado por default)
use_nsg = true
```

> **NUNCA** commite `terraform.tfvars` no git — ele pode conter informações sensíveis.

---

## 5. Executar Terraform

### 5.1 Inicializar (download de providers)

```bash
terraform init
```

### 5.2 Validar configuração

```bash
terraform validate
```

### 5.3 Preview das mudanças (não altera nada)

```bash
terraform plan -var-file="terraform.tfvars"
```

### 5.4 Aplicar (cria toda a infraestrutura)

```bash
terraform apply -var-file="terraform.tfvars"
```

Confirme digitando `yes` quando solicitado.

---

## 6. Verificar o deploy

### 6.1 Health check

```bash
curl $(terraform output -raw health_check_url)
```

Resposta esperada:

```json
{"status": "healthy", "environment": "dev"}
```

### 6.2 Testar endpoint da Function

```bash
# Hello (GET)
curl $(terraform output -raw api_base_url)/hello

# Secret (POST)
curl -X POST $(terraform output -raw api_base_url)/secret \
  -H "Content-Type: application/json" \
  -d '{"resource_id": "ocid1.secret.oc1..."}'
```

### 6.3 Verificar logs e alarmes

Se `enable_logging=true` (default), os **SERVICE logs** de invocação já estarão sendo coletados automaticamente. Os **Application Logs** (stdout das functions) requerem ativação manual — veja seção 6.3.1.

```bash
# Ver o Log Group criado
terraform output log_group_id

# Ver o Notification Topic (para configurar subscriptions)
terraform output notification_topic_id
```

### 6.3.1 Ativar Application Logs — Passo Manual Obrigatório

> **Por que manual?** O provider Terraform OCI não expõe a configuração de log de stdout de Applications via HCL. Este passo é feito **uma única vez por Application**.

**1. Obter o Log Group:**

```bash
terraform output -raw log_group_id
```

**2. OCI Console → Developer Services → Functions → Applications**

**3. Repetir para cada Application** (`api-handler`, `func-api-facade`, `rest-proxy`):

| Passo | Ação |
|-------|------|
| Clicar na Application | |
| Menu lateral → **Logs** | |
| Linha **"Function Invoke Log"** → toggle **Disabled** | Abre painel |
| **Log Group** | `log-group-serverless-poc-dev` |
| **Log Name** | `fn-invoke-<nome-da-app>-stdout` |
| **Retention** | 30 days |
| Clicar em **Enable Log** | |

**4. Verificar:** OCI Console → **Observability & Management → Logging → Search**
- Log Group: `log-group-serverless-poc-dev`
- Time range: Last 15 minutes (aguardar 2-3 min após próxima invocação)
- Confirmar campos JSON: `level`, `message`, `coldStart`, `traceId`

### 6.4 Configurar Notification Subscriptions

O módulo cria o Notification Topic mas **não cria subscriptions** (varia por equipe). Configure manualmente:

```bash
# Subscription por email
oci ons subscription create \
  --compartment-id <compartment_ocid> \
  --topic-id $(terraform output -raw notification_topic_id) \
  --protocol EMAIL \
  --endpoint "equipe@empresa.com"

# Subscription via HTTPS (webhook para Slack/PagerDuty)
oci ons subscription create \
  --compartment-id <compartment_ocid> \
  --topic-id $(terraform output -raw notification_topic_id) \
  --protocol HTTPS \
  --endpoint "https://hooks.slack.com/services/..."
```

> Após criar, confirme o subscription clicando no link enviado por email.

### 6.5 Ver todos os outputs

```bash
terraform output
```

---

## 7. Operações do dia-a-dia

### Atualizar a Function (nova versão da imagem)

1. Build e push da nova tag
2. Alterar a variável `<func>_image` correspondente no `terraform.tfvars`
3. `terraform apply -var-file="terraform.tfvars"`

### Adicionar novas rotas

Editar `route_backends` no bloco `module "api_gateway"` em `apps.tf`:

```hcl
route_backends = [
  { path = "/users",      methods = ["GET", "POST"],              function_id = module.app_users.function_id, auth_type = "ANONYMOUS" },
  { path = "/users/{id}", methods = ["GET", "PUT", "DELETE"],     function_id = module.app_users.function_id, auth_type = "ANONYMOUS" },
  { path = "/orders",     methods = ["GET", "POST"],              function_id = module.app_orders.function_id, auth_type = "ANONYMOUS" },
]
```

### Incluir uma nova Function

#### Passo 1 — Criar o código da Function

Crie um diretório para a nova function com a estrutura esperada pelo Fn Project:

```bash
mkdir -p services/minha-nova-func/src/main/java/com/brx/functions/novafunc
cd services/minha-nova-func
```

Exemplo mínimo (Java 17 + Maven):

**Handler** (`src/main/java/com/brx/functions/novafunc/NovaFuncFunction.java`):

```java
package com.brx.functions.novafunc;

import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;

public class NovaFuncFunction {

    private String environment;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        this.environment = ctx.getConfigurationByKey("ENVIRONMENT").orElse("dev");
    }

    public String handler(String input) {
        return "{\"message\": \"ok\", \"env\": \"" + environment + "\"}";
    }
}
```

**func.yaml**:

```yaml
schema_version: 20180708
name: minha-nova-func
version: 0.0.1
runtime: java
build_image: fnproject/fn-java-fdk-build:jdk17-latest
run_image: fnproject/fn-java-fdk:jre17-latest
cmd: com.brx.functions.novafunc.NovaFuncFunction::handler
memory: 256
timeout: 60
```

**pom.xml** (dependências essenciais):

```xml
<dependencies>
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>api</artifactId>
        <version>1.1.11</version>
    </dependency>
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>testing-junit4</artifactId>
        <version>1.1.11</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

> Consultar o projeto `services/api-handler/` para referência com OCI SDK, testes e Dockerfile multi-stage.

#### Passo 2 — Build e Push da imagem para o OCIR

```bash
docker build -t gru.ocir.io/<namespace>/serverless-app/minha-nova-func:0.0.1 .
docker push gru.ocir.io/<namespace>/serverless-app/minha-nova-func:0.0.1
```

#### Passo 3 — Adicionar módulo no Terraform

Em `infra/environments/dev/apps.tf`, adicione um novo bloco `module`:

```hcl
module "app_nova_func" {
  source = "../../modules/function-app"

  compartment_ocid   = var.compartment_ocid
  subnet_id          = module.network.subnet_private_id
  nsg_ids            = var.use_nsg ? [module.network.nsg_functions_id] : []
  application_name   = "app-nova-func"
  function_name      = "minha-nova-func"
  function_image     = var.nova_func_image
  memory_in_mbs      = 256
  timeout_in_seconds = 60
  function_config    = { LOG_LEVEL = "INFO" }
  function_shape     = var.function_shape
  trace_enabled      = var.trace_enabled
  environment        = var.environment
  tags               = local.tags

  depends_on = [module.iam]
}
```

#### Passo 4 — Adicionar rota no API Gateway

No mesmo `apps.tf`, adicione uma entrada no `route_backends` do `module "api_gateway"`:

```hcl
route_backends = [
  # ... rotas existentes ...
  {
    path        = "/nova-rota"
    methods     = ["GET", "POST"]
    function_id = module.app_nova_func.function_id
    auth_type   = "ANONYMOUS"
  },
]
```

#### Passo 5 — Adicionar variável de imagem

Em `variables.tf`, adicionar:

```hcl
variable "nova_func_image" {
  type        = string
  description = "OCIR image URI for minha-nova-func"
}
```

E em `terraform.tfvars`:

```hcl
nova_func_image = "gru.ocir.io/<namespace>/serverless-app/minha-nova-func:0.0.1"
```

#### Passo 6 — Aplicar as mudanças

```bash
cd infra/environments/dev
terraform validate
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

#### Passo 7 — Testar a nova Function

```bash
curl $(terraform output -raw api_base_url)/nova-rota
```

#### Resumo — Checklist nova Function

- [ ] Código da function criado (`pom.xml`, `func.yaml`, `Dockerfile`, handler Java)
- [ ] Testes executados com sucesso (`mvn test`)
- [ ] Imagem Docker buildada e pushada no OCIR
- [ ] Bloco `module "app_<name>"` adicionado em `apps.tf`
- [ ] Rota adicionada em `route_backends` do `module "api_gateway"`
- [ ] Variável de imagem adicionada em `variables.tf` e `terraform.tfvars`
- [ ] `terraform apply` executado com sucesso
- [ ] Endpoint testado e respondendo

---

### Habilitar JWT Authentication

Para proteger as rotas com autenticação JWT (OIDC/OAuth2):

#### Passo 1 — Identificar o Identity Provider

Você precisa das informações do seu IdP (Identity Cloud Service, Auth0, Okta, etc.):

| Informação | Onde encontrar |
|------------|----------------|
| Issuer URL | Configuração do IdP (ex: `https://identity.oraclecloud.com/`) |
| Audience | O identifier da sua API no IdP |
| JWKS URI | Endpoint público de chaves (ex: `https://idcs-<id>.identity.oraclecloud.com/admin/v1/SigningCert/jwk`) |

#### Passo 2 — Adicionar variáveis ao terraform.tfvars

```hcl
jwt_auth_enabled = true
jwt_issuers      = ["https://identity.oraclecloud.com/"]
jwt_audiences    = ["https://minha-api.example.com"]
jwt_jwks_uri     = "https://idcs-<id>.identity.oraclecloud.com/admin/v1/SigningCert/jwk"
```

#### Passo 3 — Aplicar

```bash
terraform plan -var-file="terraform.tfvars"   # Verificar mudanças
terraform apply -var-file="terraform.tfvars"
```

#### Passo 4 — Testar com token

```bash
# Obter token do IdP (exemplo com IDCS)
TOKEN=$(curl -s -X POST "https://idcs-<id>.identity.oraclecloud.com/oauth2/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&scope=read" \
  -u "<client_id>:<client_secret>" | jq -r '.access_token')

# Chamar API com token
curl -H "Authorization: Bearer $TOKEN" \
  $(terraform output -raw api_base_url)/hello

# Health check continua público (sem token)
curl $(terraform output -raw health_check_url)
```

> **Nota:** O health check (`/health`) é sempre público (ANONYMOUS) mesmo com JWT habilitado.

---

### Desabilitar features opcionais

Para ambientes de teste onde não precisa de logging/monitoring:

```hcl
enable_logging           = false
enable_monitoring_alarms = false
use_nsg                  = false  # Manter Security Lists apenas
```

---

### Destruir o ambiente (CUIDADO!)

```bash
terraform destroy -var-file="terraform.tfvars"
```

---

## 8. Troubleshooting

| Problema | Solução |
|----------|---------|
| `401 Not Authenticated` no OCIR login | Auth Token expirado — gere um novo |
| `401` na API com JWT habilitado | Token expirado ou issuer/audience incorretos — verifique `jwt_issuers` e `jwt_audiences` |
| `404` no endpoint da API | Verifique se o `deployment_path_prefix` + `path` batem com a URL |
| Function timeout | Aumente `function_timeout_in_seconds` ou `function_memory_in_mbs` |
| `Policy not found` | Policies levam ~30s para propagar — aguarde e tente novamente |
| `Subnet not found` | Verifique se `compartment_ocid` está correto |
| Cold start lento | Configure `provisioned_concurrency > 0` para produção |
| `400-InvalidParameter, Invalid traceConfig` | `trace_config` na Application requer um APM Domain com `domain_id`. Remova o bloco ou provisione um APM Domain |
| `400-InvalidParameter, Invalid image - incompatible architecture` | A arquitetura da imagem Docker não corresponde ao `function_shape`. Use `GENERIC_X86` para imagens x86 (padrão) ou faça `docker buildx build --platform linux/arm64` para `GENERIC_ARM` |
| Alarmes não disparam | Verifique se há subscriptions no Notification Topic (Seção 6.4) |
| Logs não aparecem | Confirme `enable_logging = true` e aguarde ~2min para propagação — se persistir, verifique se o Application Log foi habilitado manualmente (seção 6.3.1) |

---

## Resumo do fluxo

```
1. oci setup config          → Configura credenciais
2. docker push               → Publica Function no OCIR
3. cp terraform.tfvars       → Preenche variáveis
4. terraform init            → Baixa providers
5. terraform apply           → Cria infraestrutura
6. curl /health              → Valida deploy
7. oci ons subscription      → Configura alertas (opcional)
8. jwt_auth_enabled=true     → Protege rotas com JWT (opcional)
```

## O que o módulo cria automaticamente

Com as configurações default, o `terraform apply` provisiona:

| Categoria | Recursos | Sub-módulo |
|-----------|----------|------------|
| **Networking** | VCN, Subnet Pública, Subnet Privada, Internet GW, NAT GW, Service GW, Route Tables, Security Lists, NSGs | `modules/network` |
| **Security** | 2 Dynamic Groups, 3 IAM Policies | `modules/iam` |
| **Compute** | Functions Application + Function (×N) | `modules/function-app` |
| **API** | API Gateway + Deployment (rate limiting, CORS, JWT, health check) | `modules/api-gateway` |
| **Observability** | Log Group, 3 Service Logs, Notification Topic, 9 Monitoring Alarms (erros×3, latência×3, throttle×3) + 1 Alarm API GW 5xx | `modules/observability` |
| **APM** | APM Domain (free tier), Data Keys (private/public) | `modules/apm` |

## Estrutura modular

```
infra/
├── modules/
│   ├── network/            # VCN, Subnets, Gateways, NSGs
│   ├── iam/                # Dynamic Groups + Policies
│   ├── function-app/       # 1 Application + 1 Function (per instance)
│   ├── api-gateway/        # Gateway + Deployment + Routes
│   ├── vault/              # KMS Vault, Key, Object Storage Bucket
│   ├── observability/      # Logging + Alarms
│   └── apm/                # APM Domain + Data Keys (tracing)
├── environments/
│   ├── dev/
│   │   ├── main.tf         # Infra compartilhada (network, iam, vault)
│   │   ├── apps.tf         # Function apps + API Gateway + secrets
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── versions.tf
│   │   └── terraform.tfvars
│   └── prod/
├── tests/
└── README.md
```
