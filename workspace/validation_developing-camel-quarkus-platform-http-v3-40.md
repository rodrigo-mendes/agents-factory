# Best Practices Analysis: developing-camel-quarkus-platform-http-v3-40

**Date**: 2026-10-14
**File**: `packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-platform-http-v3-40/SKILL.md`
**Lines**: 109 (confirmed with a line count; hybrid target 100-200, hard limit 500)
**Judged against**: `.claude/rules/skill-structure.md` ("Hybrid knowledge skills") and `TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md`
**Scope of check**: presence and consistency only. No URL was re-fetched.
**Score**: **80/100** (rubric: start at 100; HIGH -4, MEDIUM -1.5, LOW -0.5)

---

## Summary

- Official criteria met: 8/8 (B is N/A, no scripts)
- Team conventions met: 6/7 (D2 and D5 carry findings; D2 is marked partial below)
- HIGH: 3, MEDIUM: 4, LOW: 4

Structure is complete: all four required blueprints exist, the register has both mandated headings, and there are 4 evaluation scenarios.
Every Version Context row and every Quick Reference row has a source URL or an explicit "page not recorded" / "none recorded".
Defects are in the tier discipline (what is allowed in Always Do / Never Do), not in structure.

## Official Criteria

| Criterion | Status | Notes |
|---|---|---|
| A1 Frontmatter | ✅ | `name` equals folder, only `name` + `description`, description matches `Use when` and is well under 1536 chars (regex check), third person |
| A2 Conciseness | ✅ | 109 lines |
| A3 Progressive disclosure | ✅ | one level deep; all 8 blueprint links and the anchors I checked by reading resolve (`#1-declare-the-endpoint-and-restrict-methods`, `#does-the-340-bridging-affect-the-inbound-server`, `#version-lifetime-risk`) |
| A4 Content | ✅ | version-anchored dates only; terminology consistent |
| A5 Workflows | ✅ | N/A for a knowledge skill |
| A6 Paths | ✅ | relative, forward slashes |
| B Scripts | N/A | none |
| C Evaluation | ✅ | 4 scenarios (canonical, edge, misuse, trap). Not executed here (no skill-evaluator run) |

## Team Conventions

| Criterion | Status | Notes |
|---|---|---|
| D1 Naming | ✅ | version-locked gerund-noun per `naming-conventions.md` |
| D2 Three tiers | ⚠️ | present and populated, but H1-H3 place non-High content in Always Do / Never Do |
| D3 Version Context | ✅ | table has sources; unverified rows say "none recorded" |
| D4 Verification loop | ✅ | representative commands, flagged unverified in the blueprints |
| D5 Anti-patterns with alternatives | ⚠️ | every Never Do row has a ✅ column; rows 1 and 4 use a medium-confidence alternative (M2, H2) |
| D6 Links | ✅ | no broken relative link found |
| D7 External resources | ✅ | official pages only |

## Hybrid-format checks requested

| Check | Result |
|---|---|
| Flat claims in SKILL.md have source or tag | ⚠️ one miss (M1), one source mismatch (M4) |
| Version Context / Quick Reference rows have sources | ✅ all rows |
| Always Do / Never Do contain only High claims | 🚫 H1, H2, H3, M2 |
| No claim that `@ApplicationScoped` is mandatory | ✅ SKILL.md:50 and :73 say "unless injects" / "needed only for"; eval scenario 1 has a `must_not` for it |
| Every medium/unverified item is in `unverified-and-risks.md` | ✅ all SKILL.md tags map to a register line, except the CDI source provenance (H3) |
| SKILL.md not stronger than blueprints | 🚫 H2 |

---

## Recommendations by Priority

### HIGH

