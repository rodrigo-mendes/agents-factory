# Best Practices Review: designing-oci-networking

**Date**: 2026-07-25
**File**: `.claude/skills/designing-oci-networking/SKILL.md`
**Approx lines**: ~243
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 6/8 | C missing eval scenarios |
| Team conventions (D1–D7) | 7/7 | None |
| Critical count | 0 blocking / 1 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | PASS | ~243 lines — well within limit |
| A3 — Three-tier structure present | PASS | All three tiers present, reference blueprints |
| A4 — No time-sensitive content without caveat | PASS | No pricing tables or specific dates embedded |
| A5 — External resources with official doc links | PASS | OCI Networking docs linked |
| A6 — Version context section present | PASS | Version Context section present |
| B — Code/scripts correct, safe, referenced | PASS | No inline code; patterns delegate to blueprints |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | designing-oci-networking — gerund-noun, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers with icons |
| D3 — Version context with breaking changes | PASS | Version Context section present |
| D4 — Verification loop | PASS | Verification Loop with bash commands |
| D5 — Anti-patterns with side-by-side code | PASS | Delegates to Never Do Patterns blueprint |
| D6 — External official-doc links | PASS | External Resources section |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation links to blueprints/ |

---

## Recommendations by Priority

**BAJA**
- C: Add or link `evaluation-scenarios.md` covering: subnet sizing decisions, NAT vs Service Gateway choice, NSG vs Security List decision.

---

## Conclusions

Clean, well-structured skill. One of the leaner files in the set (~243 lines). All conventions satisfied. Only gap is missing evaluation scenarios, consistent with the broader skill set.
