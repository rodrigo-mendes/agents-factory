# Evaluation Scenarios — architecting-aws-sns-pubsub

Test cases for `/evaluating-skill-scenarios architecting-aws-sns-pubsub`.

---

## Scenario 1 — Canonical: Fan-Out with DLQ and Filter Policies

```json
{
  "skills": ["architecting-aws-sns-pubsub"],
  "query": "Design a serverless fan-out architecture for an e-commerce web application where an order-placed event must trigger three independent workflows: inventory update, email notification, and fraud check. Each workflow must be independently resilient.",
  "expected_behavior": [
    "Recommends SNS Standard Topic as the fan-out layer",
    "Specifies three SQS queues (one per consumer), each as a subscription to the SNS topic",
    "Assigns a DLQ to every SNS subscription via RedrivePolicy",
    "Specifies a FilterPolicy per subscription scoped to order-created event type",
    "Lambda workers poll their respective SQS queues via event source mappings (not direct SNS-to-Lambda)",
    "Includes SQS resource-based policy granting sqs:SendMessage to the SNS topic ARN with aws:SourceArn condition",
    "Specifies CloudWatch alarm on ApproximateNumberOfMessagesVisible >= 1 on each DLQ"
  ]
}
```

---

## Scenario 2 — Canonical: FIFO Ordered Financial Transaction Pipeline

```json
{
  "skills": ["architecting-aws-sns-pubsub"],
  "query": "Design an SNS architecture for a payment processing system where price-update events must arrive at retail and wholesale consumers in strict publish order, with exactly-once delivery, and no possibility of two identical updates both applying.",
  "expected_behavior": [
    "Selects SNS FIFO Topic (not Standard) due to ordering and deduplication requirement",
    "Uses MessageGroupId set to a business entity identifier (e.g., productId)",
    "Configures ContentBasedDeduplication=false and requires publishers to supply explicit MessageDeduplicationId",
    "Downstream subscribers are SQS FIFO queues only (not Lambda/HTTP/email/SMS direct)",
    "Attaches FIFO DLQs to each subscription",
    "Recommends FifoThroughputScope=MessageGroup only if aggregate throughput exceeds 3,000 msg/s",
    "Warns about head-of-line blocking risk with coarse MessageGroupId granularity"
  ]
}
```

---

## Scenario 3 — Edge Case: Raw Message Delivery with High Attribute Count

```json
{
  "skills": ["architecting-aws-sns-pubsub"],
  "query": "Our SQS subscriber is configured with raw message delivery enabled. We send messages with 12 message attributes for routing and metadata. Some messages seem to disappear silently. What is the cause?",
  "expected_behavior": [
    "Identifies the 10-attribute hard limit on raw message delivery as the root cause",
    "States that messages exceeding 10 attributes with raw delivery are silently discarded — no CloudWatch error is raised",
    "Does NOT confuse this with DLQ routing (filtered-out messages do not go to DLQ; neither do these silently discarded messages)",
    "Recommends reducing attributes to ≤ 10, or consolidating metadata into the message body",
    "Recommends disabling raw delivery if attribute count cannot be reduced"
  ]
}
```

---

## Scenario 4 — Edge Case: Message Data Protection Replacement (Breaking Change 2026)

```json
{
  "skills": ["architecting-aws-sns-pubsub"],
  "query": "We are a new AWS customer onboarding in August 2026. We need to detect and redact PII from messages passing through our SNS topic before they reach downstream consumers. How do we implement sensitive data protection?",
  "expected_behavior": [
    "States explicitly that Message Data Protection is unavailable to new customers as of April 30, 2026",
    "Does NOT recommend configuring Message Data Protection for new customers",
    "Recommends replacement pattern: Lambda subscribed to inbound SNS topic → Amazon Bedrock Guardrails → republish (if not blocked) to destination SNS topic",
    "References the sample implementation: https://github.com/aws-samples/sample-sns-sensitive-data-protection-bedrock",
    "Notes existing customers with previously configured policies may continue using the feature"
  ]
}
```

---

## Scenario 5 — Misuse Trap: Direct SNS-to-Lambda on High-Volume Topic

```json
{
  "skills": ["architecting-aws-sns-pubsub"],
  "query": "We want to subscribe a Lambda function directly to our SNS topic that receives 5,000 events per second during peak hours. Is this the correct approach?",
  "expected_behavior": [
    "Rejects direct SNS-to-Lambda subscription for this traffic pattern",
    "Explains that Lambda concurrency exhaustion causes SNS throttle errors at peak rates",
    "States that without a DLQ on the subscription, messages are permanently and silently lost after retry exhaustion",
    "Recommends SNS → SQS Standard Queue (with DLQ) → Lambda event source mapping with MaximumConcurrency set appropriately",
    "Notes that SQS buffers the 5,000 msg/s spike and Lambda scales controlled by MaximumConcurrency"
  ]
}
```

---

## Scenario 6 — Misuse Trap: Wildcard Principal in Topic Policy

```json
{
  "skills": ["architecting-aws-sns-pubsub"],
  "query": "To make our SNS topic accessible to all our microservices, a developer set the topic policy Principal to '*' and Action to 'sns:Publish'. This was flagged in a security review. What is the correct fix?",
  "expected_behavior": [
    "Identifies the pattern as a critical security anti-pattern",
    "Explains that Principal '*' without a Condition block allows any AWS principal in any account to publish",
    "Does NOT recommend using aws:SourceOwner (deprecated)",
    "Recommends replacing '*' with specific service principals (e.g., events.amazonaws.com for EventBridge, lambda.amazonaws.com for Lambda invocations) or specific IAM role ARNs",
    "Specifies that cross-service grants must include aws:SourceArn or aws:SourceAccount conditions to prevent confused deputy attacks",
    "Provides the detection command: aws sns get-topic-attributes --query Attributes.Policy to scan for unguarded wildcards"
  ]
}
```
