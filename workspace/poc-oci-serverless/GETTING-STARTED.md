# Getting Started — OCI Serverless

Guia completo para configurar o ambiente, fazer deploy de Functions e adicionar novas capacidades ao projeto.

> 🚀 **Novo no projeto?** Comece pelo onboarding por perfil: **[docs/onboarding/README.md](docs/onboarding/README.md)**
> — trilhas separadas para **desenvolvedor Java** e **DevOps/infra**. Este documento é a referência
> operacional completa (setup, build, deploy, day-2).

---

## Sumário

- [1. Pré-requisitos](#1-pré-requisitos)
- [2. Configurar OCI CLI](#2-configurar-oci-cli)
- [3. Configurar OCIR (Container Registry)](#3-configurar-ocir-container-registry)
- [4. Build e Push de Functions](#4-build-e-push-de-functions)
- [5. Provisionar Infraestrutura (Terraform)](#5-provisionar-infraestrutura-terraform)
- [6. Verificar o Deploy](#6-verificar-o-deploy)
- [7. Adicionar Nova Function — Passo a Passo Manual](#7-adicionar-nova-function--passo-a-passo-manual)
- [8. Adicionar Nova Function — Com Agents/Comandos Claude Code](#8-adicionar-nova-function--com-agentscomandos-claude-code)
- [9. Operações do Dia-a-Dia](#9-operações-do-dia-a-dia)

---

## 1. Pré-requisitos

### Ferramentas Obrigatórias

| Ferramenta | Versão Mínima | Instalação (macOS) |
|------------|---------------|-------------------|
| Terraform | v1.11+ | `brew install terraform` |
| OCI CLI | latest | `brew install oci-cli` |
| JDK | 17 (Amazon Corretto) | `brew install --cask corretto17` |
| Maven | 3.8+ | `brew install maven` |
| Docker | 24+ | Docker Desktop |

### Verificar instalação

```bash
terraform version    # >= 1.11
oci --version        # qualquer versão recente
java -version        # 17 (Amazon Corretto)
mvn -version         # >= 3.8
docker info          # daemon rodando
```

---

## 2. Configurar OCI CLI

O projeto usa o profile **`poc`** com autenticação **SecurityToken (sessão)** — é o método
esperado pelo provider Terraform (`auth = "SecurityToken"`, `config_file_profile = "poc"` em
`infra/environments/dev/versions.tf`). A sessão expira em **~1h**; renove antes de operações longas.

### 2.1 Autenticação por sessão (SecurityToken) — recomendado

```bash
# Abre o browser, autentica e grava o token de sessão em ~/.oci/sessions/poc/
oci session authenticate --profile poc --region sa-saopaulo-1

# Validar a sessão
oci session validate --profile poc --auth security_token

# Renovar quando expirar (ou re-executar o authenticate acima)
oci session refresh --profile poc
```

> ⚠️ Se a sessão expirar no meio de um `terraform apply`/validação longa, você verá **401**.
> Rode `oci session authenticate --profile poc` novamente antes de continuar.

### 2.2 Alternativa — API Key (wizard)

Para um profile permanente por chave de API (sem expiração), use o wizard:

```bash
oci setup config
```

O wizard solicitará:

| Campo | Onde encontrar no Console OCI |
|-------|-------------------------------|
| User OCID | Profile (canto superior direito) → **My Profile** → copiar OCID |
| Tenancy OCID | Profile → **Tenancy: \<nome\>** → copiar OCID |
| Region | Região atual (ex: `sa-saopaulo-1`) |
| API Key | O wizard gera automaticamente o par de chaves |

Após finalizar o wizard, faça upload da chave pública no Console:

**Profile → My Profile → API Keys → Add API Key → Paste Public Key**

Resultado: arquivo `~/.oci/config` configurado e pronto para uso. Se usar API Key, ajuste o
`config_file_profile`/`auth` do provider Terraform de acordo.

### 2.3 Coletar informações necessárias

| Variável Terraform | Onde encontrar |
|--------------------|----------------|
| `tenancy_ocid` | Profile → **Tenancy** → OCID |
| `compartment_ocid` | **Identity & Security** → **Compartments** → selecionar → OCID |
| `compartment_name` | Nome do compartment na lista |
| `region` | Identificador da região (ex: `sa-saopaulo-1`) |

### 2.4 Descobrir o namespace do OCIR

```bash
oci os ns get
```

Ou no Console: **Developer Services → Container Registry** — namespace aparece no topo.

### Region Keys para OCIR

| Region | Identifier | OCIR Key |
|--------|-----------|----------|
| São Paulo | `sa-saopaulo-1` | `gru` |
| Vinhedo | `sa-vinhedo-1` | `vcp` |
| Ashburn | `us-ashburn-1` | `iad` |
| Phoenix | `us-phoenix-1` | `phx` |

---

## 3. Configurar OCIR (Container Registry)

### 3.1 Gerar Auth Token

OCI Console → **Profile → Auth Tokens → Generate Token**

> ⚠️ Copie o token imediatamente — ele não será exibido novamente.

### 3.2 Login no Container Registry

```bash
docker login gru.ocir.io \
  -u '<namespace>/oracleidentitycloudservice/<email>' \
  -p '<auth-token>'
```

### 3.3 Configurar credenciais para scripts automatizados

```bash
cp services/.env.example services/.env
# Editar services/.env com:
# OCIR_USERNAME=<namespace>/oracleidentitycloudservice/<email>
# OCIR_PASSWORD=<auth-token>
```

> ⚠️ **Segurança:** Nunca commite `services/.env` no git.

---

## 4. Build e Push de Functions

### Método automatizado (recomendado)

Cada function tem um script `build-push.sh`:

```bash
cd services/api-handler && ./build-push.sh
cd services/func-api-facade && ./build-push.sh
cd services/func-rr-rest-proxy && ./build-push.sh

# Override de tag
./build-push.sh 0.0.2
```

### Método manual

```bash
cd services/<function-name>

# 1. Compilar
mvn clean package

# 2. Build da imagem (x86 — compatível com GENERIC_X86)
docker build -t gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/<function-name>:0.0.1 .

# 3. Push
docker push gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/<function-name>:0.0.1
```

> Para ARM (function_shape = GENERIC_ARM):
> `docker buildx build --platform linux/arm64 -t ... .`

### Preflight check (validação pré-build)

```bash
./scripts/preflight.sh services/<function-name>
```

Valida: CMD no Dockerfile, dependências SDK, ausência de credentials hardcoded.

---

## 5. Provisionar Infraestrutura (Terraform)

### 5.1 Configurar variáveis

```bash
cd infra/environments/dev
```

Editar `terraform.tfvars` com seus valores:

```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..aaa..."
compartment_ocid = "ocid1.compartment.oc1..aaa..."
compartment_name = "meu-compartment"
region           = "sa-saopaulo-1"

# Function images (uma por função)
api_handler_image = "gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/api-handler:0.0.5"
api_facade_image  = "gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/func-api-facade:0.0.2"
rest_proxy_image  = "gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/func-rr-rest-proxy:0.0.14"
```

### 5.2 Variáveis opcionais

```hcl
# Observabilidade (habilitados por default)
enable_logging              = true
enable_monitoring_alarms    = true
alarm_duration_threshold_ms = 25000

# JWT Authentication (desabilitado por default)
jwt_auth_enabled = false
jwt_issuers      = ["https://identity.oraclecloud.com/"]
jwt_audiences    = ["https://minha-api.example.com"]
jwt_jwks_uri     = "https://idcs-<id>.identity.oraclecloud.com/admin/v1/SigningCert/jwk"

# Network Security Groups (habilitado por default)
use_nsg = true
```

> ⚠️ **Nunca** commite `terraform.tfvars` no git.

### 5.3 Executar Terraform

```bash
# Download de providers
terraform init

# Validar configuração
terraform validate

# Preview (não altera nada)
terraform plan -var-file="terraform.tfvars"

# Aplicar (cria infraestrutura)
terraform apply -var-file="terraform.tfvars"
```

---

## 6. Verificar o Deploy

### Health check

```bash
curl $(terraform output -raw health_check_url)
# → {"status": "healthy", "environment": "dev"}
```

### Testar endpoints

```bash
BASE_URL=$(terraform output -raw api_base_url)

# Hello (GET)
curl "$BASE_URL/hello"

# Secret (POST) — API Facade
curl -X POST "$BASE_URL/secret" \
  -H "Content-Type: application/json" \
  -d '{"resource_id": "ocid1.secret.oc1..."}'

# Store Create (POST) — REST Proxy
curl -X POST "$BASE_URL/store/create" \
  -H "Content-Type: application/json" \
  -d '{"store_id": "1001", "store_name": "Loja Centro"}'
```

### Ativar Application Logs — Passo Manual Obrigatório

> **Por que manual?** O provider Terraform OCI não suporta configurar o log de stdout das Applications via HCL. Este passo é feito **uma única vez por Application**, via OCI Console.

**1. Obter o Log Group provisionado pelo Terraform:**

```bash
terraform output -raw log_group_id
```

**2. OCI Console → Developer Services → Functions → Applications**

**3. Repetir para cada uma das 3 Applications** (`api-handler`, `func-api-facade`, `rest-proxy`):

| Passo | Ação |
|-------|------|
| Clique na Application | |
| Menu lateral → **Logs** | |
| Linha **"Function Invoke Log"** → toggle **Disabled** | Abre painel de configuração |
| **Log Group** | Selecionar `log-group-serverless-poc-dev` |
| **Log Name** | `fn-invoke-<nome-da-app>-stdout` |
| **Retention** | 30 days |
| Clicar em **Enable Log** | |

**4. Verificar captura de logs:**

Após 2-3 minutos, dispare uma invocação e pesquise:

```bash
# Disparar invocação
curl $(terraform output -raw api_base_url)/hello
```

OCI Console → **Observability & Management → Logging → Search**
- Log Group: `log-group-serverless-poc-dev`
- Time range: Last 15 minutes

Confirmar campos JSON presentes: `level`, `message`, `coldStart`, `traceId`.

### Ver outputs completos

```bash
terraform output
```

---

## 7. Adicionar Nova Function — Passo a Passo Manual

### Passo 1 — Criar o código Java

Crie o diretório da function seguindo a estrutura padrão:

```bash
mkdir -p services/minha-func/src/main/java/com/brx/functions/minhafunc
mkdir -p services/minha-func/src/test/java/com/brx/functions/minhafunc
```

#### Handler mínimo (`src/main/java/.../MinhaFuncFunction.java`)

```java
package com.brx.functions.minhafunc;

import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;

public class MinhaFuncFunction {

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

#### `func.yaml`

```yaml
schema_version: 20180708
name: minha-func
version: 0.0.1
runtime: java
build_image: fnproject/fn-java-fdk-build:jdk17-latest
run_image: fnproject/fn-java-fdk:jre17-latest
cmd: com.brx.functions.minhafunc.MinhaFuncFunction::handler
memory: 256
timeout: 60
```

#### `pom.xml` (dependências essenciais)

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

> Consultar `services/api-handler/` para exemplo completo com OCI SDK, fn-events, Dockerfile e testes.

#### `Dockerfile`

```dockerfile
FROM fnproject/fn-java-fdk-build:jdk17-latest AS build
WORKDIR /function
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

FROM fnproject/fn-java-fdk:jre17-latest
WORKDIR /function
COPY --from=build /function/target/libs/* /function/libs/
COPY --from=build /function/target/*.jar /function/app/
CMD ["com.brx.functions.minhafunc.MinhaFuncFunction::handler"]
```

### Passo 2 — Build e Push da imagem

```bash
cd services/minha-func
mvn clean package
docker build -t gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/minha-func:0.0.1 .
docker push gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/minha-func:0.0.1
```

### Passo 3 — Adicionar módulo Terraform

Em `infra/environments/dev/apps.tf`, adicionar:

```hcl
module "app_minha_func" {
  source = "../../modules/function-app"

  compartment_ocid   = var.compartment_ocid
  subnet_id          = module.network.subnet_private_id
  nsg_ids            = var.use_nsg ? [module.network.nsg_functions_id] : []
  application_name   = "app-minha-func"
  function_name      = "minha-func"
  function_image     = var.minha_func_image
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

### Passo 4 — Adicionar rota no API Gateway

No mesmo `apps.tf`, adicionar entrada no `route_backends` do `module "api_gateway"`:

```hcl
route_backends = [
  # ... rotas existentes ...
  {
    path        = "/minha-rota"
    methods     = ["GET", "POST"]
    function_id = module.app_minha_func.function_id
    auth_type   = "ANONYMOUS"
  },
]
```

### Passo 5 — Adicionar variável de imagem

Em `infra/environments/dev/variables.tf`:

```hcl
variable "minha_func_image" {
  type        = string
  description = "OCIR image URI for minha-func"
}
```

Em `terraform.tfvars`:

```hcl
minha_func_image = "gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/minha-func:0.0.1"
```

### Passo 6 — Aplicar

```bash
cd infra/environments/dev
terraform validate
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

### Passo 7 — Testar

```bash
curl $(terraform output -raw api_base_url)/minha-rota
```

### Checklist — Nova Function

- [ ] Código criado (`pom.xml`, `func.yaml`, `Dockerfile`, handler Java)
- [ ] Testes executados (`mvn test`)
- [ ] Imagem Docker buildada e pushada no OCIR
- [ ] `module "app_<name>"` adicionado em `apps.tf`
- [ ] Rota adicionada em `route_backends`
- [ ] Variável de imagem em `variables.tf` e `terraform.tfvars`
- [ ] `terraform apply` com sucesso
- [ ] Endpoint testado e respondendo

---

## 8. Adicionar Nova Function — Com Agents/Comandos Claude Code

O projeto tem **agents e comandos (skills) especializados** do Claude Code que automatizam a criação de
functions. Use-os para acelerar o processo. Para o mapa completo de agents/comandos, veja o **CLAUDE.md**
(tabela de roteamento) e **[docs/PROMPTS-GUIDE.md](docs/PROMPTS-GUIDE.md)**.

### Fluxo rápido — End-to-end (Java + Terraform + Rota)

```
@oci-serverless-stack /add-serverless-stack
```

Parâmetros que serão solicitados:
- Function name (ex: `minha-func`)
- API routes (ex: `/minha-rota` GET+POST)
- Authentication (ANONYMOUS / JWT)
- Docker image URI
- Memory / Timeout

Resultado: cria código Java + módulo Terraform + rota no API Gateway em uma única execução.

### Fluxo — Só o código Java

```
@oci-functions-java /add-oci-function
```

Cria scaffold completo (handler, pom.xml, func.yaml, Dockerfile, testes) sem alterar infraestrutura.

### Fluxo — Só a infraestrutura Terraform

```
@oci-terraform /add-functions-infra
```

Cria módulo function-app + variáveis + rota no API Gateway sem criar código Java.

### Fluxo — Adicionar function a app existente

```
@oci-serverless-stack /add-function-to-app
```

Registra uma nova function em uma Application existente e configura a rota no API Gateway.

### Exemplo de uso completo

```
1. Invocar: @oci-serverless-stack /add-serverless-stack
2. Informar: Function name = "func-order-processor"
3. Informar: Routes = POST /orders, GET /orders/{id}
4. Informar: Auth = JWT (AUTHENTICATION_ONLY)
5. Informar: Memory = 512MB, Timeout = 120s
6. Aguardar: Agent cria código + infra + testes
7. Executar: ./build-push.sh && terraform apply
```

> Para o catálogo completo de agents e comandos Claude Code, consulte **[docs/PROMPTS-GUIDE.md](docs/PROMPTS-GUIDE.md)**.

---

## 9. Operações do Dia-a-Dia

### Atualizar Function (nova versão)

1. Build e push da nova tag da imagem
2. Alterar `*_image` em `terraform.tfvars`
3. `terraform apply -var-file="terraform.tfvars"`

### Habilitar JWT Authentication

```hcl
# Em terraform.tfvars
jwt_auth_enabled = true
jwt_issuers      = ["https://identity.oraclecloud.com/"]
jwt_audiences    = ["https://minha-api.example.com"]
jwt_jwks_uri     = "https://idcs-<id>.identity.oraclecloud.com/admin/v1/SigningCert/jwk"
```

```bash
terraform apply -var-file="terraform.tfvars"
```

> O health check (`/health`) permanece público mesmo com JWT habilitado.

### Configurar Notification Subscriptions

O módulo cria o Notification Topic mas **não cria subscriptions**:

```bash
# Email
oci ons subscription create \
  --compartment-id <compartment_ocid> \
  --topic-id $(terraform output -raw notification_topic_id) \
  --protocol EMAIL \
  --endpoint "equipe@empresa.com"

# Webhook (Slack/PagerDuty)
oci ons subscription create \
  --compartment-id <compartment_ocid> \
  --topic-id $(terraform output -raw notification_topic_id) \
  --protocol HTTPS \
  --endpoint "https://hooks.slack.com/services/..."
```

### Destruir infraestrutura (terraform destroy)

```bash
cd infra/environments/dev
terraform destroy -var-file="terraform.tfvars"
```

> ⚠️ Se `terraform destroy` falhar parcialmente (state desatualizado, timeout, recursos órfãos), use o script de cleanup via OCI CLI como fallback:

```bash
# Verificar o que existe (sem deletar)
./scripts/oci-cleanup.sh --dry-run

# Executar limpeza completa
./scripts/oci-cleanup.sh
```

O script descobre e remove recursos via OCI CLI respeitando a ordem de dependências. Requer `jq` instalado e sessão OCI válida (profile `poc`, auth `security_token`). Renovar sessão se expirada:

```bash
oci session authenticate --profile poc
```

### Executar testes de infraestrutura

```bash
cd infra
bash tests/run_structural_tests.sh
bash tests/run_tests.sh
```
