# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 88%, a deep run using all 3 iterations, and 5 triangulated claims. Family facts verified by the orchestrator on 2026-10-28 keep the tags of the family facts file. IDs are the research IDs, except that the research contradictions C-1 and C-2 are carried as M13 and M14 and C-3 is merged into M3 (register ids are U, I, M and L only). Items documentation cannot settle are listed once, as U-ids tagged (unverified); there is no separate irresolvable class.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

| Risk | Detail | Source |
|---|---|---|
| Quarkus 3.40 lifetime | LTS released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 (2026-10-19). Quarkus 4.0.0 "Upcoming" with no date; Quarkus 4 content is rejected (family rule 1) | https://quarkus.io/releases |
| Freshness: `aws-embedded-metrics-java` | Last release 4.2.0 on 2024-08-02, more than 12 months old; the README states no maintenance status | https://repo1.maven.org/maven2/software/amazon/cloudwatchlogs/aws-embedded-metrics/maven-metadata.xml |
| Powertools moves fast | 2.11.0 (2026-10-06); the "latest" docs page carries a "not viewing the latest version" banner (M5); the existing `implementing-lambda-powertools-java` skill is locked to 2.10.0 | https://repo1.maven.org/maven2/software/amazon/lambda/powertools-metrics/maven-metadata.xml |
| AWS direction | AWS says "For new implementations, we recommend using OpenTelemetry to publish custom metrics"; the X-Ray SDK is in maintenance mode since 2026-02-25 (family fact). The emission approach may need a new ADR | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html |
| Pricing | unversioned and region-specific (M1) | https://aws.amazon.com/cloudwatch/pricing/ |

## Unverified items

