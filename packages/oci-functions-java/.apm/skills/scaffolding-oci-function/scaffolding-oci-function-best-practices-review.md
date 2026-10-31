# Best Practices Review: scaffolding-oci-function

**Date**: 2026-07-25
**File**: `.claude/skills/scaffolding-oci-function/SKILL.md`
**Approx lines**: ~460
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Correction Notice

**Correction date**: 2026-07-26

The previous report (dated 2026-07-25) contained two material errors:

1. **Ask First section falsely reported as missing.** The `## ⚠️ Ask First` section is present in the skill body. The previous report incorrectly stated it was absent and penalised A3, D2 on that basis.
2. **Scores were consequently understated.** The previous report scored 4/8 (official) and 4/7 (team). Both scores have been corrected upward to reflect the actual state of the skill.

All findings below supersede the previous report.

---

## Summary

| Dimension | Score | Notes |
|-----------|-------|-------|
| Official criteria (A1–A6, B, C) | 6/8 | Genuine gaps: A2 (body approaching 500-line limit at ~460 lines), A5 (no External Resources section) |
| Team conventions (D1–D7) | 5/7 | Genuine gaps: D6 (no External Resources section), D7 (large inline templates not yet delegated to blueprints/) |
| Critical count | 0 blocking / 3 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | Frontmatter valid and well-formed; no duplicate description block |
| A2 — Body < 500 lines | IMPROVE | ~460 lines — approaching the 500-line limit; large inline templates (Java handler, Dockerfile, build-push.py) are the primary contributors and should be migrated to blueprints/ before the limit is exceeded |
| A3 — Three-tier structure present | PASS | Complete three-tier structure present: `## ✅ Always Do`, `## ⚠️ Ask First`, and `## 🚫 Never Do` sections all present |
| A4 — No time-sensitive content without caveat | PASS | FDK 1.1.11/SDK 3.86.0 version noted with caveat to read from existing pom.xml |
| A5 — External resources with official doc links | IMPROVE | No `## External Resources` section; templates/ reference is internal only; FDK Java docs, OCI Functions docs, and Corretto 17 download link are not surfaced |
| A6 — Version context section present | PASS | `## Version Context` section present |
| B — Code/scripts correct, safe, referenced | PASS | Extensive inline Java, Dockerfile, and bash templates appear technically correct; `build-push.py` template is thorough |
| C — Testing/evaluation scenarios present or linked | PASS | `blueprints/evaluation-scenarios.md` linked |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | scaffolding-oci-function, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers present: ✅ Always Do, ⚠️ Ask First, 🚫 Never Do |
| D3 — Version context with breaking changes | PASS | Dedicated `## Version Context` section present |
| D4 — Verification loop | PASS | `## Checklist: Scaffold Complete` serves as verification loop |
| D5 — Anti-patterns with side-by-side code | PASS | 🚫 Never Do section inline with clear anti-patterns |
| D6 — External official-doc links | IMPROVE | No `## External Resources` section with official docs |
| D7 — Progressive disclosure (blueprints linked) | IMPROVE | `blueprints/evaluation-scenarios.md` linked, but large inline templates (Java handler, Dockerfile, build-push.py) not yet delegated to blueprints/; body at ~460 lines is heavy and close to the limit |

---

## Recommendations by Priority

**ALTA**
- A2/D7: Extract the Java handler, Dockerfile, and build-push.py inline templates to `blueprints/` (e.g., `blueprints/handler-templates.md`, `blueprints/dockerfile-template.md`) and link from a Quick Navigation section. Body is at ~460 lines and will breach the 500-line limit with any meaningful addition.

**MEDIA**
- A5/D6: Add an `## External Resources` section linking FDK Java docs, OCI Functions docs, and the Corretto 17 download page.

**BAJA**
- No additional low-priority findings. Core structure (three tiers, Version Context, evaluation-scenarios.md) is in place.

---

## Conclusions

This skill is structurally sound: the complete three-tier structure (✅ Always Do, ⚠️ Ask First, 🚫 Never Do), Version Context section, and blueprints/evaluation-scenarios.md link are all present. The two genuine gaps are the absence of an External Resources section and the accumulation of large inline templates that push the body toward the 500-line limit. Migrating those templates to blueprints/ is the most impactful next step.
