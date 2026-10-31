# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 93%, 6 triangulated claims and domain complexity Complex. Family facts verified by the orchestrator on 2026-10-28 keep the tags of the family facts file. Research ids are kept as written: U3 to U6 (U1 and U2 are not used), I1 and I2, M1 to M10, L1 to L4. M11 was added by this skill for the family-fact pairing with Quarkus patch 3.40.1.1; M12 (the `AWS_REGION` statement), M13 (the BOM-managed `aws-lambda-java-events` version) and M14 (the inferred year of the release date) come from the family facts and later reviews. Register ids are U, I, M and L only; the I class is irresolvable items, which carry the text tag (unverified).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Resolved items](#resolved-items)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkiverse 3.23.0 was released 2026-10-01 (artifacts dated 15:35 on Central) and the pages were read on 2026-10-28. The documentation is complete for the scope but the line is young (medium confidence, M14: the year of the date is inferred; https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sqs/3.23.0/).
- Quarkus 3.40 was released 2026-09-30 as an LTS, community-maintained until 2027-09-30; latest patch 3.40.1.1 (2026-10-19) (High; https://quarkus.io/releases). A Quarkiverse-specific end-of-support date is not published (page not recorded).
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page (High). The extension line `4.0.0.Beta1` to `Beta3` is the Quarkus 4 line and is rejected for this skill; the 3.23.0 patterns are not asserted for it (family rule 1).
- AWS service limits and behaviour are documented only as the current version (the family treats them as High). Re-check the quotas pages before pinning chunk sizes: SQS 1 MiB, SNS 256 KiB default, `PutEvents` 10 entries.

## Unverified items

4 unverified items (do not assert them). U1 and U2 are not used; the numbering follows the research.

| ID | Item | Impact and workaround |
|---|---|---|
| U3 | Cold-start latency added by the SSM and Secrets Manager config sources (no figure published) | Init duration and snapshot content unknown; measure `Init Duration` in CloudWatch with and without the sources |
| U4 | Native-image reflection for `SQSEvent`, `SQSBatchResponse`, `ScheduledEvent` (Joda `DateTime`); page not recorded | Native build or deserialization surprises; run `mvn dependency:tree -Dincludes=com.amazonaws` and a native integration test |
| U5 | Whether Quarkus' Jackson-based event mapping avoids the AWS-documented NPE on the case of `Records` and `eventSourceARN` | Empty or null records in SQS handlers; unit-test with the AWS sample event JSON through the mock event server |
| U6 | Whether AWS SDK 2.55.6 (3.23.0) models the EventBridge Custom Event Bus (EventsV2) `PutEvents` with 100 entries | Chunk size on V2 buses; chunk at 10 (classic API reference) until verified |

## Irresolvable items

2 irresolvable items (the I class is allowed by the register policy). No official page states the answer to either; in the skill text they carry the tag (unverified), and the mapping rows say "U-equivalent, irresolvable".

| ID | Item | Reason and workaround |
|---|---|---|
| I1 | Runtime behaviour of the SSM config-source scheduled reload (`update-interval-minutes` above 0) in a Lambda execution environment frozen between invocations | No page states it and the runtime source tree at tag 3.23.0 returned HTTP 404 (L4). Impact: values may not refresh as expected, or a reload may run during an invocation. Workaround: `update-interval-minutes=0` or read at runtime (Q1 options B and C) |
| I2 | Config-source values under SnapStart (captured in the snapshot at init; refresh after restore not documented) | Neither the Quarkus 3.40 SnapStart guide nor the Quarkiverse docs state it. Impact: stale secrets after rotation for the life of the snapshot. Workaround: Q1 option C with a short TTL, or option B in the handler |

## Medium-confidence items

14 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | `SNSEvent`, `ScheduledEvent` class names (README) and `ScheduledEvent` field types (`time` Joda `DateTime`, `detail` `Map<String,Object>`), plus the event setters and getters used in samples | Main-branch source of `aws-lambda-java-libs` |
| M2 | `SQSBatchResponse` Lombok annotations and builder | Main-branch source; the constructor usage is High from the AWS sample |
| M3 | `@Inject EventBridgeClient` with `quarkus-amazon-eventbridge` | The extension page does not name the class; the name is from the AWS v2 sample |
| M4 | SDK v2 accessor names not on a fetched page: `SendMessageBatchResponse.failed()`, `BatchResultErrorEntry.id()/code()/message()/senderFault()`, `PutEventsResponse.failedEntryCount()`; illustrative code bodies carry the same tag | Compositions of documented APIs, not page text |
| M5 | `url-connection-client` version supplied by the `software.amazon.awssdk:bom` the Quarkiverse BOM imports | BOM import shown; the managed entry itself was not read |
| M6 | Recommending `update-interval-minutes=0` for Lambda | Inference from the SSM page |
| M7 | The Quarkus 3.40 guide's `quarkus-jaxb` instruction applies to manual SDK wiring; relevance to Quarkiverse extensions not stated | Paraphrased by the tool |
| M8 | Quarkus Lambda deserializes events with Jackson; `@JsonProperty("detail-type")` mapping | Inferred from the `quarkus-jackson` dependency of `quarkus-amazon-lambda-common` |
| M9 | `DeleteMessage` alternative needs `sqs:DeleteMessage` and the queue URL | Inference |
| M10 | SQS page `devservices.isolated` without a deprecation note | Tool summary |
| M11 | Running amazon-services 3.23.0 on Quarkus patch 3.40.1.1 | Family fact: High for "built on 3.40.0" (parent POM), the 3.40.1.1 pairing is not stated on a page |
| M12 | The Quarkiverse client picks the region up from `AWS_REGION` in Lambda (same claim and tag as the data skill's M8) | The Quarkiverse region list omits `AWS_REGION`; delegation to the SDK chain (which checks it) is not stated; not resolved |
| M13 | `quarkus-bom` 3.40.1.1 manages `aws-lambda-java-events` 3.16.1 (family fact, rule 13; same tag in every skill) | The BOM (419,419 characters) was read by targeted extraction only; source https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom |
| M14 | Quarkiverse 3.23.0 release date 2026-10-01 (same inference as the data skill's M9) | Read from the releases page rendering ("released 01 Oct"); the year is inferred, not shown |

## Coverage limits

4 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | The SNS 3.23.x page was read 0 to 100,000 of 106,342 characters (S2) |
| L2 | Quarkiverse pages and the Quarkus guide were returned by the tool as summaries with quotes of at most 125 characters; long config tables (SQS: first 40 rows) were not read in full |
| L3 | Three AWS pages returned title-only bodies (`eb-putevent-size`, `eb-events-structure`, `configuration-envvars-runtime`); their content was taken from sibling pages |
| L4 | The Quarkiverse runtime source at tag 3.23.0 was not inspected (GitHub tree 404); config-source facts rest on the versioned page and the docs source at the tag |

## Resolved items

- C1: the brief said SQS limits of "256 KB, batch 10"; the current AWS pages state 1,048,576 bytes (1 MiB) and the batch total also 1 MiB. This skill uses 1 MiB (family fact).
- C2: `PutEvents` 1 to 10 entries (API reference and eb-putevents) versus 1 to 100 (quota page, Custom Event Bus). These are different bus types; the decision is Ask First Q5 and U6 stays open.
- C3: the family fact "3.23.0 is built on Quarkus 3.40.0" was medium and is now High, confirmed by the parent POM `quarkus.version` 3.40.0 (https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom); the 3.40.1.1 pairing stays medium (M11).
- C4: the Quarkus guide's "extensions for DynamoDB, S3, SNS and SQS (more coming)" is stale wording, not a conflict.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) pairing with patch 3.40.1.1 | SKILL.md Version Context; always-do A1; migration-notes | M11 |
| (medium confidence) region picked up from `AWS_REGION` | SKILL.md Ask First (Q9 Region row); always-do A4; evaluation-scenarios | M12 |
| (medium confidence) BOM-managed `aws-lambda-java-events` 3.16.1 | SKILL.md Version Context; ask-first Q3; migration-notes matrix; verification-loop | M13 |
| (medium confidence) release-date year inferred (2026-10-01) | SKILL.md Version Context; version-lifetime risk | M14 |
| (medium confidence) `SNSEvent`, `ScheduledEvent`, event accessors and setters | SKILL.md Ask First Q3; ask-first Q3; sns-eventbridge-handlers; verification-loop | M1 |
| (medium confidence) `SQSBatchResponse` builder | sqs-handler | M2 |
| (medium confidence) `EventBridgeClient` injection | always-do A3; publishing-and-limits | M3 |
| (medium confidence) SDK accessor names and illustrative bodies | never-do N4; always-do A3, A7; publishing-and-limits; sqs-handler; sns-eventbridge-handlers | M4 |
| (medium confidence) `url-connection-client` version via the BOM | always-do A2 | M5 |
| (medium confidence) `update-interval-minutes=0` for Lambda | SKILL.md Ask First Q2; ask-first Q2; config-sources | M6 |
| (medium confidence) `quarkus-jaxb` relevance | ask-first Q4 | M7 |
| (medium confidence) Jackson mapping and `@JsonProperty` | ask-first Q3; sns-eventbridge-handlers | M8 |
| (medium confidence) `DeleteMessage` permissions | SKILL.md Ask First Q7; ask-first Q7 | M9 |
| (medium confidence) `devservices.isolated` without deprecation note | migration-notes | M10 |
| (unverified) config-source cold-start cost | SKILL.md Ask First Q1; ask-first Q1; config-sources; verification-loop | U3 |
| (unverified) native reflection for events library classes | SKILL.md Ask First Q3; ask-first Q3; migration-notes; sns-eventbridge-handlers; verification-loop | U4 |
| (unverified) Jackson mapping versus the `Records` NPE case | sqs-handler | U5 |
| (unverified) SDK 2.55.6 support of the Custom Event Bus | SKILL.md Ask First Q5; ask-first Q5; publishing-and-limits | U6 |
| (unverified) SSM reload in a frozen Lambda | SKILL.md Ask First Q2; ask-first Q1 and Q2; config-sources | I1 (U-equivalent, irresolvable) |
| (unverified) config-source values under SnapStart | SKILL.md Ask First Q1; ask-first Q1 and Q8; config-sources | I2 (U-equivalent, irresolvable) |
| (medium confidence) and (unverified) tags inside scenario expectations | evaluation-scenarios | U3, U4, U6, I1, I2, M1, M3, M4, M6, M11, M12 |

## Source Bibliography

All read 2026-10-28. Research ids S1 to S52 are kept; S23 to S25 and S47 to S52 were added during the gap loop and no id is reused.

**Quarkiverse 3.23.x (versioned)**

| # | URL | Used for |
|---|---|---|
| S1 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html | client types, credentials, url-connection-client |
| S2 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sns.html | SNS client, Dev Services (L1) |
| S3 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-eventbridge.html | EventBridge, Dev Services |
| S4 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html | SSM config source |
| S5 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html | Secrets Manager config source |
| S6 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/index.html | 45 services listed |
| S7 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html | CRT native library |
| S8, S9 | https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/docs/modules/ROOT/pages/amazon-ssm.adoc ; .../amazon-secretsmanager.adoc | docs source at tag 3.23.0 |
| S10, S11 | https://github.com/quarkiverse/quarkus-amazon-services/releases/tag/3.23.0 ; https://github.com/quarkiverse/quarkus-amazon-services/releases | changelog, LTS label, 4.0.0.Beta* |

**Maven Central**

| # | URL | Used for |
|---|---|---|
| S12, S13 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sqs/maven-metadata.xml ; .../quarkus-amazon-secretsmanager/maven-metadata.xml | versions |
| S14 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/ | artifact list |
| S15, S18 to S21 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-{sqs,ssm,secretsmanager,eventbridge,sns}/3.23.0/quarkus-amazon-{...}-3.23.0.pom | optional url-connection-client |
| S16 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sqs/3.23.0/ | release date |
| S17 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom | Quarkus, SDK, CRT versions |
| S22 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom | BOM |
| S24, S25 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda/3.40.1.1/quarkus-amazon-lambda-3.40.1.1.pom ; .../quarkus-amazon-lambda-common/3.40.1.1/quarkus-amazon-lambda-common-3.40.1.1.pom | events dependency |
| S47 | https://repo1.maven.org/maven2/com/amazonaws/aws-lambda-java-events/maven-metadata.xml | latest 3.16.1 |

**Quarkus 3.40 and AWS (current)**

| # | URL | Used for |
|---|---|---|
| S23 | https://quarkus.io/version/3.40/guides/aws-lambda | URL connection client for native sync |
| S26 | https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html | partial batch response |
| S27 | https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html | visibility timeout, redrive |
| S28 | https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html | at-least-once, record fields |
| S29 | https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html | scaling |
| S30, S31 | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html ; .../APIReference/API_SendMessageBatch.html | SQS limits, Failed |
| S32, S33, S34 | https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_PutEvents.html ; .../userguide/eb-putevents.html ; .../userguide/eb-quota.html | PutEvents, quotas |
| S35, S36, S37 | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html ; .../eb-targets.html ; https://docs.aws.amazon.com/eventbridge/latest/ref/overiew-event-structure.html | retry, targets, event shape |
| S38, S39 | https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html ; .../API_Publish.html | SNS limits |
| S40, S41, S42 | https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html ; .../with-eventbridge-scheduler.html ; .../invocation-async-error-handling.html | SNS trigger, Scheduler, async retries |
| S43, S44, S45 | https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html ; https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html ; https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html | Parameters and Secrets extension |
| S46 | https://docs.aws.amazon.com/lambda/latest/dg/java-handler.html | `SQSEvent` input |
| S51, S52 | https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/region-selection.html ; https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html | region, credentials env vars |

**Main branch of aws-lambda-java-libs (at most medium)**: S48 https://github.com/aws/aws-lambda-java-libs/blob/main/aws-lambda-java-events/README.md ; S49 .../ScheduledEvent.java ; S50 .../SQSBatchResponse.java.

**Family facts and not cited for claims**: https://quarkus.io/releases ; https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html (SQS 1 MiB, orchestrator-verified). Pages that returned no usable body (L3) and the 404 source tree (L4) are not cited.
