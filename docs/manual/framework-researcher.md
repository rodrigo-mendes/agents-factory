# Agent: framework-researcher

> **Model:** `opus` | **Tools:** Read, Grep, Glob, WebSearch, WebFetch, Write
> **Role:** Senior Technical Researcher — builds knowledge bases validated against official documentation, free of hallucinations, with rigorous version absolutism.

**What it does:** Researches technologies, frameworks, business domains, architectures and methodologies. Every claim is linked to a dated official source. Never generates content from memory.

**What it does NOT do:** Generate SKILL.md, audit architecture, validate quality, modify project files.

**Always outputs:** A file `research_<Name>_v<Version>.md` with standardized sections ready to pass through a compiler.

---

## /researching-technical-frameworks

> **Agent:** `framework-researcher` | **Context:** fork | **Model invocation:** disabled

### When to Use

Use when you need a validated knowledge base for any software technology — languages, frameworks, libraries, SDKs, CI/CD tools.

**Trigger words:** "research FastAPI", "research Redis", "official Next.js documentation", "knowledge base for Spring Boot".

### Prerequisites

None — this is the entry point of the research pipeline.

### Inputs

| Field | Required | Example |
|-------|:-----------:|---------|
| Technology name | ✅ | `FastAPI`, `Redis`, `Spring Boot 3` |
| Specific version | ✅ | `0.115`, `7.2.4`, `3.2.x` |
| Official URL (if known) | Optional | `https://fastapi.tiangolo.com/` |
| Integration partners | Optional | `PostgreSQL, pytest, Docker` |

> **Version Absolutism:** "FastAPI" is not sufficient — provide "FastAPI 0.115". Without a specific version, the agent will ask before continuing.

### Call Example

```
/researching-technical-frameworks FastAPI 0.115
```

The agent will process with:
```
Technology: FastAPI
Version: 0.115
Official URL: https://fastapi.tiangolo.com/
Partners: PostgreSQL, pytest, Pydantic v2, Docker
```

### Output Produced

```
StoryBeat/research_FastAPI_v0.115.md
```

Main sections of the generated file:
- `## Version_Context` — changelog, breaking changes vs previous version
- `## Mandatory_Patterns (✅ Always Do)` — mandatory patterns with validated code
- `## Conditional_Patterns (⚠️ Ask First)` — decisions with documented trade-offs
- `## Forbidden_Patterns (🚫 Never Do)` — anti-patterns with correct alternatives
- `## Ecosystem_Interoperability` — tested integrations with partners
- `## Verification_Commands` — commands to verify the installation
- `## Source_Bibliography` — all sources with URL + access date

### Post-Research Verification

```bash
grep -E "^## (Mandatory_Patterns|Conditional_Patterns|Forbidden_Patterns|Source_Bibliography)" research_*.md
grep -c "✅" research_FastAPI_v0.115.md   # should have ≥ 3
grep -c "🚫" research_FastAPI_v0.115.md   # should have ≥ 2
```

### Next Steps

- Generic technology → `/skill-creator StoryBeat/research_FastAPI_v0.115.md`
- Methodology → `/methodologies-skill-generator`
- Architecture → `/architecture-approaches-skill-generator`
- Terraform → `/terraform-instructions-compiler`

---

## /technical-framework-researcher-terraform

> **Agent:** `framework-researcher` | **Context:** fork | **Model invocation:** disabled

### When to Use

Use when you want to create a provisioning skill for a specific cloud service using Terraform. Covers resources, data sources, modules and IaC patterns.

**Trigger words:** "Terraform for AWS Lambda", "provision OCI Functions", "research AWS S3 provider", "IaC skill for Azure AKS".

### Prerequisites

None — this is the entry point for the IaC pipeline.

### Inputs

| Field | Required | Example |
|-------|:-----------:|---------|
| Cloud Provider | ✅ | `AWS`, `OCI`, `Azure`, `GCP` |
| Service | ✅ | `Lambda`, `S3`, `Functions`, `AKS` |
| Terraform Version | ✅ | `1.9`, `1.10` |
| Provider Version | ✅ | `aws ~> 5.60`, `oci ~> 6.10` |
| Official URL (if known) | Optional | `https://registry.terraform.io/providers/hashicorp/aws/` |
| Use modules? | Optional | `yes — Terraform Registry` |

