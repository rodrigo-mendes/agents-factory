# SNS- and EventBridge-Triggered Handlers

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Both services invoke Lambda asynchronously, so there is no batch response: a thrown exception triggers the Lambda async retry.

## SNS-triggered handler

AWS: "Lambda supports SNS triggers for standard SNS topics only. FIFO topics aren't supported" (N8), and "Lambda asynchronous invocations process each event at least once" (A7). The record shape is `Records[].Sns.{MessageId, Message, MessageAttributes, TopicArn, Subject}` ([AWS SNS](https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html)).

```java
// Quarkus 3.40.1.1 (body illustrative, medium confidence)
@Named("orders-sns")                      // quarkus.lambda.handler=orders-sns
public class OrdersSnsHandler implements RequestHandler<SNSEvent, Void> {   // SNSEvent class: (medium confidence)
    @Override
    public Void handleRequest(SNSEvent event, Context context) {
        event.getRecords().forEach(r -> handle(r.getSNS().getMessageId(), r.getSNS().getMessage())); // accessors: (medium confidence)
        return null;   // throwing triggers Lambda async retries (2 by default)
    }
}
```

`SNSEvent` and `ScheduledEvent` class names come from the `aws-lambda-java-events` README on the main branch (medium confidence). Publishing to SNS is in [publishing](./publishing-and-limits.md).

## EventBridge-triggered handler

An EventBridge event has the top-level fields `version, id, detail-type, source, account, time, region, resources, detail` ([event structure](https://docs.aws.amazon.com/eventbridge/latest/ref/overiew-event-structure.html)). Two ways to receive it ([Q3](./ask-first-decisions.md#q3-event-input-types)):

- Library type `ScheduledEvent`: `time` is a Joda `DateTime` and `detail` a `Map<String,Object>` (main-branch source, medium confidence). Native-image reflection for these classes is (unverified).
- Own record, typed `detail`. `detail-type` needs a JSON name mapping. Quarkus deserializing events with Jackson is inferred from the `quarkus-jackson` dependency of `quarkus-amazon-lambda-common` (medium confidence).

```java
// own record per Q3 option B (top-level fields from the event-structure page)
public record OrderEvent(String version, String id,
                         @com.fasterxml.jackson.annotation.JsonProperty("detail-type") String detailType,
                         String source, String account, String time, String region,
                         java.util.List<String> resources, OrderDetail detail) {}  // Jackson mapping: (medium confidence)
```

Use `id` as the idempotency key (A7). EventBridge Scheduler also invokes Lambda asynchronously; with no payload it sends "an empty event" ([Scheduler](https://docs.aws.amazon.com/lambda/latest/dg/with-eventbridge-scheduler.html)).

## Retry layers to account for

| Layer | Behaviour | Source |
|---|---|---|
| EventBridge to target | Retries delivery "for 24 hours and up to 185 times" by default, then drops the event unless a DLQ is set | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html |
| Lambda async invocation | A function error is retried "two more times" by default; throttles and system errors for up to 6 hours | https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html |
| Discarded events | Capture with an on-failure destination or a DLQ | https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html |

EventBridge allows up to 5 targets per rule, and does not support SQS targets or target DLQs encrypted with an AWS owned key ([targets](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-targets.html)). Rule, target and DLQ resources are Terraform (`provisioning-aws-eventbridge-v6`, `provisioning-aws-sns-v6`); design choices are `architecting-eventbridge-eda` and `architecting-aws-sns-pubsub`.
