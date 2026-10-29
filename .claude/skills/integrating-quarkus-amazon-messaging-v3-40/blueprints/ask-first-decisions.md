# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Quarkiverse amazon-services 3.23.0 on Quarkus 3.40. Fetched 2026-10-28. Every decision is put to the user. Ids Q1 to Q8 follow the research.

## Contents

- [Q1. Source of secrets and parameters](#q1-source-of-secrets-and-parameters)
- [Q2. SSM update interval in Lambda](#q2-ssm-update-interval-in-lambda)
- [Q3. Event input types](#q3-event-input-types)
- [Q4. Sync or async client and HTTP implementation](#q4-sync-or-async-client-and-http-implementation)
- [Q5. EventBridge bus type and PutEvents chunk size](#q5-eventbridge-bus-type-and-putevents-chunk-size)
- [Q6. SNS payloads above 256 KiB](#q6-sns-payloads-above-256-kib)
- [Q7. SQS partial batch response or delete per message](#q7-sqs-partial-batch-response-or-delete-per-message)
- [Q8. JVM, SnapStart or native](#q8-jvm-snapstart-or-native)

## Q1. Source of secrets and parameters

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. Config source (`quarkus.ssm.config.*`, `quarkus.secretsmanager.config.*`) | Values read as normal `@ConfigProperty`; Secrets Manager "loaded once at startup (the config source does not poll for updates)"; SSM reloads every `update-interval-minutes` (default 5, `0` = once) | Fetch at startup adds cold-start work, size (unverified) (U3); SSM reload in a frozen Lambda and values under SnapStart are (unverified) (I1, I2) | Few, stable values read at boot |
| B. Injected `SsmClient` / `SecretsManagerClient` in code | Explicit call where needed; error handling in code | An API call per read unless you cache | Values needed per request or rarely |
| C. Parameters and Secrets Lambda Extension | "runtime-agnostic"; cache TTL default 300 s, size 1000; Java sample exists | A layer to manage; HTTP call in the handler; token from the credential provider chain (SnapStart) | Rotated secrets needing bounded staleness |
| D. Powertools parameters utility | Integrated API with transforms | Extra dependency; `implementing-lambda-powertools-java` (mention only) | Already using Powertools |

Sources: [Quarkiverse SSM](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html), [Secrets Manager](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html), [AWS extension](https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html). Ask: "How often does each secret or parameter change, is SnapStart (JVM) or native chosen (Q8), and is a per-request read acceptable?"

## Q2. SSM update interval in Lambda

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `5` (default) | Picks up changes in a long-lived JVM | Reload timing in a frozen environment is (unverified) (I1); components that bind config only at startup may not see later changes (paraphrase) | Rarely in Lambda (medium confidence) |
| `0` | Deterministic, one fetch per cold start | Changes only after a new execution environment | Most Lambdas (medium confidence, inference) |

Source: [SSM page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html). Ask: "Is runtime refresh of SSM values required? If yes, prefer option B or C of Q1."

## Q3. Event input types

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. Library types (`SQSEvent`, `SQSBatchResponse`, `SNSEvent`, `ScheduledEvent`) | No mapping code; AWS samples use them | `ScheduledEvent.time` is Joda `DateTime`, `detail` is `Map<String,Object>`; `SNSEvent`/`ScheduledEvent` class details are (medium confidence); native reflection is (unverified) (U4); the managed library version 3.16.1 is (medium confidence) (M13); the NPE case of `Records`/`eventSourceARN` is (unverified) (U5) | SQS (needed for `SQSBatchResponse`) |
| B. Own records | Typed `detail`; you control field names (`detail-type` needs a JSON name) | You maintain the shape; Jackson mapping is (medium confidence) | EventBridge custom events with a known schema |

Sources: [event structure](https://docs.aws.amazon.com/eventbridge/latest/ref/overiew-event-structure.html), [AWS SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html), [events README, main branch](https://github.com/aws/aws-lambda-java-libs/blob/main/aws-lambda-java-events/README.md). Ask: "Does EventBridge `detail` have a fixed schema? For SQS keep the library types."

## Q4. Sync or async client and HTTP implementation

A2 already makes `url-connection-client` explicit. This decision is everything beyond it. The general client story (HTTP client, credentials, endpoint-override) is the [data skill](../../integrating-quarkus-amazon-data-v3-40/SKILL.md).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Sync `url` (default) | Quarkus guide: URL Connection must be preferred over Apache for native sync, and it improves startup (paraphrase) | Blocking calls | Default for Lambda handlers |
| Async `netty` (default async) | Concurrency of many calls in one invocation | Extra `netty-nio-client` dependency | Fan-out publish in one handler |
| `aws-crt` (sync or async) | One client for both modes | "Since AWS CRT version 0.31.0, native library must be embedded in the docker image"; 3.23.0 ships awscrt 0.48.4 | Already standardised on CRT |

Other sync types: `apache`, `apache5`. Sources: [SQS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html), [common features](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html), [Quarkus guide](https://quarkus.io/version/3.40/guides/aws-lambda). The guide's `quarkus-jaxb` instruction applies to manual SDK wiring; its relevance to the Quarkiverse extensions is not stated (medium confidence). Ask: "Many independent AWS calls per invocation? Otherwise keep sync `url`."

## Q5. EventBridge bus type and PutEvents chunk size

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Classic custom/default bus with rules | `PutEvents` 1 to 10 entries; up to 5 targets per rule; regional PutEvents TPS quotas | Smaller chunks | The account uses rules and targets |
| Custom Event Bus (EventsV2) with subscribers | The quota page lists 1 to 100 entries per request | Whether AWS SDK 2.55.6 (the 3.23.0 SDK) models these APIs is (unverified) (U6); target model differs (one target per subscriber) | The account uses the new bus |

Chunk at 10 until verified. Sources: [PutEvents API](https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_PutEvents.html), [quotas](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-quota.html), [targets](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-targets.html). Architecture choice: `architecting-eventbridge-eda`. Ask: "Which bus type does the target account use before chunking PutEvents?"

## Q6. SNS payloads above 256 KiB

Options: raise the topic's `MaximumMessageSize` (up to 1 MiB), or offload to S3 and publish a reference (S3 is the [data skill](../../integrating-quarkus-amazon-data-v3-40/SKILL.md)). Sources: [Publish](https://docs.aws.amazon.com/sns/latest/api/API_Publish.html), [PublishBatch](https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html). Ask: "Expected payload size, and can every subscriber accept up to 1 MiB?"

## Q7. SQS partial batch response or delete per message

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `ReportBatchItemFailures` plus `SQSBatchResponse` (default choice) | No extra SQS calls; "Lambda doesn't scale down message polling when function invocations fail" | Needs the mapping setting in Terraform | New handlers |
| `DeleteMessage` per processed message | Works when the mapping cannot change | Needs the queue URL and `sqs:DeleteMessage` permission (medium confidence, inference) | Mapping fixed by another team |

Powertools batch is `implementing-lambda-powertools-java` (mention only). Sources: [AWS error handling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html), [AWS SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html). Ask only if the event source mapping cannot be changed.

## Q8. JVM, SnapStart or native

The choice is never a default (family rule 3) and is made in the [lambda skill](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md). Effects here: Lambda does not set `AWS_SESSION_TOKEN` in all initialization modes; with SnapStart the function "obtains credentials from a container endpoint instead", so read the token "from the credential provider chain of an AWS SDK" "inside the handler function, not at initialization time" (N9) ([Parameter Store extension](https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html)). Config-source values fetched at init would be captured in the snapshot (inference, I2 is (unverified)). SnapStart does not support OS-only runtimes, so native excludes it ([AWS SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)). Ask: "Which mode did the ADR choose?"