**H1. Unverified payload inside Always Do** (SKILL.md:45-46; always-do-patterns.md:3, :20, :54)
- :45 ends with "the comma-separated form is **unverified**"; :46 builds the rule "set `quarkus.http.body.*` ... explicitly" on defaults the same bullet calls **unverified**, and gives no inline URL for the whitelist half.
- always-do-patterns.md:3 promises "High-confidence patterns only" but #1 (:20) and #5 (:54) carry unverified notes.
- Fix: keep each bullet to the single High claim (`httpMethodRestrict` restricts methods; `fileNameExtWhitelist` has no default, with component-page URL). Move the comma-form and `body.*` hedges to Quick Reference (already there at :96-97) and to an Ask First row. Fix the blueprint header or move the unverified notes out.

**H2. Never Do row 4 states a medium reading as a High rule, and stronger than the blueprint** (SKILL.md:72; never-do-patterns.md:42-51; evaluation-scenarios.md:79)
- The cited guide (3.40.0 migration guide) concerns Camel's bridge of `quarkus.tls` into `SSLContextParameters`. tls-and-security.md:28-35, migration-guide.md:11 and register:26 say the inbound-server impact is unverified, and the blueprint's own reading is medium. SKILL.md:62 tags the very same topic medium in Ask First.
- The ✅ column (`quarkus.tls.legacy-endpoint.protocols`) is that medium mitigation.
- Fix: delete row 4 from Never Do (the Ask First row at :62 already covers it), or rewrite it to the verified outbound-only fact and say so. Align never-do-patterns.md #4 (severity "high") and eval scenario 4 `must_pass` at :79.

**H3. Always/Never claim on `@ApplicationScoped` rests on a page the research did not fetch** (SKILL.md:50, :73; always-do-patterns.md:58; never-do-patterns.md:55; register:61)
- Register:61 says the CDI guide was "supplied with the task, page not part of this research file". The claim "it adds boot-time cost" therefore has no fetched evidence in this skill, yet it sits in both Always Do and Never Do and is absent from the medium list.
- The conclusion (no `@ApplicationScoped` without injection; never "mandatory") is correct and consistent with the core skill, so this is provenance, not content.
- Fix: either cite the core skill's evidence ("see developing-camel-quarkus-core-v3-40, always-do #2") or tag it medium, move it to Ask First, and add it to the register's Medium-confidence list.

### MEDIUM

- **M1** (SKILL.md:74) Never Do row 6 "Assume Quarkus 4 compatibility..." has no source and no tag. Add the version-lifetime link or delete (Version Context :23 already says it).
- **M2** (SKILL.md:69; tls-and-security.md:26; register:47) Never Do row 1's ✅ column (`quarkus.tls.https.*` named configuration) comes from the unpinned "Latest" Quarkus page, which the register lists as medium. Tag it, or cite the pinned 3.40 page (always-do-patterns.md:28 already uses it for `tls-configuration-name`).
- **M3** (SKILL.md:57; integration-examples.md:36; register:48) Ask First "Body handling" states "re-readable" vs "single-read body" untagged; the blueprint tags the single-read claim medium. Add the tag.
- **M4** (SKILL.md:47) Always Do #3's only inline URL supports "`SSLContextParameters` not supported"; the property names `quarkus.tls.*` and `quarkus.http.tls-configuration-name` are sourced elsewhere (pinned reference in always-do-patterns.md:28, "Latest" page in tls-and-security.md:26). Add the pinned HTTP-reference link to the bullet.

### LOW

- **L1** (register:3, :28-39) Header says "9 unverified, 3 irresolvable"; the "Other unverified items" list has 11 entries (one added by this skill). State the reconciliation.
- **L2** (SKILL.md:95) Quick Reference "Bridged TLS default" row has no note that inbound-server impact is unverified; add "(Camel SSL contexts only)" to the row.
- **L3** (evaluation-scenarios.md:59) Scenario 3 `must_pass` asserts "no Camel Quarkus build on Quarkus 4 is known" without the medium tag used in the register.
- **L4** (never-do-patterns.md:3) Header points medium items to integration-examples.md#error-handling, but never-do-patterns.md contains none; trim.

## Conclusions

Strong provenance hygiene: most medium items are tagged and registered, and the "do not assert" items are respected in Ask First. Fixing H1-H3 (moving four claims out of the High tiers) would bring this to roughly 90.
