# Terraform AWS Shield — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - Shield (DDoS Protection)"
Cloud_Provider: "AWS"
Target_Service: "Shield (Standard + Advanced)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-28"
Domain_Complexity: "Complex"
Shield_Resources_Covered:
  - aws_shield_subscription
  - aws_shield_protection
  - aws_shield_protection_group
  - aws_shield_protection_health_check_association
  - aws_shield_application_layer_automatic_response
  - aws_shield_proactive_engagement
  - aws_shield_drt_access_role_arn_association
  - aws_shield_drt_access_log_bucket_association
  - data.aws_shield_protection
```

---

## Executive Summary

AWS Shield is AWS's managed DDoS protection service operating at two tiers: **Shield Standard** (automatic, free, L3/L4 protection for all AWS resources) and **Shield Advanced** (paid subscription providing enhanced L7 detection, automatic application-layer mitigation via AWS WAF integration, access to the Shield Response Team (SRT), proactive engagement, health-based detection, protection groups, and DDoS cost protection credits). Shield Advanced subscription costs $3,000/month per consolidated billing family (one subscription covers all accounts in the AWS Organizations family), plus DTO fees. The subscription requires a **1-year commitment** — this is the single most operationally critical fact when managing it with Terraform.

The Terraform AWS provider (v6.x) exposes eight distinct Shield resources and one data source. The resource `aws_shield_subscription` manages the actual Shield Advanced subscription — destroying it in Terraform only disables auto-renewal (within the 30-day cancellation window before renewal); it does NOT immediately cancel the subscription outside that window. Every other Shield resource (`aws_shield_protection`, `aws_shield_protection_group`, `aws_shield_application_layer_automatic_response`, `aws_shield_proactive_engagement`, `aws_shield_drt_access_role_arn_association`, `aws_shield_drt_access_log_bucket_association`, `aws_shield_protection_health_check_association`) requires an active Shield Advanced subscription as a prerequisite. Shield Standard requires no Terraform management — it is automatically active for all AWS accounts.

The three non-negotiable guardrails for any Terraform-managed Shield Advanced deployment are: **(1) `skip_destroy = true` on `aws_shield_subscription`** — removing this resource from state without being in the 30-day cancellation window will cause Terraform to set `auto_renew = DISABLED` but you remain subscribed and billed; aborting the subscription outside the window requires a support case, and Terraform cannot enforce this; **(2) every `aws_shield_protection` for a CloudFront or ALB resource must be paired with `aws_shield_application_layer_automatic_response`** — without it there is no automatic L7 DDoS mitigation, only detection; **(3) every `aws_shield_protection` must be paired with `aws_shield_protection_health_check_association`** — without a Route53 health check association, proactive SRT engagement is unavailable and detection accuracy degrades. This service is classified **Complex** due to IAM role management for SRT access, irreversible subscription state, multi-resource dependency chains, security-critical protection stack, and WAF integration requirements.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Ensures reproducibility, prevents accidental provider upgrades, and declares the deployment contract for all team members and CI pipelines. Shield manages a financial subscription — accidental upgrades that introduce breaking changes can affect billing state management.

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
    key            = "prod/shield/terraform.tfstate"
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

#### Pattern: Provider Configuration with IAM Role Assumption and Default Tags

**Why**: Credentials must never be hardcoded. `assume_role` enables cross-account deployments and CI/CD pipelines without static credentials. `default_tags` enforces tagging compliance on all Shield resources (protection objects support tagging) without per-resource tag blocks.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "terraform-shield-${var.environment}"
  }

  default_tags {
    tags = {
      Environment = var.environment
      Service     = "shield"
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [AWS Provider Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference)

---

#### Pattern: Shield Advanced Subscription with Destroy Safety

**Why**: The subscription requires a 1-year commitment. `skip_destroy = true` prevents Terraform from modifying `auto_renew` during destroy operations outside the 30-day cancellation window — this avoids a state management mismatch where Terraform removes the resource from state but billing continues. The `auto_renew = "ENABLED"` is the default and recommended value for production.

```hcl
resource "aws_shield_subscription" "main" {
  auto_renew = "ENABLED"

  # CRITICAL: Set skip_destroy = true to prevent Terraform from
  # attempting to disable auto-renewal outside the 30-day cancellation window.
  # Destruction only sets auto_renew = DISABLED — it does NOT cancel the subscription.
  # To unsubscribe outside the window, contact AWS Support.
  skip_destroy = true

  lifecycle {
    # Prevent accidental destruction of the subscription
    prevent_destroy = true
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_shield_subscription](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_subscription)

---

#### Pattern: Resource Protection for Internet-Facing Resources

**Why**: Shield Advanced protections are NOT automatic — each resource must be explicitly registered. Terraform manages this registration via `aws_shield_protection`. Every internet-facing resource (CloudFront distributions, Route53 hosted zones, ELBs, Elastic IPs, Global Accelerator accelerators) must be explicitly protected.

```hcl
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_partition" "current" {}

# Protect a CloudFront distribution
resource "aws_shield_protection" "cloudfront" {
  name         = "${var.app_name}-cloudfront-${var.environment}"
  resource_arn = aws_cloudfront_distribution.main.arn

  tags = {
    Name        = "${var.app_name}-cloudfront-protection"
    ResourceType = "cloudfront"
  }

  depends_on = [aws_shield_subscription.main]
}

# Protect an Application Load Balancer (use regional ARN)
resource "aws_shield_protection" "alb" {
  name         = "${var.app_name}-alb-${var.environment}"
  resource_arn = aws_lb.main.arn

  tags = {
    Name        = "${var.app_name}-alb-protection"
    ResourceType = "alb"
  }

  depends_on = [aws_shield_subscription.main]
}

# Protect a Route53 hosted zone
resource "aws_shield_protection" "route53" {
  name         = "${var.app_name}-route53-${var.environment}"
  resource_arn = "arn:${data.aws_partition.current.partition}:route53:::hostedzone/${aws_route53_zone.main.zone_id}"

  tags = {
    Name        = "${var.app_name}-route53-protection"
    ResourceType = "route53"
  }

  depends_on = [aws_shield_subscription.main]
}

# Protect an Elastic IP (for EC2 or NLB)
resource "aws_shield_protection" "eip" {
  name         = "${var.app_name}-eip-${var.environment}"
  resource_arn = "arn:${data.aws_partition.current.partition}:ec2:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:eip-allocation/${aws_eip.main.id}"

  tags = {
    Name        = "${var.app_name}-eip-protection"
    ResourceType = "eip"
  }

  depends_on = [aws_shield_subscription.main]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_shield_protection](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_protection)

---

#### Pattern: Health Check Association for All Protections

**Why**: Route53 health check association is the prerequisite for proactive SRT engagement and health-based detection. Without it, Shield Advanced cannot differentiate legitimate traffic spikes from DDoS attacks — degrading detection accuracy and making proactive engagement unavailable. All protections except Route53 hosted zones support health check association.

```hcl
# Route53 health check monitoring the application endpoint
resource "aws_route53_health_check" "app" {
  fqdn              = var.app_domain
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"

  tags = {
    Name        = "${var.app_name}-health-check-${var.environment}"
    ManagedBy   = "terraform"
  }
}

# Associate health check with CloudFront protection
resource "aws_shield_protection_health_check_association" "cloudfront" {
  health_check_arn     = aws_route53_health_check.app.arn
  shield_protection_id = aws_shield_protection.cloudfront.id
}

# Associate health check with ALB protection
resource "aws_shield_protection_health_check_association" "alb" {
  health_check_arn     = aws_route53_health_check.app.arn
  shield_protection_id = aws_shield_protection.alb.id
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_shield_protection_health_check_association](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_protection_health_check_association)

---

#### Pattern: Automatic Application Layer DDoS Mitigation

**Why**: Manual response to L7 DDoS attacks is too slow — attacks can saturate origin capacity within seconds. `aws_shield_application_layer_automatic_response` enables Shield Advanced to automatically enforce WAF rate-based rules against known DDoS sources. Only supported for CloudFront distributions and ALBs. Start in `COUNT` mode, switch to `BLOCK` once false-positive baseline is validated.

```hcl
# Automatic response for CloudFront — start in COUNT mode
resource "aws_shield_application_layer_automatic_response" "cloudfront" {
  resource_arn = aws_cloudfront_distribution.main.arn

  # Start with COUNT to validate detection accuracy before switching to BLOCK
  # Switch to BLOCK once false-positive rate is confirmed acceptable
  action = var.shield_auto_response_action # "COUNT" or "BLOCK"

  depends_on = [aws_shield_protection.cloudfront]
}

# Automatic response for ALB — start in COUNT mode
resource "aws_shield_application_layer_automatic_response" "alb" {
  resource_arn = aws_lb.main.arn
  action       = var.shield_auto_response_action

  depends_on = [aws_shield_protection.alb]
}

# Variable with validation
variable "shield_auto_response_action" {
  type        = string
  description = "Shield Advanced automatic L7 DDoS mitigation action. Start with COUNT, switch to BLOCK after baseline validation."
  default     = "COUNT"

  validation {
    condition     = contains(["COUNT", "BLOCK"], var.shield_auto_response_action)
    error_message = "Action must be COUNT (observe) or BLOCK (actively mitigate)."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_shield_application_layer_automatic_response](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_application_layer_automatic_response)

---

#### Pattern: Protection Groups for Aggregate Detection

**Why**: Protection groups enable Shield Advanced to detect attacks distributed across multiple resources in an application. A distributed attack targeting multiple CloudFront distributions or ALBs simultaneously may fall below individual detection thresholds but be detected at the group aggregate level. Use `for_each` to create multiple groups for different resource types.

```hcl
# Group all protected resources for aggregate detection
resource "aws_shield_protection_group" "all_resources" {
  protection_group_id = "${var.app_name}-all-${var.environment}"
  aggregation         = "MAX"
  pattern             = "ALL"

  tags = {
    Name = "${var.app_name}-all-protections-group"
  }

  depends_on = [
    aws_shield_protection.cloudfront,
    aws_shield_protection.alb,
    aws_shield_protection.route53,
  ]
}

# Group by resource type for type-specific aggregate detection
resource "aws_shield_protection_group" "cloudfront_resources" {
  protection_group_id = "${var.app_name}-cloudfront-${var.environment}"
  aggregation         = "SUM"
  pattern             = "BY_RESOURCE_TYPE"
  resource_type       = "CLOUDFRONT_DISTRIBUTION"

  tags = {
    Name = "${var.app_name}-cloudfront-group"
  }

  depends_on = [aws_shield_subscription.main]
}

# Group specific arbitrary resources (e.g., EIPs for an NLB fleet)
resource "aws_shield_protection_group" "eip_group" {
  protection_group_id = "${var.app_name}-eips-${var.environment}"
  aggregation         = "MEAN"
  pattern             = "ARBITRARY"
  members             = [
    "arn:${data.aws_partition.current.partition}:ec2:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:eip-allocation/${aws_eip.main.id}",
  ]

  tags = {
    Name = "${var.app_name}-eip-group"
  }

  depends_on = [aws_shield_protection.eip]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_shield_protection_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_protection_group)

---

#### Pattern: SRT IAM Role for Proactive Access

**Why**: The Shield Response Team requires pre-authorized IAM role access to respond to DDoS events without waiting for manual authorization during an active attack. `aws_shield_drt_access_role_arn_association` grants the SRT the ability to use this role. The role must use the AWS-managed policy `AWSShieldDRTAccessPolicy`. This is a prerequisite for `aws_shield_proactive_engagement`.

```hcl
# IAM role for SRT to assume during DDoS events
resource "aws_iam_role" "shield_srt" {
  name        = "shield-srt-role-${var.environment}"
  description = "Role for AWS Shield Response Team to access WAF and Route53 during DDoS events"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ShieldSRTAssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "drt.shield.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name      = "shield-srt-role"
    Purpose   = "SRT DDoS response access"
    ManagedBy = "terraform"
  }
}

# Attach AWS-managed SRT access policy (required — do NOT use custom policy)
resource "aws_iam_role_policy_attachment" "shield_srt" {
  role       = aws_iam_role.shield_srt.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSShieldDRTAccessPolicy"
}

# Grant SRT access to the role
resource "aws_shield_drt_access_role_arn_association" "main" {
  role_arn = aws_iam_role.shield_srt.arn

  depends_on = [
    aws_iam_role_policy_attachment.shield_srt,
    aws_shield_subscription.main,
  ]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_shield_drt_access_role_arn_association](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_drt_access_role_arn_association)

---

#### Pattern: Proactive Engagement Configuration

**Why**: Proactive engagement authorizes the SRT to contact the security team when a Route53 health check associated with a protected resource becomes unhealthy during a detected DDoS event — eliminating the support-case delay. Requires at least one phone number in the emergency contact list and an active `aws_shield_drt_access_role_arn_association`.

```hcl
resource "aws_shield_proactive_engagement" "main" {
  enabled = true

  # IMPORTANT: contacts defined here REPLACE existing contacts — not append.
  # At least one phone number is required for proactive engagement to function.
  emergency_contact {
    email_address = var.soc_primary_email
    phone_number  = var.soc_primary_phone  # Format: +12358132134
    contact_notes = "Primary SOC on-call — DDoS events for ${var.app_name}"
  }

  emergency_contact {
    email_address = var.soc_secondary_email
    phone_number  = var.soc_secondary_phone
    contact_notes = "Secondary escalation — ${var.app_name} DDoS"
  }

  # Must have SRT role access before enabling proactive engagement
  depends_on = [aws_shield_drt_access_role_arn_association.main]
}

variable "soc_primary_phone" {
  type        = string
  description = "Primary SOC contact phone number for Shield proactive engagement. Format: +XXXXXXXXXXX"
  sensitive   = true

  validation {
    condition     = can(regex("^\\+[1-9][0-9]{4,14}$", var.soc_primary_phone))
    error_message = "Phone number must start with + followed by 5-15 digits (E.164 format)."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_shield_proactive_engagement](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_proactive_engagement)

---

#### Pattern: Variable Validation & Type Safety

**Why**: Prevents misconfigured Shield deployments at `terraform plan` time — before any resources are created. Shield resources depend on each other in a strict chain; invalid inputs can cause confusing apply-time errors deep in the dependency graph.

```hcl
variable "aws_region" {
  type        = string
  description = "AWS region for Shield-protected resources"
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "Region must be a valid AWS region format (e.g., us-east-1, eu-west-1)."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "shield_protection_group_aggregation" {
  type        = string
  description = "Aggregation method for protection groups. MAX = most attacked resource drives detection. SUM = total across all. MEAN = average."
  default     = "MAX"

  validation {
    condition     = contains(["SUM", "MEAN", "MAX"], var.shield_protection_group_aggregation)
    error_message = "Aggregation must be SUM, MEAN, or MAX."
  }
}

variable "account_id" {
  type        = string
  description = "AWS account ID where Shield is deployed"

  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Account ID must be exactly 12 digits."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

#### Pattern: CloudWatch Monitoring for DDoS Metrics

**Why**: Shield Advanced metrics are only accessible through CloudWatch. Without alarms on `DDoSDetected` and attack volume metrics, the security team has no automated notification during active attacks. All Shield metrics require Shield Advanced subscription.

```hcl
resource "aws_cloudwatch_metric_alarm" "ddos_detected_cloudfront" {
  alarm_name          = "${var.app_name}-ddos-detected-cloudfront-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "DDoSDetected"
  namespace           = "AWS/DDoSProtection"
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "DDoS attack detected on CloudFront distribution ${var.app_name}"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
  ok_actions          = [aws_sns_topic.security_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    ResourceArn = aws_cloudfront_distribution.main.arn
  }

  tags = {
    Name = "${var.app_name}-ddos-detected-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "ddos_attack_volume" {
  alarm_name          = "${var.app_name}-ddos-rps-cloudfront-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DDoSAttackRequestsPerSecond"
  namespace           = "AWS/DDoSProtection"
  period              = "60"
  statistic           = "Maximum"
  threshold           = var.ddos_rps_threshold
  alarm_description   = "DDoS attack requests per second exceeded threshold for ${var.app_name}"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    ResourceArn = aws_cloudfront_distribution.main.arn
  }

  tags = {
    Name = "${var.app_name}-ddos-rps-alarm"
  }
}

variable "ddos_rps_threshold" {
  type        = number
  description = "L7 DDoS attack requests/second threshold for CloudWatch alarm"
  default     = 10000

  validation {
    condition     = var.ddos_rps_threshold > 0
    error_message = "DDoS RPS threshold must be a positive number."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [AWS Shield Metrics](https://docs.aws.amazon.com/waf/latest/developerguide/shield-metrics.html)

---

### ⚠️ Conditional Patterns

---

#### Decision: Shield Standard vs. Shield Advanced

| Option | Optimizes | Sacrifices | Scaling | State | Cost |
|--------|-----------|------------|---------|-------|------|
| **Shield Standard** | Cost ($0) — automatic L3/L4 protection | L7 detection, SRT access, proactive engagement, cost protection, detailed visibility | No scaling costs | No state to manage | $0 |
| **Shield Advanced** | Protection depth, visibility, response time, cost predictability | Budget — $3,000/mo fixed + DTO fees; 1-year commitment | DTO fees scale with protected resource traffic | Subscription state in Terraform — `prevent_destroy` required | $3,000/mo + DTO |

- **Tradeoffs**:
  - Standard is always active (no Terraform management needed). Advanced adds 8 new Terraform resources.
  - Standard does NOT provide: L7 detection, SRT access, health-based detection, proactive engagement, protection groups, DDoS cost protection, detailed attack telemetry.
  - Advanced includes WAF costs for protected resources (up to 1,500 WCUs, 50B requests/month) — offsets WAF billing.
  - One subscription per consolidated billing family — 10 accounts protected for $3,000/mo total.
- **When**: Standard for dev/staging, non-critical workloads, or applications without availability SLAs. Advanced for production applications with SLAs, regulated industries, high-value DDoS targets.
- **Agent**: "Ask user: Does this application have an availability SLA with customers, or is it a high-value target for DDoS attacks? Is this a production environment with regulatory requirements?"
- **Source**: [Shield Advanced vs Standard](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-deciding.html)

---

#### Decision: Automatic Mitigation Mode — COUNT vs. BLOCK

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **COUNT** | Visibility, safety — detects without blocking | Response time — attack traffic still reaches origin | New deployment, initial baseline validation, high false-positive risk apps |
| **BLOCK** | Response time — immediate automated blocking | Risk of false positives blocking legitimate traffic | Established baselines, high-volume attack targets, confirmed low false-positive rate |

- **When**: Start all new deployments in `COUNT`. Switch to `BLOCK` only after monitoring for at least 2 weeks with zero unexpected WAF blocks in CloudWatch Logs. `action` attribute is instantly switchable with no downtime.
- **Agent**: "Ask user: Has this deployment been in COUNT mode long enough to confirm that Shield detection has zero false positives? (Recommended: 2+ weeks of production traffic)"
- **Source**: [Automatic Application Layer Response](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html)

---

#### Decision: Individual Resource Protection vs. Protection Groups Pattern

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Individual only** | Granular per-resource visibility, simpler config | May miss distributed attacks across resources | Single-resource apps, independent services |
| **Protection groups only** | Aggregate detection, distributed attack coverage | Per-resource granularity may be masked | Complex multi-resource apps |
| **Both (recommended)** | Maximum detection coverage at all granularities | More Terraform resources to manage | All production Shield Advanced deployments |

- **When**: Always use both for production. Protection groups have no additional cost.
- **Agent**: "Ask user: Are there multiple entry points (CloudFront distributions, ALBs, EIPs) that serve the same application and could be targeted simultaneously?"
- **Source**: [Shield Protection Groups](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-protection-groups.html)

---

#### Decision: SRT Log Access — Grant S3 Bucket Access or Not

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **No S3 access granted** | Simpler config, no cross-service IAM | SRT cannot access flow logs — limits forensic capability during attacks | Baseline Shield Advanced setup, low-severity applications |
| **S3 log bucket access** | SRT can access VPC Flow Logs and WAF logs for deeper forensic analysis | Additional IAM configuration, S3 bucket policy complexity | Mission-critical apps, regulated industries, maximum SRT capability |

- **When**: Grant S3 access if maximum SRT response capability is required and you have VPC Flow Logs or WAF logs stored in S3.
- **Agent**: "Ask user: Do you want to grant the Shield Response Team access to your S3 flow logs and WAF logs for maximum forensic capability during attacks?"
- **Source**: [aws_shield_drt_access_log_bucket_association](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_drt_access_log_bucket_association)

---

#### Decision: Subscription Management — `prevent_destroy` vs. `skip_destroy`

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **`prevent_destroy = true`** | Prevents accidental `terraform destroy` from removing subscription resource | Must explicitly remove lifecycle rule to intentionally cancel | Production — highest safety, recommended |
| **`skip_destroy = true`** | Prevents auto-renewal change on destroy (state removal only) | Less protection — `terraform destroy` still removes from state | When destroy workflows are needed but subscription cancellation is manual |
| **Neither** | Flexibility | Risk — `terraform destroy` will set `auto_renew = DISABLED` | NEVER in production — the subscription persists with billing |

- **When**: Always use `prevent_destroy = true` in production. Use `skip_destroy = true` only in environments where destroy workflows are automated and subscription management is handled manually.
- **Agent**: "Ask user: Is this a production Shield Advanced subscription that should never be accidentally destroyed?"
- **Source**: [aws_shield_subscription](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_subscription)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Managing Shield Subscription Without `prevent_destroy`

```hcl
# DON'T
resource "aws_shield_subscription" "main" {
  auto_renew = "ENABLED"
  # No lifecycle protection — terraform destroy will set auto_renew = DISABLED
  # AND if within 30-day window, will queue cancellation
}
```

**Why**: A `terraform destroy` or accidental removal of this resource from the configuration will set `auto_renew = DISABLED`. If this happens within the 30-day cancellation window before subscription renewal, the subscription will NOT renew and Shield Advanced protection ceases — leaving all resources unprotected with no mitigation, no SRT access, and no DDoS cost protection.

```hcl
# DO
resource "aws_shield_subscription" "main" {
  auto_renew   = "ENABLED"
  skip_destroy = true

  lifecycle {
    prevent_destroy = true
  }
}
```

- **Impact**: `CRITICAL` — All Shield Advanced protections cease. No automatic L7 mitigation. No SRT access. No DDoS cost protection. Billing continues until window closes.
- **Severity**: CRITICAL
- **Source**: [aws_shield_subscription destruction notes](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_subscription)

---

#### Anti-Pattern: Protecting CloudFront/ALB Without Automatic Response

```hcl
# DON'T
resource "aws_shield_protection" "cloudfront" {
  name         = "my-app-cloudfront"
  resource_arn = aws_cloudfront_distribution.main.arn
}
# Missing: aws_shield_application_layer_automatic_response
# Result: Shield detects L7 attacks but does NOT automatically mitigate them
```

**Why**: Without `aws_shield_application_layer_automatic_response`, Shield Advanced can DETECT L7 DDoS attacks but takes NO automated action. During an active attack, manual intervention is required — and L7 floods can saturate origin capacity within seconds before a human can respond.

```hcl
# DO — always pair protection with automatic response for CloudFront and ALB
resource "aws_shield_protection" "cloudfront" {
  name         = "my-app-cloudfront"
  resource_arn = aws_cloudfront_distribution.main.arn
  depends_on   = [aws_shield_subscription.main]
}

resource "aws_shield_application_layer_automatic_response" "cloudfront" {
  resource_arn = aws_cloudfront_distribution.main.arn
  action       = "COUNT"  # Start with COUNT, switch to BLOCK after baseline validation
  depends_on   = [aws_shield_protection.cloudfront]
}
```

- **Impact**: `CRITICAL` — L7 DDoS attacks detected but not mitigated automatically. Origin availability at risk during attack windows. Manual intervention required within seconds for effective response.
- **Severity**: CRITICAL
- **Source**: [aws_shield_application_layer_automatic_response](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_application_layer_automatic_response)

---

#### Anti-Pattern: Shield Advanced Without Health Check Associations

```hcl
# DON'T
resource "aws_shield_protection" "alb" {
  name         = "my-app-alb"
  resource_arn = aws_lb.main.arn
}
# Missing: aws_shield_protection_health_check_association
# Result: No health-based detection, no proactive engagement available
```

**Why**: Without Route53 health check associations, Shield Advanced cannot use application health status to improve detection accuracy. False positives increase, detection thresholds are less precise, and the SRT cannot proactively engage — they can only respond after you open a support case.

```hcl
# DO — always associate health checks with each protection
resource "aws_route53_health_check" "alb" {
  fqdn              = var.app_domain
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
}

resource "aws_shield_protection_health_check_association" "alb" {
  health_check_arn     = aws_route53_health_check.alb.arn
  shield_protection_id = aws_shield_protection.alb.id
}
```

- **Impact**: `HIGH` — Delayed detection, increased false positives, proactive SRT engagement unavailable. Shield Advanced value significantly degraded.
- **Severity**: HIGH
- **Source**: [aws_shield_protection_health_check_association](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_protection_health_check_association)

---

#### Anti-Pattern: Proactive Engagement Without SRT Role Access

```hcl
# DON'T
resource "aws_shield_proactive_engagement" "main" {
  enabled = true

  emergency_contact {
    email_address = "soc@example.com"
    phone_number  = "+12358132134"
    contact_notes = "SOC on-call"
  }
}
# Missing: aws_shield_drt_access_role_arn_association
# Result: apply error — proactive engagement requires SRT IAM role pre-configured
```

**Why**: Terraform will fail to apply `aws_shield_proactive_engagement` if `aws_shield_drt_access_role_arn_association` has not been applied first. More critically, even if Terraform somehow configures this, the SRT cannot take action during a DDoS event without the IAM role to access your WAF and Route53 resources.

```hcl
# DO — explicit depends_on to enforce correct order
resource "aws_shield_proactive_engagement" "main" {
  enabled = true

  emergency_contact {
    email_address = var.soc_email
    phone_number  = var.soc_phone
    contact_notes = "Primary SOC contact"
  }

  depends_on = [aws_shield_drt_access_role_arn_association.main]
}
```

- **Impact**: `HIGH` — Apply-time Terraform error OR SRT cannot respond during active attack even with proactive engagement "enabled".
- **Severity**: HIGH
- **Source**: [aws_shield_proactive_engagement](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_proactive_engagement)

---

#### Anti-Pattern: Protecting Non-Internet-Facing Resources

```hcl
# DON'T
# Internal ALB (no public DNS, inside VPC only)
resource "aws_shield_protection" "internal_alb" {
  name         = "internal-service-alb"
  resource_arn = aws_lb.internal.arn  # Internal ALB not internet-accessible
}
# Result: Paying Shield Advanced DTO fees for a resource that cannot receive
# internet DDoS attacks — wasting money with zero security value
```

**Why**: Shield Advanced DTO fees apply per GB transferred on protected resources. Protecting internal-only resources that are not reachable from the internet provides zero DDoS protection value while adding cost.

```hcl
# DO — protect only internet-facing resources
locals {
  internet_facing_protections = {
    "cloudfront" = aws_cloudfront_distribution.main.arn
    "public-alb" = aws_lb.public.arn  # public-facing ALB only
  }
}

resource "aws_shield_protection" "internet_facing" {
  for_each     = local.internet_facing_protections
  name         = "${var.app_name}-${each.key}-${var.environment}"
  resource_arn = each.value
  depends_on   = [aws_shield_subscription.main]
}
```

- **Impact**: `MEDIUM` — Financial waste. DTO fees on internal resources with zero security ROI.
- **Severity**: MEDIUM
- **Source**: [Shield Advanced Pricing](https://aws.amazon.com/shield/pricing/)

---

#### Anti-Pattern: Hardcoded Emergency Contact Information

```hcl
# DON'T
resource "aws_shield_proactive_engagement" "main" {
  enabled = true
  emergency_contact {
    email_address = "john.doe@example.com"    # hardcoded — breaks when personnel changes
    phone_number  = "+12125551234"            # hardcoded — personal number in version control
  }
}
```

**Why**: Emergency contact information in version control creates operational risk (numbers become stale as personnel changes) and privacy risk (personal phone numbers in git history). Contact updates require code changes rather than parameter updates.

```hcl
# DO — use sensitive variables or SSM Parameter Store
data "aws_ssm_parameter" "soc_phone" {
  name            = "/shield/${var.environment}/soc-primary-phone"
  with_decryption = true
}

resource "aws_shield_proactive_engagement" "main" {
  enabled = true
  emergency_contact {
    email_address = var.soc_primary_email
    phone_number  = data.aws_ssm_parameter.soc_phone.value
    contact_notes = "Primary SOC — ${var.app_name} ${var.environment}"
  }
  depends_on = [aws_shield_drt_access_role_arn_association.main]
}
```

- **Impact**: `HIGH` — Stale contact information during DDoS attack means proactive engagement notification goes to wrong person/number. Security incident response delayed.
- **Severity**: HIGH
- **Source**: [AWS SSM Parameter Store Secure Strings](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-securestring.html)

---

#### Anti-Pattern: No Tags on Shield Protections

```hcl
# DON'T
resource "aws_shield_protection" "cloudfront" {
  name         = "cloudfront-protection"
  resource_arn = aws_cloudfront_distribution.main.arn
  # No tags — cannot track cost, ownership, or compliance
}
```

**Why**: Shield protection objects support tags. Without tags, cost attribution is impossible (DTO fees cannot be tracked per protected resource), compliance audits cannot identify ownership, and automation cannot filter protections by environment.

```hcl
# DO — tag all protection objects
resource "aws_shield_protection" "cloudfront" {
  name         = "${var.app_name}-cloudfront-${var.environment}"
  resource_arn = aws_cloudfront_distribution.main.arn

  tags = {
    Name         = "${var.app_name}-cloudfront-protection"
    ResourceType = "cloudfront"
    Application  = var.app_name
  }
  # Note: default_tags from provider block also propagate to shield_protection
}
```

- **Impact**: `MEDIUM` — Cost blindness, compliance gaps, inability to automate protection audits by environment.
- **Severity**: MEDIUM
- **Source**: [AWS Resource Tagging Strategy](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)

---

## State Management Deep Dive

### Local Development State (Shield Standard Only)

```hcl
# Use local state only for non-Shield-Advanced configurations
# Shield Standard requires no Terraform resources — it is automatic
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  # Local backend acceptable only when no aws_shield_subscription is managed
}
```

- **Risk**: Single point of failure, no sharing, no locking
- **When**: Solo development of WAF/CloudFront configurations without Shield Advanced subscription management

### Production Remote State (S3 + DynamoDB) — Required for Shield Advanced

```hcl
# DynamoDB table for state locking (run once, bootstrap separately)
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

# Backend configuration for Shield state
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/shield/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

- **Benefit**: Team access, state locking prevents concurrent subscription modifications, version history enables rollback auditing
- **Critical**: State locking is mandatory for Shield — concurrent applies could create duplicate protection objects or toggle subscription state unpredictably

### Shield State Sensitivity Handling

```hcl
# Shield outputs that should be marked sensitive
output "shield_subscription_id" {
  value       = aws_shield_subscription.main.id
  sensitive   = false  # Account ID — not secret, but no need to expose
  description = "AWS Account ID of the Shield Advanced subscription"
}

output "srt_role_arn" {
  value       = aws_iam_role.shield_srt.arn
  sensitive   = false
  description = "ARN of the IAM role granted to the Shield Response Team"
}

output "protection_ids" {
  value = {
    for k, v in aws_shield_protection.internet_facing :
    k => v.id
  }
  sensitive   = false
  description = "Map of protection name to Shield protection ID"
}

# SRT contact phone numbers are sensitive — use SSM, not outputs
# Never output phone numbers or email addresses from emergency contacts
```

---

## Module Architecture

### Standard Shield Module Structure

```
modules/
└── shield/
    ├── main.tf          # aws_shield_subscription, aws_shield_protection, etc.
    ├── variables.tf     # All input variables with validation
    ├── outputs.tf       # Protection IDs, protection group ARNs
    ├── cloudwatch.tf    # CloudWatch alarms for DDoS metrics
    ├── iam.tf           # SRT IAM role and policy attachment
    ├── versions.tf      # Required providers block
    └── README.md        # Module documentation
```

### Module Definition Example

```hcl
# modules/shield/variables.tf

variable "subscription_enabled" {
  type        = bool
  description = "Whether to manage Shield Advanced subscription. Set false for Shield Standard only environments."
  default     = true
}

variable "protected_resources" {
  type = map(object({
    resource_arn          = string
    enable_auto_response  = bool
    health_check_fqdn     = optional(string)
    health_check_path     = optional(string, "/health")
  }))
  description = "Map of resource name to Shield protection configuration"
  default     = {}
}

variable "protection_groups" {
  type = map(object({
    aggregation   = string
    pattern       = string
    resource_type = optional(string)
    members       = optional(list(string), [])
  }))
  description = "Map of protection group name to configuration"
  default     = {}

  validation {
    condition = alltrue([
      for k, v in var.protection_groups :
      contains(["SUM", "MEAN", "MAX"], v.aggregation)
    ])
    error_message = "Protection group aggregation must be SUM, MEAN, or MAX."
  }
}

# modules/shield/outputs.tf
output "protection_ids" {
  value = {
    for k, v in aws_shield_protection.resources :
    k => v.id
  }
  description = "Shield protection IDs — use for cross-stack references to health check associations"
}

output "protection_arns" {
  value = {
    for k, v in aws_shield_protection.resources :
    k => v.arn
  }
  description = "Shield protection ARNs"
}

output "protection_group_arns" {
  value = {
    for k, v in aws_shield_protection_group.groups :
    k => v.protection_group_arn
  }
  description = "Shield protection group ARNs for cross-stack event monitoring"
}

# root/main.tf — Using the module
module "shield" {
  source = "./modules/shield"

  subscription_enabled = var.environment == "prod"
  app_name             = var.app_name
  environment          = var.environment
  aws_region           = var.aws_region
  account_id           = data.aws_caller_identity.current.account_id

  protected_resources = {
    cloudfront = {
      resource_arn         = module.cdn.cloudfront_arn
      enable_auto_response = true
      health_check_fqdn    = var.app_domain
      health_check_path    = "/health"
    }
    public_alb = {
      resource_arn         = module.alb.lb_arn
      enable_auto_response = true
      health_check_fqdn    = var.app_domain
    }
  }

  protection_groups = {
    all = {
      aggregation = "MAX"
      pattern     = "ALL"
    }
    cloudfront_type = {
      aggregation   = "SUM"
      pattern       = "BY_RESOURCE_TYPE"
      resource_type = "CLOUDFRONT_DISTRIBUTION"
    }
  }
}
```

---

## Integration Patterns

### Integration: Terraform ↔ AWS WAF

**Pattern**: WAF web ACL association is prerequisite for Shield Advanced L7 detection and automatic mitigation. Shield Advanced adds a managed rule group (150 WCUs) to the web ACL when automatic response is enabled.

```hcl
# WAF web ACL with rate-based rules (prerequisite for Shield Advanced L7 protection)
resource "aws_wafv2_web_acl" "main" {
  name        = "${var.app_name}-waf-${var.environment}"
  description = "WAF ACL for ${var.app_name} — Shield Advanced integration"
  scope       = "CLOUDFRONT"  # Use REGIONAL for ALB
  provider    = aws.us_east_1  # CloudFront WAF must be in us-east-1

  default_action {
    allow {}
  }

  # Rate-based rule — first line of L7 defense
  rule {
    name     = "RateLimitPerIP"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.waf_rate_limit_per_ip
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.app_name}-rate-limit-per-ip"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules — Core Rule Set
  rule {
    name     = "AWSManagedRulesCoreRuleSet"
    priority = 2

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
      metric_name                = "${var.app_name}-managed-rules-core"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.app_name}-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Name = "${var.app_name}-waf-${var.environment}"
  }
}

# Associate WAF with CloudFront — required before aws_shield_application_layer_automatic_response
resource "aws_cloudfront_distribution" "main" {
  web_acl_id = aws_wafv2_web_acl.main.arn
  # ... rest of CloudFront config
}

variable "waf_rate_limit_per_ip" {
  type        = number
  description = "WAF rate limit per IP per 5 minutes. Set to 2-5x your normal peak per-IP rate."
  default     = 2000

  validation {
    condition     = var.waf_rate_limit_per_ip >= 100
    error_message = "WAF rate limit must be at least 100 requests per 5 minutes."
  }
}
```

- **Versions**:
  | Resource | Min Provider | Max Provider |
  |----------|-------------|-------------|
  | `aws_wafv2_web_acl` | ~> 6.0 | latest |
  | `aws_shield_application_layer_automatic_response` | ~> 6.0 | latest |

- **Issues**: Shield Advanced automatic response adds a `ShieldMitigationRuleGroup` consuming 150 WCUs to the web ACL. Verify `default_capacity_handling_behavior` on your web ACL can accommodate this. Regional WAF for ALB must be in the same region as the ALB. CloudFront WAF must be in `us-east-1`.
- **Source**: [AWS WAF + Shield Integration](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-app-layer-protections.html)

---

### Integration: Terraform ↔ Amazon CloudFront

**Pattern**: CloudFront distribution is the primary edge layer that benefits from Shield Standard's continuous inline mitigation. Shield Advanced then adds enhanced detection and automatic L7 mitigation on top.

```hcl
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  price_class         = "PriceClass_All"
  web_acl_id          = aws_wafv2_web_acl.main.arn

  origin {
    domain_name              = aws_lb.main.dns_name
    origin_id                = "alb-origin"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "alb-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      cookies { forward = "none" }
    }
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name = "${var.app_name}-cloudfront-${var.environment}"
  }
}

# Shield protection must use the distribution ARN
resource "aws_shield_protection" "cloudfront" {
  name         = "${var.app_name}-cloudfront-${var.environment}"
  resource_arn = aws_cloudfront_distribution.main.arn
  depends_on   = [aws_shield_subscription.main]
}
```

- **Issues**: CloudFront ARN format for Shield must be `arn:aws:cloudfront::ACCOUNT_ID:distribution/DISTRIBUTION_ID` — Terraform provides this via `aws_cloudfront_distribution.main.arn`. Shield Advanced automatic response is only available for CloudFront and ALB (not NLB or EC2 directly).
- **Source**: [aws_cloudfront_distribution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_distribution)

---

### Integration: Terraform ↔ Amazon Route53

**Pattern**: Route53 hosted zone protection and health check creation for health-based detection.

```hcl
resource "aws_route53_zone" "main" {
  name = var.domain_name
  tags = { Name = var.domain_name }
}

# Protect the hosted zone
resource "aws_shield_protection" "route53_zone" {
  name         = "${var.app_name}-route53-${var.environment}"
  resource_arn = "arn:${data.aws_partition.current.partition}:route53:::hostedzone/${aws_route53_zone.main.zone_id}"
  depends_on   = [aws_shield_subscription.main]
}

# Health check for application endpoint
resource "aws_route53_health_check" "app_https" {
  fqdn              = var.app_domain
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
  # Check from multiple regions for accuracy
  regions = ["us-east-1", "eu-west-1", "ap-southeast-1"]

  tags = { Name = "${var.app_name}-health-check" }
}

# Note: Route53 hosted zones do NOT support health check associations
# Only EIPs, CloudFront distributions, ALBs, and Global Accelerators support it
# aws_shield_protection_health_check_association is NOT valid for route53 zone protections
```

- **Issues**: Route53 hosted zone is the only protected resource type that does NOT support `aws_shield_protection_health_check_association`. Do not attempt to create a health check association for a Route53 zone protection — it will fail at apply time.
- **Source**: [aws_route53_health_check](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_health_check)

---

### Integration: Terraform ↔ CloudWatch + SNS

**Pattern**: Automated DDoS event notification through CloudWatch → SNS → Security team.

```hcl
resource "aws_sns_topic" "security_alerts" {
  name              = "${var.app_name}-security-alerts-${var.environment}"
  kms_master_key_id = var.sns_kms_key_id  # Encrypt SNS topic at rest

  tags = { Name = "${var.app_name}-security-alerts" }
}

resource "aws_sns_topic_subscription" "security_email" {
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = var.security_alerts_email
}

# DDoS detection alarm — fires when any protected resource is under attack
resource "aws_cloudwatch_metric_alarm" "ddos_detected" {
  for_each = aws_shield_protection.internet_facing

  alarm_name          = "${var.app_name}-ddos-detected-${each.key}-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "DDoSDetected"
  namespace           = "AWS/DDoSProtection"
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "DDoS attack detected on ${each.key} for ${var.app_name}"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
  ok_actions          = [aws_sns_topic.security_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    ResourceArn = each.value.resource_arn
  }

  tags = { Name = "${var.app_name}-ddos-detected-${each.key}" }
}
```

- **Issues**: Shield Advanced CloudWatch metrics are only available in the `us-east-1` region, regardless of where protected resources are located. For global resources like CloudFront, the metric must be read from `us-east-1`. Use `provider = aws.us_east_1` alias when creating CloudWatch alarms for Shield metrics outside of us-east-1.
- **Source**: [Shield Metrics and Alarms](https://docs.aws.amazon.com/waf/latest/developerguide/shield-metrics.html)

---

### Integration: Terraform ↔ IAM

**Pattern**: IAM role for SRT access following least-privilege principle.

```hcl
# IAM role with exactly the permissions required for SRT DDoS response
resource "aws_iam_role" "shield_srt" {
  name                 = "shield-srt-role-${var.environment}"
  max_session_duration = 3600  # 1 hour — limit SRT session duration
  description          = "Grants Shield Response Team access to WAF and Route53 for DDoS mitigation"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ShieldSRTAssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "drt.shield.amazonaws.com"
        }
        Action    = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = var.account_id  # Prevent confused deputy attacks
          }
        }
      }
    ]
  })

  tags = {
    Name    = "shield-srt-role"
    Purpose = "SRT DDoS response access"
  }
}

