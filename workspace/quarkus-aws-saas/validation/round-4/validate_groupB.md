# P6 round 4 VALIDATE - group B (independent pass)

Spec: skill-best-practices-validator (A1-A6, B, C, D1-D7) plus family rules 1-15, evidence rule, tag notation, hybrid checklist.
Rubric: 100 - 6 per HIGH - 2.5 per MEDIUM - 0.5 per LOW. Read-only pass; no skill edited.

## Score table

| Skill | HIGH | MEDIUM | LOW | Score |
|---|---|---|---|---|
| integrating-quarkus-amazon-messaging-v3-40 | 0 | 1 | 3 | 96.0 |
| logging-quarkus-lambda-v3-40 | 0 | 0 | 3 | 98.5 |
| tracing-quarkus-lambda-v3-40 | 1 | 1 | 1 | 91.0 |
| monitoring-quarkus-lambda-v3-40 | 0 | 0 | 3 | 98.5 |
| observing-quarkus-lambda (umbrella) | 3 | 3 | 2 | 73.5 |

Verified mechanically: frontmatter is name + description only, name = folder, description quoted, contains "Use when", all under 300 chars (no match for >=300; tracing and umbrella are 280-299). SKILL.md length 109-134 lines. All blueprints <= 160 lines; every blueprint over 100 lines has a Contents list. Quick Navigation links evaluation-scenarios, guardrails and the Verification Loop in all 5. Each skill ships 6 evaluation scenarios, unverified-and-risks.md with Version-lifetime risk, Tag to register mapping and bibliography. Register header counts equal listed items in all 5 registers (messaging 4U/2I/12M/4L; logging 10U/20M/5L; tracing 12U/8M/6L/3D; monitoring 8U/12M/7L/3C; umbrella 12U/6M). Internal anchors and sibling links resolved (including data skill `#c3-region`, http skill `#c1-http-api-or-rest-api`, lambda skill `#c1-jvm-snapstart-or-native`). No absolute paths, `.github`, relative dates or non-plain tag notation found. Cross-skill tags agree for: X-Ray SDK maintenance mode (High, 2026-02-25), Powertools on Quarkus (unverified in logging, tracing, monitoring, umbrella), no Quarkiverse CloudWatch registry (High), EMF limits, `AWS_LAMBDA_LOG_*` under SnapStart (medium), per-mode MDC (medium).

## HIGH findings

### H1 - tracing-quarkus-lambda-v3-40 - BOM version matrix untagged and read-coverage claim contradicts the register (rule 13, evidence rule)
- File: `tracing-quarkus-lambda-v3-40/blueprints/migration-notes.md:39-51`
- Evidence: line 39 "all 419,419 characters read in 5 windows, targeted extraction of `aws` and `opentelemetry` entries only"; rows 43-51 list `aws-xray-recorder-sdk-aws-sdk-v2 | 2.18.3`, `opentelemetry-api 1.62.0`, `opentelemetry-aws-sdk-2.2 2.28.1-alpha`, `aws-lambda-java-core / -events | 1.4.0 / 3.16.1` with no tag.
- Conflicts: (a) the same skill's register records these as M7 "Partial read of the BOM (L3), no verbatim quote recorded (family rule 13)" = (medium confidence), and L3 says "targeted extraction only"; (b) logging register M20 tags the same `aws-lambda-java-core 1.4.0` (medium confidence) with the BOM "read 0 to 100,000 of 419,419"; (c) messaging SKILL.md:22 and migration-notes.md:41 tag the `aws-lambda-java-events` resolved version (unverified) (U4), while this matrix states 3.16.1 as BOM-managed untagged. One claim, three tags across the family.
- Fix: tag every row (medium confidence) per M7, reword line 39 to "targeted extraction, not a full read (L3)", and drop or tag `aws-lambda-java-events 3.16.1` so it agrees with messaging U4 (or have the orchestrator settle it as a family fact and update messaging/logging).

### H2 - observing-quarkus-lambda - medium-confidence MDC claim placed untagged in Always Do
- File: `observing-quarkus-lambda/SKILL.md:45`
- Evidence: "Use one correlation key set across the pillars: `AWSRequestId` and `tenantId` in the log MDC ..." (Always Do bullet 2, no tag).
- Why: the per-mode MDC behaviour is M1 (medium confidence) in this umbrella's own register, and logging SKILL.md:55 deliberately keeps the MDC put out of its Always Do list ("Patterns that cannot be High stay out of this list"). Evidence rule: Always Do holds High claims only; the umbrella "adds no facts" and must keep the pillar's tag/tier.
- Fix: move the MDC part to Ask First 6 (already there) or keep only the High part (tenantId trace annotation key, EMF root property) in Always Do and tag the MDC key `(medium confidence, as in the logging skill)`.