### Call Example

```
/technical-framework-researcher-terraform
```

The agent will ask for:
```
Provider: AWS
Service: Lambda
Terraform Version: 1.9
Provider Version: aws ~> 5.60
Use modules: yes (terraform-aws-modules/lambda)
```

### Output Produced

```
StoryBeat/research_AWS_Lambda_aws5.60.md
```

Additional IaC-specific sections:
- Available resources and data sources (`aws_lambda_function`, `aws_lambda_alias`, etc.)
- Required vs optional arguments with types
- Recommended module patterns
- State management and lifecycle rules
- `terraform.tfvars` examples

### Next Steps

- Generate provisioning skill → `/skill-creator StoryBeat/research_AWS_Lambda_aws5.60.md`

> **When to use this vs. `/terraform-engineering-best-practices-researcher`:**
> This one researches **a specific service** (e.g. Lambda, S3). The other researches **the general project structure** of Terraform (modules, CI/CD, state, tests) — use both in a complementary manner.

---

## /cloud-architecture-researcher

> **Agent:** `framework-researcher` | **Context:** fork | **Model invocation:** disabled

### When to Use

Use when you need a knowledge base on cloud providers' architecture frameworks: AWS Well-Architected, Azure CAF, GCP Architecture Framework, OCI Best Practices.

**Trigger words:** "Well-Architected pillars", "Azure CAF security", "GCP reliability patterns", "OCI architecture best practices".

### Inputs

| Field | Required | Example |
|-------|:-----------:|---------|
| Cloud Provider | ✅ | `AWS`, `Azure`, `GCP`, `OCI` |
| Domain / Pillar | ✅ | `Security`, `Reliability`, `Cost Optimization` |
| Framework edition | ✅ | `2024`, `v4.0` |
| Context | Optional | `Kubernetes microservices` |

### Call Example

```
/cloud-architecture-researcher
```

```
Provider: AWS
Domain: Security
Edition: 2024
Context: serverless workloads
```

### Output Produced

```
StoryBeat/research_cloud_AWS_Security_2024.md
```

---

## /business-domain-researcher

> **Agent:** `framework-researcher` | **Context:** fork | **Model invocation:** disabled

### When to Use

Use when you need structured knowledge about an organizational domain — processes, vocabulary, regulations, support systems.

**Trigger words:** "Finance domain", "HR processes", "LGPD Compliance regulation", "Supply Chain domain".

### Inputs

| Field | Required | Example |
|-------|:-----------:|---------|
| Domain | ✅ | `Finance`, `Legal`, `HR`, `Compliance`, `Supply Chain` |
| Organizational context | ✅ | `retail bank`, `B2B fintech`, `e-commerce` |
| Regulatory URLs | Optional | `https://www.bcb.gov.br/...` |
| Support systems | Optional | `SAP, Salesforce, Workday` |

### Call Example

```
/business-domain-researcher
```

```
Domain: Finance
Context: Brazilian retail bank
Regulation: BACEN, LGPD
Systems: SAP FICO, Salesforce
```

### Output Produced

```
StoryBeat/research_Finance_banco-de-varejo.md
```

Sections: key processes, ubiquitous vocabulary (DDD), suggested bounded contexts, regulatory requirements, stakeholders and SLAs.

---

## /requirements-methodology-researcher

> **Agent:** `framework-researcher` | **Context:** fork | **Model invocation:** disabled

### When to Use

Use when you want to create a requirements practices skill — user stories, job stories, DoD, acceptance criteria, and agile frameworks.

**Trigger words:** "Scrum user stories", "SAFe epics", "BDD Gherkin", "Shape Up pitches", "INVEST acceptance criteria".

### Inputs

