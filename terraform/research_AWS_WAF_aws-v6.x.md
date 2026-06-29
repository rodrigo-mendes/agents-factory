# Terraform AWS WAF (WAFv2) — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - WAF (WAFv2)"
Cloud_Provider: "AWS"
Target_Service: "WAF v2 (Web Application Firewall)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-29)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-29"
Research_Date: "2026-05-29"
Domain_Complexity: "Complex"
Key_Resources:
  - aws_wafv2_web_acl
  - aws_wafv2_web_acl_rule
  - aws_wafv2_rule_group
  - aws_wafv2_ip_set
  - aws_wafv2_regex_pattern_set
  - aws_wafv2_web_acl_association
  - aws_wafv2_web_acl_logging_configuration
  - aws_wafv2_web_acl_rule_group_association
```

---

## Executive Summary

AWS WAF v2 (WAFv2) is a managed web application firewall that protects web applications and APIs from common exploits and bots — including SQL injection, cross-site scripting (XSS), HTTP floods, and credential stuffing — without requiring manual rule signature maintenance. WAFv2 replaced the legacy WAF Classic (v1), which is now deprecated. Terraform manages WAFv2 through a family of `aws_wafv2_*` resources. The two most critical architecture decisions at provisioning time are: **(1) scope** — `CLOUDFRONT` (must deploy in `us-east-1`) vs. `REGIONAL` (ALB, API Gateway, Cognito, App Runner) — this is immutable after creation; and **(2) rule management strategy** — inline rules in `aws_wafv2_web_acl` vs. separate `aws_wafv2_web_acl_rule` resources. The official Terraform Registry recommends using the separate `aws_wafv2_web_acl_rule` resource to avoid known limitations with ordering drifts, deletion ordering failures, and coupled update side-effects.

Provider v6.x (6.47.0, published 2026-05-28) introduces `asn_match_statement` for ASN-based filtering and `aws_managed_rules_anti_ddos_rule_set` for integrated DDoS mitigation. The `data_protection_config` block is now available on `aws_wafv2_web_acl` for field-level data redaction in logs (SUBSTITUTION or HASH). JA4 fingerprint inspection (`ja4_fingerprint` in `field_to_match`) is now generally available alongside the existing JA3 fingerprint support. `default_tags` propagation now covers all WAFv2 resources without exception.

The three non-negotiable guardrails for any WAFv2 deployment: **(1) `visibility_config` with `cloudwatch_metrics_enabled = true` and `sampled_requests_enabled = true` must be set on every web ACL and every rule** — without this, there is no traffic visibility for security incident investigation; **(2) `aws_wafv2_web_acl_logging_configuration` must be deployed and backed by a KMS-encrypted Kinesis Firehose or CloudWatch Logs group** — unauthenticated access to WAF logs exposes the attack surface; **(3) the WAF Web ACL must be explicitly associated via `aws_wafv2_web_acl_association` or via a CloudFront distribution's `web_acl_id`** — creating a web ACL without association provides zero protection. This service is classified **Complex** due to the multi-resource dependency chain, security-critical rule ordering, managed rule group capacity units (WCU), immutable scope, and the need for forensic log management.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Ensures reproducibility, pins provider to v6.x semantics (WAFv2 `asn_match_statement`, `data_protection_config`, JA4 support), and defines the deployment contract for all CI pipelines and team members.

```hcl
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/waf/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Terraform Settings Block](https://developer.hashicorp.com/terraform/language/settings) | [AWS Provider Registry](https://registry.terraform.io/providers/hashicorp/aws/latest)

---

#### Pattern: Provider Configuration with IAM Role and Default Tags

**Why**: Credentials must never be hardcoded. `assume_role` enables CI/CD without static credentials. `default_tags` enforces compliance tagging on all WAFv2 resources. For CloudFront WAF (`scope = "CLOUDFRONT"`), a second provider aliased to `us-east-1` is required because CloudFront WAF can only be managed from that region.

```hcl
# Regional WAF (ALB, API Gateway, Cognito)
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}

# CloudFront WAF must be in us-east-1 (required)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [AWS Provider Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#provider-configuration) | [CloudFront WAF Region Requirement](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-cloudfront.html)

---

#### Pattern: Web ACL with Separate Rule Resources (Preferred)

**Why**: The official registry documentation explicitly warns that inline `rule` blocks in `aws_wafv2_web_acl` have three known limitations: deletion ordering errors causing `WAFAssociatedItemException`, spurious diffs from AWS returning rules in unpredictable order, and coupled updates where modifying one rule recreates all rules. Using `aws_wafv2_web_acl_rule` resolves all three and enables independent rule lifecycle management.

```hcl
# The Web ACL shell — rules managed externally
resource "aws_wafv2_web_acl" "main" {
  name        = "${var.environment}-web-acl"
  description = "Main WAF Web ACL for ${var.environment}"
  scope       = var.waf_scope  # "REGIONAL" or "CLOUDFRONT"

  default_action {
    allow {}  # Default: allow traffic, rules block/count specific threats
    # Use block {} only after thorough testing in COUNT mode
  }

  # Required: metrics and request sampling for visibility
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.environment}-web-acl"
    sampled_requests_enabled   = true
  }

  # Token domains for SDK integrations (Bot Control, ATP, ACFP)
  # token_domains = ["myapp.example.com"]

  # REQUIRED when using aws_wafv2_web_acl_rule separately
  lifecycle {
    ignore_changes = [rule]
  }

  tags = {
    Name = "${var.environment}-web-acl"
  }
}

