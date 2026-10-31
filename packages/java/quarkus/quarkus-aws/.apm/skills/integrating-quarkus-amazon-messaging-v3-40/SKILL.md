---
name: integrating-quarkus-amazon-messaging-v3-40
description: "Integrates SQS, SNS, EventBridge clients and SSM/Secrets Manager config sources in Quarkus 3.40 LTS Lambdas with amazon-services 3.23.0, plus queue, topic and event handlers. Use when sending or consuming AWS messages. Not for DynamoDB, S3, HTTP, Terraform or Quarkus 4."
---

# Integrating Quarkus Amazon Messaging and Config Sources 3.40

> Version lock: every claim applies to **Quarkiverse `quarkus-amazon-services` 3.23.0 on Quarkus 3.40 LTS** only. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: `quarkus-amazon-sqs`, `-sns`, `-eventbridge`, `-ssm`, `-secretsmanager` (clients and the SSM / Secrets Manager config sources), and SQS-, SNS-, EventBridge-triggered handlers. Neighbours: [integrating-quarkus-amazon-data-v3-40](../integrating-quarkus-amazon-data-v3-40/SKILL.md) (DynamoDB, S3, general client config: HTTP client, credentials, region, idempotency stores), [developing-quarkus-amazon-lambda-v3-40](../developing-quarkus-amazon-lambda-v3-40/SKILL.md) (handler wiring, packaging, SnapStart), [testing-quarkus-amazon-lambda-v3-40](../testing-quarkus-amazon-lambda-v3-40/SKILL.md) (tests, Dev Services). By name only: `architecting-aws-sqs-messaging`, `architecting-aws-sns-pubsub`, `architecting-eventbridge-eda`, `implementing-lambda-powertools-java`, `provisioning-aws-sqs-v6`, `provisioning-aws-sns-v6`, `provisioning-aws-eventbridge-v6`, `provisioning-aws-secrets-manager-v6`, `provisioning-aws-parameter-store-v6`. Quarkus 4 and Quarkiverse 4.0.0.Beta* are out of scope.

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| Quarkiverse amazon-services | 3.23.0, the only 3.23.x on Maven Central; GitHub release "3.23.0 (LTS)"; artifacts dated 2026-10-01 (medium confidence, M14: year inferred) | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sqs/maven-metadata.xml ; https://github.com/quarkiverse/quarkus-amazon-services/releases |
| Quarkus base of 3.23.0 | Built on Quarkus 3.40.0 (parent POM `quarkus.version` 3.40.0); High (parent POM) | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom |
| Pairing with Quarkus patch 3.40.1.1 | Not stated on a page (medium confidence) | https://github.com/quarkiverse/quarkus-amazon-services/releases |
| AWS SDK for Java v2 / AWS CRT | 2.55.6 / 0.48.4; Java source and target 17 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom |
| Quarkus 3.40 | LTS, released 2026-09-30, community-maintained until 2027-09-30; latest patch 3.40.1.1 (2026-10-19) | https://quarkus.io/releases |
| Quarkiverse end-of-support date | page not recorded (not published) | page not recorded |
| `aws-lambda-java-events` | Comes through `quarkus-amazon-lambda-common` 3.40.1.1; `quarkus-bom` 3.40.1.1 manages version 3.16.1 (medium confidence, M13) | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-common/3.40.1.1/quarkus-amazon-lambda-common-3.40.1.1.pom |
| SQS message size and batch | 1,048,576 bytes (1 MiB); batch up to 10 messages | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html |
| SNS message size | 256 KiB by default, raisable to 1 MiB with `MaximumMessageSize`; `PublishBatch` up to 10 | https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html |
| EventBridge PutEvents (classic bus) | 1 to 10 entries, request below 1 MB; the Custom Event Bus lists 1 to 100 (Ask First Q5) | https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_PutEvents.html |

