# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkiverse amazon-services 3.23.0 on Quarkus 3.40. Fetched 2026-10-28. Method bodies are illustrative compositions of documented APIs; tags on a line map to the [register](./unverified-and-risks.md#tag-to-register-mapping). Research ids A1 to A10 are kept in the headings.

## Contents

- [A1. Coordinates and BOM](#a1-coordinates-and-bom)
- [A2. Explicit url-connection-client](#a2-explicit-url-connection-client)
- [A3. Inject the SDK client](#a3-inject-the-sdk-client)
- [A4. Default credentials and region](#a4-default-credentials-and-region)
- [A5. SQS handler returns SQSBatchResponse](#a5-sqs-handler-returns-sqsbatchresponse)
- [A6. Visibility timeout and redrive](#a6-visibility-timeout-and-redrive)
- [A7. Idempotent handlers](#a7-idempotent-handlers)
- [A8. Per-entry result checks](#a8-per-entry-result-checks)
- [A9. Batch and size limits](#a9-batch-and-size-limits)
- [A10. Explicit secret mappings](#a10-explicit-secret-mappings)

## A1. Coordinates and BOM

The artifacts on Central are `io.quarkiverse.amazonservices:quarkus-amazon-{sqs,sns,eventbridge,ssm,secretsmanager}`; 3.23.0 is the only 3.23.x version. `quarkus-amazon-services-bom` 3.23.0 manages all five and imports `software.amazon.awssdk:bom` ([BOM POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom), [Central index](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/)). Running 3.23.0 on Quarkus patch 3.40.1.1 is not stated on a page (medium confidence).

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

## A2. Explicit url-connection-client

The SQS page says "By default the extension uses the URL connection HTTP client," "so you need to add a URL connection client dependency to the `pom.xml` file". In the SQS, SNS and EventBridge 3.23.0 POMs the artifact is `optional=true`. In the SSM and Secrets Manager 3.23.0 POMs it is a non-optional dependency ([SQS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html), [SQS POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sqs/3.23.0/quarkus-amazon-sqs-3.23.0.pom), [SNS POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-sns/3.23.0/quarkus-amazon-sns-3.23.0.pom), [EventBridge POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-eventbridge/3.23.0/quarkus-amazon-eventbridge-3.23.0.pom), [SSM POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-ssm/3.23.0/quarkus-amazon-ssm-3.23.0.pom)).

```xml
<!-- version comes from the software.amazon.awssdk:bom imported by the Quarkiverse BOM (medium confidence) -->
<dependency>
  <groupId>software.amazon.awssdk</groupId>
  <artifactId>url-connection-client</artifactId>
</dependency>
```

Any other HTTP client is an Ask First decision: [Q4](./ask-first-decisions.md#q4-sync-or-async-client-and-http-implementation).

## A3. Inject the SDK client

The pages show `@Inject SqsClient` / `SqsAsyncClient` ([SQS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html)), `SnsClient` / `SnsAsyncClient` ([SNS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sns.html)), `SsmClient` ([SSM page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html)) and `SecretsManagerClient` ([Secrets Manager page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html)). The async clients return `CompletableFuture`, which can be wrapped with `Uni.createFrom().completionStage(...)`. The EventBridge page does not name the client class; injecting `EventBridgeClient` is (medium confidence), see [publishing](./publishing-and-limits.md#eventbridge-putevents).

```java
// Quarkus 3.40 / amazon-services 3.23.0 (body illustrative, medium confidence)
@ApplicationScoped
public class OrderEvents {
    @Inject SqsClient sqs;
    @Inject SnsClient sns;

    public String notify(String topicArn, String message) {
        return sns.publish(p -> p.topicArn(topicArn).message(message)).messageId(); // shape from the SNS page
    }
}
```

## A4. Default credentials and region

`quarkus.<svc>.aws.credentials.type` defaults to `default`, and the page tells AWS-account users to drop the LocalStack-style static properties so the default chain applies. Lambda sets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN` from the execution role and `AWS_REGION` for the region; the SDK region chain checks `AWS_REGION`. That the Quarkiverse client picks the region up from `AWS_REGION` is (medium confidence): the Quarkiverse region list omits `AWS_REGION` and delegation to the SDK chain is not stated; the decision (leave unset, or set explicitly or smoke-test) is the data skill's [Ask First C3](../../integrating-quarkus-amazon-data-v3-40/blueprints/ask-first-decisions.md#c3-region) ([SQS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html), [Lambda env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html), [region selection](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/region-selection.html)). The wider client configuration story is the [data skill](../../integrating-quarkus-amazon-data-v3-40/SKILL.md).

```properties
# application.properties: nothing to set for credentials or region in prod.
# Static keys and endpoint-override only under %dev / %test (LocalStack example on the SQS page)
%dev.quarkus.sqs.endpoint-override=http://localhost:4566
%dev.quarkus.sqs.aws.region=us-east-1
%dev.quarkus.sqs.aws.credentials.type=static
%dev.quarkus.sqs.aws.credentials.static-provider.access-key-id=test-key
%dev.quarkus.sqs.aws.credentials.static-provider.secret-access-key=test-secret
```

## A5. SQS handler returns SQSBatchResponse

By default "all messages in that batch become visible in the queue again" when a batch fails. With `ReportBatchItemFailures` on the event source mapping, the function returns `batchItemFailures` with `itemIdentifier` message IDs and only those become visible again. AWS's Java sample is `implements RequestHandler<SQSEvent, SQSBatchResponse>` with `new SQSBatchResponse.BatchItemFailure(message.getMessageId())` ([AWS error handling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html), [java-handler](https://docs.aws.amazon.com/lambda/latest/dg/java-handler.html)). Full handler and mapping: [sqs-handler](./sqs-handler.md). Handler wiring (`QuarkusStreamHandler`, `quarkus.lambda.handler`) is the [lambda skill](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md).

```java
return new SQSBatchResponse(failures);   // empty list = whole batch succeeded
```

## A6. Visibility timeout and redrive

AWS: "set the source queue's visibility timeout to at least six times the configuration timeout on your function"; with a batch window, six times the timeout "plus the value of `MaximumBatchingWindowInSeconds`". "Your function's timeout must be less than or equal to the queue's visibility timeout", and Lambda validates this when it creates the mapping. "We recommend setting the `maxReceiveCount` on your source queue's redrive policy to at least 5" ([AWS configure](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)). These are infrastructure values: write them with `provisioning-aws-sqs-v6` and the Lambda provisioning skill, never in Quarkus config and never SAM or CDK (family rule 4).

```text
function timeout 30 s, batch window 5 s  ->  visibility timeout >= 6*30 + 5 = 185 s
redrive policy: maxReceiveCount >= 5 -> dead-letter queue
```

## A7. Idempotent handlers

"Lambda event source mappings process each event at least once, and duplicate processing of records can occur" (SQS); "Lambda asynchronous invocations process each event at least once" (SNS); the Lambda async-invocation page says "it's possible for it to receive the same event from Lambda multiple times because the queue itself is eventually consistent" ([AWS SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html), [AWS SNS](https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html), [async errors](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html)). Choose the stable key per source: SQS `messageId`, SNS `Sns.MessageId`, EventBridge `id`. The store (DynamoDB conditional write) is the [data skill](../../integrating-quarkus-amazon-data-v3-40/SKILL.md); Powertools idempotency is `implementing-lambda-powertools-java`.

```java
// body illustrative (medium confidence); processedStore is yours
if (!processedStore.markIfAbsent(message.getMessageId())) { return; } // already done
```

## A8. Per-entry result checks

SQS: "you should check for batch errors even when the call returns an HTTP status code of `200`"; `Failed` is a list of `BatchResultErrorEntry` (`Id`, `Code`, `Message`, `SenderFault`). SNS `PublishBatch` uses the same wording with `Failed` and `Successful`. EventBridge: "if an individual entry within a request fails, EventBridge continues processing the rest", "You must detect unsuccessful entries and include them in a subsequent call", and "the index of the response element is the same as the index in the request array" ([SQS API](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessageBatch.html), [SNS API](https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html), [PutEvents](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html), [PutEvents API](https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_PutEvents.html)). Code: [publishing](./publishing-and-limits.md).

## A9. Batch and size limits

SQS: "A single message batch request can include a maximum of 10 messages"; message size at most "1,048,576 bytes (1 MiB)"; for `SendMessageBatch` the individual message and the total payload are both 1 MiB; up to 10 metadata attributes. SNS: `PublishBatch` "Publishes up to 10 messages"; individual and total size default to "256 KiB (262,144 bytes)", and the topic's `MaximumMessageSize` "supports values up to 1 MiB" ([SQS quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html), [SQS API](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessageBatch.html), [SNS PublishBatch](https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html), [SNS Publish](https://docs.aws.amazon.com/sns/latest/api/API_Publish.html)). EventBridge entry limits depend on the bus type: [Q5](./ask-first-decisions.md#q5-eventbridge-bus-type-and-putevents-chunk-size). The 256 KiB figure for SQS is outdated (research C1).

## A10. Explicit secret mappings

`quarkus.secretsmanager.config.secrets."<property>"=<secret-name>`. If the map is empty, "the config source will load all accessible secrets", and "Loading all secrets can be expensive and may require additional IAM permissions" ([Secrets Manager page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html), [docs source at tag 3.23.0](https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/docs/modules/ROOT/pages/amazon-secretsmanager.adoc)). Secrets come from Secrets Manager or SSM, never from code or config files (family rule 5). Provision them with `provisioning-aws-secrets-manager-v6` or `provisioning-aws-parameter-store-v6`.

```properties
quarkus.secretsmanager.config.enabled=true
quarkus.secretsmanager.config.secrets."stripe.api-key"=prod/stripe/api-key
```
