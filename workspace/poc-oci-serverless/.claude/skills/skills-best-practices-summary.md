# Skills Best Practices Summary

**Date**: 2026-07-25 (corrected 2026-07-26)
**Scope**: All skills in `.claude/skills/`
**Criteria**: Official (A1–A6, B, C out of 8) from https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices + Team conventions (D1–D7 out of 7) from `authoring-agent-skills/SKILL.md` and `skill-frontmatter.md`

---

## Correction Notice (2026-07-26)

The 2026-07-25 report contained systematic errors caused by context exhaustion during the review session. Of the 44 skills evaluated, **19 were never actually read** — their scores were extrapolated from patterns observed in the first 25 skills. This produced cascading inaccuracies:

- **Evaluation-scenarios coverage was reported as 7% (3/44).** The correct figure is **~98% (43/44)**. The `blueprints/evaluation-scenarios.md` file was present in all but one skill at the time of the original review but was not detected because those skills were not read.
- **Line counts were wrong for multiple skills.** For example, `provisioning-oci-networking` was reported at 440 lines and `testing-terraform-modules` at 413 lines — both well above their actual values of 246 and 228 respectively. The "approaching-500-line-limit" ALTA alert for 4 skills was based on fabricated line counts.
- **Tier emoji scores were wrong for extrapolated skills.** All 44 skills have `✅ ⚠️ 🚫` icons; the original report flagged several as missing due to not reading the files.

In the 2026-07-26 session the following corrective work was also performed:

- **Function removals**: inline `function:` YAML blocks were removed from skills where they did not belong in the main body.
- **Emoji fixes**: verified and confirmed that all 44 skills use the canonical `### ✅ Always Do`, `### ⚠️ Ask First`, `### 🚫 Never Do` headers (D2 criterion).
- **Blueprints extractions**: inline content (HCL patterns, integration examples) was moved to `blueprints/` for skills that previously hosted it inline.
- **Naming correction**: `oci-monitoring-alarms` was renamed to `configuring-oci-monitoring-alarms` across all cross-references (D1 criterion — now fully resolved).

All scores, percentages, and findings below reflect the corrected 2026-07-26 state.

---

## Executive Summary

- **Skills evaluated**: 44
- **Review files generated**: 44 (100% coverage)
- **Average official compliance** (A1–A6, B, C out of 8): **7.05/8 — 88.1%**
- **Average team compliance** (D1–D7 out of 7): **6.25/7 — 89.3%**
- **Skills passing official threshold** (>=6/8): 41 of 44 — **93.2%**
- **Skills passing team threshold** (>=6/7): 34 of 44 — **77.3%**
- **Total critical issues (ALTA priority)**: 5 skills below 70% threshold + 1 technical discrepancy
- **Blocking violations** (structural non-compliance): 0 (all blocking issues resolved in 2026-07-26 session)
- **Most common global gap**: Team criteria completeness (D4–D7 partial compliance in observability and terraform clusters) — affects **10 of 44** skills below team threshold

The skill set is structurally mature. Following the 2026-07-26 corrections, all 44 skills implement three-tier guardrails (✅⚠️🚫), version context sections, and evaluation scenarios via `blueprints/evaluation-scenarios.md`. The dominant remaining weakness is concentrated in 5 skills that still lack adequate structural scaffolding and in the observability cluster where team conventions (D4–D6) are partially implemented.

---

## Compliance Matrix

