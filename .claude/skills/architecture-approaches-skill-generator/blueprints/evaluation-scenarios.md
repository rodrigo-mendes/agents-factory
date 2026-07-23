# Evaluation Scenarios — architecture-approaches-skill-generator

Used to verify that this generator correctly classifies architecture subjects, produces
SKILL.md files that are complete (three-tier guardrails, evaluation-scenarios, External
Resources, Verification Loop), and refuses to include Tier 5 sources or version-mixed guidance.

---

## Scenario 1: Canonical — Generate C4 Model SKILL.md (Diagram Notation)

```json
{
  "skills": ["architecture-approaches-skill-generator"],
  "query": "Generate a SKILL.md for the C4 Model 2024 for a microservices platform with 10+ services.",
  "expected_behavior": [
    "Classifies subject as 'Diagram Notation' before researching",
    "Sources all mandatory elements from c4model.com (Tier 1) or Simon Brown's publications (Tier 2)",
    "Generated SKILL.md contains all three tiers: ✅ Always Do, ⚠️ Ask First, 🚫 Never Do",
    "Every 🚫 Never Do item has an inline ✅ correct alternative",
    "Generated SKILL.md includes a Verification Loop section with concrete self-check steps",
    "Generated SKILL.md includes an External Resources section with dated links",
    "Creates blueprints/evaluation-scenarios.md with ≥3 scenarios (canonical, edge, misuse)",
    "Links evaluation-scenarios.md from Quick Navigation in the generated SKILL.md",
    "Generated SKILL.md is under 500 lines",
    "Phase 4 self-validation checklist is run and failures are explicitly flagged"
  ],
  "success_criteria": {
    "must_pass": [
      "Phase 1 classification output is present before research begins",
      "At least one Tier 1 source (c4model.com) cited in Research Confidence Report",
      "Generated SKILL.md has ✅, ⚠️, and 🚫 sections all populated",
      "blueprints/evaluation-scenarios.md created alongside SKILL.md",
      "Quick Navigation links to ./blueprints/evaluation-scenarios.md",
      "External Resources section present in generated SKILL.md",
      "Verification Loop section present in generated SKILL.md"
    ],
    "must_not": [
      "Include Tier 5 sources (blog posts, informal adaptations) in the generated SKILL.md",
      "Produce a 🚫 Never Do item without a ✅ correct alternative",
      "Skip the Phase 4 self-validation checklist",
      "Exceed 500 lines in the generated SKILL.md without extracting to blueprints/",
      "Omit evaluation-scenarios.md or leave it unlinked from Quick Navigation"
    ]
  }
}
```

---

## Scenario 2: Edge — Ambiguous subject spanning multiple categories (DDD)

```json
{
  "skills": ["architecture-approaches-skill-generator"],
  "query": "Generate a SKILL.md for Domain-Driven Design for an e-commerce platform decomposing a monolith.",
  "expected_behavior": [
    "Recognizes DDD spans 'Domain Modeling' and 'Design Pattern Catalog' categories",
    "Asks the user which primary use case to emphasize (strategic vs tactical DDD) before classifying",
    "After receiving direction, classifies as 'Domain Modeling' if strategic or 'Design Pattern Catalog' if tactical",
    "Sources Eric Evans 'Domain-Driven Design' book (Tier 2) and domainlanguage.com (Tier 2) as primary sources",
    "Marks community conventions (e.g., event storming facilitator patterns not from Evans) as [MEDIUM] or [LOW]",
    "Generated SKILL.md includes abstraction discipline: distinguishes strategic DDD (bounded contexts, context maps) from tactical DDD (aggregates, entities, value objects)",
    "Generated SKILL.md's three-tier section covers DDD-specific guardrails (e.g., ✅ always define ubiquitous language per bounded context, 🚫 never share domain model across bounded contexts without anti-corruption layer)",
    "blueprints/evaluation-scenarios.md created with ≥3 DDD-specific scenarios"
  ],
  "success_criteria": {
    "must_pass": [
      "Generator asks clarifying question before proceeding when subject is ambiguous",
      "Classification is specific (not generic 'Architecture Subject')",
      "Research Confidence Report tags each finding with [HIGH]/[MEDIUM]/[LOW]",
      "Generated SKILL.md distinguishes strategic from tactical DDD in abstraction level map",
      "Three-tier guardrails present and DDD-specific (not generic)"
    ],
    "must_not": [
      "Proceed to research without classifying when subject is ambiguous",
      "Mix strategic and tactical DDD guidance without distinguishing abstraction levels",
      "Include undefined SUBJECT_EDITION without asking the user (Eric Evans vs Vernon IDDD are different editions)"
    ]
  }
}
```

---

## Scenario 3: Misuse — User requests generation with Tier 5 sources only

```json
{
  "skills": ["architecture-approaches-skill-generator"],
  "query": "Generate a SKILL.md for microservices event sourcing. My main source is this Medium blog post from 2019: https://medium.com/some-post. Use that as the basis.",
  "expected_behavior": [
    "Rejects the Medium blog post as Tier 5 — does not include it in the generated SKILL.md",
    "Explains the source hierarchy and why Tier 5 sources are excluded",
    "Identifies legitimate Tier 1/2 sources for event sourcing: Martin Fowler's bliki (Tier 2), Gregor Hohpe's EAI Patterns (Tier 2), CQRS pattern from Microsoft Docs (Tier 1 for Azure context)",
    "Proceeds with research using Tier 1/2 sources, flagging any gaps as Research Gaps",
    "Documents in Research Gaps that the 2019 blog post was rejected and what authoritative source to use instead",
    "Does NOT silently use the Tier 5 source to fill gaps",
    "Generated SKILL.md three-tier section is sourced only from Tier 1–4"
  ],
  "success_criteria": {
    "must_pass": [
      "Tier 5 source explicitly rejected with explanation",
      "Alternative Tier 1/2 sources identified and cited",
      "Research Gaps section documents the rejected source and follow-up action",
      "Generated SKILL.md contains no uncited claims from the rejected blog post"
    ],
    "must_not": [
      "Silently use the Tier 5 blog post as a source",
      "Include the 2019 blog post URL in External Resources",
      "Produce a generated SKILL.md with [REJECT]-tagged content included",
      "Refuse to generate entirely — must proceed with legitimate sources and document gaps"
    ]
  }
}
```
