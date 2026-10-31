# Never-Do — Shield Advanced

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. `region` on `aws_shield_*` Resources

The enhanced-region guide lists Shield Advanced (`aws_shield_*`) under global services, and no
`aws_shield_*` resource page documents a `region` argument.

```hcl
# WRONG
resource "aws_shield_protection" "bad" {
  name         = "cdn"
  resource_arn = aws_cloudfront_distribution.main.arn
  region       = "us-east-1"   # WRONG — global service, no region argument
}

# CORRECT
resource "aws_shield_protection" "good" {
  name         = "cdn"
  resource_arn = aws_cloudfront_distribution.main.arn
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

## 2. NLB ARN as `resource_arn`

AWS supports NLBs only through associations to Elastic IP addresses.

```hcl
# WRONG
resource "aws_shield_protection" "bad" {
  name         = "nlb"
  resource_arn = aws_lb.nlb.arn   # WRONG — NLB is protected via its EIP
}

# CORRECT — see always-do-subscription-protection.md section 2
resource "aws_shield_protection" "good" {
  name         = "nlb-eip"
  resource_arn = "arn:${data.aws_partition.current.partition}:ec2:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:eip-allocation/${aws_eip.nlb.id}"
}
```

Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html

## 3. Health Check on a Hosted-Zone Protection

Health-based detection works with any resource type except Route 53 hosted zones.

```hcl
# WRONG
resource "aws_shield_protection" "zone" {
  name         = "zone"
  resource_arn = aws_route53_zone.main.arn
}
resource "aws_shield_protection_health_check_association" "bad" {
  health_check_arn     = var.health_check_arn
  shield_protection_id = aws_shield_protection.zone.id   # WRONG — hosted zone
}
```

Correct: protect the hosted zone and omit the association; associate health checks only with
other protection types.

Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html

## 4. Protection Group Arguments Without the Matching `pattern`

`members` is for `pattern = "ARBITRARY"` only; `resource_type` is for `pattern = "BY_RESOURCE_TYPE"` only.

```hcl
# WRONG
resource "aws_shield_protection_group" "bad" {
  protection_group_id = "g"
  aggregation         = "MAX"
  pattern             = "ALL"
  members             = [aws_shield_protection.cdn.resource_arn]   # WRONG — not ARBITRARY
}

# CORRECT
resource "aws_shield_protection_group" "good" {
  protection_group_id = "g"
  aggregation         = "MAX"
  pattern             = "ALL"
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_group.html.markdown

## 5. S3 Backend with `dynamodb_table`

```hcl
# WRONG
backend "s3" { dynamodb_table = "tf-locks" }   # deprecated

# CORRECT
backend "s3" { use_lockfile = true }
```

Source: https://developer.hashicorp.com/terraform/language/backend/s3

## 6. Pinning Version 6.57.0

```hcl
# WRONG — withdrawn from GitHub and the Registry
aws = { source = "hashicorp/aws", version = "6.57.0" }

# CORRECT
aws = { source = "hashicorp/aws", version = "~> 6.69" }
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
