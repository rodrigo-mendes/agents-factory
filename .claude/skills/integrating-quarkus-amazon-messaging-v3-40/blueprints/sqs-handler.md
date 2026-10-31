# SQS-Triggered Handler

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1, `aws-lambda-java-events`. Fetched 2026-10-28. Wiring of the handler (`quarkus.lambda.handler`, `QuarkusStreamHandler::handleRequest`) is the [lambda skill](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md).

## Handler

`aws-lambda-java-events` is already on the classpath through `quarkus-amazon-lambda-common` 3.40.1.1 ([POM](https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-common/3.40.1.1/quarkus-amazon-lambda-common-3.40.1.1.pom)). This skill follows the AWS Java samples ([AWS error handling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html), [java-handler](https://docs.aws.amazon.com/lambda/latest/dg/java-handler.html)).

```java
// Quarkus 3.40.1.1 + amazon-services 3.23.0 (body illustrative, medium confidence)
// Lambda handler setting (lambda skill): io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest
package org.acme.orders;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SQSBatchResponse;
import com.amazonaws.services.lambda.runtime.events.SQSEvent;
import jakarta.inject.Inject;
import jakarta.inject.Named;
import java.util.ArrayList;
import java.util.List;

@Named("orders-queue")                  // quarkus.lambda.handler=orders-queue
public class OrdersQueueHandler implements RequestHandler<SQSEvent, SQSBatchResponse> {

    @Inject
    OrderService service;               // idempotent on messageId (A7)

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
        return new SQSBatchResponse(failures);   // empty list = whole batch succeeded
    }
}
```

The constructor usage is from the AWS sample. The Lombok annotations and builder of `SQSBatchResponse` come from main-branch source (medium confidence).

Whether Quarkus' Jackson-based event mapping avoids the NPE AWS documents for the case of `Records` and `eventSourceARN` in Java object mappers is (unverified). Test the handler with the AWS sample event JSON through the mock event server ([testing skill](../../testing-quarkus-amazon-lambda-v3-40/SKILL.md)).

## Event source mapping (infrastructure, not Quarkus)

Set it with Terraform (`provisioning-aws-sqs-v6` plus the Lambda provisioning skill), never SAM or CDK:

- `FunctionResponseTypes=ReportBatchItemFailures` is required for partial batch responses ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)).
- Visibility timeout at least 6 times the function timeout (plus the batch window), `maxReceiveCount` at least 5 ([AWS configure](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)).
- Batch size is up to 10,000 for standard queues and 10 for FIFO. A batch size over 10 needs `MaximumBatchingWindowInSeconds` of at least 1. The event must fit the 6 MB synchronous invocation payload ([AWS configure](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)).
- Execution role: `AWSLambdaSQSQueueExecutionRole`, plus `kms:Decrypt` for encrypted queues ([AWS configure](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)).

## Record fields

The record fields used are `messageId`, `receiptHandle`, `body`, `attributes` (`ApproximateReceiveCount`, and on FIFO also `MessageGroupId`, `SequenceNumber`, `MessageDeduplicationId`), `messageAttributes` and `eventSourceARN` ([AWS SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)). AWS warns that the case of `Records` and `eventSourceARN` can cause NPEs in Java object mappers.

## Scaling

- Standard queue mapping: starts with five concurrent batches, adds up to 300 concurrent invokes per minute, reaches at most 1,250 by default. Maximum concurrency is settable between 2 and 1,000; keep it at or below reserved concurrency ([AWS scaling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html)).
- Provisioned mode: 2 to 200 minimum pollers (default 2), up to 10,000 maximum (default 200), not combinable with maximum concurrency, extra cost ([AWS SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)).
- FIFO concurrency is capped by the number of message group IDs or by maximum concurrency, whichever is lower ([AWS scaling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html)).
- SQS FIFO without high throughput: 300 TPS per partition per action, or 3,000 messages per second with batching ([SQS quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html)).

## Monitoring

- Partial batch health: `NumberOfMessagesDeleted` dropping to 0, or `ApproximateAgeOfOldestMessage` rising sharply ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)).
- Provisioned pollers: `ProvisionedPollers` ([AWS SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)).
- Log `messageId` and `requestId`, never message bodies with PII (family rule 7).
- With partial batch responses "Lambda doesn't scale down message polling when function invocations fail" ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)).
