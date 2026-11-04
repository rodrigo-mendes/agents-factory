# TEST report, round 2: software-quality skills (read-only simulation, no agents spawned)

Date 2026-11-01. Method: source under packages/quality/** only. For each skill I read SKILL.md and the blueprints in my own context and judged every scenario in blueprints/evaluation-scenarios.md against Expected / must_pass and Must not / must_not. building-acceptance-tests is judged through acceptance-test-engineer.agent.md.

## Summary

| Skill | Pass / total | Partial | Fail |
|---|---|---|---|
| testing-quarkus-cucumber-v8-0 | 6/6 | 0 | 0 |
| testing-quarkus-integration-v3-40 | 6/6 | 0 | 0 |
| deriving-gherkin-from-openspec-v1-15 | 6/6 | 0 | 0 |
| building-acceptance-tests | 5/5 | 0 | 0 |

0 HIGH, 0 MEDIUM, 0 LOW new findings. No failing scenario ids.

## Round-1 findings: resolved?

| Id | Round-1 finding | Status | Evidence |
|---|---|---|---|
| F1 (zero-scenario requirement) | script exited 0 for a requirement with no scenario | RESOLVED | check_feature_coverage.py:257 adds `empty` entries (reason "no-scenarios"); :315 `gaps = missing + orphans + parse_errors + empty_requirements`; unit test test_check_feature_coverage.py:48-50; SKILL.md:98 and mapping-and-deltas.md:55 say exit 1 and a numbered question |
| F2 / F3 (WireMock default wiring) | `@ConnectWireMock(restClient)` example vs unverified redirect; two competing defaults; `%it.` missing | RESOLVED | stubbing-and-containers.md:33,43 tag the redirect (unverified) and say to wire explicitly; :49 uses `%it.`; :53 states default per case (Dev Service jar IT = packaged expression, manual resource = start() map); :56 explains `%it.` needs integration-test-profile=it; restassured-and-data.md:63 same tag |
| F4 (RestAssured override) | no Ask First row | RESOLVED | integration SKILL.md:73 Ask First row "Override the RestAssured version managed by the Quarkus BOM (6.0.1)"; Never Do kept at :85 |
| F5 (spec incomplete) | undefined | RESOLVED | acceptance-test-engineer.agent.md:49-50 defines: requirement without a scenario (script reports it), scenario without a testable THEN, or a precondition the spec does not state |
| F6 (replace spec.md) | no Never Do row | RESOLVED | deriving SKILL.md:88 Never Do row "Replace or rewrite spec.md with Gherkin, or invent a scenario for a requirement that has none" |
| F7 (JVM check only in full mode) | check ran in features-only | RESOLVED | agent.md:43-44 "In mode=full only, run java -version and mvn -version"; :46 JVM/Maven NEEDS-INPUT only in full |

Regression check: no regressions found. Agent report format and Never Do are unchanged; scenario 2 of building-acceptance-tests (features-only, no Maven, no pom edit) is now stronger. Scenario 5 of building-acceptance-tests runs in default full mode, so the JVM check still applies and still passes.

## Per-scenario verdicts

### testing-quarkus-cucumber-v8-0 (6/6)
- S1 PASS: SKILL.md:45-48 B1 default (`Main.run`, medium confidence); :52 BOMs without versions; :53 Failsafe, Surefire exclude; :55 Jackson; :56-57 public PicoContainer state; :59 tags; :60 testcase count; :94 verify. must_not OK.
- S2 PASS: :54 `@Suite`, `@IncludeEngines("cucumber")`; :66 B2 Ask First; :68 naming strategy; Surefire cannot discover features. must_not OK.
- S3 PASS: :77 Never Do `@RunWith`, deprecated for removal; migration-guide covers `@CucumberOptions`.
- S4 PASS: :67 Ask First with 1.3.0, Cucumber 7.21.1, no `@QuarkusIntegrationTest`, JUnit 6 fix unreleased; B1 stays default.
- S5 PASS: :83 Never Do real partner API, WireMock via integration skill.
- S6 PASS: :55 Jackson pair; :93 `cucumber.publish.enabled` off.

### testing-quarkus-integration-v3-40 (6/6)
- S1 PASS: :52,53,57,58,60,61,62; stubbing:47-55 packaged-properties expression with `%it.`; :62 count check; Never Do :80,81,83.
- S2 PASS: :71,72 Ask First rows; stubbing:86-89 containers need Docker, WireMock spike tagged medium and unverified.
- S3 PASS: :80 Never Do; :41 scope split to developing-quarkus-junit-v3-40.
- S4 PASS: :17,25,73,85 (default no override, Ask First, Never Do explicit version). Expected "asks first if the user accepts an override risk" is now met.
- S5 PASS: :55,81; always-do-patterns.md:24-44 return map; :46-51 IT profile in packaged file.
- S6 PASS: :69 test-host/test-port Ask First; running-app note on Dev Services (medium confidence).

### deriving-gherkin-from-openspec-v1-15 (6/6)
- S1 PASS: SKILL.md:53-63, :99 script, worked-example.md.
- S2 PASS: :57 plain and bold keywords; :69 per change vs merged Ask First; :100 `--change`.
- S3 PASS: :88 Never Do row; mapping-and-deltas.md:36 canonical spec.md; script as sync tool.
- S4 PASS: :80 Never Do invented Given; :70 Ask First numbered question.
- S5 PASS: :60,:87 Examples only from the spec.
- S6 PASS: :74 `@req-<slug>` Ask First; mapping-and-deltas.md:24; script slug logic matches the `no-rid` fixture.

### building-acceptance-tests (5/5, through acceptance-test-engineer.agent.md)
- S1 PASS: P1 script must exit 0 (:54-59), P3 AcceptanceIT and WireMock (:70-71), P4 verify (:75-77), Report Format items 1-6 (:108-113), :115 next step acceptance-test-reviewer. Never Do :100-104 (no spec edit, commit, real calls).
- S2 PASS: :61 "features-only stops here and reports"; P2-P4 not reached, so no pom change or Maven.
- S3 PASS: :45-50 NEEDS-INPUT with numbered questions for a requirement without a scenario or a scenario without a testable THEN; P0 precedes writing; Never Do forbids spec edits. Script now exits 1 on the empty requirement, so the case is also machine-detected.
- S4 PASS: :93 Ask First names quarkus-cucumber; integration SKILL.md:80 forbids `@Inject` in the IT.
- S5 PASS: :103-104 no real calls, :102 no commit/push/deploy; WireMock stubs; JVM check in full mode (default) returns NEEDS-INPUT if majors differ or are not 17/21.

## Residual non-blocking items (unchanged from round 1 pilot register)
Not scenario-affecting and not new: Cucumber SKILL.md:16 "Java baseline" cites release notes while the Quarkus range is medium confidence (:17); verify row :94 "n/a (unverified)" in both testing skills. Informational only.
