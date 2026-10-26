# Evaluation Scenarios — provisioning-aws-sqs-v6

Five scenarios (canonical, two edge cases, misuse rejection, anti-pattern trap).
Each uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Encrypted Queue with DLQ and SNS Producer

```json
{
  "skills": ["provisioning-aws-sqs-v6"],
  "query": "Generate Terraform for an SQS standard queue with a dead-letter queue, encryption at rest and a policy that lets one SNS topic send to it. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Creates the DLQ as a separate aws_sqs_queue and attaches it with aws_sqs_queue_redrive_policy (or redrive_policy) using an integer maxReceiveCount",
      "Enables exactly one encryption option (sqs_managed_sse_enabled = true or kms_master_key_id)",
      "Uses aws_sqs_queue_policy with Version = \"2012-10-17\" explicitly",
      "Policy uses Principal Service sns.amazonaws.com, sqs:SendMessage and an ArnEquals aws:SourceArn condition",
      "Sets tags on the queues",
      "Gives the DLQ longer message_retention_seconds than the source queue"
    ],
    "must_not": [
      "Omit Version from the queue policy",
      "Use Principal \"*\" without a restricting condition",
      "Write maxReceiveCount as a string",
      "Set both kms_master_key_id and sqs_managed_sse_enabled without asking"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: FIFO with High Throughput and a FIFO DLQ

```json
{
  "skills": ["provisioning-aws-sqs-v6"],
  "query": "I need a high-throughput FIFO queue with a dead-letter queue. How do I configure it in Terraform?",
  "success_criteria": {
    "must_pass": [
      "Names the FIFO queue and the DLQ with a .fifo suffix and sets fifo_queue = true on both",
      "Sets deduplication_scope = \"messageGroup\" together with fifo_throughput_limit = \"perMessageGroupId\"",
      "Notes that many distinct message group IDs are needed for high throughput",
      "Notes that content_based_deduplication hashes the body and an explicit MessageDeduplicationId overrides it",
      "Places the DLQ in the same account and Region as the source"
    ],
    "must_not": [
      "Use a standard DLQ for the FIFO source",
      "Set fifo_throughput_limit = \"perMessageGroupId\" with deduplication_scope = \"queue\"",
      "State a specific absolute messages-per-second regional quota as confirmed"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Inline Policy Is Not Deprecated

```json
{
  "skills": ["provisioning-aws-sqs-v6"],
  "query": "The inline policy argument on aws_sqs_queue is deprecated in provider 6.x, right? Also I want to set both kms_master_key_id and sqs_managed_sse_enabled so the queue has double encryption.",
  "success_criteria": {
    "must_pass": [
      "States the provider page recommends aws_sqs_queue_policy over the inline argument and does not mark the inline argument deprecated",
      "States AWS allows one SSE option per queue and asks which single option to use, noting the provider page is silent on the combination (medium confidence)",
      "Does not claim the provider raises an error for setting both",
      "Recommends the dedicated resources and notes drift is detected only when the inline argument is set"
    ],
    "must_not": [
      "Claim the inline policy argument is deprecated",
      "Claim that setting both encryption options causes a provider error",
      "Claim sqs_managed_sse_enabled defaults to true in 6.x as a fact"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Review a Faulty Snippet

```json
{
  "skills": ["provisioning-aws-sqs-v6"],
  "query": "Review this Terraform: an aws_sqs_queue_policy with jsonencode({ Statement = [{ Principal = \"*\", Action = \"sqs:SendMessage\" }] }), a redrive_policy with maxReceiveCount = \"5\", and a queue named \"orders\" with fifo_queue = true. Is this correct for hashicorp/aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects the missing Version and gives Version = \"2012-10-17\" as the fix, citing the AWS hang (timeout while waiting) warning",
      "Rejects Principal \"*\" without a restricting condition and recommends a named principal with a source condition, citing Security Hub SQS.3 or the security best practices page",
      "Rejects maxReceiveCount as a string and gives an integer",
      "Rejects the FIFO queue name without .fifo and gives the .fifo suffix as the fix"
    ],
    "must_not": [
      "Accept a queue policy without Version",
      "Accept Principal \"*\" without a restricting condition in the queue policy",
      "Accept a FIFO queue whose name does not end in .fifo",
      "Cite SQS limits or defaults that the skill does not document as confirmed"
    ]
  }
}
```

---

## Scenario 5 — Edge Case: Service Producers on an Encrypted Queue

```json
{
  "skills": ["provisioning-aws-sqs-v6"],
  "query": "S3 and SNS must send to my SSE-KMS encrypted SQS queue. Which key do I use?",
  "success_criteria": {
    "must_pass": [
      "Recommends a customer managed KMS key because the AWS managed key policy cannot be modified",
      "States the service principal needs kms:Decrypt and kms:GenerateDataKey in the key policy",
      "Points to provisioning-aws-kms-v6 for the key policy",
      "States the S3 and EventBridge condition keys were not confirmed and must be taken from their docs (unverified)"
    ],
    "must_not": [
      "Use alias/aws/sqs as the queue key for AWS service producers",
      "State exact S3 or EventBridge condition keys as confirmed by this skill"
    ]
  }
}
```
