# Terraform AWS SES — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - SES (Simple Email Service)"
Cloud_Provider: "AWS"
Target_Service: "SES (Domain Identities, Email Identities, DKIM, MAIL FROM, Configuration Sets, Event Destinations, Receipt Rules, Templates, Identity Policies)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-28"
Domain_Complexity: "Standard"
V6x_Notable_Changes: |
  - aws_ses_domain_identity and aws_ses_email_identity: region argument added (optional, overrides provider region)
  - Import blocks supported for all SES resources (Terraform v1.5.0+)
  - aws_ses_event_destination: cloudwatch_destination and kinesis_destination are mutually exclusive
  - aws_ses_domain_mail_from: behavior_on_mx_failure default changed to UseDefaultValue
  - aws_ses_receipt_rule: S3, Lambda, SNS, SQS, Bounce, Add Header, Stop, WorkMail actions supported
  - SES v1 (classic) and SESv2 are separate provider namespaces; this document covers SES v1 (aws_ses_*)
```

---

## Executive Summary

Amazon SES (Simple Email Service) is AWS's cloud-based email sending and receiving service used for transactional, marketing, and bulk email. It supports both sending (SMTP, API) and receiving (receipt rules) email, with identity verification via domain or individual email address. SES imposes a strict reputation model: new accounts start in sandbox mode (send only to verified addresses, 200 emails/day), and production access requires an explicit AWS Support request. The Terraform aws provider v6.x covers the classic SES API (`aws_ses_*`) with 14 resources and 3 data sources; the newer SESv2 API is a separate resource namespace (`aws_sesv2_*`) not covered here.

The SES Terraform resource surface is composed of four distinct layers: **(1) Identity management** — `aws_ses_domain_identity`, `aws_ses_email_identity`, `aws_ses_domain_dkim`, `aws_ses_domain_identity_verification`, `aws_ses_domain_mail_from`; **(2) Sending configuration** — `aws_ses_configuration_set`, `aws_ses_event_destination`, `aws_ses_identity_notification_topic`, `aws_ses_identity_policy`, `aws_ses_template`; **(3) Email receiving** — `aws_ses_receipt_rule_set`, `aws_ses_receipt_rule`, `aws_ses_active_receipt_rule_set`, `aws_ses_receipt_filter`; **(4) Data sources** — `data.aws_ses_domain_identity`, `data.aws_ses_email_identity`, `data.aws_ses_active_receipt_rule_set`. Domain verification flows through Route53 (TXT record for identity, CNAME records for DKIM, MX+TXT for MAIL FROM); automation requires Route53 zone management in the same Terraform workspace or cross-stack data sources.

Three non-negotiable guardrails for any SES deployment: **(1) DKIM signing (`aws_ses_domain_dkim`) must always accompany domain identity** — without DKIM, emails will fail DMARC checks and land in spam; missing the 3 CNAME Route53 records causes silent failures at send time with no Terraform plan-time error; **(2) a custom MAIL FROM domain (`aws_ses_domain_mail_from`) is required for DMARC alignment** — using the default amazonses.com MAIL FROM domain passes SPF only in relaxed mode, which many DMARC policies will reject at `p=reject`; **(3) bounce and complaint notifications (`aws_ses_identity_notification_topic`) must be configured on all identities** — SES automatically suppresses addresses with hard bounces, but without SNS notifications your application cannot programmatically remove bad addresses; exceeding a 5% complaint rate or 10% bounce rate causes AWS to pause your SES account. This service is classified **Standard** due to multi-resource composition (identity + DKIM + MAIL FROM + Route53 DNS), DNS propagation dependencies, IAM cross-service permissions, and reputation management complexity.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Pins provider version to prevent accidental upgrades that could introduce breaking changes. Defines the deployment contract for all team members and CI pipelines.

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
    key            = "prod/ses/terraform.tfstate"
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

**Why**: Credentials must never be hardcoded. `assume_role` enables cross-account SES sending from application accounts. `default_tags` enforces compliance tagging. SES resources themselves are not taggable with `default_tags` (SES does not support resource tagging in the classic API), but the provider block ensures IAM, S3, SNS, and Route53 resources created alongside SES are tagged.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformSESRole"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
      Service     = "ses"
    }
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [AWS Provider Authentication](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration) | [assume_role block](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#assume-role)

---

#### Pattern: Domain Identity with DKIM and Route53 Verification

**Why**: A domain identity alone is unverified and cannot send email. DKIM requires 3 CNAME records in Route53. Without these records, all outbound email will fail DMARC checks. The `aws_ses_domain_identity_verification` resource (optional) can be used to wait for verification, but it has a default 45-minute timeout — use `timeouts` block for long-TTL DNS zones.

```hcl
# 1. Register the domain identity
resource "aws_ses_domain_identity" "main" {
  domain = var.email_domain
}

# 2. Verify domain via Route53 TXT record
resource "aws_route53_record" "ses_verification" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "_amazonses.${aws_ses_domain_identity.main.domain}"
  type    = "TXT"
  ttl     = 600
  records = [aws_ses_domain_identity.main.verification_token]
}

# 3. Enable DKIM signing
resource "aws_ses_domain_dkim" "main" {
  domain = aws_ses_domain_identity.main.domain
}

# 4. Create 3 CNAME records for DKIM tokens
resource "aws_route53_record" "dkim" {
  count   = 3
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "${aws_ses_domain_dkim.main.dkim_tokens[count.index]}._domainkey"
  type    = "CNAME"
  ttl     = 600
  records = ["${aws_ses_domain_dkim.main.dkim_tokens[count.index]}.dkim.amazonses.com"]
}

# 5. (Optional) Wait for domain verification — use in CI with caution; DNS TTL dependent
resource "aws_ses_domain_identity_verification" "main" {
  domain = aws_ses_domain_identity.main.id

  depends_on = [aws_route53_record.ses_verification]

  timeouts {
    create = "60m"  # Increase for high-TTL DNS zones
  }
}

data "aws_route53_zone" "main" {
  name         = var.email_domain
  private_zone = false
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_ses_domain_identity](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_identity) | [aws_ses_domain_dkim](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_dkim)

---

#### Pattern: Custom MAIL FROM Domain for DMARC Alignment

**Why**: The default MAIL FROM address uses `email.amazonses.com`. For DMARC alignment (`p=reject` or `p=quarantine`), the MAIL FROM domain must align with the From header domain. A custom MAIL FROM subdomain (e.g., `bounce.example.com`) enables SPF alignment. Requires an MX record pointing to the SES feedback SMTP endpoint and a TXT record for SPF.

