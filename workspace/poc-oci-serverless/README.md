# POC OCI Serverless — Functions + API Gateway

Proof of Concept de arquitetura serverless na **Oracle Cloud Infrastructure (OCI)** utilizando **OCI Functions** e **API Gateway**, provisionada com **Terraform** modular.

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| **[docs/onboarding/README.md](docs/onboarding/README.md)** | Onboarding por perfil — trilhas para dev Java e DevOps/infra |
| **[GETTING-STARTED.md](GETTING-STARTED.md)** | Setup do ambiente, build & deploy, como adicionar novas functions |
| **[docs/PROMPTS-GUIDE.md](docs/PROMPTS-GUIDE.md)** | Catálogo de agents/comandos Claude Code e guia de uso |
| **[infra/README.md](infra/README.md)** | Composição dos módulos Terraform, inputs/outputs |
| **[docs/patterns/README.md](docs/patterns/README.md)** | Catálogo de padrões de integração serverless |

## Arquitetura

```
Internet → [API Gateway (subnet pública)] → [Functions (subnet privada)] → OCI Services
                                                                          ↓
                                                              [Vault, Object Storage, DB]
```



### Diagrama de Recursos (Terraform)

```mermaid
architecture-beta
    service client(internet)[Internet]

    group oci(cloud)[OCI Compartment]

    group vcn(cloud)[VCN] in oci
    service igw(internet)[Internet GW] in vcn
    service natgw(internet)[NAT GW] in vcn
    service sgw(internet)[Service GW] in vcn

    group pub(server)[Subnet Publica] in vcn
    service apigw(server)[API Gateway] in pub
    service deploy(server)[API Deployment] in pub

    group priv(server)[Subnet Privada] in vcn
    service fnapp(server)[Functions App] in priv
    service fn(server)[Function Handler] in priv

    group services(cloud)[OCI Services] in oci
    service vault(database)[Vault] in services
    service objst(disk)[Object Storage] in services
    service ocir(database)[OCIR] in services

    client:R -- L:igw
    igw:R -- L:apigw
    apigw:B -- T:deploy
    deploy:R -- L:fn
    fnapp:B -- T:fn
    fn:R -- L:vault
    fn:B -- T:objst
    ocir:T -- B:fnapp
    natgw:T -- B:igw
    sgw:T -- B:natgw
```

> **Detalhes adicionais por módulo Terraform:**
>
> | Módulo | Recursos |
> |---|---|
> | **network** | VCN, Internet/NAT/Service Gateway, Subnet Publica + Privada, Route Tables, Security Lists, NSGs |
> | **iam** | Dynamic Groups (Functions, API Gateway), Policies (FaaS Network, APIGW Invoke, FN Services) |
> | **functions** | Functions Application, múltiplas Functions (Java 17, 256 MB, deploy condicional) |
> | **api-gateway** | Gateway, Deployment (JWT, CORS, Rate Limiting, rotas dinâmicas por function) |
> | **vault** | Vault, KMS Master Key, Secrets, Object Storage Bucket |
> | **observability** | Log Group, Service Logs (invoke, access, execution), Notification Topic, Alarms (errors, duration, throttle, 5xx) |
> | **apm** | APM Domain (free tier), Data Keys (private/public) |

### Diagrama de Sequência — `GET /v1/hello`

```mermaid
sequenceDiagram
    actor Client as Client (curl)
    participant IGW as Internet Gateway
    participant APIGW as API Gateway
    participant DEPLOY as API Deployment<br/>(JWT / CORS / Rate Limit)
    participant NSG_PUB as NSG API Gateway
    participant NSG_PRIV as NSG Functions
    participant FN as Function<br/>api-handler (Java 17)
    participant LOG as OCI Logging
    participant MON as OCI Monitoring

    Client->>+IGW: GET /v1/hello
    Note over IGW: Route Table: 0.0.0.0/0 → IGW<br/>Security List: allow 443

    IGW->>+APIGW: Forward HTTPS request
    APIGW->>+DEPLOY: Match route /hello [GET]

    Note over DEPLOY: 1. Rate Limit check (CLIENT_IP)<br/>2. CORS validation<br/>3. JWT auth (if enabled,<br/>   anonymous allowed)

    DEPLOY->>LOG: Access Log (request metadata)
    DEPLOY->>LOG: Execution Log (routing info)

    DEPLOY->>+NSG_PUB: Egress to Functions subnet :443
    NSG_PUB->>+NSG_PRIV: Ingress from APIGW NSG

    NSG_PRIV->>+FN: Invoke function (ORACLE_FUNCTIONS_BACKEND)

    Note over FN: @FnConfiguration (first call only):<br/>• Read ENVIRONMENT = "dev"<br/>• Initialize OciServiceClient

    Note over FN: handler(req):<br/>1. Extract path from<br/>   APIGatewayRequestEvent<br/>2. Route by path: /hello

    Note over FN: handleHello →<br/>ApiResponse.ok("Hello from OCI<br/>Functions (Java 17)!<br/>Environment: dev")

    FN-->>-NSG_PRIV: APIGatewayResponseEvent JSON
    NSG_PRIV-->>-NSG_PUB: Response
    NSG_PUB-->>-DEPLOY: Response

    DEPLOY->>LOG: Execution Log (response status)

    DEPLOY-->>-APIGW: HTTP 200 OK
    APIGW-->>-IGW: Response
    IGW-->>-Client: {"message":"Hello from OCI Functions<br/>(Java 17)! Environment: dev",<br/>"data":null,"status_code":200}

    FN->>LOG: Invoke Log (function metrics)
    LOG->>MON: Metrics: FunctionInvocationDuration,<br/>FunctionErrors, HttpResponses

    Note over MON: Evaluate alarms:<br/>• FunctionErrors[5m].sum() > 0 ?<br/>• P95 duration > threshold ?<br/>• APIGW 5xx > 5 ?
```

