# Best Practices Review: designing-oci-api-gateway

**Date**: 2026-07-25
**File**: `.claude/skills/designing-oci-api-gateway/SKILL.md`
**Approx lines**: ~390
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 6/8 | A4 (time-sensitive year in description, pricing table) |
| Team conventions (D1–D7) | 6/7 | D1 (name not gerund pattern) |
| Critical count | 0 blocking / 2 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid (name, description, format) | PASS | name matches folder; description has "Use when"; within 1536 chars |
| A2 — Body < 500 lines | PASS | ~390 lines |
| A3 — Three-tier structure present (Always/Ask/Never) | PASS | All three tiers present, reference blueprints |
| A4 — No time-sensitive content without caveat | IMPROVE | Description includes "2024" year; body contains pricing table (API calls/data transfer costs) — pricing changes without notice |
| A5 — External resources with official doc links | PASS | Multiple official OCI docs linked |
| A6 — Version context section present | PASS | Version Context section with target version and breaking changes |
| B — Code/scripts are correct, safe, referenced | PASS | No inline code; patterns delegate to blueprints |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md blueprint linked or present |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | IMPROVE | "designing-oci-api-gateway" is gerund-noun but "designing" qualifies; folder name matches `name` field — acceptable |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers with icons present |
| D3 — Version context with breaking changes | PASS | Version Context section present |
| D4 — Verification loop | PASS | Verification Loop section with bash commands and expected outputs |
| D5 — Anti-patterns with side-by-side code | PASS | Delegates to Never Do Patterns blueprint with ❌/✅ examples |
| D6 — External official-doc links | PASS | External Resources section with official OCI docs |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation links to blueprints/ for all detailed content |

---

## Recommendations by Priority

**MEDIA**
- A4: Remove or gate the pricing table behind a "prices subject to change" caveat and link to official pricing page instead of embedding values. Remove or qualify the "2024" year reference in description.

**BAJA**
- C: Add or link an `evaluation-scenarios.md` blueprint covering at least: JWT auth decision, rate limiting configuration, CORS setup, and private vs public gateway decision.

---

## Conclusions

Solid skill. Three-tier structure correct, progressive disclosure observed, version context present. Main risk is the embedded pricing table (A4) which will silently become incorrect. Missing evaluation scenarios (C) is a gap shared by most skills in the set.
