# Best Practices Analysis (round 2, final): developing-camel-quarkus-xslt-v3-40

**Date**: 2026-10-14
**File**: `packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-xslt-v3-40/SKILL.md`
**Lines**: 102
**Judged against**: hybrid knowledge skill rule + `TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md`; shared facts `workspace/_family_facts_v3.40.md`
**Method note**: URLs not fetched; presence and consistency only. Multi-claim rule: HIGH when a bullet mixes different evidence/confidence, MEDIUM for several same-source facts.

**Score: 86/100** (-4 per HIGH, -1.5 per MEDIUM, -0.5 per LOW)

## Summary

- Official A1-A6, B, C: 8/8. Team D1-D7: 7/7 on structure; guardrail purity affected by H1.
- HIGH 1, MEDIUM 5, LOW 4.

## The 8 hybrid checks

| # | Check | Result |
|---|---|---|
| 1 | High-only Always/Never, High alternatives, one claim per bullet | Mostly PASS: Never Do 4 rows and alternatives High. Always Do 1 and 3 hold several facts (M1); H1 confidence conflict |
| 2 | Source column on all Version Context / Quick Reference rows | PASS (URL or "page not recorded" on every row, lines 16-21 and 78-88) |
| 3 | Shared facts = family tags | PASS (LTS date, versions, Quarkus 3.40 LTS, no CQ on Quarkus 4 medium, CQ end date unverified, @ApplicationScoped fact in integration-examples.md:3). Jackson 3 is `unverified` here but medium in rest (cross-skill) |
| 4 | Register counts and mapping | Counts PASS (U1-U14 = 14, M1-M8 = 8, matches header line 3). Mapping misses two tags (M2) |
| 5 | No claim stronger in SKILL.md than blueprint | One conflict (H1) |
| 6 | `@ApplicationScoped` | PASS (always-do-patterns.md:25, integration-examples.md:3, extension-functions.md:29 state "no @ApplicationScoped"; no sample has it) |
| 7 | Links and anchors | PASS (#1-build-time-template-sources, #2-classpath-templates-in-native-mode, #3-secure-processing-stays-on, the six never-do contents anchors, #version-lifetime-risk, #source-bibliography all resolve; 5 blueprint files exist) |
| 8 | Scenarios | PASS (5 scenarios, all 4 types; evaluation-scenarios.md:22 has the `@ApplicationScoped` must_not) |

## Recommendations by Priority

### HIGH

- **H1 (checks 1 and 5, SKILL.md:46 vs SKILL.md:80, native-mode.md:18, unverified-and-risks.md:18 U2)**: Always Do 1 states as High that listed sources "are compiled into Java classes at build time" and mandates listing every template, while the Quick Reference says which properties are build-time is `unverified`, native-mode.md:18 files `sources` under "Medium confidence and unverified" ("treat as build-time"), and U2 is irresolvable. The extension page establishes compilation of listed sources; it does not establish that `sources` is a build-time-fixed property. Fix: reword the bullet to the page statement only ("sources listed are precompiled; scheme-less = classpath:"), drop "every" (unlisted templates still run on JVM, SKILL.md:67), and keep the build-time property question in Ask First.

### MEDIUM

- **M1 (SKILL.md:46, 48)**: Always Do 1 carries two facts (precompiled at build time; scheme-less = classpath:); Always Do 3 carries three (disabling permits extension functions; startup warning; disable only if all templates trusted) plus an implied "default is secure processing on" that is asserted without a quote (always-do-patterns.md:53). Split to one claim per bullet.
- **M2 (unverified-and-risks.md:7, 45-63; SKILL.md:88)**: the `unverified` tag on Jackson 3 (register line 7) has no U/M id, and `(log output unverified)` in Quick Reference line 88 is absent from the mapping. Add lines or reword. Line 7 also leaks process ("mentioned in the caller's brief").
- **M3 (never-do-patterns.md:36)**: "Xalan-J 2.7.x predates JAXP 1.5" is an unsourced assertion in a block headed high confidence, while U5 says the Xalan-J version claims are unverified. Source it or tag it.
- **M4 (register line 67, bibliography)**: states "the fetch tool returns summaries, so confirm exact wording" while all Always/Never claims are High; add which High claims rest on summarised pages (hardening claims in security-hardening-3-40.md come from summary text).
- **M5 (SKILL.md:20, 54-55 vs register M1-M2)**: Version Context Saxon row and Ask First rows carry medium tags correctly, but SKILL.md:85 Quick Reference lists Saxon defaults medium while SKILL.md:86 (Saxon error properties, same page) is untagged; tag consistently.

### LOW

- extension-functions.md:19 import "not shown on the page" (fine, disclosed); 
- never-do-patterns.md:67-68 sample uses `platform-http:` not declared in the skill's dependencies.
- migration-guide.md:12 mentions "AdviceWith in 3.36" as a core-skill matter without source here.
- High family facts are untagged in Version Context (rest tags them); style only.

## Conclusions

Cleanest of the four on guardrails: Never Do and its alternatives are all High and sourced; scenarios are thorough (5). Single real defect is the High-vs-unverified build-time conflict. Fixing H1 and M1/M2 gives about 94.
