# Agente: framework-researcher

> **Modelo:** `opus` | **Tools:** Read, Grep, Glob, WebSearch, WebFetch, Write
> **Papel:** Senior Technical Researcher — constrói bases de conhecimento validadas contra documentação oficial, livres de alucinações, com version absolutism rigoroso.

**O que faz:** Pesquisa tecnologias, frameworks, domínios de negócio, arquiteturas e metodologias. Cada claim é vinculado a uma fonte oficial datada. Nunca gera conteúdo de memória.

**O que NÃO faz:** Gerar SKILL.md, auditar arquitetura, validar qualidade, modificar arquivos de projeto.

**Output sempre:** Um arquivo `research_<Nome>_v<Versão>.md` com seções padronizadas prontas para passar por um compiler.

---

## /researching-technical-frameworks

> **Agente:** `framework-researcher` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use quando precisar de uma base de conhecimento validada para qualquer tecnologia de software — linguagens, frameworks, bibliotecas, SDKs, ferramentas de CI/CD.

**Palavras-gatilho:** "pesquisar FastAPI", "research Redis", "documentação oficial de Next.js", "base de conhecimento para Spring Boot".

### Pré-condições

Nenhuma — é o ponto de entrada do pipeline de pesquisa.

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Nome da tecnologia | ✅ | `FastAPI`, `Redis`, `Spring Boot 3` |
| Versão específica | ✅ | `0.115`, `7.2.4`, `3.2.x` |
| URL oficial (se conhecido) | Opcional | `https://fastapi.tiangolo.com/` |
| Parceiros de integração | Opcional | `PostgreSQL, pytest, Docker` |

> **Version Absolutism:** "FastAPI" não é suficiente — fornecer "FastAPI 0.115". Sem versão específica, o agente pedirá antes de continuar.

### Exemplo de Chamada

```
/researching-technical-frameworks FastAPI 0.115
```

O agente vai processar com:
```
Tecnologia: FastAPI
Versão: 0.115
URL oficial: https://fastapi.tiangolo.com/
Parceiros: PostgreSQL, pytest, Pydantic v2, Docker
```

### Output Produzido

```
StoryBeat/research_FastAPI_v0.115.md
```

Seções principais do arquivo gerado:
- `## Version_Context` — changelog, breaking changes vs versão anterior
- `## Mandatory_Patterns (✅ Always Do)` — padrões obrigatórios com código validado
- `## Conditional_Patterns (⚠️ Ask First)` — decisões com trade-offs documentados
- `## Forbidden_Patterns (🚫 Never Do)` — anti-padrões com alternativas corretas
- `## Ecosystem_Interoperability` — integrações testadas com parceiros
- `## Verification_Commands` — comandos para verificar a instalação
- `## Source_Bibliography` — todas as fontes com URL + data de acesso

### Verificação Pós-Pesquisa

```bash
grep -E "^## (Mandatory_Patterns|Conditional_Patterns|Forbidden_Patterns|Source_Bibliography)" research_*.md
grep -c "✅" research_FastAPI_v0.115.md   # deve ter ≥ 3
grep -c "🚫" research_FastAPI_v0.115.md   # deve ter ≥ 2
```

### Próximos Passos

- Tecnologia genérica → `/skill-creator StoryBeat/research_FastAPI_v0.115.md`
- Metodologia → `/methodologies-skill-generator`
- Arquitetura → `/architecture-approaches-skill-generator`
- Terraform → `/terraform-instructions-compiler`

---

## /technical-framework-researcher-terraform

> **Agente:** `framework-researcher` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use quando quiser criar uma skill de provisionamento de um serviço cloud específico usando Terraform. Cobre resources, data sources, módulos e padrões de IaC.

**Palavras-gatilho:** "Terraform para AWS Lambda", "provisionar OCI Functions", "research AWS S3 provider", "skill de IaC para Azure AKS".

### Pré-condições

Nenhuma — é ponto de entrada para o pipeline de IaC.

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Cloud Provider | ✅ | `AWS`, `OCI`, `Azure`, `GCP` |
| Serviço | ✅ | `Lambda`, `S3`, `Functions`, `AKS` |
| Versão Terraform | ✅ | `1.9`, `1.10` |
| Versão do Provider | ✅ | `aws ~> 5.60`, `oci ~> 6.10` |
| URL oficial (se conhecido) | Opcional | `https://registry.terraform.io/providers/hashicorp/aws/` |
| Usar módulos? | Opcional | `sim — Terraform Registry` |

