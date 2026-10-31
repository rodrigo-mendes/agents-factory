# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkiverse amazon-services 3.23.0 on Quarkus 3.40. Fetched 2026-10-28. Severity wording: low, moderate, high (research N1 to N10).

## Contents

- [N1. Throwing from the SQS handler for one bad record](#n1-throwing-from-the-sqs-handler-for-one-bad-record)
- [N2. Returning a bad itemIdentifier](#n2-returning-a-bad-itemidentifier)
- [N3. Continuing past the first failure on a FIFO queue](#n3-continuing-past-the-first-failure-on-a-fifo-queue)
- [N4. Treating HTTP 200 from a batch publish as success](#n4-treating-http-200-from-a-batch-publish-as-success)
- [N5. More than 10 entries in one call](#n5-more-than-10-entries-in-one-call)
- [N6. Visibility timeout below the function timeout](#n6-visibility-timeout-below-the-function-timeout)
- [N7. Static AWS keys in production config](#n7-static-aws-keys-in-production-config)
- [N8. Lambda on an SNS FIFO topic](#n8-lambda-on-an-sns-fifo-topic)
- [N9. AWS_SESSION_TOKEN read at init](#n9-aws_session_token-read-at-init)
- [N10. Apache sync client in a native Lambda](#n10-apache-sync-client-in-a-native-lambda)

## N1. Throwing from the SQS handler for one bad record

Severity: high. "If your function throws an exception, the entire batch is considered a complete failure" ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)). Impact: successfully processed messages become visible again and are reprocessed.

```java
// ❌ WRONG
public Void handleRequest(SQSEvent event, Context ctx) {
    for (SQSEvent.SQSMessage m : event.getRecords()) {
        service.process(m.getBody());   // one bad body throws -> whole batch retried
    }
    return null;
}
```

```java
// ✅ CORRECT (plus ReportBatchItemFailures on the event source mapping)
public SQSBatchResponse handleRequest(SQSEvent event, Context ctx) {
    List<SQSBatchResponse.BatchItemFailure> failures = new ArrayList<>();
    for (SQSEvent.SQSMessage m : event.getRecords()) {
        try { service.process(m.getBody()); }
        catch (Exception e) { failures.add(new SQSBatchResponse.BatchItemFailure(m.getMessageId())); }
    }
    return new SQSBatchResponse(failures);
}
```

## N2. Returning a bad itemIdentifier

Severity: high. Lambda treats the batch as a complete failure for "An empty string `itemIdentifier`", "A null `itemIdentifier`", a bad key name, or "a message ID that doesn't exist" ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)). Impact: the whole batch is retried.

```java
// ❌ WRONG
failures.add(new SQSBatchResponse.BatchItemFailure(m.getReceiptHandle()));
// ✅ CORRECT
failures.add(new SQSBatchResponse.BatchItemFailure(m.getMessageId()));
```

## N3. Continuing past the first failure on a FIFO queue

Severity: high. "your function should stop processing messages after the first failure and return all failed and unprocessed messages in `batchItemFailures`. This helps preserve the ordering" ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)). Impact: messages of the same group are processed out of order.

```java
// ❌ WRONG
for (var m : records) { try { process(m); } catch (Exception e) { failures.add(fail(m)); } } // keeps going
```

```java
// ✅ CORRECT
for (int i = 0; i < records.size(); i++) {
    try { process(records.get(i)); }
    catch (Exception e) {
        for (int j = i; j < records.size(); j++) failures.add(fail(records.get(j)));
        break;
    }
}
```

## N4. Treating HTTP 200 from a batch publish as success

Severity: high. SQS and SNS batch calls can mix success and failure, and "you should check for batch errors even when the call returns an HTTP status code of `200`". `PutEvents` can partly succeed, and an event sent to a bus that does not exist is dropped with a `200` and is not counted in `FailedEntryCount` ([SQS API](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessageBatch.html), [SNS API](https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html), [PutEvents](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html)). Impact: silent message loss.

```java
// ❌ WRONG
sqs.sendMessageBatch(b -> b.queueUrl(url).entries(entries));   // result ignored
```

```java
// ✅ CORRECT (accessor failed() is (medium confidence))
var resp = sqs.sendMessageBatch(b -> b.queueUrl(url).entries(entries));
if (!resp.failed().isEmpty()) { retryOrRaise(resp.failed()); }
```

## N5. More than 10 entries in one call

Severity: moderate. SQS `TooManyEntriesInBatchRequest` where the maximum "is 10"; SNS "more than 10" gives the same exception; classic-bus `PutEvents` "Maximum number of 10 items" ([SQS API](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessageBatch.html), [SNS API](https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html), [PutEvents API](https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_PutEvents.html)). Impact: HTTP 400 for the whole request. The Custom Event Bus limit is [Q5](./ask-first-decisions.md#q5-eventbridge-bus-type-and-putevents-chunk-size).

```java
// ❌ WRONG
sqs.sendMessageBatch(b -> b.queueUrl(url).entries(all250Entries));
// ✅ CORRECT: chunks of at most 10, each response checked (see publishing-and-limits.md)
```

## N6. Visibility timeout below the function timeout

Severity: high. Lambda rejects a mapping whose function timeout exceeds the visibility timeout; without headroom, messages become visible while still in flight ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)). Impact: duplicate processing; event source mapping creation error.

```text
❌ WRONG   function timeout 60 s, queue visibility timeout 30 s
✅ CORRECT function timeout 60 s, queue visibility timeout >= 360 s (+ MaximumBatchingWindowInSeconds), set with provisioning-aws-sqs-v6
```

## N7. Static AWS keys in production config

Severity: high. Lambda already provides the execution role's keys in the environment and the default credentials type is `default` ([SQS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html), [Lambda env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)). Family rule 5: secrets never in code or config. Impact: long-lived keys in the artifact; the role's least privilege is bypassed.

```properties
# ❌ WRONG
quarkus.sqs.aws.credentials.type=static
quarkus.sqs.aws.credentials.static-provider.access-key-id=AKIA...
```

```properties
# ✅ CORRECT: prod has no credentials keys; static only under %dev
%dev.quarkus.sqs.aws.credentials.type=static
```

## N8. Lambda on an SNS FIFO topic

Severity: moderate. "Lambda supports SNS triggers for standard SNS topics only. FIFO topics aren't supported" ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html)). Impact: the subscription design cannot work. For ordered processing, choose a design in `architecting-aws-sns-pubsub`.

```text
❌ WRONG   SNS FIFO topic      --lambda protocol--> Quarkus Lambda
✅ CORRECT SNS standard topic  --lambda protocol--> Quarkus Lambda
```

## N9. AWS_SESSION_TOKEN read at init

Severity: moderate. The variable is not set in every initialization mode (SnapStart uses a container credentials endpoint); resolve the token from the SDK credential provider chain inside the handler. AWS's Java sample resolves `DefaultCredentialsProvider` to `AwsSessionCredentials.sessionToken()` in `handleRequest` ([Parameter Store extension](https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html), [Lambda extension](https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html)). Impact: missing or stale token after a SnapStart restore; requests to `localhost:2773` rejected.

```java
// ❌ WRONG
private static final String TOKEN = System.getenv("AWS_SESSION_TOKEN"); // init time
// ✅ CORRECT (in the handler)
String token = ((AwsSessionCredentials) credentialsProvider.resolveCredentials()).sessionToken();
```

## N10. Apache sync client in a native Lambda

Severity: moderate. The default sync type is `url`; for native, "the URL Connection client must be preferred over the Apache HTTP Client when using synchronous mode" ([Quarkus guide](https://quarkus.io/version/3.40/guides/aws-lambda), [SQS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html)). Impact: client creation fails at startup when no implementation is present, or a heavier client in native.

```properties
# ❌ WRONG (native Lambda, sync calls)
quarkus.sqs.sync-client.type=apache
# ✅ CORRECT (default; plus software.amazon.awssdk:url-connection-client)
quarkus.sqs.sync-client.type=url
```
