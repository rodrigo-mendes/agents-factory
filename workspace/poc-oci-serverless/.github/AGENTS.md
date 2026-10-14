# Agents, Skills & Prompts — Catálogo

> Referência completa do ecossistema de customização Copilot para este projeto.

## Agents Disponíveis

| Agent | Descrição | Uso |
|-------|-----------|-----|
| `@oci-terraform` | OCI Infrastructure Provisioner — Terraform P0-P5 workflow | Provisionar/modificar infra OCI |
| `@oci-functions-java` | OCI Functions Java Developer — FDK v1.1.x P0-P5 workflow | Criar/modificar Java functions |
| `@oci-serverless-architect` | OCI Serverless Solution Architect — advisory only P0-P6 | Design reviews, auditorias, ADRs |
| `@oci-serverless-stack` | Full-Stack Serverless Deployer — orquestra Java + Terraform | End-to-end function + infra + routes |
| `@oci-observability` | OCI Observability Engineer — infra + design P0-P5 | APM, logging, alarms, connector-hub, dashboards, validação live |
| `@oci-deployer` | OCI Function Deployer — build, push, deploy, validate P0-P6 | Deploy iterations em infra existente |
| `@oci-debugger` | OCI Function Debugger — diagnostic por HTTP status P0-P4 | Diagnosticar 502/503/504/500 em runtime |

## Handoff Protocol

Todo handoff entre agents passa por **records estruturados** em `docs/handoff/<capability>/` — nunca por prosa. Cada agent **lê** os records existentes na entrada e **escreve** um record na saída. Regras aplicáveis a todas as superfícies (IDE, cloud agent, CLI): [`.github/instructions/handoff-protocol.instructions.md`](instructions/handoff-protocol.instructions.md) (`applyTo: "**"`). Spec completa: [docs/handoff/README.md](../docs/handoff/README.md).

**Dois tipos de record** (campo `kind:` no frontmatter):

| Kind | Escrito por | Consumido por | Conteúdo |
|------|-------------|---------------|----------|
| `work-order` (`stream-{a,b,c}.md`) | `@oci-serverless-architect` | `@oci-serverless-stack` / agents leaf | scope, components, constraints, dependencies, acceptance criteria |
| `report` (`report-*.md`) | `@oci-functions-java`, `@oci-terraform` | `@oci-serverless-stack` | arquivos alterados, OCIDs, validação, acceptance status, next action |
| `report` → `deploy-report.md` | `@oci-deployer` | `@oci-debugger`, user | image tag, smoke HTTP status, OCIDs, outcome |
| `report` → `diagnosis-report.md` | `@oci-debugger` | `@oci-deployer` / `@oci-terraform` | root cause, evidência, fix exato, classificação |

**Mecanismo no Copilot:** delegação programática usa o tool `agent`; transições agent→agent usam o frontmatter nativo `handoffs:` (botões clicáveis no VS Code) definido em cada `.github/agents/*.agent.md`, ou `@`-mention / `/prompt`. Em cloud agent / CLI (sem agents/prompt files), os próprios records são o mecanismo — leia o último record, execute, escreva o próximo e declare a próxima ação em prosa. Skeletons: `docs/handoff/_templates/`.

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
│   ├── Events → @oci-terraform + /add-event-rule
│   └── Object Storage → @oci-terraform + /add-object-storage-infra
│
├── Provisionar observabilidade (infra)?
│   ├── Logging → @oci-observability + /add-logging
│   ├── Connector Hub → @oci-observability + /add-connector-hub
│   ├── APM (tracing/synthetics) → @oci-observability + /add-apm-infrastructure
│   ├── Monitoring alarms → @oci-observability + /design-monitoring-alarms
│   └── APM/custom dashboards → @oci-observability + /add-apm-dashboards
│
├── Adicionar capacidade a function existente?
│   ├── Object Storage → @oci-functions-java + /add-object-storage
│   ├── REST client → @oci-functions-java + /add-rest-client
│   ├── Event handler → @oci-functions-java + /add-event-handler
│   ├── Event publishing → @oci-functions-java + /add-event-publishing
│   ├── Structured logging → @oci-functions-java + /setup-function-logging
│   ├── Custom metrics → @oci-functions-java + /add-function-metrics
│   ├── Distributed tracing → @oci-functions-java + /add-function-tracing
│   ├── Unit & Integration tests → @oci-functions-java + /add-function-tests
│   └── Full observability block → @oci-functions-java + /add-function-observability
│
├── Architecture review / design?
│   ├── Full architecture → @oci-serverless-architect + /design-serverless-architecture
│   ├── API Gateway strategy → @oci-serverless-architect + /design-api-gateway
│   ├── Networking → @oci-serverless-architect + /design-networking
│   ├── Vault/Security → @oci-serverless-architect + /design-vault-security
│   ├── Object Storage → @oci-serverless-architect + /design-object-storage
│   ├── Logging/Observability → @oci-observability + /design-logging
│   ├── Connector Hub → @oci-observability + /design-connector-hub
│   ├── APM/Tracing → @oci-observability + /design-apm-observability
│   ├── APM dashboards → @oci-observability + /design-apm-dashboards
│   ├── Monitoring Alarms → @oci-observability + /design-monitoring-alarms
│   └── Full Observability (3 pillars) → @oci-serverless-architect + /design-function-observability
│
├── Governance (projeto Terraform)?
│   ├── Structure, modules & policy → @oci-terraform + /engineer-terraform-project
│   └── Native integration tests (.tftest.hcl) → @oci-terraform + /add-terraform-tests
│
├── Executar um pattern spec?
│   └── @oci-serverless-stack + /execute-pattern
│
├── Deploy nova versão (build + push + terraform + test)?
│   └── @oci-deployer + /deploy-function
│
├── Diagnosticar erro em function deployed (502/503/504)?
│   └── @oci-debugger + /debug-function
│
└── Auditar infra vs docs?
    └── @oci-serverless-architect + /audit-infra-prerequisites
