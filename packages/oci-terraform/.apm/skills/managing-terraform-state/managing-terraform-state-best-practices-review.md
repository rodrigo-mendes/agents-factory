# Best Practices Review: managing-terraform-state

**Date**: 2026-07-25
**File**: `.claude/skills/managing-terraform-state/SKILL.md`
**Approx lines**: ~316
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 6/8 | A3 (tiers inline/anchor-only), C (no eval scenarios) |
| Team conventions (D1–D7) | 5/7 | D5, D7 (no blueprints/) |
| Critical count | 0 blocking / 3 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | PASS | ~316 lines |
| A3 — Three-tier structure present | PASS | All three tiers inline with ✅⚠️🚫 icons; Quick Navigation links to anchors not blueprints |
| A4 — No time-sensitive content without caveat | PASS | No pricing tables; Terraform version noted |
| A5 — External resources with official doc links | PASS | Terraform state docs linked |
| A6 — Version context section present | PASS | Version Context present |
| B — Code/scripts correct, safe, referenced | PASS | Bash recovery commands inline appear correct and safe |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | managing-terraform-state, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers inline |
| D3 — Version context with breaking changes | PASS | Terraform version noted |
| D4 — Verification loop | PASS | Verification Loop present |
| D5 — Anti-patterns with side-by-side code | IMPROVE | Anti-patterns present but inline; no dedicated never-do-patterns.md with ❌/✅ side-by-side format |
| D6 — External official-doc links | PASS | External Resources section |
| D7 — Progressive disclosure (blueprints linked) | IMPROVE | No `blueprints/` directory; anchor-only Quick Navigation — same deviation as managing-terraform-cicd |

---

## Recommendations by Priority

**MEDIA**
- D7/D5: Extract detailed three-tier content to `blueprints/` to align with team convention. State recovery procedures especially would benefit from a dedicated blueprint with full recovery runbook.

**BAJA**
- C: Add or link `evaluation-scenarios.md` covering: state lock recovery, state drift scenarios, backend migration procedures.

---

## Conclusions

Functional skill with all critical content present. Anchor-only navigation pattern (no blueprints/) is consistent with its sibling `managing-terraform-cicd` but deviates from the broader team convention. Both terraform-management skills form a coherent pair with the same structural approach.
