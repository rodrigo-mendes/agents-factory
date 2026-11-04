# Round 2 validation: 3 knowledge skills + 2 packages (software-quality)

Date 2026-11-01. Approval: relay of G1 ("Approve", 2026-10-31); G2 recorded. Not a new approval.
Read-only except this file. Source under packages/quality/** only. verify_skill.py, verify_package.py and the unittests were run by the orchestrator (not re-run here).

## Scores

| Target | Score | HIGH | MEDIUM | LOW |
|---|---|---|---|---|
| testing-quarkus-cucumber-v8-0 | 97.0 / 100 | 0 | 1 | 1 |
| testing-quarkus-integration-v3-40 | 99.5 / 100 | 0 | 0 | 1 |
| deriving-gherkin-from-openspec-v1-15 | 97.0 / 100 | 0 | 1 | 1 |
| acceptance-testing (package) | 9.0 / 10 | 0 | 0 | 2 |
| quarkus-acceptance-testing (package) | 9.0 / 10 | 0 | 1 | 1 |

(The tag contradiction below is one defect across files. It is counted once as MEDIUM per skill and once for the package.)

## Round-1 findings: status

Round 1 F-001..F-006 are read as the test F1-F6 plus the audit remediation list.

| Item | Status | Evidence |
|---|---|---|
| F1 zero-scenario requirement passes silently | RESOLVED | check_feature_coverage.py:257 `"reason": "no-scenarios"`, :315 `gaps = ... + s["empty_requirements"]`; test file :48-50; SKILL.md:98 and mapping-and-deltas.md:55 document it |
| F2 `@ConnectWireMock` redirect unverified | RESOLVED | restassured-and-data.md:63 "(unverified) for the launched process; also set %it.quarkus.rest-client...url explicitly" |
| F3 competing wiring defaults / `%it.` missing | RESOLVED | stubbing-and-containers.md:49 now `%it.` and :56 states the profile property is required |
| F4 no Ask First row for a RestAssured override | RESOLVED | integration SKILL.md:73 Ask First row, and Never Do :85 |
| F5 "spec incomplete" undefined | RESOLVED | engineer agent:49-50 defines three cases |
| F6 no Never Do row for replacing spec.md | RESOLVED | deriving SKILL.md:88 |
| F7 JVM check in features-only | RESOLVED | engineer agent:43-44 "In `mode=full` only" |
| Audit 1 engineer coverage command | RESOLVED | engineer agent:58 spells out `--spec-root ... --features ... [--change <id>] --strict` |
| Audit 2 junit boundary line | RESOLVED | integration SKILL.md:41 and :48 defer to `developing-quarkus-junit-v3-40` |
| Audit 3 conditional `@change` in rules | RESOLVED in the rules only; see M1 for the skills |
| Audit 4 reviewer launch path | RESOLVED | acceptance-testing README:42-43; quarkus README:21-22, :43 |
| Engineer/reviewer Bash honesty note | RESOLVED | engineer agent:98, reviewer agent:34 |
| Cucumber M1 (Java range), M2 (sources), M3 (Failsafe duplication) | RESOLVED | SKILL.md:16-17 split into two rows with medium tag; :52-60 cite F5/F11 pages; runner-patterns.md:49 now points to the integration skill |
| Cucumber L1 (jakarta-cdi), L3 (Jackson 2.21.8), L4/L7 tag format | RESOLVED | SKILL.md:79 lists `cucumber-jakarta-cdi`; 2.21.8 absent from migration-guide; SKILL.md:94 `n/a (unverified)` |
| Cucumber L2 (3.6.1 pin, shared property name) | PARTLY | runner-patterns.md:13 has "spike version (medium confidence)", but migration-guide.md:47 and unverified-and-risks.md:54,78 still cite 3.6.1 as "current" without a URL on the migration row; see L1 below |
| Integration L1 `(unverified output)` wording | RESOLVED | SKILL.md:98 is a bare `(unverified)` |
| Deriving L1 (regex pipes) | RESOLVED | SKILL.md:97 explains the escaped pipes |
| Deriving L3 (`--change` MISSING for the base) | RESOLVED | SKILL.md:69 |
| Package L (Testcontainers medium tag in README) | RESOLVED | quarkus README:54 |
| Package L (factory-core dependency reason) | RESOLVED | acceptance-testing README:7 |
| Package L (rest/arc unused) | RESOLVED | quarkus README:19 explains it |

## Findings

### MEDIUM

M1. Contradiction after the F-003 audit fix: the `@change-<id>` tag is conditional in the rules and reviewer, but still mandatory in the skills.
- Rules (updated): gherkin-feature-authoring.instructions.md:17 "Add `@change-<id>` only when generating from a change delta, and then it is required; for a spec root no change tag". quarkus-acceptance-tests.instructions.md:30 says the same. The reviewer agent:51 flags only "a delta feature without `@change`", so the rules and reviewer agree with each other.
- Skills (not updated):
  - deriving SKILL.md:58 "Tag each Rule `@R<n>` ... and each Feature `@change-<id>`" and :96 "Change tag | `@change-<id>` on the Feature".
  - mapping-and-deltas.md:18,25 and always-do-patterns.md:20 repeat it unconditionally.
  - cucumber SKILL.md:59 "Tag every scenario `@R<n>` and `@change-<id>`"; always-do-patterns.md:33 and evaluation-scenarios.md:13 repeat it.
  - acceptance-testing README:21 "and change (`@change-<id>`)".
- Effect: for a spec-root run, the skill the agent loads says to add `@change-...` while the rule says not to. Only deriving evaluation-scenarios.md:11 is conditional ("when a change id is known"). The script is unaffected.
- Not HIGH: no wrong fact and no spec-forbidden action. It is a guidance conflict that could make the engineer invent a change id.
- Fix: in deriving SKILL.md:58,96, mapping-and-deltas.md:18,25 and always-do-patterns.md:20, write "`@change-<id>` on the Feature when generating from a change delta; none for a spec root". Update cucumber SKILL.md:59, always-do-patterns.md:33 and evaluation-scenarios.md:13 the same way. Add "(delta only)" to README:21.

### LOW

L1. Surefire/Failsafe version provenance (cucumber, partly open). migration-guide.md:47 states 3.5.4 -> 3.6.1 and unverified-and-risks.md:54 says "Failsafe current 3.6.1", while runner-patterns.md:13 pins the spike version 3.5.4. The 3.6.1 claim has only a Maven page URL in the bibliography (:78), and the migration row carries no medium-confidence tag. Fix: tag the migration row (medium confidence), or drop the 3.6.1 number.

L2. Not verified in this round: anchors. I checked the anchors referenced from the SKILL.md files and the README links by reading target headings only in the files I opened. I did not open every blueprint heading, and the orchestrator's verify scripts did not flag any broken link. If a heading was renamed in a blueprint, a link could still break. Fix: spot-check `#medium-confidence-items`, `#version-lifetime-risk`, `#source-bibliography` and `#failsafe-pom`.

L3. Integration SKILL.md:41 boundary is part of the "Scope split" sentence and not an explicit "defer for X" line. It is acceptable and resolves audit S1; making it a bulleted list item would be clearer. Cosmetic.

L4. acceptance-testing README:21 repeats M1 (counted under M1; listed for the package score).

## Cross-checks (no regression found)

- Register counts: SKILL.md pointers to register items M1 (cucumber), U1/I2/M1/M2 (integration) match unverified-and-risks.md rows (integration :20-25 verified). No count mismatch found.
- Versions agree across skills, README and rules: Cucumber 8.0.4, Quarkus 3.40 LTS, RestAssured 6.0.1, wiremock 1.8.1, Testcontainers 2.0.5 (medium), JDK 17/21.
- Runner default B1 agrees across the cucumber skill, the rule (`quarkus-acceptance-tests`:27) and the engineer agent:70-71. Ask First lists agree: rule:35-38, engineer agent:93, command skill:26.
- Rule Verify greps agree with the skills (`@Inject` check, JUnit 4 runner grep, `java -version`). The engine package `io.cucumber.junit.platform.engine` exception is stated.
- Reviewer: no Write/Edit tool, Never Do table matches the tools. Engineer: Write/Edit/Bash with an honest prose-limit note (:98), Never Do consistent with the command skill's "Will not" list.
- Command skill: `context: fork`, `agent: acceptance-test-engineer`, `disable-model-invocation: true`, argument-hint matches the agent's Input section.
- apm.yml: dependency paths resolve (factory-core, openspec-core, ../acceptance-testing, quarkus-core); no double listing.
- Script docs vs script: `empty_requirements` key and exit 1 documented in the script docstring, SKILL.md and blueprint, and tested.

## Package scoring notes

- acceptance-testing 9.0: artifacts complete; the only deductions are M1 residue (README:21) and the prose-only Bash limit that is disclosed.
- quarkus-acceptance-testing 9.0: one MEDIUM (M1, the cucumber skill and its blueprints), one LOW (L1).

## Priority

1. M1 (one sweep across 7 files). 2. L1. 3. L2 spot-check.
No HIGH. All round-1 HIGH-class items stay at 0. No regression by score: skills 89 -> 97, 98.5 -> 99.5, 98 -> 97 (deriving drops 1 only because M1 is now counted for it).
