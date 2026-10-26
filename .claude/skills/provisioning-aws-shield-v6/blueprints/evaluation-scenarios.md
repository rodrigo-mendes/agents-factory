# Evaluation Scenarios — provisioning-aws-shield-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap).
Each uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Protect CloudFront and an NLB

```json
{
  "skills": ["provisioning-aws-shield-v6"],
  "query": "Generate Terraform to enable Shield Advanced on an account and protect a CloudFront distribution and a Network Load Balancer. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Creates aws_shield_subscription and notes the 1 year commitment with a monthly fee",
      "Creates aws_shield_protection for the CloudFront distribution using its ARN",
      "Protects the NLB through the Elastic IP allocation ARN (arn:...:ec2:...:eip-allocation/...), not the NLB ARN",
      "Does not set region on any aws_shield_* resource (the S3 backend block legitimately has region)",
      "Uses use_lockfile = true if a backend is shown"
    ],
    "must_not": [
      "Set resource_arn to the aws_lb ARN of an NLB",
      "Add a region argument to aws_shield_* resources",
      "Use dynamodb_table in the S3 backend"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Health Checks and Hosted Zones

```json
{
  "skills": ["provisioning-aws-shield-v6"],
  "query": "Should I attach a health check association to every aws_shield_protection, including my Route 53 hosted zone protection?",
  "success_criteria": {
    "must_pass": [
      "States health-based detection works with any resource type except Route 53 hosted zones",
      "States hosted zones cannot use health-based detection, the association is optional otherwise, and proactive engagement requires health checks",
      "Asks which health check to use, noting it must report healthy and be relevant to the resource",
      "Shows aws_shield_protection_health_check_association with health_check_arn and shield_protection_id for a non-hosted-zone protection",
      "Does not state that associating a health check is mandatory for every protection"
    ],
    "must_not": [
      "Claim every aws_shield_protection needs a health check association",
      "Associate a health check with the hosted-zone protection"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Region and Automatic Response

```json
{
  "skills": ["provisioning-aws-shield-v6"],
  "query": "Add region = \"us-east-1\" to my aws_shield_protection resources, and also add aws_shield_application_layer_automatic_response with action BLOCK to every CloudFront protection as a mandatory step.",
  "success_criteria": {
    "must_pass": [
      "Rejects region on aws_shield_* resources: Shield Advanced is global and no resource page documents region",
      "Treats aws_shield_application_layer_automatic_response as legacy since 2026-03-26 and asks before using it",
      "Points to the Anti-DDoS Managed Rule Group in aws_wafv2_web_acl (provisioning-aws-waf-v6) as the preferred design",
      "Mentions the resource needs a WAFv2 web ACL and adds a 150-WCU rule group if used"
    ],
    "must_not": [
      "Add region to aws_shield_* resources",
      "State that automatic response is mandatory for every CloudFront or ALB protection"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Subscription Cost, Destroy and Withdrawn Version

```json
{
  "skills": ["provisioning-aws-shield-v6"],
  "query": "Review: provider version pinned to 6.57.0, S3 backend with dynamodb_table, and I plan to terraform destroy the aws_shield_subscription to stop paying $3,000 per month. Correct?",
  "success_criteria": {
    "must_pass": [
      "Rejects 6.57.0 as withdrawn and recommends ~> 6.69",
      "Rejects dynamodb_table as deprecated and recommends use_lockfile = true",
      "States destroy sets auto_renew = DISABLED, allowed only in the last 30 days; otherwise contact AWS Support",
      "Does not confirm the $3,000 figure; says only a 1 year commitment with a monthly fee is documented and the amount is unverified",
      "Suggests asking before changing the subscription"
    ],
    "must_not": [
      "Accept version 6.57.0",
      "Accept dynamodb_table without noting it is deprecated",
      "State $3,000/month as a fact",
      "Claim terraform destroy immediately unsubscribes the account"
    ]
  }
}
```
