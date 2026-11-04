# TEST report, round 1: software-quality skills (evaluating-skill-scenarios, read-only simulation)

Date 2026-11-01. Method: for each skill I read SKILL.md and all blueprints (source under packages/quality/**) in my own context, derived the answer the skill text leads to for every scenario, and judged it against must_pass / must_not. No agents spawned. For `building-acceptance-tests` (a router) the behaviour comes from `acceptance-test-engineer.agent.md`, which the command forks to. The scenario files use "expected / must not" prose for the first three skills; I treated Expected as must_pass and Must not as must_not.

## Summary

| Skill | Pass / total | Partial | Fail |
|---|---|---|---|
| testing-quarkus-cucumber-v8-0 | 6/6 | 0 | 0 |
| testing-quarkus-integration-v3-40 | 6/6 | 0 | 0 |
| deriving-gherkin-from-openspec-v1-15 | 6/6 | 0 | 0 |
| building-acceptance-tests | 5/5 | 0 | 0 |

No scenario fails, so there are no failing scenario ids. Each has a one-line evidence quote under "Per-scenario verdicts" below. The findings after that are risks to the behaviour, not failures.

## Per-scenario verdicts

### testing-quarkus-cucumber-v8-0 (6/6)
- S1 canonical: PASS. SKILL.md:44 "Default pattern B1 ... `Main.run`"; always-do-patterns.md:7-8 BOMs without versions; runner-patterns.md:59-60,50-54 Failsafe plus Surefire exclude; steps-and-state.md:10-17 public ScenarioContext; tags always-do:33; Jackson always-do:25-27; verify SKILL.md:94 and always-do:61. must_not: OK.
- S2 pipeline-started app: PASS. runner-patterns.md:98-106 `@Suite`/`@IncludeEngines`/`GLUE_PROPERTY_NAME`; :114 `app.base-uri`; :120 naming-strategy long; SKILL.md:54 "Surefire and Failsafe cannot discover `.feature` files". must_not: OK (second app copy only under Ask First, SKILL.md:70).
- S3 JUnit 4 runner: PASS. SKILL.md:77 "`@RunWith(Cucumber.class)` ... deprecated for removal"; migration-guide.md:20 moves `@CucumberOptions`. must_not: OK.
- S4 "the Quarkus way": PASS. SKILL.md:67 Ask First row (7.21.1, no `@QuarkusIntegrationTest`, JUnit 6 fix unreleased); never-do-patterns.md:63-70 (spike, "(unverified)" compatibility). must_not: OK.
- S5 real partner API: PASS. SKILL.md:83 Never Do; never-do-patterns.md:51-54. must_not: OK.
- S6 HTML report: PASS. SKILL.md:55; steps-and-state.md:92,94 (Jackson, publish off). must_not: OK.

### testing-quarkus-integration-v3-40 (6/6)
- S1: PASS. SKILL.md:52,57,60,62; stubbing-and-containers.md:33-49 (ConnectWireMock and application.properties expression, medium confidence); always-do-patterns.md:61 count check. must_not: OK.
- S2 no Docker: PASS. stubbing-and-containers.md:84,87; SKILL.md:71-72 Ask First rows; WireMock tagged medium/unverified.
- S3 injection: PASS. SKILL.md:79 Never Do; always-do-patterns.md:20-21; scope split to `developing-quarkus-junit-v3-40` (SKILL.md:41).
- S4 RestAssured 6.3.0: PASS. SKILL.md:17,25,84; never-do-patterns.md:47-54.
- S5 test properties: PASS. SKILL.md:55,80; always-do-patterns.md:24-44 (return map).
- S6 running app: PASS. SKILL.md:69; failsafe-and-run-modes.md:72-80 (host, port, ssl, data question).

### deriving-gherkin-from-openspec-v1-15 (6/6)
- S1: PASS. SKILL.md:53-63; worked-example.md; script exists and was read.
- S2 delta, plain keywords: PASS. mapping-and-deltas.md:14-16,38-49; SKILL.md:57,69 (per-change vs merged is Ask First); script `--change`.
- S3 replace spec.md: PASS, weakly. mapping-and-deltas.md:36 "Keep `spec.md` canonical ... (medium confidence)"; questions-and-traceability.md:12 "one-way derivation"; the script is the sync tool. No explicit Never Do row (F3).
- S4 missing precondition: PASS. SKILL.md:80; never-do-patterns.md:5-23; questions-and-traceability.md:9-12.
- S5 invented variants: PASS. SKILL.md:60,87; mapping-and-deltas.md:51-53.
- S6 no R-id: PASS. mapping-and-deltas.md:24; script slug logic (check_feature_coverage.py:53-72) and the `no-rid` fixture match (`Named   Visitor` normalizes to `named visitor`).

### building-acceptance-tests (5/5; behaviour via acceptance-test-engineer.agent.md)
- S1 full: PASS. agent P1 (script must exit 0), P3 (B1 IT, WireMock), P4 verify, Report Format items 1-6 (agent:99-104), "Next step ... acceptance-test-reviewer" (agent:106). must_not: Never Do agent:91-95.
- S2 features-only: PASS. agent:50-53 "`features-only` stops here and reports".
- S3 incomplete spec: PASS. agent:44-46 returns NEEDS-INPUT with numbered questions if the spec is incomplete; nothing is written (P0 precedes P3). See F5 for the weak point.
- S4 runner choice: PASS. agent:86 Ask First names quarkus-cucumber; integration SKILL.md:79 forbids `@Inject` in the IT.
- S5 safety: PASS. agent:94 (no real calls), agent:92 (no commit/push/deploy), agent:43-44 (java -version and mvn -version, 17 or 21, else NEEDS-INPUT); stubs via WireMock.

## Findings (risks, none blocking)

Known pilot items for testing-quarkus-cucumber-v8-0 re-checked in the source:

| Pilot item | Still present | Where |
|---|---|---|
| M1 Quarkus Java range cited to Cucumber release notes; "Max 21" | yes | SKILL.md:16; migration-guide.md:42 |
| M3 Always Do bullets 9 and 10 cite the engine README for `@R` tags and the testcase count; Never Do rows 1 and 6 put B1 (medium) first | yes | SKILL.md:59,60,77,82 |
| M2 rule 7 vs B1 | not re-checked against `_family_rules.md` here (the brief says rule 7 was reworded at G2); SKILL.md:44-47 still tags B1 "medium confidence" | SKILL.md:44-47 |
| L4 Never Do row lists only picocontainer (no jakarta-cdi, no CHANGELOG cite) | yes | SKILL.md:79 |
| L5 pom pins 3.6.1 untested; property `failsafe-plugin.version` reused for Surefire; extra picocontainer and logging properties | yes | runner-patterns.md:12,31,39,50,62-65 |
| L6 Jackson "2.21.8" untagged | yes | migration-guide.md:46 |
| L7 "representative command (unverified output)" in place of a plain tag | yes | SKILL.md:94 (same wording in integration SKILL.md:97) |
| L8 B1 spike evidence pointer | yes (optional) | SKILL.md:44-47 |

None of these causes a scenario failure.

New findings from this round:

- F1 MEDIUM, deriving-gherkin: `check_feature_coverage.py:253-255,307`. A requirement with zero scenarios is labelled `status: gap` in per_requirement, but `gaps = missing + orphans + parse_errors` ignores it, so the script exits 0 ("complete") and no MISSING line appears. A spec requirement with no scenario passes the "coverage must exit 0" gate silently; SKILL.md:99 and always-do:30 define exit 0 as complete. Fix hint: add per-requirement zero-scenario entries (for example `empty_requirements`) and return 1, add a test fixture, and add a sentence to mapping-and-deltas.md that a requirement without scenarios is a numbered question.
- F2 LOW, integration: stubbing-and-containers.md:32-43 and restassured-and-data.md:62-65 show `@ConnectWireMock(restClient=...)` while stubbing:43 says the redirect to the launched process is unverified. Fix hint: mark the examples "(redirect unverified; wire the URL as below)" or show the explicit wiring beside them.
- F3 LOW, integration: two competing wiring defaults. Scenario 1 expects the packaged-properties expression (stubbing:47-55), Scenario 5 expects the test-resource return map as default (always-do-patterns.md:24-44). The snippet at stubbing:47-50 also lacks the `%it.` prefix that line 54 requires. Fix hint: state which is default per use case (Dev Service vs manual) and show `%it.` in the snippet.
- F4 LOW, integration: Scenario 4 expects "asks first if the user accepts an override risk", but SKILL.md:66-73 has no Ask First row for a version override, only Never Do (SKILL.md:84). Fix hint: add an Ask First row or soften the scenario.
- F5 LOW, building-acceptance-tests and deriving-gherkin: Scenario 3 depends on the generic "spec is incomplete" in agent:44-46. Neither the agent nor the deriving skill defines it (requirement without scenario, scenario without a THEN or testable outcome). Combined with F1 the script will not flag it. Fix hint: define the cases in agent P0 or in deriving always-do-patterns.md.
- F6 LOW, deriving-gherkin: Scenario 3 (replace spec.md with the feature) is answered only by mapping-and-deltas.md:36. SKILL.md:76-87 has no Never Do row. Fix hint: add "Replace or rewrite spec.md as Gherkin | keep spec.md canonical, derive the .feature (medium confidence)".
- F7 LOW, building-acceptance-tests: agent:43-44 runs the JVM and Maven check and may return NEEDS-INPUT even in `mode=features-only`, which needs neither. Fix hint: run the JVM/Maven check only in `full` mode.

## Rubric note
These are behavioural results, not the 100-point static score. Counted as the validator rubric would: 0 HIGH. F1 is the only MEDIUM and the rest are LOW. All four skills pass their scenario suites.
