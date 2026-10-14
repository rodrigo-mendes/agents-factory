# Validation 2 (final) - developing-camel-quarkus-file-v3-40

Validator: skill-best-practices-validator (hybrid knowledge skill rubric). Date 2026-10-14.
Target: packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-file-v3-40/ (SKILL.md 114 lines, 10 blueprints).
Scoring: 100 minus 4 per HIGH, 1.5 per MEDIUM, 0.5 per LOW. URLs were not fetched; presence and consistency only.

**Score: 88 / 100** (1 HIGH, 4 MEDIUM, 4 LOW)

Note on process: the P3 "Report Plan" approval gate could not be obtained from the user inside this run; reports were written to the paths the invoking agent specified.

## Official criteria (A-C)

| ID | Status | Evidence |
|---|---|---|
| A1 | PASS | name = folder, third person, "Use when", "Not for" |
| A2 | PASS | 114 lines |
| A3 | PASS | one level; contents lists in long blueprints; all linked files exist |
| A4 | WARN | M1 (confidence basis inconsistent) |
| A5 | PASS (n/a) | |
| A6 | PASS | |
| B | n/a | |
| C | PASS | 4 scenarios, one per type; scenario 1 must_not has the @ApplicationScoped item (evaluation-scenarios.md:23) |

## Team criteria (D1-D7)

| ID | Status | Evidence |
|---|---|---|
| D1 | PASS | |
| D2 | WARN | H1 |
| D3 | PASS | every row has a Source |
| D4 | n/a | |
| D5 | PASS | all 9 never-do patterns have side-by-side code |
| D6 | PASS | |
| D7 | PASS | |

## Checks requested by the caller

| # | Check | Result |
|---|---|---|
| 1 | High-only Always/Never Do, High alternatives, one claim per bullet | FAIL on one row (H1); Always Do bullets (SKILL.md:47-51) are one High claim each with an inline URL |
| 2 | Source column | PASS. Version Context 14-21 and Quick Reference 84-100 all have URL or "page not recorded" |
| 3 | Shared facts match tags | PARTIAL (M3): SKILL.md:24-25 and register :16-19 match; migration-guide.md:40 does not |
| 4 | Register counts and mapping table | PARTIAL. 12 unverified bullets and 3 irresolvable rows equal the header; two of the 12 are medium, not unverified (M2); no "inferred" row in the mapping table |
| 5 | Not stronger than blueprint | PASS (Always/Never rows and Quick Reference spot-checked against blueprints; inferences stay in the blueprint at the same strength) |
| 6 | @ApplicationScoped | PASS. SKILL.md and all file blueprints contain no sample with the annotation; file-consumer-producer.md:10 says "no CDI annotation needed"; scenario must_not present; no "mandatory" wording |
| 7 | Links and anchors | PASS. `#1-extension-through-the-platform-bom`, `#2-explicit-read-lock`, `#3-explicit-post-processing`, `#4-sftp-host-key-verification`, all nine never-do contents anchors, file-consumer-producer and integration-examples contents anchors, `#version-lifetime-risk`, `#source-bibliography` resolve |
| 8 | Scenarios | PASS |

## Recommendations by priority

### HIGH

- **H1 (check 1, check 3, D2)** SKILL.md:78 Never Do row 6 ("Assume Quarkus 4 compatibility ... (medium confidence, absence of evidence)") is a medium claim inside Never Do. It also breaks this skill's own rule at blueprints/unverified-and-risks.md:10 ("medium confidence ... never in Always Do or Never Do"). Fix: delete the row (Version-lifetime risk, SKILL.md:24, already carries it) or restate it with the High fact only (Beta1 2026-10-01 makes Java 21 the new base, https://quarkus.io/blog/quarkus-4-0-0-beta1-released/) and the High alternative already in the row, as platform-http does at its line 76.

### MEDIUM

- **M1 (A4, check 5)** The medium tag is applied for "single page" to Atomic writes and Idempotency (SKILL.md:57-58; file-consumer-producer.md:45, :56) while readLock, post-processing and SFTP defaults from the same page (file-component.html) are High and drive Always Do. The stated reason ("single page") does not distinguish them. Fix: state the real reason for the medium tag (for example "producer options read through a summary only") or drop it.
- **M2 (check 4)** blueprints/unverified-and-risks.md:38 (4.21/4.22 guides partly read; "medium confidence") and :41 (file-cluster-service defaults, "medium confidence") sit in the Unverified list that header line 3 counts as 12 unverified; they belong in Medium-confidence items. The mapping table (lines 7-12) has no row for the "inferred" tag used at never-do-patterns.md:22, :74, :101 and SKILL.md ("inferred"). Fix: move the two items, recount (10 unverified), add the row.
- **M3 (check 3)** blueprints/migration-guide.md:40 states "Quarkus 4 not supported" untagged; family fact: "No Camel Quarkus build on Quarkus 4 is known" (Medium, absence of evidence). Fix: use the family wording.
- **M4 (cross-skill, check 5)** blueprints/integration-examples.md:43-45 hard-codes `org.apache.camel.quarkus.test.CamelQuarkusTestSupport` and `io.quarkus.test.junit.callback.QuarkusTestMethodContext` in code while register lines 36 and the core skill (irresolvable item: "Package of CamelQuarkusTestSupport ... do not assert"; core eval scenario 2 must_not "Invent a package name") say the package is unverified. A comment disclaims it, but the code still presents a guessed FQN. Fix: drop the imports and write `extends CamelQuarkusTestSupport` with the IDE note, as http does.

### LOW

- **L1** SKILL.md:76 Never Do row 4 says "both pages warn" but cites only the ftp page; add the mina-sftp URL.
- **L2** blueprints/always-do-patterns.md:7 and :21 label sections "Confidence: high" while section 2's sample is from the `main` branch (line 36, medium for the tag). Move the caveat next to the sample.
- **L3** SKILL.md:100 and blueprints/native-mode.md:43 say "log output unverified"; the register has no entry for it (http has one).
- **L4** SKILL.md:74 Never Do row 2 alternative defers to Ask First "Several instances"; fine, but the cell would be clearer as a single High alternative (`readLock=changed`) only.

## Conclusions

Cleanest Always Do tier of the four (one High claim per bullet, URL on each). One Never Do row violates both the family-facts tag and this skill's own register rule, and the register mixes medium items into the unverified count.
