# Best Practices Review: testing-terraform-modules

**Date**: 2026-07-25
**File**: `.claude/skills/testing-terraform-modules/SKILL.md`
**Approx lines**: ~413
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 5/8 | A2 (413 lines — high risk), A3/D7 (inline tiers, no blueprints), C (no eval scenarios) |
| Team conventions (D1–D7) | 5/7 | D5 (inline), D7 (no blueprints/) |
| Critical count | 0 blocking / 4 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | IMPROVE | ~413 lines — 87 lines from limit. All three tiers inline with full `.tftest.hcl` code blocks |
| A3 — Three-tier structure present | PASS | All three tiers present inline; Quick Navigation links to anchors not blueprints |
| A4 — No time-sensitive content without caveat | PASS | Terraform v1.11 native testing noted; no pricing |
| A5 — External resources with official doc links | PASS | Terraform testing docs linked |
| A6 — Version context section present | PASS | Version Context with Terraform v1.11 |
| B — Code/scripts correct, safe, referenced | PASS | Inline `.tftest.hcl` examples appear correct |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked (ironic given this IS the testing skill) |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | testing-terraform-modules, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers inline |
| D3 — Version context with breaking changes | PASS | Terraform v1.11 testing framework version |
| D4 — Verification loop | PASS | Verification Loop present |
| D5 — Anti-patterns with side-by-side code | IMPROVE | Anti-patterns inline; no dedicated never-do-patterns.md with formal ❌/✅ format |
| D6 — External official-doc links | PASS | External Resources section |
| D7 — Progressive disclosure (blueprints linked) | IMPROVE | No `blueprints/` directory; anchor-only Quick Navigation. Same pattern as managing-terraform-* pair — all terraform-management skills share this approach |

---

## Recommendations by Priority

**ALTA**
- A2: At 413 lines with no blueprints/, any future addition risks hitting 500. Extract the inline `.tftest.hcl` examples to `blueprints/always-do-patterns.md` and `blueprints/never-do-patterns.md`.

**MEDIA**
- C: Add `evaluation-scenarios.md` — particularly ironic that the testing skill lacks evaluation scenarios. Cover: unit vs integration test selection, mocking OCI resources in tests, Terraform state for test runs.

**BAJA**
- D7: Align with team convention by adopting blueprints/ structure.

---

## Conclusions

Substantive skill with good Terraform v1.11 native testing content. The inline approach (no blueprints/) is shared by the terraform-management pair and forms a consistent sub-group within the set. However, at 413 lines it is the second-largest in its peer group and at high size risk. The absence of evaluation-scenarios in the testing skill itself is the most notable gap.