### Exemplo de Chamada

```
/technical-framework-researcher-terraform
```

O agente vai pedir:
```
Provider: AWS
Serviço: Lambda
Versão Terraform: 1.9
Versão Provider: aws ~> 5.60
Usar módulos: sim (terraform-aws-modules/lambda)
```

### Output Produzido

```
StoryBeat/research_AWS_Lambda_aws5.60.md
```

Seções adicionais específicas de IaC:
- Resources e data sources disponíveis (`aws_lambda_function`, `aws_lambda_alias`, etc.)
- Argumentos obrigatórios vs opcionais com tipos
- Padrões de módulo recomendados
- State management e lifecycle rules
- Exemplos de `terraform.tfvars`

### Próximos Passos

- Gerar skill de provisionamento → `/skill-creator StoryBeat/research_AWS_Lambda_aws5.60.md`

> **Quando usar este vs. `/terraform-engineering-best-practices-researcher`:**
> Este pesquisa **um serviço específico** (ex: Lambda, S3). O outro pesquisa **a estrutura geral do projeto** Terraform (módulos, CI/CD, state, testes) — use os dois de forma complementar.

---

## /cloud-architecture-researcher

> **Agente:** `framework-researcher` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use quando precisar de uma base de conhecimento sobre os frameworks de arquitetura dos cloud providers: AWS Well-Architected, Azure CAF, GCP Architecture Framework, OCI Best Practices.

**Palavras-gatilho:** "pilares do Well-Architected", "Azure CAF security", "GCP reliability patterns", "OCI architecture best practices".

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Cloud Provider | ✅ | `AWS`, `Azure`, `GCP`, `OCI` |
| Domínio / Pilar | ✅ | `Security`, `Reliability`, `Cost Optimization` |
| Edição do framework | ✅ | `2024`, `v4.0` |
| Contexto | Opcional | `microserviços em Kubernetes` |

### Exemplo de Chamada

```
/cloud-architecture-researcher
```

```
Provider: AWS
Domínio: Security
Edição: 2024
Contexto: workloads serverless
```

### Output Produzido

```
StoryBeat/research_cloud_AWS_Security_2024.md
```

---

## /business-domain-researcher

> **Agente:** `framework-researcher` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use quando precisar de conhecimento estruturado sobre um domínio organizacional — processos, vocabulário, regulamentações, sistemas de suporte.

**Palavras-gatilho:** "domínio de Finance", "processos de RH", "regulamentação de Compliance LGPD", "domínio de Supply Chain".

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Domínio | ✅ | `Finance`, `Legal`, `HR`, `Compliance`, `Supply Chain` |
| Contexto organizacional | ✅ | `banco de varejo`, `fintec B2B`, `e-commerce` |
| URLs regulatórias | Opcional | `https://www.bcb.gov.br/...` |
| Sistemas de suporte | Opcional | `SAP, Salesforce, Workday` |

### Exemplo de Chamada

```
/business-domain-researcher
```

```
Domínio: Finance
Contexto: banco de varejo brasileiro
Regulamentação: BACEN, LGPD
Sistemas: SAP FICO, Salesforce
```

### Output Produzido

```
StoryBeat/research_Finance_banco-de-varejo.md
```

Seções: processos-chave, vocabulário ubíquo (DDD), bounded contexts sugeridos, requisitos regulatórios, stakeholders e SLAs.

---

## /requirements-methodology-researcher

> **Agente:** `framework-researcher` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use quando quiser criar uma skill de práticas de requisitos — user stories, job stories, DoD, critérios de aceitação, e frameworks ágeis.

**Palavras-gatilho:** "user stories Scrum", "SAFe epics", "BDD Gherkin", "Shape Up pitches", "critérios de aceitação INVEST".

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Framework | ✅ | `Scrum`, `SAFe`, `Shape Up`, `Kanban` |
| Tipo de prática / artefato | ✅ | `user stories`, `acceptance criteria`, `DoD` |
| Edição | ✅ | `Scrum Guide 2020`, `SAFe 6.0` |
| Contexto do time | Opcional | `10 pessoas, distribuído, produto SaaS` |