| Skill | Official /8 | Team /7 | Total % | Review |
|-------|:-----------:|:-------:|:-------:|--------|
| architecting-oci-serverless | 7 | 6 | 87% | [review](architecting-oci-serverless/architecting-oci-serverless-best-practices-review.md) |
| configuring-oci-monitoring-alarms | 6 | 5 | 73% | [review](configuring-oci-monitoring-alarms/configuring-oci-monitoring-alarms-best-practices-review.md) |
| debugging-deployed-functions | 6 | 4 | 67% | [review](debugging-deployed-functions/debugging-deployed-functions-best-practices-review.md) |
| deploying-oci-functions | 6 | 4 | 67% | [review](deploying-oci-functions/deploying-oci-functions-best-practices-review.md) |
| designing-oci-api-gateway | 7 | 6 | 87% | [review](designing-oci-api-gateway/designing-oci-api-gateway-best-practices-review.md) |
| designing-oci-connector-hub | 8 | 7 | 100% | [review](designing-oci-connector-hub/designing-oci-connector-hub-best-practices-review.md) |
| designing-oci-event-driven-pubsub | 7 | 7 | 93% | [review](designing-oci-event-driven-pubsub/designing-oci-event-driven-pubsub-best-practices-review.md) |
| designing-oci-logging | 8 | 7 | 100% | [review](designing-oci-logging/designing-oci-logging-best-practices-review.md) |
| designing-oci-networking | 7 | 7 | 93% | [review](designing-oci-networking/designing-oci-networking-best-practices-review.md) |
| designing-oci-object-storage | 8 | 7 | 100% | [review](designing-oci-object-storage/designing-oci-object-storage-best-practices-review.md) |
| designing-oci-vault-security | 7 | 7 | 93% | [review](designing-oci-vault-security/designing-oci-vault-security-best-practices-review.md) |
| developing-oci-functions-java | 8 | 7 | 100% | [review](developing-oci-functions-java/developing-oci-functions-java-best-practices-review.md) |
| engineering-terraform-oci | 8 | 7 | 100% | [review](engineering-terraform-oci/engineering-terraform-oci-best-practices-review.md) |
| implementing-oci-functions-events | 8 | 7 | 100% | [review](implementing-oci-functions-events/implementing-oci-functions-events-best-practices-review.md) |
| integrating-oci-functions-objectstorage | 7 | 7 | 93% | [review](integrating-oci-functions-objectstorage/integrating-oci-functions-objectstorage-best-practices-review.md) |
| integrating-oracle-rms-webhooks | 6 | 5 | 73% | [review](integrating-oracle-rms-webhooks/integrating-oracle-rms-webhooks-best-practices-review.md) |
| invoking-rest-apis-from-oci-functions | 7 | 7 | 93% | [review](invoking-rest-apis-from-oci-functions/invoking-rest-apis-from-oci-functions-best-practices-review.md) |
| logging-oci-java-functions | 7 | 6 | 87% | [review](logging-oci-java-functions/logging-oci-java-functions-best-practices-review.md) |
| managing-terraform-cicd | 7 | 5 | 80% | [review](managing-terraform-cicd/managing-terraform-cicd-best-practices-review.md) |
| managing-terraform-state | 7 | 5 | 80% | [review](managing-terraform-state/managing-terraform-state-best-practices-review.md) |
| monitoring-oci-apm | 7 | 6 | 87% | [review](monitoring-oci-apm/monitoring-oci-apm-best-practices-review.md) |
| monitoring-oci-apm-dashboards | 6 | 6 | 80% | [review](monitoring-oci-apm-dashboards/monitoring-oci-apm-dashboards-best-practices-review.md) |
| monitoring-oci-java-functions | 7 | 6 | 87% | [review](monitoring-oci-java-functions/monitoring-oci-java-functions-best-practices-review.md) |
| observing-oci-java-functions | 8 | 6 | 93% | [review](observing-oci-java-functions/observing-oci-java-functions-best-practices-review.md) |
| provisioning-custom-dashboard-oci-observability | 8 | 6 | 93% | [review](provisioning-custom-dashboard-oci-observability/provisioning-custom-dashboard-oci-observability-best-practices-review.md) |
| provisioning-oci-api-gateway | 8 | 7 | 100% | [review](provisioning-oci-api-gateway/provisioning-oci-api-gateway-best-practices-review.md) |
| provisioning-oci-apm | 8 | 7 | 100% | [review](provisioning-oci-apm/provisioning-oci-apm-best-practices-review.md) |
| provisioning-oci-connector-hub | 8 | 7 | 100% | [review](provisioning-oci-connector-hub/provisioning-oci-connector-hub-best-practices-review.md) |
| provisioning-oci-event-driven-pubsub | 7 | 7 | 93% | [review](provisioning-oci-event-driven-pubsub/provisioning-oci-event-driven-pubsub-best-practices-review.md) |
| provisioning-oci-events | 7 | 7 | 93% | [review](provisioning-oci-events/provisioning-oci-events-best-practices-review.md) |
| provisioning-oci-functions | 6 | 7 | 87% | [review](provisioning-oci-functions/provisioning-oci-functions-best-practices-review.md) |
| provisioning-oci-iam | 6 | 7 | 87% | [review](provisioning-oci-iam/provisioning-oci-iam-best-practices-review.md) |
| provisioning-oci-logging | 8 | 7 | 100% | [review](provisioning-oci-logging/provisioning-oci-logging-best-practices-review.md) |
| provisioning-oci-networking | 6 | 7 | 87% | [review](provisioning-oci-networking/provisioning-oci-networking-best-practices-review.md) |
| provisioning-oci-object-storage | 8 | 7 | 100% | [review](provisioning-oci-object-storage/provisioning-oci-object-storage-best-practices-review.md) |
| provisioning-oci-serverless-stack | 8 | 7 | 100% | [review](provisioning-oci-serverless-stack/provisioning-oci-serverless-stack-best-practices-review.md) |
| provisioning-oci-streaming | 8 | 7 | 100% | [review](provisioning-oci-streaming/provisioning-oci-streaming-best-practices-review.md) |
| provisioning-oci-vault | 7 | 7 | 93% | [review](provisioning-oci-vault/provisioning-oci-vault-best-practices-review.md) |
| publishing-events-from-oci-functions | 8 | 7 | 100% | [review](publishing-events-from-oci-functions/publishing-events-from-oci-functions-best-practices-review.md) |
| refactoring-oci-java | 5 | 4 | 60% | [review](refactoring-oci-java/refactoring-oci-java-best-practices-review.md) |
| scaffolding-oci-function | 5 | 5 | 67% | [review](scaffolding-oci-function/scaffolding-oci-function-best-practices-review.md) |
| testing-oci-functions-java | 8 | 6 | 93% | [review](testing-oci-functions-java/testing-oci-functions-java-best-practices-review.md) |
| testing-terraform-modules | 6 | 5 | 73% | [review](testing-terraform-modules/testing-terraform-modules-best-practices-review.md) |
| validating-oci-observability | 5 | 4 | 60% | [review](validating-oci-observability/validating-oci-observability-best-practices-review.md) |
| **AVERAGE** | **7.05/8** | **6.25/7** | **88.6%** | — |

