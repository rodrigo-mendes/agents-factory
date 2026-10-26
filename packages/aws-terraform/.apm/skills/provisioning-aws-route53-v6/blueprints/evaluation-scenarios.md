# Evaluation Scenarios — provisioning-aws-route53-v6

Four scenarios required for a hybrid knowledge skill (canonical, edge, misuse rejection, anti-pattern trap).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Public zone with alias, failover and query logging

```json
{
  "skills": ["provisioning-aws-route53-v6"],
  "query": "Generate Terraform for a public hosted zone example.com with an alias A record to an ALB, a failover pair with a health check, and DNS query logging. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Does not set region on any aws_route53_zone, aws_route53_record, aws_route53_health_check or aws_route53_query_log",
      "Alias record has an alias block (name, zone_id, evaluate_target_health) and no ttl or records",
      "Failover records set set_identifier and failover_routing_policy PRIMARY/SECONDARY, with health_check_id on the primary",
      "Query log group is in us-east-1 (provider alias or region = \"us-east-1\" on the log group) with retention_in_days set",
      "Adds an aws_cloudwatch_log_resource_policy for route53.amazonaws.com and depends_on it from aws_route53_query_log",
      "Uses use_lockfile = true if a backend is shown"
    ],
    "must_not": [
      "Set region on a Route 53 zone or record",
      "Combine alias with ttl or records",
      "Create the log group outside us-east-1",
      "Use dynamodb_table in the S3 backend"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Resolver region and DNSSEC prerequisites

```json
{
  "skills": ["provisioning-aws-route53-v6"],
  "query": "Do Route 53 Resolver resources accept a region argument? And what do I need to enable DNSSEC signing on a public zone?",
  "success_criteria": {
    "must_pass": [
      "States that aws_route53_zone/record and other core Route 53 resources are global and take no region",
      "States that aws_route53_resolver_* resources document an optional region on the resource page (carve-out; the region guide does not classify Resolver)",
      "States that the DNSSEC KMS key must be in us-east-1, customer managed, asymmetric ECC_NIST_P256 with SIGN_VERIFY usage",
      "States that DNSSEC applies to public hosted zones only",
      "States that aws_route53_key_signing_key plus aws_route53_hosted_zone_dnssec do not publish the DS record at the parent (medium confidence)",
      "Mentions CloudWatch alarms on DNSSECInternalFailure and DNSSECKeySigningKeysNeedingAction"
    ],
    "must_not": [
      "Claim all aws_route53_* resources reject region without the Resolver carve-out",
      "Claim DNSSEC is supported for private zones",
      "Claim these resources establish the chain of trust"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Exclusive records and mixed VPC association

```json
{
  "skills": ["provisioning-aws-route53-v6"],
  "query": "Can I use inline vpc blocks and aws_route53_zone_association on the same private zone? And is aws_route53_records_exclusive drift-free?",
  "success_criteria": {
    "must_pass": [
      "Rejects mixing in-line vpc blocks with aws_route53_zone_association for the same zone (perpetual difference in plan output)",
      "Mentions lifecycle ignore_changes = [vpc] only as a workaround",
      "States aws_route53_records_exclusive reconciles only on apply and does not prevent out-of-band creation",
      "States every aws_route53_record managed alongside needs an equivalent resource_record_set block to avoid drift, and the default NS/SOA must NOT be included (persistent drift)"
    ],
    "must_not": [
      "Claim aws_route53_records_exclusive has no drift risk",
      "Silently permit mixing inline vpc blocks and zone association"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Legacy claims and region on a zone

```json
{
  "skills": ["provisioning-aws-route53-v6"],
  "query": "Review: aws_route53_zone with region = \"us-east-1\", health check relying on a default failure_threshold of 3, an alias record with ttl = 60, and provider pinned to 6.57.0 with dynamodb_table locking.",
  "success_criteria": {
    "must_pass": [
      "Rejects region on aws_route53_zone because Route 53 is global",
      "Says the provider doc states no default for failure_threshold, so it must be set explicitly (not assumed to be 3)",
      "Rejects ttl on an alias record (conflicts with alias)",
      "Rejects pinning 6.57.0 (withdrawn) and suggests ~> 6.69",
      "Rejects dynamodb_table (deprecated) and suggests use_lockfile = true"
    ],
    "must_not": [
      "Accept region on aws_route53_zone",
      "Assert failure_threshold defaults to 3 or that intervals are 10 seconds",
      "Accept ttl together with alias",
      "Accept pinning 6.57.0"
    ]
  }
}
```
