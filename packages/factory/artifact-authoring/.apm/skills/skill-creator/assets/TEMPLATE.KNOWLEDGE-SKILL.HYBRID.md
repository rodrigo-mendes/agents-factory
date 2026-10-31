---
name: [gerund-noun-vMAJOR-MINOR]
description: "[What it teaches, with the exact version]. Use when [trigger specific to this technology and version]. Not for [adjacent versions or runtimes]."
---

> ⚙️ **Hybrid knowledge skill template.** Use this for version-locked, research-derived reference skills
> that are too large for `TEMPLATE.KNOWLEDGE-SKILL.md` (> 150 lines of guidance, or claims that need
> sources). Frontmatter stays `name` + `description` only (no fork, no agent). Keep SKILL.md lean
> (target 100–200 lines, hard limit 500) and move bulk to `blueprints/`.

# [Title] [version]

> Version lock: every claim applies to **[technology] [version]** only. Research date **[YYYY-MM-DD]**.
> Claims tagged **unverified** or **medium confidence** were not fully confirmed against an official page.

## Version Context

| Item | Value | Source (fetched [YYYY-MM-DD]) |
|---|---|---|
| [Technology] | [version, release date, support status] | [exact page URL] |
| [Runtime / platform] | [value] | [exact page URL, or "none recorded" + **unverified**] |

**Version-lifetime risk** (as of [YYYY-MM-DD]; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- [Known successor release or end-of-support date, with source]

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **[Pattern]** — [what and why; **high-confidence claims only**, with an inline source link]. See [patterns](./blueprints/always-do-patterns.md#anchor).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| [Decision] | [A vs B; medium-confidence or unverified items go here, tagged] | "[question to the user]" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| [Anti-pattern with inline source, or tagged **medium confidence**] | [Correct alternative] |

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| [Default / limit / name] | [value] | [exact page URL, or "page not recorded"] |

## External Resources

All fetched [YYYY-MM-DD].

- [Official docs index](URL)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)

<!--
Required blueprints (see skill-structure rule, "Hybrid knowledge skills"):
  blueprints/always-do-patterns.md, never-do-patterns.md, unverified-and-risks.md (with the
  headings "Version-lifetime risk" and "Source Bibliography"), evaluation-scenarios.md (>= 3 scenarios).
Reference implementation: packages/java/quarkus/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-core-v3-40/
-->