# Rule managed as a separate resource — avoids inline rule limitations
resource "aws_wafv2_web_acl_rule" "aws_common_ruleset" {
  name        = "AWSManagedRulesCommonRuleSet"
  web_acl_id  = aws_wafv2_web_acl.main.id
  scope       = var.waf_scope
  priority    = 10

  override_action {
    none {}  # Enforce rule group actions (block/count as defined)
    # Use count {} to put rule group in COUNT mode for testing
  }

  statement {
    managed_rule_group_statement {
      name        = "AWSManagedRulesCommonRuleSet"
      vendor_name = "AWS"
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "AWSManagedRulesCommonRuleSet"
    sampled_requests_enabled   = true
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_wafv2_web_acl](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl) | [aws_wafv2_web_acl_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl_rule)

---

#### Pattern: Mandatory visibility_config on Every Rule and Web ACL

**Why**: `visibility_config` is required by the API and must be set on both the web ACL and every individual rule. Without `cloudwatch_metrics_enabled = true` and `sampled_requests_enabled = true`, there is no CloudWatch metric data or request sampling for forensic investigation during a security incident. In production, all three fields must be explicitly true.

```hcl
# visibility_config template — apply to EVERY rule and web ACL
visibility_config {
  cloudwatch_metrics_enabled = true   # Sends metrics to CloudWatch
  metric_name                = "unique-metric-name-per-rule"  # alphanumeric, hyphen, underscore only; max 128 chars
  sampled_requests_enabled   = true   # Stores request samples for console review
}
```

```hcl
# Example: Inline visibility on a rate-based rule
resource "aws_wafv2_web_acl_rule" "ip_rate_limit" {
  name       = "ip-rate-limit-1000rpm"
  web_acl_id = aws_wafv2_web_acl.main.id
  scope      = var.waf_scope
  priority   = 5

  action {
    block {}
  }

  statement {
    rate_based_statement {
      aggregate_key_type   = "IP"
      limit                = 1000
      evaluation_window_sec = 60  # Per-minute limit
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "ip-rate-limit-1000rpm"
    sampled_requests_enabled   = true
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [visibility_config Block](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl#visibility_config-block) | [AWS WAF Metrics](https://docs.aws.amazon.com/waf/latest/developerguide/monitoring-cloudwatch.html#waf-metrics)

---

#### Pattern: WAF Logging Configuration (Mandatory for Production)

**Why**: Without logging, there is no audit trail for blocked/counted requests, no forensic data for incident response, and no compliance evidence. Log destination must be created before the logging configuration and the delivery stream/log group name **must** start with `aws-waf-logs-`. KMS encryption is required for compliance.

```hcl
# KMS key for WAF log encryption
resource "aws_kms_key" "waf_logs" {
  description             = "KMS key for WAF logs encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name = "${var.environment}-waf-logs-kms"
  }
}

# CloudWatch Logs group for WAF logs
resource "aws_cloudwatch_log_group" "waf_logs" {
  name              = "aws-waf-logs-${var.environment}"  # MUST start with "aws-waf-logs-"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.waf_logs.arn

  tags = {
    Name = "${var.environment}-waf-logs"
  }
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  log_destination_configs = [aws_cloudwatch_log_group.waf_logs.arn]
  resource_arn            = aws_wafv2_web_acl.main.arn

  # Redact sensitive fields from logs (GDPR/PCI compliance)
  redacted_fields {
    single_header {
      name = "authorization"
    }
  }

  redacted_fields {
    single_header {
      name = "cookie"
    }
  }

  # Filter to log only BLOCK actions (reduces log volume)
  logging_filter {
    default_behavior = "DROP"  # Don't log ALLOW traffic

    filter {
      behavior = "KEEP"

      condition {
        action_condition {
          action = "BLOCK"
        }
      }

      requirement = "MEETS_ANY"
    }
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_wafv2_web_acl_logging_configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl_logging_configuration) | [WAF Logging Destinations](https://docs.aws.amazon.com/waf/latest/developerguide/logging.html)

---

#### Pattern: Web ACL Association with Protected Resource

**Why**: A WAF Web ACL does nothing until associated with a protected resource. The association is a separate resource for REGIONAL resources (ALB, API Gateway, Cognito, App Runner). CloudFront uses `web_acl_id` directly on the distribution. Forgetting the association is a silent failure — WAF is configured but traffic is unprotected.

```hcl
# Associate WAF with ALB (REGIONAL)
resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# Associate WAF with API Gateway stage (REGIONAL)
resource "aws_wafv2_web_acl_association" "api_gateway" {
  resource_arn = aws_api_gateway_stage.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# Associate WAF with Cognito User Pool (REGIONAL)
resource "aws_wafv2_web_acl_association" "cognito" {
  resource_arn = aws_cognito_user_pool.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# CloudFront: WAF embedded directly in distribution config
# scope MUST be "CLOUDFRONT" and provider MUST be us-east-1
resource "aws_cloudfront_distribution" "main" {
  # provider = aws.us_east_1  # Only needed if default provider is not us-east-1
  web_acl_id = aws_wafv2_web_acl.cloudfront_waf.arn
  # ... rest of distribution config
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_wafv2_web_acl_association](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl_association) | [Associating WAF with AWS Resources](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-associating-aws-resource.html)

---

#### Pattern: IP Set for Allow/Block Lists

**Why**: IP sets enable dynamic IP-based access control without recreating the web ACL. They support both IPv4 and IPv6, and can reference forwarded IP headers (X-Forwarded-For) for use behind load balancers. IP sets can be updated in-place without disrupting the web ACL.

```hcl
resource "aws_wafv2_ip_set" "blocked_ips" {
  name               = "${var.environment}-blocked-ips"
  description        = "Known malicious IP addresses"
  scope              = var.waf_scope
  ip_address_version = "IPV4"

  addresses = var.blocked_cidr_ranges  # e.g., ["203.0.113.0/24", "198.51.100.5/32"]

  tags = {
    Name = "${var.environment}-blocked-ips"
  }
}

resource "aws_wafv2_ip_set" "allowed_ips" {
  name               = "${var.environment}-allowlist-ips"
  description        = "Trusted IP addresses (office, VPN)"
  scope              = var.waf_scope
  ip_address_version = "IPV4"

  addresses = var.allowed_cidr_ranges

  tags = {
    Name = "${var.environment}-allowlist-ips"
  }
}

# Use the IP set in a rule
resource "aws_wafv2_web_acl_rule" "block_known_bad_ips" {
  name       = "block-known-bad-ips"
  web_acl_id = aws_wafv2_web_acl.main.id
  scope      = var.waf_scope
  priority   = 1  # Low number = evaluated first

  action {
    block {}
  }

  statement {
    ip_set_reference_statement {
      arn = aws_wafv2_ip_set.blocked_ips.arn
      # For traffic behind a load balancer (X-Forwarded-For)
      # ip_set_forwarded_ip_config {
      #   header_name        = "X-Forwarded-For"
      #   fallback_behavior  = "NO_MATCH"
      #   position           = "FIRST"
      # }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "block-known-bad-ips"
    sampled_requests_enabled   = true
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_wafv2_ip_set](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_ip_set)

---

#### Pattern: Variable Validation & Type Safety

**Why**: Prevents invalid WAF configurations at `terraform plan` time. Scope is immutable after creation — validating it early prevents costly destroy-and-recreate cycles. WCU (Web ACL Capacity Units) validation prevents exceeding AWS limits (1,500 WCU per web ACL for REGIONAL, 1,500 for CLOUDFRONT).

```hcl
variable "waf_scope" {
  type        = string
  description = "WAF scope: REGIONAL (ALB/APIGW/Cognito) or CLOUDFRONT (immutable)"
  default     = "REGIONAL"

  validation {
    condition     = contains(["REGIONAL", "CLOUDFRONT"], var.waf_scope)
    error_message = "WAF scope must be REGIONAL or CLOUDFRONT. CLOUDFRONT requires us-east-1 provider."
  }
}

variable "blocked_cidr_ranges" {
  type        = list(string)
  description = "CIDR ranges to block at the WAF level"
  default     = []

  validation {
    condition     = alltrue([for cidr in var.blocked_cidr_ranges : can(cidrhost(cidr, 0))])
    error_message = "All entries in blocked_cidr_ranges must be valid CIDR notation (e.g., 10.0.0.0/8)."
  }
}

variable "rate_limit_rpm" {
  type        = number
  description = "Requests per minute per IP before rate-limiting triggers"
  default     = 1000

  validation {
    condition     = var.rate_limit_rpm >= 100 && var.rate_limit_rpm <= 2000000000
    error_message = "Rate limit must be between 100 and 2,000,000,000."
  }
}

variable "environment" {
  type        = string
  description = "Environment name (prod, staging, dev)"

  validation {
    condition     = contains(["prod", "staging", "dev"], var.environment)
    error_message = "Environment must be prod, staging, or dev."
  }
}
```

- **Source**: [Custom Validation Rules](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules) | [WAF Quotas](https://docs.aws.amazon.com/waf/latest/developerguide/limits.html)

---

### ⚠️ Conditional Patterns

---

#### Decision: Inline Rules vs. Separate `aws_wafv2_web_acl_rule` Resources

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Inline `rule {}` in web ACL** | Simpler single-file config | Drift detection, deletion ordering, update isolation | Prototyping, < 3 rules, no IP sets/rule groups |
| **`aws_wafv2_web_acl_rule` (separate)** | Independent lifecycle, no ordering drift, isolated updates | More resource blocks, `ignore_changes = [rule]` required | Production, rule groups, IP sets, > 3 rules |
| **`aws_wafv2_web_acl_rule_group_association`** | Dedicated managed rule group lifecycle | Extra resource per group | Many managed rule groups needing separate state tracking |

**Trade-off detail**:
- Inline rules cause `WAFAssociatedItemException` when removing a rule that references an IP set — Terraform deletes the IP set before removing the rule reference
- Inline rules have spurious diffs because AWS returns rules in unpredictable order
- When using separate `aws_wafv2_web_acl_rule`, you **must** add `lifecycle { ignore_changes = [rule] }` to the `aws_wafv2_web_acl` resource

**Agent**: "Ask user: How many rules are planned? Do any rules reference IP sets or rule groups? Is this a production deployment?"

- **Source**: [aws_wafv2_web_acl Known Limitations Note](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl)

---

#### Decision: Default Action — Allow vs. Block

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **`default_action { allow {} }`** | Reduced false-positive risk, safe migration | Any traffic not matched by rules passes through | Standard API/web apps with defined threat rules |
| **`default_action { block {} }`** | Maximum security, allowlist-based model | Risk of blocking legitimate users, requires exhaustive allowlist | High-security endpoints (admin, payments, auth) |

**Recommendation**: Always start with `allow` + managed rule groups in `count` mode. Validate no false positives, then switch to `none` (enforce). Consider `block` default only for highly-restricted internal applications.

**Agent**: "Ask user: Is this a public-facing API or a restricted internal endpoint? What is the acceptable false-positive rate?"

- **Source**: [WAF Default Action](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-processing.html)

---

#### Decision: Managed Rule Groups vs. Custom Rules

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **AWS Managed Rule Groups** | Zero maintenance, threat intel updated by AWS | Less control, cost per WCU, possible false positives | Baseline protection, OWASP Top 10 |
| **Custom `aws_wafv2_rule_group`** | Full control, business-specific logic | Maintenance burden, no automatic threat intel updates | Custom block lists, business logic protection |
| **Hybrid (managed + custom)** | Best coverage | Higher WCU cost (1,500 WCU limit) | Production environments |

**WCU Cost of Common Managed Groups**:
| Group | WCUs |
|-------|------|
| AWSManagedRulesCommonRuleSet | 700 |
| AWSManagedRulesSQLiRuleSet | 200 |
| AWSManagedRulesKnownBadInputsRuleSet | 200 |
| AWSManagedRulesBotControlRuleSet (Common) | 50 |
| AWSManagedRulesBotControlRuleSet (Targeted) | 50 + ML cost |
| AWSManagedRulesATPRuleSet | 50 |

**Agent**: "Ask user: Do you need baseline OWASP protection, bot protection, account takeover protection, or all three? Current WCU usage must be checked to avoid exceeding the 1,500 limit."

- **Source**: [AWS Managed Rule Groups List](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html) | [WCU Pricing](https://aws.amazon.com/waf/pricing/)

---

#### Decision: COUNT mode vs. BLOCK mode Rollout Strategy

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Start in COUNT mode** | Safety, false-positive discovery | Active protection delayed | New rule rollout, managed rule group onboarding |
| **Start in BLOCK mode** | Immediate protection | Risk of blocking legitimate traffic | Known malicious IPs, emergency response |
| **Gradual promotion** | Balance of safety and security | More operational steps | Production with SLA requirements |

```hcl
# Phase 1: Test in COUNT mode (override_action = count)
override_action {
  count {}  # Rule group in COUNT mode
}

# Phase 2: After validating no false positives, switch to ENFORCE
override_action {
  none {}  # Rule group enforces its configured actions
}
```

**Agent**: "Ask user: Is this a new WAF deployment on existing traffic? What is the acceptable latency to start blocking threats?"

---

#### Decision: REGIONAL vs. CLOUDFRONT Scope

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **REGIONAL** | Protects ALB, API GW, Cognito, App Runner in any region | Cannot protect CloudFront | API-first architectures, regional resources |
| **CLOUDFRONT** | Edge-level filtering (before origin), global CDN WAF | Must deploy in us-east-1, cannot protect regional resources | SPA/static sites, global traffic filtering |

**Critical**: Scope is **immutable** — changing `scope` forces resource replacement (destroy + create), causing a protection gap.

**Agent**: "Ask user: What resource type is being protected? Is global edge filtering needed or regional origin protection? Is the resource an ALB/API Gateway (use REGIONAL) or CloudFront (use CLOUDFRONT)?"

---

#### Decision: Log Destination — CloudWatch Logs vs. Kinesis Firehose vs. S3

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **CloudWatch Logs** | Easy querying, Log Insights integration, real-time alerts | Cost at high volume, limited long-term storage | Standard production, < 1M req/hour |
| **Kinesis Data Firehose → S3** | High throughput, cost-efficient at scale, SIEM integration | Latency (buffering), more setup | High-traffic applications, SIEM integration |
| **S3 directly (via Firehose)** | Lowest cost, long-term retention | No real-time querying | Compliance archival |

**Note**: Regardless of destination, the name **must** start with `aws-waf-logs-`.

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: WAF Web ACL Created Without Association

```hcl
# DON'T — Web ACL with no association protects nothing
resource "aws_wafv2_web_acl" "main" {
  name  = "prod-waf"
  scope = "REGIONAL"

  default_action { allow {} }
  visibility_config {
    cloudwatch_metrics_enabled = false
    metric_name                = "prod-waf"
    sampled_requests_enabled   = false
  }
}
# Missing: aws_wafv2_web_acl_association
```

```hcl
# DO — Always associate the Web ACL with a protected resource
resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn

  depends_on = [
    aws_wafv2_web_acl.main,
    aws_lb.main
  ]
}
```

- **Impact**: Silent failure — WAF rules are defined but traffic is completely unprotected
- **Severity**: CRITICAL
- **Source**: [Associating AWS Resources](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-associating-aws-resource.html)

---

#### Anti-Pattern: visibility_config with Metrics and Sampling Disabled

```hcl
# DON'T — Disabling metrics and sampling leaves you blind during incidents
visibility_config {
  cloudwatch_metrics_enabled = false  # DON'T in production
  metric_name                = "my-waf"
  sampled_requests_enabled   = false  # DON'T in production
}
```

```hcl
# DO — Enable on every rule and the web ACL
visibility_config {
  cloudwatch_metrics_enabled = true
  metric_name                = "prod-waf-common-ruleset"
  sampled_requests_enabled   = true
}
```

- **Impact**: No CloudWatch metrics, no request samples — impossible to investigate security incidents or tune rules
- **Severity**: HIGH
- **Source**: [WAF Monitoring](https://docs.aws.amazon.com/waf/latest/developerguide/monitoring-cloudwatch.html)

---

#### Anti-Pattern: Using WAF Classic (v1) Resources

```hcl
# DON'T — WAF Classic is deprecated; these resources are EOL
resource "aws_waf_web_acl" "main" { ... }        # WAF Classic (deprecated)
resource "aws_waf_rule" "main" { ... }            # WAF Classic (deprecated)
resource "aws_wafregional_web_acl" "main" { ... } # WAF Classic Regional (deprecated)
```

```hcl
# DO — Use WAFv2 resources exclusively
resource "aws_wafv2_web_acl" "main" { ... }
resource "aws_wafv2_web_acl_rule" "main" { ... }
```

- **Impact**: AWS WAF Classic (v1) is deprecated. New features, managed rule groups, and support are WAFv2 only
- **Severity**: HIGH
- **Source**: [WAF Classic Migration Guide](https://docs.aws.amazon.com/waf/latest/developerguide/classic-waf-chapter.html)

---

#### Anti-Pattern: Deploying Managed Rule Groups in BLOCK Mode Without Testing

```hcl
# DON'T — Immediately enforcing managed rules on production traffic
resource "aws_wafv2_web_acl_rule" "common_ruleset" {
  # ...
  override_action {
    none {}  # DON'T do this without testing first
  }

  statement {
    managed_rule_group_statement {
      name        = "AWSManagedRulesCommonRuleSet"
      vendor_name = "AWS"
    }
  }
}
```

```hcl
# DO — Start in COUNT mode, validate, then promote to BLOCK
# Phase 1: COUNT mode
resource "aws_wafv2_web_acl_rule" "common_ruleset" {
  # ...
  override_action {
    count {}  # Start in count mode — records matches but does NOT block
  }

  statement {
    managed_rule_group_statement {
      name        = "AWSManagedRulesCommonRuleSet"
      vendor_name = "AWS"
    }
  }
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "CommonRuleSet-Count"
    sampled_requests_enabled   = true
  }
}
# Phase 2 (after 1-2 weeks of monitoring): Change override_action to none {}
```

- **Impact**: HIGH — The `AWSManagedRulesCommonRuleSet` (700 WCUs) includes rules like `SizeRestrictions_QUERYSTRING` and `NoUserAgent_HEADER` that may block legitimate API traffic
- **Severity**: HIGH
- **Source**: [Testing WAF Rules](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-testing.html)

---

#### Anti-Pattern: CloudFront WAF Not Deployed in us-east-1

```hcl
# DON'T — CLOUDFRONT scope WAF deployed outside us-east-1
provider "aws" {
  region = "eu-west-1"  # Wrong for CLOUDFRONT scope
}

resource "aws_wafv2_web_acl" "cloudfront_waf" {
  scope = "CLOUDFRONT"  # This will fail: CloudFront WAF requires us-east-1
  # ...
}
```

```hcl
# DO — Dedicated us-east-1 provider for CloudFront WAF
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  # ...
}

resource "aws_wafv2_web_acl" "cloudfront_waf" {
  provider = aws.us_east_1
  scope    = "CLOUDFRONT"
  # ...
}
```

- **Impact**: API error: `WAFInvalidParameterException: Error reason: The scope is not valid for the given resource type`
- **Severity**: CRITICAL
- **Source**: [WAF CloudFront Requirements](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-cloudfront.html)

---

#### Anti-Pattern: No Logging Configuration

```hcl
# DON'T — Web ACL without logging
resource "aws_wafv2_web_acl" "main" {
  name  = "prod-waf"
  scope = "REGIONAL"
  # ... rules defined ...
}
# Missing: aws_wafv2_web_acl_logging_configuration
```

```hcl
# DO — Always attach a logging configuration
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  log_destination_configs = [aws_cloudwatch_log_group.waf_logs.arn]
  resource_arn            = aws_wafv2_web_acl.main.arn
  # ...
}
```

- **Impact**: No forensic trail for blocked requests, no compliance audit log, no ability to tune rules based on actual traffic
- **Severity**: HIGH
- **Source**: [WAF Logging](https://docs.aws.amazon.com/waf/latest/developerguide/logging.html)

---

#### Anti-Pattern: Hardcoded WAF Rule Priorities with Gaps or Conflicts

```hcl
# DON'T — Rules sharing the same priority or chaotic numbering
resource "aws_wafv2_web_acl_rule" "allowlist" {
  priority = 1
  # ...
}
resource "aws_wafv2_web_acl_rule" "block_sqli" {
  priority = 1  # DON'T — duplicate priority, API error
  # ...
}
```

```hcl
# DO — Use consistent spacing (e.g., multiples of 10) for easy insertion
# Priority 1-9:    Emergency blocks (individual IPs, geo-blocks)
# Priority 10-19:  IP allowlists
# Priority 20-49:  Rate limiting
# Priority 50-99:  Custom business rules
# Priority 100+:   Managed rule groups
resource "aws_wafv2_web_acl_rule" "allowlist" {
  priority = 10
}
resource "aws_wafv2_web_acl_rule" "rate_limit" {
  priority = 20
}
resource "aws_wafv2_web_acl_rule" "common_ruleset" {
  priority = 100
}
```

- **Impact**: API error if duplicate priorities; incorrect evaluation order if priorities are wrong (lower number = first evaluated, first match wins for terminating rules)
- **Severity**: HIGH
- **Source**: [WAF Rule Priority](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-rule-priority.html)

---

#### Anti-Pattern: Missing `lifecycle { ignore_changes = [rule] }` When Using Separate Rule Resources

```hcl
# DON'T — Web ACL without ignore_changes when using aws_wafv2_web_acl_rule
resource "aws_wafv2_web_acl" "main" {
  name  = "prod-waf"
  scope = "REGIONAL"
  # No lifecycle block
  # ...
}

resource "aws_wafv2_web_acl_rule" "custom_rule" {
  web_acl_id = aws_wafv2_web_acl.main.id
  # ...
}
# Result: Endless spurious diffs on the web ACL's `rule` attribute
```

```hcl
# DO — Add lifecycle ignore_changes when managing rules externally
resource "aws_wafv2_web_acl" "main" {
  name  = "prod-waf"
  scope = "REGIONAL"
  # ...

  lifecycle {
    ignore_changes = [rule]  # REQUIRED when using aws_wafv2_web_acl_rule
  }
}
```

- **Impact**: Perpetual drift detection causing false positives in CI/CD pipelines; `terraform plan` always shows changes even when configuration is stable
- **Severity**: MEDIUM
- **Source**: [aws_wafv2_web_acl Warning Note](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl)

---

#### Anti-Pattern: Exceeding WCU Limit

```hcl
# DON'T — Adding too many managed rule groups without tracking WCU usage
# AWSManagedRulesCommonRuleSet:        700 WCU
# AWSManagedRulesSQLiRuleSet:          200 WCU
# AWSManagedRulesLinuxRuleSet:         200 WCU
# AWSManagedRulesWindowsRuleSet:       200 WCU
# AWSManagedRulesPHPRuleSet:           100 WCU
# AWSManagedRulesBotControlRuleSet:     50 WCU
# TOTAL:                              1450 WCU — dangerously close to 1500 limit
# Adding one more group will FAIL with WAFUnavailableEntityException
```

```hcl
# DO — Track WCU in variables/comments and validate before adding rules
# Use aws_wafv2_web_acl.main.capacity (output) to check current usage
output "waf_web_acl_capacity_units" {
  value       = aws_wafv2_web_acl.main.capacity
  description = "Current WCU usage - max 1500 for REGIONAL/CLOUDFRONT"
}
```

- **Impact**: `terraform apply` fails with `WAFUnavailableEntityException` when adding new rules that exceed 1,500 WCU; may require removing existing rules under active protection
- **Severity**: HIGH
- **Source**: [WAF Quotas and WCU](https://docs.aws.amazon.com/waf/latest/developerguide/limits.html)

---

## State Management Deep Dive

### Local Development State

```hcl
# Use local state only for development/learning
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

- **Risk**: Single point of failure, no locking — if two developers apply simultaneously, WAF rules can be in an inconsistent state (rule priority conflicts)
- **When**: Solo development, proof-of-concept only

### Production Remote State (S3 + DynamoDB)

```hcl
# State locking table (run once, bootstrap)
resource "aws_dynamodb_table" "terraform_locks" {
  name           = "terraform-locks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "terraform-locks"
    ManagedBy = "terraform"
  }
}

# WAF-specific state backend
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/waf/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

- **Benefit**: DynamoDB locking prevents concurrent WAF rule modifications that would create priority conflicts
- **WAF-specific risk**: State file contains WAF Web ACL ARNs — restrict state bucket access to Terraform service accounts only
- **Critical**: CloudFront WAF state **must** be in `us-east-1` backend even if the application runs in another region

### State File Sensitivity

WAF state files contain:
- Web ACL ARNs (used in service associations — protect from unauthorized association)
- IP set contents (reveals your blocklist/allowlist to attackers)
- Rule logic (reveals detection patterns enabling evasion)

```hcl
# Sensitive outputs — mask in logs and plans
output "web_acl_arn" {
  value       = aws_wafv2_web_acl.main.arn
  description = "WAF Web ACL ARN for resource association"
  sensitive   = false  # ARNs are not secrets, but restrict access to state bucket
}

output "web_acl_id" {
  value       = aws_wafv2_web_acl.main.id
  description = "WAF Web ACL ID for import/reference"
}
```

---

## Module Architecture

### Standard WAF Module Structure

```
modules/
└── waf/
    ├── main.tf          # Web ACL, rules, IP sets, regex sets
    ├── logging.tf       # Logging configuration, log group
    ├── associations.tf  # web_acl_association resources
    ├── variables.tf     # Input variables with validation
    ├── outputs.tf       # web_acl_arn, web_acl_id, capacity
    ├── versions.tf      # Terraform and provider version constraints
    └── README.md        # Usage, WCU accounting, rule priority map
```

### Module Definition Example

```hcl
# modules/waf/variables.tf
variable "scope" {
  type        = string
  description = "WAF scope — REGIONAL or CLOUDFRONT (immutable)"
  validation {
    condition     = contains(["REGIONAL", "CLOUDFRONT"], var.scope)
    error_message = "scope must be REGIONAL or CLOUDFRONT"
  }
}

variable "enable_common_ruleset" {
  type        = bool
  description = "Enable AWSManagedRulesCommonRuleSet (700 WCU)"
  default     = true
}

variable "enable_sqli_ruleset" {
  type        = bool
  description = "Enable AWSManagedRulesSQLiRuleSet (200 WCU)"
  default     = true
}

variable "enable_bot_control" {
  type        = bool
  description = "Enable AWSManagedRulesBotControlRuleSet (50+ WCU, additional cost)"
  default     = false
}

variable "rate_limit_rpm" {
  type        = number
  description = "Per-IP request rate limit per minute"
  default     = 1000
  validation {
    condition     = var.rate_limit_rpm >= 100
    error_message = "Minimum rate limit is 100 requests per evaluation window"
  }
}

variable "protected_resource_arns" {
  type        = list(string)
  description = "ARNs of resources to associate with the Web ACL (ALB, API GW, Cognito)"
  default     = []
}

# modules/waf/outputs.tf
output "web_acl_arn" {
  value       = aws_wafv2_web_acl.main.arn
  description = "WAF Web ACL ARN — use in resource associations or CloudFront web_acl_id"
}

output "web_acl_id" {
  value       = aws_wafv2_web_acl.main.id
  description = "WAF Web ACL ID"
}

output "web_acl_capacity" {
  value       = aws_wafv2_web_acl.main.capacity
  description = "Current WCU usage — max 1500"
}

# root/main.tf — using the WAF module
module "regional_waf" {
  source = "./modules/waf"

  scope                   = "REGIONAL"
  enable_common_ruleset   = true
  enable_sqli_ruleset     = true
  enable_bot_control      = false
  rate_limit_rpm          = 500
  protected_resource_arns = [aws_lb.api.arn, aws_api_gateway_stage.main.arn]
}
```

---

## Integration Patterns

### Integration: Terraform ↔ CloudFront

**Pattern**: CloudFront WAF must use `scope = "CLOUDFRONT"` and a `us-east-1` provider. The `web_acl_id` attribute on `aws_cloudfront_distribution` accepts the Web ACL ARN.

```hcl
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
  }
}

resource "aws_wafv2_web_acl" "cloudfront_waf" {
  provider    = aws.us_east_1
  name        = "${var.environment}-cloudfront-waf"
  description = "WAF for CloudFront distribution"
  scope       = "CLOUDFRONT"  # MUST be CLOUDFRONT for CloudFront

  default_action { allow {} }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.environment}-cloudfront-waf"
    sampled_requests_enabled   = true
  }

  lifecycle {
    ignore_changes = [rule]
  }
}

resource "aws_cloudfront_distribution" "main" {
  web_acl_id = aws_wafv2_web_acl.cloudfront_waf.arn  # Uses ARN, not ID
  # ... rest of distribution
}
```

| Resource | Min Provider Version | Max | Notes |
|----------|---------------------|-----|-------|
| `aws_wafv2_web_acl` (CLOUDFRONT) | aws ~> 6.0 | N/A | Must deploy in us-east-1 |
| `aws_cloudfront_distribution` | aws ~> 6.0 | N/A | `web_acl_id` takes WAF ARN |

**Gotchas**: CloudFront cannot use a REGIONAL Web ACL. WAF for CloudFront only shows logs in CloudWatch Logs groups in `us-east-1`. Changes to the CloudFront WAF require propagation time (~15 min for CloudFront distribution changes).

- **Source**: [CloudFront + WAF](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-cloudfront.html)

---

### Integration: Terraform ↔ ALB (Application Load Balancer)

**Pattern**: REGIONAL Web ACL associated via `aws_wafv2_web_acl_association` using the ALB ARN.

```hcl
resource "aws_lb" "main" {
  name               = "${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = var.public_subnet_ids
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn

  depends_on = [
    aws_lb.main,
    aws_wafv2_web_acl.main
  ]
}
```

**Gotchas**: The ALB must be in an `active` state before WAF association. WAF evaluation happens at the ALB level before the request reaches targets, providing early termination. Large request body inspection limit for ALB is configurable via `association_config` block.

- **Source**: [WAF with ALB](https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html)

---

### Integration: Terraform ↔ API Gateway

**Pattern**: REGIONAL Web ACL associated via `aws_wafv2_web_acl_association` using the API Gateway **stage** ARN (not the REST API ARN).

```hcl
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment
}

resource "aws_wafv2_web_acl_association" "api_gateway" {
  # Stage ARN format: arn:aws:apigateway:{region}::/restapis/{api-id}/stages/{stage-name}
  resource_arn = aws_api_gateway_stage.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# For HTTP APIs (API Gateway v2), the ARN format differs:
# arn:aws:apigateway:{region}::/apis/{api-id}/stages/{stage-name}
resource "aws_wafv2_web_acl_association" "http_api" {
  resource_arn = aws_apigatewayv2_stage.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}
```

**Gotchas**: The association must use the **stage** ARN, not the API ARN. Large request body inspection for API Gateway is configured via `association_config.request_body.api_gateway.default_size_inspection_limit` (KB_16, KB_32, KB_48, KB_64).

- **Source**: [WAF with API Gateway](https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html)

---

### Integration: Terraform ↔ Cognito User Pool

**Pattern**: REGIONAL Web ACL associated via `aws_wafv2_web_acl_association` using the Cognito User Pool ARN. Enables ATP (Account Takeover Protection) managed rule group for login endpoint protection.

```hcl
resource "aws_wafv2_web_acl_association" "cognito" {
  resource_arn = aws_cognito_user_pool.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# ATP rule group for Cognito — requires knowing the login path
resource "aws_wafv2_web_acl_rule" "atp_cognito" {
  name       = "AWSManagedRulesATPRuleSet"
  web_acl_id = aws_wafv2_web_acl.main.id
  scope      = "REGIONAL"
  priority   = 110

  override_action {
    count {}  # Start in count mode
  }

  statement {
    managed_rule_group_statement {
      name        = "AWSManagedRulesATPRuleSet"
      vendor_name = "AWS"

      managed_rule_group_configs {
        aws_managed_rules_atp_rule_set {
          login_path = "/login"  # Your Cognito login endpoint path

          request_inspection {
            payload_type = "JSON"
            username_field {
              identifier = "/username"
            }
            password_field {
              identifier = "/password"
            }
          }
        }
      }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "ATP-Cognito"
    sampled_requests_enabled   = true
  }
}
```

**Gotchas**: Response inspection for ATP is only available on CloudFront-scoped Web ACLs. The `token_domains` attribute on the Web ACL must include Cognito's domain if using Bot Control or ATP with token-based verification.

- **Source**: [WAF with Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-waf.html)

---

### Integration: Terraform ↔ CloudWatch (Monitoring & Alerting)

```hcl
# Alert on high block rate (potential attack in progress)
resource "aws_cloudwatch_metric_alarm" "waf_high_blocked_requests" {
  alarm_name          = "${var.environment}-waf-high-block-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = 300  # 5-minute windows
  statistic           = "Sum"
  threshold           = 1000  # Alert if > 1000 blocks in 5 min
  alarm_description   = "WAF blocking high volume of requests — possible attack"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]

  dimensions = {
    WebACL = aws_wafv2_web_acl.main.name
    Region = var.aws_region
    Rule   = "ALL"  # All rules combined
  }
}

# Alert on allowed requests spike (possible bypass)
resource "aws_cloudwatch_metric_alarm" "waf_allowed_requests_spike" {
  alarm_name          = "${var.environment}-waf-request-spike"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "AllowedRequests"
  namespace           = "AWS/WAFV2"
  period              = 60
  statistic           = "Sum"
  threshold           = 10000  # Tune to expected baseline
  alarm_actions       = [aws_sns_topic.security_alerts.arn]

  dimensions = {
    WebACL = aws_wafv2_web_acl.main.name
    Region = var.aws_region
    Rule   = "ALL"
  }
}
```

- **Source**: [WAF CloudWatch Metrics](https://docs.aws.amazon.com/waf/latest/developerguide/monitoring-cloudwatch.html)

---

### Integration: Terraform ↔ Shield Advanced

**Pattern**: Shield Advanced provides DDoS protection at the network/transport layer; WAF provides application-layer (L7) protection. Together they form a layered defense. The `aws_managed_rules_anti_ddos_rule_set` (v6.x) provides integrated WAF-level DDoS mitigation.

```hcl
# Shield Advanced subscription (account-level, one per org)
resource "aws_shield_protection" "alb" {
  name         = "${var.environment}-alb-shield"
  resource_arn = aws_lb.main.arn
}

# Enable automatic application layer DDoS mitigation
resource "aws_shield_application_layer_automatic_response" "alb" {
  resource_arn = aws_lb.main.arn
  action       = "COUNT"  # Use COUNT before switching to BLOCK
}

# WAF Anti-DDoS managed rule group (v6.x feature)
resource "aws_wafv2_web_acl_rule" "anti_ddos" {
  name       = "AWSManagedRulesAntiDDoSRuleSet"
  web_acl_id = aws_wafv2_web_acl.main.id
  scope      = "REGIONAL"
  priority   = 200

  override_action {
    none {}
  }

  statement {
    managed_rule_group_statement {
      name        = "AWSManagedRulesAntiDDoSRuleSet"
      vendor_name = "AWS"

      managed_rule_group_configs {
        aws_managed_rules_anti_ddos_rule_set {
          sensitivity_to_block = "LOW"

          client_side_action_config {
            challenge {
              usage_of_action = "ENABLED"
              sensitivity      = "HIGH"
            }
          }
        }
      }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "AntiDDoS"
    sampled_requests_enabled   = true
  }
}
```

**Gotchas**: Shield Advanced auto-mitigation creates `ShieldMitigationRuleGroup_<account-id>_<web-acl-guid>_*` rules automatically in the Web ACL. These should NOT be included in Terraform config — the provider automatically ignores rules matching that pattern.

- **Source**: [Shield Advanced + WAF](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html)

---

### Integration: Terraform ↔ KMS (Encryption)

**Pattern**: KMS encrypts WAF CloudWatch Logs groups and Kinesis Firehose delivery streams for log data at rest.

```hcl
resource "aws_kms_key" "waf_logs" {
  description             = "KMS key for WAF logs"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt*",
          "kms:Decrypt*",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:Describe*"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.aws_region}:${var.account_id}:*"
          }
        }
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "waf_logs" {
  name              = "aws-waf-logs-${var.environment}"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.waf_logs.arn
}
```

- **Source**: [CloudWatch Logs KMS Encryption](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html)

---

## Executable Verification

### Terraform CLI Commands

```bash
# 1. Initialize and upgrade providers
terraform init -upgrade
# Expected: Terraform has been successfully initialized!
# Expected: aws provider version 6.47.0 installed

# 2. Format validation
terraform fmt -recursive -check=true
# Expected: Exit code 0 (no output = all files formatted correctly)

# 3. Syntax validation
terraform validate
# Expected: Success! The configuration is valid.

# 4. Security scanning
tfsec . --format sarif
# Expected: Result: 0 critical, 0 high findings
# Known WAF-specific findings to review:
#   aws-wafv2-enforce-admin-protect-rule-group - if not using admin page protection
#   aws-wafv2-no-public-logging-configuration - if logging not yet configured

checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks

# 5. Plan — always review before apply
terraform plan -out=tfplan -lock=true
terraform show tfplan | head -100
# Expected: Plan shows web ACL, rules, IP sets, associations

# 6. Apply
terraform apply tfplan
# Expected: Apply complete! Resources: N added

# 7. Verify association
terraform state list | grep wafv2
# Expected: Lists all WAFv2 resources including associations

# 8. Verify Web ACL capacity
terraform output waf_web_acl_capacity_units
# Expected: Number < 1500

# 9. Verify logging
aws wafv2 get-logging-configuration \
  --resource-arn $(terraform output -raw web_acl_arn) \
  --region us-east-1
# Expected: LoggingConfiguration with log destination ARN

# 10. Import existing Web ACL into Terraform state
terraform import aws_wafv2_web_acl.main "a1b2c3d4-d5f6-7777-8888-9999aaaabbbbcccc/my-web-acl/REGIONAL"
# ID format: {uuid}/{name}/{scope}
```

---

## Configuration Validation & Type Safety

```hcl
variable "waf_scope" {
  type        = string
  description = "WAF scope — REGIONAL or CLOUDFRONT. Immutable after creation."
  default     = "REGIONAL"

  validation {
    condition     = contains(["REGIONAL", "CLOUDFRONT"], var.waf_scope)
    error_message = "waf_scope must be REGIONAL or CLOUDFRONT."
  }
}

variable "rate_limit_per_minute" {
  type        = number
  description = "Max requests per IP per minute (100–2,000,000,000)"
  default     = 1000

  validation {
    condition     = var.rate_limit_per_minute >= 100 && var.rate_limit_per_minute <= 2000000000
    error_message = "Rate limit must be 100–2,000,000,000 per AWS quotas."
  }
}

variable "enable_managed_rule_groups" {
  type = object({
    common_ruleset       = bool
    sqli_ruleset         = bool
    known_bad_inputs     = bool
    linux_ruleset        = bool
    windows_ruleset      = bool
    bot_control_common   = bool
    bot_control_targeted = bool
    atp                  = bool
    acfp                 = bool
  })
  description = "Toggle individual managed rule groups to stay within 1,500 WCU"
  default = {
    common_ruleset       = true
    sqli_ruleset         = true
    known_bad_inputs     = true
    linux_ruleset        = false
    windows_ruleset      = false
    bot_control_common   = false
    bot_control_targeted = false
    atp                  = false
    acfp                 = false
  }
}

variable "allowed_cidr_ranges" {
  type        = list(string)
  description = "CIDR ranges for IP allowlist"
  default     = []

  validation {
    condition     = alltrue([for cidr in var.allowed_cidr_ranges : can(cidrhost(cidr, 0))])
    error_message = "All entries must be valid CIDR notation."
  }
}

variable "log_retention_days" {
  type        = number
  description = "WAF log retention in days"
  default     = 90

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "log_retention_days must be a valid CloudWatch retention value."
  }
}
```

---

## Drift Detection & Reconciliation

### Scenario: Manual WAF Rule Added via AWS Console

```
Detection: terraform plan output showing:
  # aws_wafv2_web_acl.main will be updated in-place
  ~ resource "aws_wafv2_web_acl" "main" {
      # Rule added outside Terraform detected only if NOT using ignore_changes = [rule]
    }
```

```bash
# Recovery: Import the manually-created rule
terraform import aws_wafv2_web_acl_rule.manual_rule \
  "web-acl-id/REGIONAL/manual-rule-name"

# Or: Reconcile by removing the manual rule via AWS CLI
aws wafv2 delete-web-acl --name my-web-acl --scope REGIONAL \
  --id web-acl-id --lock-token $(aws wafv2 get-web-acl ... | jq -r .LockToken)

# Refresh state to detect current reality
terraform refresh
```

### Scenario: IP Set Updated Manually

```bash
# Detect drift
terraform plan
# Shows: aws_wafv2_ip_set.blocked_ips will be updated (addresses diff)

# Recovery option 1: Accept manual changes and update Terraform
terraform import aws_wafv2_ip_set.blocked_ips "ip-set-id/blocked-ips/REGIONAL"
# Then update variables.tf with the new addresses

# Recovery option 2: Revert manual change
terraform apply -target=aws_wafv2_ip_set.blocked_ips
```

### Lifecycle Rules

```hcl
# Protect Web ACL from accidental deletion (production)
resource "aws_wafv2_web_acl" "main" {
  # ...
  lifecycle {
    ignore_changes    = [rule]         # Required when using separate rule resources
    prevent_destroy   = true           # Prevent terraform destroy from removing WAF
    create_before_destroy = false      # NOT needed for WAF (no zero-downtime destroy requirement)
  }
}
```

---

## Secrets & Sensitive Data Management

WAF configuration itself does not contain API keys or passwords, but its logs can contain sensitive PII from request bodies, headers, and cookies.

```hcl
# Redact sensitive fields from WAF logs
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  log_destination_configs = [aws_cloudwatch_log_group.waf_logs.arn]
  resource_arn            = aws_wafv2_web_acl.main.arn

  # Redact Authorization header (contains tokens/credentials)
  redacted_fields {
    single_header {
      name = "authorization"  # lowercase required
    }
  }

  # Redact Cookie header (may contain session tokens)
  redacted_fields {
    single_header {
      name = "cookie"
    }
  }

  # Redact password field in POST body
  # Note: body redaction requires the body field_to_match type
  # For JSON body fields, use data_protection_config on the web ACL instead
}

# Data protection for sensitive fields in web ACL (v6.x feature)
resource "aws_wafv2_web_acl" "main" {
  # ...
  data_protection_config {
    data_protection {
      action = "SUBSTITUTION"  # Replaces field value in logs with placeholder
      field {
        field_type = "SINGLE_HEADER"
        field_keys = ["authorization", "x-api-key"]
      }
    }

    data_protection {
      action = "HASH"  # Replaces with SHA-256 hash (for analytics without exposure)
      field {
        field_type = "SINGLE_COOKIE"
        field_keys = ["session_id", "auth_token"]
      }
    }
  }
}
```

- **Source**: [WAF Log Redaction](https://docs.aws.amazon.com/waf/latest/developerguide/logging-fields.html) | [Data Protection Config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl#data_protection_config-block)

---

## Testing & Validation Frameworks

### Static Analysis

```bash
# terraform validate
terraform validate
# Expected: Success! The configuration is valid.

# tfsec — WAF-specific checks
tfsec . --include-ignored --format default
# Key WAF checks:
# aws-wafv2-enforce-admin-protect-rule-group
# aws-wafv2-no-public-logging-configuration

# checkov — Policy-as-code
checkov -d . --framework terraform --check CKV_AWS_192,CKV_AWS_174,CKV_AWS_175,CKV2_AWS_31
# CKV_AWS_192: Ensure WAF prevents message lookup in Log4j2
# CKV_AWS_174: Ensure WAF Web ACL has at least one rule or rule group
# CKV_AWS_175: Ensure AWS WAF V2 has logging enabled
# CKV2_AWS_31: Ensure WAF2 has a logging destination
```

### Terratest Integration Test

```go
package test

import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/stretchr/testify/assert"
  "github.com/aws/aws-sdk-go/aws"
  "github.com/aws/aws-sdk-go/aws/session"
  "github.com/aws/aws-sdk-go/service/wafv2"
)

func TestWAFDeployment(t *testing.T) {
  opts := &terraform.Options{
    TerraformDir: "../examples/waf",
    Vars: map[string]interface{}{
      "environment":         "test",
      "waf_scope":           "REGIONAL",
      "rate_limit_per_minute": 1000,
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  webAclArn := terraform.Output(t, opts, "web_acl_arn")
  assert.Contains(t, webAclArn, "arn:aws:wafv2:")

  // Verify Web ACL exists and has logging enabled
  sess := session.Must(session.NewSession(&aws.Config{Region: aws.String("us-east-1")}))
  svc := wafv2.New(sess)

  loggingConfig, err := svc.GetLoggingConfiguration(&wafv2.GetLoggingConfigurationInput{
    ResourceArn: aws.String(webAclArn),
  })
  assert.NoError(t, err, "Logging configuration should exist")
  assert.NotNil(t, loggingConfig.LoggingConfiguration)
}
```

### Terraform Native Test (>= 1.6)

```hcl
# tests/waf.tftest.hcl
run "waf_has_visibility_enabled" {
  command = plan

  variables {
    environment   = "test"
    waf_scope     = "REGIONAL"
  }

  assert {
    condition     = aws_wafv2_web_acl.main.visibility_config[0].cloudwatch_metrics_enabled == true
    error_message = "WAF Web ACL must have CloudWatch metrics enabled"
  }

  assert {
    condition     = aws_wafv2_web_acl.main.visibility_config[0].sampled_requests_enabled == true
    error_message = "WAF Web ACL must have sampled requests enabled"
  }
}
```

---

## Production Considerations

### Performance

- **WAF Latency**: WAF adds ~1ms per request for REGIONAL deployments; negligible for CloudFront (evaluated at edge)
- **Rule Evaluation**: Rules evaluated in priority order — lower priority rules add cumulative evaluation time; keep high-traffic IP set lookups at priority < 10
- **Bot Control Targeted Inspection**: Uses ML — adds ~2ms additional latency vs. common inspection

### Scalability

- **WCU Limit**: 1,500 WCU per Web ACL (REGIONAL and CLOUDFRONT). Request increase via AWS Support for up to 5,000 WCU
- **IP Set Size**: Up to 10,000 addresses per IP set; up to 10 IP set references per rule statement
- **Rate-Based Rules**: Each rate-based rule can track up to 10,000 unique aggregate keys simultaneously
- **Regex Patterns**: Max 200 characters per pattern; up to 10 patterns per regex pattern set

### Monitoring & Alerting

```hcl
# Dashboard for WAF operational visibility
resource "aws_cloudwatch_dashboard" "waf" {
  dashboard_name = "${var.environment}-waf-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title  = "Blocked Requests"
          metrics = [["AWS/WAFV2", "BlockedRequests", "WebACL", aws_wafv2_web_acl.main.name, "Region", var.aws_region, "Rule", "ALL"]]
          period = 300
          stat   = "Sum"
        }
      },
      {
        type = "metric"
        properties = {
          title  = "Allowed Requests"
          metrics = [["AWS/WAFV2", "AllowedRequests", "WebACL", aws_wafv2_web_acl.main.name, "Region", var.aws_region, "Rule", "ALL"]]
          period = 300
          stat   = "Sum"
        }
      }
    ]
  })
}
```

### Security Checklist

- [ ] `scope` confirmed and correct for the protected resource type
- [ ] `aws_wafv2_web_acl_association` or `web_acl_id` confirmed in place
- [ ] `aws_wafv2_web_acl_logging_configuration` deployed and tested
- [ ] Log destination name starts with `aws-waf-logs-`
- [ ] KMS encryption on log destination
- [ ] `redacted_fields` configured for `authorization` and `cookie` headers
- [ ] `data_protection_config` configured for sensitive body fields
- [ ] `visibility_config` has `cloudwatch_metrics_enabled = true` and `sampled_requests_enabled = true` on every rule
- [ ] All managed rule groups started in COUNT mode (`override_action { count {} }`)
- [ ] At least `AWSManagedRulesCommonRuleSet` deployed (OWASP baseline)
- [ ] Rate-limiting rule deployed for IP-based flood protection
- [ ] CloudWatch alarms on BlockedRequests and AllowedRequests spike
- [ ] WCU usage tracked (`terraform output waf_web_acl_capacity_units < 1500`)
- [ ] `lifecycle { ignore_changes = [rule] }` on Web ACL (if using separate rule resources)
- [ ] `prevent_destroy = true` on Web ACL for production environments
- [ ] State file in encrypted S3 backend with DynamoDB locking

### Disaster Recovery Runbook

```bash
# 1. WAF accidentally deleted — restore from state
terraform state show aws_wafv2_web_acl.main
# Get the ID and name from the state

# 2. Re-import if Web ACL still exists in AWS but not in state
terraform import aws_wafv2_web_acl.main \
  "$(aws wafv2 list-web-acls --scope REGIONAL | jq -r '.WebACLs[] | select(.Name=="prod-web-acl") | .Id')/prod-web-acl/REGIONAL"

# 3. Re-associate after accidental association deletion
terraform apply -target=aws_wafv2_web_acl_association.alb

# 4. Temporarily disable WAF (emergency — traffic blocked by misconfigured rule)
# Option A: Disassociate WAF from resource (EMERGENCY ONLY)
aws wafv2 disassociate-web-acl --resource-arn <protected-resource-arn>
# Option B: Change default_action to allow {} and override_action to count {} on all rules

# 5. Roll back to previous rule configuration
aws s3api get-object \
  --bucket my-org-terraform-state \
  --key "prod/waf/terraform.tfstate" \
  --version-id <previous-version-id> \
  terraform.tfstate.backup
terraform state push terraform.tfstate.backup  # Restore previous state
terraform apply  # Re-apply previous configuration
```

---

## Reference Implementations

### Complete Production WAF (Root Module Example)

```hcl
# terraform.tfvars
environment           = "prod"
aws_region            = "us-east-1"
waf_scope             = "REGIONAL"
rate_limit_per_minute = 500
allowed_cidr_ranges   = ["203.0.113.0/32"]  # Office IP
blocked_cidr_ranges   = []
log_retention_days    = 90
```

```hcl
# main.tf — Complete WAF deployment
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/waf/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
  }
  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Service     = "waf"
    }
  }
}

# Web ACL (shell — rules managed separately)
resource "aws_wafv2_web_acl" "main" {
  name        = "${var.environment}-web-acl"
  description = "Web ACL for ${var.environment}"
  scope       = var.waf_scope

  default_action { allow {} }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.environment}-web-acl"
    sampled_requests_enabled   = true
  }

  lifecycle {
    ignore_changes  = [rule]
    prevent_destroy = true
  }
}

# IP Sets
resource "aws_wafv2_ip_set" "allowed" {
  name               = "${var.environment}-allowed-ips"
  scope              = var.waf_scope
  ip_address_version = "IPV4"
  addresses          = var.allowed_cidr_ranges
}

resource "aws_wafv2_ip_set" "blocked" {
  name               = "${var.environment}-blocked-ips"
  scope              = var.waf_scope
  ip_address_version = "IPV4"
  addresses          = var.blocked_cidr_ranges
}

# Priority 1 — Allow trusted IPs (bypass all rules)
resource "aws_wafv2_web_acl_rule" "allow_trusted_ips" {
  count      = length(var.allowed_cidr_ranges) > 0 ? 1 : 0
  name       = "allow-trusted-ips"
  web_acl_id = aws_wafv2_web_acl.main.id
  scope      = var.waf_scope
  priority   = 1

  action { allow {} }

  statement {
    ip_set_reference_statement {
      arn = aws_wafv2_ip_set.allowed.arn
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "allow-trusted-ips"
    sampled_requests_enabled   = true
  }
}

# Priority 5 — Rate limit by IP
resource "aws_wafv2_web_acl_rule" "rate_limit" {
  name       = "ip-rate-limit"
  web_acl_id = aws_wafv2_web_acl.main.id
  scope      = var.waf_scope
  priority   = 5

  action { block {} }

  statement {
    rate_based_statement {
      aggregate_key_type    = "IP"
      limit                 = var.rate_limit_per_minute
      evaluation_window_sec = 60
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "ip-rate-limit"
    sampled_requests_enabled   = true
  }
}

# Priority 100 — AWS Common Rule Set (OWASP Top 10 baseline)
resource "aws_wafv2_web_acl_rule" "common_ruleset" {
  name       = "AWSManagedRulesCommonRuleSet"
  web_acl_id = aws_wafv2_web_acl.main.id
  scope      = var.waf_scope
  priority   = 100

  override_action { count {} }  # Start in COUNT mode

  statement {
    managed_rule_group_statement {
      name        = "AWSManagedRulesCommonRuleSet"
      vendor_name = "AWS"
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "CommonRuleSet"
    sampled_requests_enabled   = true
  }
}

# Priority 110 — Known Bad Inputs
resource "aws_wafv2_web_acl_rule" "known_bad_inputs" {
  name       = "AWSManagedRulesKnownBadInputsRuleSet"
  web_acl_id = aws_wafv2_web_acl.main.id
  scope      = var.waf_scope
  priority   = 110

  override_action { none {} }  # Known bad inputs: safe to enforce immediately

  statement {
    managed_rule_group_statement {
      name        = "AWSManagedRulesKnownBadInputsRuleSet"
      vendor_name = "AWS"
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "KnownBadInputs"
    sampled_requests_enabled   = true
  }
}

# Logging
resource "aws_kms_key" "waf_logs" {
  description             = "KMS for WAF logs"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_cloudwatch_log_group" "waf_logs" {
  name              = "aws-waf-logs-${var.environment}"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.waf_logs.arn
}

resource "aws_wafv2_web_acl_logging_configuration" "main" {
  log_destination_configs = [aws_cloudwatch_log_group.waf_logs.arn]
  resource_arn            = aws_wafv2_web_acl.main.arn

  redacted_fields {
    single_header { name = "authorization" }
  }
  redacted_fields {
    single_header { name = "cookie" }
  }

  logging_filter {
    default_behavior = "DROP"
    filter {
      behavior    = "KEEP"
      requirement = "MEETS_ANY"
      condition {
        action_condition { action = "BLOCK" }
      }
    }
  }
}

# Outputs
output "web_acl_arn" {
  value       = aws_wafv2_web_acl.main.arn
  description = "Web ACL ARN — use in aws_wafv2_web_acl_association or CloudFront web_acl_id"
}

output "web_acl_id" {
  value       = aws_wafv2_web_acl.main.id
  description = "Web ACL ID"
}

output "waf_web_acl_capacity_units" {
  value       = aws_wafv2_web_acl.main.capacity
  description = "Current WCU usage — maximum 1,500"
}
```

---

## Source Bibliography

### Primary Sources
- [aws_wafv2_web_acl](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl) — Main resource (v6.47.0, 2026-05-28)
- [aws_wafv2_web_acl_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl_rule) — Separate rule management
- [aws_wafv2_rule_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_rule_group) — Custom rule groups
- [aws_wafv2_ip_set](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_ip_set) — IP set management
- [aws_wafv2_web_acl_association](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl_association) — Resource association
- [aws_wafv2_web_acl_logging_configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl_logging_configuration) — Logging
- [AWS WAF Developer Guide](https://docs.aws.amazon.com/waf/latest/developerguide/)
- [AWS Managed Rule Groups List](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html)
- [WAF Pricing](https://aws.amazon.com/waf/pricing/)

### Validation & Tools
- [tfsec](https://github.com/aquasecurity/tfsec) — Static security analysis
- [Checkov WAF checks](https://www.checkov.io/5.Policy%20Index/terraform.html) — Policy-as-code (CKV_AWS_192, CKV_AWS_174, CKV_AWS_175, CKV2_AWS_31)
- [Terratest](https://terratest.gruntwork.io/) — Integration testing framework
- [GitHub Issues: terraform-provider-aws WAFv2](https://github.com/hashicorp/terraform-provider-aws/issues?q=wafv2)

---

## Completion Checklist

- [x] All Terraform >= 1.7 and aws ~> 6.0 patterns validated
- [x] Known inline rule limitations documented with recommended alternative
- [x] State management strategy documented (S3 + DynamoDB)
- [x] Module architecture defined
- [x] Every anti-pattern has tested alternative
- [x] CLI commands validated with expected outputs
- [x] Integration examples: CloudFront, ALB, API Gateway, Cognito, Shield, CloudWatch, KMS
- [x] Sources link directly to registry docs (v6.47.0)
- [x] Security checklist complete
- [x] Complete root module example with .tfvars
- [x] Disaster recovery procedures documented
- [x] WCU capacity accounting included

---

## Research Gaps

```
Gap: aws_wafv2_web_acl_logging_configuration Kinesis Firehose destination details
Impact: Teams using high-volume applications may need Firehose instead of CloudWatch Logs
Workaround: Use CloudWatch Logs for < 1M req/hour; use Kinesis Firehose for higher volumes
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl_logging_configuration

Gap: aws_wafv2_web_acl_rule resource limitations vs. aws_wafv2_web_acl inline rules — official
      docs say to prefer separate resource but don't enumerate all edge cases
Impact: Teams may hit undocumented limitations during complex multi-rule deployments
Workaround: Use separate aws_wafv2_web_acl_rule resources for all production deployments
Follow-up: https://github.com/hashicorp/terraform-provider-aws/issues?q=wafv2_web_acl_rule

Gap: Exact WCU cost for AWSManagedRulesAntiDDoSRuleSet (v6.x addition)
Impact: WCU budget planning affected if deploying alongside CommonRuleSet + SQLiRuleSet
Workaround: Check aws_wafv2_web_acl.main.capacity output after first apply
Follow-up: https://docs.aws.amazon.com/waf/latest/developerguide/waf-anti-ddos-managed-rule-group.html
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Terraform configuration block and backend setup
- `visibility_config` with `cloudwatch_metrics_enabled = true` on all rules
- KMS-encrypted CloudWatch Logs group for WAF logging
- `lifecycle { ignore_changes = [rule] }` when using `aws_wafv2_web_acl_rule`
- `redacted_fields` for `authorization` and `cookie` headers
- IP set creation and rule association
- Rate-based rule with `aggregate_key_type = "IP"`

### Medium Confidence (Validate with user)
- Default action (`allow` vs. `block`)
- Managed rule group selection and WCU budget
- Rate limit threshold values
- Log filtering strategy (DROP vs. KEEP all)
- `token_domains` for Bot Control / ATP SDK integrations

### Low Confidence (Must ask user)
- CloudFront vs. REGIONAL scope (immutable after creation)
- Bot Control inspection level (Common vs. Targeted — cost difference)
- ATP login path and payload type (application-specific)
- ACFP registration/creation paths (application-specific)
- Compliance-specific requirements (PCI-DSS, HIPAA, SOC2 — affects log retention and field redaction)

### Edge Cases (When to pause)
- Scope mismatch between WAF and protected resource type detected
- WCU approaching 1,500 limit when adding new rule groups
- Rate limit change on production Web ACL (may cause legitimate traffic drops)
- `prevent_destroy = true` blocking required infrastructure teardown
- Shield auto-mitigation rules appearing in Terraform diff

### Emergency Stop
- Halt if `scope` is being changed (requires destroy-recreate — protection gap)
- Halt if `terraform destroy` planned on Web ACL associated with production resource
- Halt if logging configuration is being removed from production Web ACL
- Halt if `default_action { block {} }` is being applied to new Web ACL without established allowlist
