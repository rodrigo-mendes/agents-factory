# Evaluation Scenarios — provisioning-aws-sns-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap) plus one extra.
Each uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Encrypted Topic with SQS Subscription and DLQ

```json
{
  "skills": ["provisioning-aws-sns-v6"],
  "query": "Generate Terraform for an encrypted SNS topic with an SQS subscription and a dead-letter queue. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Sets kms_master_key_id on the topic",
      "Adds redrive_policy with deadLetterTargetArn on the subscription",
      "States the DLQ must be in the same account and region as the subscription",
      "Marks example names and ARNs as examples",
      "Treats the queue and queue policies as defined elsewhere (sibling sqs skill), not invented"
    ],
    "must_not": [
      "Subscribe to an SQS queue without mentioning a DLQ",
      "Use a bare account ID as a topic-policy Principal"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: FIFO Topic Delivery and Throughput Scope

```json
{
  "skills": ["provisioning-aws-sns-v6"],
  "query": "Create a FIFO SNS topic with high throughput that feeds a standard SQS queue and a Lambda function.",
  "success_criteria": {
    "must_pass": [
      "Uses a name ending in .fifo with fifo_topic = true",
      "States that SQS standard queues are supported on FIFO topics",
      "States that fifo_throughput_scope = MessageGroup is the high-throughput mode",
      "States that MessageGroup cannot be reverted to Topic",
      "Asks the user before choosing MessageGroup",
      "Routes Lambda delivery through an SQS queue instead of a direct subscription",
      "Recommends setting fifo_throughput_scope at creation"
    ],
    "must_not": [
      "Claim FIFO topics may only deliver to SQS FIFO queues",
      "Claim MessageGroup is the lower-throughput setting",
      "Create a direct lambda, email or HTTP(S) subscription on the FIFO topic"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: AWS Managed Key and EventBridge Conditions

```json
{
  "skills": ["provisioning-aws-sns-v6"],
  "query": "EventBridge and CloudWatch alarms publish to my topic. Is alias/aws/sns fine, and can I add aws:SourceAccount to the key policy for EventBridge?",
  "success_criteria": {
    "must_pass": [
      "Rejects alias/aws/sns and recommends a customer managed key",
      "States the service principal needs kms:GenerateDataKey* and kms:Decrypt in the key policy",
      "States aws:SourceAccount/aws:SourceArn conditions are not supported for EventBridge publishing to encrypted topics",
      "Cites the SNS key management page"
    ],
    "must_not": [
      "Accept alias/aws/sns for AWS service publishers",
      "Add aws:SourceAccount or aws:SourceArn conditions to the EventBridge key-policy statement"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Unconfirmed Email and Provider Region

```json
{
  "skills": ["provisioning-aws-sns-v6"],
  "query": "I subscribe ops@example.com by email in Terraform, and the topic is in us-east-1 but my default provider is eu-west-1. Terraform destroy will clean it up, right?",
  "success_criteria": {
    "must_pass": [
      "States that Terraform cannot remove an unconfirmed email subscription; destroy removes it from state only and it stays in AWS",
      "States that confirmation can happen outside Terraform and that pending_confirmation shows the status",
      "States that the subscription must use a provider in the topic's region or creation fails",
      "Recommends a provider alias in us-east-1"
    ],
    "must_not": [
      "Claim destroy removes an unconfirmed subscription from AWS",
      "Create the subscription with the eu-west-1 provider"
    ]
  }
}
```

---

## Scenario 5 — Policy Ownership Decision

```json
{
  "skills": ["provisioning-aws-sns-v6"],
  "query": "Should I set policy on aws_sns_topic and also create aws_sns_topic_policy?",
  "success_criteria": {
    "must_pass": [
      "Asks or recommends picking one mechanism",
      "Marks the conflict as an inference with (unverified), noting neither provider page has a do-not-mix note"
    ],
    "must_not": [
      "State as a documented fact that the provider docs forbid mixing them",
      "Use a bare account ID as Principal"
    ]
  }
}
```
