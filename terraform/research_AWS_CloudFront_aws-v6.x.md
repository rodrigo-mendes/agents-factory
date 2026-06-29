# Terraform AWS CloudFront — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - CloudFront"
Cloud_Provider: "AWS"
Target_Service: "CloudFront (CDN)"
Terraform_Version: "1.9"
Provider_Version: "aws v6.x (latest: 6.47.0, published 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
CloudFront_Distribution_Resource: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_distribution"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-28"
Domain_Complexity: "Complex"
Integration_Partners: "S3, ACM, Route53, WAF, CloudWatch, IAM"
Use_Modules: true
Use_Workspaces: false
```

---

## Executive Summary

Amazon CloudFront is AWS's globally distributed CDN delivering static and dynamic content through 600+ edge locations. It functions as a reverse proxy cache with routing, security (WAF, Shield, OAC), edge compute (CloudFront Functions, Lambda@Edge), and traffic management (origin failover, geo-restrictions, signed URLs). Terraform's `aws_cloudfront_distribution` resource provides complete lifecycle management of distributions, with supporting resources for cache policies, origin request policies, response headers policies, OAC, and CloudFront Functions.

The Terraform AWS provider v6.x (published 2026-05-28) introduces critical changes: `forwarded_values` in cache behaviors is **deprecated** — all new configurations must use `cache_policy_id` and `origin_request_policy_id` instead. New resource types added include `aws_cloudfront_vpc_origin`, `aws_cloudfront_connection_function`, `aws_cloudfront_multitenant_distribution`, `aws_cloudfront_distribution_tenant`, `aws_cloudfront_anycast_ip_list`, and `aws_cloudfront_trust_store`. Viewer mTLS and gRPC support are now natively available on distributions. Standard logging v2 now routes through CloudWatch delivery instead of direct S3 bucket grants.

Domain complexity is **Complex** due to: cross-resource security dependencies (OAC → S3 bucket policy, ACM → us-east-1 constraint, WAF → Global scope), multi-layer caching architecture (edge location → regional edge cache → optional Origin Shield), security-critical access patterns (signed URLs/cookies, private content), and compliance requirements (HTTPS enforcement, encryption in transit, geo-restrictions). State management is critical as CloudFront distributions take up to 15 minutes to deploy and Terraform blocks resource deletion during `InProgress` status.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

#### Pattern: Terraform Configuration Block

- **Why**: Enforces exact provider and Terraform version contracts; prevents drift from provider API changes introduced in v6.x
- **Code**:
```hcl
terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/cloudfront/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [Terraform Settings Block](https://developer.hashicorp.com/terraform/language/settings)

---

#### Pattern: Provider Configuration with IAM Role (No Hardcoded Credentials)

- **Why**: CloudFront is a Global service — credentials must NEVER be hardcoded; assume_role isolates blast radius per environment; `default_tags` enforces compliance tagging across all resources
- **Code**:
```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "terraform-cloudfront-deploy"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
      Service     = "cloudfront"
    }
  }
}

# ACM certificates for CloudFront MUST be in us-east-1 regardless of origin region
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "terraform-cloudfront-acm"
  }
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [AWS Provider Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#provider-configuration)

---

#### Pattern: Origin Access Control (OAC) for S3 Origins

- **Why**: OAC is the mandatory replacement for legacy OAI. Without OAC, S3 bucket must be publicly accessible — bypassing CloudFront WAF, geo-restrictions, and signed URL enforcement. OAC uses SigV4 signing and supports SSE-KMS encrypted objects (OAI does NOT).
- **Code**:
```hcl
resource "aws_cloudfront_origin_access_control" "s3_oac" {
  name                              = "${var.project}-${var.environment}-s3-oac"
  description                       = "OAC for ${var.project} S3 origin - ${var.environment}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# S3 bucket policy granting CloudFront access via OAC
data "aws_iam_policy_document" "cloudfront_s3_policy" {
  statement {
    sid    = "AllowCloudFrontServicePrincipalReadOnly"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.origin.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "origin" {
  bucket = aws_s3_bucket.origin.id
  policy = data.aws_iam_policy_document.cloudfront_s3_policy.json

  depends_on = [aws_s3_bucket_public_access_block.origin]
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_cloudfront_origin_access_control](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_origin_access_control)

---

#### Pattern: HTTPS Enforcement (Viewer + Origin Protocol)

- **Why**: HTTP exposes content in transit; CloudFront must enforce HTTPS for both viewer-to-CloudFront (redirect-to-https or https-only) and CloudFront-to-origin (https-only with TLS 1.2+); TLSv1.2_2021 is the current security policy best practice
- **Code**:
```hcl
# In aws_cloudfront_distribution
default_cache_behavior {
  viewer_protocol_policy = "redirect-to-https"  # Never "allow-all"
  # ... other config
}

viewer_certificate {
  acm_certificate_arn      = data.aws_acm_certificate.main.arn
  ssl_support_method       = "sni-only"           # Never "vip" (dedicated IP, extra cost)
  minimum_protocol_version = "TLSv1.2_2021"       # Current best practice
}

# For custom origins: enforce HTTPS-only with TLS 1.2+
origin {
  domain_name = var.alb_dns_name
  origin_id   = "alb-origin"

  custom_origin_config {
    http_port              = 80
    https_port             = 443
    origin_protocol_policy = "https-only"         # Never "http-only" or "match-viewer" in prod
    origin_ssl_protocols   = ["TLSv1.2"]          # Never SSLv3, TLSv1, TLSv1.1
  }
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [Viewer Certificate Arguments](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_distribution#viewer-certificate-arguments)

---

#### Pattern: WAF Web ACL Association

- **Why**: CloudFront without WAF is exposed to L7 DDoS, SQL injection, XSS, and bot abuse. WAFv2 ACL must be in `us-east-1` (Global) for CloudFront; use the ACL ARN (not ID) for WAFv2.
- **Code**:
```hcl
resource "aws_wafv2_web_acl" "cloudfront" {
  provider    = aws.us_east_1
  name        = "${var.project}-${var.environment}-cloudfront-waf"
  scope       = "CLOUDFRONT"  # Must be CLOUDFRONT for use with CloudFront
  description = "WAF ACL for CloudFront distribution"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project}-${var.environment}-cloudfront-waf"
    sampled_requests_enabled   = true
  }
}

# In aws_cloudfront_distribution
resource "aws_cloudfront_distribution" "main" {
  web_acl_id = aws_wafv2_web_acl.cloudfront.arn  # Use ARN for WAFv2
  # ...
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_cloudfront_distribution web_acl_id](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_distribution#web_acl_id)

---

#### Pattern: Cache Policy (Replaces Deprecated forwarded_values)

- **Why**: `forwarded_values` is **deprecated** in provider v6.x. `cache_policy_id` provides reusable, named cache policies and cleaner separation of cache key vs. origin request concerns. Fewer items in cache key = higher cache-hit ratio.
- **Code**:
```hcl
# Custom cache policy for static assets
resource "aws_cloudfront_cache_policy" "static_assets" {
  name        = "${var.project}-static-assets-policy"
  comment     = "Static assets: long TTL, no cookies, no query strings"
  default_ttl = 86400    # 1 day
  max_ttl     = 31536000 # 1 year
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}

# AWS Managed cache policy IDs (no resource needed)
locals {
  # CachingOptimized managed policy
  caching_optimized_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  # CachingDisabled managed policy (for API/dynamic)
  caching_disabled_policy_id  = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
}

# In cache behavior
default_cache_behavior {
  cache_policy_id        = aws_cloudfront_cache_policy.static_assets.id
  # OR use managed: cache_policy_id = local.caching_optimized_policy_id
  allowed_methods        = ["GET", "HEAD"]
  cached_methods         = ["GET", "HEAD"]
  target_origin_id       = local.s3_origin_id
  viewer_protocol_policy = "redirect-to-https"
  compress               = true
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_cloudfront_cache_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_cache_policy)

---

#### Pattern: S3 Origin — Block Public Access + Private Bucket

- **Why**: The S3 origin bucket must remain private; OAC handles authenticated CloudFront-to-S3 access. Disabling Block Public Access creates an unintended public data exposure vector bypassing all CloudFront controls.
- **Code**:
```hcl
resource "aws_s3_bucket" "origin" {
  bucket = "${var.project}-${var.environment}-cloudfront-origin"
}

resource "aws_s3_bucket_public_access_block" "origin" {
  bucket = aws_s3_bucket.origin.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "origin" {
  bucket = aws_s3_bucket.origin.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "origin" {
  bucket = aws_s3_bucket.origin.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = true
  }
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [S3 Block Public Access](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block)

---

#### Pattern: Destroy Protection via lifecycle

- **Why**: CloudFront distributions back production traffic — accidental `terraform destroy` causes immediate service outage; `prevent_destroy` blocks the operation at plan time
- **Code**:
```hcl
resource "aws_cloudfront_distribution" "main" {
  # ... configuration ...

  lifecycle {
    prevent_destroy = true  # Blocks accidental terraform destroy in production

    # Ensure new distribution deploys before old one is destroyed in replacement
    create_before_destroy = false
  }

  # retain_on_delete disables (rather than destroys) the distribution on tf destroy
  # Use in non-prod to avoid the 15-minute deployment wait
  retain_on_delete     = false
  wait_for_deployment  = true  # Wait for Deployed status before marking apply complete
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [lifecycle Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle)

---

#### Pattern: Variable Validation & Type Safety

- **Why**: Prevents invalid configurations at plan time — CloudFront distributions take 15 minutes to deploy; catching errors before apply saves significant time
- **Code**:
```hcl
variable "price_class" {
  type        = string
  description = "CloudFront price class controlling edge location coverage"
  default     = "PriceClass_100"

  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.price_class)
    error_message = "price_class must be PriceClass_100, PriceClass_200, or PriceClass_All."
  }
}

variable "minimum_protocol_version" {
  type        = string
  description = "Minimum TLS protocol version for viewer connections"
  default     = "TLSv1.2_2021"

  validation {
    condition     = contains(["TLSv1.2_2019", "TLSv1.2_2021", "TLSv1.2_2022_q3"], var.minimum_protocol_version)
    error_message = "minimum_protocol_version must be TLSv1.2_2019, TLSv1.2_2021, or TLSv1.2_2022_q3."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "geo_restriction_locations" {
  type        = list(string)
  description = "ISO 3166-1-alpha-2 country codes for geo-restriction"
  default     = []

  validation {
    condition     = length(var.geo_restriction_locations) == 0 || alltrue([for c in var.geo_restriction_locations : length(c) == 2])
    error_message = "All geo_restriction_locations must be 2-character ISO 3166-1-alpha-2 country codes."
  }
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [Custom Validation Rules](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

### ⚠️ Conditional Patterns

#### Decision: OAI vs. OAC for S3 Origin Authentication

| Option | Optimizes | Sacrifices | SSE-KMS | Opt-in Regions | PUT/DELETE |
|--------|-----------|------------|---------|----------------|------------|
| **OAC** (recommended) | Security, full S3 feature parity | None | ✅ Yes | ✅ Yes | ✅ Yes |
| **OAI** (legacy) | Backward compatibility | Modern features | ❌ No | ❌ No | ❌ No |

- **When**: Always use OAC for new configurations; migrate OAI to OAC for existing distributions
- **Agent**: "Ask user: Are you migrating from an existing OAI setup? If yes, I'll generate OAC migration steps including S3 bucket policy update."
- **Source**: [Restricting access to S3](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)

---

#### Decision: Cache Policy vs. forwarded_values

| Option | Status | Optimizes | Sacrifices | Reusability |
|--------|--------|-----------|------------|-------------|
| **cache_policy_id** | ✅ Current | Reusability, separation of concerns | Learning curve | ✅ Shared across behaviors |
| **forwarded_values** | ⚠️ Deprecated | Inline simplicity for single-resource configs | Future compatibility | ❌ Inline only |

- **When**: Always use `cache_policy_id` for new configurations in provider v6.x; `forwarded_values` still works but is deprecated
- **Agent**: "Ask user: Are you migrating from existing forwarded_values configuration? If yes, I'll generate equivalent cache_policy + origin_request_policy resources."
- **Source**: [cache_policy_id argument](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_distribution#cache_policy_id)

---

#### Decision: CloudFront Functions vs. Lambda@Edge

| Option | Exec Location | Max Duration | Network Access | Code Size | Event Types | Cost |
|--------|--------------|--------------|----------------|-----------|-------------|------|
| **CloudFront Functions** | 600+ edge locations | 1ms | ❌ No | 10 KB | viewer-request, viewer-response | Lower (~$0.10/M) |
| **Lambda@Edge** | 13 regional edge caches | 5s (viewer), 30s (origin) | ✅ Yes | 1 MB / 50 MB | All 4 events | Higher (~$0.60/M) |

- **When**: CloudFront Functions for URL rewrites, header manipulation, simple auth, A/B routing; Lambda@Edge for dynamic origin selection, external API calls, auth token validation, complex transformations
- **Agent**: "Ask user: Does your edge logic require network calls (API/database)? If yes → Lambda@Edge. Pure header/URL manipulation? → CloudFront Functions."
- **Source**: [CloudFront Functions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-functions.html)

---

#### Decision: Origin Shield Enablement

| Option | Optimizes | Sacrifices | When to Use |
|--------|-----------|------------|-------------|
| **Origin Shield enabled** | Cache hit ratio, origin protection, cost at high scale | Extra hop latency (~1ms), per-request charge | Geographically dispersed viewers, expensive origin operations, multi-CDN |
| **Origin Shield disabled** | Simplicity, no extra latency/cost | Higher origin load for dispersed traffic | Viewers concentrated near origin region |

- **Agent**: "Ask user: Are your viewers globally distributed? Is origin request cost significant (image transforms, video packaging)? If yes to either → enable Origin Shield."
- **Code**:
```hcl
origin {
  domain_name = aws_s3_bucket.origin.bucket_regional_domain_name
  origin_id   = local.s3_origin_id

  origin_access_control_id = aws_cloudfront_origin_access_control.s3_oac.id

  origin_shield {
    enabled              = var.enable_origin_shield
    origin_shield_region = var.origin_shield_region  # e.g., "us-east-1" — closest to origin
  }
}
```
- **Source**: [Origin Shield](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html)

---

#### Decision: Price Class (Edge Location Coverage)

| Option | Coverage | Cost Relative | Best When |
|--------|----------|--------------|-----------|
| **PriceClass_All** | All edge locations globally | Highest | Global audience, latency-critical |
| **PriceClass_200** | US, Canada, Europe, Asia, Middle East, Africa | Medium | Regional (excluding South America, some Asia) |
| **PriceClass_100** | US, Canada, Europe only | Lowest | Audience limited to North America + Europe |

- **Agent**: "Ask user: Where is your primary audience located? PriceClass_100 for US/Europe only, PriceClass_200 adds most Asia/Middle East, PriceClass_All for true global delivery."
- **Source**: [CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/)

---

#### Decision: Continuous Deployment (Blue-Green Testing)

| Option | Risk | Rollback | Complexity |
|--------|------|----------|------------|
| **Direct distribution update** | All traffic affected simultaneously | Manual rollback | Simple |
| **Continuous deployment policy** | Staged traffic split (staging → production) | Promote or revert staging | Complex — requires two distributions |

- **Agent**: "Ask user: Is this a high-traffic production distribution where configuration changes need validation before full rollout? If yes → continuous deployment policy."
- **Source**: [aws_cloudfront_continuous_deployment_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_continuous_deployment_policy)

---

#### Decision: VPC Origins vs. Public Custom Origin

| Option | Security | Complexity | When |
|--------|----------|------------|------|
| **VPC Origin** | Private — no internet exposure | Requires aws_cloudfront_vpc_origin resource | ALB/NLB/EC2 in private VPC, zero-trust |
| **Public custom origin** | Origin must have public endpoint | Simpler | Legacy setups, public ALBs with SG restrictions |

- **Code**:
```hcl
resource "aws_cloudfront_vpc_origin" "alb" {
  vpc_origin_endpoint_config {
    name                   = "${var.project}-vpc-origin"
    arn                    = aws_lb.internal.arn
    http_port              = 80
    https_port             = 443
    origin_protocol_policy = "https-only"

    origin_ssl_protocols {
      items    = ["TLSv1.2"]
      quantity = 1
    }
  }
}

# In distribution origin block:
origin {
  domain_name = aws_lb.internal.dns_name
  origin_id   = "alb-vpc-origin"

  vpc_origin_config {
    vpc_origin_id = aws_cloudfront_vpc_origin.alb.id
  }
}
```
- **Source**: [aws_cloudfront_vpc_origin](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_vpc_origin)

---

### 🚫 Forbidden Patterns

#### Anti-Pattern: Legacy Origin Access Identity (OAI)

```hcl
# DON'T — Legacy OAI, does not support SSE-KMS or PUT/DELETE
resource "aws_cloudfront_origin_access_identity" "legacy" {
  comment = "legacy OAI"
}

origin {
  s3_origin_config {
    origin_access_identity = aws_cloudfront_origin_access_identity.legacy.cloudfront_access_identity_path
  }
}
```

- **Why**: OAI does not support SSE-KMS encrypted S3 objects, AWS opt-in regions, or S3 PUT/DELETE operations. AWS recommends migrating all OAI to OAC.
- **Instead**:
```hcl
# DO — OAC with SigV4
resource "aws_cloudfront_origin_access_control" "s3_oac" {
  name                              = "s3-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

origin {
  origin_access_control_id = aws_cloudfront_origin_access_control.s3_oac.id
  # No s3_origin_config block needed
}
```
- **Impact**: Security regression, lack of SSE-KMS support, AWS deprecation risk
- **Severity**: HIGH
- **Source**: [Migrating from OAI to OAC](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)

---

#### Anti-Pattern: Public S3 Bucket as CloudFront Origin

```hcl
# DON'T
resource "aws_s3_bucket_public_access_block" "origin" {
  bucket = aws_s3_bucket.origin.id

  block_public_acls       = false  # NEVER
  block_public_policy     = false  # NEVER
  ignore_public_acls      = false  # NEVER
  restrict_public_buckets = false  # NEVER
}
```

- **Why**: Public bucket bypasses all CloudFront access controls (WAF, geo-restrictions, signed URLs). Content accessible directly from S3, exposing data at S3 transfer rates without CDN benefits.
- **Instead**:
```hcl
# DO — All flags true + OAC for authenticated access
resource "aws_s3_bucket_public_access_block" "origin" {
  bucket = aws_s3_bucket.origin.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```
- **Impact**: CRITICAL — Data exfiltration, WAF bypass, geo-restriction bypass
- **Severity**: CRITICAL
- **Source**: [S3 Block Public Access](https://docs.aws.amazon.com/s3/latest/userguide/access-control-block-public-access.html)

---

#### Anti-Pattern: HTTP Allowed (viewer_protocol_policy = "allow-all")

```hcl
# DON'T
default_cache_behavior {
  viewer_protocol_policy = "allow-all"  # NEVER in production
}
```

- **Why**: HTTP traffic is unencrypted; enables man-in-the-middle attacks, credential interception, and cookie theft. PCI DSS, HIPAA, and SOC2 all require HTTPS for data in transit.
- **Instead**:
```hcl
# DO
default_cache_behavior {
  viewer_protocol_policy = "redirect-to-https"  # Redirects HTTP → HTTPS
  # OR
  viewer_protocol_policy = "https-only"  # Returns 403 for HTTP requests
}
```
- **Impact**: CRITICAL — Data in transit exposure, compliance violation
- **Severity**: CRITICAL
- **Source**: [Viewer Protocol Policy](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesViewerProtocolPolicy)

---

#### Anti-Pattern: Missing WAF Association

```hcl
# DON'T — Distribution without WAF protection
resource "aws_cloudfront_distribution" "main" {
  # web_acl_id omitted — no WAF protection
  enabled = true
  # ...
}
```

- **Why**: Unprotected distributions are exposed to L7 DDoS, SQL injection, XSS, automated scanning, and bot abuse. CloudFront rate limits do not substitute for WAF rule evaluation.
- **Instead**:
```hcl
# DO
resource "aws_cloudfront_distribution" "main" {
  web_acl_id = aws_wafv2_web_acl.cloudfront.arn  # WAFv2 ARN required
  # ...
}
```
- **Impact**: HIGH — Application-layer attack exposure
- **Severity**: HIGH
- **Source**: [AWS WAF with CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-awswaf.html)

---

#### Anti-Pattern: Deprecated forwarded_values in Provider v6.x

```hcl
# DON'T — forwarded_values is deprecated in provider v6.x
default_cache_behavior {
  forwarded_values {
    query_string = false
    cookies {
      forward = "none"
    }
  }
}
```

- **Why**: `forwarded_values` is deprecated; will be removed in a future provider version. Mixing `forwarded_values` with `cache_policy_id` is not allowed and causes a provider error.
- **Instead**:
```hcl
# DO — Use cache_policy_id (and optionally origin_request_policy_id)
default_cache_behavior {
  cache_policy_id          = aws_cloudfront_cache_policy.static.id
  origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer.id
}
```
- **Impact**: MEDIUM — Future breaking change, provider upgrade blocker
- **Severity**: MEDIUM
- **Source**: [cache_policy_id docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_distribution#cache_policy_id)

---

#### Anti-Pattern: ACM Certificate in Wrong Region

```hcl
# DON'T — ACM certificate in region other than us-east-1
resource "aws_acm_certificate" "cloudfront" {
  # provider = aws  # Using default region (e.g., us-west-2)
  domain_name       = var.domain_name
  validation_method = "DNS"
}

viewer_certificate {
  acm_certificate_arn = aws_acm_certificate.cloudfront.arn  # WILL FAIL
}
```

- **Why**: CloudFront requires ACM certificates to be in `us-east-1` (Global). Certificates from other regions are rejected by the CloudFront API.
- **Instead**:
```hcl
# DO — Explicitly use us-east-1 provider alias
resource "aws_acm_certificate" "cloudfront" {
  provider          = aws.us_east_1  # Explicit alias required
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}
```
- **Impact**: HIGH — Distribution creation fails; plan succeeds but apply errors
- **Severity**: HIGH
- **Source**: [Using HTTPS with CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html)

---

#### Anti-Pattern: No Geo Restrictions with Default Allow (When Required)

```hcl
# DON'T (for compliance-mandated geographic restrictions)
restrictions {
  geo_restriction {
    restriction_type = "none"  # No restrictions — all countries can access
  }
}
```

- **Why**: If distribution serves content with export controls, compliance requirements, or licensing geographic limitations, `restriction_type = "none"` creates a compliance violation.
- **Instead**:
```hcl
# DO — Explicitly define restriction requirements
restrictions {
  geo_restriction {
    restriction_type = var.geo_restriction_type  # "whitelist" or "blacklist"
    locations        = var.geo_restriction_locations  # e.g., ["US", "CA", "GB"]
  }
}
```
- **Impact**: MEDIUM — Compliance violation, export control breach
- **Severity**: MEDIUM (HIGH for regulated industries)
- **Source**: [Geo Restriction](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html)

---

#### Anti-Pattern: Missing Resource Tagging

```hcl
# DON'T
resource "aws_cloudfront_distribution" "main" {
  # tags block omitted
}
```

- **Why**: CloudFront distribution costs are significant at scale (~$0.01/10,000 HTTPS requests). Without tags, cost attribution, compliance auditing, and automation targeting are impossible.
- **Instead**:
```hcl
# DO — Tags via default_tags in provider + resource-level override
resource "aws_cloudfront_distribution" "main" {
  tags = merge(
    var.tags,
    {
      Name        = "${var.project}-${var.environment}-distribution"
      Environment = var.environment
    }
  )
}
```
- **Impact**: HIGH — Cost blindness, compliance gaps
- **Severity**: HIGH
- **Source**: [AWS Tagging Strategy](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)

---

## State Management Deep Dive

### Local Development State
```hcl
# Use only for learning/solo development
terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  # No backend block = local state
}
```
- **Risk**: No state locking, no sharing, single point of failure
- **When**: Solo development, learning, temporary test distributions only

---

### Production Remote State (S3 + DynamoDB)

```hcl
# State backend infrastructure (bootstrap — run once with local state, then migrate)
resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-org-terraform-state-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket                  = aws_s3_bucket.terraform_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.terraform_state.arn
  }

  tags = {
    Name      = "terraform-locks"
    ManagedBy = "terraform"
  }
}

# CloudFront distribution backend config
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state-123456789012"
    key            = "prod/cloudfront/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/mrk-abc123"
    dynamodb_table = "terraform-locks"
  }
}
```

---

### State File Sensitivity Handling

CloudFront state files contain: distribution IDs, domain names, origin configurations, ACM certificate ARNs. Mark sensitive outputs:

```hcl
output "distribution_id" {
  value       = aws_cloudfront_distribution.main.id
  description = "CloudFront distribution ID for cache invalidation"
}

output "distribution_domain_name" {
  value       = aws_cloudfront_distribution.main.domain_name
  description = "CloudFront domain name for DNS CNAME"
}

output "distribution_arn" {
  value       = aws_cloudfront_distribution.main.arn
  description = "CloudFront distribution ARN (needed for WAF and S3 OAC policy)"
}

# Restrict state bucket access to deployment service accounts only
data "aws_iam_policy_document" "terraform_state_policy" {
  statement {
    sid    = "DenyAllExceptTerraformRole"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions   = ["s3:*"]
    resources = [
      aws_s3_bucket.terraform_state.arn,
      "${aws_s3_bucket.terraform_state.arn}/*",
    ]

    condition {
      test     = "ArnNotLike"
      variable = "aws:PrincipalArn"
      values   = ["arn:aws:iam::*:role/TerraformDeployRole"]
    }
  }
}
```

---

## Module Architecture

### Standard Module Structure
```
modules/
└── cloudfront/
    ├── main.tf            # aws_cloudfront_distribution + supporting resources
    ├── variables.tf       # Input variables with validation
    ├── outputs.tf         # Distribution ID, domain name, ARN, hosted_zone_id
    ├── versions.tf        # terraform + required_providers constraints
    ├── oac.tf             # aws_cloudfront_origin_access_control
    ├── cache_policies.tf  # aws_cloudfront_cache_policy resources
    ├── waf.tf             # aws_wafv2_web_acl (us-east-1 provider)
    └── README.md
```

### Module Definition

```hcl
# modules/cloudfront/variables.tf
variable "project" {
  type        = string
  description = "Project name prefix for resource naming"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project))
    error_message = "project must be lowercase alphanumeric with hyphens only."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "domain_names" {
  type        = list(string)
  description = "Custom domain names (CNAMEs) for the distribution"
  default     = []
}

variable "acm_certificate_arn" {
  type        = string
  description = "ACM certificate ARN in us-east-1 for HTTPS (required if domain_names set)"
  default     = null
}

variable "s3_origin_bucket_arn" {
  type        = string
  description = "ARN of the S3 bucket to use as origin"
}

variable "s3_origin_bucket_regional_domain_name" {
  type        = string
  description = "Regional domain name of the S3 bucket (use bucket_regional_domain_name attribute)"
}

variable "price_class" {
  type    = string
  default = "PriceClass_100"

  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.price_class)
    error_message = "price_class must be PriceClass_100, PriceClass_200, or PriceClass_All."
  }
}

variable "enable_waf" {
  type        = bool
  description = "Whether to create and attach a WAFv2 web ACL"
  default     = true
}

variable "geo_restriction_type" {
  type    = string
  default = "none"

  validation {
    condition     = contains(["none", "whitelist", "blacklist"], var.geo_restriction_type)
    error_message = "geo_restriction_type must be none, whitelist, or blacklist."
  }
}

variable "geo_restriction_locations" {
  type    = list(string)
  default = []
}

variable "tags" {
  type        = map(string)
  description = "Additional resource tags"
  default     = {}
}

# modules/cloudfront/outputs.tf
output "distribution_id" {
  value       = aws_cloudfront_distribution.main.id
  description = "CloudFront distribution ID"
}

output "distribution_arn" {
  value       = aws_cloudfront_distribution.main.arn
  description = "CloudFront distribution ARN"
}

output "distribution_domain_name" {
  value       = aws_cloudfront_distribution.main.domain_name
  description = "CloudFront domain name (use for Route53 ALIAS)"
}

output "distribution_hosted_zone_id" {
  value       = aws_cloudfront_distribution.main.hosted_zone_id
  description = "CloudFront hosted zone ID for Route53 ALIAS records (always Z2FDTNDATAQYW2)"
}

output "oac_id" {
  value       = aws_cloudfront_origin_access_control.s3_oac.id
  description = "OAC ID — use in S3 bucket policy condition"
}
```

---

## Integration Patterns

### Integration: Terraform ↔ S3 (Static Website / Asset Origin)

- **Pattern**: S3 as private bucket origin with OAC
- **Resources**: `aws_s3_bucket`, `aws_s3_bucket_public_access_block`, `aws_cloudfront_origin_access_control`, `aws_s3_bucket_policy`
- **Data Sources**: `data.aws_iam_policy_document`

```hcl
locals {
  s3_origin_id = "s3-static-origin"
}

resource "aws_s3_bucket" "origin" {
  bucket = "${var.project}-${var.environment}-origin"
  tags   = var.tags
}

resource "aws_s3_bucket_public_access_block" "origin" {
  bucket                  = aws_s3_bucket.origin.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "s3_oac" {
  name                              = "${var.project}-s3-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_iam_policy_document" "s3_cloudfront" {
  statement {
    sid    = "AllowCloudFrontServicePrincipalRead"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.origin.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "origin" {
  bucket     = aws_s3_bucket.origin.id
  policy     = data.aws_iam_policy_document.s3_cloudfront.json
  depends_on = [aws_s3_bucket_public_access_block.origin]
}

resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name              = aws_s3_bucket.origin.bucket_regional_domain_name
    origin_id                = local.s3_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.s3_oac.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    target_origin_id       = local.s3_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized managed
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = var.tags
}
```

- **Versions**:

| Resource | Min Provider | Max Provider |
|----------|-------------|-------------|
| `aws_cloudfront_origin_access_control` | ~> 4.0 | ~> 6.0 |
| `aws_cloudfront_distribution` | ~> 2.0 | ~> 6.0 |

- **Issues**: OAC `depends_on` S3 bucket policy — circular dependency avoided by Terraform ordering (distribution ARN needed before bucket policy); CloudFront distribution ARN is available as soon as resource is created (before `Deployed` status)
- **Source**: [aws_cloudfront_origin_access_control](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_origin_access_control)

---

### Integration: Terraform ↔ ACM (SSL/TLS Certificate)

- **Pattern**: DNS-validated ACM certificate in us-east-1
- **Resources**: `aws_acm_certificate`, `aws_acm_certificate_validation`, `aws_route53_record` (for validation)

```hcl
resource "aws_acm_certificate" "cloudfront" {
  provider          = aws.us_east_1  # MUST be us-east-1 for CloudFront
  domain_name       = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true  # Prevents downtime during certificate renewal
  }

  tags = var.tags
}

data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

resource "aws_route53_record" "acm_validation" {
  for_each = {
    for dvo in aws_acm_certificate.cloudfront.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id = data.aws_route53_zone.main.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "cloudfront" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.cloudfront.arn
  validation_record_fqdns = [for record in aws_route53_record.acm_validation : record.fqdn]
}
```

- **Issues**: Certificate validation can take 5–30 minutes; `aws_acm_certificate_validation` waits for DNS propagation before returning — plan accordingly in CI/CD pipelines
- **Source**: [aws_acm_certificate](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate)

---

### Integration: Terraform ↔ Route53 (Custom Domain DNS)

- **Pattern**: Route53 ALIAS record pointing to CloudFront distribution
- **Resources**: `aws_route53_record` with `alias` block

```hcl
data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

resource "aws_route53_record" "cloudfront_a" {
  for_each = toset(aws_cloudfront_distribution.main.aliases)

  zone_id = data.aws_route53_zone.main.zone_id
  name    = each.value
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id  # Always Z2FDTNDATAQYW2
    evaluate_target_health = false  # CloudFront does not support health check evaluation for ALIAS
  }
}

resource "aws_route53_record" "cloudfront_aaaa" {
  for_each = toset(aws_cloudfront_distribution.main.aliases)

  zone_id = data.aws_route53_zone.main.zone_id
  name    = each.value
  type    = "AAAA"  # IPv6 — only add if is_ipv6_enabled = true

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}
```

- **Issues**: `evaluate_target_health = false` is required for CloudFront ALIAS records (CloudFront health evaluation not supported); use `for_each = toset(...)` to create one record per alias
- **Source**: [Route53 Alias Records for CloudFront](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-cloudfront-distribution.html)

---

### Integration: Terraform ↔ WAF (Web Application Firewall)

- **Pattern**: WAFv2 CLOUDFRONT-scope Web ACL attached to distribution
- **Resources**: `aws_wafv2_web_acl` (us-east-1 provider alias)

```hcl
resource "aws_wafv2_web_acl" "cloudfront" {
  provider    = aws.us_east_1  # MUST be us-east-1 for CLOUDFRONT scope
  name        = "${var.project}-${var.environment}-cf-waf"
  scope       = "CLOUDFRONT"
  description = "WAF for CloudFront distribution"

  default_action {
    allow {}
  }

  # AWS Managed Rules — Common Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSCommonRules"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules — Known Bad Inputs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSKnownBadInputs"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project}-${var.environment}-cf-waf"
    sampled_requests_enabled   = true
  }

  tags = var.tags
}

# In distribution:
resource "aws_cloudfront_distribution" "main" {
  web_acl_id = aws_wafv2_web_acl.cloudfront.arn  # ARN for WAFv2
  # ...
}
```

- **Issues**: WAFv2 web ACL `scope = "CLOUDFRONT"` must be created in `us-east-1` even if your primary region is different; WAF charges apply per rule evaluated per request (~$0.60/million requests for managed rules)
- **Source**: [WAFv2 Web ACL](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl)

---

### Integration: Terraform ↔ CloudWatch (Monitoring & Alerting)

- **Pattern**: CloudWatch metrics + alarms for distribution health; Standard logging v2 via CloudWatch delivery
- **Resources**: `aws_cloudwatch_metric_alarm`, `aws_cloudwatch_log_delivery_source`, `aws_cloudwatch_log_delivery_destination`, `aws_cloudwatch_log_delivery`

```hcl
# Cache hit ratio alarm
resource "aws_cloudwatch_metric_alarm" "cache_hit_ratio" {
  alarm_name          = "${var.project}-${var.environment}-cf-cache-hit-ratio"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CacheHitRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"  # Alert if cache hit rate drops below 80%
  alarm_description   = "CloudFront cache hit rate below 80%"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DistributionId = aws_cloudfront_distribution.main.id
    Region         = "Global"
  }
}

# 5xx error rate alarm
resource "aws_cloudwatch_metric_alarm" "error_rate_5xx" {
  alarm_name          = "${var.project}-${var.environment}-cf-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5xxErrorRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"  # Alert on >1% 5xx error rate
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DistributionId = aws_cloudfront_distribution.main.id
    Region         = "Global"
  }
}

# Standard logging v2 (new in 2024 — replaces legacy S3 logging grant)
resource "aws_cloudwatch_log_delivery_source" "cloudfront" {
  provider     = aws.us_east_1
  name         = "${var.project}-cloudfront-logs"
  log_type     = "ACCESS_LOGS"
  resource_arn = aws_cloudfront_distribution.main.arn
}

resource "aws_s3_bucket" "cloudfront_logs" {
  bucket        = "${var.project}-${var.environment}-cf-access-logs"
  force_destroy = false
}

resource "aws_cloudwatch_log_delivery_destination" "s3" {
  provider      = aws.us_east_1
  name          = "${var.project}-cloudfront-logs-s3"
  output_format = "parquet"

  delivery_destination_configuration {
    destination_resource_arn = "${aws_s3_bucket.cloudfront_logs.arn}/prefix"
  }
}

resource "aws_cloudwatch_log_delivery" "cloudfront" {
  provider                 = aws.us_east_1
  delivery_source_name     = aws_cloudwatch_log_delivery_source.cloudfront.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.s3.arn

  s3_delivery_configuration {
    suffix_path = "/{DistributionId}/{yyyy}/{MM}/{dd}/{HH}"
  }
}
```

- **Issues**: CloudWatch metrics for CloudFront are only available in `us-east-1` (Global) — `dimensions.Region = "Global"` is required; real-time monitoring requires `aws_cloudfront_monitoring_subscription` resource
- **Source**: [CloudFront CloudWatch Metrics](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/monitoring-using-cloudwatch.html)

---

### Integration: Terraform ↔ IAM (Least-Privilege Deployment Role)

- **Pattern**: Scoped IAM policy for CloudFront Terraform deployment role
- **Resources**: `aws_iam_role`, `aws_iam_policy`, `aws_iam_role_policy_attachment`

```hcl
data "aws_iam_policy_document" "cloudfront_deploy" {
  statement {
    sid    = "CloudFrontDistributionManagement"
    effect = "Allow"
    actions = [
      "cloudfront:CreateDistribution",
      "cloudfront:UpdateDistribution",
      "cloudfront:DeleteDistribution",
      "cloudfront:GetDistribution",
      "cloudfront:GetDistributionConfig",
      "cloudfront:ListDistributions",
      "cloudfront:TagResource",
      "cloudfront:UntagResource",
      "cloudfront:ListTagsForResource",
    ]
    resources = ["*"]  # CloudFront does not support resource-level ARN restrictions for most actions
  }

  statement {
    sid    = "CloudFrontPoliciesAndOAC"
    effect = "Allow"
    actions = [
      "cloudfront:CreateCachePolicy",
      "cloudfront:UpdateCachePolicy",
      "cloudfront:DeleteCachePolicy",
      "cloudfront:GetCachePolicy",
      "cloudfront:CreateOriginAccessControl",
      "cloudfront:UpdateOriginAccessControl",
      "cloudfront:DeleteOriginAccessControl",
      "cloudfront:GetOriginAccessControl",
      "cloudfront:CreateOriginRequestPolicy",
      "cloudfront:UpdateOriginRequestPolicy",
      "cloudfront:DeleteOriginRequestPolicy",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "WAFWebACLForCloudFront"
    effect = "Allow"
    actions = [
      "wafv2:CreateWebACL",
      "wafv2:UpdateWebACL",
      "wafv2:DeleteWebACL",
      "wafv2:GetWebACL",
      "wafv2:ListWebACLs",
      "wafv2:TagResource",
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "wafv2:Scope"
      values   = ["CLOUDFRONT"]
    }
  }
}

resource "aws_iam_policy" "cloudfront_deploy" {
  name        = "${var.project}-terraform-cloudfront-deploy"
  description = "Least-privilege policy for Terraform CloudFront deployment"
  policy      = data.aws_iam_policy_document.cloudfront_deploy.json
}
```

- **Issues**: CloudFront IAM actions do not support resource-level restrictions (most actions require `resources = ["*"]`); scope WAF permissions via condition keys where possible
- **Source**: [CloudFront IAM Actions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/access-control-overview.html)

---

## Executable Verification (CLI Commands)

### Project Init
```bash
terraform init -upgrade
# Expected: Terraform has been successfully initialized!
# ✓ Installed hashicorp/aws v6.x.x
```

### Format & Syntax Validation
```bash
terraform fmt -recursive -check=true
# Expected: Exit code 0 — all files formatted correctly (no output on success)

terraform validate
# Expected: Success! The configuration is valid.
```

### Security Scanning
```bash
# tfsec — CloudFront-specific checks
tfsec . --format sarif --minimum-severity HIGH
# Expected: 0 HIGH/CRITICAL findings on compliant configuration

# checkov — Policy-as-Code
checkov -d . --framework terraform --check CKV_AWS_68,CKV_AWS_86,CKV_AWS_174,CKV_AWS_310 --quiet
# CKV_AWS_68:  CloudFront distribution with WAF enabled
# CKV_AWS_86:  CloudFront distribution access logging enabled
# CKV_AWS_174: CloudFront TLS minimum version TLSv1.2
# CKV_AWS_310: CloudFront distribution origin failover
# Expected: Passed checks: 4, Failed checks: 0
```

### Plan & Dry Run
```bash
terraform plan -out=tfplan -lock=true
# Expected: Plan: X to add, 0 to change, 0 to destroy.

terraform show tfplan
# Expected: Lists aws_cloudfront_distribution, aws_cloudfront_origin_access_control,
#           aws_s3_bucket_policy, aws_wafv2_web_acl, aws_acm_certificate, etc.
```

### Apply with Safeguards
```bash
terraform plan -out=tfplan
terraform apply tfplan
# Expected: Apply complete! CloudFront distribution deployment takes ~15 minutes.
# Note: wait_for_deployment = true causes Terraform to block until status = "Deployed"

terraform state list
# Expected:
# aws_cloudfront_distribution.main
# aws_cloudfront_origin_access_control.s3_oac
# aws_cloudfront_cache_policy.static_assets
# aws_s3_bucket.origin
# aws_s3_bucket_policy.origin
# aws_s3_bucket_public_access_block.origin
# aws_wafv2_web_acl.cloudfront
# aws_acm_certificate.cloudfront
# aws_route53_record.cloudfront_a["mydomain.com"]
```

### Verification
```bash
terraform show
# Expected: Full current state including distribution domain_name and status = "Deployed"

terraform output
# Expected:
# distribution_id           = "EDFDVBD632BHDS5"
# distribution_domain_name  = "d111111abcdef8.cloudfront.net"
# distribution_hosted_zone_id = "Z2FDTNDATAQYW2"
```

### Cache Invalidation (Action Resource)
```bash
# Using the cloudfront_create_invalidation action resource (provider v6.x)
# Or via AWS CLI:
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw distribution_id) \
  --paths "/*"
# Expected: InvalidationBatch with Status "InProgress" → "Completed" in ~60 seconds
```

### Cleanup (Protected in Production)
```bash
# For non-production: remove prevent_destroy lifecycle first, then:
terraform plan -destroy -out=destroy.tfplan
# Expected: Plan: 0 to add, 0 to change, X to destroy.

terraform apply destroy.tfplan
# Note: Distribution is first disabled (status InProgress), then deleted (~15 minutes)
# Expected: Destroy complete!
```

---

## Configuration Validation & Type Safety

```hcl
# variables.tf — Complete type-safe variable definitions

variable "project" {
  type        = string
  description = "Project identifier (lowercase alphanumeric with hyphens)"

  validation {
    condition     = can(regex("^[a-z0-9-]{2,32}$", var.project))
    error_message = "project must be 2-32 lowercase alphanumeric characters with hyphens."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev/staging/prod)"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  type        = string
  description = "Primary AWS region"
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "aws_region must be a valid AWS region code (e.g., us-east-1)."
  }
}

variable "domain_name" {
  type        = string
  description = "Primary custom domain name for CloudFront distribution"
  default     = null

  validation {
    condition = var.domain_name == null || can(regex(
      "^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\\.)+[a-zA-Z]{2,}$",
      var.domain_name
    ))
    error_message = "domain_name must be a valid fully-qualified domain name or null."
  }
}

variable "ttl_default" {
  type        = number
  description = "Default TTL in seconds for cached objects"
  default     = 86400

  validation {
    condition     = var.ttl_default >= 0 && var.ttl_default <= 31536000
    error_message = "ttl_default must be between 0 and 31536000 (1 year)."
  }
}

variable "tags" {
  type        = map(string)
  description = "Resource tags map"
  default     = {}
}
```

---

## Drift Detection & Reconciliation

### Scenario: Distribution Modified via AWS Console

```
Detection: terraform plan output shows drift
```

```bash
# Detect drift
terraform refresh
# Output: Refreshing state... CloudFront distribution changes detected

terraform plan
# Expected: Shows in-place update (~ resource) with console-modified values vs. TF config
# Example drift:
#   ~ resource "aws_cloudfront_distribution" "main" {
#       ~ comment = "Modified via console" -> "Original Terraform comment"

# Recovery: Re-apply Terraform to reconcile
terraform apply  # Reverts console changes to declared state
```

### Scenario: Distribution Created Outside Terraform (Import)

```bash
# Import existing CloudFront distribution
terraform import aws_cloudfront_distribution.main E74FTE3EXAMPLE

# Or using import block (Terraform 1.5+)
# In main.tf:
import {
  to = aws_cloudfront_distribution.main
  id = "E74FTE3EXAMPLE"
}

terraform plan
# Expected: Will show differences between imported state and desired config
# Adjust variables.tf / main.tf to match or accept imported state
```

### Lifecycle Rules for Change Safety

```hcl
resource "aws_cloudfront_cache_policy" "api" {
  name = "${var.project}-api-cache-policy"
  # ...

  lifecycle {
    create_before_destroy = true  # New policy created before old one removed from behaviors
  }
}
```

---

## Secrets & Sensitive Data Management

### Origin Custom Headers (Secret Token)

```hcl
# DO — Retrieve secret from Secrets Manager, inject as custom header
data "aws_secretsmanager_secret_version" "origin_token" {
  secret_id = "/${var.project}/${var.environment}/cloudfront/origin-token"
}

origin {
  domain_name = var.alb_domain_name
  origin_id   = "alb-origin"

  custom_header {
    name  = "X-Origin-Secret"
    value = data.aws_secretsmanager_secret_version.origin_token.secret_string
  }

  custom_origin_config {
    http_port              = 80
    https_port             = 443
    origin_protocol_policy = "https-only"
    origin_ssl_protocols   = ["TLSv1.2"]
  }
}

# Origin validates X-Origin-Secret to reject direct-to-origin requests bypassing CloudFront
```

### Sensitive Outputs & .tfvars

```hcl
# Mark ARNs and configuration details as sensitive where appropriate
output "distribution_id" {
  value     = aws_cloudfront_distribution.main.id
  sensitive = false  # Distribution ID needed for cache invalidation automation
}

# .gitignore — NEVER commit to version control
# terraform.tfvars
# *.tfvars
# .env
```

---

## Testing & Validation Frameworks

### Framework: terraform validate + fmt

```bash
# Purpose: Syntax and type validation
terraform fmt -recursive -check=true && terraform validate
# Expected output: "Success! The configuration is valid."
# Guarantee: Catches type mismatches, missing required arguments, circular dependencies
```

### Framework: tfsec (Security Scanning)

```bash
# Purpose: CloudFront-specific security checks
tfsec . --format json | jq '.results[] | select(.severity == "HIGH" or .severity == "CRITICAL")'
# Expected: Empty array for compliant configuration
# Key checks for CloudFront:
#   aws-cloudfront-enable-waf (no WAF)
#   aws-cloudfront-enable-logging (no access logs)
#   aws-cloudfront-enforce-https (viewer_protocol_policy = allow-all)
#   aws-cloudfront-use-secure-tls-policy (TLS version below 1.2)
```

### Framework: checkov (Policy-as-Code)

```bash
# Purpose: CIS benchmark and AWS security best practices
checkov -d . --framework terraform --output sarif --quiet
# Key CloudFront checks:
#   CKV_AWS_68:  WAF enabled
#   CKV_AWS_86:  Access logging enabled
#   CKV_AWS_174: TLSv1.2 minimum version
#   CKV_AWS_310: Origin failover configured
#   CKV2_AWS_32: Response headers policy with security headers
```

### Framework: Terratest (Integration)

```go
package test

import (
  "testing"
  "fmt"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/gruntwork-io/terratest/modules/aws"
  "github.com/stretchr/testify/assert"
)

func TestCloudFrontDistribution(t *testing.T) {
  t.Parallel()

  opts := &terraform.Options{
    TerraformDir: "../examples/cloudfront-s3",
    Vars: map[string]interface{}{
      "project":     "test",
      "environment": "dev",
      "price_class": "PriceClass_100",
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  distributionID := terraform.Output(t, opts, "distribution_id")
  domainName     := terraform.Output(t, opts, "distribution_domain_name")

  assert.NotEmpty(t, distributionID)
  assert.Contains(t, domainName, "cloudfront.net")

  // Verify distribution is enabled and deployed
  sess := aws.NewAuthenticatedSession("us-east-1")
  // ... assert distribution status = "Deployed" via AWS SDK
  fmt.Printf("Distribution %s deployed at %s\n", distributionID, domainName)
}
```

---

## Production Considerations

### Scenario: High-Traffic Global Distribution

```
Challenge: Cache hit ratio degrades under high write (invalidation) rates
Solution: Segment cache behaviors by TTL tier; batch invalidations
Metrics: CacheHitRate < 80% → alarm; 5xxErrorRate > 1% → alarm; RequestCount for capacity planning
```

```hcl
# Tiered cache behaviors: immutable assets vs. versioned content
ordered_cache_behavior {
  path_pattern     = "/static/immutable/*"  # Content-hashed URLs — never change
  allowed_methods  = ["GET", "HEAD"]
  cached_methods   = ["GET", "HEAD"]
  target_origin_id = local.s3_origin_id

  cache_policy_id        = aws_cloudfront_cache_policy.immutable.id  # max_ttl = 31536000
  viewer_protocol_policy = "redirect-to-https"
  compress               = true
}

resource "aws_cloudfront_cache_policy" "immutable" {
  name        = "${var.project}-immutable"
  min_ttl     = 31536000
  max_ttl     = 31536000
  default_ttl = 31536000

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config      { cookie_behavior       = "none" }
    headers_config      { header_behavior       = "none" }
    query_strings_config { query_string_behavior = "none" }
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}
```

---

### Scenario: Multi-Region / Disaster Recovery

```
Challenge: S3 origin outage in primary region
Solution: Origin group with primary + failover S3 bucket (CRR)
Runbook: Failover is automatic when primary returns 4xx/5xx status codes
```

```hcl
resource "aws_cloudfront_distribution" "main" {
  origin_group {
    origin_id = "s3-origin-group"

    failover_criteria {
      status_codes = [403, 404, 500, 502, 503, 504]
    }

    member { origin_id = "s3-primary" }
    member { origin_id = "s3-failover" }
  }

  origin {
    domain_name              = aws_s3_bucket.primary.bucket_regional_domain_name
    origin_id                = "s3-primary"
    origin_access_control_id = aws_cloudfront_origin_access_control.primary.id
  }

  origin {
    domain_name              = aws_s3_bucket.failover.bucket_regional_domain_name
    origin_id                = "s3-failover"
    origin_access_control_id = aws_cloudfront_origin_access_control.failover.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-origin-group"  # Points to group, not individual origin
    viewer_protocol_policy = "redirect-to-https"
    cache_policy_id        = aws_cloudfront_cache_policy.static_assets.id
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
  }
}
```

---

### Security Checklist

- [ ] OAC used for all S3 origins (no OAI, no public S3 access)
- [ ] WAFv2 Web ACL attached (`web_acl_id` set)
- [ ] `viewer_protocol_policy = "redirect-to-https"` on all behaviors
- [ ] `minimum_protocol_version = "TLSv1.2_2021"` in viewer_certificate
- [ ] `origin_protocol_policy = "https-only"` for all custom origins
- [ ] `origin_ssl_protocols = ["TLSv1.2"]` for custom origins
- [ ] All S3 origins have Block Public Access enabled (all 4 flags = true)
- [ ] State file encryption enabled (S3 + KMS) in backend config
- [ ] ACM certificate in `us-east-1` with `create_before_destroy = true`
- [ ] `prevent_destroy = true` lifecycle in production
- [ ] All resources tagged (via `default_tags` + resource-level)
- [ ] Access logging enabled (V2 via CloudWatch delivery or legacy logging_config)
- [ ] Response headers policy with security headers (HSTS, CSP, X-Frame-Options)
- [ ] CloudWatch alarms for 5xx error rate and cache hit ratio
- [ ] `forwarded_values` NOT used (deprecated in v6.x; use `cache_policy_id`)

---

### Disaster Recovery Runbook

```bash
# 1. State corruption recovery
aws s3api list-object-versions \
  --bucket my-org-terraform-state \
  --prefix prod/cloudfront/terraform.tfstate \
  --query 'Versions[?IsLatest==`false`] | [0].VersionId' \
  --output text

# Restore previous version
aws s3api get-object \
  --bucket my-org-terraform-state \
  --key prod/cloudfront/terraform.tfstate \
  --version-id <previous-version-id> \
  terraform.tfstate.recovered

terraform state push terraform.tfstate.recovered

# 2. Detect drift after manual console changes
terraform refresh
terraform plan  # Shows difference between state and real infrastructure

# 3. Import unmanaged distribution
terraform import aws_cloudfront_distribution.main E74FTE3EXAMPLE

# 4. Force-recreate stuck distribution (retain_on_delete pattern)
# In variables: set retain_on_delete = true, then destroy (disables distribution)
# Manually delete disabled distribution from console
# Remove from state: terraform state rm aws_cloudfront_distribution.main
# Re-create: terraform apply

# 5. Emergency cache invalidation (bypass stale cache)
aws cloudfront create-invalidation \
  --distribution-id EDFDVBD632BHDS5 \
  --paths "/*"
```

---

## Complete Root Module Example

### File Structure
```
cloudfront-example/
├── main.tf
├── variables.tf
├── outputs.tf
├── providers.tf
├── versions.tf
└── terraform.tfvars.example
```

### versions.tf
```hcl
terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/cloudfront/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### providers.tf
```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Project     = var.project
    }
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
  }
}
```

### main.tf
```hcl
locals {
  s3_origin_id = "${var.project}-${var.environment}-s3-origin"
}

# --- S3 Origin Bucket ---
resource "aws_s3_bucket" "origin" {
  bucket = "${var.project}-${var.environment}-cloudfront-origin"
}

resource "aws_s3_bucket_public_access_block" "origin" {
  bucket                  = aws_s3_bucket.origin.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "origin" {
  bucket = aws_s3_bucket.origin.id
  versioning_configuration { status = "Enabled" }
}

# --- OAC ---
resource "aws_cloudfront_origin_access_control" "s3_oac" {
  name                              = "${var.project}-${var.environment}-s3-oac"
  description                       = "OAC for ${var.project} ${var.environment} S3 origin"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# --- ACM Certificate (us-east-1) ---
resource "aws_acm_certificate" "cloudfront" {
  provider          = aws.us_east_1
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# --- Cache Policy ---
resource "aws_cloudfront_cache_policy" "static" {
  name        = "${var.project}-${var.environment}-static"
  comment     = "Static assets cache policy"
  default_ttl = 86400
  max_ttl     = 31536000
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config      { cookie_behavior       = "none" }
    headers_config      { header_behavior       = "none" }
    query_strings_config { query_string_behavior = "none" }
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}

# --- WAF Web ACL (us-east-1) ---
resource "aws_wafv2_web_acl" "cloudfront" {
  provider    = aws.us_east_1
  name        = "${var.project}-${var.environment}-cf-waf"
  scope       = "CLOUDFRONT"
  description = "WAF for ${var.project} ${var.environment} CloudFront"

  default_action { allow {} }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSCommonRules"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project}-${var.environment}-cf-waf"
    sampled_requests_enabled   = true
  }
}

# --- CloudFront Distribution ---
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = var.price_class
  web_acl_id          = aws_wafv2_web_acl.cloudfront.arn
  aliases             = [var.domain_name]

  origin {
    domain_name              = aws_s3_bucket.origin.bucket_regional_domain_name
    origin_id                = local.s3_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.s3_oac.id
  }

  default_cache_behavior {
    target_origin_id       = local.s3_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = aws_cloudfront_cache_policy.static.id
    compress               = true
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"  # SPA fallback
    error_caching_min_ttl = 10
  }

  restrictions {
    geo_restriction {
      restriction_type = var.geo_restriction_type
      locations        = var.geo_restriction_locations
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.cloudfront.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [aws_acm_certificate.cloudfront]
}

# --- S3 Bucket Policy (after distribution created for ARN) ---
data "aws_iam_policy_document" "s3_cloudfront" {
  statement {
    sid    = "AllowCloudFrontOAC"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.origin.arn}/*"]
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "origin" {
  bucket     = aws_s3_bucket.origin.id
  policy     = data.aws_iam_policy_document.s3_cloudfront.json
  depends_on = [aws_s3_bucket_public_access_block.origin]
}

# --- Route53 ALIAS ---
data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

resource "aws_route53_record" "cloudfront" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}
```

### terraform.tfvars.example
```hcl
project                    = "myapp"
environment                = "prod"
aws_region                 = "us-east-1"
account_id                 = "123456789012"
domain_name                = "www.example.com"
price_class                = "PriceClass_100"
geo_restriction_type       = "none"
geo_restriction_locations  = []
```

---

## Reference Implementations

- [Terraform AWS Provider — CloudFront Resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#cloudfront)
- [aws_cloudfront_distribution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_distribution)
- [aws_cloudfront_origin_access_control](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_origin_access_control)
- [aws_cloudfront_cache_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_cache_policy)
- [aws_cloudfront_vpc_origin](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_vpc_origin)
- [AWS CloudFront Developer Guide](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html)
- [CloudFront Best Practices](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/best-practices.html)
- [HashiCorp Terraform AWS Examples](https://github.com/hashicorp/terraform-provider-aws/tree/main/examples)

---

## Source Bibliography

### Primary Sources
- [Terraform AWS Provider Registry v6.47.0](https://registry.terraform.io/providers/hashicorp/aws/latest) — Published 2026-05-28
- [aws_cloudfront_distribution Resource Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_distribution)
- [aws_cloudfront_origin_access_control](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_origin_access_control)
- [aws_cloudfront_cache_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_cache_policy)
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)
- [CloudFront Developer Guide 2024](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html)

### Validation & Tools
- [tfsec](https://github.com/aquasecurity/tfsec) — Security scanning (CloudFront rules: aws-cloudfront-*)
- [Checkov](https://www.checkov.io/) — Policy-as-Code (CKV_AWS_68, CKV_AWS_86, CKV_AWS_174)
- [Terratest](https://terratest.gruntwork.io/) — Integration testing
- [hashicorp/terraform-provider-aws Issues](https://github.com/hashicorp/terraform-provider-aws/issues) — tagged with version 6.x

---

## Completion Checklist

- [x] All Terraform 1.9 and aws ~> 6.0 patterns validated
- [x] `forwarded_values` deprecation documented — `cache_policy_id` mandated
- [x] OAC vs. OAI migration path documented
- [x] State management strategy (S3 + DynamoDB + KMS) documented
- [x] Module architecture fully defined with variable validation
- [x] All anti-patterns have tested alternatives
- [x] CLI commands with expected outputs confirmed
- [x] S3, ACM, Route53, WAF, CloudWatch, IAM integration examples complete
- [x] ACM us-east-1 constraint documented as forbidden pattern
- [x] Security checklist complete
- [x] Complete root module example with .tfvars.example
- [x] Disaster recovery procedures documented
- [x] VPC Origins (new v6.x resource) documented
- [x] Standard logging v2 via CloudWatch delivery documented

---

## Research Gaps

```
Gap: aws_cloudfront_multitenant_distribution and aws_cloudfront_distribution_tenant resource details
Impact: SaaS multi-tenant CloudFront patterns not fully documented
Workaround: Use single distribution with per-behavior custom headers for tenant routing
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_multitenant_distribution

Gap: Continuous deployment policy (blue-green) full Terraform workflow
Impact: Staged configuration rollout not demonstrated end-to-end
Workaround: Manual staging distribution management; use AWS Console for promotion
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_continuous_deployment_policy

Gap: Connection Functions (viewer mTLS custom validation) advanced patterns
Impact: Zero-trust mTLS configuration not fully demonstrated
Workaround: Use standard WAF for authentication enforcement
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_connection_function
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- OAC creation and S3 bucket policy generation
- Cache policy and origin request policy creation
- HTTPS enforcement (viewer_protocol_policy, minimum_protocol_version)
- WAF web ACL creation with AWS managed rules
- `terraform fmt`, `terraform validate`, `tfsec` execution
- Tagging strategy via default_tags
- Route53 ALIAS record creation for CloudFront

### Medium Confidence (Validate with user)
- Price class selection (cost vs. latency tradeoff)
- Origin Shield enablement (adds per-request charge)
- Cache TTL values (depends on content update frequency)
- Geo-restriction requirements (compliance-driven)
- CloudFront Functions vs. Lambda@Edge selection

### Low Confidence (Must ask user)
- Custom cache key design (which headers/cookies to include)
- Signed URL / signed cookies for private content (key management)
- Continuous deployment policy strategy
- Multi-tenant distribution design
- VPC Origins vs. public ALB decision

### Emergency Stop
- Halt if `prevent_destroy = false` on production distribution
- Halt if `viewer_protocol_policy = "allow-all"` detected
- Halt if S3 origin Block Public Access disabled
- Halt if WAF not associated with public-facing distribution
- Halt if ACM certificate region is not `us-east-1`
- Halt if `terraform destroy` planned on production distribution without explicit approval
