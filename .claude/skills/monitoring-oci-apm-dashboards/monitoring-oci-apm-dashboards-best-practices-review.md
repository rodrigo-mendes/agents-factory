# Best Practices Review: monitoring-oci-apm-dashboards

**Date**: 2026-07-26 (corrected; original 2026-07-25)
**File**: `.claude/skills/monitoring-oci-apm-dashboards/SKILL.md`
**Approx lines**: ~200
**Refs**: authoring-agent-skills/SKILL.md, skill-frontmatter.md

---

## Correction Notice

**Correction date**: 2026-07-26

The previous report (2026-07-25) contained scoring errors:

- **Official score was incorrectly reported as 5/8.** Criterion C (evaluation scenarios) was marked as a gap ("No evaluation-scenarios.md linked"), but `blueprints/evaluation-scenarios.md` is present in the skill directory. This was a false negative that penalised the score by one point.
- **Three-tier structure was complete.** The previous report acknowledged this in criterion A3 but the summary implied structural gaps that did not exist.
- **External Resources and Version Context were present and correct.** These were already marked PASS in the original table; the summary text was misleading by grouping them with real issues.

Corrected scores: **7/8 official**, **6/7 team**. The two remaining official improvement items (A4 year-tied version identifier and B OTLP endpoint discrepancy) are unchanged. The team deduction is for a non-standard `## Function` section at the top of the skill body, which was not noted in the original report.

---

## Summary

| Dimension | Score | Critical Issues |
|-----------|-------|-----------------|
| Official criteria (A1–A6, B, C) | 7/8 | A4 ("OCI Best Practices Framework 2024" year-tied), B (OTLP endpoint discrepancy in troubleshooting section) |
| Team conventions (D1–D7) | 6/7 | D7 (non-standard `## Function` section at top of body) |
| Critical count | 0 blocking / 2 improve |

---

## Official Criteria

| Criterion | Status | Finding |
|-----------|--------|---------|
| A1 — Frontmatter valid | PASS | name matches folder; description has "Use when"; within char limit |
| A2 — Body < 500 lines | PASS | ~200 lines |
| A3 — Three-tier structure present | PASS | All three tiers present and complete: 5 Always Do / 3 Ask First / 4 Never Do — all reference blueprints |
| A4 — No time-sensitive content without caveat | IMPROVE | Version Context "Target version: OCI Best Practices Framework 2024" and "Release date: 2024" — year-tied; same pattern as monitoring-oci-apm skill cluster |
| A5 — External resources with official doc links | PASS | OCI APM, Management Dashboards, OpenTelemetry docs linked in External Resources section |
| A6 — Version context section present | PASS | Version Context section present with key capabilities and breaking changes |
| B — Code/scripts correct, safe, referenced | IMPROVE | Integration Patterns "OTLP spans not appearing" troubleshooting instructs: "Check `OTEL_EXPORTER_OTLP_ENDPOINT` ends with `/20200101/observations/public-span`" — but `validating-oci-observability` and `provisioning-custom-dashboard-oci-observability` both confirm the correct OTel path is `/20200101/opentelemetry/private/v1/traces`. The `public-span` endpoint appears to be outdated or for a different use case. RISK: MEDIUM — could cause agent misconfiguration |
| C — Testing/evaluation scenarios present or linked | PASS | `blueprints/evaluation-scenarios.md` is present in the skill directory (was incorrectly flagged as absent in the original report) |

---

## Team Conventions

| Convention | Status | Finding |
|------------|--------|---------|
| D1 — Naming: kebab-case gerund-noun | PASS | monitoring-oci-apm-dashboards, matches folder |
| D2 — Three-tier architecture (✅⚠️🚫) | PASS | All three tiers with icons, complete and consistent |
| D3 — Version context with breaking changes | PASS | Version Context with key new capabilities |
| D4 — Verification loop | PASS | Verification Loop with 4 OCI CLI audit commands |
| D5 — Anti-patterns with side-by-side code | PASS | Delegates to Never Do Patterns blueprint |
| D6 — External official-doc links | PASS | External Resources section with OCI APM and Management Dashboards docs |
| D7 — Progressive disclosure (blueprints linked) | IMPROVE | Quick Navigation links to blueprints/ are present, but skill body opens with a non-standard `## Function` section that does not appear in the canonical skill template. This section should be removed or merged into the frontmatter description. |

---

## Recommendations by Priority

**ALTA**
- B: Verify the OTLP endpoint path in "OTLP spans not appearing" troubleshooting: `/20200101/observations/public-span` vs `/20200101/opentelemetry/private/v1/traces`. Cross-check with `validating-oci-observability/SKILL.md` (which documents the correct path as the latter). If the `public-span` path is for OCI APM native agent (not OTel), clarify this distinction explicitly to prevent misconfiguration.

**MEDIA**
- A4: Remove "2024" year from Version Context; use "APM GA" as version identifier.

**BAJA**
- D7: Remove or merge the non-standard `## Function` section at the top of the skill body to align with the standard template structure from `authoring-agent-skills/SKILL.md`.

---

## Conclusions

Well-structured skill with complete three-tier architecture, Version Context, External Resources, and evaluation scenarios via `blueprints/evaluation-scenarios.md`. The potential OTLP endpoint discrepancy (B criterion) remains the most actionable finding and should be verified before agents use this skill for instrumentation guidance. Year-tied version context is consistent with the monitoring skills cluster pattern and is a low-risk improvement. The non-standard `## Function` section is a minor structural deviation with no functional impact.