# Only use the AWS-managed policy — do NOT create a custom policy for SRT
resource "aws_iam_role_policy_attachment" "shield_srt_policy" {
  role       = aws_iam_role.shield_srt.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSShieldDRTAccessPolicy"
}

resource "aws_shield_drt_access_role_arn_association" "main" {
  role_arn   = aws_iam_role.shield_srt.arn
  depends_on = [aws_iam_role_policy_attachment.shield_srt_policy]
}
```

- **Issues**: The role must have the `AWSShieldDRTAccessPolicy` managed policy — custom policies will be rejected. The SRT service principal is `drt.shield.amazonaws.com`. Only one role can be associated per account at a time — updating the association replaces the previous role.
- **Source**: [SRT IAM Role Requirements](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-srt-access.html)

---

## Quality Control

### Verification Commands

```bash
# Format validation
terraform fmt -recursive -check=true
# Expected: Exit code 0, no formatting errors

# Syntax validation
terraform validate
# Expected: "Success! Valid configuration detected"

# Security scanning
tfsec . --format json | jq '.results[] | select(.severity == "CRITICAL" or .severity == "HIGH")'
# Expected: No CRITICAL or HIGH findings on Shield configuration

# Linting and compliance
checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks; no CRITICAL policy violations

# Plan before apply — review subscription impact
terraform plan -out=tfplan -lock=true
terraform show tfplan | grep -E "shield|subscription|protection"
# Expected: Clear resource additions with no unexpected subscription state changes

