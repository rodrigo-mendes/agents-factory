# Research: Quarkiverse amazon-services 3.23.x messaging and configuration (SQS, SNS, EventBridge, SSM, Secrets Manager) for Quarkus 3.40 LTS Lambdas

Unit U5 of the quarkus-aws-saas family. Future skill: `integrating-quarkus-amazon-messaging-v3-40` (package `quarkus-aws`).
Source item: "SQS/SNS/EventBridge + SSM/Secrets Manager from Quarkus Lambdas".
Family facts applied as given: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `workspace/_family_facts_v3.40.md`.
Family rules applied as given: `workspace/quarkus-aws-saas/_family_rules_v3.40.md` (incl. rules 5, 9-12), `workspace/_family_rules_v3.40.md` (incl. evidence rule 5 and tag notation rule 7).

All pages were read on **2026-10-28** with the WebFetch tool. Quoted sentences were returned verbatim by the tool (it caps verbatim quotes at about 125 characters, so long passages are paraphrased and not put in quotes). Every `[Sn]` tag resolves to exactly one URL in the [Source Bibliography](#source-bibliography), all read 2026-10-28. Pages read only in part, or that came back with no body text, are listed as coverage limits (L-ids) in [Research Gaps](#research-gaps).

Scope boundary. Covered here: the five Quarkiverse client extensions, SSM and Secrets Manager as Quarkus config sources, the AWS Parameters and Secrets Lambda Extension (as an alternative), SQS/SNS/EventBridge-triggered handlers, and publishing limits and per-entry error checks. Referenced by name and not repeated here: handler wiring and packaging (U1, `developing-quarkus-amazon-lambda-v3-40`), HTTP (U2), DynamoDB/S3 and the general client configuration story, i.e. HTTP client, credentials and region (U4, `integrating-quarkus-amazon-data-v3-40`), testing (U6, `testing-quarkus-amazon-lambda-v3-40`), messaging architecture (`architecting-aws-sqs-messaging`, `architecting-aws-sns-pubsub`, `architecting-eventbridge-eda`), Terraform (`provisioning-aws-sqs-v6` and siblings), and Powertools batch/idempotency/parameters (`implementing-lambda-powertools-java`, mentioned only).

## Contents

- [Metadata](#metadata)
- [Executive Summary](#executive-summary)
- [Architectural Guardrails](#architectural-guardrails): [Mandatory](#-mandatory-patterns), [Conditional](#️-conditional-patterns), [Forbidden](#-forbidden-patterns)
- [Migration Guide](#migration-guide)
- [Implementation Blueprint](#implementation-blueprint)
- [Quality Control](#quality-control)
- [Production Readiness](#production-readiness)
- [Reference Implementations](#reference-implementations)
- [Source Bibliography](#source-bibliography)
- [Research Gaps](#research-gaps)
- [Research Iteration Changelog](#research-iteration-changelog)
- [Completion Checklist](#completion-checklist)
- [Agent Operation Notes](#agent-operation-notes)

---

## Metadata

```yaml
Full_Name: Quarkiverse Quarkus Amazon Services 3.23.x — quarkus-amazon-sqs, quarkus-amazon-sns, quarkus-amazon-eventbridge, quarkus-amazon-ssm, quarkus-amazon-secretsmanager — used from Quarkus 3.40 LTS AWS Lambdas (io.quarkus:quarkus-amazon-lambda 3.40.1.1)
Target_Version: io.quarkiverse.amazonservices 3.23.0 (only 3.23.x release on Maven Central at 2026-10-28) on Quarkus 3.40 LTS (patch 3.40.1.1)
Release_Date: 3.23.0 artifacts dated 2026-10-01 15:35 on Maven Central [S16]; GitHub release "3.23.0 (LTS)" "released this 01 Oct" [S10][S11]
Support_Status: "3.23.0 (LTS)" label on the GitHub releases page [S11]; built on quarkus.version 3.40.0 [S17]; Quarkus 3.40 LTS community-maintained until 2027-09-30 (family fact, https://quarkus.io/releases). A Quarkiverse-specific end-of-support date is not published (page not recorded)
Primary_Docs: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/ (amazon-sqs, amazon-sns, amazon-eventbridge, amazon-ssm, amazon-secretsmanager, common-features)
Secondary_Docs: https://quarkus.io/version/3.40/guides/aws-lambda ; AWS Lambda Developer Guide (with-sqs, services-sqs-configure, services-sqs-errorhandling, services-sqs-scaling, with-sns, with-eventbridge-scheduler, invocation-async-error-handling, with-secrets-manager, java-handler) ; SQS/SNS/EventBridge API references and quotas ; Systems Manager ps-integration-lambda-extensions
Official_Repo: https://github.com/quarkiverse/quarkus-amazon-services (docs sources read at tag 3.23.0 [S8][S9])
Registry: https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/
Research_Date: 2026-10-28
Domain_Complexity: Complex
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 6
Unverified_Count: 4
Irresolvable_Count: 2
Research_Quality_Score: 93%   # ~88 sourced claims; 4 unverified + 2 irresolvable -> (88-6)/88
Execution_Notes: >
  Caller constraints honoured: no sub-agents (P2.parallel skipped, every page fetched by this agent),
  no plan mode (scope approval relayed by the caller from PIPELINE_STATE.md#approvals, gates G1 and G2
  of 2026-10-28; recorded here as a relay, not as an approval by this agent), and the file was written
  directly instead of through research-synthesizer.
```

---

## Executive Summary

Quarkiverse **Quarkus Amazon Services** "expose AWS services through configuration properties and CDI injection" [S6]. The 3.23.x line is the one built on Quarkus 3.40: the 3.23.0 parent POM on Maven Central sets `quarkus.version` 3.40.0, `awssdk.version` 2.55.6 and `awscrt.version` 0.48.4 [S17], and the GitHub release notes list "bump quarkus.version from 3.39.2 to 3.40.0" [S10]. The only 3.23.x version on Central is **3.23.0**; the other post-3.22 versions are `4.0.0.Beta2`/`4.0.0.Beta3` (the Quarkus 4 line, out of scope under family rule 1) [S12][S13]. The five artifacts in scope are `io.quarkiverse.amazonservices:quarkus-amazon-sqs`, `quarkus-amazon-sns`, `quarkus-amazon-eventbridge`, `quarkus-amazon-ssm` and `quarkus-amazon-secretsmanager`, all managed by `quarkus-amazon-services-bom` 3.23.0, which also imports `software.amazon.awssdk:bom` [S14][S22]. Each extension injects the AWS SDK v2 sync and async clients (for example `SqsClient` / `SqsAsyncClient`), uses the URL-connection HTTP client by default for sync calls (`quarkus.<svc>.sync-client.type`, default `url`) and Netty for async calls (default `netty`) [S1][S2][S3]. There is one 3.23.x feature that matters for Lambdas: **SSM Parameter Store and Secrets Manager can be used as Quarkus config sources** (`quarkus.ssm.config.*`, `quarkus.secretsmanager.config.*`, both disabled by default). These are part of the same extensions, so no separate artifact is needed. They are documented on the 3.23.x pages and in the docs sources at tag 3.23.0 [S4][S5][S8][S9].

On the Lambda side, the handler wiring comes from U1 (`QuarkusStreamHandler`, `quarkus.lambda.handler`; family fact). Event types come from `com.amazonaws:aws-lambda-java-events`, which `io.quarkus:quarkus-amazon-lambda-common` 3.40.1.1 already depends on [S25]. AWS documents the SQS contract: messages arrive in batches through an event source mapping, delivery is at-least-once, and partial batch responses (`ReportBatchItemFailures` plus a `batchItemFailures` list of `itemIdentifier` message IDs, `SQSBatchResponse` in Java) make only the failed messages visible again [S26][S28]. AWS also says to set the visibility timeout to at least six times the function timeout, and `maxReceiveCount` to at least 5 for the DLQ redrive [S27]. SNS and EventBridge invoke Lambda asynchronously. Lambda does not support SNS FIFO topics as triggers [S40][S36][S41]. When publishing, the batch APIs report results per entry, and AWS says to "check for batch errors even when the call returns an HTTP status code of 200" (SQS `SendMessageBatch`, SNS `PublishBatch`), or to check `FailedEntryCount` and the index-aligned `Entries` (EventBridge `PutEvents`) [S31][S38][S32][S33].

The three critical patterns are as follows. (1) An SQS handler returns `SQSBatchResponse` with the failed message IDs and never throws for a single bad record, because "If your function throws an exception, the entire batch is considered a complete failure" [S26]. Handlers must also be idempotent [S28][S40]. (2) Every batch publish call checks per-entry failures, within the current limits: SQS messages up to 1 MiB with 10 per batch [S30][S31]; SNS 256 KiB by default, raisable to 1 MiB with `MaximumMessageSize` [S39][S38]; EventBridge 10 entries and less than 1 MB per `PutEvents` request on the classic bus [S32][S33]. (3) In a deployed Lambda, leave the client credentials at the default (`quarkus.<svc>.aws.credentials.type=default`), which resolves the execution role's keys that Lambda puts in the environment, and let the region come from `AWS_REGION` [S1][S52][S51]. Secrets come from Secrets Manager/SSM (family rule 5). Choosing between config source, runtime client and the AWS Parameters and Secrets Lambda Extension is an Ask-First decision. Domain complexity is **Complex**: five services, two invocation models (event source mapping vs asynchronous), secrets handling, per-entry error semantics, and an interaction with the JVM+SnapStart vs native decision (family rule 3).

---

## Architectural Guardrails

> Confidence legend: 🟢 High (versioned official page, Maven Central POM/metadata, docs source at tag 3.23.0, or the current official AWS page for an AWS service limit/behaviour, read 2026-10-28) | 🟡 Medium (inference, main-branch source, paraphrase of a code sample, or illustrative code) | 🔴 Low (community or unverified, verify before use)
> Family evidence rule (`workspace/_family_rules_v3.40.md` rule 5): one versioned official source is enough for High. AWS service documentation is published only as the current version, and the family already treats it as High (family facts rows 13, 15, 16). Triangulation badges mark claims where two independent official sources agree.

### ✅ Mandatory Patterns

**A1. Declare the extensions with the 3.23.0 coordinates and import the Quarkiverse BOM**
> Confidence: 🟢 High | [✓✓ Triangulated | Maven Central metadata/POMs [S12][S15][S22] (2026-10-28) + 3.23.x extension pages [S1][S4] (2026-10-28)]
- Why: the artifacts on Central are `io.quarkiverse.amazonservices:quarkus-amazon-{sqs,sns,eventbridge,ssm,secretsmanager}`, and 3.23.0 is the only 3.23.x version [S12][S14]. `quarkus-amazon-services-bom` 3.23.0 manages all five (`${project.version}`) and imports `software.amazon.awssdk:bom` [S22]. The extension pages name them `amazon-sqs`, `amazon-ssm`, and so on, in `-Dextensions=` [S1][S4].
- Code:
  ```xml
  <!-- Quarkiverse amazon-services 3.23.0 on Quarkus 3.40 LTS -->
  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>io.quarkiverse.amazonservices</groupId>
        <artifactId>quarkus-amazon-services-bom</artifactId>
        <version>3.23.0</version>
        <type>pom</type>
        <scope>import</scope>
      </dependency>
    </dependencies>
  </dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>io.quarkiverse.amazonservices</groupId>
      <artifactId>quarkus-amazon-sqs</artifactId>
    </dependency>
    <!-- likewise quarkus-amazon-sns, quarkus-amazon-eventbridge,
         quarkus-amazon-ssm, quarkus-amazon-secretsmanager -->
  </dependencies>
  ```
- Source: https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom (2026-10-28)

**A2. Add `url-connection-client` explicitly when you use the default sync client of SQS, SNS or EventBridge**
> Confidence: 🟢 High | [✓✓ Triangulated | SQS 3.23.x page [S1] + 3.23.0 POMs [S15][S20][S21] (2026-10-28)]
- Why: "By default the extension uses the URL connection HTTP client," "so you need to add a URL connection client dependency to the `pom.xml` file" [S1]. In the SQS, SNS and EventBridge 3.23.0 POMs, `url-connection-client` is `optional=true` [S15][S20][S21]. In the SSM and Secrets Manager 3.23.0 POMs it is a non-optional dependency [S18][S19]. Sync client types are `url` (default), `apache`, `apache5`, `aws-crt`. Async types are `netty` (default) and `aws-crt` [S1][S2][S3].
- Code:
  ```xml
  <!-- version from the software.amazon.awssdk:bom imported by the Quarkiverse BOM (medium confidence) -->
  <dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>url-connection-client</artifactId>
  </dependency>
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html (2026-10-28)

**A3. Inject the SDK client the extension produces; do not build clients by hand**
> Confidence: 🟢 High (SQS, SNS, SSM, Secrets Manager) | single versioned source each
- Why: the pages show `@Inject SqsClient sqs;` / `@Inject SqsAsyncClient sqs;` [S1], `SnsClient` / `SnsAsyncClient` [S2], `SsmClient` / `SsmAsyncClient` [S4], and `SecretsManagerClient` / `SecretsManagerAsyncClient` [S5]. The async clients return `CompletableFuture`/`CompletionStage`, which can be wrapped with `Uni.createFrom().completionStage(...)` [S1][S4]. The EventBridge page does not name the client class [S3]. The class `EventBridgeClient` comes from the AWS Java v2 PutEvents sample [S33], and injecting it is (medium confidence), see M3.
- Code:
  ```java
  // Quarkus 3.40 / amazon-services 3.23.0
  @ApplicationScoped
  public class OrderEvents {
      @Inject SqsClient sqs;   // quarkus-amazon-sqs
      @Inject SnsClient sns;   // quarkus-amazon-sns

      public String notify(String topicArn, String message) {
          // SNS page's own sync example shape [S2]
          return sns.publish(p -> p.topicArn(topicArn).message(message)).messageId();
      }
  }
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sns.html (2026-10-28, read in part, L1)

**A4. In a deployed Lambda, keep the default credentials provider (execution role) and the environment region**
> Confidence: 🟢 High | [✓✓ Triangulated | SQS 3.23.x config reference [S1] + Lambda reserved env vars [S52] + SDK region chain [S51] (2026-10-28)]
- Why: `quarkus.<svc>.aws.credentials.type` defaults to `default`. For AWS accounts the page says to remove the LocalStack-style static properties "so the default credentials chain applies" (paraphrase) [S1]. Lambda sets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, i.e. "The access keys obtained from the function's execution role", and `AWS_REGION`, "The AWS Region where the Lambda function is executed" [S52]. The SDK's default region chain checks `AWS_REGION`, with the note "The Lambda container sets this environment variable" [S51]. The full client-configuration story (HTTP client, credentials, endpoint-override) is U4's. This unit only cites it.
- Code:
  ```properties
  # application.properties — prod profile: nothing to set for credentials/region.
  # Static keys and endpoint-override only in %dev/%test (LocalStack example on the SQS page [S1])
  %dev.quarkus.sqs.endpoint-override=http://localhost:4566
  %dev.quarkus.sqs.aws.region=us-east-1
  %dev.quarkus.sqs.aws.credentials.type=static
  %dev.quarkus.sqs.aws.credentials.static-provider.access-key-id=test-key
  %dev.quarkus.sqs.aws.credentials.static-provider.secret-access-key=test-secret
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html (2026-10-28)

**A5. SQS-triggered handler: `RequestHandler<SQSEvent, SQSBatchResponse>` that collects failed message IDs**
> Confidence: 🟢 High | [✓✓ Triangulated | services-sqs-errorhandling Java sample [S26] + java-handler "use the `SQSEvent` object" [S46] (2026-10-28)]
- Why: by default "all messages in that batch become visible in the queue again" when a batch fails [S26]. With `ReportBatchItemFailures` set on the event source mapping, the function returns `batchItemFailures` with `itemIdentifier` message IDs, and only those become visible again [S26]. AWS's Java sample is `implements RequestHandler<SQSEvent, SQSBatchResponse>` with `new SQSBatchResponse.BatchItemFailure(message.getMessageId())` [S26]. In Quarkus the class is selected by CDI name through `quarkus.lambda.handler`, and the Lambda handler stays `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` (family fact; details in U1). `aws-lambda-java-events` is already on the classpath through `quarkus-amazon-lambda-common` 3.40.1.1 [S25].
- Code: see [Implementation Blueprint, step 3](#implementation-blueprint).
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html (2026-10-28)

**A6. Set the SQS visibility timeout to at least 6× the function timeout and `maxReceiveCount` to at least 5**
> Confidence: 🟢 High | single official source (services-sqs-configure) [S27]
- Why: "set the source queue's visibility timeout to at least six times the configuration timeout on your function". With a batch window, "six times your Event Function timeout, plus the value of `MaximumBatchingWindowInSeconds`". "Your function's timeout must be less than or equal to the queue's visibility timeout", and Lambda validates this when it creates the mapping. "We recommend setting the `maxReceiveCount` on your source queue's redrive policy to at least 5" [S27]. These are infrastructure values. Write them with `provisioning-aws-sqs-v6` and the Lambda provisioning skill (family rule 4), not in Quarkus config.
- Code:
  ```text
  function timeout 30 s, batch window 5 s  ->  visibility timeout >= 6*30 + 5 = 185 s
  redrive policy: maxReceiveCount >= 5 -> dead-letter queue
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html (2026-10-28)

**A7. Make every SQS-, SNS- and EventBridge-triggered handler idempotent**
> Confidence: 🟢 High | [✓✓ Triangulated | with-sqs [S28] + with-sns [S40] + invocation-async-error-handling [S42] (2026-10-28)]
- Why: "Lambda event source mappings process each event at least once, and duplicate processing of records can occur" [S28]. "Lambda asynchronous invocations process each event at least once" [S40]. "it's possible for it to receive the same event from Lambda multiple times because the queue itself is eventually consistent" [S42]. Implementation choices (DynamoDB conditional write, Powertools idempotency) belong to U4 and `implementing-lambda-powertools-java`.
- Code:
  ```java
  // key the side effect on a stable id: SQS messageId, SNS Sns.MessageId, EventBridge id
  if (!processedStore.markIfAbsent(message.getMessageId())) { return; } // already done
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html (2026-10-28)

**A8. Check per-entry results of every batch publish call, even on HTTP 200**
> Confidence: 🟢 High | [✓✓ Triangulated | SendMessageBatch [S31] + PublishBatch [S38] + PutEvents [S32][S33] (2026-10-28)]
- Why: SQS: "you should check for batch errors even when the call returns an HTTP status code of `200`". `Failed` is a list of `BatchResultErrorEntry` (`Id`, `Code`, `Message`, `SenderFault`) [S31]. SNS `PublishBatch` uses the same wording, with `Failed`/`Successful` [S38]. EventBridge: "if an individual entry within a request fails, EventBridge continues processing the rest", "You must detect unsuccessful entries and include them in a subsequent call", and "the index of the response element is the same as the index in the request array" [S33][S32].
- Code: see [Implementation Blueprint, step 5](#implementation-blueprint).
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html (2026-10-28)

**A9. Respect the documented batch and size limits before calling the API**
> Confidence: 🟢 High | one official page per limit
- Why:
  - SQS: "A single message batch request can include a maximum of 10 messages". Message size max "1,048,576 bytes (1 MiB)" [S30]. For `SendMessageBatch`, the individual message and the total payload are "both 1 MiB 1,048,576 bytes" [S31]. Up to "10 metadata attributes" [S30].
  - SNS: `PublishBatch` "Publishes up to 10 messages". Individual and total size default to "256 KiB (262,144 bytes)", and the topic's `MaximumMessageSize` "supports values up to 1 MiB" [S38]. `Publish` has the same default and maximum [S39].
  - EventBridge (classic bus): `Entries` "Minimum number of 1 item. Maximum number of 10 items" [S32]. "The total request size ... must be less than 1 MB (1,048,576 bytes)", computed from `Time` (14 bytes), `Source`, `DetailType`, `Detail` and `Resources` UTF-8 bytes. For larger events, AWS recommends uploading to S3 and sending the object URL [S33].
- Code: see [Implementation Blueprint, step 5](#implementation-blueprint) (chunking into ≤ 10).
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html (2026-10-28)

**A10. With the Secrets Manager config source in production, map each property to a named secret**
> Confidence: 🟢 High | [✓✓ Triangulated | 3.23.x page [S5] + docs source at tag 3.23.0 [S9] (2026-10-28)]
- Why: `quarkus.secretsmanager.config.secrets."<property>"=<secret-name>`. If the map is empty, "the config source will load all accessible secrets", and "Loading all secrets can be expensive and may require additional IAM permissions". The page advises explicit mappings in production [S5].
- Code:
  ```properties
  quarkus.secretsmanager.config.enabled=true
  quarkus.secretsmanager.config.secrets."stripe.api-key"=prod/stripe/api-key
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html (2026-10-28)

### ⚠️ Conditional Patterns

**Q1. Where do secrets and parameters come from at runtime?**
> Confidence: 🟢 High for each option's documented behaviour | 🟡 Medium for the Lambda-specific consequences (I1, I2, U3)
- Options: (A) Quarkiverse config source (`quarkus.ssm.config.*` / `quarkus.secretsmanager.config.*`) [S4][S5]; (B) the injected `SsmClient` / `SecretsManagerClient` called from code [S4][S5]; (C) AWS Parameters and Secrets Lambda Extension, an HTTP call to `localhost:2773` with the `X-Aws-Parameters-Secrets-Token` header [S43][S45]; (D) the Powertools parameters utility (mention only, `implementing-lambda-powertools-java`) [S45].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A config source | values available as normal `@ConfigProperty`; Secrets Manager values "loaded once at startup (the config source does not poll for updates)" [S5]; SSM reloads every `update-interval-minutes` (default 5, `0` = once) [S4] | fetch happens at startup, which adds cold-start work (unquantified, U3); behaviour of the SSM reload in a frozen Lambda environment and under SnapStart is not documented (I1, I2) | few, stable values read at boot |
  | B injected client | explicit call where needed; error handling in code | an API call per read unless you cache; you write the code | values needed per request or rarely |
  | C Lambda extension | "runtime-agnostic", "works with any Lambda runtime"; cache TTL default 300 s, size 1000 [S45]; Java sample exists [S45] | a layer to manage; HTTP call in the handler; header token must come from the credential provider chain (SnapStart) [S43] | rotated secrets needing a bounded staleness; shared cache semantics |
  | D Powertools | integrated API with transforms [S45] | extra dependency; covered by another skill | already using Powertools |

- Agent: "Ask the user how often each secret/parameter changes, whether SnapStart (JVM) or native is chosen (family rule 3), and whether a per-request read is acceptable."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html (2026-10-28)

**Q2. `quarkus.ssm.config.update-interval-minutes` inside Lambda**
> Confidence: 🟡 Medium
- Options: default `5` (periodic reload after the initial fetch) or `0` (fetch only once at startup) [S4].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | 5 (default) | picks up changes in a long-lived JVM | reload timing in a frozen execution environment is undocumented (I1); "Components that bind config only at startup may not see later changes" (paraphrase) [S4] | rarely in Lambda (medium confidence) |
  | 0 | deterministic, one fetch per cold start | changes only after a new execution environment | most Lambdas (medium confidence, inference) |

- Agent: "Ask whether runtime refresh of SSM values is a requirement; if yes, prefer option B or C of Q1."
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html (2026-10-28)

**Q3. Event input types: `aws-lambda-java-events` classes or own records?**
> Confidence: 🟢 High for `SQSEvent`/`SQSBatchResponse`; 🟡 Medium for `SNSEvent`/`ScheduledEvent` (M1)
- Options: (A) library types (`SQSEvent` [S46], `SQSBatchResponse` [S26], `SNSEvent` and `ScheduledEvent` [S48]); (B) own Java record matching the documented JSON (SNS event shape [S40], EventBridge event top-level fields `version, id, detail-type, source, account, time, region, resources, detail` [S37]).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A library types | no mapping code; AWS samples use them | `ScheduledEvent.time` is a Joda `DateTime` and `detail` a `Map<String,Object>` (main-branch source, M1) [S49]; native reflection behaviour unverified (U4); AWS warns of NPEs from the case of "Records" and "eventSourceARN" in Java object mappers [S28] | SQS (needed for `SQSBatchResponse`) |
  | B own records | typed `detail`; you control field names (`detail-type` needs a JSON name mapping) | you maintain the shape | EventBridge custom events with a known `detail` schema |

- Agent: "Ask whether EventBridge `detail` has a fixed schema; for SQS keep the library types."
- Source: https://docs.aws.amazon.com/eventbridge/latest/ref/overiew-event-structure.html (2026-10-28)

**Q4. Sync vs async client, and which HTTP implementation**
> Confidence: 🟢 High
- Options: sync `url` (default) / `apache` / `apache5` / `aws-crt`; async `netty` (default) / `aws-crt` [S1].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | sync `url` | the Quarkus 3.40 Lambda guide: "the URL Connection client must be preferred over the Apache HTTP Client when using synchronous mode" for native, and it improves startup (paraphrase) [S23] | blocking calls | default for Lambda handlers |
  | async `netty` | concurrency of many calls in one invocation | extra `netty-nio-client` dependency [S1] | fan-out publish inside one handler |
  | `aws-crt` | sync or async with one client | "Since AWS CRT version 0.31.0, native library must be embedded in the docker image" [S7]; 3.23.0 ships awscrt 0.48.4 [S17] | when already standardised on CRT |

- Agent: "Ask whether the handler issues many independent AWS calls per invocation; otherwise keep sync `url`."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

**Q5. EventBridge bus type: classic bus (rules/targets) or the new Custom Event Bus (EventsV2)**
> Confidence: 🟢 High for the quoted quotas; which bus applies is a design decision
- Options: classic custom/default bus with rules (`PutEvents` 1–10 entries [S32], up to 5 targets per rule [S36], PutEvents TPS quotas per Region [S34]); Custom Event Bus with subscribers ("Entries per PutEvents or PutRawEvents request | 1 to 100", fixed) [S34].
- Tradeoffs: the bus type changes the entry limit (10 vs 100) and the target model (rule targets vs one target per subscriber) [S34][S36]. Whether AWS SDK 2.55.6 (the 3.23.0 SDK) models the Custom Event Bus APIs was not checked (page not recorded). Architecture choice: `architecting-eventbridge-eda`.
- Agent: "Ask which bus type the target account uses before chunking PutEvents."
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-quota.html (2026-10-28)

**Q6. SNS payloads larger than 256 KiB**
> Confidence: 🟢 High
- Options: raise the topic's `MaximumMessageSize` (up to 1 MiB) [S39][S38], or offload to S3 and publish a reference (U4 covers S3).
- Agent: "Ask the expected payload size and whether every subscriber can accept up to 1 MiB."
- Source: https://docs.aws.amazon.com/sns/latest/api/API_Publish.html (2026-10-28)

**Q7. SQS: partial batch response or delete as you go**
> Confidence: 🟢 High
- Options: `ReportBatchItemFailures` plus `SQSBatchResponse` [S26], or "use the DeleteMessage API to remove messages from the queue as your Lambda Event Function successfully processes them" [S28]; Powertools batch (mention only) [S26].
- Tradeoffs: partial batch responses need no extra SQS calls, and with them "Lambda doesn't scale down message polling when function invocations fail" [S26]. `DeleteMessage` needs the queue URL and `sqs:DeleteMessage` permission (inference, medium confidence).
- Agent: "Default to partial batch responses; ask only if the ESM cannot be changed."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html (2026-10-28)

**Q8. JVM + SnapStart vs native (family rule 3) as it affects this unit**
> Confidence: 🟢 High for the AWS SnapStart token note; 🟡 Medium for the config-source impact
- AWS: Lambda doesn't set `AWS_SESSION_TOKEN` in all initialization modes; with SnapStart the function "obtains credentials from a container endpoint instead". Read the token "from the credential provider chain of an AWS SDK", and resolve it "inside the handler function, not at initialization time" [S43]. With SnapStart, config-source values fetched at init would be captured in the snapshot (inference, I2). Decide with the U1 ADR.
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html (2026-10-28)

### 🚫 Forbidden Patterns

**N1. Throwing from the SQS handler because one record failed**
> Severity: High
> Confidence: 🟢 High
- Why: "If your function throws an exception, the entire batch is considered a complete failure" [S26].
- Impact: successfully processed messages become visible again and are reprocessed.
- ❌ Wrong:
  ```java
  public Void handleRequest(SQSEvent event, Context ctx) {
      for (SQSEvent.SQSMessage m : event.getRecords()) {
          service.process(m.getBody());   // one bad body throws -> whole batch retried
      }
      return null;
  }
  ```
- ✅ Correct:
  ```java
  public SQSBatchResponse handleRequest(SQSEvent event, Context ctx) {
      List<SQSBatchResponse.BatchItemFailure> failures = new ArrayList<>();
      for (SQSEvent.SQSMessage m : event.getRecords()) {
          try { service.process(m.getBody()); }
          catch (Exception e) { failures.add(new SQSBatchResponse.BatchItemFailure(m.getMessageId())); }
      }
      return new SQSBatchResponse(failures);   // plus ReportBatchItemFailures on the ESM
  }
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html (2026-10-28)

**N2. Returning a bad `itemIdentifier`**
> Severity: High
> Confidence: 🟢 High
- Why: Lambda treats the batch as a complete failure for "An empty string `itemIdentifier`", "A null `itemIdentifier`", a bad key name, or "a message ID that doesn't exist" [S26].
- Impact: the whole batch is retried.
- ❌ Wrong: `failures.add(new SQSBatchResponse.BatchItemFailure(m.getReceiptHandle()));`
- ✅ Correct: `failures.add(new SQSBatchResponse.BatchItemFailure(m.getMessageId()));`
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html (2026-10-28)

**N3. Continuing past the first failure on a FIFO queue**
> Severity: High
> Confidence: 🟢 High
- Why: "your function should stop processing messages after the first failure and return all failed and unprocessed messages in `batchItemFailures`. This helps preserve the ordering" [S26].
- Impact: messages of the same group are processed out of order.
- ❌ Wrong:
  ```java
  for (var m : records) { try { process(m); } catch (Exception e) { failures.add(fail(m)); } } // keeps going
  ```
- ✅ Correct:
  ```java
  for (int i = 0; i < records.size(); i++) {
      try { process(records.get(i)); }
      catch (Exception e) {
          for (int j = i; j < records.size(); j++) failures.add(fail(records.get(j)));
          break;
      }
  }
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html (2026-10-28)

**N4. Treating HTTP 200 from a batch publish as "all entries succeeded"**
> Severity: High
> Confidence: 🟢 High
- Why: SQS and SNS batch calls can mix success and failure and "you should check for batch errors even when the call returns an HTTP status code of 200" [S31][S38]. PutEvents can partly succeed, and an event sent to a bus that does not exist is dropped with a `200` and is not counted in `FailedEntryCount` [S33].
- Impact: silent message loss.
- ❌ Wrong:
  ```java
  sqs.sendMessageBatch(b -> b.queueUrl(url).entries(entries));   // result ignored
  ```
- ✅ Correct:
  ```java
  var resp = sqs.sendMessageBatch(b -> b.queueUrl(url).entries(entries));
  if (!resp.failed().isEmpty()) { retryOrRaise(resp.failed()); }   // accessor name: medium confidence (M4)
  ```
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessageBatch.html (2026-10-28)

**N5. More than 10 entries in one SQS/SNS batch or classic-bus PutEvents call**
> Severity: Moderate
> Confidence: 🟢 High
- Why: SQS `TooManyEntriesInBatchRequest`, where the maximum "is 10" [S31]; SNS "more than 10" gives the same exception [S38]; PutEvents "Maximum number of 10 items" [S32].
- Impact: HTTP 400 for the whole request.
- ❌ Wrong: `sqs.sendMessageBatch(b -> b.queueUrl(url).entries(all250Entries));`
- ✅ Correct: split into chunks of ≤ 10 entries and check each response (step 5 of the blueprint).
- Source: https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html (2026-10-28)

**N6. Visibility timeout lower than the function timeout (or the 6× guidance ignored)**
> Severity: High
> Confidence: 🟢 High
- Why: Lambda rejects a mapping whose function timeout exceeds the visibility timeout. Without headroom, messages become visible while still in flight, and throttled retries have no time [S27].
- Impact: duplicate processing; event source mapping creation error.
- ❌ Wrong: `function timeout 60 s, queue visibility timeout 30 s`
- ✅ Correct: `function timeout 60 s, queue visibility timeout >= 360 s (+ MaximumBatchingWindowInSeconds)`, set in Terraform (`provisioning-aws-sqs-v6`)
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html (2026-10-28)

**N7. Static AWS keys in the production `application.properties`**
> Severity: Critical
> Confidence: 🟢 High
- Why: Lambda already provides the execution role's keys in the environment [S52], and the default credentials type is `default` [S1]. Family rule 5: secrets never in code/config.
- Impact: long-lived keys in the artifact; the role's least privilege is bypassed.
- ❌ Wrong:
  ```properties
  quarkus.sqs.aws.credentials.type=static
  quarkus.sqs.aws.credentials.static-provider.access-key-id=AKIA...
  ```
- ✅ Correct:
  ```properties
  # prod: no credentials keys (type defaults to "default" -> execution role)
  %dev.quarkus.sqs.aws.credentials.type=static
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html (2026-10-28)

**N8. Subscribing a Lambda to an SNS FIFO topic**
> Severity: Moderate
> Confidence: 🟢 High
- Why: "Lambda supports SNS triggers for standard SNS topics only. FIFO topics aren't supported" [S40].
- Impact: the subscription design cannot work.
- ❌ Wrong: `SNS FIFO topic  --lambda protocol-->  Quarkus Lambda`
- ✅ Correct: `SNS standard topic  --lambda protocol-->  Quarkus Lambda` (for ordered processing, choose a design in `architecting-aws-sns-pubsub`)
- Source: https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html (2026-10-28)

**N9. Reading `AWS_SESSION_TOKEN` at init for the Parameters and Secrets extension header**
> Severity: Moderate
> Confidence: 🟢 High
- Why: the variable is not set in every initialization mode (SnapStart uses a container credentials endpoint); resolve the token from the SDK credential provider chain inside the handler [S43]. AWS's Java sample resolves `DefaultCredentialsProvider` → `AwsSessionCredentials.sessionToken()` in `handleRequest` [S45].
- Impact: missing or stale token after a SnapStart restore; requests to `localhost:2773` rejected.
- ❌ Wrong:
  ```java
  private static final String TOKEN = System.getenv("AWS_SESSION_TOKEN"); // init time
  ```
- ✅ Correct:
  ```java
  String token = ((AwsSessionCredentials) credentialsProvider.resolveCredentials()).sessionToken(); // in handler
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html (2026-10-28)

**N10. Sync client left without its HTTP implementation, or Apache in native sync mode**
> Severity: Moderate
> Confidence: 🟢 High
- Why: the default sync type is `url` and the page says to add `url-connection-client` [S1]; in SQS/SNS/EventBridge it is optional in the POM [S15][S20][S21]. For native, "the URL Connection client must be preferred over the Apache HTTP Client when using synchronous mode" [S23].
- Impact: client creation fails at startup (missing implementation), or a heavier client in native.
- ❌ Wrong:
  ```properties
  quarkus.sqs.sync-client.type=apache   # native Lambda, sync calls
  ```
- ✅ Correct:
  ```properties
  quarkus.sqs.sync-client.type=url      # default; plus software.amazon.awssdk:url-connection-client
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda (2026-10-28)

---

## Migration Guide

> Confidence: 🟢 High | Sources: GitHub releases [S10][S11] (2026-10-28) + Maven Central [S12][S17] (2026-10-28)

**Breaking Changes (3.22.x → 3.23.0)**: none listed in the 3.23.0 release notes. The items are the Quarkus bump "from 3.39.2 to 3.40.0", the AWS SDK BOM "from 2.54.13 to 2.55.6", a docs link fix, and Maven plugin bumps [S10]. Only the Quarkus 3.40 base matters for this family.

**Deprecations seen on 3.23.x pages**: `quarkus.sns.devservices.isolated` and `quarkus.eventbridge.devservices.isolated` are marked deprecated (default `true`) [S2][S3]. The SQS page lists `isolated` (default `true`) without a deprecation note in the tool's summary (medium confidence) [S1]. Dev Services belongs to U6.

**Do not upgrade into**: `4.0.0.Beta1`–`Beta3` is the Quarkus 4 line ("feat: bump to quarkus 4"). It also makes Floci the default Dev Services stack and notes "The Apache (v4) client is deprecated in favor of `apache5`" [S11]. Family rule 1 rejects it. The `apache5` sync type already exists in 3.23.x [S1].

**Upgrade Steps**:
1. Set the Quarkus platform to 3.40.1.1 (family fact; U1).
2. Import `io.quarkiverse.amazonservices:quarkus-amazon-services-bom:3.23.0` [S22].
3. Remove versions from the `quarkus-amazon-*` dependencies (managed by the BOM) [S22].
4. Keep `software.amazon.awssdk:url-connection-client` for SQS/SNS/EventBridge sync clients [S1][S15].
5. If you previously loaded SSM/Secrets Manager values by hand at boot, consider the config sources (Q1). Both are off by default (`quarkus.ssm.config.enabled=false`, `quarkus.secretsmanager.config.enabled=false`) [S4][S5].

```bash
# Representative — adapt to your environment
mvn -q dependency:tree -Dincludes=io.quarkiverse.amazonservices
# Expected: every quarkus-amazon-* at 3.23.0 (no 4.0.0.Beta*)
```

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Quarkus | 3.40.0 | 3.40.x | `quarkus.version` 3.40.0 in the 3.23.0 parent POM [S17]; family target 3.40.1.1 |
| AWS SDK for Java v2 | 2.55.6 | 2.55.6 | `awssdk.version` in the parent POM [S17] |
| AWS CRT | 0.48.4 | 0.48.4 | `awscrt.version` [S17] |
| Java | 17 | (page not recorded) | parent POM compiles with source/target 17 [S17]; Lambda runtime choice per U1 |
| aws-lambda-java-events | (unverified) | 3.16.1 (latest on Central, 2025-07-16) | brought by `quarkus-amazon-lambda-common` 3.40.1.1 [S25][S47]; the version Quarkus 3.40.1.1 resolves is unverified (U4) |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | AWS Java sample [S26] + Quarkiverse 3.23.x pages [S1][S4][S5]]. Code samples are illustrative compositions of documented APIs; SDK v2 accessor names not shown on a fetched page are tagged (medium confidence, M4).

**Step 1. Dependencies**: A1 (BOM + extensions) and A2 (`url-connection-client`). Lambda core per U1 (`io.quarkus:quarkus-amazon-lambda`).

**Step 2. Configuration**

```properties
# Quarkus 3.40 / amazon-services 3.23.0 — application.properties
quarkus.lambda.handler=orders-queue                 # CDI name of the handler (family fact, U1)

# Secrets Manager config source (A10, Q1)
quarkus.secretsmanager.config.enabled=true
quarkus.secretsmanager.config.secrets."stripe.api-key"=prod/stripe/api-key

# SSM Parameter Store config source (Q1, Q2)
quarkus.ssm.config.enabled=true
quarkus.ssm.config.path=/myapp/prod/                # all parameters under the path (recursive=true by default)
quarkus.ssm.config.with-decryption=true             # default true: decrypts SecureString
quarkus.ssm.config.update-interval-minutes=0        # 0 = fetch once at startup (default 5) — choice per Q2
```

Documented key behaviour, with defaults stated per key (family rule 10):
- `quarkus.ssm.config.enabled`: default `false` [S4].
- `quarkus.ssm.config.path`: no default. Passed to `GetParametersByPathRequest` [S4].
- `quarkus.ssm.config.names`: no default. Full parameter names, "Batched in groups of ten per AWS limit". Can be combined with `path` [S4].
- `quarkus.ssm.config.recursive`: default `true` [S4].
- `quarkus.ssm.config.with-decryption`: default `true` [S4].
- `quarkus.ssm.config.update-interval-minutes`: default `5`. "Set to `0` to fetch only once at startup" [S4].
- If both `path` and `names` are unset, "the config source is not registered" [S4].
- SSM key mapping: "a leading `/` is removed and remaining `/` characters become `.`" (e.g. `/myapp/prod/url` → `myapp.prod.url`). JSON values are flattened to dotted keys; on reload failure "the previous snapshot (if any) is left in place" [S4].
- `quarkus.secretsmanager.config.enabled`: default `false` [S5].
- `quarkus.secretsmanager.config.secrets."<property>"`: `Map<String,String>`, no default listed [S5].
- Secrets Manager JSON secrets are detected ("value starts with `{` or `[`") and flattened. With a mapping, the mapped property name becomes the prefix [S5].
- Failed fetches (access denied, deletion, throttling) are logged, and the other secrets still load (paraphrase) [S5].
- Both config sources use "the same ... client configuration as the rest of the extension" [S4][S5], so the credentials and region rules of A4 apply.

**Step 3. SQS-triggered handler (Quarkus 3.40.1.1, `aws-lambda-java-events`)**

```java
// Quarkus 3.40.1.1 + amazon-services 3.23.0. Lambda handler (U1):
// io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest
package org.acme.orders;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SQSBatchResponse;
import com.amazonaws.services.lambda.runtime.events.SQSEvent;
import jakarta.inject.Inject;
import jakarta.inject.Named;
import java.util.ArrayList;
import java.util.List;

@Named("orders-queue")
public class OrdersQueueHandler implements RequestHandler<SQSEvent, SQSBatchResponse> {

    @Inject
    OrderService service;   // idempotent on messageId (A7)

    @Override
    public SQSBatchResponse handleRequest(SQSEvent event, Context context) {
        List<SQSBatchResponse.BatchItemFailure> failures = new ArrayList<>();
        for (SQSEvent.SQSMessage message : event.getRecords()) {
            try {
                service.process(message.getMessageId(), message.getBody());
            } catch (Exception e) {
                failures.add(new SQSBatchResponse.BatchItemFailure(message.getMessageId()));
                // FIFO queue: add this and all remaining messages, then break (N3)
            }
        }
        return new SQSBatchResponse(failures);   // empty list = whole batch succeeded [S26]
    }
}
```

The event source mapping needs `FunctionResponseTypes=ReportBatchItemFailures` [S26]. Set it in Terraform, not in Quarkus (family rule 4). The SQS record fields used are `messageId`, `receiptHandle`, `body`, `attributes` (`ApproximateReceiveCount`, and on FIFO also `MessageGroupId`, `SequenceNumber`, `MessageDeduplicationId`), `messageAttributes`, `eventSourceARN` [S28]. Batch size is up to 10,000 for standard queues and 10 for FIFO. A batch size over 10 needs `MaximumBatchingWindowInSeconds` ≥ 1. The total event must fit the 6 MB synchronous invocation payload [S27].

**Step 4. SNS- and EventBridge-triggered handlers**

```java
// SNS: invoked asynchronously; record shape Records[].Sns.{MessageId, Message, MessageAttributes, TopicArn, Subject} [S40]
@Named("orders-sns")
public class OrdersSnsHandler implements RequestHandler<SNSEvent, Void> {          // SNSEvent: medium confidence (M1)
    @Override
    public Void handleRequest(SNSEvent event, Context context) {
        event.getRecords().forEach(r -> handle(r.getSNS().getMessageId(), r.getSNS().getMessage())); // accessors: medium (M1)
        return null;   // throwing triggers Lambda async retries (2 by default) [S42]
    }
}

// EventBridge: own record per Q3 option B (top-level fields from [S37])
public record OrderEvent(String version, String id,
                         @com.fasterxml.jackson.annotation.JsonProperty("detail-type") String detailType,
                         String source, String account, String time, String region,
                         java.util.List<String> resources, OrderDetail detail) {}  // Jackson mapping: medium (M8)
```

Retry layers to account for. EventBridge retries delivery to a target "for 24 hours and up to 185 times" by default, and drops the event afterwards unless a DLQ is set [S35]. Once Lambda accepts an asynchronous event, a function error is retried "two more times" by default, and throttles or system errors are retried for up to 6 hours. Use an on-failure destination or a DLQ to capture discarded events [S42]. EventBridge Scheduler also invokes Lambda asynchronously. With no payload it sends "an empty event" [S41].

**Step 5. Publishing with per-entry checks (A8, A9, N4, N5)**

```java
// SQS SendMessageBatch: <= 10 entries, <= 1 MiB total [S31]
for (List<SendMessageBatchRequestEntry> chunk : chunksOf(entries, 10)) {
    SendMessageBatchResponse resp = sqs.sendMessageBatch(b -> b.queueUrl(queueUrl).entries(chunk));
    if (!resp.failed().isEmpty()) {                       // accessor: medium confidence (M4)
        resp.failed().forEach(f -> log.errorf("SQS entry %s failed: %s %s senderFault=%s",
                f.id(), f.code(), f.message(), f.senderFault()));
    }
}

// EventBridge PutEvents (classic bus): <= 10 entries, < 1 MB total; result index == request index [S32][S33]
PutEventsResponse result = eventBridge.putEvents(r -> r.entries(chunk));
List<PutEventsResultEntry> results = result.entries();     // entries()/eventId()/errorCode(): AWS v2 sample [S33]
for (int i = 0; i < results.size(); i++) {
    if (results.get(i).errorCode() != null) { retryLater.add(chunk.get(i)); }
}
```

The entry-size calculation (`Time` = 14 bytes plus the UTF-8 bytes of `Source`, `DetailType`, `Detail`, `Resources`) is AWS's own Java helper [S33]. Run it before batching if `Detail` can be large.

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
# 1. Only 3.23.x of the Quarkiverse extensions on the classpath
mvn -q dependency:tree -Dincludes=io.quarkiverse.amazonservices
# Expected: quarkus-amazon-{sqs,sns,eventbridge,ssm,secretsmanager}:3.23.0

# 2. Sync HTTP implementation present for SQS/SNS/EventBridge
mvn -q dependency:tree -Dincludes=software.amazon.awssdk:url-connection-client
# Expected: one match

# 3. No static AWS keys outside %dev/%test
grep -nE '^quarkus\.[a-z]+\.aws\.credentials\.static-provider' src/main/resources/application.properties
# Expected: no output (exit code 1)

# 4. SQS handlers return SQSBatchResponse
grep -rn "RequestHandler<SQSEvent" src/main/java | grep -v "SQSBatchResponse"
# Expected: no output

# 5. Batch publish results are inspected
grep -rnE "sendMessageBatch|publishBatch|putEvents" src/main/java
# Expected: every call site assigns the response and reads failed()/entries()
```

**Mocking**: test depth is U6 (`testing-quarkus-amazon-lambda-v3-40`). For this unit, the handler logic can be unit-tested by building `SQSEvent`/`SQSMessage` objects and asserting the returned `batchItemFailures`. The services can be run locally through Quarkiverse Dev Services (`quarkus.<svc>.devservices.*`, provider options include `localstack`, `ministack`, `moto`, `floci` on the SNS/EventBridge pages) [S2][S3].

```java
// Illustrative unit test (JUnit per developing-quarkus-junit-v3-40; setters from aws-lambda-java-events, medium confidence M1)
SQSEvent.SQSMessage bad = new SQSEvent.SQSMessage();
bad.setMessageId("id2");
bad.setBody("not-json");
SQSEvent event = new SQSEvent();
event.setRecords(List.of(bad));
SQSBatchResponse resp = handler.handleRequest(event, null);
assertEquals("id2", resp.getBatchItemFailures().get(0).getItemIdentifier());
```

---

## Production Readiness

- **Performance**:
  - Config sources fetch at startup ("Quarkus will fetch secret values at startup") [S5], which adds init latency per cold start (unquantified, U3).
  - The sync `url` client is the Quarkus guide's recommendation for native/startup [S23].
  - The Parameters and Secrets extension caches for 300 s by default (TTL range 0–300 s, cache size 1000, port 2773, max connections 3, timeouts default 0 = none) [S43][S45].
- **Scalability**:
  - SQS standard ESM: starts with five concurrent batches, adds up to 300 concurrent invokes per minute, and reaches at most 1,250 by default [S29].
  - Maximum concurrency is settable between 2 and 1,000. Keep it at or below reserved concurrency [S29].
  - Provisioned mode: 2–200 minimum pollers (default 2), up to 10,000 maximum (default 200), not combinable with maximum concurrency, extra cost [S28].
  - FIFO concurrency is capped by the number of message group IDs or by maximum concurrency, whichever is lower [S29].
  - SQS FIFO without high throughput: 300 TPS per partition per action, or 3,000 messages/s with batching [S30].
  - EventBridge classic PutEvents TPS is regional (e.g. us-east-1 10,000/s, eu-west-1 10,000/s, other Regions 400/s by default). Targets per rule: 5 [S34].
- **Monitoring**:
  - Partial batch reporting health: `NumberOfMessagesDeleted` dropping to 0, or `ApproximateAgeOfOldestMessage` rising sharply [S26].
  - Provisioned pollers: `ProvisionedPollers` [S28].
  - Extension logs: set `PARAMETERS_SECRETS_EXTENSION_LOG_LEVEL=DEBUG` while setting up [S43].
  - Log `messageId`/`requestId`, never message bodies with PII (family rule 7).
- **Security**:
  - Execution role permissions: `AWSLambdaSQSQueueExecutionRole` for the SQS trigger, plus `kms:Decrypt` for encrypted queues [S27].
  - Extension reads: `ssm:GetParameter` and `kms:Decrypt` for `SecureString` [S43]; `secretsmanager:GetSecretValue` [S45].
  - Explicit secret mappings rather than "load all accessible secrets" [S5].
  - EventBridge does not support SQS targets or target DLQs encrypted with an AWS owned key [S36].
  - In a VPC, Secrets Manager needs a VPC endpoint for the extension [S44].
  - Secrets come from Secrets Manager/SSM, never from env vars or properties (family rule 5). AWS also recommends Secrets Manager over environment variables [S52].

---

## Reference Implementations

- AWS Java sample for partial batch responses (`ProcessSQSMessageBatch`) on https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html. It links the Serverless examples repo `aws-samples/serverless-snippets/lambda-function-sqs-report-batch-item-failures` (not read).
- AWS Java v2 PutEvents sample and failure-retry loop: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html (the retry loop is written in SDK v1 style; port it to v2 accessors).
- AWS Java sample for the Parameters and Secrets extension (`example.Hello`): https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html
- Quarkiverse 3.23.x extension guides (SQS, SNS, EventBridge, SSM, Secrets Manager): https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/
- Event classes: https://github.com/aws/aws-lambda-java-libs/tree/main/aws-lambda-java-events (main branch, medium confidence).

---

## Source Bibliography

**Primary — Quarkiverse 3.23.x (versioned), all read 2026-10-28**
- [S1] https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html
- [S2] https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sns.html (read 0–100,000 of 106,342 characters, L1)
- [S3] https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-eventbridge.html
- [S4] https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html
- [S5] https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html
- [S6] https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/index.html
- [S7] https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html
- [S8] https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/docs/modules/ROOT/pages/amazon-ssm.adoc (docs source at tag 3.23.0)
- [S9] https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/docs/modules/ROOT/pages/amazon-secretsmanager.adoc (docs source at tag 3.23.0)
- [S10] https://github.com/quarkiverse/quarkus-amazon-services/releases/tag/3.23.0
- [S11] https://github.com/quarkiverse/quarkus-amazon-services/releases

**Primary — Maven Central, all read 2026-10-28**
- [S12] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sqs/maven-metadata.xml (latest 4.0.0.Beta3; lastUpdated 20261017211442)
- [S13] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-secretsmanager/maven-metadata.xml
- [S14] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/
- [S15] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sqs/3.23.0/quarkus-amazon-sqs-3.23.0.pom
- [S16] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sqs/3.23.0/ (files dated 2026-10-01 15:35)
- [S17] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom
- [S18] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-ssm/3.23.0/quarkus-amazon-ssm-3.23.0.pom
- [S19] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-secretsmanager/3.23.0/quarkus-amazon-secretsmanager-3.23.0.pom
- [S20] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-eventbridge/3.23.0/quarkus-amazon-eventbridge-3.23.0.pom
- [S21] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sns/3.23.0/quarkus-amazon-sns-3.23.0.pom
- [S22] https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom
- [S24] https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda/3.40.1.1/quarkus-amazon-lambda-3.40.1.1.pom
- [S25] https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-common/3.40.1.1/quarkus-amazon-lambda-common-3.40.1.1.pom
- [S47] https://repo1.maven.org/maven2/com/amazonaws/aws-lambda-java-events/maven-metadata.xml (latest 3.16.1; lastUpdated 20250716120355; older than 12 months but the current stable, so not rejected)

**Primary — Quarkus 3.40 (versioned), read 2026-10-28**
- [S23] https://quarkus.io/version/3.40/guides/aws-lambda (read in full per the tool)

**Primary — AWS official documentation (current), all read 2026-10-28**
- [S26] https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html
- [S27] https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html
- [S28] https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
- [S29] https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html
- [S30] https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html
- [S31] https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessageBatch.html
- [S32] https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_PutEvents.html
- [S33] https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html
- [S34] https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-quota.html
- [S35] https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html
- [S36] https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-targets.html
- [S37] https://docs.aws.amazon.com/eventbridge/latest/ref/overiew-event-structure.html
- [S38] https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html
- [S39] https://docs.aws.amazon.com/sns/latest/api/API_Publish.html
- [S40] https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html
- [S41] https://docs.aws.amazon.com/lambda/latest/dg/with-eventbridge-scheduler.html
- [S42] https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html
- [S43] https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html (extension ARN tables "Last updated: October 21, 2026")
- [S44] https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html
- [S45] https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html
- [S46] https://docs.aws.amazon.com/lambda/latest/dg/java-handler.html
- [S51] https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/region-selection.html
- [S52] https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html

**Validation — official repository, main branch (at most medium per family rule 5), read 2026-10-28**
- [S48] https://github.com/aws/aws-lambda-java-libs/blob/main/aws-lambda-java-events/README.md
- [S49] https://github.com/aws/aws-lambda-java-libs/blob/main/aws-lambda-java-events/src/main/java/com/amazonaws/services/lambda/runtime/events/ScheduledEvent.java
- [S50] https://github.com/aws/aws-lambda-java-libs/blob/main/aws-lambda-java-events/src/main/java/com/amazonaws/services/lambda/runtime/events/SQSBatchResponse.java

**Fetched with no usable body / not found (not cited for claims)**
- https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevent-size.html (title only; content taken from [S33] anchor `eb-putevent-size`)
- https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-events-structure.html (title only; content taken from [S37])
- https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars-runtime.html (title only; content taken from [S52] anchor `configuration-envvars-runtime`)
- https://github.com/quarkiverse/quarkus-amazon-services/tree/3.23.0/ssm/runtime and `.../ssm/runtime/src/main/java/io/quarkus/amazon/ssm/runtime` (HTTP 404)

(IDs S23–S25 and S47–S52 are numbered out of order because they were added during the gap loop. No ID is reused.)

---

## Research Gaps

> Every gap that survives all gap-loop iterations also appears as an IRRESOLVABLE row in the Research Iteration Changelog.

Unverified (U-ids):

```
U1 (unused id — intentionally skipped so that U-ids match the Metadata count of 4: U3..U6)
```

```
Gap: U3 — cold-start latency added by the SSM / Secrets Manager config sources
Impact: init duration and SnapStart snapshot content unknown
Workaround: measure Init Duration in CloudWatch with and without the config sources
Follow-up: Quarkiverse 3.23.x pages (no figure published)
§7-ref: Iteration 3 — unverified (not quantifiable from documentation)
```

```
Gap: U4 — aws-lambda-java-events version resolved by Quarkus 3.40.1.1, and native-image reflection for SQSEvent/SQSBatchResponse/ScheduledEvent (Joda DateTime)
Impact: native build or runtime deserialization surprises
Workaround: run `mvn dependency:tree -Dincludes=com.amazonaws` and a native integration test (U6)
Follow-up: io.quarkus:quarkus-bom 3.40.1.1 POM; extensions/amazon-lambda at tag 3.40.1.1
§7-ref: Iteration 3 — unverified (page not recorded)
```

```
Gap: U5 — whether Quarkus' Jackson-based event mapping avoids the AWS-documented NPE on "Records"/"eventSourceARN" case
Impact: empty or null records in SQS handlers
Workaround: unit-test the handler with the AWS sample event JSON [S28] through the mock event server (U6)
Follow-up: Quarkus source at tag 3.40.1.1 (amazon-lambda common runtime)
§7-ref: Iteration 3 — unverified
```

```
Gap: U6 — whether AWS SDK 2.55.6 (3.23.0) models the EventBridge Custom Event Bus (EventsV2) PutEvents with 100 entries
Impact: chunk size for PutEvents on V2 buses
Workaround: chunk at 10 (classic API reference) until verified
Follow-up: AWS SDK for Java v2 changelog / EventBridge API reference for V2
§7-ref: Iteration 3 — unverified
```

Irresolvable (I-ids):

```
Gap: I1 — runtime behaviour of the SSM config-source scheduled reload (update-interval-minutes > 0) inside a Lambda execution environment that is frozen between invocations
Impact: values may not refresh as expected, or a reload may run during an invocation
Workaround: set update-interval-minutes=0 (Q2) or read at runtime (Q1 option B/C)
Follow-up: Quarkiverse SSM config-source source code (GitHub tree at tag 3.23.0 returned 404)
§7-ref: Iteration 3 — IRRESOLVABLE
```

```
Gap: I2 — config-source values under SnapStart (captured in the snapshot at init; refresh after restore not documented)
Impact: stale secrets after rotation for the life of the snapshot
Workaround: for rotated secrets use Q1 option C with a short TTL, or option B in the handler
Follow-up: Quarkus 3.40 SnapStart guide + Quarkiverse docs (neither states it)
§7-ref: Iteration 3 — IRRESOLVABLE
```

Medium-confidence items (M-ids):
- M1 `SNSEvent`, `ScheduledEvent` class names (README) and `ScheduledEvent` field types (`time` Joda `DateTime`, `detail` `Map<String,Object>`), plus the event setters/getters used in samples. Main-branch source [S48][S49].
- M2 `SQSBatchResponse` Lombok annotations and builder (main-branch source) [S50]. The constructor usage is High from [S26].
- M3 `@Inject EventBridgeClient` with `quarkus-amazon-eventbridge`. The page does not name the class [S3]. The class name is from the AWS v2 sample [S33].
- M4 SDK v2 accessor names not on a fetched page: `SendMessageBatchResponse.failed()`, `BatchResultErrorEntry.id()/code()/message()/senderFault()`, `PutEventsResponse.failedEntryCount()`.
- M5 `url-connection-client` version supplied by the `software.amazon.awssdk:bom` the Quarkiverse BOM imports [S22].
- M6 Recommending `update-interval-minutes=0` for Lambda (inference from [S4]).
- M7 The Quarkus 3.40 guide's `quarkus-jaxb` instruction applies to manual SDK wiring. Paraphrased by the tool [S23]; its relevance to Quarkiverse extensions is not stated.
- M8 Quarkus Lambda deserializes events with Jackson (inferred from the `quarkus-jackson` dependency of `quarkus-amazon-lambda-common` [S25]); `@JsonProperty("detail-type")` mapping.
- M9 `DeleteMessage` alternative needs `sqs:DeleteMessage` and the queue URL (inference).
- M10 SQS page `devservices.isolated` without a deprecation note (tool summary) [S1].

Coverage limits (L-ids):
- L1 SNS 3.23.x page read 0–100,000 of 106,342 characters [S2].
- L2 Quarkiverse pages and the Quarkus guide were returned by the tool as summaries with ≤ 125-character quotes. Long config tables (SQS: first 40 rows) were not read in full.
- L3 Three AWS pages returned title-only bodies (listed in the bibliography); their content was taken from sibling pages.
- L4 The Quarkiverse runtime source at tag 3.23.0 was not inspected (GitHub tree 404). Config-source facts rest on the versioned page and the docs source at the tag.

Contradictions and corrections for the caller:
- C1 The brief says SQS "SendMessage/SendMessageBatch limits (256 KB, batch 10)". The current AWS pages state a maximum message size of "1,048,576 bytes (1 MiB)", with the batch total also 1 MiB [S30][S31]. The batch limit of 10 is confirmed. This document uses 1 MiB.
- C2 PutEvents entries: the API reference gives 1–10 [S32] and eb-putevents "up to 10" [S33], while eb-quota lists "Entries per PutEvents or PutRawEvents request | 1 to 100" for the new Custom Event Bus [S34]. These are different bus types (Q5, U6).
- C3 Family fact row 17 ("3.23.0 (LTS) is the line built on Quarkus 3.40.0", Medium, inferred from the changelog, https://github.com/quarkiverse/quarkus-amazon-services/releases) is now confirmed by the Central parent POM `quarkus.version` 3.40.0 (https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom). The orchestrator may raise it to High. The family file was not edited.
- C4 (informational) The Quarkus 3.40 Lambda guide says "Quarkus now has extensions for DynamoDB, S3, SNS and SQS (more coming)" [S23], while the 3.23.x index lists 45 services [S6]. It is stale wording, not a conflict with any family fact.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Executive Summary / Metadata | Quarkus base of 3.23.0 (family fact 17 was Medium) | Resolved: `quarkus.version` 3.40.0 in parent POM (C3) | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom (2026-10-28) |
| 1 | Q1 / Step 2 | Are the SSM/Secrets Manager config sources in 3.23.x or only 4.0.0.Beta1 (Beta1 notes mention "add integration tests for ssm config source")? | Resolved: present in docs source at tag 3.23.0 | https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/docs/modules/ROOT/pages/amazon-ssm.adoc ; …/amazon-secretsmanager.adoc (2026-10-28) |
| 1 | A9 | EventBridge entry size (eb-putevent-size page empty) | Resolved via eb-putevents anchor | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html (2026-10-28) |
| 2 | Q3 / Step 4 | EventBridge event top-level fields (eb-events-structure page empty) | Resolved | https://docs.aws.amazon.com/eventbridge/latest/ref/overiew-event-structure.html (2026-10-28) |
| 2 | A4 | Lambda reserved credentials/region env vars (runtime page empty) | Resolved | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html (2026-10-28) |
| 2 | A1 / A2 | BOM coverage and url-connection-client management | Resolved (BOM manages the 5 artifacts, imports AWS SDK BOM); url-connection-client version via AWS BOM stays M5 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom (2026-10-28) |
| 3 | Q2 | SSM reload in frozen Lambda environment (I1) | ⚠️ IRRESOLVABLE — no page states it; runtime source tree at tag returned 404 | — |
| 3 | Q8 | Config-source values under SnapStart (I2) | ⚠️ IRRESOLVABLE — neither Quarkiverse nor Quarkus docs state it | — |
| 3 | Production Readiness | Config-source cold-start cost (U3) | Left unverified — no published figure | — |
| 3 | Compatibility Matrix | aws-lambda-java-events version in Quarkus 3.40.1.1 + native reflection (U4) | Left unverified — page not recorded within the iteration budget | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (artifacts, injection, shared config, config sources, Lambda extension, SQS/SNS/EventBridge handlers, publishing limits, per-entry checks)
- [x] Pattern counts driven by domain needs (10 ✅, 8 ⚠️, 10 🚫)
- [x] Every anti-pattern has an alternative; each ✅ alternative is High (family rule 9)
- [x] All CLI commands marked as representative
- [x] Integration examples complete (SQS handler, SNS/EventBridge handlers, batch publish)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example (SQS handler, step 3)
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated where two sources exist; single-source High kept per family evidence rule 5
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in the changelog

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1–A10 and N1–N10. These are the 3.23.0 coordinates, the default client types, the config-source keys and defaults, the SQS partial-batch contract, the visibility-timeout/redrive guidance, the batch limits and the per-entry checks.
- **Medium Confidence (validate with user)**: M1–M10. Mainly the `SNSEvent`/`ScheduledEvent` details, the `EventBridgeClient` injection and the SDK v2 accessor names. Also Q1–Q8 decisions.
- **Low Confidence (must ask human)**: U3–U6 and I1–I2. Config-source behaviour in Lambda/SnapStart, cold-start cost, events-library version/native reflection, Custom Event Bus support in SDK 2.55.6.
- **Edge Cases (pause)**: Quarkiverse 3.23.0 was released 2026-10-01 (27 days before this research); docs are complete for the scope but the line is young. Any request for 4.0.0.Beta* content is out of scope (family rule 1).
- **Emergency Stop**: not triggered (official sources exist for every scope item).
- **Version lock**: everything here is for Quarkiverse amazon-services 3.23.0 on Quarkus 3.40 LTS (3.40.1.1) and AWS SDK for Java v2 2.55.6. Re-research on any other version line.
