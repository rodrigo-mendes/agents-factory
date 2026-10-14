# Best Practices Review: designing-oci-event-driven-pubsub

**Date**: 2026-07-25
**File**: `.claude/skills/designing-oci-event-driven-pubsub/SKILL.md`
**Approx lines**: 295 (non-blank lines: 222)
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 7/8 | A4 (time-sensitive "2024" edition and "2026-07-22" delivery date) |
| Team conventions (D1–D7) | 6/7 | D2 (three-tier headings lack emoji icons at heading level) |
| Critical count | 0 blocking / 2 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid (name, description, format) | PASS | `name: designing-oci-event-driven-pubsub` matches folder; description is in third-person, specific, has "Use when" trigger, uses YAML quoting for colon-containing value; within 1536 chars |
| A2 — Body < 500 lines | PASS | 295 total lines; well within limit |
| A3 — Three-tier structure present (Always/Ask/Never) | PASS | `### Always Do`, `### Ask First`, `### Never Do` present under `## Blueprints & Guardrails` (lines 143/156/166); each delegates to blueprint files |
| A4 — No time-sensitive content without caveat | IMPROVE | Line 14: `**Target Edition**: OCI Best Practices 2024`; line 16: `**Support Status**: Active — pattern delivered GREEN in dev environment (2026-07-22)`; line 91: example timestamp `"2026-07-22T18:35:33Z"` — the delivery date in Support Status and the edition year will silently age without a caveat or pointer to a release-notes URL |
| A5 — External resources with official doc links | PASS | `## External Resources` (lines 284–295) links to official OCI Streaming, SCH, and Functions docs, plus pattern docs within the repo; all links are relative or https |
| A6 — Version context section present | PASS | `## Version Context` (lines 10–23) declares FDK Java v1.1.x, Java 17, Target Edition, pattern docs path, support status, and key architectural facts |
| B — Code/scripts are correct, safe, referenced | PASS | Verification Loop (lines 191–237) has 5 explicit OCI CLI + logging bash commands with expected outputs and a troubleshooting key; no voodoo constants |
| C — Testing/evaluation scenarios present or linked | PASS | `evaluations.json` file confirmed present in the skill directory; linked in Quick Navigation at line 33 |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | `designing-oci-event-driven-pubsub` is gerund-noun; `name` field matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | IMPROVE | Three-tier headings use plain text (`### Always Do`, `### Ask First`, `### Never Do`) without the canonical emoji icons (✅⚠️🚫) required by the team convention (see authoring-agent-skills/SKILL.md Quality Checklist and Skill Artifact Verification step 3); the parent section heading `## Blueprints & Guardrails` is correct |
| D3 — Version context with breaking changes | PASS | Version Context (lines 10–23) present with technology stack, architectural constraints, and critical agent warning |
| D4 — Verification loop | PASS | `## Verification Loop` (lines 191–237) with five numbered bash command blocks, expected outputs, and troubleshooting cases |
| D5 — Anti-patterns with side-by-side code | PASS | Never Do section delegates to `blueprints/never-do-patterns.md` (file confirmed present); prose summaries in SKILL.md are sufficiently specific to identify the prohibited pattern |
| D6 — External official-doc links | PASS | External Resources section with OCI official docs and internal pattern docs |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation (lines 27–36) links to four blueprint files (`always-do-patterns.md`, `ask-first-decisions.md`, `never-do-patterns.md`, `integration-patterns.md`) and `evaluations.json`; all confirmed present in blueprints directory |

---

## Recommendations by Priority

**MEDIA**
- A4: Replace the delivery date in `**Support Status**` with a pointer to the handoff evidence doc (already linked in External Resources) instead of a static date. Qualify `**Target Edition**: OCI Best Practices 2024` with "verify currency at" and link to the OCI release notes or the official architecture center URL.
- D2: Prefix the three-tier headings with their canonical icons: `### ✅ Always Do`, `### ⚠️ Ask First`, `### 🚫 Never Do` — this enables the team's automated verification step (`grep -E "^### ✅ Always Do|^### ⚠️ Ask First|^### 🚫 Never Do" SKILL.md`) to pass.

**BAJA**
- A4 (secondary): The example JSON timestamp `"2026-07-22T18:35:33Z"` at line 91 is a real date that will appear outdated; replace with `"<ISO8601 timestamp>"` placeholder.

---

## Conclusions

Well-structured architecture skill with strong domain specificity. The five-principle Core Design Principles section is particularly effective (SCH cold-start ceiling, fan-out via N independent connectors, distributed tracing through stream boundary). Evaluation scenarios are present (evaluations.json), which distinguishes this skill from most in the set. Two targeted fixes: add emoji icons to the three-tier headings (D2) and gate the time-sensitive dates in Version Context (A4).