### H3 - observing-quarkus-lambda - medium-confidence claim in a Never Do row, untagged
- File: `observing-quarkus-lambda/SKILL.md:70` (mirrored in `blueprints/never-do-patterns.md:74-88`, N5)
- Evidence: "Assume the same MDC is filled in every mode ([logging]...) | Decide per mode with Ask First 6 and check one JSON log line shows `mdc`"; N5 itself says "(medium confidence)".
- Why: tier rule "Never Do: High rows only, and the alternative is High too"; the pillar skill keeps this out of its Never Do table (F8 is not in logging's table either).
- Fix: remove the row from the SKILL.md table (keep N5 in the blueprint with its tag), or retag as a medium item in Ask First.

### H4 - observing-quarkus-lambda - same claim, two tags (HTTP API trace start)
- File: `observing-quarkus-lambda/blueprints/correlation-recipe.md:77`
- Evidence: "With an HTTP API there is no API Gateway node and the trace starts at the Lambda segment (medium confidence, M3)."
- Conflict: `SKILL.md:59`, `blueprints/ask-first-decisions.md:44` and register mapping row (`unverified-and-risks.md:70`) state the same claim untagged as High; family fact 35 is High, and register M3 says "Upgraded to High ... keeps this row as the record". Rule 13: the same claim carries the same tag everywhere.
- Fix: remove the tag at correlation-recipe.md:77 and the `M3` reference; list that file in the mapping row for the untagged High statement.

(Counts: tracing 1 HIGH = H1; umbrella 3 HIGH = H2, H3, H4.)

## MEDIUM findings

### M-1 - tracing - X-Ray SDK 2.18.3 untagged outside Version Context
- Files: `tracing-quarkus-lambda-v3-40/SKILL.md:60` (Ask First C1 "A: X-Ray SDK 2.18.3"), `blueprints/ask-first-decisions.md:20`, `blueprints/migration-notes.md:15`, `blueprints/always-do-patterns.md:72,102` (code comments).
- Evidence: SKILL.md:18 tags it "(medium confidence)" (M7); the register mapping lists SKILL.md Version Context only.
- Fix: add `(medium confidence)` at SKILL.md:60 and in ask-first C1 (comments in code may keep the note "version per quarkus-bom, medium confidence").

### M-2 - messaging - trailing comments in `.properties` examples
- File: `integrating-quarkus-amazon-messaging-v3-40/blueprints/config-sources.md:17` and `:27`.
- Evidence: `quarkus.lambda.handler=orders-queue                 # handler selection: lambda skill`; `quarkus.ssm.config.update-interval-minutes=0        # choice per Q2; (medium confidence) for Lambda`.
- Why: in a properties file `#` after a value is part of the value; the second line would fail integer conversion if copied. The other skills keep comments on their own line.
- Fix: move both comments to separate lines above the keys.

### M-3 - observing-quarkus-lambda - register points to a non-existent source id
- File: `observing-quarkus-lambda/blueprints/unverified-and-risks.md:47`
- Evidence: "M3 | HTTP API traces start at the `AWS::Lambda` segment | tracing (was M7)"; tracing M7 is "Versions managed by the quarkus-bom 3.40.1.1 POM".
- Fix: change "Carried from" to "family fact 35 (orchestrator-verified)" and fix the mapping row accordingly.

### M-4 - observing-quarkus-lambda - "one key set" is not one key set
- Files: `observing-quarkus-lambda/SKILL.md:45,117`, `blueprints/always-do-patterns.md:21`, `blueprints/correlation-recipe.md:17,58`.
- Evidence: key table: `AWSRequestId` | MDC | trace metadata | "EMF root property"; but correlation-recipe.md:58 says "`tenantId` and `requestId` as root properties" and `monitoring-quarkus-lambda-v3-40/blueprints/emf-implementation.md:52` writes `root.put("requestId", requestId)`; family rule 7 names `requestId`; logging SKILL.md:55 and description say `requestId` while the code uses `AWSRequestId`.
- Why: the join step (correlation-recipe.md:67) queries `mdc.AWSRequestId`; an EMF/metric property named `requestId` does not match the stated key set, so the umbrella's core promise is internally inconsistent.
- Fix: pick one spelling for the EMF property (either state "`requestId` in EMF" explicitly in the key table, or change the monitoring sketch), and make logging SKILL.md:55 say `AWSRequestId`.

### M-5 - observing-quarkus-lambda - Quick Reference row carries a medium claim untagged
- File: `observing-quarkus-lambda/SKILL.md:117`
- Evidence: "MDC keys | `AWSRequestId` (poll loop spelling), `tenantId` | logging" (no tag; source is logging M2 / U8 spelling).
- Fix: add `(medium confidence)`, same as the table on line 93.

(Counts: tracing 1 MEDIUM = M-1; messaging 1 = M-2; umbrella 3 = M-3, M-4, M-5.)

## LOW findings

Messaging
- L-1 `integrating-quarkus-amazon-messaging-v3-40/SKILL.md:52-61`: Always Do bullets carry two inline URLs and, for A8/A9, several claims (evidence rule: one High claim, one URL per bullet).
- L-2 `SKILL.md:17`: confidence written as lowercase "high" ("Built on Quarkus 3.40.0 (parent POM ...); high"); tag notation uses plain `(medium confidence)`/`(unverified)` and "High" elsewhere. Reword to "High (parent POM)".
- L-3 `SKILL.md:74`: Ask First row "Region source in Lambda" has no Q id (Q1-Q8 skip it); give it Q9 or fold it into Q4.

Logging
- L-4 `logging-quarkus-lambda-v3-40/SKILL.md:3,55` vs `blueprints/always-do-patterns.md:92`: skill text says MDC `requestId`; code and blueprints use `AWSRequestId` (see M-4).
- L-5 `blueprints/verification-loop.md:88`: checklist "Every handler puts and clears `AWSRequestId` and `tenantId` in `finally` (JVM mode)" has no `(medium confidence)` although the same claim is tagged in always-do 6 and migration-notes.
- L-6 `SKILL.md:51,52`: Always Do bullets with two URLs (same as L-1).

Tracing
- L-7 `tracing-quarkus-lambda-v3-40/SKILL.md:48,50,52`: Always Do bullets end with the caveat sentence "X-Ray SDK is in maintenance mode since 2026-02-25"; evidence rule says caveats move to Ask First (C1 already carries it). Keep as a path label in the bullet heading instead.

Monitoring
- L-8 `monitoring-quarkus-lambda-v3-40/SKILL.md:17`: extension row cites the unversioned `https://quarkus.io/guides/aws-lambda` (max medium by the evidence rule); every sibling skill uses `https://quarkus.io/version/3.40/guides/aws-lambda`.
- L-9 `SKILL.md:21`: `powertools-metrics` 2.11.0 untagged (Maven metadata, defensible), while family fact 37 tags 2.11.0 (medium confidence). Add a note "(registry; family fact 37 medium from docs)" or tag it.
- L-10 `SKILL.md:60` and `blueprints/migration-notes.md:11`: "Powertools says frameworks are 'not officially supported'" and "Powertools 2.x supports Java 17 to 25" are M5/C-2 (latest pages, medium) but untagged here; ask-first D1 tags them.

Umbrella
- L-11 `observing-quarkus-lambda/blueprints/unverified-and-risks.md:28,58`: U3 (MDC classes share a store) is listed but the mapping row says "not asserted"; the tag is used nowhere in the umbrella. Remove or use it.
- L-12 `SKILL.md:44-49`: Always Do bullets cite no source URL, only pillar anchors; acceptable for a carry-only umbrella, but the evidence rule asks for an inline URL per bullet. Add the primary URL of each carried claim or state the exemption in Version Context.

(Counts: messaging 3 = L-1..L-3; logging 3 = L-4..L-6; tracing 1 = L-7; monitoring 3 = L-8..L-10; umbrella 2 = L-11, L-12.)

## Cross-skill consistency summary

| Fact | messaging | logging | tracing | monitoring | umbrella | Family fact |
|---|---|---|---|---|---|---|
| X-Ray SDK maintenance mode 2026-02-25 | - | - | High | - | High | High (34) - consistent |
| Powertools logging/tracing/metrics on Quarkus | name only | (unverified) | (unverified) | (unverified) | (unverified) | (unverified) (36) - consistent |
| EMF limits 100/30/100/1 MB | - | - | - | High | High | n/a |
| quarkus-bom managed versions (aws-lambda-java-core 1.4.0, events 3.16.1, X-Ray SDK 2.18.3) | events (unverified) | core (medium) | untagged matrix (H1), 2.18.3 untagged outside Version Context (M-1) | - | 2.18.3 untagged in ask-first 1 | Not a family fact -> propose orchestrator settle |
| MDC request-id key | - | `AWSRequestId` (text says `requestId`) | - | EMF property `requestId` | `AWSRequestId` (M-4) | rule 7: `requestId` |
| HTTP API trace starts at Lambda segment | - | - | High | - | High in SKILL, medium in correlation-recipe (H4) | High (35) |
| Per-mode MDC, `AWS_LAMBDA_LOG_*` under SnapStart | - | medium (kept out of Always/Never) | - | - | medium, but placed in Always/Never untagged (H2, H3) | n/a |

Research provenance: no fact absent from its research file was found in messaging, logging (Quarkus 4 Beta1 date is a Camel-family fact, accepted by the family facts header), tracing or monitoring beyond the items above; umbrella adds no new research facts except the tags noted.
