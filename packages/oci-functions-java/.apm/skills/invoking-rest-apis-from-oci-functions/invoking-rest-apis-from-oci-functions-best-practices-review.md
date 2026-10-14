# Best Practices Review: invoking-rest-apis-from-oci-functions

**Date**: 2026-07-25
**File**: `.claude/skills/invoking-rest-apis-from-oci-functions/SKILL.md`
**Approx lines**: ~264
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 6/8 | A5 (relative cross-skill links), C (no eval scenarios) |
| Team conventions (D1–D7) | 7/7 | None |
| Critical count | 0 blocking / 2 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | PASS | ~264 lines |
| A3 — Three-tier structure present | PASS | All three tiers present, reference blueprints |
| A4 — No time-sensitive content without caveat | PASS | Version context noted |
| A5 — External resources with official doc links | IMPROVE | Uses relative `../../skills/...` cross-skill links — same portability fragility as sibling integration skills |
| A6 — Version context section present | PASS | Version Context section present |
| B — Code/scripts correct, safe, referenced | PASS | Delegates to blueprints |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | invoking-rest-apis-from-oci-functions, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers with icons |
| D3 — Version context with breaking changes | PASS | Version Context present |
| D4 — Verification loop | PASS | Verification Loop section present |
| D5 — Anti-patterns with side-by-side code | PASS | Delegates to Never Do Patterns blueprint |
| D6 — External official-doc links | PASS | External Resources section |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation links to blueprints/ |

---

## Recommendations by Priority

**MEDIA**
- A5: Replace relative `../../skills/...` links with skill name references or absolute `.claude/skills/...` paths.

**BAJA**
- C: Add or link `evaluation-scenarios.md` covering: OCI SDK vs custom HttpClient selection, Vault auth vs API key auth decision, timeout budget scenarios.

---

## Conclusions

Clean skill with proper progressive disclosure. Relative link pattern is a shared fragility across several integration skills. Missing evaluation scenarios consistent with the set.
