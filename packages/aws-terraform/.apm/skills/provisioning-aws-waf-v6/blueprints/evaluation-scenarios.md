# Evaluation Scenarios — provisioning-aws-waf-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap). Each uses
`success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Regional web ACL with logging and ALB association

```json
{
  "skills": ["provisioning-aws-waf-v6"],
  "query": "Generate Terraform for a regional WAFv2 web ACL with a managed rule group, a rate-based rule, logging, and an association with an existing ALB. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Sets scope = \"REGIONAL\", default_action and visibility_config on the web ACL",
      "Uses override_action (count first, then none) on the managed rule group statement, not action",
      "Rate-based rule limit is at least 10",
      "Any aws_wafv2_web_acl_rule uses web_acl_arn and its parent web ACL has lifecycle { ignore_changes = [rule] }",
      "Uses aws_wafv2_web_acl_association with resource_arn and web_acl_arn",
      "Logging destination name starts with aws-waf-logs-"
    ],
    "must_not": [
      "Use action on a rule-group statement",
      "Use web_acl_id or scope on aws_wafv2_web_acl_rule",
      "Hard-code WCU numbers for managed rule groups",
      "Use dynamodb_table in the S3 backend"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: CloudFront-scope web ACL

```json
{
  "skills": ["provisioning-aws-waf-v6"],
  "query": "I need a WAFv2 web ACL in front of a CloudFront distribution. How do I create and attach it in Terraform with aws provider 6.x?",
  "success_criteria": {
    "must_pass": [
      "Uses scope = \"CLOUDFRONT\" with the provider targeting us-east-1 (alias)",
      "Attaches the ACL with aws_cloudfront_distribution web_acl_id = the web ACL arn",
      "States that aws_wafv2_web_acl_association must not be used for CloudFront",
      "If region = \"us-east-1\" on the resource is mentioned, labels it as an inference (medium confidence)",
      "Points to provisioning-aws-cloudfront-v6 for the distribution itself"
    ],
    "must_not": [
      "Create an aws_wafv2_web_acl_association for the CloudFront distribution",
      "Create a CLOUDFRONT-scope web ACL with a non-us-east-1 provider",
      "Claim the state backend must be in us-east-1"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: HTTP API association and legacy limits

```json
{
  "skills": ["provisioning-aws-waf-v6"],
  "query": "Associate my web ACL with an aws_apigatewayv2_stage HTTP API, and set a WCU validation of max 1500 and a rate limit minimum of 100.",
  "success_criteria": {
    "must_pass": [
      "Rejects the HTTP API association: the association supports REST API stages only",
      "States that the hard WCU maximum is 5,000 and 1,500 is only a pricing threshold",
      "States that the AWS rate-based rule minimum is 10",
      "Suggests a REST API stage and points to provisioning-aws-api-gateway-v6"
    ],
    "must_not": [
      "Create aws_wafv2_web_acl_association with an HTTP API stage",
      "Validate capacity <= 1500 as the maximum",
      "Validate rate limit >= 100 as the AWS minimum"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: web_acl_rule arguments and inline mixing

```json
{
  "skills": ["provisioning-aws-waf-v6"],
  "query": "Review this Terraform: aws_wafv2_web_acl_rule with web_acl_id and scope, attached to a web ACL that also has inline rule blocks and no lifecycle block. Is this correct for hashicorp/aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects web_acl_id and scope; states the argument is web_acl_arn and scope is not an argument",
      "States the parent web ACL needs lifecycle { ignore_changes = [rule] } when separate rule resources are used",
      "Mentions inline rule limitations: deletion-ordering errors, spurious diffs, coupled updates",
      "Offers a corrected snippet or recommends keeping all rules inline"
    ],
    "must_not": [
      "Accept web_acl_id or scope on aws_wafv2_web_acl_rule",
      "Accept mixing inline rule with separate rule resources without ignore_changes"
    ]
  }
}
```
