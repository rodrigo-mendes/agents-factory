# Best Practices Analysis (round 2, final): developing-camel-quarkus-rest-v3-40

**Date**: 2026-10-14
**File**: `packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-rest-v3-40/SKILL.md`
**Lines**: 111 (hybrid target 100-200, limit 500)
**Judged against**: `.claude/rules/skill-structure.md` "Hybrid knowledge skills" + `TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md`
**Shared-fact truth**: `workspace/_family_facts_v3.40.md`
**Method note**: URLs not fetched; presence and consistency checked. "One claim per Always Do bullet" is applied as: HIGH when a bullet mixes claims of different evidence/confidence, MEDIUM when it holds several same-source facts.

**Score: 72/100** (scale: 100, -4 per HIGH, -1.5 per MEDIUM, -0.5 per LOW)

## Summary

- Official criteria (A1-A6, B, C): 8/8 (name = folder, description 1 sentence "Guides ... Use when ... Not for", third person, one-level links, 4 scenarios).
- Team conventions D1-D7: 6/7 (D2/D5 fail on the hybrid guardrail purity, see HIGH).
- HIGH 4, MEDIUM 7, LOW 4.

## The 8 hybrid checks

| # | Check | Result |
|---|---|---|
| 1 | Always/Never hold High claims with versioned evidence; each Never Do alternative High; one High claim per bullet | FAIL (H1-H4) |
| 2 | Source column on every Version Context and Quick Reference row | PASS (all rows have an exact URL or "page not recorded") |
| 3 | Shared facts match family tags | PASS for facts 7-9, 11-14, 17, 20-21. Java 17/21 tagged High here, medium in bean (M7) |
| 4 | Register counts = listed items; mapping covers every tag | Counts PASS (11 unverified listed 1-11 + 3 skill-added 12-14; 5 irresolvable rows). Mapping is category-level only (M6) |
| 5 | No claim stronger in SKILL.md than in blueprint | FAIL (H3, M3, M4) |
| 6 | `@ApplicationScoped` never mandatory; none on a route without injection | PASS (SKILL.md:76; always-do-patterns.md:23; rest-dsl-configuration.md:18; no route sample has it) |
| 7 | Relative links and anchors resolve | PASS (all 11 blueprint links exist; #1-dependencies ... #5-server-settings-belong-to-quarkus, #medium-confidence-cautions, #tag-to-register-mapping, #version-lifetime-risk, #source-bibliography, #reuse-the-quarkus-objectmapper resolve) |
| 8 | Scenarios cover 4 types; scenario 1 must_not has the `@ApplicationScoped` item | PASS (evaluation-scenarios.md:21) |

## Recommendations by Priority

### HIGH

- **H1 (check 1, SKILL.md:46, Always Do 1)**: the bullet mixes a High fact (platform-http is the REST transport, rest.html) with the instruction to declare `camel-quarkus-jackson` and `camel-quarkus-direct`, whose only evidence is the example pom on the `main` branch, declared "supporting only" (always-do-patterns.md:7,16; unverified-and-risks.md:60). Fix: Always Do keeps only "camel-quarkus-rest depends on platform-http and configures it as REST transport"; move jackson/direct to Ask First tagged medium, or cite a versioned page.
- **H2 (check 1, SKILL.md:47, Always Do 2)**: "set `type`/`outType` on verbs" rests on the unversioned binding manual (always-do-patterns.md:20,36 "follows the binding manual example"), only "default off" is High. Fix: Always Do = "bindingMode defaults to off; set it explicitly" (main.html); move type/outType to the blueprint as medium.
- **H3 (checks 1 and 5, SKILL.md:48, Always Do 3)**: stated High citing the rest-openapi component page, but openapi-contract-first.md:24 tags "each operationId maps to direct:<operationId>" as "medium confidence: unversioned page" (rest-dsl-openapi.html), and SKILL.md:91 calls the same component URL (/4.22.x/) "page shows no version" (medium). always-do-patterns.md:65 says High. Fix: reconcile on one tag; demote to Ask First unless a versioned page statement is quoted.
- **H4 (check 1, SKILL.md:72, Never Do 1)**: the alternative "the Quarkus TLS registry (same page: managed by Quarkus)" is not High: always-do-patterns.md:98 says the skill "has not verified" the TLS keys, and migration-guide.md:9 / validation-and-cors.md:50 say the effect of TLS bridging on the inbound server is unverified. The row also carries an `unverified` tag, which the register itself calls a defect inside Never Do (unverified-and-risks.md:76). Fix: alternative = "configure the server through `quarkus.http.*` (page: managed by Quarkus)"; move the TLS-registry advice and the runtime-result note to the blueprint.

### MEDIUM

- **M1 (SKILL.md:72,74)**: `unverified` tags inside Never Do rows 1 and 3 (removal date); move to blueprint (rule at unverified-and-risks.md:76).
- **M2 (SKILL.md:64 vs unverified-and-risks.md:63,71)**: "Alternate transport" tagged High but listed in the medium register as single-source; mapping row 71 says High is not listed as a risk. Pick one.
- **M3 (SKILL.md:66 vs integration-examples.md:22-23)**: quarkus-junit + rest-assured is medium in SKILL.md ("example pom on main") but "high confidence" in the blueprint; the "needed only for CamelQuarkusTestSupport" clause sits inside a cell tagged High while the blueprint section is "medium confidence, both pages" (line 20).
- **M4 (migration-guide.md:42)**: "Quarkus 4 / Jackson 3 | none | not supported" is stronger than SKILL.md:24-25 (no build known, medium; Jackson 3 medium). Reword "no build known (medium)".
- **M5 (migration-guide.md:15, validation-and-cors.md:49)**: Camel 4.22.2 changes (fileNameExtWhitelist, Content-Type) listed as relevant while the pinned stack is Camel 4.22.1 (SKILL.md:17). State applicability or drop.
- **M6 (unverified-and-risks.md:69-74)**: mapping is by tag class, not by item. SKILL.md uses `unverified` for root-path, doc-path permission and CORS interplay (SKILL.md:58,60,94), which live under Irresolvable (lines 25-31), while the mapping sends `unverified` to "Other unverified items". Add item-level lines.
- **M7 (SKILL.md:18 vs unverified-and-risks.md:44)**: Java 17 and 21 is High from q-3.40.0, but item 8 says that page shows neither release date nor Camel version; bean tags the same fact medium. Align (see cross-skill).

### LOW

- always-do-patterns.md:3 says sections 2 and 4 are High although each contains medium parts (lines 20, 65).
- rest-dsl-configuration.md:15 cites `manual/latest/rest-dsl.html`, absent from the bibliography; "high for the structure (official example plus manuals)" blends High with medium sources.
- never-do-patterns.md:94-95 ❌ sample has `@Inject` on a RouteBuilder with no scope (would also fail for that reason).
- Bibliography (unverified-and-risks.md:82,85,89,93) uses brace/glob URL forms, not exact URLs.

## Conclusions

Strengths: lean SKILL.md, every table row sourced, `@ApplicationScoped` handled correctly everywhere, honest unverified handling (SSL, root-path, CORS interplay), complete 4-type scenarios. Weakness: the Always Do list still mixes in medium evidence (H1-H3) and the TLS alternative overreaches (H4). Fixing H1-H4 and M3/M4 gets the skill to about 85.
