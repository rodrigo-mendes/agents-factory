# Best Practices Review: architecting-oci-serverless

**Date**: 2026-07-25
**File**: `.claude/skills/architecting-oci-serverless/SKILL.md`
**Approx lines**: 444 (non-blank lines: 349)
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 6/8 | A4 (time-sensitive "2024" in description and body) |
| Team conventions (D1–D7) | 6/7 | D5 (anti-patterns summarized inline but no side-by-side code in SKILL.md body) |
| Critical count | 0 blocking / 2 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid (name, description, format) | PASS | `name: architecting-oci-serverless` matches folder; description is third-person, specific, includes "Use when"; well under 1536 chars |
| A2 — Body < 500 lines | PASS | 444 total file lines; within limit |
| A3 — Three-tier structure present (Always/Ask/Never) | PASS | `### ✅ Always Do`, `### ⚠️ Ask First`, `### 🚫 Never Do` all present at lines 88/101/115, delegating to blueprints |
| A4 — No time-sensitive content without caveat | IMPROVE | Description (line 3) includes "OCI Best Practices 2024"; Version Context (line 11) repeats "Target Edition: OCI Best Practices 2024"; line 15 says "Key Capabilities (2024+)" — none flagged as potentially stale |
| A5 — External resources with official doc links | PASS | Comprehensive External Resources section (lines 406–443) with 20+ official OCI doc links, all using HTTPS |
| A6 — Version context section present | PASS | `## Version Context` at line 6 covers technology, edition, key capabilities, service limits, and critical agent warning |
| B — Code/scripts are correct, safe, referenced | PASS | Verification Loop (lines 204–292) has explicit OCI CLI bash commands, expected outputs, exit codes, and troubleshooting table |
| C — Testing/evaluation scenarios present or linked | IMPROVE | No `evaluations.json` or `evaluation-scenarios.md` blueprint present or linked; Quick Navigation does not reference any evaluation artifact |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | `architecting-oci-serverless` is gerund-noun; `name` field matches folder name |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers with correct icons present under `## Blueprints & Guardrails`; each delegates detailed content to blueprint files |
| D3 — Version context with breaking changes | PASS | Version Context present; Critical Agent Warning block provides version-specific guidance; no breaking-changes list but domain is architectural rather than versioned API |
| D4 — Verification loop | PASS | Seven-step Verification Loop with bash commands, exit codes, expected outputs, and troubleshooting (lines 204–292) |
| D5 — Anti-patterns with side-by-side code | IMPROVE | Never Do section (lines 115–126) lists prohibited patterns with brief prose but no side-by-side wrong/correct code in SKILL.md body; blueprints directory exists (`blueprints/never-do-patterns.md`) but the SKILL.md body alone does not satisfy the convention for a quick-reference inline anti-pattern |
| D6 — External official-doc links | PASS | External Resources section with organized subsections (Official Documentation, API Gateway, IAM & Security, Architecture & Pricing, Open Source) |
| D7 — Progressive disclosure (blueprints linked) | PASS | Quick Navigation links to `blueprints/always-do-patterns.md`, `blueprints/ask-first-decisions.md`, `blueprints/never-do-patterns.md`; all three blueprint files confirmed present |

---

## Recommendations by Priority

**MEDIA**
- A4: Remove the year "2024" from the frontmatter description (line 3) and qualify the Version Context "Target Edition" line with a "verify currency" note or link to the official OCI release notes page. The description is the most persistent string — embedding a year ties it to a point in time that will silently expire.

**BAJA**
- C: Add or link an `evaluations.json` or `evaluation-scenarios.md` covering at least: correct subnet placement decision (Functions private vs public), IAM least-privilege scope, cold-start mitigation selection, and credential-scan pass/fail.
- D5: Add a minimal two-line wrong/correct code pair directly in the Never Do section of SKILL.md so the prohibition is self-contained (e.g., hardcoded credential `config["DB_PASSWORD"] = "secret"` vs Vault retrieval pattern) before delegating full examples to the blueprint.

---

## Conclusions

Strong architectural reference skill. Three-tier structure correct and complete, progressive disclosure to blueprints observed, Verification Loop is thorough with exit codes. Main gap is the "2024" year anchoring in description and Version Context (A4), which will silently age into misinformation. Missing evaluation scenarios (C) is a pattern shared by most skills in the set.
