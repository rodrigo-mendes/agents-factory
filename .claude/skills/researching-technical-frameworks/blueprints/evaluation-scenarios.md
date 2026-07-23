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
    "Flags any community blog posts older than 6 months as 'potentially outdated — verify against official docs'; rejects sources older than 12 months unless they document the current stable version",
    "Self-validation checklist at end of research confirms: 'Every URL includes publication date: ✅' or lists which ones are missing dates"
  ]
}
```

---

## Scenario 5: JVM SDK — Stripe Java SDK (version absolutism + multi-artifact research)

```json
{
  "skills": ["researching-technical-frameworks"],
  "query": "Research the Stripe Java SDK v27 covering payment intents, webhook handling, and idempotency. Integration partners: Stripe Webhooks, Stripe API 2026-06-24.dahlia.",
  "expected_behavior": [
    "Asks clarifying question about research breadth (Minimal / Standard / Comprehensive) before proceeding",
    "After user confirms scope, identifies primary sources: stripe.com/docs/api, github.com/stripe/stripe-java, mvnrepository.com entry for com.stripe:stripe-java:27.x",
    "Pins SDK version to v27.x in every code comment — never uses 'latest' or omits version",
    "Documents multi-artifact scope: SDK artifact (Maven GAV), Stripe API date version (2026-06-24.dahlia), and webhook secret separately",
    "Mandatory Patterns include: STRIPE_SECRET_KEY via env var (never hardcoded), Stripe.apiVersion pinned to exact date string, idempotency key on all mutating calls",
    "Conditional Patterns include: retry strategy (RateLimitException only vs. broader), webhook signature verification (required if webhooks in scope)",
    "Forbidden Patterns include: hardcoded API keys, relying on SDK default API version, retrying on 400 validation errors",
    "Webhook section documents Webhook.constructEvent() signature verification before any processing",
    "Idempotency section documents key generation strategy and 24-hour server retention window",
    "Output named research_Stripe-Java-SDK_v27.md with Stripe-API-version 2026-06-24.dahlia noted in metadata",
    "All sources include publication/access dates"
  ]
}
```

---

## Scenario 6 (Edge): Date-versioned REST API — Stripe API non-semver version absolutism

```json
{
  "skills": ["researching-technical-frameworks"],
  "query": "Research the Stripe API version 2026-06-24.dahlia — focus on Payment Intents and the new breaking changes from the previous version.",
  "expected_behavior": [
    "Recognizes this is a date-versioned API (not semver) and applies version absolutism to the exact string '2026-06-24.dahlia'",
    "Does NOT treat the version as a date range or approximate it — pins exactly to '2026-06-24.dahlia' in all code comments",
    "Primary source: stripe.com/docs/api and stripe.com/docs/upgrades (changelog between versions)",
    "Documents what changed from the previous date version (breaking changes section is mandatory for date-version migrations)",
    "Mandatory Patterns include: Stripe-Version header set to '2026-06-24.dahlia' in every API call; SDK pinned to matching SDK version",
    "Forbidden Patterns include: omitting the version header (reverts to account default, which may differ), using approximate dates like '2026-06-*'",
    "Flags any source referencing a different date version as out-of-scope for this research document",
    "Output named research_Stripe-API_v2026-06-24-dahlia.md — filename reflects the full version string",
    "Version mentioned 5+ times throughout: title, metadata, code comments, anti-patterns, final warning"
  ]
}
```
