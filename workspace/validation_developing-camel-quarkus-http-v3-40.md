# Best Practices Analysis: developing-camel-quarkus-http-v3-40

**Date**: 2026-10-14
**File**: `packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-http-v3-40/SKILL.md`
**Lines**: 106 (confirmed; hybrid target 100-200, hard limit 500)
**Judged against**: `.claude/rules/skill-structure.md` ("Hybrid knowledge skills") and `TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md`
**Scope of check**: presence and consistency only. No URL was re-fetched.
**Score**: **85/100** (rubric: start at 100; HIGH -4, MEDIUM -1.5, LOW -0.5)

---

## Summary

- Official criteria met: 8/8 (B is N/A)
- Team conventions met: 6/7 (D2 partial)
- HIGH: 2, MEDIUM: 3, LOW: 5

Best-tagged of the four: the Ask First table tags medium items on almost every row, and the Never Do tier deliberately excludes the medium anti-patterns (SKILL.md:75, never-do-patterns.md:64). Defects are two places where SKILL.md is stronger than its own blueprint/register, plus register gaps.

## Official Criteria

| Criterion | Status | Notes |
|---|---|---|
| A1 Frontmatter | ✅ | name = folder; `Use when` present; length under 1536 (regex check); third person |
| A2 Conciseness | ✅ | 106 lines |
| A3 Progressive disclosure | ✅ | all 8 blueprint links exist; anchors checked by reading resolve; blueprints >100 lines have a Contents block |
| A4 Content | ✅ | |
| A5 Workflows | ✅ | N/A |
| A6 Paths | ✅ | |
| B Scripts | N/A | |
| C Evaluation | ✅ | 5 scenarios (scenario 5 is labelled "Anti-Pattern Trap" but typed "Ask First", see L1). Not executed |

## Team Conventions

| Criterion | Status | Notes |
|---|---|---|
| D1 | ✅ | |
| D2 | ⚠️ | H1 and H2 put medium-by-register claims in Always Do |
| D3 | ✅ | table rows sourced; HttpClient 5 version marked unverified |
| D4 | ✅ | representative commands, "log output unverified" |
| D5 | ⚠️ | Never Do row 2 ✅ column is medium (M2) |
| D6 | ✅ | |
| D7 | ✅ | |

## Hybrid-format checks requested

| Check | Result |
|---|---|
| Flat claims have source or tag | ✅ every Always/Never row has a URL; Ask First rows tagged |
| Version Context / Quick Reference rows sourced | ✅ (Quick Ref :94 uses "none", which is acceptable only because the row says representative) |
| Always/Never only High per the skill's own register | 🚫 H1, H2, M2 |
| `@ApplicationScoped` never "mandatory" | ✅ not asserted in SKILL.md; plain RouteBuilder in code (always-do-patterns.md:38, integration-examples.md:15); eval scenarios 1 and 4 have `must_not` at :23 |
| Every medium/unverified item in the register | ⚠️ M1 |
| SKILL.md not stronger than blueprints | 🚫 H1 |

---

## Recommendations by Priority

### HIGH

**H1. "TLSv1.3 default" asserted High; the blueprint and register say the value is medium** (SKILL.md:48, :89; always-do-patterns.md:54; integration-examples.md:55; register:37)
- SKILL.md:48 (Always Do) and Quick Reference :89 cite the pinned 3.40.0 migration guide for "`quarkus.tls.protocols` defaults to `TLSv1.3`". always-do-patterns.md:54 says "default value: https://quarkus.io/guides/tls-registry-reference (unpinned "current" URL, so medium confidence for the value itself)"; register:37 lists "the `quarkus.tls` default value (unpinned URL)" as medium.
- Fix: split the bullet. Keep the verified part in Always Do ("from 3.40.0 `protocols`, `cipher-suites`, `key-exchange-groups` are applied to bridged beans", migration guide). Move the default value to Quick Reference tagged "(medium confidence: unpinned page)" and into Ask First row :57. Adjust eval scenario 1 `must_pass` ("TLSv1.3 only by default").

**H2. Always Do #4 relies on the same single-page data that SKILL.md itself labels medium** (SKILL.md:49 vs :58, :79, :83-88; register:37, :41)
- :49 asserts "`throwExceptionOnFailure` is `true` by default, and a status outside `okStatusCodeRange` throws". Quick Reference :79 says every row from that page is medium; :87 and register:41 record a contradiction in the page on exactly this range; Ask First :58 tags the topic medium.
- Fix: Always Do becomes "Handle `HttpOperationFailedException` with `onException`" with no default claim (and still cites the page only for the exception existing); the default and range stay in Quick Reference/Ask First. Note the exception's Java package is unverified (register:26), so the bullet should say "resolve the import in the IDE".

### MEDIUM

- **M1. Register does not contain every medium/unverified item that SKILL.md or the blueprints tag.**
  - "Java serialization" (SKILL.md:62) and "Multiple TLS identities" (SKILL.md:64) are tagged medium but absent from register:37.
  - integration-examples.md:96-100 "Production notes (medium confidence)" is absent.
  - migration-guide.md:12-13 mark the 4.18 and 4.21 entries "page partially read" but register:37 does not list them.
  - tls-and-security.md:42 (`hostnameVerificationPolicy` medium, single page) is also absent.
  - Fix: add these to "Medium-confidence items".
- **M2** (SKILL.md:71; tls-and-security.md:42) Never Do row 2's ✅ column (`hostnameVerificationPolicy`) is medium (single page) in the blueprint, untagged in SKILL.md. Tag it or say "set verification on the endpoint" with no option name.
- **M3. Irresolvable item not surfaced in SKILL.md** (register:19; fault-tolerance-and-errors.md:60; always-do-patterns.md:64) The `faultToleranceConfiguration` defaults and "does the fallback run on timeout" are "do not assert" items, but SKILL.md Always Do #5 recommends the circuit breaker without any caveat. Add "(defaults and timeout-fallback behaviour unverified; set every option)" to the bullet or a Quick Reference row.

### LOW

- **L1** (evaluation-scenarios.md:85-87) Scenario 5 header says Anti-Pattern Trap but the type line says Ask First decision; the file title says "Five scenarios covering the four types". Relabel.
- **L2** (SKILL.md:72) "no such extension exists" is an inference from a 404 plus absence in the index; register:18 lists the sibling question as irresolvable. Soften to "is not listed in the 3.40.x extension index".
- **L3** (SKILL.md:73) "lacks the Quarkus native support and automatic native SSL" is stated as fact from the extension page; the page states what the extension adds, not what plain `camel-http` lacks. Reword.
- **L4** (SKILL.md:16-17 vs sibling skills) 3.40.0 release date and LTS status are stated High with the releases page here, but medium in platform-http and rest because "the release page shows no date". Align with the core register (see cross-skill patterns).
- **L5** (SKILL.md:94) Source cell "none"; use the template wording "page not recorded".

## Conclusions

Closest to the format's intent. Fix H1 and H2 (two bullets in Always Do) and complete the register for M1; the skill then scores around 92.
