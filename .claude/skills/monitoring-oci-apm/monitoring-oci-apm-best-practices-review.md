# Best Practices Review: monitoring-oci-apm

**Date**: 2026-07-25
**File**: `.claude/skills/monitoring-oci-apm/SKILL.md`
**Approx lines**: ~207
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 6/8 | A4 ("2024" year in description), C (no eval scenarios) |
| Team conventions (D1–D7) | 6/7 | D6 (Related skills section in Portuguese — language consistency) |
| Critical count | 0 blocking / 3 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | PASS | ~207 lines |
| A3 — Three-tier structure present | PASS | All three tiers present, reference blueprints |
| A4 — No time-sensitive content without caveat | IMPROVE | Description contains "OCI Best Practices 2024" — the year ties the skill to a specific release cycle; if OCI updates its best practices framework the description becomes misleading |
| A5 — External resources with official doc links | PASS | OCI APM docs linked |
| A6 — Version context section present | PASS | Version Context present |
| B — Code/scripts correct, safe, referenced | PASS | Delegates to blueprints |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | monitoring-oci-apm, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers with icons |
| D3 — Version context with breaking changes | PASS | Version Context with APM version |
| D4 — Verification loop | PASS | Verification Loop present |
| D5 — Anti-patterns with side-by-side code | PASS | Delegates to Never Do Patterns blueprint |
| D6 — External official-doc links | IMPROVE | `## Related skills` section at bottom written entirely in Portuguese ("Escopo desta skill", "aprofundamento em", "validados AO VIVO") — inconsistent with the English body of the skill; ideally all skill body text in one language |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation links to blueprints/ |

---

## Recommendations by Priority

**MEDIA**
- D6: Convert the "Related skills" Portuguese section to English or decide on Portuguese as the project language and apply consistently. Mixed language reduces readability.
- A4: Remove the specific "2024" year from the description; reference "OCI APM GA" instead. Add a note in Version Context if the specific year is load-bearing.

**BAJA**
- C: Add or link `evaluation-scenarios.md` covering: APM domain isolation, data key type selection, trace sampling strategy.

---

## Conclusions

Solid skill following most conventions. The Portuguese "Related skills" section is an inconsistency introduced in the newer observability skills cluster. Missing evaluation scenarios consistent with broader set.