# Validate Shield protections after apply
aws shield list-protections --query 'Protections[*].{Name:Name,ARN:ResourceArn}' --output table
# Expected: All internet-facing resources appear in the list

# Validate automatic response configuration
aws shield describe-protection \
  --resource-arn $(terraform output -raw cloudfront_arn) \
  --query 'Protection.ApplicationLayerAutomaticResponseConfiguration'
# Expected: {"Action": {"Count": {}}, "Status": "ENABLED"} or Block variant

# Verify health check associations
aws shield list-protections --query 'Protections[*].HealthCheckIds' --output json
# Expected: All protections (except Route53 zones) have non-empty HealthCheckIds arrays

# Verify proactive engagement
aws shield describe-subscription \
  --query 'Subscription.ProactiveEngagementStatus'
# Expected: "ENABLED"

# State validation
terraform state list | grep shield
# Expected: All shield resources present in state

terraform state show aws_shield_subscription.main
# Expected: auto_renew = "ENABLED", id = account_id
```

### Testing with Terratest

```go
package test

import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/gruntwork-io/terratest/modules/aws"
  "github.com/stretchr/testify/assert"
)

func TestShieldAdvancedProtections(t *testing.T) {
  t.Parallel()

  opts := &terraform.Options{
    TerraformDir: "../examples/shield",
    Vars: map[string]interface{}{
      "environment":               "test",
      "shield_auto_response_action": "COUNT",  // Never BLOCK in test environments
      "subscription_enabled":     false,        // Don't create real subscription in tests
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  // Validate protection IDs are non-empty
  protectionIDs := terraform.OutputMap(t, opts, "protection_ids")
  assert.NotEmpty(t, protectionIDs, "Protection IDs should not be empty")

  // Validate protection group ARNs
  groupARNs := terraform.OutputMap(t, opts, "protection_group_arns")
  for _, arn := range groupARNs {
    assert.Contains(t, arn, "arn:aws:shield")
  }
}
```

---

## Production Readiness

### Performance & Scale

- **Shield Advanced detection latency**: L3/L4 attacks at edge — continuous inline, zero detection latency. L7 attacks — minutes to detect and deploy automatic mitigations for new attack patterns.
- **Protection limits**: Maximum 1,000 resource protections per account. Maximum 10 members per ARBITRARY protection group. Maximum 6 emergency contacts in proactive engagement.
- **CloudWatch metric delay**: Shield DDoS metrics have 60-second granularity. `DDoSDetected` metric updates within ~2 minutes of attack onset.
- **WAF WCU impact**: Shield automatic response adds 150 WCUs to the web ACL. Default web ACL capacity is 5,000 WCUs. Monitor WCU usage to avoid hitting the limit.

### Monitoring & Alerting

```hcl
# Complete monitoring setup for Shield Advanced
resource "aws_cloudwatch_dashboard" "shield" {
  dashboard_name = "${var.app_name}-shield-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title  = "DDoS Detection Status"
          metrics = [
            ["AWS/DDoSProtection", "DDoSDetected", "ResourceArn", aws_cloudfront_distribution.main.arn]
          ]
          period = 60
          stat   = "Sum"
        }
      },
      {
        type = "metric"
        properties = {
          title  = "Attack Volume (Requests/sec)"
          metrics = [
            ["AWS/DDoSProtection", "DDoSAttackRequestsPerSecond", "ResourceArn", aws_cloudfront_distribution.main.arn]
          ]
          period = 60
          stat   = "Maximum"
        }
      }
    ]
  })
}
```

### Security Checklist

- [ ] `aws_shield_subscription` has `prevent_destroy = true` and `skip_destroy = true`
- [ ] Every internet-facing resource has an `aws_shield_protection`
- [ ] Every protection (except Route53 zones) has an `aws_shield_protection_health_check_association`
- [ ] Every CloudFront and ALB protection has `aws_shield_application_layer_automatic_response`
- [ ] SRT IAM role exists with `AWSShieldDRTAccessPolicy` and is registered via `aws_shield_drt_access_role_arn_association`
- [ ] `aws_shield_proactive_engagement` enabled with valid phone numbers in emergency contacts
- [ ] CloudWatch alarms exist for `DDoSDetected` on all protected resources
- [ ] WAF web ACL associated with all CloudFront distributions and public ALBs
- [ ] Rate-based rules in WAF web ACL (at minimum 2,000 requests/5min per IP)
- [ ] Protection groups created for aggregate detection
- [ ] State file encryption enabled (S3 backend with `encrypt = true`)
- [ ] All Shield protection objects tagged with environment, owner, and application
- [ ] Emergency contact phone numbers stored in SSM Parameter Store (not hardcoded)
- [ ] Business or Enterprise Support plan active (required for SRT access)

### Disaster Recovery Runbook

```bash
# 1. Shield state recovery — if protection IDs are lost from state
# Look up protection IDs by resource ARN
aws shield list-protections --query 'Protections[?ResourceArn==`RESOURCE_ARN`].Id' --output text

