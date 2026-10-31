# Best Practices Review: managing-terraform-cicd

**Date**: 2026-07-25
**File**: `.claude/skills/managing-terraform-cicd/SKILL.md`
**Approx lines**: ~327
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 6/8 | A3 (tiers inline with code, no blueprints), C (no eval scenarios) |
| Team conventions (D1–D7) | 5/7 | D5 (inline code in tiers not blueprint-backed), D7 (no blueprints/) |
| Critical count | 0 blocking / 3 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | PASS | ~327 lines |
| A3 — Three-tier structure present | PASS | All three tiers present inline with ✅⚠️🚫 icons; Quick Navigation links to anchors (#-always-do etc.) not to blueprint files |
| A4 — No time-sensitive content without caveat | PASS | No pricing; Azure DevOps pipeline syntax stable |
| A5 — External resources with official doc links | PASS | Azure DevOps and Terraform docs linked |
| A6 — Version context section present | PASS | Terraform version and provider versions noted |
| B — Code/scripts correct, safe, referenced | PASS | YAML pipeline and bash code inline; appears correct |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | managing-terraform-cicd, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers present inline |
| D3 — Version context with breaking changes | PASS | Terraform/provider versions noted |
| D4 — Verification loop | PASS | Verification Loop present |
| D5 — Anti-patterns with side-by-side code | IMPROVE | Anti-patterns present but all inline in SKILL.md rather than in a `never-do-patterns.md` blueprint; side-by-side ❌/✅ examples not consistently structured |
| D6 — External official-doc links | PASS | External Resources section |
| D7 — Progressive disclosure (blueprints linked) | IMPROVE | No `blueprints/` directory referenced; all content (including substantial YAML pipeline code) is inline. At ~327 lines this is within limit but inconsistent with team convention |

---

## Recommendations by Priority

**MEDIA**
- D7/D5: Extract inline three-tier content (especially the pipeline YAML) to `blueprints/always-do-patterns.md`, `blueprints/never-do-patterns.md`, `blueprints/ask-first-decisions.md` to align with team convention and enable future growth without hitting the 500-line limit.

**BAJA**
- C: Add or link `evaluation-scenarios.md` covering: SecurityToken auth lifecycle, plan vs apply gate scenarios, state lock handling.

---

## Conclusions

Functional skill but uses the "anchor-only Quick Navigation" pattern instead of blueprints/, unlike most peers. All content inline risks hitting the 500-line limit if extended. The deviation from team convention reduces consistency across the skill set.