```

## Prompts Disponíveis (47 total)

### Entry Points (Agents)

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/oci-terraform` | oci-terraform | Entry point genérico Terraform |
| `/oci-functions-java` | oci-functions-java | Entry point genérico Java |
| `/oci-serverless-architect` | oci-serverless-architect | Entry point genérico Architecture |
| `/oci-serverless-stack` | oci-serverless-stack | Entry point genérico Full Stack |
| `/oci-observability` | oci-observability | Entry point genérico Observability (APM, logging, alarms, connector-hub, dashboards) |
| `/add-serverless-stack` | oci-serverless-stack | Stack completo end-to-end (Java + Functions + API GW + IAM) |
| `/add-function-to-app` | oci-serverless-stack | Adicionar function a app existente (modo incremental) |

### Infrastructure Provisioning

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/add-functions-infra` | oci-terraform | Application + Function resources |
| `/add-api-gateway` | oci-terraform | Gateway + Deployment + Routes |
| `/add-networking` | oci-terraform | VCN + Subnets + NSGs + Gateways |
| `/add-iam` | oci-terraform | Dynamic Groups + Policies |
| `/add-vault` | oci-terraform | Vault + Keys + Secrets |
| `/add-streaming` | oci-terraform | Stream Pool + Streams |
| `/add-event-rule` | oci-terraform | Events Rules (automação) |
| `/add-object-storage-infra` | oci-terraform | Object Storage buckets + lifecycle |
| `/engineer-terraform-project` | oci-terraform | Project governance & module design |
| `/add-terraform-tests` | oci-terraform | Declarative Terraform native tests (.tftest.hcl) |

### Observability (Infra + Design)

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/add-logging` | oci-observability | Log Groups + Logs + UMA |
| `/add-connector-hub` | oci-observability | Service Connector Hub pipelines |
| `/add-apm-infrastructure` | oci-observability | APM domains + synthetic monitors |
| `/add-apm-dashboards` | oci-observability | Custom Management Dashboards (+ APM/logging/alarms stack) |
| `/design-logging` | oci-observability | Logging & observability design |
| `/design-connector-hub` | oci-observability | Connector Hub pipeline design |
| `/design-apm-observability` | oci-observability | APM & distributed tracing design |
| `/design-apm-dashboards` | oci-observability | APM dashboard design (widgets, APM QL, IAM) |
| `/design-monitoring-alarms` | oci-observability | Monitoring alarms & alerting |

### Java Function Development

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/add-oci-function` | oci-functions-java | Scaffold nova function |
| `/add-event-handler` | oci-functions-java | Typed event handler (fn-events) |
| `/add-event-publishing` | oci-functions-java | Publicar eventos (Streaming, ONS, Queue) |
| `/add-object-storage` | oci-functions-java | Object Storage read/write |
| `/add-rest-client` | oci-functions-java | REST API client (HttpClient, OAuth2) |
| `/setup-function-logging` | oci-functions-java | Structured logging + OCI Logging |
| `/add-function-metrics` | oci-functions-java | Custom metrics + OCI Monitoring |
| `/add-function-tracing` | oci-functions-java | Distributed tracing + OCI APM OpenTelemetry |
| `/add-function-tests` | oci-functions-java | JUnit 5 testing + Mockito + FnTestingRule |
| `/add-function-observability` | oci-functions-java | Complete three-pillar observability block |

### Architecture & Design

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/design-serverless-architecture` | oci-serverless-architect | Design OCI serverless patterns |
| `/design-api-gateway` | oci-serverless-architect | API Gateway strategy |
| `/design-networking` | oci-serverless-architect | Network architecture (VCN, NSGs) |
| `/design-vault-security` | oci-serverless-architect | Vault security design |
| `/design-object-storage` | oci-serverless-architect | Object Storage architecture |
| `/design-function-observability` | oci-serverless-architect | Full observability (3 pillars, function-level) |

> Observability infra + design prompts (`/add-logging`, `/add-connector-hub`, `/add-apm-infrastructure`, `/add-apm-dashboards`, `/design-logging`, `/design-connector-hub`, `/design-apm-observability`, `/design-apm-dashboards`, `/design-monitoring-alarms`) live under **Observability** above, owned by `@oci-observability`.

### Operations & Deploy

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/deploy-function` | oci-deployer | Build, push, deploy, validate |
| `/debug-function` | oci-debugger | Diagnosticar erros runtime (502/503/504) |

### Audit & Orchestration

| Prompt | Agent | Descrição |
|--------|-------|-----------|
| `/design-specification-audit` | oci-serverless-architect | Audit infra vs documentation |
| `/audit-infra-prerequisites` | oci-serverless-architect | Audit pré-reqs de um pattern |
| `/execute-pattern` | oci-serverless-stack | Executar pattern spec doc |

---

> **Guia completo** com skills, workflows, e exemplos: [docs/PROMPTS-GUIDE.md](../docs/PROMPTS-GUIDE.md)
>
> **Como adicionar functions** (manual e com prompts): [GETTING-STARTED.md](../GETTING-STARTED.md#7-adicionar-nova-function--passo-a-passo-manual)