# Import protection back into state
terraform import aws_shield_protection.cloudfront PROTECTION_ID

# Import protection group back into state
terraform import aws_shield_protection_group.all_resources PROTECTION_GROUP_ID

# Import subscription back into state (use account ID)
terraform import aws_shield_subscription.main ACCOUNT_ID

# 2. Proactive engagement restoration after import
terraform import aws_shield_proactive_engagement.main ACCOUNT_ID

# 3. Verify full protection chain after recovery
terraform plan
# Expected: No changes — all resources reconciled with existing infrastructure

# 4. Active attack response — switch from COUNT to BLOCK immediately
# Update variable and apply targeted change only
terraform apply -target=aws_shield_application_layer_automatic_response.cloudfront \
  -var="shield_auto_response_action=BLOCK"

# 5. Revert to COUNT after attack subsides
terraform apply -target=aws_shield_application_layer_automatic_response.cloudfront \
  -var="shield_auto_response_action=COUNT"

# 6. Post-attack state verification
terraform show | grep -E "action|auto_renew|enabled"
# Expected: action = "COUNT" (or BLOCK if staying), auto_renew = "ENABLED", enabled = true
```

---

## Reference Root Module — Copy-Paste Example

### Directory Structure

```
shield-advanced/
├── main.tf
├── variables.tf
├── outputs.tf
├── cloudwatch.tf
├── iam.tf
├── terraform.tfvars.example
└── versions.tf
```

### `versions.tf`

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
    key            = "prod/shield/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### `main.tf`

```hcl
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_partition" "current" {}

provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "terraform-shield-${var.environment}"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
      Application = var.app_name
    }
  }
}

# -----------------------------------------------------------------------
# Shield Advanced Subscription (1-year commitment — protected from destroy)
# -----------------------------------------------------------------------
resource "aws_shield_subscription" "main" {
  auto_renew   = "ENABLED"
  skip_destroy = true

  lifecycle {
    prevent_destroy = true
  }
}

# -----------------------------------------------------------------------
# Resource Protections
# -----------------------------------------------------------------------
resource "aws_shield_protection" "cloudfront" {
  name         = "${var.app_name}-cloudfront-${var.environment}"
  resource_arn = var.cloudfront_distribution_arn
  tags         = { ResourceType = "cloudfront" }
  depends_on   = [aws_shield_subscription.main]
}

resource "aws_shield_protection" "alb" {
  name         = "${var.app_name}-alb-${var.environment}"
  resource_arn = var.alb_arn
  tags         = { ResourceType = "alb" }
  depends_on   = [aws_shield_subscription.main]
}

resource "aws_shield_protection" "route53_zone" {
  name         = "${var.app_name}-route53-${var.environment}"
  resource_arn = "arn:${data.aws_partition.current.partition}:route53:::hostedzone/${var.route53_zone_id}"
  tags         = { ResourceType = "route53" }
  depends_on   = [aws_shield_subscription.main]
}

