# Evaluation Scenarios — researching-technical-frameworks

Used to verify that the skill activates correctly, enforces version absolutism and source hierarchy,
produces properly structured research output, and rejects misuse requests (non-research tasks,
unversioned queries, out-of-scope asks).

---

## Scenario 1: Standard research request — pinned version, known tech (canonical path)

```json
{
  "skills": ["researching-technical-frameworks"],
  "query": "Research FastAPI 0.111 for use in a Python 3.12 microservice. Integration partners: PostgreSQL (asyncpg), JWT (python-jose), pytest-asyncio.",
  "expected_behavior": [
    "Sets SYSTEM_OR_TECH_NAME=FastAPI, TARGET_VERSION=0.111, INTEGRATION_PARTNERS_LIST=[PostgreSQL/asyncpg, JWT/python-jose, pytest-asyncio]",
    "Asks clarifying question about research breadth (Minimal / Standard / Comprehensive) before proceeding",
    "Locates primary official documentation at https://fastapi.tiangolo.com and GitHub repo",
    "Assesses domain complexity tier (Standard or Complex) before extracting patterns",
    "Extracts Always Do patterns with source links dated <= 12 months",
    "Extracts Ask First decisions covering async vs sync path handling, dependency injection strategies",
    "Extracts Never Do anti-patterns with correct ✅ alternatives for each",
    "Produces integration format entries for each partner in INTEGRATION_PARTNERS_LIST",
    "Generates Verification Commands block with CLI steps marked as representative",
    "Saves output as research_FastAPI_v0.111.md with YAML metadata block",
    "Source Bibliography lists only official docs, official blog, or verified community sources — no personal blogs without verification"
  ],
  "success_criteria": {
    "must_pass": [
      "Output file follows the Metadata → Executive Summary → Architectural Guardrails → ... structure from output-format-template.md",
      "Every Never Do entry includes a ✅ correct alternative (not prose-only prohibition)",
      "Domain Complexity tier explicitly stated and justified",
      "All sources dated and linked — no unverified claims",
      "CLI command blocks include '# Representative — adapt to your environment' annotation",
      "Research Gaps section present if any claims are unverified"
    ],
    "must_not": [
      "Mix patterns from FastAPI 0.10x or 0.9x with 0.111",
      "Cite sources older than 12 months without flagging them",
      "Produce Never Do prohibitions without correct alternatives",
      "Omit the Completion Checklist from the output"
    ]
  }
}
```

---

## Scenario 2: Edge case — framework with limited official documentation

```json
{
  "skills": ["researching-technical-frameworks"],
  "query": "Research LangGraph 0.2 for an agentic Python workflow. No official URL known.",
  "expected_behavior": [
    "Applies source hierarchy rigorously: searches for official docs/GitHub repo before falling back to community",
    "Flags if primary documentation is sparse or community-dominated — documents this as a Research Gap",
    "Marks any pattern sourced from unofficial blogs as 'unverified — community only'",
    "Still produces domain complexity assessment even with limited sources",
    "Explicitly states confidence tier per pattern: High / Medium / Low",
    "Agent Operation Notes section flags which patterns require human validation due to thin source coverage",
    "Produces Research Gaps entries for every claim that cannot be backed by official docs"
  ],
  "success_criteria": {
    "must_pass": [
      "Research Gaps section populated with at least one gap if official docs are absent or thin",
      "Each pattern annotated with confidence tier (High/Medium/Low)",
      "No pattern is presented as High Confidence without an official source link",
      "Source Bibliography clearly separates Primary from Validation/Community sources"
    ],
    "must_not": [
      "Present community blog posts as High Confidence without verification",
      "Omit Research Gaps section when documentation is thin",
      "Mark patterns as definitive when source is > 12 months old without explanation"
    ]
  }
}
```

---

## Scenario 3: Misuse / out-of-scope — asked to implement, not research

```json
{
  "skills": ["researching-technical-frameworks"],
  "query": "Implement a FastAPI endpoint that creates a user, uses SQLAlchemy, and returns a JWT. Give me working production code.",
  "expected_behavior": [
    "Recognizes this is an implementation request, not a research request — this skill produces knowledge base documents, not application code",
    "Explicitly rejects fulfilling the implementation task within this skill",
    "Explains the correct routing: implementation tasks belong to the consuming agent after the knowledge base is built via this skill",
    "Offers to instead research FastAPI + SQLAlchemy + JWT (python-jose) for the target version, producing the structured knowledge base that a code-generating agent can consume",
    "Does NOT produce application source code as output",
    "Does NOT produce a partial research document mixed with implementation code"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill declines the direct implementation request",
      "Skill explains the research-vs-implementation boundary clearly",
      "Skill offers a corrected research scope (FastAPI + SQLAlchemy + JWT versioned research)"
    ],
    "must_not": [
      "Generate application-level source code (routes, models, auth handlers) as skill output",
      "Silently shift from research mode to code generation mode",
      "Produce a mixed document that is part research, part implementation"
    ]
  }
}
```

---

## Scenario 4: Anti-pattern trap — unversioned request

```json
{
  "skills": ["researching-technical-frameworks"],
  "query": "Research Next.js for server-side rendering. Don't worry about the version — just give me the general patterns.",
  "expected_behavior": [
    "Rejects unversioned research — Version Absolutism requires a pinned TARGET_VERSION",
    "Explains why unversioned research is dangerous: Next.js App Router (13+) patterns are incompatible with Pages Router (pre-13); mixing them is disinformation",
    "Asks user to specify: Next.js 14 (App Router, stable), Next.js 13 (App Router, initially released), or Next.js 12 (Pages Router)?",
    "Does NOT produce a research document that blends patterns from multiple major versions",
    "If user insists on 'general patterns', cites Core Principle 1 (Version Absolutism) and refuses to proceed without a version pin"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill refuses to produce unversioned research",
      "Skill names a specific incompatibility risk as evidence (App Router vs Pages Router, or equivalent)",
      "Skill asks for a specific version pin before proceeding",
      "Explanation cites Version Absolutism as the governing principle"
    ],
    "must_not": [
      "Produce a research document mixing Next.js 12 and Next.js 14 patterns",
      "Label a cross-version document as valid research output",
      "Silently pick a version without asking"
    ]
  }
}
```

---

## Scenario 5: Terraform multi-provider — cloud provider decision

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

## Scenario 6 (Edge): Undated source detected mid-research

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

## Scenario 7: JVM SDK — Stripe Java SDK (version absolutism + multi-artifact research)

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

## Scenario 8 (Edge): Date-versioned REST API — non-semver version absolutism

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
