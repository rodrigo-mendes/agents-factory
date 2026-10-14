# Best Practices Review: provisioning-oci-iam

**Date**: 2026-07-25
**File**: `.claude/skills/provisioning-oci-iam/SKILL.md`
**Approx lines**: ~414
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 5/8 | A2 (414 lines — approaching limit), C (no eval scenarios) |
| Team conventions (D1–D7) | 7/7 | None |
| Critical count | 0 blocking / 2 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | IMPROVE | ~414 lines — 86 lines from violation. Inline Module Architecture, State Management, and Agent Operation Notes are the contributors |
| A3 — Three-tier structure present | PASS | All three tiers present, reference blueprints |
| A4 — No time-sensitive content without caveat | PASS | Terraform provider version noted; no pricing |
| A5 — External resources with official doc links | PASS | OCI IAM Terraform docs linked |
| A6 — Version context section present | PASS | Version Context present |
| B — Code/scripts correct, safe, referenced | PASS | Inline HCL appears correct |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | provisioning-oci-iam, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers with icons, reference blueprints |
| D3 — Version context with breaking changes | PASS | Provider version noted |
| D4 — Verification loop | PASS | Verification Loop present |
| D5 — Anti-patterns with side-by-side code | PASS | Delegates to Never Do Patterns blueprint |
| D6 — External official-doc links | PASS | External Resources section |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation links to blueprints/ |

---

## Recommendations by Priority

**ALTA**
- A2: At 414 lines this skill is at HIGH RISK. Extract inline Module Architecture and State Management sections to `blueprints/integration-patterns.md`. Current at 83% of limit.

**BAJA**
- C: Add or link `evaluation-scenarios.md` covering: dynamic group rule scope, policy verb minimization, Identity Domains migration scenario.

---

## Conclusions

Structurally sound. Size risk is the main concern — any substantive future addition will cross 500 lines. Extract inline sections to blueprints proactively.