**Version-lifetime risk** (details in [register](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkiverse 3.23.0 was released 2026-10-01 (medium confidence, M14: year inferred) and the pages were read on 2026-10-28. The documentation covers the scope but the line is young.
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page; `4.0.0.Beta1` to `Beta3` of the extensions are the Quarkus 4 line and are rejected here. Pin 3.23.0.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [SQS-triggered handler](./blueprints/sqs-handler.md)
- [SNS- and EventBridge-triggered handlers](./blueprints/sns-eventbridge-handlers.md)
- [Publishing and limits](./blueprints/publishing-and-limits.md)
- [SSM and Secrets Manager config sources](./blueprints/config-sources.md)
- [Verification Loop](./blueprints/verification-loop.md#verification-loop)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Import `quarkus-amazon-services-bom` 3.23.0 and declare the `io.quarkiverse.amazonservices:quarkus-amazon-{sqs,sns,eventbridge,ssm,secretsmanager}` artifacts without versions.** The BOM manages all five ([BOM POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom)). See [A1](./blueprints/always-do-patterns.md#a1-coordinates-and-bom).
- **Add `software.amazon.awssdk:url-connection-client` explicitly for the SQS, SNS and EventBridge sync clients.** It is `optional` in their 3.23.0 POMs ([SQS POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sqs/3.23.0/quarkus-amazon-sqs-3.23.0.pom)). See [A2](./blueprints/always-do-patterns.md#a2-explicit-url-connection-client).
- **Inject the SDK client the extension produces (`SqsClient`, `SnsClient`, `SsmClient`, `SecretsManagerClient`).** Do not build clients by hand ([SNS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sns.html)). See [A3](./blueprints/always-do-patterns.md#a3-inject-the-sdk-client).
- **Leave `aws.credentials.type` at its default in a deployed Lambda.** The default chain resolves the execution role ([Lambda env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)). See [A4](./blueprints/always-do-patterns.md#a4-default-credentials-and-region).
- **Return `SQSBatchResponse` with the failed `messageId` values from an SQS handler.** A thrown exception fails the whole batch ([AWS error handling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)). See [A5](./blueprints/always-do-patterns.md#a5-sqs-handler-returns-sqsbatchresponse).
- **Set the queue visibility timeout to at least six times the function timeout and `maxReceiveCount` to at least 5.** Write both in Terraform with `provisioning-aws-sqs-v6` ([AWS configure](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)). See [A6](./blueprints/always-do-patterns.md#a6-visibility-timeout-and-redrive).
- **Make every SQS-, SNS- and EventBridge-triggered handler idempotent.** Lambda processes each event at least once ([AWS SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)). See [A7](./blueprints/always-do-patterns.md#a7-idempotent-handlers).
- **Check the per-entry result of every batch publish, even on HTTP 200.** That is `Failed` for SQS `SendMessageBatch` and SNS `PublishBatch`, and `FailedEntryCount` plus index-aligned `Entries` for `PutEvents` ([PutEvents](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html)). See [A8](./blueprints/always-do-patterns.md#a8-per-entry-result-checks).
- **Send at most 10 entries per SQS or SNS batch and keep SQS messages at or below 1 MiB.** SNS defaults to 256 KiB ([SNS PublishBatch](https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html)). See [A9](./blueprints/always-do-patterns.md#a9-batch-and-size-limits).
- **Map each Secrets Manager config property to a named secret.** An empty map loads every accessible secret ([Secrets Manager page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html)). See [A10](./blueprints/always-do-patterns.md#a10-explicit-secret-mappings).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Q1 Source of secrets and parameters | A: config source (loaded at startup; fetch cost U3 (unverified); behaviour under SnapStart is (unverified), I2). B: injected client in code. C: AWS Parameters and Secrets Lambda Extension (`localhost:2773`). D: Powertools (by name). [Detail](./blueprints/ask-first-decisions.md#q1-source-of-secrets-and-parameters) | "How often does each value change, is SnapStart or native chosen, is a per-request read acceptable?" |
| Q2 `quarkus.ssm.config.update-interval-minutes` | Default `5` vs `0` (fetch once). Reload in a frozen Lambda environment is (unverified), I1; `0` for Lambda is (medium confidence). [Detail](./blueprints/ask-first-decisions.md#q2-ssm-update-interval-in-lambda) | "Is runtime refresh of SSM values required?" |
| Q3 Event input types | Library types (`SQSEvent` needed for `SQSBatchResponse`) vs own records for EventBridge `detail`. `SNSEvent`, `ScheduledEvent` are (medium confidence); native reflection (unverified). [Detail](./blueprints/ask-first-decisions.md#q3-event-input-types) | "Does EventBridge `detail` have a fixed schema?" |
| Q4 HTTP client beyond the explicit `url-connection-client` | Sync `url` (default) / `apache` / `apache5` / `aws-crt`; async `netty` (default) / `aws-crt`. CRT native library is not embedded by default. General story: [data skill](../integrating-quarkus-amazon-data-v3-40/SKILL.md). [Detail](./blueprints/ask-first-decisions.md#q4-sync-or-async-client-and-http-implementation) | "Many independent AWS calls per invocation? Already on CRT?" |
| Q5 EventBridge bus type and `PutEvents` chunk size | Classic bus: 10 entries. Custom Event Bus (EventsV2): 1 to 100 on the quota page; SDK 2.55.6 support is (unverified) (U6). Chunk at 10 until confirmed. [Detail](./blueprints/ask-first-decisions.md#q5-eventbridge-bus-type-and-putevents-chunk-size) | "Which bus type does the target account use?" |
| Q6 SNS payloads above 256 KiB | Raise `MaximumMessageSize` (up to 1 MiB) vs S3 reference ([data skill](../integrating-quarkus-amazon-data-v3-40/SKILL.md)). [Detail](./blueprints/ask-first-decisions.md#q6-sns-payloads-above-256-kib) | "Expected payload size; can every subscriber take 1 MiB?" |
| Q7 SQS failure reporting | `ReportBatchItemFailures` (default choice) vs `DeleteMessage` per message (permissions are (medium confidence)). [Detail](./blueprints/ask-first-decisions.md#q7-sqs-partial-batch-response-or-delete-per-message) | "Can the event source mapping be changed?" |
| Q9 Region source in Lambda | That the region comes from `AWS_REGION` is (medium confidence): the SDK chain checks it, but whether Quarkiverse 3.23.0 delegates to that chain is not stated; set the region explicitly or smoke-test. See the data skill's [C3](../integrating-quarkus-amazon-data-v3-40/blueprints/ask-first-decisions.md#c3-region) ([Lambda env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)) | "Set `quarkus.<svc>.aws.region` explicitly, or rely on `AWS_REGION` after a smoke test?" |
| Q8 JVM + SnapStart vs native | Never a default; decide in the [lambda skill](../developing-quarkus-amazon-lambda-v3-40/SKILL.md). Effect here: token and config-source timing. [Detail](./blueprints/ask-first-decisions.md#q8-jvm-snapstart-or-native) | "Which mode did the ADR choose?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| N1 Throw from the SQS handler because one record failed; "the entire batch is considered a complete failure" ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)) | Catch per record and return `SQSBatchResponse` with the failed IDs ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)) |
| N2 Return the receipt handle, an empty, a null or an unknown value as `itemIdentifier` ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)) | Return `message.getMessageId()` ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)) |
| N3 Keep processing after the first failure on a FIFO queue ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)) | Stop and return the failed and all unprocessed messages ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)) |
| N4 Treat HTTP 200 from a batch publish as "all entries succeeded" ([SQS API](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessageBatch.html)) | Inspect the per-entry failures of every response and retry or raise ([PutEvents](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html)) |
| N5 Send more than 10 entries in one SQS, SNS or classic-bus `PutEvents` call ([SNS API](https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html)) | Split into chunks of at most 10 and check each response ([SNS API](https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html)) |
| N6 Set the visibility timeout below the function timeout ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)) | Use at least 6 times the function timeout, plus `MaximumBatchingWindowInSeconds` ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)) |
| N7 Put static AWS keys in the production `application.properties` ([SQS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html)) | Keep the default credentials type; static keys only under `%dev` or `%test` ([SQS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html)) |
| N8 Subscribe a Lambda to an SNS FIFO topic ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html)) | Use a standard SNS topic ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html)) |
| N9 Read `AWS_SESSION_TOKEN` at init for the extension header ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html)) | Resolve the token from the SDK credential provider chain inside the handler ([AWS](https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html)) |
| N10 Use `sync-client.type=apache` in a native Lambda ([Quarkus guide](https://quarkus.io/version/3.40/guides/aws-lambda)) | Keep `sync-client.type=url` plus `url-connection-client` ([Quarkus guide](https://quarkus.io/version/3.40/guides/aws-lambda)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Artifacts | `io.quarkiverse.amazonservices:quarkus-amazon-sqs`, `-sns`, `-eventbridge`, `-ssm`, `-secretsmanager` 3.23.0 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom |
| Client types | `quarkus.<svc>.sync-client.type` default `url`; `quarkus.<svc>.async-client.type` default `netty` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html |
| Credentials | `quarkus.<svc>.aws.credentials.type` default `default` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html |
| Config sources | `quarkus.ssm.config.enabled`, `quarkus.secretsmanager.config.enabled`, each default `false` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html ; https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html |
| SQS trigger | `FunctionResponseTypes=ReportBatchItemFailures`; visibility timeout at least 6x function timeout; `maxReceiveCount` at least 5 | https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html |
| Batch limits | SQS 10 messages / 1 MiB; SNS 10 / 256 KiB default; classic `PutEvents` 10 entries / below 1 MB | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html |
| Async retries | Lambda async invocation: two more retries by default; EventBridge target retry 24 hours, up to 185 times | https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html ; https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html |
| Extension | Parameters and Secrets Lambda Extension: port 2773, header `X-Aws-Parameters-Secrets-Token`, cache TTL default 300 s | https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html |
| Representative command | `mvn -q dependency:tree -Dincludes=io.quarkiverse.amazonservices` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html |

## External Resources

All fetched 2026-10-28.

- Quarkiverse 3.23.x guides: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/
- Quarkus AWS Lambda guide: https://quarkus.io/version/3.40/guides/aws-lambda
- Lambda with SQS error handling: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html
- EventBridge PutEvents: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html
- Full bibliography: [register](./blueprints/unverified-and-risks.md#source-bibliography)