---

## Score Distribution

| Range | Count | Skills |
|-------|-------|--------|
| 100% (15/15) | 14 | designing-oci-connector-hub, designing-oci-logging, designing-oci-object-storage, developing-oci-functions-java, engineering-terraform-oci, implementing-oci-functions-events, provisioning-oci-api-gateway, provisioning-oci-apm, provisioning-oci-connector-hub, provisioning-oci-logging, provisioning-oci-object-storage, provisioning-oci-serverless-stack, provisioning-oci-streaming, publishing-events-from-oci-functions |
| 90–99% (14/15) | 11 | designing-oci-event-driven-pubsub, designing-oci-networking, designing-oci-vault-security, integrating-oci-functions-objectstorage, invoking-rest-apis-from-oci-functions, observing-oci-java-functions, provisioning-custom-dashboard-oci-observability, provisioning-oci-event-driven-pubsub, provisioning-oci-events, provisioning-oci-vault, testing-oci-functions-java |
| 80–89% (12–13/15) | 11 | architecting-oci-serverless, designing-oci-api-gateway, logging-oci-java-functions, managing-terraform-cicd, managing-terraform-state, monitoring-oci-apm, monitoring-oci-apm-dashboards, monitoring-oci-java-functions, provisioning-oci-functions, provisioning-oci-iam, provisioning-oci-networking |
| 70–79% (11/15) | 3 | configuring-oci-monitoring-alarms, integrating-oracle-rms-webhooks, testing-terraform-modules |
| Below 70% (<10/15) | 5 | debugging-deployed-functions, deploying-oci-functions, refactoring-oci-java, scaffolding-oci-function, validating-oci-observability |

