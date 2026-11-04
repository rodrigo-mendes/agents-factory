# Round 1 validation: 3 knowledge skills (software-quality)

Date 2026-11-01. Spec: skill-best-practices-validator + hybrid-format-checklist.md. Checked against _family_facts.md (F1-F14), _family_rules.md (1-10), SPIKE_RESULTS.md (via facts F14, pilot).
Approval: relay of G1 ("Approve", 2026-10-31); G2 recorded. Not a new approval.
Read-only except this file. Not run: scripts/verify_skill.py and the unittest self-test (no shell tool in this session); the caller must run both.

## Scores

| Skill | Score | HIGH | MEDIUM | LOW |
|---|---|---|---|---|
| testing-quarkus-cucumber-v8-0 | 89.0 / 100 | 0 | 3 | 7 |
| testing-quarkus-integration-v3-40 | 98.5 / 100 | 0 | 0 | 3 |
| deriving-gherkin-from-openspec-v1-15 | 98.0 / 100 | 0 | 0 | 4 |

No HIGH finding. All three pass.

## Measured facts
SKILL.md lines: cucumber 103, integration 106, deriving 109 (target 100-200). Blueprint files all <= 107 lines (max runner-patterns 123 lines in cucumber; stubbing-and-containers 126 lines in integration; limit 160). Descriptions quoted, < 300 chars, contain "Use when"; name == folder; frontmatter has only name + description. No absolute paths, `.github/` or relative dates found. Neighbour skills exist: `developing-quarkus-junit-v3-40` (packages/java/quarkus/quarkus-core), `specifying-changes-with-openspec-v1-15` (packages/delivery/specs/openspec-core), plus the 3 skills themselves. Script docs vs script: verified below.

## Pilot items re-check (testing-quarkus-cucumber-v8-0)
- Pilot M2 (rule 7 vs B1): RESOLVED, rule 7 now names B1 as default and B2 as engine.
- Pilot M1 (Java range), M3 (Always/Never Do evidence): STILL PRESENT (M1, M2 below).
- Pilot L4, L5, L6, L7, L8: STILL PRESENT (L1-L5, L7 below).

## 1. testing-quarkus-cucumber-v8-0 (89.0)

### MEDIUM
M1. Rule 1: mis-sourced claim. SKILL.md:16 "Java baseline | 17 (Quarkus 3.40 is tested on 17 and 21)" cites only release-notes/v8.0.0.md, which supports F2 only. migration-guide.md:42 repeats "21 (tested by Quarkus 3.40 LTS)" as a Max. Fix: split the row (Java 17 cites release notes, Quarkus range cites the Quarkus page) or tag (medium confidence); drop "Max 21" if unsourced.
M2. Rules 1 and 3: evidence for Always/Never Do. SKILL.md:51 "cucumber-bom plus the Quarkus platform BOM manage Cucumber, JUnit Platform, RestAssured and Jackson ([CHANGELOG])": the CHANGELOG does not say Quarkus manages RestAssured/Jackson (F5, F13 do). SKILL.md:59 and :60 cite the engine README for the `@R`/`@change` tags (F11, factory convention) and the non-zero testcase count (derived from F6/F3). Never Do row 1 (:77) and row 6 (:82) give B1 first as the alternative; B1 is medium confidence and rule 3 wants High alternatives. Fix: cite F5/F13/F11 pages, tag derived ones (medium confidence), list the B2 `@Suite` alternative first.
M3. Duplication with the integration skill. SKILL.md:38-40 says Failsafe pom details live in `testing-quarkus-integration-v3-40`, yet runner-patterns.md:55-67 repeats the Failsafe plugin block (executions integration-test/verify, `java.util.logging.manager`, `maven.home`) that failsafe-and-run-modes.md:19-38 already holds. Always Do :52 ("integration-test runs after package, verify fails the build") and :53 ("*IT class, Surefire skips it") restate integration Always Do :52-53. Fix: keep only the Cucumber-specific delta (exclude `**/*IT.java` from Surefire, B1 class) and link to `failsafe-and-run-modes.md#failsafe-pom`; reduce :52/:53 to one pointer bullet.

### LOW
L1. Family fact F4 (SKILL.md:79; never-do-patterns.md:30). Never Do row for `cucumber-cdi2` names only `cucumber-picocontainer`; F4 says `cucumber-jakarta-cdi`. migration-guide.md:22 has it. Fix: add "or `cucumber-jakarta-cdi` for a separate CDI SE container".
L2. Untested versions and extras (runner-patterns.md:12, 31, 39, 62-65). Spike used Failsafe/Surefire 3.5.4; the fragment pins 3.6.1 ("current plugin line", no URL); adds `cucumber-picocontainer`, logmanager and `maven.home`, not in the spike. Surefire reuses the property `failsafe-plugin.version` (:50). Also the integration skill uses `${surefire-plugin.version}` unpinned (failsafe-and-run-modes.md:22,41): property naming differs across the two skills. Fix: tag (medium confidence), rename to one shared property.
L3. Unsourced Jackson version (migration-guide.md:46) "2.21.8 (Quarkus BOM)" without a tag. Fix: (unverified) or drop the number.
L4. Tag format, rule 2 (SKILL.md:94) "representative command (unverified output)" in the Source cell. Fix: `n/a (unverified)`.
L5. B1 spike evidence only in the register/runner-patterns (SKILL.md:44-47). Fix: one-line pointer to the register item for the spike.
L6. Cross-skill run command mismatch: SKILL.md:94 `mvn -B verify` vs integration skill (failsafe-and-run-modes.md:17,49) where generated projects default `skipITs=true` and ITs need `-DskipITs=false`. Cucumber's hand-written pom does not set skipITs, so it works as written, but a reader combining both skills can get zero tests. Fix: one sentence in runner-patterns noting that a generated `skipITs=true` must be removed or overridden.
L7. (see L5) kept for pilot parity: SKILL.md:94 Quick Reference lacks the evidence pointer.

