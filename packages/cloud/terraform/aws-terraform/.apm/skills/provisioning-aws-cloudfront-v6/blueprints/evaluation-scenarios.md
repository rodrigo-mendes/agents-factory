# Evaluation Scenarios — provisioning-aws-cloudfront-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap). Each uses
`success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Static site on S3 with OAC, ACM and Route 53

```json
{
  "skills": ["provisioning-aws-cloudfront-v6"],
  "query": "Generate Terraform for a CloudFront distribution in front of a private S3 bucket with a custom domain, ACM certificate and Route 53 alias. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69; S3 backend uses use_lockfile = true",
      "Uses an aws_cloudfront_origin_access_control with signing_behavior = \"always\" and origin_access_control_id on the origin (no s3_origin_config)",
      "Adds an S3 bucket policy for principal cloudfront.amazonaws.com with an AWS:SourceArn condition on the distribution ARN",
      "Creates the ACM certificate with a us-east-1 provider alias; no region argument on CloudFront resources",
      "Sets minimum_protocol_version explicitly (TLSv1.2_2021 or newer) with ssl_support_method = \"sni-only\"",
      "Uses viewer_protocol_policy = \"redirect-to-https\"",
      "Creates Route 53 alias records using domain_name and hosted_zone_id of the distribution",
      "Sets is_ipv6_enabled and price_class explicitly"
    ],
    "must_not": [
      "Use an origin access identity",
      "Omit minimum_protocol_version",
      "Set region on aws_cloudfront_distribution",
      "Use dynamodb_table in the S3 backend"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: WAF, logging v2 and region placement

```json
{
  "skills": ["provisioning-aws-cloudfront-v6"],
  "query": "Attach a WAFv2 web ACL and enable standard logging v2 on my distribution. Which resources must be in us-east-1 and how do I reference the ACL?",
  "success_criteria": {
    "must_pass": [
      "States web_acl_id takes the WAFv2 ARN (aws_wafv2_web_acl.x.arn), not the ID",
      "States the web ACL uses scope CLOUDFRONT in us-east-1, tagged as medium confidence for the alias-vs-region choice",
      "States the CloudWatch Logs delivery API must be called in us-east-1 and a Firehose destination must be in us-east-1",
      "Uses aws_cloudwatch_log_delivery_source with log_type = \"ACCESS_LOGS\" and resource_arn = the distribution ARN",
      "Notes Security Hub CloudFront.5 checks only legacy logging, tagged medium confidence"
    ],
    "must_not": [
      "Claim v2 logging replaces or changes legacy logging",
      "State unresearched argument names of the delivery destination as verified fact"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: OAC on an S3 website endpoint

```json
{
  "skills": ["provisioning-aws-cloudfront-v6"],
  "query": "My S3 bucket has static website hosting enabled. Configure an origin access control for the website endpoint.",
  "success_criteria": {
    "must_pass": [
      "States S3 website endpoints cannot use OAC or OAI",
      "Recommends configuring the website endpoint as a custom origin (custom_origin_config)",
      "Does not set origin_access_control_id on the website endpoint origin"
    ],
    "must_not": [
      "Claim OAC works with S3 website endpoints",
      "Fall back to an origin access identity for the website endpoint"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Legacy snippet review

```json
{
  "skills": ["provisioning-aws-cloudfront-v6"],
  "query": "Review: a CloudFront distribution with forwarded_values, a viewer_certificate without minimum_protocol_version (assume TLSv1.2_2021 is the default), trusted_signers = [\"self\"], and an etag set on a response headers policy. Correct for aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects forwarded_values as deprecated and recommends cache_policy_id and/or origin_request_policy_id",
      "Corrects the assumption: the provider default for minimum_protocol_version is TLSv1; set it explicitly",
      "Recommends trusted_key_groups over trusted_signers (CloudFront.17)",
      "Rejects the configured etag: computed only since 6.0.0"
    ],
    "must_not": [
      "Accept TLSv1.2_2021 as the provider default",
      "Accept etag as configurable on the response headers policy",
      "Claim forwarded_values was removed in 6.x"
    ]
  }
}
```
