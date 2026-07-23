# Evaluation Scenarios — technical-framework-researcher

Used to verify that the skill activates correctly, enforces version absolutism and source hierarchy,
produces properly structured research output, and rejects misuse requests (non-research tasks,
unversioned queries, out-of-scope asks).

---

## Scenario 1: Standard research request — pinned version, known tech (canonical path)

```json
{
  "skills": ["technical-framework-researcher"],
  "query": "Research FastAPI 0.111 for use in a Python 3.12 microservice. Integration partners: PostgreSQL (asyncpg), JWT (python-jose), pytest-asyncio.",
  "expected_behavior": [
    "Sets SYSTEM_OR_TECH_NAME=FastAPI, TARGET_VERSION=0.111, INTEGRATION_PARTNERS_LIST=[PostgreSQL/asyncpg, JWT/python-jose, pytest-asyncio]",
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
  "skills": ["technical-framework-researcher"],
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
  "skills": ["technical-framework-researcher"],
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

## Scenario 4: Anti-pattern trap — unversioned or contradictory version request

```json
{
  "skills": ["technical-framework-researcher"],
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