## Tecnologias

| Componente | Tecnologia |
|---|---|
| Compute | OCI Functions (FaaS) — multi-function por Application |
| Roteamento | OCI API Gateway (rotas dinâmicas por função) |
| Linguagem | Java 17 (Amazon Corretto) |
| FDK | Fn Project FDK 1.1.11 (fn-events) |
| OCI SDK | OCI Java SDK 3.86.x |
| IaC | Terraform >= 1.5 (OCI Provider oracle/oci >= 6.0, < 9.0; testado 1.11 / 8.x) |
| Container Registry | OCI Container Registry (OCIR) |
| Autenticação | Resource Principal / JWT / OAuth2 (Client Credentials) |
| Segredos | OCI Vault (KMS) |
| Observabilidade | OCI Logging + Monitoring Alarms |

## Estrutura do Projeto

```
poc-oci-serverless/
├── GETTING-STARTED.md           # Setup, deploy, como adicionar functions
├── docs/
│   ├── onboarding/              # Onboarding por perfil (dev Java / DevOps-infra)
│   ├── PROMPTS-GUIDE.md         # Catálogo de agents/comandos Claude Code
│   └── patterns/                # Padrões de integração serverless
├── infra/                       # Infraestrutura como código (Terraform)
│   ├── modules/                 # Módulos reutilizáveis (cada um com README)
│   │   ├── network/            # VCN, Subnets, Gateways, NSGs
│   │   ├── iam/                # Dynamic Groups + Policies
│   │   ├── function-app/       # 1 Application + 1 Function (per instance)
│   │   ├── api-gateway/        # Gateway + Deployment (JWT, CORS, Rate Limit)
│   │   ├── vault/              # Vault, KMS Keys, Object Storage Bucket
│   │   └── observability/      # Logging + Monitoring Alarms
│   └── environments/            # Composição por ambiente (dev, prod)
├── services/                    # Código das Functions (cada uma com README)
│   ├── api-handler/            # Reference — Health check (Java 17)
│   ├── func-api-facade/        # Pattern 03 — API Facade (Java 17)
│   └── func-rr-rest-proxy/     # Pattern 01a — REST Proxy (Java 17)
└── scripts/                     # Scripts de validação e build
```

### `services/`

Código-fonte das Functions serverless. Cada function tem sua própria **Application isolada** com routing centralizado no API Gateway via `route_backends`.

#### `services/api-handler/` — Reference (Health Check)

Function Java 17 de referência. Smoke test para validar conectividade do API Gateway.

| Route | Método | Descrição |
|---|---|---|
| `/hello` | GET | Health check / smoke test |

> 📖 **[services/api-handler/README.md](services/api-handler/README.md)**

---

#### `services/func-api-facade/` — Pattern 03 (API Facade)

Function Java 17 que implementa o padrão API Facade — camada de transformação integrando serviços OCI (Vault, Object Storage).

| Route | Método | Descrição |
|---|---|---|
| `/hello` | GET | Health check |
| `/secret` | POST | Lê segredo do OCI Vault |
| `/store` | POST | Grava objeto no Object Storage |

Usa **Resource Principal** para autenticação (zero credentials no código).

> 📖 **[services/func-api-facade/README.md](services/func-api-facade/README.md)**

---

#### `services/func-rr-rest-proxy/` — Pattern 01a (REST Proxy)

Function Java 17 que implementa o padrão Request-Reply REST Proxy — bridge entre Oracle RMS (JSON + OAuth2) e BrxServices (XML) para operações de loja.

| Route | Método | Descrição |
|---|---|---|
| `/store/create` | POST | Cria loja via proxy REST (RMS → BrxServices) |
| `/store/update` | POST | Atualiza loja via proxy REST (RMS → BrxServices) |

Usa **Resource Principal** + **OAuth2 Client Credentials** (IDCS) para autenticação. Segredos armazenados no OCI Vault.

> 📖 **[services/func-rr-rest-proxy/README.md](services/func-rr-rest-proxy/README.md)**

## Quick Start

> Guia completo com pré-requisitos, configuração e deploy: **[GETTING-STARTED.md](GETTING-STARTED.md)**

Resumo rápido:

```bash
# 1. Build & push de uma function
cd services/api-handler && ./build-push.sh

# 2. Provisionar infraestrutura
cd infra/environments/dev
terraform init && terraform apply -var-file="terraform.tfvars"

# 3. Testar
curl $(terraform output -raw api_base_url)/hello
```

## Padrões de Integração

O projeto implementa padrões de integração serverless em fases incrementais:

| Fase | Padrão | Serviço | Status |
|---|---|---|---|
| 0 (Reference) | 03 — API Facade | `func-api-facade` | ✅ Implementado |
| 1 (Foundations) | 01a — REST Proxy | `func-rr-rest-proxy` | ✅ Implementado |
| 1 | 01b — Database | — | Planejado |
| 1 | 01c — Event Publish | — | Planejado |
| 2 (Event-Driven) | 02 — Pub/Sub | — | Planejado |
| 3 (Composition) | 04 — Saga | — | Planejado |

> 📖 Catálogo completo: **[docs/patterns/README.md](docs/patterns/README.md)**