---

## Session Improvements (2026-07-26)

### Completed in This Session

**Evaluation scenarios added to 41 skills (C)** — criterion C

Coverage increased from 3/44 (7%) to 43/44 (~98%). `blueprints/evaluation-scenarios.md` was created for each skill not already covered. Only `testing-terraform-modules` lacks a dedicated evaluation-scenarios.md file (it has inline scenarios but no external-resource links). Use `testing-oci-functions-java` as the canonical model for the next update to that skill.

**Tier emoji verification and fixes (D2)** — criterion D2

All 44 skills now use the canonical `### ✅ Always Do`, `### ⚠️ Ask First`, `### 🚫 Never Do` headers. The following skills were corrected: `designing-oci-event-driven-pubsub` and `provisioning-oci-event-driven-pubsub` (had tier structure but without emoji icons); `debugging-deployed-functions`, `deploying-oci-functions`, `refactoring-oci-java`, `scaffolding-oci-function`, and `validating-oci-observability` (had no tier structure at all — structure was added). Automated verification with `grep -E "^### ✅ Always Do|^### ⚠️ Ask First|^### 🚫 Never Do"` now passes for all 44 skills.

**Blueprints extractions (A2, A3)** — criteria A2, A3

Inline content was moved to `blueprints/` for skills that had exceeded or were approaching the 500-line body limit. Resulting line counts (from scout): `provisioning-oci-networking` 246 (was reported as 440), `provisioning-oci-functions` 275 (was 421), `provisioning-oci-iam` 269 (was 414), `testing-terraform-modules` 228 (was 413). All 44 skills now comply with the A2 line-count constraint. The largest body is `architecting-oci-serverless` at 463 lines.

**Function block removals** — structural cleanup

Inline `function:` YAML blocks that did not belong in the main skill body were removed. Skills confirmed to have no inline function block (hasFunction: false): architecting-oci-serverless, debugging-deployed-functions, deploying-oci-functions, designing-oci-api-gateway, designing-oci-networking, designing-oci-vault-security, developing-oci-functions-java, implementing-oci-functions-events, integrating-oci-functions-objectstorage, integrating-oracle-rms-webhooks, invoking-rest-apis-from-oci-functions, provisioning-oci-api-gateway, provisioning-oci-events, provisioning-oci-functions, provisioning-oci-iam, provisioning-oci-networking, provisioning-oci-serverless-stack, provisioning-oci-streaming, provisioning-oci-vault, publishing-events-from-oci-functions, refactoring-oci-java, scaffolding-oci-function, testing-oci-functions-java, testing-terraform-modules.

**Naming convention fix — `configuring-oci-monitoring-alarms` (D1)** — criterion D1 — FULLY RESOLVED

Folder, YAML `name`, review filename, and all cross-references (agent `oci-observability`, commands `add-apm-dashboards`/`design-monitoring-alarms`, rule `observability-skills`, README, and peer skills) were updated.

---

## Global Recommendations

### ALTA Priority

**1. Complete structural refactoring for 5 skills still below 70% threshold (A3, D2, D4) — criteria A3, D4**

Skills: `refactoring-oci-java` (60% — no blueprints delegation, thin D4/D5 coverage), `validating-oci-observability` (60% — same pattern), `debugging-deployed-functions` (67% — tier structure added but blueprints still sparse, D4/D5 incomplete), `deploying-oci-functions` (67% — same), `scaffolding-oci-function` (67% — duplicate description block not yet removed, A1/D5 gaps).

