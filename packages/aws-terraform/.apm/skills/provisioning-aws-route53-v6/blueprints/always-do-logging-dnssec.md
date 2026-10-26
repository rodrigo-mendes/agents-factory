# Always-Do — Query Logging, DNSSEC, Delegation Sets, Resolver

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 5. Query logging

Public zones only; log group must be in us-east-1; a CloudWatch Logs resource policy must allow
`route53.amazonaws.com` `logs:CreateLogStream` + `logs:PutLogEvents` on `/aws/route53/*`. AWS limits
10 CloudWatch Logs resource policies per account/region, so reuse one policy across zones. Satisfies
Security Hub Route53.2.

```hcl
resource "aws_cloudwatch_log_group" "query" {
  provider          = aws.us_east_1
  name              = "/aws/route53/${aws_route53_zone.public.name}"
  retention_in_days = 90   # example value; CloudWatch keeps logs indefinitely by default
}

data "aws_iam_policy_document" "route53_query_logging" {
  statement {
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:log-group:/aws/route53/*"]   # example ARN pattern; AWS scope: /aws/route53/*
    principals {
      type        = "Service"
      identifiers = ["route53.amazonaws.com"]
    }
  }
}

resource "aws_cloudwatch_log_resource_policy" "route53" {
  provider        = aws.us_east_1
  policy_name     = "route53-query-logging"
  policy_document = data.aws_iam_policy_document.route53_query_logging.json
}

resource "aws_route53_query_log" "public" {
  depends_on               = [aws_cloudwatch_log_resource_policy.route53]
  zone_id                  = aws_route53_zone.public.zone_id
  cloudwatch_log_group_arn = aws_cloudwatch_log_group.query.arn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_query_log.html.markdown
# Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/route53-controls.html
```

## 6. DNSSEC

Public hosted zones only. KMS key: customer managed, asymmetric `ECC_NIST_P256`, usage
`SIGN_VERIFY`, in us-east-1. You own KSK management/rotation; Route 53 manages the ZSK. Create
CloudWatch alarms on `DNSSECInternalFailure` and `DNSSECKeySigningKeysNeedingAction`. These two
resources do not publish the DS record at the parent; that is a separate step (medium confidence).
HCL below is a fragment with example values.

```hcl
data "aws_caller_identity" "current" {}

resource "aws_kms_key" "dnssec" {
  provider                 = aws.us_east_1
  customer_master_key_spec = "ECC_NIST_P256"
  key_usage                = "SIGN_VERIFY"
  deletion_window_in_days  = 7
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "Allow Route 53 DNSSEC Service"
        Effect    = "Allow"
        Principal = { Service = "dnssec-route53.amazonaws.com" }
        Action    = ["kms:DescribeKey", "kms:GetPublicKey", "kms:Sign"]
        Resource  = "*"
        Condition = {
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
          ArnLike      = { "aws:SourceArn" = "arn:aws:route53:::hostedzone/*" }
        }
      },
      {
        Sid       = "Allow Route 53 DNSSEC Service to CreateGrant"
        Effect    = "Allow"
        Principal = { Service = "dnssec-route53.amazonaws.com" }
        Action    = "kms:CreateGrant"
        Resource  = "*"
        Condition = { Bool = { "kms:GrantIsForAWSResource" = "true" } }
      },
      {
        Sid       = "Enable IAM User Permissions"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      }
    ]
  })
}

resource "aws_route53_key_signing_key" "this" {
  hosted_zone_id             = aws_route53_zone.public.id
  key_management_service_arn = aws_kms_key.dnssec.arn
  name                       = "example"
}

resource "aws_route53_hosted_zone_dnssec" "this" {
  hosted_zone_id = aws_route53_key_signing_key.this.hosted_zone_id
  depends_on     = [aws_route53_key_signing_key.this]
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_key_signing_key.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_hosted_zone_dnssec.html.markdown
# Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec-cmk-requirements.html
# Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html
```

## 7. Delegation sets and Resolver

A delegation set gives several public zones identical NS; it conflicts with private zones. Resolver
resources document an optional `region` on the resource page
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_endpoint.html.markdown);
the region guide does not classify Resolver. The provider doc does not state a minimum number of `ip_address` blocks (unverified).

```hcl
resource "aws_route53_delegation_set" "shared" {
  reference_name = "shared"
}
resource "aws_route53_zone" "a" {
  name              = "a.example.com"
  delegation_set_id = aws_route53_delegation_set.shared.id
}

resource "aws_route53_resolver_endpoint" "outbound" {
  name               = "outbound"
  direction          = "OUTBOUND"
  security_group_ids = [aws_security_group.resolver.id]
  ip_address { subnet_id = aws_subnet.a.id }
  ip_address { subnet_id = aws_subnet.b.id }
}

resource "aws_route53_resolver_rule" "fwd" {
  domain_name          = "corp.example.com"
  rule_type            = "FORWARD"
  resolver_endpoint_id = aws_route53_resolver_endpoint.outbound.id
  target_ip { ip = "10.0.0.10" }
}

resource "aws_route53_resolver_rule_association" "fwd" {
  resolver_rule_id = aws_route53_resolver_rule.fwd.id
  vpc_id           = aws_vpc.main.id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_delegation_set.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_endpoint.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_rule.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_rule_association.html.markdown
```
