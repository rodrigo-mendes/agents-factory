# Evaluation Scenarios — provisioning-aws-xray-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap). Each uses
`success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Sampling Rule, Group and Encryption

```json
{
  "skills": ["provisioning-aws-xray-v6"],
  "query": "Generate Terraform for an X-Ray sampling rule for a checkout service, a group for its errors, and encryption with a customer managed key. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Sets every Required argument of aws_xray_sampling_rule (priority, reservoir_size, fixed_rate, host, http_method, url_path, service_name, service_type, resource_arn, version)",
      "Uses a priority within 1-9999 and a fixed_rate fraction between 0 and 1",
      "Uses aws_xray_group with group_name and filter_expression",
      "Uses aws_xray_encryption_config with type = \"KMS\" and key_id, marking the KMS key as defined elsewhere",
      "Marks example values as examples"
    ],
    "must_not": [
      "Use a fixed_rate expressed as a percentage above 1",
      "Invent a filter_expression syntax without marking it as a placeholder",
      "Use dynamodb_table in an S3 backend"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Lambda and API Gateway Tracing

```json
{
  "skills": ["provisioning-aws-xray-v6"],
  "query": "I enable X-Ray Active tracing on Lambda and want every request traced at a 50% rate. I also want X-Ray traces for my API Gateway HTTP API. How do I do this in Terraform?",
  "success_criteria": {
    "must_pass": [
      "States that Lambda Active sends traces only for sampled requests and that the sampling rate is not configurable",
      "States that AWS says X-Ray only supports tracing for REST APIs through API Gateway, so an HTTP API is not covered",
      "Points to provisioning-aws-lambda-v6 and provisioning-aws-api-gateway-v6 for the tracing_config and xray_tracing_enabled arguments",
      "Mentions that the Lambda execution role needs xray:PutTraceSegments and xray:PutTelemetryRecords"
    ],
    "must_not": [
      "Claim Lambda Active traces every request regardless of sampling",
      "Claim a custom sampling rule sets the Lambda sampling rate",
      "Claim API Gateway HTTP APIs are traced by X-Ray"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Reverting Encryption by Deleting the Resource

```json
{
  "skills": ["provisioning-aws-xray-v6"],
  "query": "I will delete aws_xray_encryption_config from my Terraform so X-Ray goes back to the AWS managed key aws/xray. Does that work?",
  "success_criteria": {
    "must_pass": [
      "States that removing the resource from Terraform does not change the encryption configuration in X-Ray",
      "States that default encryption (NONE) and the AWS managed key aws/xray are separate options",
      "Recommends applying type = \"NONE\" to return to default encryption",
      "Cites the provider page or the AWS encryption page"
    ],
    "must_not": [
      "Claim type = \"NONE\" uses the AWS managed key aws/xray",
      "Claim deleting the resource reverts the configuration"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Review of a Flawed Snippet

```json
{
  "skills": ["provisioning-aws-xray-v6"],
  "query": "Review: provider pinned to 6.57.0, S3 backend with dynamodb_table, rule_name treated as required, and an error sampling rule with attributes = { \"http.status\" = \"5??\" }. Is this correct for hashicorp/aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects 6.57.0 as withdrawn and offers ~> 6.69",
      "Rejects dynamodb_table as deprecated and offers use_lockfile = true",
      "States that rule_name is Optional in the provider (and is the resource id)",
      "States that the X-Ray SDK ignores rules that specify attributes and that API Gateway matches original request headers, so the example rule is not supported by the docs",
      "States that the AWS quota page lists 25 custom sampling rules per region, adjustable, not per account"
    ],
    "must_not": [
      "Accept version 6.57.0",
      "Accept dynamodb_table without noting its deprecated status",
      "Present the attributes-based error rule as a working pattern"
    ]
  }
}
```