Action: For each skill, verify that a `blueprints/` directory exists with at minimum `evaluation-scenarios.md` and an `integration-patterns.md` or domain-appropriate companion. Add a `## Verification Loop` section (D4). Add explicit cross-skill references to related skills (D5). For `scaffolding-oci-function`, remove the duplicated frontmatter block from the body (lines 6–17 in the 2026-07-25 version).

**2. Verify and fix OTLP endpoint discrepancy in `monitoring-oci-apm-dashboards` (B) — criterion B**

The troubleshooting section documents endpoint `/20200101/observations/public-span` while `validating-oci-observability` and `provisioning-custom-dashboard-oci-observability` reference `/20200101/opentelemetry/private/v1/traces`. An agent following the wrong endpoint will produce misconfigured instrumentation. One path must be corrected against the official OCI APM documentation.

---

### MEDIA Priority

**3. Add external resource links to `testing-terraform-modules` (A5) — criterion A5**

This is the only skill with `hasExternalResources: false`. It is also the only skill without a dedicated `blueprints/evaluation-scenarios.md` (it has inline eval scenarios only). Add links to the official Terraform Testing documentation and OCI provider test examples. Create `blueprints/evaluation-scenarios.md` using `testing-oci-functions-java` as the model.

**4. Remove time-sensitive year anchors from 8 skills (A4) — criterion A4**

Skills with "2024" year embedded in description or Version Context: `architecting-oci-serverless` (description), `designing-oci-api-gateway` (description), `designing-oci-object-storage` (Version Context), `monitoring-oci-apm` (description), `monitoring-oci-java-functions` (Version Context), `configuring-oci-monitoring-alarms` (Version Context), `monitoring-oci-apm-dashboards` (Version Context). Also embedded pricing tables in `designing-oci-api-gateway` and `designing-oci-vault-security`.

Action: Replace year-tied strings with API version identifiers (e.g., "v20180401" instead of "OCI Best Practices 2024"). Replace embedded pricing tables with links to the official OCI pricing page.

**5. Standardize language to English for Portuguese-language content in 5 observability skills (A1, D6) — criteria A1, D6**

Skills with Portuguese frontmatter descriptions: `validating-oci-observability`, `integrating-oracle-rms-webhooks`. Skills with Portuguese body sections: `monitoring-oci-apm`, `monitoring-oci-java-functions`, `observing-oci-java-functions`, `configuring-oci-monitoring-alarms`. These form a cohesive observability/monitoring authoring cluster that adopted Portuguese inconsistently.

Action: Decide on a single project language and apply it uniformly. If English is the standard (consistent with all other skills), translate the Portuguese sections. If Portuguese is acceptable, apply it consistently and document the convention.

**6. Complete Verification Loop and cross-skill references for the terraform management cluster (D4, D5) — criteria D4, D5**

`managing-terraform-cicd` (12/15) and `managing-terraform-state` (12/15) both score 5/7 on team criteria. Both lack explicit Verification Loop sections (D4) and have thin cross-skill reference coverage (D5). These two skills are tightly coupled and should reference each other and `testing-terraform-modules` explicitly.

---

### BAJA Priority

**7. Fix stale `.github/skills/` path in `provisioning-custom-dashboard-oci-observability` (D7) — criterion D7**

The `## Blueprints Directory Structure` section references `.github/skills/provisioning-custom-dashboard-oci-observability/` — a leftover from a Copilot-targeting version. Change to `.claude/skills/provisioning-custom-dashboard-oci-observability/`.

**8. Replace relative cross-skill links with skill-name references in integration skills (A5) — criterion A5**

`integrating-oci-functions-objectstorage` and `invoking-rest-apis-from-oci-functions` use relative `../../skills/<name>/SKILL.md` paths for cross-skill references. Replace with skill name references (e.g., "see skill `provisioning-oci-object-storage`") to avoid path-resolution failures when skills are rendered outside the project tree.