```hcl
resource "aws_ses_domain_mail_from" "main" {
  domain           = aws_ses_domain_identity.main.domain
  mail_from_domain = "bounce.${aws_ses_domain_identity.main.domain}"

  # Options: UseDefaultValue (default), RejectMessage
  behavior_on_mx_failure = "UseDefaultValue"
}

# MX record for MAIL FROM subdomain — points to SES feedback endpoint
resource "aws_route53_record" "mail_from_mx" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = aws_ses_domain_mail_from.main.mail_from_domain
  type    = "MX"
  ttl     = 600
  records = ["10 feedback-smtp.${var.aws_region}.amazonses.com"]
}

# TXT/SPF record for MAIL FROM subdomain
resource "aws_route53_record" "mail_from_spf" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = aws_ses_domain_mail_from.main.mail_from_domain
  type    = "TXT"
  ttl     = 600
  records = ["v=spf1 include:amazonses.com ~all"]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_ses_domain_mail_from](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_mail_from) | [Amazon SES MAIL FROM docs](https://docs.aws.amazon.com/ses/latest/dg/mail-from.html)

---

#### Pattern: Bounce and Complaint Notification via SNS

**Why**: Exceeding a 5% complaint rate or 10% bounce rate causes AWS to pause your SES sending account. Without SNS notifications, your application cannot automatically process bounces/complaints to remove bad addresses. Both `Bounce` and `Complaint` notification types must be configured. `Delivery` notification is optional but useful for delivery confirmation.

```hcl
# SNS topic for bounce/complaint notifications
resource "aws_sns_topic" "ses_notifications" {
  name              = "${var.environment}-ses-notifications"
  kms_master_key_id = aws_kms_key.sns.arn  # Encrypt at rest

  tags = {
    Name        = "${var.environment}-ses-notifications"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Bounce notifications
resource "aws_ses_identity_notification_topic" "bounce" {
  identity                 = aws_ses_domain_identity.main.domain
  notification_type        = "Bounce"
  topic_arn                = aws_sns_topic.ses_notifications.arn
  include_original_headers = true
}

# Complaint notifications
resource "aws_ses_identity_notification_topic" "complaint" {
  identity                 = aws_ses_domain_identity.main.domain
  notification_type        = "Complaint"
  topic_arn                = aws_sns_topic.ses_notifications.arn
  include_original_headers = true
}

# Delivery notifications (optional — can increase SNS costs at scale)
resource "aws_ses_identity_notification_topic" "delivery" {
  identity                 = aws_ses_domain_identity.main.domain
  notification_type        = "Delivery"
  topic_arn                = aws_sns_topic.ses_notifications.arn
  include_original_headers = false
}

# SES must have permission to publish to the SNS topic
data "aws_iam_policy_document" "ses_sns_policy" {
  statement {
    sid    = "AllowSESSNSPublish"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ses.amazonaws.com"]
    }

    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.ses_notifications.arn]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "ses_notifications" {
  arn    = aws_sns_topic.ses_notifications.arn
  policy = data.aws_iam_policy_document.ses_sns_policy.json
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_ses_identity_notification_topic](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_identity_notification_topic) | [SES Notifications docs](https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications.html)

---

#### Pattern: Configuration Set with Event Destination

**Why**: Configuration sets enable per-sending-operation event tracking (opens, clicks, bounces, deliveries) and enforce TLS. Without a configuration set, you cannot track sending metrics per campaign, tenant, or application. Event destinations require the configuration set to exist before creation.

```hcl
resource "aws_ses_configuration_set" "main" {
  name = "${var.environment}-ses-config"

  # Require TLS for all sending using this configuration set
  delivery_options {
    tls_policy = "Require"
  }

  # Track reputation metrics (bounce/complaint rates)
  reputation_metrics_enabled = true

  # Allow sending to be paused via SendingEnabled API
  sending_enabled = true
}

# SNS event destination for real-time event processing
resource "aws_ses_event_destination" "sns" {
  name                   = "${var.environment}-ses-events-sns"
  configuration_set_name = aws_ses_configuration_set.main.name
  enabled                = true

  matching_types = [
    "send",
    "reject",
    "bounce",
    "complaint",
    "delivery",
    "open",
    "click",
    "renderingFailure"
  ]

  sns_destination {
    topic_arn = aws_sns_topic.ses_notifications.arn
  }
}

# CloudWatch destination for metrics and dashboards
resource "aws_ses_event_destination" "cloudwatch" {
  name                   = "${var.environment}-ses-events-cloudwatch"
  configuration_set_name = aws_ses_configuration_set.main.name
  enabled                = true

  matching_types = ["bounce", "complaint", "send"]

  cloudwatch_destination {
    default_value  = "none"
    dimension_name = "ses:source-ip"
    value_source   = "messageTag"
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_ses_configuration_set](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_configuration_set) | [aws_ses_event_destination](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_event_destination)

---

#### Pattern: IAM Least-Privilege Sending Policy

**Why**: Application IAM roles must be scoped to only `ses:SendEmail` and `ses:SendRawEmail` on the specific identity ARN. Granting `ses:*` allows listing, deleting identities, and modifying sending limits — a significant blast radius for a compromised credential.

```hcl
data "aws_iam_policy_document" "ses_sender" {
  statement {
    sid    = "AllowSESSend"
    effect = "Allow"

    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail",
      "ses:SendTemplatedEmail",
    ]

    resources = [
      aws_ses_domain_identity.main.arn,
    ]

    condition {
      test     = "StringEquals"
      variable = "ses:FromAddress"
      values   = ["noreply@${var.email_domain}"]
    }
  }
}

resource "aws_iam_policy" "ses_sender" {
  name        = "${var.environment}-ses-sender-policy"
  description = "Allow application to send email via SES identity"
  policy      = data.aws_iam_policy_document.ses_sender.json

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_iam_role_policy_attachment" "app_ses" {
  role       = var.app_iam_role_name
  policy_arn = aws_iam_policy.ses_sender.arn
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [SES IAM Actions](https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html) | [aws_iam_policy_document](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document)

---

#### Pattern: Variable Validation and Type Safety

**Why**: Prevents invalid SES configurations (wrong regions, malformed domain names, invalid notification types) at `terraform plan` time, before any AWS API call is made.

```hcl
variable "email_domain" {
  type        = string
  description = "The domain to register as an SES identity (e.g., example.com)"

  validation {
    condition     = can(regex("^[a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?(\\.[a-zA-Z]{2,})+$", var.email_domain))
    error_message = "email_domain must be a valid domain name (e.g., example.com)."
  }
}

variable "aws_region" {
  type        = string
  description = "AWS region for SES deployment"
  default     = "us-east-1"

  validation {
    condition = contains([
      "us-east-1", "us-west-2", "eu-west-1", "eu-central-1",
      "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
      "ca-central-1", "sa-east-1"
    ], var.aws_region)
    error_message = "SES is only available in specific AWS regions. Check https://docs.aws.amazon.com/general/latest/gr/ses.html for the current list."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment (sandbox, staging, production)"

  validation {
    condition     = contains(["sandbox", "staging", "production"], var.environment)
    error_message = "environment must be one of: sandbox, staging, production."
  }
}

variable "ses_tls_policy" {
  type        = string
  description = "TLS enforcement policy for the configuration set"
  default     = "Require"

  validation {
    condition     = contains(["Require", "Optional"], var.ses_tls_policy)
    error_message = "ses_tls_policy must be 'Require' or 'Optional'. Use 'Require' for production."
  }
}
```

- **Terraform Version**: >= 1.7 (validation blocks)
- **Provider Version**: aws ~> 6.0
- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

### ⚠️ Conditional Patterns

---

#### Decision: Domain Identity vs. Email Identity

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **`aws_ses_domain_identity`** | Bulk sending, DKIM/DMARC support, all subdomain addresses, no per-address verification | Complexity (requires DNS records, Route53 setup) | Production apps, transactional email at scale, DMARC compliance required |
| **`aws_ses_email_identity`** | Simplicity, no DNS ownership required | Single address only, no DKIM/DMARC, sandbox testing only | Development/testing, single-address applications, accounts without DNS access |

- Agent: "Ask user: Do you own the DNS zone for this domain and need production sending capabilities? → Use domain identity. Testing only? → Email identity is sufficient."
- Source: [aws_ses_domain_identity](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_identity) | [aws_ses_email_identity](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_email_identity)

---

#### Decision: SES v1 (aws_ses_*) vs. SESv2 (aws_sesv2_*)

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **SES v1** | Terraform maturity, community examples, receipt rules for inbound email | Missing features: dedicated IPs, virtual deliverability manager, contact lists in v1 | Inbound email processing required, stable existing deployments |
| **SESv2** | Newer API, dedicated IPs, virtual deliverability manager, contact lists, suppression list management | Separate Terraform resource namespace (`aws_sesv2_*`), fewer community examples | New greenfield projects, advanced deliverability management needed |

- Agent: "Ask user: Do you need inbound email receipt rules? → SES v1. Need contact list management, VDM, or dedicated IPs via Terraform? → SESv2 (`aws_sesv2_*` resources)."
- Source: [SESv2 vs SES comparison](https://docs.aws.amazon.com/ses/latest/dg/what-is.html)

---

#### Decision: SNS vs. CloudWatch vs. Kinesis Firehose Event Destination

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **SNS** | Real-time processing, fan-out to Lambda/SQS, bounce list automation | Ordering not guaranteed, Lambda cold starts | Real-time bounce/complaint processing, webhook delivery |
| **CloudWatch** | Dashboards, alarms, metrics, long-term retention | No per-message payload, aggregated only | Reputation monitoring, alerting on bounce/complaint rates |
| **Kinesis Firehose** | High-throughput streaming to S3/Redshift/OpenSearch, batch analytics | Cost (Firehose + S3), IAM role complexity | Analytics, compliance archiving, high-volume sending |

- Note: `cloudwatch_destination` and `kinesis_destination` are mutually exclusive on the same event destination resource; create separate `aws_ses_event_destination` resources for each.
- Agent: "Ask user: Real-time automation (bounce removal, CRM sync)? → SNS. Dashboard/alerting only? → CloudWatch. Data warehouse/analytics? → Kinesis Firehose."
- Source: [aws_ses_event_destination](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_event_destination)

---

#### Decision: Receipt Rules (Inbound Email) vs. Sending Only

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Receipt Rules only (sending)** | Simplicity — no receipt infrastructure | Cannot receive email | Transactional/marketing sending only |
| **Receipt Rules enabled** | Full email infrastructure, inbound processing, auto-reply | Additional resources: S3 bucket, Lambda, SNS; IP filter management; only available in select regions | Support inbox, autoresponder, email parsing pipelines |

- Note: SES inbound email (receipt rules) is only available in `us-east-1`, `us-west-2`, and `eu-west-1`. Not available in all SES regions.
- Agent: "Ask user: Does your application need to receive and process inbound email? Receipt rules are only available in 3 regions. If yes, confirm deployment region is us-east-1, us-west-2, or eu-west-1."
- Source: [SES email receiving](https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html) | [aws_ses_receipt_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_receipt_rule)

---

#### Decision: Identity Policy vs. IAM Policy for Cross-Account Sending

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **IAM policy** (default) | Standard AWS IAM patterns, enforced via IAM | Single-account only | Same-account application sending |
| **Identity policy (`aws_ses_identity_policy`)** | Cross-account access, delegate sending to other accounts | Additional resource, policy size limits | Multi-account architecture, SaaS model where customers send from your verified domain |

- Agent: "Ask user: Do external AWS accounts need to send email using this SES identity? → Use aws_ses_identity_policy. Same account only? → IAM policy is sufficient."
- Source: [aws_ses_identity_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_identity_policy) | [SES cross-account access](https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Hardcoded AWS Credentials

```hcl
# DON'T
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  region     = "us-east-1"
}
```

**Why**: Credentials in code are exposed via VCS history, CI logs, and team access. Cannot be rotated without code changes.

**Instead**:
```hcl
# DO — Use IAM roles (EC2/ECS/Lambda instance profiles) or environment variables
provider "aws" {
  region = var.aws_region
  # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN from environment
  # OR instance profile / task role / Lambda execution role automatically
}
```

- **Impact**: CRITICAL — Full AWS account compromise
- **Severity**: CRITICAL
- **Source**: [AWS Security Best Practices](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)

---

#### Anti-Pattern: Sending Without TLS Enforcement

```hcl
# DON'T — Default TLS policy is Optional, not Require
resource "aws_ses_configuration_set" "main" {
  name = "my-config-set"
  # No delivery_options block = TLS Optional
}
```

**Why**: Optional TLS allows email to be sent in plaintext over SMTP, exposing email content in transit. Non-compliant with SOC2, HIPAA, and GDPR requirements.

**Instead**:
```hcl
# DO — Always require TLS
resource "aws_ses_configuration_set" "main" {
  name = "${var.environment}-ses-config"

  delivery_options {
    tls_policy = "Require"  # Reject connections that don't support STARTTLS
  }

  reputation_metrics_enabled = true
}
```

- **Impact**: HIGH — Email content exposed in transit, compliance violations
- **Severity**: HIGH
- **Source**: [SES Configuration Set TLS](https://docs.aws.amazon.com/ses/latest/dg/creating-configuration-sets.html)

---

#### Anti-Pattern: Missing Bounce and Complaint Notification

```hcl
# DON'T — Registering identity without bounce/complaint notifications
resource "aws_ses_domain_identity" "main" {
  domain = "example.com"
}
# No aws_ses_identity_notification_topic for Bounce or Complaint
```

**Why**: Without bounce/complaint notifications, your application cannot remove bad addresses. Exceeding 10% bounce rate or 5% complaint rate causes AWS to suspend SES sending. Silent failures accumulate until account suspension.

**Instead**:
```hcl
# DO — Always configure Bounce and Complaint notifications
resource "aws_ses_identity_notification_topic" "bounce" {
  identity          = aws_ses_domain_identity.main.domain
  notification_type = "Bounce"
  topic_arn         = aws_sns_topic.ses_notifications.arn
}

resource "aws_ses_identity_notification_topic" "complaint" {
  identity          = aws_ses_domain_identity.main.domain
  notification_type = "Complaint"
  topic_arn         = aws_sns_topic.ses_notifications.arn
}
```

- **Impact**: CRITICAL — Account suspension, email deliverability loss
- **Severity**: CRITICAL
- **Source**: [SES Bounce Handling](https://docs.aws.amazon.com/ses/latest/dg/send-email-concepts-process.html) | [SES Sending Review Process](https://docs.aws.amazon.com/ses/latest/dg/reputationdashboardmessages.html)

---

#### Anti-Pattern: Domain Identity Without DKIM

```hcl
# DON'T — Domain identity without DKIM configuration
resource "aws_ses_domain_identity" "main" {
  domain = "example.com"
}

resource "aws_route53_record" "ses_verification" {
  # ... verification record
}

# No aws_ses_domain_dkim — emails will fail DMARC
```

**Why**: Without DKIM, emails from this domain will fail DMARC alignment checks. Major email providers (Gmail, Outlook) increasingly reject or quarantine emails that fail DMARC. This is a silent failure — SES will send the email, but recipients will not receive it.

**Instead**:
```hcl
# DO — Always pair domain identity with DKIM
resource "aws_ses_domain_dkim" "main" {
  domain = aws_ses_domain_identity.main.domain
}

resource "aws_route53_record" "dkim" {
  count   = 3
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "${aws_ses_domain_dkim.main.dkim_tokens[count.index]}._domainkey"
  type    = "CNAME"
  ttl     = 600
  records = ["${aws_ses_domain_dkim.main.dkim_tokens[count.index]}.dkim.amazonses.com"]
}
```

- **Impact**: HIGH — Email deliverability failure, DMARC rejections
- **Severity**: HIGH
- **Source**: [SES Easy DKIM](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html) | [aws_ses_domain_dkim](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_dkim)

---

#### Anti-Pattern: Overly Permissive SES IAM Policy

```hcl
# DON'T — Wildcard SES permissions
resource "aws_iam_policy" "ses" {
  name   = "ses-full-access"
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = "ses:*"          # DON'T — includes DeleteIdentity, UpdateAccountSendingEnabled
      Resource = "*"              # DON'T — across all identities
    }]
  })
}
```

**Why**: `ses:*` includes destructive actions like `ses:DeleteIdentity`, `ses:UpdateAccountSendingEnabled`, `ses:PutAccountSendingAttributes` — a compromised credential can disable your entire SES account.

**Instead**:
```hcl
# DO — Scope to minimum required actions and specific identity ARN
data "aws_iam_policy_document" "ses_sender" {
  statement {
    effect = "Allow"
    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail",
      "ses:SendTemplatedEmail",
    ]
    resources = [aws_ses_domain_identity.main.arn]

    condition {
      test     = "StringEquals"
      variable = "ses:FromAddress"
      values   = ["noreply@${var.email_domain}"]
    }
  }
}
```

- **Impact**: CRITICAL — Account-level email sending disabled, identity deletion
- **Severity**: CRITICAL
- **Source**: [SES IAM Actions](https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html)

---

#### Anti-Pattern: No State File Encryption

```hcl
# DON'T
backend "s3" {
  bucket = "my-tf-state"
  key    = "ses/terraform.tfstate"
  region = "us-east-1"
  # Missing: encrypt = true, dynamodb_table for locking
}
```

**Why**: Terraform state for SES deployments contains domain ARNs, verification tokens, DKIM tokens, and SNS topic ARNs. Unencrypted state in a shared bucket can expose email infrastructure details, enabling phishing or reputation attacks against your domain.

**Instead**:
```hcl
# DO
backend "s3" {
  bucket         = "my-org-terraform-state"
  key            = "prod/ses/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-locks"
  kms_key_id     = "arn:aws:kms:us-east-1:ACCOUNT:key/KEY-ID"  # CMK for state
}
```

- **Impact**: CRITICAL — Infrastructure details exposed, potential domain hijacking
- **Severity**: CRITICAL
- **Source**: [Terraform State Security](https://developer.hashicorp.com/terraform/language/state/sensitive-data)

---

#### Anti-Pattern: Using aws_ses_domain_identity_verification in Production CI/CD Without Timeout Handling

```hcl
# DON'T — Default 45 min timeout with no handling in CI
resource "aws_ses_domain_identity_verification" "main" {
  domain = aws_ses_domain_identity.main.id
  # Default 45-minute timeout — will fail if DNS TTL is high
  depends_on = [aws_route53_record.ses_verification]
}
```

**Why**: DNS propagation can take 5 minutes to several hours depending on TTL settings and DNS provider caching. The default 45-minute timeout causes CI pipelines to fail if DNS propagation is slow. This is especially problematic on first deployment with high-TTL DNS zones.

**Instead**:
```hcl
# DO — Increase timeout or omit verification resource entirely
# Option A: Increase timeout
resource "aws_ses_domain_identity_verification" "main" {
  domain = aws_ses_domain_identity.main.id

  depends_on = [aws_route53_record.ses_verification]

  timeouts {
    create = "2h"  # Allow for slow DNS propagation
  }
}

# Option B: Skip verification resource, check verification in post-deploy test
# Verification happens asynchronously; SES console shows "verified" once complete
```

- **Impact**: MEDIUM — CI pipeline failures on initial deployment
- **Severity**: MEDIUM
- **Source**: [aws_ses_domain_identity_verification](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_identity_verification)

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
  # No backend block = local state in terraform.tfstate
}
```

- **Risk**: No locking (concurrent applies corrupt state), no sharing, no version history
- **When**: Solo development, sandbox testing, throwaway environments

### Production Remote State (S3 + DynamoDB)

```hcl
# DynamoDB table for state locking (create once, shared across all workspaces)
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

# S3 state bucket with versioning, encryption, and access control
resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-org-terraform-state"

  lifecycle {
    prevent_destroy = true  # Never accidentally delete state bucket
  }

  tags = {
    Name      = "terraform-state"
    ManagedBy = "terraform"
  }
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
      kms_master_key_id = aws_kms_key.state.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Backend configuration — use in terraform block
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/ses/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

- **Benefit**: Team access, state locking, version history, encryption
- **Safeguard**: State may contain domain ARNs and DKIM tokens; restrict S3 + DynamoDB access to Terraform service accounts only

### Multi-Environment State Isolation

```
Scenario: Multi-environment (sandbox/staging/production)
Backend: Separate S3 keys per environment
Locking: Shared DynamoDB table with per-key locks
Encryption: S3 SSE with CMK

# Separate state keys prevent cross-environment blast radius
sandbox:    s3://bucket/sandbox/ses/terraform.tfstate
staging:    s3://bucket/staging/ses/terraform.tfstate
production: s3://bucket/prod/ses/terraform.tfstate
```

---

## Module Architecture

### Standard SES Module Structure

```
modules/
└── ses/
    ├── main.tf           # aws_ses_domain_identity, aws_ses_domain_dkim, etc.
    ├── variables.tf      # email_domain, aws_region, environment, config
    ├── outputs.tf        # identity_arn, dkim_tokens, configuration_set_name
    ├── versions.tf       # required_version, required_providers
    └── README.md         # Usage, inputs, outputs, gotchas
```

### Module Definition Example

```hcl
# modules/ses/variables.tf

variable "domain" {
  type        = string
  description = "Domain name to register as SES identity"

  validation {
    condition     = can(regex("^[a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?(\\.[a-zA-Z]{2,})+$", var.domain))
    error_message = "domain must be a valid fully-qualified domain name."
  }
}

variable "route53_zone_id" {
  type        = string
  description = "Route53 hosted zone ID for the domain"

  validation {
    condition     = can(regex("^Z[A-Z0-9]+$", var.route53_zone_id))
    error_message = "route53_zone_id must be a valid Route53 zone ID starting with Z."
  }
}

variable "bounce_sns_topic_arn" {
  type        = string
  description = "ARN of SNS topic for bounce/complaint notifications"

  validation {
    condition     = can(regex("^arn:aws:sns:", var.bounce_sns_topic_arn))
    error_message = "bounce_sns_topic_arn must be a valid SNS topic ARN."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["sandbox", "staging", "production"], var.environment)
    error_message = "environment must be sandbox, staging, or production."
  }
}

variable "enable_receipt_rules" {
  type        = bool
  description = "Enable inbound email receipt rules (only in us-east-1, us-west-2, eu-west-1)"
  default     = false
}

# modules/ses/outputs.tf
output "domain_identity_arn" {
  value       = aws_ses_domain_identity.main.arn
  description = "ARN of the SES domain identity — use in IAM policies for ses:SendEmail"
}

output "configuration_set_name" {
  value       = aws_ses_configuration_set.main.name
  description = "Name of the SES configuration set — pass to application as env var"
}

output "dkim_tokens" {
  value       = aws_ses_domain_dkim.main.dkim_tokens
  description = "DKIM tokens — for informational purposes; Route53 records already created"
}

output "mail_from_domain" {
  value       = aws_ses_domain_mail_from.main.mail_from_domain
  description = "Custom MAIL FROM domain — use in DMARC policy record"
}
```

### Root Module Usage

```hcl
# root/main.tf
module "ses" {
  source = "./modules/ses"

  domain               = "example.com"
  route53_zone_id      = module.dns.zone_id
  bounce_sns_topic_arn = module.notifications.ses_topic_arn
  environment          = var.environment
  enable_receipt_rules = false

  depends_on = [module.dns]
}

# Pass configuration set name to application
output "ses_configuration_set" {
  value       = module.ses.configuration_set_name
  description = "SES configuration set name for application environment config"
}
```

---

## Integration Patterns

### Integration: Terraform ↔ Route53

**Pattern**: DNS records for SES domain verification, DKIM, MAIL FROM, and SPF
**Resources**: `aws_ses_domain_identity` → `aws_route53_record` (TXT), `aws_ses_domain_dkim` → `aws_route53_record` (3× CNAME), `aws_ses_domain_mail_from` → `aws_route53_record` (MX + TXT)

```hcl
data "aws_route53_zone" "main" {
  name         = var.email_domain
  private_zone = false
}

# SES verification TXT record
resource "aws_route53_record" "ses_verification" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "_amazonses.${aws_ses_domain_identity.main.domain}"
  type    = "TXT"
  ttl     = 600
  records = [aws_ses_domain_identity.main.verification_token]
}

# DKIM CNAME records (always 3)
resource "aws_route53_record" "dkim" {
  count   = 3
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "${aws_ses_domain_dkim.main.dkim_tokens[count.index]}._domainkey"
  type    = "CNAME"
  ttl     = 600
  records = ["${aws_ses_domain_dkim.main.dkim_tokens[count.index]}.dkim.amazonses.com"]
}
```

| Resource | Min Provider Version | Notes |
|----------|---------------------|-------|
| `aws_route53_record` | ~> 6.0 | `count.index` in CNAME names requires for_each alternative at scale |
| `data.aws_route53_zone` | ~> 6.0 | Use `private_zone = false` unless SES is for internal email only |

**Issues**: Route53 zone must exist before SES records; use `data` source, not `resource`, if zone is managed externally. DNS TTL affects propagation time for `aws_ses_domain_identity_verification`.

**Source**: [aws_route53_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record)

---

### Integration: Terraform ↔ SNS

**Pattern**: SNS topics receive SES bounce, complaint, and delivery notifications; can fan out to Lambda, SQS, or HTTP endpoints for processing

```hcl
resource "aws_sns_topic" "ses_bounces" {
  name              = "${var.environment}-ses-bounces"
  kms_master_key_id = "alias/aws/sns"  # Use CMK for sensitive email metadata

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# SES must be authorized to publish to the topic
resource "aws_sns_topic_policy" "ses_bounces" {
  arn = aws_sns_topic.ses_bounces.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowSESPublish"
      Effect = "Allow"
      Principal = {
        Service = "ses.amazonaws.com"
      }
      Action   = "SNS:Publish"
      Resource = aws_sns_topic.ses_bounces.arn
      Condition = {
        StringEquals = {
          "AWS:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })
}

resource "aws_ses_identity_notification_topic" "bounce" {
  identity                 = aws_ses_domain_identity.main.domain
  notification_type        = "Bounce"
  topic_arn                = aws_sns_topic.ses_bounces.arn
  include_original_headers = true
}
```

| Resource | Min Provider Version | Notes |
|----------|---------------------|-------|
| `aws_sns_topic` | ~> 6.0 | KMS encryption required for HIPAA/PCI compliance |
| `aws_sns_topic_policy` | ~> 6.0 | Source account condition prevents cross-account topic abuse |

**Issues**: SNS topic policy must be in place before `aws_ses_identity_notification_topic` — use `depends_on` or resource ordering. KMS CMK on SNS requires SES service principal to have `kms:GenerateDataKey*` and `kms:Decrypt` permissions.

**Source**: [aws_sns_topic_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_policy) | [SES Notification requirements](https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications-sns.html)

---

### Integration: Terraform ↔ S3 (Receipt Rules / Event Archive)

**Pattern**: S3 action in receipt rules stores inbound email; Kinesis Firehose event destination archives sending events to S3

```hcl
resource "aws_s3_bucket" "ses_inbox" {
  bucket = "${var.environment}-ses-inbox-${data.aws_caller_identity.current.account_id}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "ses_inbox" {
  bucket = aws_s3_bucket.ses_inbox.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ses_inbox" {
  bucket = aws_s3_bucket.ses_inbox.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# SES must be allowed to write to S3
resource "aws_s3_bucket_policy" "ses_inbox" {
  bucket = aws_s3_bucket.ses_inbox.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowSESPut"
      Effect = "Allow"
      Principal = {
        Service = "ses.amazonaws.com"
      }
      Action   = "s3:PutObject"
      Resource = "${aws_s3_bucket.ses_inbox.arn}/*"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })
}

# Receipt rule to store inbound email to S3
resource "aws_ses_receipt_rule" "store_email" {
  name          = "store-to-s3"
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
  recipients    = ["support@${var.email_domain}"]
  enabled       = true
  scan_enabled  = true  # Enable SES spam/virus scanning

  s3_action {
    bucket_name       = aws_s3_bucket.ses_inbox.id
    object_key_prefix = "emails/"
    position          = 1
  }

  depends_on = [aws_s3_bucket_policy.ses_inbox]
}
```

**Issues**: S3 bucket policy granting SES write access must be applied **before** creating `aws_ses_receipt_rule` with S3 action — SES validates bucket access at rule creation time. Missing bucket policy causes a silent rule creation failure with a confusing error.

**Source**: [SES Receipt Rule S3 action](https://docs.aws.amazon.com/ses/latest/dg/receiving-email-action-s3.html) | [aws_ses_receipt_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_receipt_rule)

---

### Integration: Terraform ↔ IAM

**Pattern**: IAM execution roles for applications sending email; IAM role for SES to publish to SNS/Kinesis; cross-account identity policies

```hcl
# Application role that can send email
data "aws_iam_policy_document" "ses_sender" {
  statement {
    sid    = "SendEmail"
    effect = "Allow"

    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail",
      "ses:SendTemplatedEmail",
    ]

    resources = [aws_ses_domain_identity.main.arn]

    condition {
      test     = "StringLike"
      variable = "ses:FromAddress"
      values   = ["*@${var.email_domain}"]  # Restrict to domain, not wildcard
    }
  }
}

# Identity policy for cross-account sending delegation
resource "aws_ses_identity_policy" "cross_account" {
  identity = aws_ses_domain_identity.main.arn
  name     = "cross-account-sending"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AuthorizeChildAccount"
      Effect = "Allow"
      Principal = {
        AWS = "arn:aws:iam::${var.child_account_id}:root"
      }
      Action   = ["ses:SendEmail", "ses:SendRawEmail"]
      Resource = aws_ses_domain_identity.main.arn
    }]
  })
}
```

| Resource | Min Provider Version | Notes |
|----------|---------------------|-------|
| `aws_ses_identity_policy` | ~> 6.0 | Max policy size 4,096 bytes; cannot be combined with `aws_ses_sending_authorization_policy` |

**Source**: [aws_ses_identity_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_identity_policy) | [SES sending authorization](https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html)

---

### Integration: Terraform ↔ CloudWatch

**Pattern**: CloudWatch alarms on SES sending metrics; CloudWatch event destination for sending event tracking

```hcl
# CloudWatch alarm for high bounce rate
resource "aws_cloudwatch_metric_alarm" "ses_bounce_rate" {
  alarm_name          = "${var.environment}-ses-bounce-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Reputation.BounceRate"
  namespace           = "AWS/SES"
  period              = 300
  statistic           = "Average"
  threshold           = 0.05  # 5% — AWS suspension threshold
  alarm_description   = "SES bounce rate exceeds 5% — account suspension risk"
  alarm_actions       = [aws_sns_topic.ses_notifications.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Alarm for high complaint rate
resource "aws_cloudwatch_metric_alarm" "ses_complaint_rate" {
  alarm_name          = "${var.environment}-ses-complaint-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Reputation.ComplaintRate"
  namespace           = "AWS/SES"
  period              = 300
  statistic           = "Average"
  threshold           = 0.001  # 0.1% — AWS suspension threshold
  alarm_description   = "SES complaint rate exceeds 0.1% — account suspension risk"
  alarm_actions       = [aws_sns_topic.ses_notifications.arn]
  treat_missing_data  = "notBreaching"
}
```

**Issues**: `AWS/SES` namespace metrics are only published when SES reputation tracking is enabled via configuration set (`reputation_metrics_enabled = true`). Without a configuration set, no reputation metrics appear in CloudWatch.

**Source**: [SES CloudWatch metrics](https://docs.aws.amazon.com/ses/latest/dg/monitor-using-cloudwatch.html)

---

### Integration: Terraform ↔ Lambda (Receipt Rules)

**Pattern**: Lambda function invoked by SES receipt rules to process inbound email

```hcl
resource "aws_lambda_permission" "ses_invoke" {
  statement_id  = "AllowSESInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.email_processor_lambda_arn
  principal     = "ses.amazonaws.com"
  source_account = data.aws_caller_identity.current.account_id
}

resource "aws_ses_receipt_rule" "process_email" {
  name          = "process-with-lambda"
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
  recipients    = ["inbound@${var.email_domain}"]
  enabled       = true
  scan_enabled  = true

  lambda_action {
    function_arn    = var.email_processor_lambda_arn
    invocation_type = "Event"  # Async invocation; use RequestResponse for sync
    position        = 1
  }

  depends_on = [aws_lambda_permission.ses_invoke]
}
```

**Issues**: `aws_lambda_permission` granting `ses.amazonaws.com` must be applied before `aws_ses_receipt_rule` — SES validates Lambda invoke permission at rule creation. `source_account` condition in the Lambda permission prevents other SES accounts from invoking your function.

**Source**: [SES Lambda action](https://docs.aws.amazon.com/ses/latest/dg/receiving-email-action-lambda.html)

---

## Quality Control

### Verification Commands

```bash
# Format validation
terraform fmt -recursive -check=true
# Expected: Exit code 0, no formatting changes needed

# Syntax validation
terraform validate
# Expected: "Success! The configuration is valid."

# Security scanning
tfsec . --minimum-severity HIGH
# Expected: No HIGH or CRITICAL findings
# Key checks: SES S3 bucket public access, SNS encryption, state file encryption

# Policy validation
checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks
# Watch for: CKV_AWS_197 (SES TLS), CKV_AWS_163 (SNS encryption)

# Plan verification
terraform plan -out=tfplan -lock=true
# Expected: Clean plan showing SES resources, Route53 records, SNS topics

# Show human-readable plan
terraform show tfplan | grep -E "aws_ses|aws_route53"
# Expected: Domain identity, DKIM, MAIL FROM, configuration set resources listed

# State validation after apply
terraform state list | grep ses
# Expected: All SES resources enumerated
# aws_ses_domain_identity.main
# aws_ses_domain_dkim.main
# aws_ses_domain_mail_from.main
# aws_ses_configuration_set.main
# aws_ses_event_destination.sns
# aws_ses_identity_notification_topic.bounce
# aws_ses_identity_notification_topic.complaint

# Verify SES domain verification status (out-of-band check)
aws ses get-identity-verification-attributes \
  --identities "example.com" \
  --region us-east-1
# Expected: "VerificationStatus": "Success"
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

func TestSESDeployment(t *testing.T) {
  t.Parallel()

  awsRegion := "us-east-1"

  opts := &terraform.Options{
    TerraformDir: "../examples/ses",
    Vars: map[string]interface{}{
      "environment":  "test",
      "email_domain": "test.example.com",
      "aws_region":   awsRegion,
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  // Verify SES domain identity ARN
  identityARN := terraform.Output(t, opts, "domain_identity_arn")
  assert.Contains(t, identityARN, "arn:aws:ses")
  assert.Contains(t, identityARN, "test.example.com")

  // Verify configuration set exists
  configSetName := terraform.Output(t, opts, "configuration_set_name")
  assert.NotEmpty(t, configSetName)

  // Verify DKIM tokens output
  dkimTokens := terraform.OutputList(t, opts, "dkim_tokens")
  assert.Equal(t, 3, len(dkimTokens), "Expected 3 DKIM tokens")
}
```

---

## Drift Detection & Reconciliation

### Scenario: DNS Record Deleted Outside Terraform

```
Detection:
  terraform plan
  # Output shows Route53 records marked as "(known after apply)" or drift
  # If Route53 record was deleted: "aws_route53_record.dkim[0] will be created"

Recovery:
  terraform apply  # Re-creates deleted DNS records

# Verify no drift after recovery
terraform plan
# Expected: "No changes. Infrastructure is up-to-date."
```

### Scenario: SES Domain Identity Deleted in Console

```bash
# Detect deletion
terraform plan
# Output: "aws_ses_domain_identity.main will be created"
# (SES identity deleted = new identity needed, new verification token generated)

# Recover — apply will re-register and generate new verification token
terraform apply
# IMPORTANT: New verification token requires updating Route53 TXT record
# This happens automatically if Route53 record is in same workspace

# If identity was only partially deleted (DKIM removed):
terraform import aws_ses_domain_dkim.main "example.com"
```

### Lifecycle Protection

```hcl
# Protect domain identity from accidental destruction
resource "aws_ses_domain_identity" "main" {
  domain = var.email_domain

  lifecycle {
    prevent_destroy = true  # Add for production — removing costs re-verification time
  }
}
```

---

## Secrets & Sensitive Data Management

### SES SMTP Credentials (IAM User SMTP Credentials)

```
Secret Type: SES SMTP password (derived from IAM secret access key)
Storage: AWS Secrets Manager
Retrieval: data.aws_secretsmanager_secret_version

NOTE: SES SMTP credentials are NOT standard IAM credentials.
They must be derived from the IAM secret access key using an HMAC-SHA256 algorithm.
Terraform cannot generate SES SMTP passwords natively — this must be done
via AWS CLI: aws ses create-smtp-credentials --set-name ...
OR use the SESv2 API.
```

```hcl
# Store SES SMTP credentials in Secrets Manager (set externally)
data "aws_secretsmanager_secret_version" "ses_smtp" {
  secret_id = "/${var.environment}/ses/smtp-credentials"
}

# Pass to application via ECS task definition or Lambda env vars (sensitive)
output "ses_smtp_endpoint" {
  value       = "email-smtp.${var.aws_region}.amazonaws.com"
  description = "SES SMTP endpoint — not sensitive, but region-dependent"
  sensitive   = false
}
```

### Sensitive Outputs

```hcl
# SES domain identity ARN — not sensitive but include for completeness
output "domain_identity_arn" {
  value       = aws_ses_domain_identity.main.arn
  description = "SES domain identity ARN — used in IAM policies"
  sensitive   = false
}

# Mark DKIM tokens as sensitive (optional — tokens are public DNS CNAME values
# but marking sensitive prevents accidental log exposure)
output "dkim_tokens" {
  value       = aws_ses_domain_dkim.main.dkim_tokens
  description = "DKIM tokens — informational only; Route53 records already created"
  sensitive   = false  # Safe to display — values are publicly visible in DNS
}
```

---

## Production Considerations

### SES Regional Availability

```
SES sending regions (as of 2026):
  us-east-1 (N. Virginia) — also supports inbound receipt rules
  us-west-2 (Oregon) — also supports inbound receipt rules
  eu-west-1 (Ireland) — also supports inbound receipt rules
  eu-central-1 (Frankfurt) — sending only
  ap-southeast-1 (Singapore) — sending only
  ap-southeast-2 (Sydney) — sending only
  ap-northeast-1 (Tokyo) — sending only
  ca-central-1 (Canada) — sending only
  sa-east-1 (São Paulo) — sending only

Challenge: SES is region-scoped — a domain identity in us-east-1 cannot be
used to send from eu-west-1 without re-verifying in that region.
Solution: Multi-region deployments require separate domain identities per region.
          Use terraform workspaces or separate root modules per region.
```

### Sending Limits and Sandbox Mode

```
Scenario: New AWS account (Sandbox mode)
Challenge: 200 emails/day, send only to verified addresses
Solution: Request production access via AWS Support case
          (typical approval: 24-48 hours)

Runbook:
  1. Terraform deploys SES configuration
  2. Verify domain in SES console shows "Verified"
  3. File AWS Support case: Service Limit Increase → SES Sending Limits
  4. Specify: use case (transactional), estimated volume, bounce/complaint handling

Terraform cannot automate sandbox removal — requires AWS Support approval.
```

### Monitoring & Alerting

```hcl
# Reputation dashboard alarms (requires configuration set with reputation_metrics_enabled)
resource "aws_cloudwatch_metric_alarm" "ses_bounce_rate" {
  alarm_name          = "${var.environment}-ses-bounce-rate"
  metric_name         = "Reputation.BounceRate"
  namespace           = "AWS/SES"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  period              = 300
  statistic           = "Average"
  threshold           = 0.05   # 5% = AWS suspension threshold
  alarm_actions       = [aws_sns_topic.ses_notifications.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "ses_complaint_rate" {
  alarm_name          = "${var.environment}-ses-complaint-rate"
  metric_name         = "Reputation.ComplaintRate"
  namespace           = "AWS/SES"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  period              = 300
  statistic           = "Average"
  threshold           = 0.001  # 0.1% = AWS suspension threshold
  alarm_actions       = [aws_sns_topic.ses_notifications.arn]
  treat_missing_data  = "notBreaching"
}
```

### Security Checklist

- [ ] All SMTP credentials stored in Secrets Manager (never in `.tfvars` or code)
- [ ] State file encryption enabled (S3 + KMS)
- [ ] Domain identity + DKIM configured for all sending domains
- [ ] Custom MAIL FROM domain configured for DMARC alignment
- [ ] Bounce and Complaint SNS notifications configured on all identities
- [ ] SES TLS enforcement (`tls_policy = "Require"`) on all configuration sets
- [ ] IAM sender policies scoped to specific identity ARN and FromAddress
- [ ] SNS topics for notifications encrypted with KMS
- [ ] S3 bucket (for receipt rules/event archive) has public access blocked
- [ ] S3 bucket policy uses `aws:SourceAccount` condition to prevent confused deputy
- [ ] CloudWatch alarms on bounce rate (>5%) and complaint rate (>0.1%)
- [ ] Lambda `source_account` condition in `aws_lambda_permission` for receipt rules

### Disaster Recovery Runbook

```bash
# 1. SES domain identity deleted / verification reset
aws ses get-identity-verification-attributes \
  --identities "example.com" \
  --region us-east-1
# If status != "Success":

terraform plan  # Will show re-create
terraform apply  # Re-registers identity and DKIM tokens (Route53 records auto-updated)

# 2. State corruption recovery
aws s3api get-object \
  --bucket my-org-terraform-state \
  --key prod/ses/terraform.tfstate.backup \
  terraform.tfstate.backup

terraform state push terraform.tfstate.backup

# 3. Import existing SES resources
terraform import aws_ses_domain_identity.main "example.com"
terraform import aws_ses_domain_dkim.main "example.com"
terraform import aws_ses_domain_mail_from.main "example.com"
terraform import aws_ses_configuration_set.main "config-set-name"
terraform import aws_ses_event_destination.sns "config-set-name/destination-name"

# 4. Verify state matches infrastructure
terraform plan
# Expected: No changes after successful import
```

---

## Complete Working Example

### Root Module: Production SES Deployment

```hcl
# terraform.tfvars
email_domain = "example.com"
environment  = "production"
aws_region   = "us-east-1"
account_id   = "123456789012"
owner        = "platform-team"
cost_center  = "platform"

# main.tf
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
    key            = "prod/ses/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformRole"
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

data "aws_caller_identity" "current" {}

data "aws_route53_zone" "main" {
  name         = var.email_domain
  private_zone = false
}

# === Identity ===

resource "aws_ses_domain_identity" "main" {
  domain = var.email_domain
}

resource "aws_route53_record" "ses_verification" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "_amazonses.${aws_ses_domain_identity.main.domain}"
  type    = "TXT"
  ttl     = 600
  records = [aws_ses_domain_identity.main.verification_token]
}

resource "aws_ses_domain_dkim" "main" {
  domain = aws_ses_domain_identity.main.domain
}

resource "aws_route53_record" "dkim" {
  count   = 3
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "${aws_ses_domain_dkim.main.dkim_tokens[count.index]}._domainkey"
  type    = "CNAME"
  ttl     = 600
  records = ["${aws_ses_domain_dkim.main.dkim_tokens[count.index]}.dkim.amazonses.com"]
}

resource "aws_ses_domain_mail_from" "main" {
  domain           = aws_ses_domain_identity.main.domain
  mail_from_domain = "bounce.${var.email_domain}"
}

resource "aws_route53_record" "mail_from_mx" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "bounce.${var.email_domain}"
  type    = "MX"
  ttl     = 600
  records = ["10 feedback-smtp.${var.aws_region}.amazonses.com"]
}

resource "aws_route53_record" "mail_from_spf" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "bounce.${var.email_domain}"
  type    = "TXT"
  ttl     = 600
  records = ["v=spf1 include:amazonses.com ~all"]
}

# === Notifications ===

resource "aws_sns_topic" "ses_notifications" {
  name              = "${var.environment}-ses-notifications"
  kms_master_key_id = "alias/aws/sns"
}

resource "aws_sns_topic_policy" "ses_notifications" {
  arn = aws_sns_topic.ses_notifications.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowSESPublish"
      Effect = "Allow"
      Principal = { Service = "ses.amazonaws.com" }
      Action   = "SNS:Publish"
      Resource = aws_sns_topic.ses_notifications.arn
      Condition = {
        StringEquals = { "AWS:SourceAccount" = data.aws_caller_identity.current.account_id }
      }
    }]
  })
}

resource "aws_ses_identity_notification_topic" "bounce" {
  identity                 = aws_ses_domain_identity.main.domain
  notification_type        = "Bounce"
  topic_arn                = aws_sns_topic.ses_notifications.arn
  include_original_headers = true
}

resource "aws_ses_identity_notification_topic" "complaint" {
  identity                 = aws_ses_domain_identity.main.domain
  notification_type        = "Complaint"
  topic_arn                = aws_sns_topic.ses_notifications.arn
  include_original_headers = true
}

# === Configuration Set ===

resource "aws_ses_configuration_set" "main" {
  name = "${var.environment}-ses-config"

  delivery_options {
    tls_policy = "Require"
  }

  reputation_metrics_enabled = true
  sending_enabled            = true
}

resource "aws_ses_event_destination" "cloudwatch" {
  name                   = "${var.environment}-cw-events"
  configuration_set_name = aws_ses_configuration_set.main.name
  enabled                = true
  matching_types         = ["bounce", "complaint", "send"]

  cloudwatch_destination {
    default_value  = "none"
    dimension_name = "ses:caller-identity"
    value_source   = "messageTag"
  }
}

# === IAM ===

data "aws_iam_policy_document" "ses_sender" {
  statement {
    effect    = "Allow"
    actions   = ["ses:SendEmail", "ses:SendRawEmail", "ses:SendTemplatedEmail"]
    resources = [aws_ses_domain_identity.main.arn]

    condition {
      test     = "StringLike"
      variable = "ses:FromAddress"
      values   = ["*@${var.email_domain}"]
    }
  }
}

resource "aws_iam_policy" "ses_sender" {
  name        = "${var.environment}-ses-sender"
  description = "Allows application to send email via SES"
  policy      = data.aws_iam_policy_document.ses_sender.json
}

# === Monitoring ===

resource "aws_cloudwatch_metric_alarm" "ses_bounce_rate" {
  alarm_name          = "${var.environment}-ses-bounce-high"
  metric_name         = "Reputation.BounceRate"
  namespace           = "AWS/SES"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  period              = 300
  statistic           = "Average"
  threshold           = 0.05
  alarm_description   = "SES bounce rate > 5% — account suspension risk"
  alarm_actions       = [aws_sns_topic.ses_notifications.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "ses_complaint_rate" {
  alarm_name          = "${var.environment}-ses-complaint-high"
  metric_name         = "Reputation.ComplaintRate"
  namespace           = "AWS/SES"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  period              = 300
  statistic           = "Average"
  threshold           = 0.001
  alarm_description   = "SES complaint rate > 0.1% — account suspension risk"
  alarm_actions       = [aws_sns_topic.ses_notifications.arn]
  treat_missing_data  = "notBreaching"
}

# === Outputs ===

output "domain_identity_arn" {
  value       = aws_ses_domain_identity.main.arn
  description = "SES domain identity ARN — use in IAM sender policy"
}

output "configuration_set_name" {
  value       = aws_ses_configuration_set.main.name
  description = "Configuration set name — pass to application as SES_CONFIGURATION_SET env var"
}

output "ses_sender_policy_arn" {
  value       = aws_iam_policy.ses_sender.arn
  description = "IAM policy ARN — attach to application role"
}

output "ses_notifications_topic_arn" {
  value       = aws_sns_topic.ses_notifications.arn
  description = "SNS topic ARN for bounce/complaint notifications"
}
```

---

## Reference Implementations

- [Official Terraform AWS Examples](https://github.com/hashicorp/terraform-aws-examples)
- [AWS SES Developer Guide](https://docs.aws.amazon.com/ses/latest/dg/Welcome.html)
- [Terraform AWS Provider SES Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#ses-simple-email)
- [AWS SES Best Practices](https://docs.aws.amazon.com/ses/latest/dg/best-practices.html)
- [DMARC Configuration Guide](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html)

---

## Source Bibliography

### Primary Sources
- [aws_ses_domain_identity](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_identity) — verified 2026-05-28 (aws v6.47.0)
- [aws_ses_email_identity](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_email_identity) — verified 2026-05-28
- [aws_ses_domain_dkim](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_dkim) — verified 2026-05-28
- [aws_ses_domain_identity_verification](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_identity_verification) — verified 2026-05-28
- [aws_ses_domain_mail_from](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_mail_from) — verified 2026-05-28
- [aws_ses_configuration_set](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_configuration_set) — verified 2026-05-28
- [aws_ses_event_destination](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_event_destination) — verified 2026-05-28
- [aws_ses_identity_notification_topic](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_identity_notification_topic) — verified 2026-05-28
- [aws_ses_identity_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_identity_policy) — verified 2026-05-28
- [aws_ses_receipt_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_receipt_rule) — verified 2026-05-28
- [aws_ses_receipt_rule_set](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_receipt_rule_set) — verified 2026-05-28
- [aws_ses_active_receipt_rule_set](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_active_receipt_rule_set) — verified 2026-05-28
- [aws_ses_template](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_template) — verified 2026-05-28
- [aws_ses_receipt_filter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_receipt_filter) — verified 2026-05-28
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language) — HCL reference
- [AWS SES Developer Guide](https://docs.aws.amazon.com/ses/latest/dg/Welcome.html)
- [AWS SES IAM Actions Reference](https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html)

### Validation & Tools
- [tfsec GitHub](https://github.com/aquasecurity/tfsec) — Security scanner (SES checks: sns encryption, s3 public access)
- [Checkov](https://www.checkov.io/) — CKV_AWS_197 (SES TLS), CKV_AWS_163 (SNS encryption)
- [Terratest](https://terratest.gruntwork.io/) — Integration testing framework
- GitHub Issues: [hashicorp/terraform-provider-aws SES label](https://github.com/hashicorp/terraform-provider-aws/issues?q=label%3Aservice%2Fses)

---

## Research Gaps

```
Gap: aws_ses_configuration_set delivery_options tls_policy validation at plan time
Impact: Invalid TLS policy value only caught at apply time, not plan
Workaround: Use variable validation with contains(["Require", "Optional"], ...)
Follow-up: https://github.com/hashicorp/terraform-provider-aws/issues (ses label)

Gap: Terraform cannot generate SES SMTP credentials (derived IAM key)
Impact: SMTP password rotation must be done outside Terraform (AWS CLI or console)
Workaround: Use SES API directly (AWS SDK), store result in Secrets Manager manually
Follow-up: https://docs.aws.amazon.com/ses/latest/dg/smtp-credentials.html

Gap: aws_ses_domain_identity_verification eventual-consistency with high-TTL DNS
Impact: CI pipelines may timeout on first deployment in zones with >600s TTL
Workaround: Set timeouts { create = "2h" } or skip verification resource; validate in post-deploy check
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_domain_identity_verification

Gap: SES receipt rules (inbound) region restriction not validated by Terraform
Impact: aws_ses_receipt_rule_set apply succeeds in all regions, but inbound routing only works in us-east-1, us-west-2, eu-west-1
Workaround: Add variable validation on aws_region to restrict to inbound-capable regions when enable_receipt_rules = true
Follow-up: https://docs.aws.amazon.com/ses/latest/dg/regions.html#region-receive-email

Gap: SES v1 vs. SESv2 resource coexistence
Impact: aws_ses_* and aws_sesv2_* resources can conflict on the same identity (e.g., configuration sets have different ARN formats)
Workaround: Choose one API version per deployment; do not mix v1 and v2 resources on same domain
Follow-up: https://docs.aws.amazon.com/ses/latest/dg/what-is.html
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Domain identity + DKIM + MAIL FROM + Route53 records
- Bounce/Complaint SNS notification configuration
- Configuration set with TLS enforcement
- IAM least-privilege sending policies
- State management setup and backend configuration
- CloudWatch alarms on bounce/complaint rates

### Medium Confidence (Validate with user)
- SES v1 vs. SESv2 API choice
- Inbound receipt rules vs. sending only
- SNS vs. CloudWatch vs. Kinesis event destination
- Single-region vs. multi-region SES deployment

### Low Confidence (Must ask user)
- Sandbox → production access request (requires AWS Support case — not automatable)
- DMARC policy strictness (`p=none` vs. `p=quarantine` vs. `p=reject`)
- Dedicated IP vs. shared IP pool for high-volume sending
- Custom DKIM key length (SES defaults to 2048-bit RSA)

### Emergency Stop
- Halt if state file encryption is disabled
- Halt if SMTP credentials are found hardcoded in any `.tf` or `.tfvars` file
- Halt if `aws_ses_*` resources are planned for a region that doesn't support SES
- Halt if `prevent_destroy = false` on production domain identity (deletion means re-verification)