### Exemplo de Chamada

```
/requirements-methodology-researcher
```

```
Framework: Scrum
Prática: user stories + acceptance criteria
Edição: Scrum Guide 2020
Contexto: squad de 8 pessoas, produto mobile, 2 semanas de sprint
```

### Próximos Passos

- `/methodologies-skill-generator` — compila pesquisa em SKILL.md de metodologia

---

## /architecture-methodology-researcher

> **Agente:** `framework-researcher` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use quando quiser criar uma skill sobre uma metodologia de arquitetura de software — notações, frameworks de decisão, padrões estruturais.

**Palavras-gatilho:** "C4 Model", "TOGAF", "DDD", "ADR", "UML", "Event-Driven Architecture", "ArchiMate".

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Metodologia | ✅ | `C4 Model`, `TOGAF`, `DDD`, `ADR`, `UML 2.5` |
| Versão / edição | ✅ | `C4 v4`, `TOGAF 10`, `DDD (Evans 2003)` |
| Contexto de arquitetura | Opcional | `microserviços`, `monólito modular` |
| Nível de abstração | Opcional | `System Context`, `Component`, `Code` |

### Exemplo de Chamada

```
/architecture-methodology-researcher
```

```
Metodologia: C4 Model
Edição: v4 (2024)
Contexto: plataforma de pagamentos com 12 microserviços
Nível: System Context + Container
```

### Próximos Passos

- `/architecture-approaches-skill-generator` — compila pesquisa em SKILL.md de arquitetura

---

## /terraform-engineering-best-practices-researcher

> **Agente:** `framework-researcher` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use quando quiser definir os **padrões de engenharia Terraform para um projeto inteiro** — estrutura de diretórios, módulos, CI/CD, testes, governance, state management. Produz uma única pesquisa de práticas gerais (não repita por serviço).

**Palavras-gatilho:** "estrutura de projeto Terraform", "módulos reutilizáveis", "pipeline CI/CD Terraform", "testes Terratest", "governance IaC".

> **Quando usar este vs. `/technical-framework-researcher-terraform`:**
> Este gera **o arcabouço geral do projeto** (1 por projeto). O outro gera skills de **serviço específico** (ex: `provisioning-aws-s3`, `provisioning-oci-functions`) — use ambos de forma complementar.

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Versão Terraform | ✅ | `1.9`, `1.10` |
| Provider principal | ✅ | `AWS`, `OCI`, `Azure` |
| Tamanho do time | ✅ | `pequeno (1-5)`, `médio (6-20)`, `grande (20+)` |
| Escala do projeto | ✅ | `3 envs, ~50 resources` |
| Ferramentas preferidas | Opcional | `GitHub Actions, Atlantis, Checkov` |
| Requisitos de compliance | Opcional | `SOC2, PCI-DSS` |

### Exemplo de Chamada

```
/terraform-engineering-best-practices-researcher
```

```
Versão Terraform: 1.9
Provider: AWS
Tamanho do time: médio (8 devs)
Escala: 4 envs (dev/staging/prod/dr), ~200 resources
Ferramentas: GitHub Actions + Atlantis
Compliance: SOC2
```

### Output Produzido

```
StoryBeat/research_Terraform_Engineering_Best_Practices_v1.9.md
```

Seções: estrutura de diretórios recomendada, design de módulos, estratégia de environments, state management, pipeline CI/CD, pirâmide de testes, code quality, governance.

### Próximos Passos

- `/terraform-instructions-compiler StoryBeat/research_Terraform_Engineering_Best_Practices_v1.9.md`

---

## Princípios do Agente

**Version Absolutism** — cada pesquisa cobre exatamente uma versão. Pesquisas para versões diferentes são arquivos separados.

**Source Hierarchy:**
1. Documentação oficial / registry (única fonte aceita automaticamente)
2. Blog oficial do projeto
3. Exemplos oficiais
4. Comunidade verificada com data < 12 meses
5. Qualquer outra fonte → rejeitada

**Executable Truth** — todo claim inclui URL + data de acesso. Sem fonte = marcado como "unverified".

---

*Ver [README do manual](README.md) para navegação geral.*
