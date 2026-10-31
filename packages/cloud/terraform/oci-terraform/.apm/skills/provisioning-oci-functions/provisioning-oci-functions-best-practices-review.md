# Best Practices Review: provisioning-oci-functions

**Date**: 2026-07-25
**File**: `.claude/skills/provisioning-oci-functions/SKILL.md`
**Approx lines**: ~421
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 5/8 | A2 (421 lines — close to limit), C (no eval scenarios), plus risk of hitting limit |
| Team conventions (D1–D7) | 7/7 | None |
| Critical count | 0 blocking / 3 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | IMPROVE | ~421 lines — 79 lines from violation. Inline Advanced Patterns and Module Interface sections with substantial HCL are the main contributors |
| A3 — Three-tier structure present | PASS | All three tiers present, reference blueprints |
| A4 — No time-sensitive content without caveat | PASS | Terraform OCI Provider version noted |
| A5 — External resources with official doc links | PASS | OCI Functions Terraform docs linked |
| A6 — Version context section present | PASS | Version Context with provider and Terraform versions |
| B — Code/scripts correct, safe, referenced | PASS | Inline HCL appears correct |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | provisioning-oci-functions, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers with icons, reference blueprints |
| D3 — Version context with breaking changes | PASS | Provider version noted |
| D4 — Verification loop | PASS | Verification Loop present |
| D5 — Anti-patterns with side-by-side code | PASS | Delegates to Never Do Patterns blueprint |
| D6 — External official-doc links | PASS | External Resources section |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation links to blueprints/ |

---

## Recommendations by Priority

**ALTA**
- A2: At 421 lines this skill is at HIGH RISK of exceeding 500 lines with any future additions. Extract the inline Module Interface and Advanced Patterns HCL to `blueprints/integration-patterns.md` immediately. Current content is 84% of the allowed limit.

**BAJA**
- C: Add or link `evaluation-scenarios.md` covering: provisioned concurrency decision, memory/timeout tuning, image digest pinning validation.

---

## Conclusions

Structurally sound skill but at significant size risk. The inline HCL sections must be moved to blueprints before the next content addition to avoid a 500-line violation.
