# Best Practices Review: integrating-oracle-rms-webhooks

**Date**: 2026-07-25
**File**: `.claude/skills/integrating-oracle-rms-webhooks/SKILL.md`
**Approx lines**: ~111
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 5/8 | A1 (description in Portuguese), A3 (partial three-tier — body guardrails but Quick Navigation labels are non-standard), C (no eval scenarios) |
| Team conventions (D1–D7) | 5/7 | D3 (API version in description not Version Context section), D6 (no External Resources section — only inline links), D7 (blueprints linked but body is mixed EN/PT) |
| Critical count | 0 blocking / 5 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | IMPROVE | `description` is entirely in Portuguese ("Integra OCI Functions com as APIs do Oracle Retail...") — this is fine if the project language is Portuguese, but inconsistent with the English descriptions of all other skills in the set |
| A2 — Body < 500 lines | PASS | ~111 lines — very lean |
| A3 — Three-tier structure present | PASS | Has `### ✅ Always`, `### ⚠️ Ask First`, `### 🚫 Never` inline in Guardrails section; Quick Navigation links to blueprints/ |
| A4 — No time-sensitive content without caveat | PASS | MFCS 26.1.x tenant ID noted; caveat "validado em vivo" noted |
| A5 — External resources with official doc links | IMPROVE | `## External Resources` section present but links are narrative (inline URL in sentences) without structured bullet list format; one link points to a Swagger that is auth-gated |
| A6 — Version context section present | PASS | Version Context section present (API 26.1.x, OAuth2, Java 17/FDK 1.1.x) |
| B — Code/scripts correct, safe, referenced | PASS | JSON envelope examples and scripts/ reference; impl reference to services/func-rr-rest-proxy |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No evaluation-scenarios.md linked; scripts/ directory serves as practical validation |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | integrating-oracle-rms-webhooks, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers present inline under Guardrails section |
| D3 — Version context with breaking changes | IMPROVE | Version Context present but mixes API version, auth method, network constraints — could be cleaner; no explicit breaking changes section |
| D4 — Verification loop | PASS | scripts/ directory with validate scripts serves as verification; no formal `## Verification Loop` section but functionally covered |
| D5 — Anti-patterns with side-by-side code | PASS | `### 🚫 Never` section and blueprints/never-do-patterns.md linked |
| D6 — External official-doc links | IMPROVE | External links are partial (Swagger is auth-gated, white paper is informal reference); no structured External Resources section |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation links to blueprints/; scripts/ referenced |

---

## Recommendations by Priority

**MEDIA**
- A1: Decide on project language (EN or PT) and apply consistently to the description field. Currently this is the only skill with a Portuguese description.
- D6: Add a formal `## External Resources` section with structured bullet list of Oracle RMS/MFCS docs; note auth-gated resources explicitly.

**BAJA**
- D4: Add a formal `## Verification Loop` section separate from the scripts/ reference, with expected outputs for each validation step.
- C: Add or link `evaluation-scenarios.md` covering: EVENT vs PAYLOAD mode selection, sync vs async for large batches, auth flow validation.
- D3: Add an explicit "Breaking Changes" or "Known Gotchas" subsection in Version Context documenting the `?item=` filter trap and base URL concatenation error.

---

## Conclusions

Compact, highly specialized skill with real production validation evidence. The scripts/ tooling is a strong addition. Main gaps are language consistency (Portuguese description vs English body peers) and lack of a formal External Resources section with accessible official docs. The MFCS API is auth-gated which limits link value.
