# Best Practices Review: provisioning-oci-networking

**Date**: 2026-07-25
**File**: `.claude/skills/provisioning-oci-networking/SKILL.md`
**Approx lines**: ~440
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 5/8 | A2 (440 lines — critical near-limit), C (no eval scenarios) |
| Team conventions (D1–D7) | 7/7 | None |
| Critical count | 0 blocking / 2 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | IMPROVE | ~440 lines — CRITICAL: only 60 lines from the 500-line limit. Inline Module Interface, Integration Patterns, and import commands are the contributors |
| A3 — Three-tier structure present | PASS | All three tiers present, reference blueprints |
| A4 — No time-sensitive content without caveat | PASS | Terraform provider version noted; no pricing |
| A5 — External resources with official doc links | PASS | OCI Networking Terraform docs linked |
| A6 — Version context section present | PASS | Version Context with provider version |
| B — Code/scripts correct, safe, referenced | PASS | Inline HCL and CLI commands appear correct |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | provisioning-oci-networking, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers with icons, reference blueprints |
| D3 — Version context with breaking changes | PASS | Provider version noted |
| D4 — Verification loop | PASS | Verification Loop present |
| D5 — Anti-patterns with side-by-side code | PASS | Delegates to Never Do Patterns blueprint |
| D6 — External official-doc links | PASS | External Resources section |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation links to blueprints/ |

---

## Recommendations by Priority

**ALTA**
- A2: At 440 lines this is the MOST CRITICAL size risk in the set — only 60 lines from the 500-line limit. Move inline Module Interface HCL and Integration Patterns sections to `blueprints/integration-patterns.md` immediately. Any review or addition will push it over.

**BAJA**
- C: Add or link `evaluation-scenarios.md` covering: NSG vs Security List decision, subnet sizing, import from existing VCN.

---

## Conclusions

Largest file in the provisioning group. Structurally correct but the inline content density is the primary risk. Needs immediate extraction to blueprints/.