9 unverified items (do not assert them).

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Quarkus compatibility of Powertools metrics (annotation with AspectJ weaving on CDI beans, functional API inside `QuarkusStreamHandler`); not stated on any page (follow-up: https://github.com/aws-powertools/powertools-lambda-java issues, Powertools "frameworks" pages) | Do not recommend as supported; use hand-written EMF or test in a deployed function (if mandated, functional API tested in a deployed function) |
| U2 | `aws-embedded-metrics-java` 4.2.0 behaviour under Lambda JSON log format, in Quarkus and in native image; README is silent | Deployed test before adoption |
| U3 | Data loss or delay of push registries (Micrometer step registry, OTel periodic reader) on frozen Lambda environments; inference only; no official statement (follow-up: Micrometer CloudWatch docs 1.17.x, AWS Lambda and OpenTelemetry docs) | Prefer EMF; if mandated, force a publish before the handler returns and verify in a deployed test |
| U4 | `micrometer-registry-cloudwatch2` constructor and SDK client requirements and native-image support | Do not invent producer code; ask and test |
| U5 | PutMetricData request price: the tool returned "$0.01/M requests"; unit ambiguous | Read the pricing page before budgeting |
| U6 | Whether `quarkus-amazon-lambda` 3.40.1.1 brings a Jackson `ObjectMapper` bean transitively | Add `quarkus-jackson` explicitly if the build needs it |
| U7 | CloudWatch Logs Insights price per GB scanned | Read the pricing page before choosing tenant option B |
| U8 | Names of the `AWS/Logs` metrics that report EMF parsing and validation failures | Look them up on the EMF spec page before alarming on them |
| U9 | CloudWatch Logs ingestion price per GB: the pricing page examples conflict ($0.25 vs $0.50 for the same scenario); same tag as the logging skill | Do not quote a price; read the pricing page before budgeting |

## Medium-confidence items

14 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Pricing figures ($0.30 per metric first 10,000, free tier 10 metrics; the log-ingestion price is U9, not quoted) | US East (N. Virginia), unversioned page |
| M2 | Micrometer 1.17.1 and the `micrometer-bom` import in the Quarkus 3.40.1.1 BOM | BOM partly read (L3) |
| M3 | Micrometer CloudWatch docs read at 1.17.2, not 1.17.1 | Patch differs |
| M4 | `aws-embedded-metrics-java` README statements | Main-branch page |
| M5 | Powertools pages (including the "GraalVM support" bullet and the "not officially supported" tenet) | "Latest" pages with a version banner while Central has 2.11.0 |
| M6 | `InitDuration` is not a listed `AWS/Lambda` metric | Absence of evidence |
| M7 | No Quarkiverse CloudWatch registry | Research: absence of evidence. Upgraded to High by the family fact verified 2026-10-28 (full Central listing); the skill states it as High and keeps this row as the record |
| M8 | EMF lines without `level` are dropped when `ApplicationLogLevel` is WARN or higher | Inference from two High statements |
| M9 | A raw EMF line on `System.out` with Lambda JSON log format stays at the root | Inference from "doesn't double-encode"; AWS recommends testing |
| M10 | Quarkus native on `provided.al2023` gets no Lambda-side JSON capture or filtering unless the runtime honours `AWS_LAMBDA_LOG_FORMAT` and `AWS_LAMBDA_LOG_LEVEL` | Inference from two pages |
| M11 | Default Micrometer binders publish JVM and system meters as billed custom metrics | Inference from Quarkus defaults and metric concepts |
| M12 | `quarkus-logging-json` places an EMF string logged through the Quarkus logger inside its own JSON document (the wrapping half of Never Do F1) | Inference from the extension's purpose; no page read shows it (family rule 13). The High half is the default console format prefix against EMF "no additional data" |
| M13 | Powertools metrics page says "CloudWatch EMF supports a max of 9 dimensions per metric" and, on the same page, "Maximum of 30 dimensions"; the AWS EMF spec says a DimensionSet "MUST NOT contain more than 30 dimension keys". Rule applied: follow the AWS spec (30); the Powertools "9" is treated as stale | Contradiction inside a "latest" Powertools page (M5). URLs: https://docs.aws.amazon.com/powertools/java/latest/core/metrics/ and https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html |
| M14 | Powertools home says Java "from 17 to 25"; the Lambda Java logging guide's Powertools SAM walkthrough requires "Java 11" and uses `--runtime java11`. Rule applied: treat the Lambda sample as outdated | Two official pages disagree. URLs: https://docs.aws.amazon.com/powertools/java/latest/ and https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html |

## Coverage limits

7 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | monitoring-cloudwatchlogs-advanced.html returned no body text |
| L2 | Quarkus logging guide: characters 0 to 100,000 of 199,486 |
| L3 | Quarkus BOM `pom.xml`: characters 0 to 200,000 of 318,246 |
| L4 | Pricing page: tool summaries in two passes (0 to 100,000, 100,000 to 154,061); only quoted figures used |
| L5 | Quotas page: only the CloudWatch metrics and API table inspected |
| L6 | Quarkus Micrometer guide: tool-estimated 55,000 characters, answered as a summary with short quotes |
| L7 | All pages: the fetch tool caps verbatim quotes at about 125 characters |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) `aws-embedded-metrics` under Quarkus, native, JSON log format | SKILL.md Ask First; ask-first-decisions D1 | U2 |
| (unverified) Powertools metrics on Quarkus; Powertools Java logging inside Quarkus (unverified) | SKILL.md Ask First; ask-first-decisions D1, D5; migration-notes; evaluation-scenarios 5 | U1 |
| (unverified) push registry or OTel export on a frozen environment | SKILL.md Ask First; ask-first-decisions D1; emf-implementation; evaluation-scenarios 5 | U3 |
| (unverified) `micrometer-registry-cloudwatch2` constructor, SDK client, native | ask-first-decisions D1; emf-implementation | U4 |
| (unverified) PutMetricData price unit | cardinality-cost-and-builtins Cost | U5 |
| (unverified) Jackson `ObjectMapper` bean | emf-implementation Metrics bean | U6 |
| (unverified) Logs Insights scan price | ask-first-decisions D2; cardinality-cost-and-builtins Cost | U7 |
| (unverified) `AWS/Logs` metric names | never-do F1; verification-loop | U8 |
| (medium confidence) pricing figures | SKILL.md Quick Reference; ask-first-decisions D2; cardinality-cost-and-builtins | M1 |
| (medium confidence) Micrometer 1.17.1 via the Quarkus BOM | SKILL.md Version Context; migration-notes | M2 |
| docs page 1.17.2 vs 1.17.1 (version mismatch of the doc, not a content conflict) | migration-notes | M3 |
| (medium confidence) README on main branch; README states no maintenance status (absence of evidence) | SKILL.md Version Context; ask-first-decisions D1 | M4 |
| (medium confidence) Powertools "latest" pages, "GraalVM support" bullet | SKILL.md Quick Reference; ask-first-decisions D1 | M5 |
| (medium confidence) `InitDuration` not listed | ask-first-decisions D5; cardinality-cost-and-builtins | M6 |
| no Quarkiverse CloudWatch registry (stated High) | SKILL.md Version Context and Ask First; ask-first-decisions D1; migration-notes | M7 |
| (medium confidence) WARN or higher drops EMF lines without `level` | SKILL.md Ask First; ask-first-decisions D3 | M8 |
| (medium confidence) raw EMF line stays at the root under JSON format | ask-first-decisions D3 | M9 |
| (medium confidence) native on `provided.al2023` log handling | ask-first-decisions D3 | M10 |
| (medium confidence) default binders as billed metrics | SKILL.md Quick Reference; ask-first-decisions D1; emf-implementation | M11 |
| (medium confidence) `quarkus-logging-json` wraps a logged EMF string | never-do F1 | M12 |
| page read in part | SKILL.md Quick Reference; never-do F1; cardinality-cost-and-builtins | L2, L4, L5, L6 |
| (medium confidence) Powertools 9 vs 30 dimensions | SKILL.md Quick Reference; always-do 4 | M13 |
| (medium confidence) Powertools `java11` sample | migration-notes | M14 |
| (unverified) log ingestion price per GB | cardinality-cost-and-builtins Cost | U9 |