| Field | Required | Example |
|-------|:-----------:|---------|
| Framework | ✅ | `Scrum`, `SAFe`, `Shape Up`, `Kanban` |
| Practice / artifact type | ✅ | `user stories`, `acceptance criteria`, `DoD` |
| Edition | ✅ | `Scrum Guide 2020`, `SAFe 6.0` |
| Team context | Optional | `10 people, distributed, SaaS product` |

### Call Example

```
/requirements-methodology-researcher
```

```
Framework: Scrum
Practice: user stories + acceptance criteria
Edition: Scrum Guide 2020
Context: 8-person squad, mobile product, 2-week sprint
```

### Next Steps

- `/methodologies-skill-generator` — compiles research into methodology SKILL.md

---

## /architecture-methodology-researcher

> **Agent:** `framework-researcher` | **Context:** fork | **Model invocation:** disabled

### When to Use

Use when you want to create a skill about a software architecture methodology — notations, decision frameworks, structural patterns.

**Trigger words:** "C4 Model", "TOGAF", "DDD", "ADR", "UML", "Event-Driven Architecture", "ArchiMate".

### Inputs

| Field | Required | Example |
|-------|:-----------:|---------|
| Methodology | ✅ | `C4 Model`, `TOGAF`, `DDD`, `ADR`, `UML 2.5` |
| Version / edition | ✅ | `C4 v4`, `TOGAF 10`, `DDD (Evans 2003)` |
| Architecture context | Optional | `microservices`, `modular monolith` |
| Abstraction level | Optional | `System Context`, `Component`, `Code` |

### Call Example

```
/architecture-methodology-researcher
```

```
Methodology: C4 Model
Edition: v4 (2024)
Context: payments platform with 12 microservices
Level: System Context + Container
```

### Next Steps

- `/architecture-approaches-skill-generator` — compiles research into architecture SKILL.md

---

## /terraform-engineering-best-practices-researcher

> **Agent:** `framework-researcher` | **Context:** fork | **Model invocation:** disabled

### When to Use

Use when you want to define **Terraform engineering standards for an entire project** — directory structure, modules, CI/CD, tests, governance, state management. Produces a single general-practices research file (do not repeat per service).

**Trigger words:** "Terraform project structure", "reusable modules", "Terraform CI/CD pipeline", "Terratest tests", "IaC governance".

> **When to use this vs. `/technical-framework-researcher-terraform`:**
> This generates **the general project framework** (1 per project). The other generates **specific service** skills (e.g. `provisioning-aws-s3`, `provisioning-oci-functions`) — use both in a complementary manner.

### Inputs

| Field | Required | Example |
|-------|:-----------:|---------|
| Terraform Version | ✅ | `1.9`, `1.10` |
| Main provider | ✅ | `AWS`, `OCI`, `Azure` |
| Team size | ✅ | `small (1-5)`, `medium (6-20)`, `large (20+)` |
| Project scale | ✅ | `3 envs, ~50 resources` |
| Preferred tools | Optional | `GitHub Actions, Atlantis, Checkov` |
| Compliance requirements | Optional | `SOC2, PCI-DSS` |

### Call Example

```
/terraform-engineering-best-practices-researcher
```

```
Terraform Version: 1.9
Provider: AWS
Team size: medium (8 devs)
Scale: 4 envs (dev/staging/prod/dr), ~200 resources
Tools: GitHub Actions + Atlantis
Compliance: SOC2
```

### Output Produced

```
StoryBeat/research_Terraform_Engineering_Best_Practices_v1.9.md
```

Sections: recommended directory structure, module design, environment strategy, state management, CI/CD pipeline, test pyramid, code quality, governance.

### Next Steps

- `/terraform-instructions-compiler StoryBeat/research_Terraform_Engineering_Best_Practices_v1.9.md`

---

## Agent Principles

**Version Absolutism** — each research file covers exactly one version. Research files for different versions are separate files.

**Source Hierarchy:**
1. Official documentation / registry (the only automatically accepted source)
2. Official project blog
3. Official examples
4. Verified community with date < 12 months
5. Any other source → rejected

**Executable Truth** — every claim includes URL + access date. No source = marked as "unverified".

---

*See [manual README](README.md) for general navigation.*
