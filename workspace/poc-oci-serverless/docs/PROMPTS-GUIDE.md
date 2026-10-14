# Guia de Agents, Comandos e Skills

> Referência completa do ecossistema de automação **Claude Code** para este projeto.
> Consulte este documento para saber qual agent/comando usar em cada situação.
> (Os comandos `/<nome>` são skills com `context: fork` que invocam o agent indicado.)

---

## Sumário

- [Visão Geral](#visão-geral)
- [Agents Disponíveis](#agents-disponíveis)
- [Decision Tree — Qual Agent/Prompt Usar?](#decision-tree--qual-agentprompt-usar)
- [Catálogo de Prompts](#catálogo-de-prompts)
- [Skills Disponíveis](#skills-disponíveis)
- [Guia de Uso — Workflows Comuns](#guia-de-uso--workflows-comuns)
- [Sequência de Prompts por Padrão](#sequência-de-prompts-por-padrão)
- [Matriz de Cobertura: Padrões × Prompts](#matriz-de-cobertura-padrões--prompts)

---

## Visão Geral

O projeto utiliza 3 camadas de automação:

| Camada | O que é | Quantidade |
|--------|---------|:----------:|
| **Agents** | Agentes especializados com workflows completos (P0-P5/P6) | 7 |
| **Comandos** | Slash commands em `.claude/commands/` (`context: fork` + `background: false`) que coletam parâmetros e invocam agents | 46 |
| **Skills** | Knowledge-skills domain-specific carregadas sob demanda | 44 |

> **Fonte da verdade do catálogo completo de comandos:** [`.claude/AGENTS.md`](../.claude/AGENTS.md). Este guia foca no mapeamento **padrão × comando** e nos workflows; a lista bruta de comandos é mantida no AGENTS.md. As seções abaixo cobrem os comandos mais usados por padrão — consulte o AGENTS.md para o catálogo integral (observabilidade, connector-hub, APM, testes, deploy/debug etc.).

**Fluxo típico:**

```
Usuário → invoca /<comando> → coleta parâmetros → roteia para @agent → agent carrega skills → executa workflow
```

---

## Agents Disponíveis

| Agent | Descrição | Quando usar |
|-------|-----------|-------------|
| `@oci-terraform` | OCI Infrastructure Provisioner — Terraform P0-P5 workflow | Provisionar/modificar infra OCI |
| `@oci-functions-java` | OCI Functions Java Developer — FDK v1.1.x P0-P5 workflow | Criar/modificar Java functions |
| `@oci-serverless-architect` | OCI Serverless Solution Architect — advisory only P0-P6 | Design reviews, auditorias, ADRs |
| `@oci-serverless-stack` | Full-Stack Serverless Deployer — orquestra Java + Terraform | End-to-end function + infra + routes |
| `@oci-observability` | OCI Observability Engineer — APM/tracing, Logging, Alarms, Connector Hub, Dashboards | Provisionar/validar observabilidade |
| `@oci-deployer` | OCI Function Deployer — build, push, deploy, validate P0-P6 | Deploy iterations em infra existente |
| `@oci-debugger` | OCI Function Debugger — diagnostic por HTTP status P0-P4 | Diagnosticar 502/503/504/500 em runtime |

---

## Decision Tree — Qual Agent/Prompt Usar?

```
Precisa de...
├── Nova function Java?
│   ├── Só o código Java → @oci-functions-java + /add-oci-function
│   ├── Só a infra Terraform → @oci-terraform + /add-functions-infra
│   └── Ambos (end-to-end) → @oci-serverless-stack + /add-serverless-stack
│
├── Adicionar function a app existente?
│   └── @oci-serverless-stack + /add-function-to-app
│
├── Provisionar infra (sem function)?
│   ├── Networking → @oci-terraform + /add-networking
│   ├── IAM → @oci-terraform + /add-iam
│   ├── API Gateway → @oci-terraform + /add-api-gateway
│   ├── Vault → @oci-terraform + /add-vault
│   ├── Streaming → @oci-terraform + /add-streaming
│   └── Events → @oci-terraform + /add-event-rule
│
├── Adicionar capacidade a function existente?
│   ├── Object Storage → @oci-functions-java + /add-object-storage
│   ├── REST client → @oci-functions-java + /add-rest-client
│   ├── Event handler → @oci-functions-java + /add-event-handler
│   └── Event publishing → @oci-functions-java + /add-event-publishing
│
├── Architecture review / design?
│   ├── Full architecture → @oci-serverless-architect + /design-serverless-architecture
│   ├── API Gateway strategy → @oci-serverless-architect + /design-api-gateway
│   ├── Networking → @oci-serverless-architect + /design-networking
│   └── Vault/Security → @oci-serverless-architect + /design-vault-security
│
├── Executar um pattern spec?
│   └── @oci-serverless-stack + /execute-pattern
│
├── Deploy nova versão (build + push + terraform + test)?
│   └── @oci-deployer
│
├── Diagnosticar erro em function deployed (502/503/504)?
│   └── @oci-debugger
│
└── Auditar infra vs docs?
    └── @oci-serverless-architect + /audit-infra-prerequisites
```

---

## Catálogo de Prompts

### Entry Points (Genéricos)

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/provision-infra` | oci-terraform | Entry point genérico — coleta o que provisionar e roteia |
| `/develop-function` | oci-functions-java | Entry point genérico — coleta tipo de function e roteia |
| `/add-observability` | oci-observability | Entry point genérico — coleta pilar de observabilidade e roteia |
| `/create-serverless-capability` | oci-serverless-stack | Entry point genérico — coleta function + infra e roteia |

### Infrastructure Provisioning (Terraform)

| Prompt | Descrição | Parâmetros |
|--------|-----------|------------|
| `/add-serverless-stack` | Stack completo (Functions + API GW + IAM) | Function name, routes, auth, image, memory/timeout |
| `/add-functions-infra` | Application + Function resources | Function name, app name, image, memory, timeout, compartment |
| `/add-api-gateway` | Gateway + Deployment + Routes | Routes (path, methods, backend), auth, CORS, rate limit |
| `/add-networking` | VCN + Subnets + NSGs + Gateways | CIDR blocks, subnet types, gateways, NSG rules |
| `/add-iam` | Dynamic Groups + Policies | Resource type, permissions, compartment scope, matching rules |
| `/add-vault` | Vault + Keys + Secrets | Secrets (names, purpose), key algorithm, rotation, consumers |
| `/add-streaming` | Stream Pool + Streams | Stream name, partitions, retention, encryption |
| `/add-event-rule` | Events Rules (automação) | Event type, source, condition filter, target action |
| `/add-function-to-app` | Add function a app existente | Function name, image, routes, memory, timeout, auth type |

### Java Function Development

| Prompt | Descrição | Parâmetros |
|--------|-----------|------------|
| `/add-oci-function` | Scaffold nova function | Function name, handler type (API GW / Event / Scheduled) |
| `/add-event-handler` | Typed event handler (fn-events) | Event source, function class, request/response types, idempotency |
| `/add-event-publishing` | Publicar eventos (Streaming, ONS, Queue) | Target service, function class, message format, volume |
| `/add-object-storage` | Object Storage read/write | Bucket name, operations (read/write), function class, file size |
| `/add-rest-client` | REST API client (HttpClient, OAuth2) | Target API, auth method, function class, HTTP methods, secret OCID |

### Architecture & Design

| Prompt | Descrição | Parâmetros |
|--------|-----------|------------|
| `/design-serverless-architecture` | Design OCI serverless patterns | Scope, components, NFRs, business context |
| `/design-api-gateway` | API Gateway strategy | Endpoints, consumers, auth, rate limiting, CORS, versioning |
| `/design-networking` | Network architecture (VCN, NSGs) | Connectivity, security zones, workload placement, compliance |
| `/design-vault-security` | Vault security design | Secret types, rotation, encryption, consumers, compliance |

### Audit & Orchestration

| Prompt | Descrição | Parâmetros |
|--------|-----------|------------|
| `/design-specification-audit` | Audit infra vs documentation | Infra dir, service dir, docs source, scope |
| `/audit-infra-prerequisites` | Audit pré-reqs de um pattern | Pattern document path, infra directory |
| `/execute-pattern` | Executar pattern spec end-to-end | Pattern document path, environment, OCIR namespace |

### Observabilidade & Instrumentação de Function

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/add-function-logging` | oci-functions-java | Structured logging (SLF4J/Logback) + OCI Logging |
| `/add-function-metrics` | oci-functions-java | Custom metrics via PostMetricData + OCI Monitoring |
| `/add-function-tracing` | oci-functions-java | Distributed tracing OpenTelemetry → OCI APM |
| `/add-function-observability` | oci-functions-java | Bloco de observabilidade completo (logs + metrics + tracing) |
| `/add-function-tests` | oci-functions-java | Unit tests (FnTestingRule, Mockito) |
| `/design-function-observability` | oci-serverless-architect | Design dos 3 pilares de observabilidade |
| `/design-apm-observability` | oci-serverless-architect | Design APM / tracing distribuído |
| `/design-logging` | oci-serverless-architect | Design de logging (topologia, retenção, pipelines) |
| `/design-object-storage` | oci-serverless-architect | Design de bucket / lifecycle / segurança |
| `/design-connector-hub` | oci-serverless-architect | Design de pipelines Connector Hub |
| `/design-monitoring-alarms` | oci-terraform | Alarmes de Monitoring (multi-threshold, supressão) |

### Infraestrutura de Observabilidade (Terraform)

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/add-logging` | oci-terraform | Log Groups + Logs + UMA |
| `/add-object-storage-infra` | oci-terraform | Object Storage buckets + lifecycle |
| `/add-connector-hub` | oci-terraform | Service Connector Hub pipelines |
| `/add-apm-infrastructure` | oci-terraform | APM domains + synthetic monitors |
| `/engineer-terraform-project` | oci-terraform | Governança de projeto & design de módulos |
| `/add-terraform-tests` | oci-terraform | Terraform native tests (`.tftest.hcl`) |

### Operações (Deploy & Debug)

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/deploy-function` | oci-deployer | Build → push → deploy → smoke test (infra existente) |
| `/debug-function` | oci-debugger | Diagnóstico runtime por HTTP status (502/503/504/500) |

> Validação ao vivo de observabilidade (4 pilares): skill `validating-oci-observability` (scripts em `.claude/skills/validating-oci-observability/scripts/`).

---

## Skills Disponíveis

### Architecture & Design (4)

| Skill | Quando é carregada |
|-------|--------------------|
| `architecting-oci-serverless` | Ao discutir arquitetura serverless, design de patterns |
| `designing-oci-api-gateway` | Ao planejar rotas, autenticação, rate limiting do API Gateway |
| `designing-oci-networking` | Ao projetar VCN, subnets, NSGs, conectividade |
| `designing-oci-vault-security` | Ao planejar secrets, encryption, key rotation |

### Java Functions Development (6)

| Skill | Quando é carregada |
|-------|--------------------|
| `developing-oci-functions-java` | Ao criar/modificar handlers com FDK |
| `implementing-oci-functions-events` | Ao implementar event handlers (fn-events) |
| `integrating-oci-functions-objectstorage` | Ao integrar com Object Storage |
| `invoking-rest-apis-from-oci-functions` | Ao chamar REST APIs externas/OCI |
| `publishing-events-from-oci-functions` | Ao publicar eventos (Streaming, ONS, Queue) |
| `testing-oci-functions-java` | Ao escrever unit tests (FnTestingRule, Mockito) |

### Terraform Provisioning (8)

| Skill | Quando é carregada |
|-------|--------------------|
| `provisioning-oci-functions` | Ao provisionar Application + Function |
| `provisioning-oci-api-gateway` | Ao provisionar Gateway + Deployment + Routes |
| `provisioning-oci-iam` | Ao provisionar Dynamic Groups + Policies |
| `provisioning-oci-networking` | Ao provisionar VCN + Subnets + NSGs |
| `provisioning-oci-vault` | Ao provisionar Vault + Keys + Secrets |
| `provisioning-oci-streaming` | Ao provisionar Stream Pool + Streams |
| `provisioning-oci-events` | Ao provisionar Events Rules |
| `provisioning-oci-serverless-stack` | Ao provisionar stack integrado |

### Terraform Operations (3)

| Skill | Quando é carregada |
|-------|--------------------|
| `managing-terraform-state` | Ao lidar com state, import, moved blocks |
| `managing-terraform-cicd` | Ao configurar pipelines CI/CD |
| `testing-terraform-modules` | Ao escrever terraform test (`.tftest.hcl`) |

---

## Guia de Uso — Workflows Comuns

### Workflow 1 — Criar function end-to-end (Java + Terraform + Rota)

```
1. @oci-serverless-stack /add-serverless-stack
2. Informar: function name, routes, auth type, memory, timeout
3. Agent cria:
   - services/<func-name>/ (Java scaffold completo)
   - infra/environments/dev/apps.tf (module instance)
   - Rota no route_backends do API Gateway
   - Variável de imagem
4. Você executa: ./build-push.sh && terraform apply
```

### Workflow 2 — Adicionar capacidade a function existente

```
1. @oci-functions-java /add-rest-client   (ou /add-object-storage, /add-event-publishing)
2. Informar: target API, auth method, function class existente
3. Agent adiciona:
   - Client class com HttpClient/OCI SDK
   - Configuração de secrets (se OAuth2)
   - Testes unitários
```

### Workflow 3 — Executar um pattern spec completo

```
1. @oci-serverless-architect /audit-infra-prerequisites
   → Informar: path do pattern doc (ex: docs/patterns/01-request-reply/01b-request-reply-database.md)
   → Verifica módulos necessários, identifica gaps

2. @oci-serverless-stack /execute-pattern
   → Informar: pattern doc path, environment (dev), OCIR namespace
   → Executa a sequência de prompts definida na seção 5 do pattern
```

### Workflow 4 — Deploy de nova versão

```
1. @oci-deployer
2. Informar: function name, nova tag
3. Agent executa:
   - Preflight check (scripts/preflight.sh)
   - mvn clean package
   - docker build + push
   - terraform apply
   - curl health check
```

### Workflow 5 — Diagnosticar erro em runtime

```
1. @oci-debugger
2. Informar: HTTP status (502/503/504), function name, endpoint
3. Agent executa diagnóstico P0-P4:
   - P0: Verifica se function existe e está deployada
   - P1: Verifica logs de invocação
   - P2: Verifica timeout/memory
   - P3: Verifica conectividade de rede
   - P4: Verifica código (initError, cold start failure)
```

---

## Sequência de Prompts por Padrão

### Convenção

- **Prompt 0** (obrigatório): Todo padrão DEVE iniciar com `/audit-infra-prerequisites` antes de qualquer implementação
- Se o Prompt 0 identificar gaps (módulos faltantes), resolver antes de avançar
- Os prompts são executados na ordem indicada, respeitando dependências

### Fase 0 — Referência

#### Padrão 03 — API Facade

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc: `docs/patterns/03-api-facade/03-api-facade.md` | — |
| 1 | `/add-serverless-stack` | Function: `func-api-facade`, Routes: `/hello` GET+POST, `/secret` POST, `/store` POST, 256MB/60s | — |
| 2 | `/add-oci-function` → `/add-object-storage` → `/add-rest-client` | Scaffold + Object Storage + Vault secrets | 1 |
| 3 | `/add-event-handler` | API Gateway, `ApiFacadeFunction`, `ApiFacadeRequest`/`ApiFacadeResponse` | 2 |
| 4 | Testes | Mock `ObjectStorageClient` + `SecretsClient`, 6 cenários | 3 |
| 5 | Observabilidade | `func-api-facade`, latência P95 25s | 1 |

### Fase 1 — Fundações

#### Padrão 01a — Request-Reply: REST Proxy

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc: `docs/patterns/01-request-reply/01a-request-reply-rest-proxy.md` | — |
| 1 | `/add-serverless-stack` | Function: `func-rr-rest-proxy`, Route: `POST /proxy`, 256MB/60s | — |
| 2 | `/add-oci-function` → `/add-rest-client` | Scaffold + HttpClient OAuth2, Target: `PROXY_TARGET_BASE_URL` | 1 |
| 3 | `/add-event-handler` | API Gateway, `RestProxyFunction`, `RestProxyRequest`/`RestProxyResponse` | 2 |
| 4 | Testes | Mock `HttpClient`, `RestProxyClient` isolado | 3 |
| 5 | Observabilidade | `func-rr-rest-proxy` | 1 |

#### Padrão 01b — Request-Reply: Database

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc | — |
| 1 | `/add-serverless-stack` | Functions: ORDS (256MB) + JDBC (512MB), Routes: `/database/ords` + `/database/jdbc` | — |
| 2a | `/add-oci-function` → `/add-rest-client` | ORDS: HttpClient OAuth2 | 1 |
| 2b | `/add-oci-function` | JDBC: UCP pool, mTLS wallet, `PreparedStatement` | 1 |
| 3 | `/add-event-handler` | Handlers para ambos | 2a, 2b |
| 4 | Testes | Mock `HttpClient` (ORDS) / `DataSource` (JDBC) | 3 |
| 5 | `/add-vault` | Secrets: DB credentials, wallet | 1 |

#### Padrão 07 — Scatter-Gather

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc | — |
| 1 | `/add-oci-function` + `/add-rest-client` + free-text | `ParallelHttpClient` (`CompletableFuture.allOf`) | — |
| 2 | `/add-event-handler` | `ScatterGatherFunction`, `SGRequest`/`SGResponse` | 1 |
| 3 | Testes | `ParallelHttpClient` isolado, partial-success | 1 |
| 4 | `/add-serverless-stack` | `func-scatter-gather`, `/aggregate/{resource}` GET+POST, 512MB/120s | — |

#### Padrão 08 — Circuit Breaker

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc | — |
| 1 | `/add-oci-function` + free-text | `CircuitBreaker.java` state machine (pattern-specific) | — |
| 2 | `/add-rest-client` → `/add-event-handler` | `BackendClient` + `CircuitBreakerFunction`, `X-Circuit-State` header | 1 |
| 3 | Testes | State transitions, fallback com `is_fallback: true` | 2 |
| 4 | `/add-serverless-stack` | `func-circuit-breaker`, `/resilient/{path*}`, provisioned_concurrency=1, 256MB/60s | — |

#### Padrão 13 — Zero-Trust (cross-cutting)

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc | — |
| 1 | `/add-api-gateway` | JWT: issuers, audiences, JWKS URI, `/health` anônima | — |
| 2 | `/add-vault` + `/add-iam` | AES-256, rotação 90d, policy Functions → keys | — |
| 3 | `/add-networking` | NSGs: API GW ingress 443, Functions egress SGW + NAT | — |
| 4 | Manual | Auditoria: grep credentials, PII em logs, stack traces | 1-3 |

### Fase 2 — Event-Driven

#### Padrão 01c — Request-Reply: Event Publish

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc | — |
| 1 | `/add-serverless-stack` (×3) + `/add-iam` + `/add-streaming` | 3 Functions + IAM + Stream Pool | — |
| 2 | `/add-oci-function` → `/add-event-publishing` | Streaming: JSON→Base64, partition key | 1 |
| 3 | `/add-oci-function` → `/add-event-publishing` | Queue: JSON direto | 1 |
| 4 | `/add-oci-function` → `/add-event-publishing` | Notification: title + body JSON, < 64KB | 1 |
| 5 | Testes | Mocks StreamClient/QueueClient/ONS | 2-4 |

#### Padrão 02 — Event-Driven Pub-Sub

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc | — |
| 1 | `/add-streaming` + `/add-iam` | Stream pool (private), stream, policies | — |
| 2 | `/add-serverless-stack` (×2) | Producer: 256MB/60s `POST /events` — Consumer: 256MB/120s (SCH) | 1 |
| 3 | `/add-oci-function` → `/add-event-publishing` | Producer: Streaming, correlation_id | 2 |
| 4 | `/add-oci-function` → `/add-event-handler` | Consumer: SCH, batch, idempotency | 2 |
| 5 | Testes | Producer: mock StreamClient — Consumer: batch, dedup | 3, 4 |

#### Padrão 17 — Webhook Fanout

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc | — |
| 1 | `/add-oci-function` + free-text | `HmacValidator` (HMAC-SHA256, constant-time) | — |
| 2 | `/add-event-publishing` → `/add-event-handler` | ONS publisher + `WebhookFanoutFunction` | 1 |
| 3 | Testes | `HmacValidator` + mock `NotificationDataPlaneClient` | 2 |
| 4 | `/add-serverless-stack` + `/add-iam` | `POST /webhook/{event}` (anônima), `use ons-topics` | — |
| 5 | `/add-vault` | Secret: `webhook-hmac-secret` | — |

### Fase 3 — Composição

#### Padrão 11 — BFF

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc | — |
| 1 | `/add-oci-function` → `/add-rest-client` → `/add-event-handler` | Mobile: `func-bff-mobile`, 4 campos | — |
| 2 | `/add-oci-function` → `/add-rest-client` → `/add-event-handler` | Web: `func-bff-web`, 15+ campos | — |
| 3 | Testes (×2) | Mobile: compacto — Web: completo | 1, 2 |
| 4 | `/add-serverless-stack` (×2) + `/add-api-gateway` | Mobile: 256MB/30s `/mobile/*` — Web: 512MB/60s `/web/*` | — |

#### Padrão 06 — Strangler Fig

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc | — |
| 1 | `/add-api-gateway` | Rotas com split de tráfego (weight-based routing) | — |
| 2 | `/add-oci-function` → `/add-rest-client` | Proxy para legacy + nova implementação | 1 |
| 3 | Testes | Validar routing correto baseado em weight/header | 2 |

#### Padrão 04 — Saga Compensation

| # | Prompt | Parâmetros | Dep. |
|---|--------|------------|------|
| 0 | `/audit-infra-prerequisites` | Pattern doc | — |
| 1 | `/add-oci-function` + free-text | `SagaExecutor` (compensação LIFO, state machine) | — |
| 2 | `/add-event-publishing` + `/add-streaming` | Stream para saga events | 1 |
| 3 | `/add-serverless-stack` | `func-saga-orchestrator`, 512MB/120s | — |
| 4 | Testes | State transitions, compensação parcial | 1-2 |

---

## Matriz de Cobertura: Padrões × Prompts

### Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Totalmente coberto pelo prompt |
| ⚠️ | Parcialmente coberto — requer free-text complementar |
| ❌ | Não aplicável |

### Prompts de Infraestrutura

| Prompt | 01a | 01b | 01c | 02 | 03 | 04 | 06 | 07 | 08 | 11 | 13 | 17 |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `/audit-infra-prerequisites` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/add-serverless-stack` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `/add-functions-infra` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `/add-api-gateway` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| `/add-iam` | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `/add-networking` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `/add-vault` | ⚠️ | ✅ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `/add-streaming` | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Prompts de Código Java

| Prompt | 01a | 01b | 01c | 02 | 03 | 04 | 06 | 07 | 08 | 11 | 13 | 17 |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `/add-oci-function` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `/add-event-handler` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `/add-event-publishing` | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `/add-rest-client` | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ⚠️ | ✅ | ✅ | ❌ | ❌ |
| `/add-object-storage` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Prompts de Design

| Prompt | Aplicável a |
|--------|-------------|
| `/design-serverless-architecture` | Todos — revisão de arquitetura antes de implementar |
| `/design-api-gateway` | 01a, 01b, 01c, 02, 03, 06, 07, 08, 11, 17 — qualquer padrão com rotas API |
| `/design-networking` | 13 — Zero-Trust (NSGs), qualquer novo VCN/subnet |
| `/design-vault-security` | 01a, 01b, 03, 13, 17 — padrões com secrets/encryption |

### Lógica Pattern-Specific (requer free-text)

Estes componentes NÃO são cobertos por prompts genéricos. A seção 5 de cada pattern spec mantém free-text:

| Padrão | Componente | Motivo |
|--------|-----------|--------|
| 04 — Saga | `SagaExecutor` | Engine com compensação LIFO, state machine |
| 07 — Scatter-Gather | `ParallelHttpClient` | `CompletableFuture.allOf()` + `sendAsync()` paralelo |
| 08 — Circuit Breaker | `CircuitBreaker` | State machine CLOSED/OPEN/HALF_OPEN com `AtomicReference` |
| 17 — Webhook Fanout | `HmacValidator` | HMAC-SHA256 com constant-time comparison |

---

## Notas

1. `/audit-infra-prerequisites` é **obrigatório como Prompt 0** em todos os padrões
2. `/add-vault` marcado ⚠️ em 01a e 03 porque depende do resultado da auditoria
3. `/add-event-rule` não é usado por nenhum padrão atual — útil para automação OCI events
4. `/add-rest-client` no padrão 07 é ⚠️ porque o `ParallelHttpClient` estende com chamadas assíncronas
5. Para padrão 13 (Zero-Trust), prompts são de **hardening** da infra existente, não criação Java