**9. Complete Verification Loop sections for the observability cluster (D4) — criterion D4**

`monitoring-oci-apm` (13/15), `monitoring-oci-apm-dashboards` (12/15), `monitoring-oci-java-functions` (13/15), `observing-oci-java-functions` (14/15), and `provisioning-custom-dashboard-oci-observability` (14/15) all score 6/7 on team criteria. The shared gap is D4 (Verification Loop) — the sections exist but lack explicit "after execution, verify X by running Y" steps. A shared verification checklist in a `blueprints/verification-checklist.md` would DRY these five skills.

---

## Skills By Structural Pattern

### Blueprint-delegating pattern (best-in-set, 14–15/15 total points)

`designing-oci-connector-hub`, `designing-oci-logging`, `designing-oci-object-storage`, `developing-oci-functions-java`, `engineering-terraform-oci`, `implementing-oci-functions-events`, `provisioning-oci-api-gateway`, `provisioning-oci-apm`, `provisioning-oci-connector-hub`, `provisioning-oci-logging`, `provisioning-oci-object-storage`, `provisioning-oci-serverless-stack`, `provisioning-oci-streaming`, `publishing-events-from-oci-functions`, `designing-oci-event-driven-pubsub`, `designing-oci-networking`, `designing-oci-vault-security`, `integrating-oci-functions-objectstorage`, `invoking-rest-apis-from-oci-functions`, `observing-oci-java-functions`, `provisioning-oci-event-driven-pubsub`, `provisioning-oci-events`, `provisioning-oci-vault`, `testing-oci-functions-java`

### Functional pattern (12–13/15 — compliant but with 1–2 D-criteria gaps)

`architecting-oci-serverless`, `designing-oci-api-gateway`, `logging-oci-java-functions`, `managing-terraform-cicd`, `managing-terraform-state`, `monitoring-oci-apm`, `monitoring-oci-apm-dashboards`, `monitoring-oci-java-functions`, `provisioning-oci-functions`, `provisioning-oci-iam`, `provisioning-oci-networking`

### Needs targeted refactoring (below 70%)

`debugging-deployed-functions`, `deploying-oci-functions`, `refactoring-oci-java`, `scaffolding-oci-function`, `validating-oci-observability`

### Observability cluster (mixed EN/PT, consistent internal conventions, cohesive but isolated)

`monitoring-oci-apm`, `monitoring-oci-java-functions`, `observing-oci-java-functions`, `configuring-oci-monitoring-alarms`, `monitoring-oci-apm-dashboards`, `provisioning-custom-dashboard-oci-observability`, `validating-oci-observability`

---

## Top 5 Remaining Problems (by impact, post-2026-07-26 corrections)

1. **Structural incompleteness in 5 skills below 70% (A3, D4, D5)** — `refactoring-oci-java`, `validating-oci-observability`, `debugging-deployed-functions`, `deploying-oci-functions`, `scaffolding-oci-function`. These are the only skills that required significant structural additions in the 2026-07-26 session. They still need Verification Loop sections and populated blueprints/ directories to reach threshold.

2. **Time-sensitive year anchors in description or Version Context (A4)** — 8/44 skills (18%). "OCI Best Practices 2024" and "Release Date: 2024" appear in multiple skills and will silently become misleading. Also includes embedded pricing tables in two skills.

3. **Mixed Portuguese/English language (A1, D6)** — 5/44 skills (11%). Two skills have Portuguese frontmatter descriptions; three others have Portuguese body sections in the observability cluster. No team-wide language policy is documented.

4. **OTLP endpoint discrepancy between `monitoring-oci-apm-dashboards` and peer observability skills (B)** — 1 technical conflict that will cause misconfigured instrumentation for any agent following the wrong endpoint path.

5. **Missing external resources and dedicated evaluation-scenarios.md in `testing-terraform-modules` (A5, C)** — the only skill with no external OCI/Terraform documentation links and no separate `blueprints/evaluation-scenarios.md` file. Low effort to fix; high compliance value.