# -----------------------------------------------------------------------
# Health Check Associations (not supported for Route53 zone protections)
# -----------------------------------------------------------------------
resource "aws_route53_health_check" "app" {
  fqdn              = var.app_domain
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
  tags              = { Name = "${var.app_name}-health-check" }
}

resource "aws_shield_protection_health_check_association" "cloudfront" {
  health_check_arn     = aws_route53_health_check.app.arn
  shield_protection_id = aws_shield_protection.cloudfront.id
}

resource "aws_shield_protection_health_check_association" "alb" {
  health_check_arn     = aws_route53_health_check.app.arn
  shield_protection_id = aws_shield_protection.alb.id
}

# -----------------------------------------------------------------------
# Automatic Application Layer DDoS Mitigation
# -----------------------------------------------------------------------
resource "aws_shield_application_layer_automatic_response" "cloudfront" {
  resource_arn = var.cloudfront_distribution_arn
  action       = var.shield_auto_response_action
  depends_on   = [aws_shield_protection.cloudfront]
}

resource "aws_shield_application_layer_automatic_response" "alb" {
  resource_arn = var.alb_arn
  action       = var.shield_auto_response_action
  depends_on   = [aws_shield_protection.alb]
}

# -----------------------------------------------------------------------
# Protection Groups
# -----------------------------------------------------------------------
resource "aws_shield_protection_group" "all" {
  protection_group_id = "${var.app_name}-all-${var.environment}"
  aggregation         = "MAX"
  pattern             = "ALL"
  depends_on = [
    aws_shield_protection.cloudfront,
    aws_shield_protection.alb,
    aws_shield_protection.route53_zone,
  ]
}

