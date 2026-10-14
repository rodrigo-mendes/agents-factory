# Best Practices Review: provisioning-oci-event-driven-pubsub

**Date**: 2026-07-25
**File**: `.claude/skills/provisioning-oci-event-driven-pubsub/SKILL.md`
**Approx lines**: 237 (non-blank lines: 192)
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 6/8 | A4 (time-sensitive delivery date), C (no evaluation scenarios) |
| Team conventions (D1–D7) | 6/7 | D2 (three-tier headings lack emoji icons) |
| Critical count | 0 blocking / 3 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid (name, description, format) | PASS | `name: provisioning-oci-event-driven-pubsub` matches folder; description is third-person, specific, includes "Use when", uses YAML quoting for colon-containing value; well within 1536 chars |
| A2 — Body < 500 lines | PASS | 237 total lines; well within limit |
| A3 — Three-tier structure present (Always/Ask/Never) | PASS | `### Always Do`, `### Ask First`, `### Never Do` present under `## Blueprints & Guardrails` (lines 87/100/110); all delegate to blueprint files confirmed present |
| A4 — No time-sensitive content without caveat | IMPROVE | Line 14: `**Pattern delivered**: event-pubsub — GREEN in dev 2026-07-22` — a delivery date in the Version Context will silently become misleading as the environment evolves; no caveat or pointer to handoff evidence to contextualize it |
| A5 — External resources with official doc links | PASS | `## External Resources` (lines 226–236) links to Terraform registry docs for all three resources, OCI provisioned concurrency docs, cross-skill references, handoff evidence, and pattern spec |
| A6 — Version context section present | PASS | `## Version Context` (lines 10–30) declares Terraform oracle/oci >= 6.0, < 9.0 (tested v8.x), Terraform >= 1.5, modules implemented, and key provider constraints |
| B — Code/scripts are correct, safe, referenced | PASS | Verification Loop (lines 123–188) has five bash command blocks with OCI CLI commands, expected outputs, and a troubleshooting section; Quick Reference (lines 191–224) includes IAM policy template and optional+computed workaround |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No `evaluations.json` or `evaluation-scenarios.md`; no blueprint or inline evaluation scenarios; the Verification Loop provides operational smoke tests but not evaluation scenarios for skill correctness |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | `provisioning-oci-event-driven-pubsub` is gerund-noun; `name` field matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | IMPROVE | Three-tier headings use plain text (`### Always Do`, `### Ask First`, `### Never Do`) without canonical emoji icons (✅⚠️🚫); same issue as `designing-oci-event-driven-pubsub` — prevents automated grep verification per authoring-agent-skills/SKILL.md step 3 |
| D3 — Version context with breaking changes | PASS | Version Context (lines 10–30) present with provider constraints, known optional+computed traps, and immutability notes; no formal "Breaking Changes" block but the provider constraint notes serve the same purpose |
| D4 — Verification loop | PASS | `## Verification Loop` (lines 123–188) with five numbered verification steps, expected outputs, and troubleshooting table covering all common failure modes |
| D5 — Anti-patterns with side-by-side code | PASS | Never Do section delegates to `blueprints/never-do-patterns.md` (file confirmed present); SKILL.md summaries are specific and actionable |
| D6 — External official-doc links | PASS | External Resources section with Terraform registry links, OCI docs, and internal cross-references |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation (lines 32–40) links to four blueprint files (`always-do-patterns.md`, `ask-first-decisions.md`, `never-do-patterns.md`, `integration-patterns.md`); Module Architecture section provides inline diagram; all blueprints confirmed present |

---

## Recommendations by Priority

**MEDIA**
- D2: Add emoji icons to the three-tier headings: `### ✅ Always Do`, `### ⚠️ Ask First`, `### 🚫 Never Do`. Consistent with `architecting-oci-serverless` and required for automated verification.
- A4: Replace the static delivery date in Version Context (`GREEN in dev 2026-07-22`) with a reference to the handoff evidence document already linked in External Resources. Dates in Version Context convey recency but become misleading over time.

**BAJA**
- C: Add or link an `evaluations.json` covering at least: correct PUBLIC pool is applied (no private_endpoint_settings), all four IAM verbs are present in policy, SCH connectors reach ACTIVE state after apply, fan-out produces >= 2 consumer log entries per event.

---

## Conclusions

Well-composed Terraform composition skill with correct module architecture documentation, complete IAM verb checklist, and effective Verification Loop. The optional+computed attribute trap (`private_endpoint_settings`, `provisioned_concurrency_config`) is clearly documented with the `terraform apply -replace` workaround — this is a high-value, non-obvious insight. Two targeted fixes: add emoji icons to three-tier headings (D2) and remove the static delivery date from Version Context (A4). Missing evaluation scenarios (C) is the only substantive gap.