Positive checks: F1 (8.0.4, 8.0.0, 7.34.9), F2, F3 (6.1.3 via BOM, `@Suite`, `junit-platform-suite`), F5, F6, F7 (1.3.0, 7.21.1, no IT support, JUnit 6 fix unreleased), F8 (1.8.1, WireMock 3.x) match; rules 4, 5, 8, 9, 10 satisfied; rule 7 satisfied (B1 default, B2 engine, no JUnit 4).

## 2. testing-quarkus-integration-v3-40 (98.5)

### LOW
L1. Tag format, rule 2 (SKILL.md:97) "representative command (unverified output)". Fix: `n/a (unverified)`. Same pattern in failsafe-and-run-modes.md:46.
L2. Rule 1 (SKILL.md:57) "tests never call a real service (family rule 4; [rest-client guide])": the rest-client guide does not state that policy. Fix: cite family rule 4 only, or tag (medium confidence).
L3. stubbing-and-containers.md:54 says to keep the key under `%it.`, but never states that `quarkus.test.integration-test-profile=it` must be set (default profile is `prod`, SKILL.md:56, :93). Fix: add the property to that bullet, otherwise the `%it.` key never applies.

Positive checks: F5 (LTS 2026-09-30, `quarkus-junit`, JUnit 6.1.3, Testcontainers 2.0.5 medium for patches), F6, F8 (1.8.1, WireMock 3.13.2, `@ConnectWireMock` on both), F12, F13 (6.0.1 managed, 6.3.0 not), F14 (spike, medium) match. Rule 4 (WireMock 3.x, Dev Services/Testcontainers), rule 8 (no overrides), rule 9 (pointer to `developing-quarkus-junit-v3-40`) satisfied. Neighbour names correct. Test names `R1_list_returnsOrders` follow F11.

## 3. deriving-gherkin-from-openspec-v1-15 (98.0)

### Script documentation vs scripts/check_feature_coverage.py (checked line by line)
Matches: arguments `--spec-root` (default openspec), `--change`, `--features` (required), `--json`, `--strict` (script.py:290-295); exit codes 0/1/2/3 (:303-308, Parser3.error -> 3); spec parsing `### Requirement:` and `#### Scenario:` exactly 4 `#` (:33-34); delta sections ADDED/MODIFIED/REMOVED/RENAMED and merge order RENAMED, REMOVED, MODIFIED+ADDED (:154-162) = mapping-and-deltas.md:40,49; tag inheritance Feature/Rule/Scenario (:202); `@R<n>` / `@req-<slug>` (:39, :70-72); verbatim name match, case-insensitive (:241); `--strict` warns and continues when `gherkin` is missing (:217-220) = always-do-patterns.md:28; Python 3.8+ stdlib only (no newer syntax found); `--json` keys missing/orphans/covered/summary/parse_errors (:270). The test file imports the script via sys.path (test_check_feature_coverage.py:10-12) so `unittest discover -s <skill>/scripts/tests` is a valid command; 10 test methods exist (not executed here).

### LOW
L1. SKILL.md:96 Quick Reference puts the step regex `(GIVEN|WHEN|THEN|AND)` in a Markdown table cell: unescaped `|` splits the cell. The regex is not used by the script (the script never parses step bullets) and the cited concepts.md does not contain it. Fix: move it to a code block in a blueprint, or escape the pipes, and label it derived guidance.
L2. Tag format, rule 2 (SKILL.md:23 "(repo convention, High)"; :93 "(repo convention)"). Fix: write plain `(medium confidence)` or cite F11's source page.
L3. Ask First row 1 (SKILL.md:69) offers "generate from the change delta only", but the script with `--change` always checks the merged base + delta set, so untouched base requirements without features are reported MISSING (exit 1). mapping-and-deltas.md:49 describes the merge but not this consequence. Fix: add one sentence saying delta-only generation requires the base features to already exist, or the script gap is expected.
L4. Not run: `scripts/verify_skill.py` and the unit tests (no shell). Release gate for the caller.

Positive checks: F9 (gherkin 42.0.1, keywords, one Background per Feature/Rule), F10 (bold and plain bullets, 4 `#`, no official tooling #508/#987), F11 labelled as factory convention; rules 5, 6 satisfied (question instead of invented Given); neighbour names `testing-quarkus-cucumber-v8-0`, `developing-quarkus-junit-v3-40`, `specifying-changes-with-openspec-v1-15` all exist.

## Cross-skill consistency
- Versions agree: Quarkus 3.40 LTS, RestAssured 6.0.1, JUnit 6.1.3, Testcontainers 2.0.x, quarkus-wiremock 1.8.1 / WireMock 3.13.2, Cucumber 8.0.4. Research dates differ (2026-10-31 vs 2026-11-01) but each is internally consistent.
- Tag conventions agree: `@R<n>` + `@change-<id>`, test names `R<n>_<scenario>_<expectation>` (F11).
- Duplication: only the Failsafe block and two Always Do bullets (cucumber M3); no other overlap.
- Neighbour names all correct.

## Priority order for fixes
Cucumber M2, M1, M3, then L1-L6; integration L3; deriving L3, L1; remaining LOW tag-format items.