resource "aws_shield_protection_group" "cloudfront_type" {
  protection_group_id = "${var.app_name}-cloudfront-type-${var.environment}"
  aggregation         = "SUM"
  pattern             = "BY_RESOURCE_TYPE"
  resource_type       = "CLOUDFRONT_DISTRIBUTION"
  depends_on          = [aws_shield_subscription.main]
}
```

### `iam.tf`

```hcl
resource "aws_iam_role" "shield_srt" {
  name        = "shield-srt-role-${var.environment}"
  description = "Shield Response Team role for ${var.app_name} DDoS event response"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "ShieldSRTAssumeRole"
      Effect    = "Allow"
      Principal = { Service = "drt.shield.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Purpose = "shield-srt-access" }
}

resource "aws_iam_role_policy_attachment" "shield_srt" {
  role       = aws_iam_role.shield_srt.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSShieldDRTAccessPolicy"
}

resource "aws_shield_drt_access_role_arn_association" "main" {
  role_arn   = aws_iam_role.shield_srt.arn
  depends_on = [aws_iam_role_policy_attachment.shield_srt]
}

resource "aws_shield_proactive_engagement" "main" {
  enabled = true

  emergency_contact {
    email_address = var.soc_primary_email
    phone_number  = var.soc_primary_phone
    contact_notes = "Primary SOC — ${var.app_name} DDoS events"
  }

  depends_on = [aws_shield_drt_access_role_arn_association.main]
}
```

### `terraform.tfvars.example`

```hcl
app_name    = "my-application"
environment = "prod"
aws_region  = "us-east-1"
account_id  = "123456789012"
owner       = "platform-team"
cost_center = "engineering"

cloudfront_distribution_arn = "arn:aws:cloudfront::123456789012:distribution/EXAMPLEDIST"
alb_arn                     = "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/1234567890"
route53_zone_id             = "Z1234567890ABC"
app_domain                  = "api.my-application.com"

shield_auto_response_action = "COUNT"  # Switch to BLOCK after 2+ weeks of baseline validation

# Store these in SSM Parameter Store or pass via CI/CD secrets — do NOT commit real values
soc_primary_email = "soc-oncall@example.com"
soc_primary_phone = "+12125551234"  # Retrieve from SSM in production
```

---

## Reference Implementations

- [Official Terraform AWS Provider - Shield](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_protection)
- [AWS Shield Advanced Developer Guide](https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html)
- [AWS Well-Architected Framework — Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- [Terraform AWS Provider GitHub](https://github.com/hashicorp/terraform-provider-aws)

---

## Source Bibliography

### Primary Sources
- [Terraform AWS Provider Registry v6.x](https://registry.terraform.io/providers/hashicorp/aws/latest) — 6.47.0 verified 2026-05-28
- [aws_shield_subscription](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_subscription)
- [aws_shield_protection](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_protection)
- [aws_shield_protection_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_protection_group)
- [aws_shield_protection_health_check_association](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_protection_health_check_association)
- [aws_shield_application_layer_automatic_response](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_application_layer_automatic_response)
- [aws_shield_proactive_engagement](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_proactive_engagement)
- [aws_shield_drt_access_role_arn_association](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_drt_access_role_arn_association)
- [AWS Shield Advanced Documentation](https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html)
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)

### Validation & Tools
- [tfsec GitHub](https://github.com/aquasecurity/tfsec) — Security scanner
- [Checkov](https://www.checkov.io/) — Policy-as-code validator
- [Terratest](https://terratest.gruntwork.io/) — Testing framework
- [AWS Shield Pricing](https://aws.amazon.com/shield/pricing/)
- [GitHub Issues — hashicorp/terraform-provider-aws — shield label](https://github.com/hashicorp/terraform-provider-aws/issues?q=label%3Aservice%2Fshield)

---

## Completion Checklist

- [x] All Terraform 1.7 and aws ~> 6.0 patterns validated against registry 6.47.0
- [x] Code examples for all 8 Shield Terraform resources
- [x] State management strategy documented with `prevent_destroy` / `skip_destroy` guidance
- [x] Module architecture fully defined with standard structure
- [x] Every anti-pattern has tested safe alternative
- [x] CLI commands with expected verification outputs
- [x] Integration examples for WAF, CloudFront, Route53, CloudWatch, IAM
- [x] Sources dated and directly linked to registry docs
- [x] Security checklist complete
- [x] Copy-paste working root module with `.tfvars.example`
- [x] Disaster recovery and state import procedures documented

---

## Research Gaps

```
Gap: aws_shield_drt_access_log_bucket_association S3 bucket policy requirements
Impact: Incomplete SRT log access configuration may prevent S3 bucket association from applying
Workaround: Manually verify S3 bucket policy includes drt.shield.amazonaws.com principal before associating
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_drt_access_log_bucket_association

Gap: Shield Advanced subscription import behavior when subscription already exists in another Terraform workspace
Impact: Potential state conflict if multiple Terraform workspaces attempt to manage the same subscription
Workaround: Use a single dedicated Terraform workspace for the shield_subscription resource; reference it from other workspaces via remote state data source
Follow-up: https://developer.hashicorp.com/terraform/language/state/remote-state-data

Gap: Shield Advanced availability for GovCloud and China regions
Impact: aws_shield_subscription may not be available in all AWS partitions
Workaround: Verify subscription availability for target partition before deploying; use data.aws_partition.current.partition in all ARN constructions
Follow-up: https://docs.aws.amazon.com/general/latest/gr/shield.html
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Terraform syntax validation and formatting for Shield resources
- Mandatory security patterns: `prevent_destroy`, `skip_destroy`, health check associations
- CloudWatch alarm creation for DDoS metrics
- IAM role creation for SRT access (using required `AWSShieldDRTAccessPolicy`)
- Protection group creation for existing protected resources
- State management setup and import commands

### Medium Confidence (Validate with user)
- Switching `aws_shield_application_layer_automatic_response` action from COUNT to BLOCK
- Emergency contact information updates (phone numbers, email addresses)
- Protection group aggregation method selection (SUM vs MEAN vs MAX)
- Deciding which resources to include in ARBITRARY protection groups
- WAF rate limit thresholds (require application traffic baseline knowledge)

### Low Confidence (Must ask user)
- Whether to purchase Shield Advanced subscription ($3,000/month commitment)
- Contact information for `aws_shield_proactive_engagement` emergency contacts
- Which accounts in the AWS Organizations family to centralize under one Shield subscription
- Compliance-specific SRT access requirements (SOC2, PCI-DSS, HIPAA)
- Decision to cancel subscription (requires support case outside 30-day window)

### Edge Cases (When to pause)
- Any change to `aws_shield_subscription` resource — review billing impact before applying
- Switching automatic response from COUNT to BLOCK in production — pause and confirm false-positive validation
- Removing any `aws_shield_protection` — verify resource is genuinely no longer internet-facing before proceeding
- Updating emergency contacts — verify contacts are aware and reachable at new numbers
- `terraform destroy` on the root module containing Shield subscription — HALT and confirm explicit user intent

### Emergency Stop
- Halt if `prevent_destroy` is missing from `aws_shield_subscription` in production
- Halt if `terraform destroy` is planned on the Shield subscription without explicit user confirmation
- Halt if hardcoded phone numbers or email addresses are found in Shield proactive engagement configuration
- Halt if `aws_shield_protection` exists for a resource that is clearly internal-only (no public DNS, private subnet)
