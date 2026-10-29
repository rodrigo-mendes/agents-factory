# Agents Factory

Framework sistemático para criação de **Skills, Subagentes e Rules** em **Claude Code**
(`.claude/`, única fonte de verdade) — focado em prevenir alucinações de IA através de pesquisa
validada, versionamento rigoroso e padrões de qualidade. O espelho GitHub Copilot (`.github/`)
pré-migração foi retirado (ver `.claude/MIGRATION.md`); `audit-architecture-*` e
`copilot-compatibility-review` continuam a existir como ferramentas genéricas para auditar
*outros* projetos que tenham `.github/`.

## O que é

O Agents Factory é uma fábrica de artefatos de IA que oferece:

- **226 Skills** (Claude Code) — 67 comandos (`/nome`) e 159 skills de conhecimento (auto-invocáveis), vindas de 32 pacotes APM (ver [Catálogo de pacotes](#catálogo-de-pacotes)). Pesquisa, autoria de skills/agentes/rules, compilação, validação e auditoria — inclui a **família platform-software** (15: orquestradora + 14 irmãs para Kafka, Redis, MongoDB, Postgres…), o **pipeline de livros técnicos** (`book-writing`), os pacotes **Camel Quarkus**, **AWS** (arquitetura + Terraform), **OCI** serverless, **Stripe Java**, **LangChain4j**, o conjunto **Quarkus na AWS Lambda para SaaS** (orquestrador `building-quarkus-aws-saas`, handoff genérico, deploy, observabilidade) e o **orquestrador de pacotes** `building-agent-packages`
- **41 subagentes** e **50 rules** escopadas por caminho (`paths:`)
- **Ficheiros de `assets/`** nas skills que os possuem (`skill-creator`, `agent-creator`, `rules-compiler`, `terraform-instructions-compiler`, `structuring-camel-quarkus-projects`) — não existe mais `.claude/templates/`
- **4 Fluxos Combinados** — Pipelines de ponta-a-ponta

## Início Rápido

### Claude Code (recomendado)

```
/researching-technical-frameworks
```
> Pesquisa a tecnologia com version absolutism, produzindo uma base de conhecimento livre de alucinações.

```
/project-analysis-validator
```
> Análise estrutural e de qualidade de projetos de agente com recomendações priorizadas.

```
/audit-cc-architecture-consensus
```
> Auditoria multi-modelo de projetos Claude Code com relatório de consenso priorizado.

## Estrutura do Repositório

```
.claude/                    ← Claude Code (única fonte de verdade — não há .github/)
├── agents/                 ← 41 subagentes: 5 roteadores (framework-researcher, artifact-author, architecture-auditor, quality-validator, skill-evaluator) + 2 helpers de pesquisa (research-synthesizer, section-investigator) + 13 do pipeline de livros (book-writing) + camel-quarkus-integrator + terraform-rules-author + aws-terraform-engineer + aws-architect + 7 OCI + 2 Stripe + langchain4j-integrator + 6 Quarkus/AWS SaaS (quarkus-lambda-integrator, quarkus-code-reviewer, aws-lambda-deployer, aws-lambda-debugger, aws-observability, spec-synchronizer)
├── skills/                 ← 226 skills (67 comandos + 159 de conhecimento); incl. platform-software (15), Camel Quarkus (12), quarkus-core (4), Quarkus/AWS SaaS (22), AWS (40 + 26 Terraform), OCI, Stripe, LangChain4j e as skills com assets/ próprio
│                              (skill-creator, agent-creator, rules-compiler, terraform-instructions-compiler, structuring-camel-quarkus-projects, …)
├── rules/                  ← 50 rules: 5 da fábrica (agent/rules/skill-frontmatter, naming-conventions, skill-structure) + Camel Quarkus, AWS, OCI, Stripe, LangChain4j e Quarkus/AWS SaaS
└── settings.json          ← GERADO por `apm install --target claude` (exceto settings*.json); edite `packages/`
packages/                   ← fonte de verdade: 32 pacotes APM (ver catálogo abaixo)
```

## Catálogo de pacotes

Contagens reais (`verify_package.py`); a soma bate com `.claude/` (226 skills, 41 agentes, 50 rules).

| Pacote | Skills | Agentes | Rules | Conteúdo |
|---|---|---|---|---|
| `factory-core` | 0 | 0 | 5 | Rules de frontmatter e naming da fábrica |
| `research-core` | 0 | 3 | 0 | framework-researcher + 2 helpers internos |
| `researching-frameworks` | 5 | 0 | 0 | Comandos de pesquisa anti-alucinação (frameworks, cloud, metodologia, domínio) |
| [`researching-platform`](packages/researching-platform/README.md) | 15 | 0 | 0 | Família platform-software (datastores, brokers, gateways) |
| `artifact-authoring` | 5 | 1 | 0 | artifact-author + skill/agent/rule authoring |
| `auditing` | 8 | 1 | 0 | architecture-auditor + auditorias Copilot e Claude Code |
| `validating` | 5 | 1 | 0 | quality-validator + validações |
| `evaluating` | 1 | 1 | 0 | skill-evaluator (LLM-as-judge) |
| [`agent-package-builder`](packages/agent-package-builder/README.md) | 1 | 0 | 0 | `building-agent-packages`: pesquisa → skills → agente/rules → loop de qualidade → commits |
| [`book-writing`](packages/book-writing/README.md) | 10 | 13 | 0 | Pipeline de livros técnicos (EPUB 3.0) |
| `quarkus-core` | 4 | 0 | 1 | Base Quarkus 3.40 LTS (ArC, REST, JUnit) + `refactoring-quarkus-java` + regra de clean code |
| [`camel-quarkus-skills`](packages/camel-quarkus-integrator/README.md) | 10 | 0 | 0 | Camel Quarkus 3.40 LTS, uma skill por extensão (depende de `quarkus-core`) |
| [`camel-quarkus-integrator`](packages/camel-quarkus-integrator/README.md) | 2 | 1 | 3 | Orquestradora + executor camel-quarkus-integrator |
| `terraform` | 5 | 2 | 0 | Pesquisa Terraform, terraform-rules-author, aws-terraform-engineer |
| [`aws-terraform`](packages/aws-terraform/README.md) | 26 | 0 | 3 | `provisioning-aws-<serviço>-v6` (hashicorp/aws 6.x) |
| [`aws-skills`](packages/aws-skills/README.md) | 40 | 0 | 0 | Arquitetura AWS (Well-Architected, serviços) |
| [`aws-architect`](packages/aws-architect/README.md) | 1 | 1 | 2 | Agente consultivo aws-architect + guardrails |
| [`oci-core`](packages/oci-core/README.md) | 1 | 0 | 0 | Perfil OCI do protocolo de handoff genérico (`handoff-core`) |
| [`oci-functions-java`](packages/oci-functions-java/README.md) | 14 | 3 | 17 | OCI Functions Java (FDK 1.1.x, Java 17) |
| [`oci-terraform`](packages/oci-terraform/README.md) | 20 | 1 | 8 | Terraform OCI (oracle/oci) |
| [`oci-observability`](packages/oci-observability/README.md) | 10 | 1 | 1 | APM, Logging, alarmes, Connector Hub, dashboards |
| [`oci-architecture`](packages/oci-architecture/README.md) | 8 | 2 | 2 | Arquitetura serverless OCI |
| [`stripe-java`](packages/stripe-java/README.md) | 6 | 2 | 1 | Stripe Java 34.x (advisor + integrator) |
| [`langchain4j`](packages/langchain4j/README.md) | 3 | 1 | 2 | LangChain4j 1.22.0 chat + streaming com OpenAI e Anthropic |
| [`handoff-core`](packages/handoff-core/README.md) | 3 | 1 | 0 | Protocolo de handoff genérico v1 + scripts, OpenSpec, `spec-synchronizer`, `/syncing-spec-from-code` |
| [`quarkus-aws`](packages/quarkus-aws/README.md) | 11 | 2 | 2 | Quarkus 3.40 na AWS Lambda (HTTP, Cognito, dados, mensageria, testes, logs, traces, métricas) + integrador e revisor |
| [`aws-lambda`](packages/aws-lambda/README.md) | 2 | 2 | 1 | Deploy (só com plan aprovado) e diagnóstico de Lambda, qualquer runtime |
| [`aws-observability`](packages/aws-observability/README.md) | 2 | 1 | 1 | Agente `aws-observability`, `/observe-aws-workload`, validação ao vivo (só leitura) |
| [`quarkus-aws-saas`](packages/quarkus-aws-saas/README.md) | 4 | 0 | 0 | Orquestrador SDD `building-quarkus-aws-saas`, perfil de handoff, Stripe e LangChain4j no Quarkus |

## Documentação

| Seção | Descrição |
|-------|-----------|
| [Visão Geral](docs/visao-geral.md) | Arquitetura do framework com diagramas |
| [Catálogo de Capacidades](docs/capacidades/README.md) | Todas as capacidades listadas e categorizadas |
| [Catálogo de pacotes](#catálogo-de-pacotes) | Os 32 pacotes APM com contagens e READMEs |
| [Família Platform Software](docs/manual/platform-software-family.md) | 15 comandos para pesquisar plataformas auto-hospedadas (Kafka, Redis, Mongo…) |
| [Como Usar](docs/como-usar/README.md) | Guias passo-a-passo por jornada |
| [Fluxos Combinados](docs/fluxos/README.md) | Pipelines de ponta-a-ponta com diagramas |
| [Referência](docs/referencia/convencoes.md) | Convenções, padrões e glossário |

## Pré-requisitos

- Claude Code CLI instalado
- Este repositório clonado

## Princípios

| Princípio | Descrição |
|-----------|-----------|
| **Version Absolutism** | Uma skill = uma versão. Nunca misturar versões. |
| **Three-Tier (✅⚠️🚫)** | Padrões obrigatórios, decisões do usuário, anti-padrões |
| **P0-P5 Workflow** | Todo agente segue: Verify → Analyze → Consult → Propose → Implement → Validate |
| **Anti-Alucinação** | Toda informação validada contra documentação oficial |
