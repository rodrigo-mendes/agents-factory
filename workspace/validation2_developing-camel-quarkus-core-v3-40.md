# Validation 2 (final) - developing-camel-quarkus-core-v3-40

Validator: skill-best-practices-validator (hybrid knowledge skill rubric). Date 2026-10-14.
Target: packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-core-v3-40/ (SKILL.md 108 lines, 8 blueprints).
Scoring: 100 minus 4 per HIGH, 1.5 per MEDIUM, 0.5 per LOW. URLs were not fetched; presence and consistency only.

**Score: 71 / 100** (5 HIGH, 5 MEDIUM, 4 LOW)

Note on process: the P3 "Report Plan" approval gate could not be obtained from the user inside this run; reports were written to the paths the invoking agent specified.

## Official criteria (A-C)

| ID | Status | Evidence |
|---|---|---|
| A1 | PASS | name matches folder, kebab-case, description third person with "Use when" and "Not for" (SKILL.md:2-3), < 1536 chars |
| A2 | PASS | 108 lines (< 500, within 100-200 target) |
| A3 | PASS | one level of blueprints; all 8 linked files exist |
| A4 | WARN | see M2, M3 (claims stronger than their blueprint) |
| A5 | PASS (n/a) | knowledge skill, no workflow |
| A6 | PASS | relative paths only |
| B | n/a | no scripts |
| C | WARN | 4 scenarios, one per type, but scenario 1 misses a must_not item (H5) |

## Team criteria (D1-D7)

| ID | Status | Evidence |
|---|---|---|
| D1 | PASS | `developing-camel-quarkus-core-v3-40` matches the version-locked naming rule |
| D2 | WARN | three tiers present; Never Do holds medium rows (H1), Always Do bullets multi-claim (H2) |
| D3 | PASS | Version Context present, every row has a Source |
| D4 | n/a | hybrid knowledge skill |
| D5 | WARN | 6 of 7 Never Do rows have side-by-side code in never-do-patterns.md; row 7 has none (prose only) |
| D6 | PASS | see check 7 |
| D7 | PASS | External Resources + bibliography |

## Checks requested by the caller

| # | Check | Result |
|---|---|---|
| 1 | Always/Never Do High only; each Never Do alternative High; one High claim per Always Do bullet | FAIL (H1, H2) |
| 2 | Source column on every Version Context and Quick Reference row (exact URL or "page not recorded") | PARTIAL (M1) |
| 3 | Shared facts match family-facts tags | FAIL (H3) |
| 4 | Register counts equal lists; tag-to-register mapping table | FAIL (H4; counts M4) |
| 5 | No claim stronger in SKILL.md than in blueprint | PARTIAL (M2, M3) |
| 6 | @ApplicationScoped never mandatory; no sample puts it on a route without injection | PASS. always-do-patterns.md:48 and :67 and integration-examples.md:31 carry `@ConfigProperty`; integration-examples.md:97 is a non-route bean; never-do-patterns.md:38 is a labelled WRONG example |
| 7 | Relative links and anchors resolve | PASS. All 8 blueprint files exist; anchors `#1-bom-import`, `#2-routebuilder-discovery`, `#3-named-beans`, `#testing`, `#error-handling`, `#version-lifetime-risk`, `#source-bibliography`, `#quick-reference`, `#external-resources`, `#blueprints--guardrails` all match headings |
| 8 | Scenarios cover the 4 types; scenario 1 must_not has the @ApplicationScoped item | FAIL (H5): types covered (canonical, edge, misuse, trap) |

## Recommendations by priority

### HIGH

