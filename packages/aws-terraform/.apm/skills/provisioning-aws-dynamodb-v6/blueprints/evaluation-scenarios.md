# Evaluation Scenarios — provisioning-aws-dynamodb-v6

Five scenarios (canonical, edge, misuse rejection, anti-pattern trap, unverified handling).
Each uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Protected on-demand table

```json
{
  "skills": ["provisioning-aws-dynamodb-v6"],
  "query": "Generate Terraform for a DynamoDB table with a partition and sort key, on-demand billing, point-in-time recovery, deletion protection and a customer managed KMS key. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Sets billing_mode = \"PAY_PER_REQUEST\" explicitly",
      "Defines attribute blocks only for the key attributes",
      "Sets deletion_protection_enabled = true and point_in_time_recovery { enabled = true }",
      "Uses server_side_encryption { enabled = true, kms_key_arn = ... } for the customer managed key",
      "Marks example names and values as examples"
    ],
    "must_not": [
      "Add attribute blocks for non-key attributes",
      "Create a DynamoDB lock table or use dynamodb_table in the S3 backend",
      "Claim a Security Hub control requires a customer managed key"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Separate global index resource and warm throughput

```json
{
  "skills": ["provisioning-aws-dynamodb-v6"],
  "query": "I want to manage a global secondary index with the separate aws_dynamodb_global_secondary_index resource and lower the table warm throughput. What arguments do I use and what should I watch for?",
  "success_criteria": {
    "must_pass": [
      "Uses index_name, key_schema, projection and provisioned_throughput (PROVISIONED table) or on_demand_throughput (PAY_PER_REQUEST table)",
      "States the table must not also declare inline global_secondary_index blocks",
      "Asks the user before adopting the resource, noting the table page calls it experimental while the resource page shows no warning (medium confidence)",
      "States that provider >= 6.57.1 no longer replaces the table when warm_throughput decreases, and that 6.57.0 must never be pinned",
      "Notes that explicitly setting both warm_throughput values to the default/minimum causes reported diffs"
    ],
    "must_not": [
      "Use name, hash_key, range_key, projection_type or read_capacity as arguments of aws_dynamodb_global_secondary_index",
      "Declare the separate resource experimental as a settled fact"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Customer managed key "required" by Security Hub

```json
{
  "skills": ["provisioning-aws-dynamodb-v6"],
  "query": "Security Hub requires a customer managed KMS key for DynamoDB tables, right? Set kms_key_arn to alias/aws/dynamodb so we are compliant.",
  "success_criteria": {
    "must_pass": [
      "Does not confirm the claim: the DynamoDB controls DynamoDB.1, .2, .4, .5 and .6 do not mention a customer managed key (medium confidence, absence of evidence); DynamoDB.3 and .7 concern DAX",
      "States that alias/aws/dynamodb is the AWS managed key and that the default (no server_side_encryption block) is the AWS owned key",
      "States that kms_key_arn is for keys other than alias/aws/dynamodb, and that enabled = true without kms_key_arn selects the AWS managed key",
      "Offers the choice of AWS owned, AWS managed or customer managed key as a user decision and points to provisioning-aws-kms-v6 for the key"
    ],
    "must_not": [
      "Set kms_key_arn to the alias/aws/dynamodb ARN",
      "Call alias/aws/dynamodb the default key",
      "Confirm that Security Hub requires a customer managed key for tables",
      "State as a High-confidence fact that no Security Hub control could ever require one"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Legacy snippet

```json
{
  "skills": ["provisioning-aws-dynamodb-v6"],
  "query": "Review this: an S3 backend with dynamodb_table locking, a global table built with both replica blocks and aws_dynamodb_table_replica, and an inline global_secondary_index using hash_key and range_key. Is it correct for hashicorp/aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects dynamodb_table locking as deprecated and gives use_lockfile = true",
      "Rejects mixing replica blocks with aws_dynamodb_table_replica; offers one mechanism, with ignore_changes = [replica] when using the replica resource",
      "Rejects inline GSI hash_key/range_key as deprecated in 6.x and gives key_schema blocks",
      "Cites the S3 backend docs or the provider table page for each rejection"
    ],
    "must_not": [
      "Accept dynamodb_table without noting its deprecated status",
      "Accept both replica mechanisms on one table",
      "Say aws_dynamodb_global_table V1 is deprecated; the page only says to use the replica block for V2 and warns about restrictions"
    ]
  }
}
```

---

## Scenario 5 — Unverified handling: settings the docs leave open

```json
{
  "skills": ["provisioning-aws-dynamodb-v6"],
  "query": "Set up a write-capacity autoscaling policy, a Kinesis streaming destination with the default precision, contributor insights in a specific mode, and tell me exactly when TTL deletes items.",
  "success_criteria": {
    "must_pass": [
      "Says the write-capacity metric type is not shown on the provider page and must be confirmed (unverified)",
      "Says the Kinesis precision default is not stated and either sets it explicitly or asks",
      "Says the contributor insights mode values are not listed and does not invent one",
      "Says TTL deletion timing was not verified and gives no deadline"
    ],
    "must_not": [
      "State a TTL deletion deadline as fact",
      "Invent contributor insights mode values",
      "State the Kinesis precision default as fact"
    ]
  }
}
```
