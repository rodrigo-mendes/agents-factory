# Never-Do — Region, Query Logs, DNSSEC, Provider/Backend

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 1. region on global Route 53 resources

`aws_route53_*` zones, records, health checks, query logs, DNSSEC, delegation sets, and
`aws_route53domains_*` take no `region` argument and no `@region` import per the AWS provider region
guide. Carve-out: `aws_route53_resolver_*` resources document an optional `region` on their resource
pages (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_endpoint.html.markdown).

```hcl
# WRONG
resource "aws_route53_zone" "bad" {
  name   = "example.com"
  region = "us-east-1"   # WRONG — Route 53 is global
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

# CORRECT — no region argument
resource "aws_route53_zone" "good" {
  name = "example.com"
}
```

## 2. Query log log group outside us-east-1 or on private zone

The log group must be in us-east-1 and the hosted zone must be public.

```hcl
# WRONG — log group in the default provider region, zone is private
resource "aws_cloudwatch_log_group" "bad" {
  name = "/aws/route53/internal.example.com"
}
resource "aws_route53_query_log" "bad" {
  zone_id                  = aws_route53_zone.private.zone_id   # WRONG — private
  cloudwatch_log_group_arn = aws_cloudwatch_log_group.bad.arn   # WRONG — not us-east-1
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_query_log.html.markdown

# CORRECT — see always-do-logging-dnssec.md#5-query-logging
resource "aws_cloudwatch_log_group" "good" {
  provider = aws.us_east_1
  name     = "/aws/route53/${aws_route53_zone.public.name}"
}
```

## 3. DNSSEC on a private zone or with a non-us-east-1 KMS key

DNSSEC signing is for public hosted zones only (private zones: use Resolver DNSSEC validation). The KSK
KMS key must be in us-east-1.

```hcl
# WRONG — key in the default provider region
resource "aws_kms_key" "bad" {
  customer_master_key_spec = "ECC_NIST_P256"
  key_usage                = "SIGN_VERIFY"
}
resource "aws_route53_key_signing_key" "bad" {
  hosted_zone_id             = aws_route53_zone.private.id   # WRONG — private zone
  key_management_service_arn = aws_kms_key.bad.arn           # WRONG — not us-east-1
  name                       = "bad"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_key_signing_key.html.markdown

# CORRECT — public zone + aws_kms_key with provider = aws.us_east_1 (always-do-logging-dnssec.md#6-dnssec)
```

## 4. Withdrawn version and deprecated backend option

```hcl
# WRONG
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.57.0" }   # WRONG — withdrawn
  }
  backend "s3" {
    bucket         = "my-tf-state"
    key            = "route53/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "locks"   # WRONG — deprecated
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
# Source: https://developer.hashicorp.com/terraform/language/backend/s3

# CORRECT
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
  backend "s3" {
    bucket       = "my-tf-state"
    key          = "route53/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true
  }
}
```