## Source Bibliography

All read 2026-10-28.

| # | URL | Coverage | Used for |
|---|---|---|---|
| S1 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html | full | document shape, limits, timestamp, cardinality |
| S2 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Libraries.html | full | stdout in Lambda |
| S3 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Alarms.html | full | EMF alarms |
| S4 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html | full | units, resolution, retention |
| S5 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html | full | publishing, visibility delay |
| S6 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricData.html | full | namespace rule, limits |
| S7 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html | full | units, value range |
| S8 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_limits.html | metrics table only (L5) | quotas |
| S9 | https://aws.amazon.com/cloudwatch/pricing/ | summaries (L4) | prices |
| S10 | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html | full | built-in metrics |
| S11 | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html | full | built-in metric list |
| S12 | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-view.html | full | namespace, dimensions |
| S13 | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html | full | log format |
| S14 | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html | full | log-level filtering |
| S15 | https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html | full | Java stdout, REPORT line |
| S16 | https://docs.aws.amazon.com/lambda/latest/dg/nodejs-logging.html | full (EMF section) | JSON format warning |
| S17 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html | full | freeze and lifecycle |
| S18 | https://quarkus.io/version/3.40/guides/telemetry-micrometer | summary (L6) | Micrometer, cardinality, binders |
| S19 | https://quarkus.io/version/3.40/guides/logging | 0 to 100,000 of 199,486 (L2) | console format, JSON logging |
| S20 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/bom/application/pom.xml | 0 to 200,000 of 318,246 (L3) | Micrometer BOM import (cited in SKILL.md Version Context) |
| S21 | https://repo1.maven.org/maven2/io/micrometer/micrometer-bom/1.17.1/micrometer-bom-1.17.1.pom | read | `micrometer-registry-cloudwatch2` 1.17.1 |
| S22 | https://docs.micrometer.io/micrometer/reference/implementations/cloudwatch.html | read, version 1.17.2 (M3) | step 1 minute |
| S23 | https://docs.quarkiverse.io/quarkus-micrometer-registry/dev/ | read | registries list |
| S24 | https://repo1.maven.org/maven2/io/quarkiverse/micrometer/registry/ | read | no cloudwatch |
| S25 | https://repo1.maven.org/maven2/io/quarkiverse/micrometer/registry/quarkus-micrometer-registry-cloudwatch/maven-metadata.xml | HTTP 404 | absence |
| S26 | https://github.com/awslabs/aws-embedded-metrics-java | main branch (M4) | library API |
| S27 | https://repo1.maven.org/maven2/software/amazon/cloudwatchlogs/aws-embedded-metrics/maven-metadata.xml | read | 4.2.0, 2024-08-02 |
| S28 | https://docs.aws.amazon.com/powertools/java/latest/core/metrics/ | read (M5) | Powertools metrics |
| S29 | https://docs.aws.amazon.com/powertools/java/latest/ | read (M5) | tenets, Java range |
| S30 | https://repo1.maven.org/maven2/software/amazon/lambda/powertools-metrics/maven-metadata.xml | read | 2.11.0, 2026-10-06 |
| S31 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/metrics-otel-send.html | full | OpenTelemetry path, IAM action |
| S32 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Stats.html | full | Logs Insights `stats` |

Validation searches (not evidence): WebSearch "quarkus-micrometer-registry-cloudwatch quarkiverse" and "Powertools for AWS Lambda Java Quarkus support metrics" (2026-10-28), no CloudWatch registry and no official Quarkus statement found. The Lambda advanced logging controls page returned a title only (L1).

**Family facts used** (orchestrator-verified, not re-fetched): Quarkus 3.40 LTS dates and patch (https://quarkus.io/releases); Lambda runtimes (https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html); handler wiring and native packaging (https://quarkus.io/guides/aws-lambda); no Quarkiverse CloudWatch registry (https://repo1.maven.org/maven2/io/quarkiverse/micrometer/registry/); Quarkus logging guide Log4j prohibition (https://quarkus.io/version/3.40/guides/logging); Powertools 2.11.0 (medium confidence, https://docs.powertools.aws.dev/lambda/java/); `quarkus-test-amazon-lambda` removed in 3.31 (https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31); X-Ray maintenance mode (https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html).
