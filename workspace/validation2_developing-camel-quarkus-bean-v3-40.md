# Best Practices Analysis (round 2, final): developing-camel-quarkus-bean-v3-40

**Date**: 2026-10-14
**File**: `packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-bean-v3-40/SKILL.md`
**Lines**: 104
**Judged against**: hybrid knowledge skill rule + `TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md`; shared facts `workspace/_family_facts_v3.40.md`
**Method note**: URLs not fetched; presence and consistency only. Multi-claim rule: HIGH when a bullet mixes different evidence/confidence, MEDIUM for several same-source facts.

**Score: 82/100** (-4 per HIGH, -1.5 per MEDIUM, -0.5 per LOW)

## Summary

- Official A1-A6, B, C: 8/8. Team D1-D7: 6/7 (D2 guardrail purity, D5 sample conflicts).
- HIGH 2, MEDIUM 5, LOW 4.

## The 8 hybrid checks

| # | Check | Result |
|---|---|---|
| 1 | High-only Always/Never, High alternatives, one claim per bullet | FAIL (H1, H2); Never Do rows 1-2 and alternatives High; row 3 alternative questionable (M2) |
| 2 | Source column on all rows | PASS (lines 16-21, 81-92) |
| 3 | Shared facts = family tags | PASS: LTS, versions, Quarkus 3.40 LTS, Quarkus 4 (medium), end date (unverified), @ApplicationScoped fact (Always Do 4), Identifier/@Named unremovable (High) and ArC removal (unverified), junit rename + stub (blueprints). Java tagged medium (differs from rest) |
| 4 | Register counts and mapping | PASS counts (U1-U11 = 11, header "11 unverified"; M1-M11). Mapping covers every SKILL.md tag; two blueprint tags unmapped (M4) |
| 5 | No claim stronger in SKILL.md than blueprint | FAIL (H1: scope requirement is medium in blueprint; H2) |
| 6 | `@ApplicationScoped` | PASS (always-do-patterns.md:50 "only for @Inject/@ConfigProperty"; injection sample at :59-63 has `@ConfigProperty`; route samples plain; remaining uses are on bean classes) |
| 7 | Links and anchors | PASS (#1-named-bean-recipe ... #4-routebuilder-scope-only-when-injecting, #named-vs-identifier, #medium-confidence-pitfalls, #scope-and-discovery, #tag-to-register-mapping, #version-lifetime-risk, #source-bibliography resolve; 5 blueprint files exist) |
| 8 | Scenarios | PASS (4 types; evaluation-scenarios.md:21-22 have the `@ApplicationScoped` must_not items) |

## Recommendations by Priority

### HIGH

- **H1 (checks 1 and 5, SKILL.md:46, Always Do 1)**: "give every route-referenced bean a scope" is stated as an always-rule backed by High, but the necessity of a scope is medium everywhere else: SKILL.md:56 (Ask First, medium), cdi-and-native.md:36 ("Medium confidence"), register M7. The cited CDI guide only "shows this recipe". The bullet also bundles three annotations plus the native-mode claim. Fix: Always Do = "`@RegisterForReflection` on beans referenced by name (native guide, CDI guide)"; keep scope and name in Ask First; the recipe stays in the blueprint.
- **H2 (checks 1 and 5, SKILL.md:47, Always Do 2)**: "Set `method=` / `.bean(name, method)` on bean calls" is High only for the option's existence; the reason to always pin is medium (always-do-patterns.md:33 "medium confidence"; register M2, M11). It is also contradicted by the skill's own material: integration-examples.md:33 calls `.bean("orderService")` relying on `@Handler`; evaluation-scenarios.md:18 accepts "or uses @Handler"; bean-binding.md:62 recommends `@Handler`. Fix: "Select the target method explicitly, with `method=`, `.bean(name, method)` or `@Handler`" and tag the rationale medium in the blueprint, or move to Ask First.

### MEDIUM

- **M1 (never-do-patterns.md:39-44)**: the Mutable-state sample `Acc` has no scope, name or `@RegisterForReflection` yet is referenced as `bean:acc`; it violates Always Do 1 and scenario 4 must_pass ("Adds a bean-defining scope"). Make the sample conform (`@ApplicationScoped @Named("acc") @RegisterForReflection`).
- **M2 (SKILL.md:73)**: the alternative `scope=Request` is High per the component page, but SKILL.md:59 says registry-delegated `Prototype` may still return a singleton under CDI; the skill does not state whether `Request` behaves per exchange for a CDI-managed named bean. Tag the CDI case or add the page statement.
- **M3 (cdi-and-native.md:19)**: "`@Named` ... adds `@Default` when it is the only qualifier ... per the research" is an untagged, unsourced claim; no register line. Source or tag.
- **M4 (register mapping lines 56-74)**: no line for the integration-examples.md:45 JAXB "(medium)" binding claim, nor for bean-binding.md:83 "Redelivery defaults ... not re-verified". Add M12/M13 or reword.
- **M5 (register line 78, 95)**: High claims from the CDI reference rest on a page read only "first 100,000 of 104,471 characters" and on tool summaries; record whether the quoted `@Identifier`/`@Named` passages fall inside the read portion (family fact says orchestrator-fetched, so this should be cross-referenced).

### LOW

- testing-with-injectmock.md:27-30: High junit rename/stub facts filed under heading "## Unverified"; split the heading.
- SKILL.md:55 default `@Identifier` + `@Unremovable` vs Always Do 1 recipe using `@Named("x")`: state which is the default.
- never-do-patterns.md:7 says the missing-reflection result "fails in native mode" flatly; SKILL.md does not. Soften or tag.
- Register U4 "`camel-quarkus-log` options unverified" duplicates what the log skill states from log.html (cross-skill).

## Conclusions

Good register hygiene (every SKILL.md tag mapped), clean family-fact alignment, strong scenarios. The two Always Do bullets are the remaining defect class (medium claims promoted to rules). Fixing H1/H2 and M1 gives about 92.
