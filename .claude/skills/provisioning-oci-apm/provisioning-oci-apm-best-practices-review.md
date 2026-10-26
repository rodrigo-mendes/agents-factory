# Best Practices Review: provisioning-oci-apm

**Date**: 2026-07-25
**File**: `.claude/skills/provisioning-oci-apm/SKILL.md`
**Approx lines**: ~194
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 7/8 | C (no eval scenarios) |
| Team conventions (D1–D7) | 7/7 | None |
| Critical count | 0 blocking / 1 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | PASS | ~194 lines — lean skill |
| A3 — Three-tier structure present | PASS | All three tiers present, reference blueprints |
| A4 — No time-sensitive content without caveat | PASS | oracle/oci ~> 8.0/Terraform >= 1.9 version constraint noted |
| A5 — External resources with official doc links | PASS | OCI APM Terraform registry docs linked |
| A6 — Version context section present | PASS | Version Context with provider version |
| B — Code/scripts correct, safe, referenced | PASS | Delegates to blueprints |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | provisioning-oci-apm, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers with icons |
| D3 — Version context with breaking changes | PASS | Provider version constraint |
| D4 — Verification loop | PASS | Verification Loop present |
| D5 — Anti-patterns with side-by-side code | PASS | Delegates to Never Do Patterns blueprint |
| D6 — External official-doc links | PASS | External Resources section |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation links to blueprints/ |

---

## Recommendations by Priority

**BAJA**
- C: Add or link `evaluation-scenarios.md` covering: free tier vs paid APM domain decision, APM key type selection (private vs public).

---

## Conclusions

Compact, well-organized skill. Includes `## Function` specialist declaration section consistent with the newer skill generation pattern. Missing evaluation scenarios consistent with broader set.
