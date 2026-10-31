# Publishing and Limits

Back to [SKILL.md](../SKILL.md). Quarkiverse amazon-services 3.23.0, AWS SDK for Java v2 2.55.6. Fetched 2026-10-28. SDK v2 accessor names not shown on a fetched page are tagged (medium confidence).

## Contents

- [Limits table](#limits-table)
- [SQS SendMessageBatch](#sqs-sendmessagebatch)
- [SNS publish](#sns-publish)
- [EventBridge PutEvents](#eventbridge-putevents)
- [Production readiness](#production-readiness)

## Limits table

| Service | Limit | Source |
|---|---|---|
| SQS | Batch up to 10 messages; message up to 1,048,576 bytes (1 MiB); `SendMessageBatch` individual message and total payload both 1 MiB; up to 10 metadata attributes | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html |
| SQS large payloads | SQS Extended Client Library for Java (S3 reference, sync clients only) (family fact); S3 is the [data skill](../../integrating-quarkus-amazon-data-v3-40/SKILL.md) | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html |
| SNS | `PublishBatch` up to 10 messages; individual and total size 256 KiB (262,144 bytes) by default; topic `MaximumMessageSize` up to 1 MiB | https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html ; https://docs.aws.amazon.com/sns/latest/api/API_Publish.html |
| EventBridge classic bus | `Entries` 1 to 10; request total below 1 MB (1,048,576 bytes) from `Time` (14 bytes), `Source`, `DetailType`, `Detail`, `Resources` UTF-8 bytes; larger events: upload to S3 and send the object URL | https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_PutEvents.html ; https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html |
| EventBridge Custom Event Bus | the quota page lists "Entries per PutEvents or PutRawEvents request" as 1 to 100; SDK 2.55.6 modelling is (unverified) | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-quota.html |
| EventBridge PutEvents TPS | Regional (for example us-east-1 and eu-west-1 10,000 per second, other Regions 400 per second by default) | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-quota.html |

## SQS SendMessageBatch

`Failed` is a list of `BatchResultErrorEntry` with `Id`, `Code`, `Message`, `SenderFault` ([SQS API](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessageBatch.html)).

```java
// body illustrative; accessors failed(), id(), code(), message(), senderFault() are (medium confidence)
for (List<SendMessageBatchRequestEntry> chunk : chunksOf(entries, 10)) {      // N5
    SendMessageBatchResponse resp = sqs.sendMessageBatch(b -> b.queueUrl(queueUrl).entries(chunk));
    if (!resp.failed().isEmpty()) {
        resp.failed().forEach(f -> log.errorf("SQS entry %s failed: %s %s senderFault=%s",
                f.id(), f.code(), f.message(), f.senderFault()));
        // retry the senderFault=false entries or raise; never ignore (N4)
    }
}
```

## SNS publish

The sync example shape from the SNS page: `sns.publish(p -> p.topicArn(topicArn).message(message)).messageId()` ([SNS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sns.html), read in part, L1). For `PublishBatch`, check `Failed` and `Successful` exactly as for SQS ([SNS API](https://docs.aws.amazon.com/sns/latest/api/API_PublishBatch.html)). Topic payloads above 256 KiB: [Q6](./ask-first-decisions.md#q6-sns-payloads-above-256-kib).

## EventBridge PutEvents

"If an individual entry within a request fails, EventBridge continues processing the rest"; the index of each response element equals the index in the request array ([PutEvents](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html)). `@Inject EventBridgeClient` with `quarkus-amazon-eventbridge` is (medium confidence): the extension page does not name the class, the class name is from the AWS v2 sample. The AWS retry loop is written in SDK v1 style, so port it to v2 accessors.

```java
// classic bus: <= 10 entries, < 1 MB total (Q5 decides the chunk size)
PutEventsResponse result = eventBridge.putEvents(r -> r.entries(chunk));
List<PutEventsResultEntry> results = result.entries();     // entries(), eventId(), errorCode(): AWS v2 sample
for (int i = 0; i < results.size(); i++) {
    if (results.get(i).errorCode() != null) { retryLater.add(chunk.get(i)); }
}
// failedEntryCount() accessor: (medium confidence)
```

An event sent to a bus that does not exist is dropped with a `200` and is not counted in `FailedEntryCount` ([PutEvents](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html)). The entry-size calculation is AWS's own Java helper on the same page; run it before batching if `Detail` can be large.

## Production readiness

- Sync `url` is the Quarkus guide's recommendation for native and startup ([Quarkus guide](https://quarkus.io/version/3.40/guides/aws-lambda)).
- Log entry ids and `requestId`, never payloads with PII (family rule 7).
- IAM and queue, topic and bus resources are Terraform (`provisioning-aws-sqs-v6`, `provisioning-aws-sns-v6`, `provisioning-aws-eventbridge-v6`), never SAM or CDK (family rule 4).