- **H1 (D2, check 1)** SKILL.md:70 and :72 (Never Do rows 4 and 6) are tagged **medium confidence** and sit inside the Never Do table; row 6's alternative ("adviceRoute() ... signature unverified") is not High either. SKILL.md:73 (row 7, "Assume Quarkus 4 compatibility") carries no source or tag although the underlying fact is Medium (family facts). Fix: move rows 4 and 6 to Ask First or leave them only in blueprints/never-do-patterns.md (as http does); rewrite row 7 using only High facts (Beta1 2026-10-01, Java 21 base, https://quarkus.io/blog/quarkus-4-0-0-beta1-released/) with alternative "Stay on 3.40.x / 3.40.1" (https://camel.apache.org/camel-quarkus/latest/), as platform-http does.
- **H2 (D2, check 1)** SKILL.md:44-48 Always Do. Bullets 1, 2, 4, 5 have no inline source URL. Bullet 1 holds three claims (same version, major.minor match, import order). Bullet 3 (line 46) holds five (name qualifier + scope, `@RegisterForReflection`, `@Named` not removed, `@Identifier` preferred, `@Unremovable` advice) and its last part depends on an Unverified fact (removal of `@Identifier`-only beans). Bullet 5 holds three, including "CamelQuarkusTestSupport works in JVM mode only" with no source. Fix: one High claim per bullet with its URL (dependency-management.html, cdi.html, native-mode.html, testing.html); move `@Identifier`/`@Unremovable` solely to the existing Ask First "Bean naming" row (line 61).
- **H3 (check 3)** The shared fact "No Camel Quarkus build on Quarkus 4 is known" (family-facts: Medium, absence of evidence) is untagged in core: SKILL.md:23 ("No Camel Quarkus release ... is known"), blueprints/migration-guide.md:33 ("no CQ build exists", stronger still), blueprints/evaluation-scenarios.md:39, :58, blueprints/unverified-and-risks.md:8 and :17 (classed "irresolvable", never tagged Medium). Fix: add "(medium confidence, absence of evidence; the Beta1 post does not mention Camel Quarkus)" at each place and list it under Medium-confidence items in the register.
- **H4 (check 4)** blueprints/unverified-and-risks.md has no tag-to-register mapping table (platform-http, http and file all have one). Tags used in SKILL.md but absent from the register: Maven 3.8.2/3.9.16 "unverified" (SKILL.md:19; and blueprints/migration-guide.md:35 states the same Maven values as fact under a header "Confidence: high", line 3); "log output unverified" (SKILL.md:90). Fix: add the table (High / medium / unverified / irresolvable / inferred), add the Maven and log-output entries, and tag migration-guide.md:35 **unverified**.
- **H5 (check 8, C1)** blueprints/evaluation-scenarios.md:21-23, scenario 1 `must_not` has no @ApplicationScoped item (it appears only in must_pass, lines 17-18). Fix: add `"State that @ApplicationScoped is mandatory on a RouteBuilder"` to must_not, as the other three skills do.

### MEDIUM

- **M1 (check 2)** SKILL.md:83, :85, :86, :88 Quick Reference Source cells are bare relative paths (`user-guide/bootstrap.html`), not exact URLs; :90 says `none` instead of "page not recorded". Fix: full https URLs; use "page not recorded".
- **M2 (check 5)** SKILL.md:44 "The official guide says ... import order sets precedence" is stronger than blueprints/always-do-patterns.md:8, which states the wording comes from a tool summary and must be re-checked. Fix: soften SKILL.md or re-verify the quote and drop the caveat.
- **M3 (check 5)** SKILL.md:46 makes `@RegisterForReflection` unconditional for named beans; blueprints/native-mode.md:20 says "for beans invoked reflectively". Fix: align with the blueprint.
- **M4 (check 4)** Register counts: unverified-and-risks.md:3 says 12 other unverified items; the list (lines 23-35) has 13 bullets (line 33 is a "Resolved" note, not an item). Line 31 labels the REST-coexistence entry "irresolvable" but it sits in "Other unverified", and the junit5 row at line 19 sits in the "do not assert" table while declaring itself "Resolved (High)". Fix: move or relabel so each entry lives in one class; state counts that equal the lists.
- **M5 (check 1/5)** SKILL.md:68 and blueprints/never-do-patterns.md:17-28 put "widen TLS globally" in Never Do (marked critical), but the family facts only establish that unknown names fail; the harm of widening is a judgement, and platform-http (Ask First) and http (Ask First, "avoid") treat it as a decision. The sample in never-do-patterns.md:23 (`TLSv1.3,TLSv1.2,TLSv1`) uses valid JSSE names, so it does not illustrate the "unknown names fail" claim. Also the same decision is listed in Ask First (SKILL.md:56). Fix: keep only "OpenSSL-style or unknown names fail" in Never Do with a High alternative (JSSE names); leave scope widening in Ask First.

### LOW

- **L1** blueprints/unverified-and-risks.md:7 "Jackson 3" is not in the family facts and has no source; line 9 "expects 3.40 LTS to be the last 3.x line" is an unsourced expectation (labelled as such; consider deleting).
- **L2** blueprints/tls-and-security.md:31-33 (dev console exposure, Jolokia) lack a per-item source; header line 3 cites only the 3.40.0 guide.
- **L3** blueprints/never-do-patterns.md:32 rates @ApplicationScoped severity "medium"; platform-http rates the same rule "low". Align.
- **L4** SKILL.md:19 Version Context "none recorded" and :84, :89 "page not recorded" are fine; use one wording ("page not recorded") for consistency with the other three skills.

## Conclusions

The structure, links, line count and @ApplicationScoped handling are sound. Remaining defects repeat the classes found in round 1 (medium claims in Never Do, multi-claim Always Do bullets, untagged shared fact) and the register lacks the mapping table. core is the weakest of the four; it appears not to have received the same fix pass as http and platform-http.
