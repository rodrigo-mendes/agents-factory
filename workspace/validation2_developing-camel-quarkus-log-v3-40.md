# Best Practices Analysis (round 2, final): developing-camel-quarkus-log-v3-40

**Date**: 2026-10-14
**File**: `packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-log-v3-40/SKILL.md`
**Lines**: 110
**Judged against**: hybrid knowledge skill rule + `TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md`; shared facts `workspace/_family_facts_v3.40.md`
**Method note**: URLs not fetched; presence and consistency only. Multi-claim rule: HIGH when a bullet mixes different evidence/confidence, MEDIUM for several same-source facts.

**Score: 83/100** (-4 per HIGH, -1.5 per MEDIUM, -0.5 per LOW)

## Summary

- Official A1-A6, B, C: 8/8. Team D1-D7: 6/7 (D2/D5 on masking claims).
- HIGH 2, MEDIUM 5, LOW 3.

## The 8 hybrid checks

| # | Check | Result |
|---|---|---|
| 1 | High-only Always/Never, High alternatives, one claim per bullet | FAIL (H2); Always Do 1 multi-claim (M1); Never Do 3 alternative equivalence (M2) |
| 2 | Source column on all rows | PASS (lines 16-22, 82-96) |
| 3 | Shared facts = family tags | FAIL on one: Identifier lookup (H1). Others PASS (LTS, versions, Quarkus 3.40 LTS, Quarkus 4 medium, end date unverified). Quarkus 4 post: the Java 21 base detail is omitted (LOW) |
| 4 | Register counts and mapping | Counts PASS (R1-R2, U1-U6, M1-M8 match header line 3). Mapping misses two tags (M3) |
| 5 | No claim stronger in SKILL.md than blueprint | One conflict (H2) |
| 6 | `@ApplicationScoped` | PASS (masking-and-security.md:23 states it is on the CDI bean, not on a route; integration-examples.md:15,45 route plain, formatter bean scoped; evaluation-scenarios.md:19,23) |
| 7 | Links and anchors | PASS (#1-eip-versus-component, #2-endpoint-masking, #3-camel-quarkus-mdc, the five never-do contents anchors, #1-dumping-headers-and-properties-severity-critical, #5-runtime-trace-below-min-level-severity-medium-medium-confidence, #version-lifetime-risk, #source-bibliography resolve; 6 blueprint files exist) |
| 8 | Scenarios | PASS (5 scenarios, all 4 types; evaluation-scenarios.md:23 has the `@ApplicationScoped` must_not) |

## Recommendations by Priority

### HIGH

- **H1 (check 3, masking-and-security.md:23, unverified-and-risks.md:25 U6, :55, integration-examples.md:71)**: the log skill calls "whether Camel's name lookup works with `@Identifier`" unverified. The family facts mark only "ArC removal of an `@Identifier`-only bean" as Unverified, and the bean skill states as High (cdi.html) that the CDI guide documents `@Identifier` for naming beans used from routes (cdi-and-native.md:15). Same fact, two confidences. Fix: split U6 into (a) lookup: align with bean (High per cdi.html) and (b) removal: Unverified, exactly the family tag; keep `@Named` in the sample as the safe choice.
- **H2 (checks 1 and 5, SKILL.md:49 and :72 vs masking-and-security.md:7)**: Always Do 2 and the Never Do alternative present `logMask=true` as the remedy for "secrets or PII", while the blueprint documents that the default masking formatter masks only key-named values, URI userinfo passwords and PEM private-key blocks. Body PII is not covered; integration-examples.md:22-24,76 even expects a masked `pan` from `logMask=true`. Never Do row 1 also states "often `Authorization`" (an inference, not on the page) and "default to `false`" for `showProperties`, which is recorded nowhere in the Quick Reference (line 84 lists showAll/showHeaders only) or in log-component-options.md:16-24. Fix: SKILL.md bullet = "logMask=true masks key-named values, URI passwords and PEM keys (log-eip page)"; drop "often Authorization" or tag it; record the showProperties default and its page; correct the integration-examples.md:76 expectation or use a key the default formatter masks.

### MEDIUM

- **M1 (SKILL.md:48)**: Always Do 1 carries two claims from two pages (EIP quote; component options). Split.
- **M2 (SKILL.md:74, never-do-patterns.md:34-42, evaluation-scenarios.md:57)**: the ✅ replaces `camel.main.mdcLoggingKeysPattern` with `quarkus.camel.mdc.custom-exchange-headers`/`custom-exchange-properties`. Nothing in the skill states the two are equivalent (the sources only say the old key is deprecated and that the new properties exist); scenario 3 enforces the mapping. Cite the page sentence or tag medium.
- **M3 (register mapping lines 40-57)**: no line for "Custom mask (medium confidence for the wiring)" (masking-and-security.md:21) nor for "(log output unverified)" (integration-examples.md:77). The "R2 | SKILL.md Version Context" row points to the wrong section (the tag is in Version-lifetime risk, SKILL.md:26).
- **M4 (integration-examples.md:71)**: "The bean sample below keeps `@Named`" but the bean sample is above (lines 42-50); the unverified note is attached to the wrong place.
- **M5 (quarkus-logging.md:15 vs SKILL.md:94)**: the blueprint admits the research "did not record reading these values" on the 3.40 selector, yet Quick Reference lists the unpinned guide as Source for level/min-level defaults; tagged medium, but say "value page not recorded for 3.40".

### LOW

- SKILL.md:25 omits the High detail "Java 21 as the new base version" that the other three include.
- migration-guide.md:9 "now documented" implies a change versus 3.15 that is not sourced.
- Register U6/R2 classification differs from sibling skills (cross-skill).

## Conclusions

Strong on defaults (all sourced), deprecation guidance and medium-tag discipline. Risk: the masking guidance reads as stronger protection than the blueprint supports (H2), and U6 diverges from the family fact (H1). Fixing H1/H2/M1-M3 gives about 92.
