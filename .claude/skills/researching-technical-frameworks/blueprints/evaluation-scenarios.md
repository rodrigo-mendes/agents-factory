# Evaluation Scenarios — researching-technical-frameworks

Used to verify that the skill activates correctly, enforces version absolutism, handles scope decisions, and rejects invalid inputs.

---

## Scenario 1: Research with all valid inputs (Standard scope)

```json
{
  "skills": ["researching-technical-frameworks"],
  "query": "Preciso de um research sobre FastAPI v0.104 com SQLAlchemy 2.0 como integration partner para criar um skill completo.",
  "expected_behavior": [
    "Asks clarifying question about research breadth (Minimal / Standard / Comprehensive) before proceeding",
    "After user confirms 'Standard', sets research scope to 15-25 pages covering full FastAPI 0.104 API surface + SQLAlchemy 2.0 integration",
    "Identifies primary sources: fastapi.tiangolo.com, pypi.org/project/fastapi/, fastapi.tiangolo.com/release-notes/",
    "Tags every code sample and claim with 'v0.104' — never uses unversioned references",
    "Includes publication dates on all sources",
    "Output file named research_FastAPI_v0.104.md",
    "Document includes all three tiers: Mandatory Patterns, Conditional Patterns, Forbidden Patterns",
    "SQLAlchemy 2.0 integration example included with install instructions and working code"
  ]
}
```

---

## Scenario 2: Reject research without explicit version (anti-pattern enforcement)

```json
{
  "skills": ["researching-technical-frameworks"],
  "query": "Faça um research sobre FastAPI para criar um skill.",
  "expected_behavior": [
    "Rejects the request immediately — no version specified",
    "Asks: 'Which version of FastAPI? (e.g., 0.104.x, 0.100.x) — Version Absolutism requires a specific semantic version before research starts'",
    "Does NOT proceed with research until version is confirmed",
    "Does NOT guess or assume the latest version",
    "After user provides version (e.g., '0.104'), asks about research breadth (Minimal/Standard/Comprehensive) before starting"
  ]
}
```

---

## Scenario 3: Terraform multi-provider research — cloud provider decision

```json
{
  "skills": ["researching-technical-frameworks"],
  "query": "Pesquisa o Terraform AWS Provider v5 focando em RDS PostgreSQL com VPC e Secrets Manager.",
  "expected_behavior": [
    "Identifies this as provider-specific Terraform IaC — no need to ask cloud provider (AWS is explicit)",
    "Sets provider to hashicorp/aws, pins to v5.x in research",
    "Primary source: registry.terraform.io/providers/hashicorp/aws/latest",
    "Extracts Mandatory Patterns: provider config block with ~> 5.0 constraint, VPC resource dependencies, encryption, Secrets Manager integration",
    "Extracts Forbidden Patterns: hardcoded credentials in .tf files, public RDS without security group restriction",
    "Output named research_Terraform_AWS_RDS-PostgreSQL_v5.md",
    "Every code example includes # Terraform AWS Provider v5.x comment",
    "All sources include publication/access dates"
  ]
}
```

---

## Scenario 4 (Edge): Undated source detected mid-research

```json
{
  "skills": ["researching-technical-frameworks"],
  "query": "Pesquisa Kafka 3.5 com foco em consumer groups e exactly-once semantics.",
  "expected_behavior": [
    "During research, if a source has no publication date, flags it explicitly: '[WARNING: Source undated — cannot validate currency for Kafka 3.5]'",
    "Does NOT include undated sources as authoritative references",
    "Searches for the official Kafka 3.5 release date from kafka.apache.org/downloads",
    "Flags any community blog posts older than 12 months as 'potentially outdated — verify against official docs'",
    "Self-validation checklist at end of research confirms: 'Every URL includes publication date: ✅' or lists which ones are missing dates"
  ]
}
```
