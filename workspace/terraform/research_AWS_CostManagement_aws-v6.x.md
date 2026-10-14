# Terraform AWS Cost Management — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - Cost Management (Budgets, Cost Explorer, Anomaly Detection)"
Cloud_Provider: "AWS"
Target_Service: "Cost Management (aws_budgets_budget, aws_ce_anomaly_monitor, aws_ce_anomaly_subscription, aws_ce_cost_allocation_tag, aws_ce_cost_category, aws_budgets_budget_action)"
Terraform_Version: "1.9"
Provider_Version: "aws v6.x (latest: 6.47.0, published 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Budgets_Resource: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget"
Budget_Action_Resource: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget_action"
CE_Anomaly_Monitor_Resource: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_anomaly_monitor"
CE_Anomaly_Subscription_Resource: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_anomaly_subscription"
CE_Cost_Allocation_Tag_Resource: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_allocation_tag"
CE_Cost_Category_Resource: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_category"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-28"
Domain_Complexity: "Standard"
Integration_Partners: "SNS, IAM, S3, Organizations, CloudWatch, KMS, DynamoDB"
Use_Modules: true
Use_Workspaces: false
```

---

## Executive Summary

AWS Cost Management is the suite of services that provides cost visibility, governance, and optimization for AWS workloads. It centers on **AWS Budgets** (`aws_budgets_budget`) for proactive threshold alerts and automated enforcement actions, **Cost Anomaly Detection** (`aws_ce_anomaly_monitor` + `aws_ce_anomaly_subscription`) for ML-based spend anomaly alerting, **Cost Allocation Tags** (`aws_ce_cost_allocation_tag`) for activating resource tags as cost dimensions in Cost Explorer, and **Cost Categories** (`aws_ce_cost_category`) for rule-based cost grouping across accounts and services. Budget Actions (`aws_budgets_budget_action`) extend budgets with automated IAM policy enforcement, SCP application, and EC2/RDS instance shutdown. Together these resources implement the full FinOps inform-optimize-operate lifecycle through Terraform-managed infrastructure-as-code.

The Terraform AWS provider v6.x introduces critical changes relevant to this domain: `aws_budgets_budget` now supports a `filter_expression` block with logical operators (`and`, `or`, `not`) and explicit `metrics` definitions (replacing legacy `cost_filter` for new deployments); the two approaches are mutually exclusive — `filter_expression` conflicts with `cost_filter`, and `metrics` conflicts with `cost_types`. The new expression-based filter unlocks compound filtering (e.g., multi-service AND environment-tag combinations) and explicit cost metric selection (`UnblendedCost`, `BlendedCost`, `AmortizedCost`, `NetUnblendedCost`, `NetAmortizedCost`). Budget auto-adjust data is now natively supported (historical or forecast-based auto-adjusting limits). Cost Anomaly Detection subscriptions use `threshold_expression` with dimension-based conditions (`ANOMALY_TOTAL_IMPACT_ABSOLUTE`, `ANOMALY_TOTAL_IMPACT_PERCENTAGE`) rather than deprecated numeric threshold fields.

Domain complexity is **Standard** because: resources are non-stateful (no persistent infrastructure — only billing configuration objects), there are no VPC dependencies or network security surfaces, all Cost Management API endpoints are global (no region constraints beyond management account requirements), and the primary risk profile is governance misconfiguration rather than infrastructure drift. However, IAM least-privilege for `aws_budgets_budget_action` execution roles requires careful scoping, cost allocation tag activation must run in the management (payer) account, and anomaly detection subscription SNS policies require explicit service principal grants from `costalerts.amazonaws.com`.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

#### Pattern: Terraform Configuration Block

- **Why**: Enforces exact provider version contracts; prevents use of deprecated `cost_filter` patterns removed in future provider versions; ensures `filter_expression` features are available
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
    key            = "prod/cost-management/terraform.tfstate"
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

#### Pattern: Provider Configuration with IAM Role and Default Tags

- **Why**: Cost Management resources are global (billing plane); `assume_role` isolates blast radius per account; `default_tags` enforces tagging across all resources including budget objects; no credential hardcoding
- **Code**:
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
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [Provider Configuration Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#default_tags-configuration-block)

---

#### Pattern: Monthly Cost Budget with Both ACTUAL and FORECASTED Notifications

- **Why**: ACTUAL alert fires after overspend occurs; FORECASTED alert provides advance warning before month-end; both together are the minimum viable budget governance. Without FORECASTED, teams learn of overruns only after the fact.
- **Code**:
```hcl
resource "aws_budgets_budget" "monthly_cost" {
  name         = "${var.environment}-monthly-cost-budget"
  budget_type  = "COST"
  limit_amount = var.monthly_budget_usd
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  # ACTUAL: Alert when real spend crosses 80% and 100% thresholds
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_alerts.arn]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_alerts.arn]
    subscriber_email_addresses = var.billing_alert_emails
  }

  # FORECASTED: Early warning before month-end overspend
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_alerts.arn]
    subscriber_email_addresses = var.billing_alert_emails
  }

  tags = {
    Name        = "${var.environment}-monthly-cost-budget"
    Environment = var.environment
  }
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_budgets_budget](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget)

---

#### Pattern: Cost Anomaly Monitor (DIMENSIONAL — AWS Services)

- **Why**: AWS-managed dimensional monitor tracks ALL AWS services automatically; zero maintenance as new services are onboarded; single monitor covers all spend anomalies without manual service enumeration
- **Code**:
```hcl
resource "aws_ce_anomaly_monitor" "aws_services" {
  name              = "${var.environment}-aws-services-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"

  tags = {
    Name        = "${var.environment}-aws-services-monitor"
    Environment = var.environment
  }
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_ce_anomaly_monitor](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_anomaly_monitor)

---

#### Pattern: Cost Anomaly Subscription with SNS and Dual Threshold

- **Why**: SNS enables downstream integrations (Lambda, PagerDuty, Slack); dual threshold (absolute + percentage) prevents alert fatigue on small accounts while catching absolute spikes on large accounts; `costalerts.amazonaws.com` service principal must be granted SNS Publish permission
- **Code**:
```hcl
resource "aws_sns_topic" "cost_anomaly_updates" {
  name              = "${var.environment}-cost-anomaly-updates"
  kms_master_key_id = aws_kms_key.sns.arn

  tags = {
    Name        = "${var.environment}-cost-anomaly-updates"
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "cost_anomaly_sns_policy" {
  policy_id = "__default_policy_ID"

  # Allow Cost Anomaly Detection to publish anomaly alerts
  statement {
    sid     = "AllowCostAnomalyDetectionPublish"
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type        = "Service"
      identifiers = ["costalerts.amazonaws.com"]
    }

    resources = [aws_sns_topic.cost_anomaly_updates.arn]
  }

  # Default SNS topic policy for account owner
  statement {
    sid     = "__default_statement_ID"
    effect  = "Allow"
    actions = [
      "SNS:Subscribe", "SNS:SetTopicAttributes",
      "SNS:RemovePermission", "SNS:Receive",
      "SNS:Publish", "SNS:ListSubscriptionsByTopic",
      "SNS:GetTopicAttributes", "SNS:DeleteTopic",
      "SNS:AddPermission",
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceOwner"
      values   = [var.account_id]
    }

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    resources = [aws_sns_topic.cost_anomaly_updates.arn]
  }
}

resource "aws_sns_topic_policy" "cost_anomaly" {
  arn    = aws_sns_topic.cost_anomaly_updates.arn
  policy = data.aws_iam_policy_document.cost_anomaly_sns_policy.json
}

resource "aws_ce_anomaly_subscription" "realtime" {
  name      = "${var.environment}-realtime-anomaly-subscription"
  frequency = "IMMEDIATE"

  monitor_arn_list = [
    aws_ce_anomaly_monitor.aws_services.arn
  ]

  subscriber {
    type    = "SNS"
    address = aws_sns_topic.cost_anomaly_updates.arn
  }

  # Alert when anomaly exceeds $100 AND 20% above baseline
  threshold_expression {
    and {
      dimension {
        key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
        match_options = ["GREATER_THAN_OR_EQUAL"]
        values        = ["100"]
      }
    }
    and {
      dimension {
        key           = "ANOMALY_TOTAL_IMPACT_PERCENTAGE"
        match_options = ["GREATER_THAN_OR_EQUAL"]
        values        = ["20"]
      }
    }
  }

  depends_on = [aws_sns_topic_policy.cost_anomaly]

  tags = {
    Name        = "${var.environment}-realtime-anomaly-subscription"
    Environment = var.environment
  }
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_ce_anomaly_subscription](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_anomaly_subscription)

---

#### Pattern: Cost Allocation Tag Activation

- **Why**: Tags applied to resources do NOT appear as cost dimensions in Cost Explorer until explicitly activated; activation is irreversible per tag key (can only deactivate, not delete); must run in management/payer account for multi-account orgs; takes up to 24 hours to appear after activation
- **Code**:
```hcl
# Activate standard organizational tags as cost allocation tags
# NOTE: Run this module from the management (payer) account only
resource "aws_ce_cost_allocation_tag" "environment" {
  tag_key = "Environment"
  status  = "Active"
}

resource "aws_ce_cost_allocation_tag" "team" {
  tag_key = "Team"
  status  = "Active"
}

resource "aws_ce_cost_allocation_tag" "application" {
  tag_key = "Application"
  status  = "Active"
}

resource "aws_ce_cost_allocation_tag" "cost_center" {
  tag_key = "CostCenter"
  status  = "Active"
}

# Activate AWS Organizations account tags (prefix with accountTag/)
resource "aws_ce_cost_allocation_tag" "account_environment" {
  tag_key = "accountTag/Environment"
  status  = "Active"
}
```
- **Terraform Version**: 1.9+
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_ce_cost_allocation_tag](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_allocation_tag)

---

#### Pattern: Variable Validation and Type Safety

- **Why**: Prevents invalid configurations at `terraform plan` time; budget amounts must be positive numbers; notification thresholds must be within valid ranges; email addresses must be valid format
- **Code**:
```hcl
variable "monthly_budget_usd" {
  type        = string
  description = "Monthly budget limit in USD (e.g., '500.00')"

  validation {
    condition     = can(tonumber(var.monthly_budget_usd)) && tonumber(var.monthly_budget_usd) > 0
    error_message = "Monthly budget must be a positive numeric value string (e.g., '500.00')."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "billing_alert_emails" {
  type        = list(string)
  description = "List of email addresses for billing alert notifications"
  default     = []

  validation {
    condition     = alltrue([for email in var.billing_alert_emails : can(regex("^[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}$", email))])
    error_message = "All billing alert emails must be valid email addresses."
  }
}

variable "anomaly_absolute_threshold_usd" {
  type        = number
  description = "Minimum absolute spend anomaly (USD) that triggers an alert"
  default     = 100

  validation {
    condition     = var.anomaly_absolute_threshold_usd >= 1
    error_message = "Absolute anomaly threshold must be at least $1 USD."
  }
}

variable "account_id" {
  type        = string
  description = "AWS Account ID for SNS policy and assume_role"

  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Account ID must be exactly 12 digits."
  }
}
```
- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

### ⚠️ Conditional Patterns

#### Decision: Legacy `cost_filter` vs New `filter_expression` on `aws_budgets_budget`

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **`cost_filter`** (legacy) | Backward compat, simpler syntax, no `metrics` required | Compound logic (AND/OR/NOT), explicit metric selection, future-proofing | Existing budgets, simple single-dimension filters, teams migrating gradually |
| **`filter_expression`** (v6.x) | Compound filters (AND/OR/NOT nesting up to depth 2), explicit metric types, expression reuse | Requires `metrics` field, cannot combine with `cost_filter` | New budgets, multi-dimension filtering, explicit cost metric (amortized, net unblended) |

**Important**: The two approaches conflict — `filter_expression` cannot be used with `cost_filter`, and `metrics` cannot be used with `cost_types`. Choose one approach per budget resource.

- **Agent**: "Ask user: Are you creating a new budget or maintaining an existing one? Do you need compound filtering (e.g., service AND tag combinations)?"
- **Source**: [aws_budgets_budget filter_expression](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget#filter_expression)

---

#### Decision: Static Budget Limit vs Auto-Adjust Budget

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Static `limit_amount`** | Predictable spend cap, hard governance ceiling, simple audit | Doesn't adapt to natural growth, requires manual updates | Fixed-spend projects, compliance budgets, cost freeze environments |
| **`planned_limit` blocks** | Seasonality modeling, fiscal year alignment, project-based budgets up to 3 years | Complex configuration, requires upfront planning | Seasonal workloads (e.g., holiday traffic ramp), project-based budgets |
| **`auto_adjust_data` (HISTORICAL)** | Adapts to organic growth, reduces false alerts as usage grows | No hard ceiling (won't stop overspend), may mask cost anomalies | Growth-stage products, teams doing exploratory development |
| **`auto_adjust_data` (FORECAST)** | Proactively adjusts before spend occurs | Less predictable, relies on forecast accuracy | Mature workloads with predictable patterns |

- **Agent**: "Ask user: Is this a governance/compliance budget (use static) or an informational alerting budget (consider auto-adjust)? Is spend expected to grow organically?"
- **Source**: [aws_budgets_budget auto_adjust_data](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget#auto_adjust_data)

---

#### Decision: DIMENSIONAL vs CUSTOM Anomaly Monitor

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **`DIMENSIONAL` (SERVICE/LINKED_ACCOUNT/TAG/COST_CATEGORY)** | Zero-maintenance, auto-discovers new services/accounts, broad coverage | Less targeted, may alert on expected spend changes | Default choice; covers entire org with one monitor per dimension |
| **`CUSTOM` (JSON expression filter)** | Targets specific tag/service combinations, isolates team-specific spend | Manual maintenance, won't auto-include new services, complex JSON spec | When specific team or workload needs isolated anomaly tracking |

- **Agent**: "Ask user: Do you need org-wide anomaly detection (use DIMENSIONAL) or per-team/workload tracking (use CUSTOM with tag-based monitor specification)?"
- **Source**: [aws_ce_anomaly_monitor](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_anomaly_monitor)

---

#### Decision: Budget Action Approval Model (AUTOMATIC vs MANUAL)

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **`AUTOMATIC`** | Immediate enforcement without human delay, strong cost governance | Risk of unexpected resource shutdown if thresholds set too low, requires tested IAM policies | Production cost governance with well-tested thresholds (≥110% of expected) |
| **`MANUAL`** | Human approval gate, prevents accidental enforcement, safer for first deployment | Response delay (hours/days), requires monitoring workflow | Initial deployment, dev environments, low-stakes budgets |

- **Agent**: "Ask user: Is this budget action for automatic cost enforcement or as an alert requiring manual review? What threshold percentage triggers the action?"
- **Source**: [aws_budgets_budget_action](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget_action)

---

#### Decision: Cost Category vs Cost Allocation Tags for Attribution

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Cost Allocation Tags** | Simple activation, works with resource tags already applied, supports Organizations account tags | Requires consistent tagging across all resources, only covers tagable resources, not retroactive | Teams with strong tagging discipline, greenfield environments |
| **Cost Categories** | Retroactive (applies to historical data), covers untaggable resources (support, data transfer), complex rule-based logic | Up to 50 categories × 500 rules, cannot use in IAM policies, additional configuration overhead | Organizations with incomplete tagging, shared services, multi-account chargeback |

- **Agent**: "Ask user: Is resource tagging already enforced across the organization? Do you need to handle costs from untaggable resources (support charges, data transfer)?"
- **Source**: [aws_ce_cost_allocation_tag](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_allocation_tag), [aws_ce_cost_category](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_category)

---

### 🚫 Forbidden Patterns

#### Anti-Pattern: Missing FORECASTED Budget Notification

```hcl
# DON'T — Only ACTUAL notification; no advance warning
resource "aws_budgets_budget" "bad_budget" {
  name         = "monthly-budget"
  budget_type  = "COST"
  limit_amount = "1000"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"     # DON'T — No FORECASTED counterpart
    subscriber_email_addresses = ["ops@example.com"]
  }
}
```

- **Why**: ACTUAL-only alerts notify after overspend has already occurred; by end-of-month, the bill is locked; FORECASTED alerts fire with 7-14 days of lead time, allowing mitigation
- **Instead**:
```hcl
# DO — Both ACTUAL and FORECASTED notifications
resource "aws_budgets_budget" "good_budget" {
  name         = "monthly-budget"
  budget_type  = "COST"
  limit_amount = "1000"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_alerts.arn]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"  # Early warning
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_alerts.arn]
  }
}
```
- **Impact**: Governance failure — cost overruns discovered only after billing period closes
- **Severity**: HIGH
- **Source**: [AWS Budgets Best Practices](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html)

---

#### Anti-Pattern: Anomaly Subscription Without SNS Policy for `costalerts.amazonaws.com`

```hcl
# DON'T — SNS topic without Cost Anomaly Detection service principal
resource "aws_sns_topic" "alerts" {
  name = "cost-alerts"
  # No topic policy granting costalerts.amazonaws.com permission
}

resource "aws_ce_anomaly_subscription" "bad" {
  name      = "anomaly-sub"
  frequency = "IMMEDIATE"
  monitor_arn_list = [aws_ce_anomaly_monitor.monitor.arn]

  subscriber {
    type    = "SNS"
    address = aws_sns_topic.alerts.arn
    # Will silently fail — SNS will reject Publish from Cost Anomaly Detection
  }
}
```

- **Why**: Cost Anomaly Detection publishes via service principal `costalerts.amazonaws.com` — without explicit SNS policy, the subscription silently fails; no anomaly alerts are ever delivered; there is no apply-time error
- **Instead**:
```hcl
# DO — Grant costalerts.amazonaws.com SNS Publish permission
data "aws_iam_policy_document" "allow_cost_anomaly_publish" {
  statement {
    sid     = "AllowCostAnomalyDetectionPublish"
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type        = "Service"
      identifiers = ["costalerts.amazonaws.com"]
    }

    resources = [aws_sns_topic.alerts.arn]
  }
}

resource "aws_sns_topic_policy" "cost_anomaly_policy" {
  arn    = aws_sns_topic.alerts.arn
  policy = data.aws_iam_policy_document.allow_cost_anomaly_publish.json
}

resource "aws_ce_anomaly_subscription" "good" {
  name      = "anomaly-sub"
  frequency = "IMMEDIATE"
  monitor_arn_list = [aws_ce_anomaly_monitor.monitor.arn]

  subscriber {
    type    = "SNS"
    address = aws_sns_topic.alerts.arn
  }

  depends_on = [aws_sns_topic_policy.cost_anomaly_policy]
}
```
- **Impact**: Silent alert delivery failure — anomaly detection infrastructure exists but never delivers notifications
- **Severity**: HIGH
- **Source**: [CE Anomaly Subscription SNS Example](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_anomaly_subscription#sns-example)

---

#### Anti-Pattern: Budget Action with Overly Broad IAM Policy

```hcl
# DON'T — Budget action IAM policy with AdministratorAccess
resource "aws_iam_policy" "budget_action_policy" {
  name = "budget-enforcement-policy"
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = "*"         # DON'T — Full administrator access
      Resource = "*"
    }]
  })
}

resource "aws_budgets_budget_action" "bad_action" {
  budget_name        = aws_budgets_budget.budget.name
  action_type        = "APPLY_IAM_POLICY"
  approval_model     = "AUTOMATIC"
  notification_type  = "ACTUAL"
  execution_role_arn = aws_iam_role.budget_action.arn

  action_threshold {
    action_threshold_type  = "PERCENTAGE"
    action_threshold_value = 100
  }

  definition {
    iam_action_definition {
      policy_arn = aws_iam_policy.budget_action_policy.arn  # Admin policy applied on breach
      roles      = [aws_iam_role.app_role.name]
    }
  }
}
```

- **Why**: Applying an overly broad policy on budget breach can cause service disruptions beyond the intended cost control; IAM policy application via budget action is additive, not substitutive — the role retains all existing permissions
- **Instead**:
```hcl
# DO — Targeted deny policy for specific provisioning actions
data "aws_iam_policy_document" "budget_enforcement_deny" {
  statement {
    sid    = "DenyResourceProvisioning"
    effect = "Deny"
    actions = [
      "ec2:RunInstances",
      "ec2:CreateVolume",
      "rds:CreateDBInstance",
      "lambda:CreateFunction",
      "ecs:RunTask",
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }
}

resource "aws_iam_policy" "budget_enforcement_deny" {
  name        = "BudgetEnforcementDenyProvisioning"
  description = "Applied automatically when budget threshold is exceeded — denies new resource creation"
  policy      = data.aws_iam_policy_document.budget_enforcement_deny.json
}

resource "aws_budgets_budget_action" "good_action" {
  budget_name        = aws_budgets_budget.budget.name
  action_type        = "APPLY_IAM_POLICY"
  approval_model     = "MANUAL"  # Require approval before enforcement
  notification_type  = "ACTUAL"
  execution_role_arn = aws_iam_role.budget_action.arn

  action_threshold {
    action_threshold_type  = "PERCENTAGE"
    action_threshold_value = 110  # Higher threshold to prevent premature lockout
  }

  definition {
    iam_action_definition {
      policy_arn = aws_iam_policy.budget_enforcement_deny.arn
      roles      = [aws_iam_role.app_role.name]
    }
  }
}
```
- **Impact**: Unintended service disruption, privilege escalation risk, broad access lockout
- **Severity**: HIGH
- **Source**: [Budget Actions Docs](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html)

---

#### Anti-Pattern: Cost Allocation Tag Applied Outside Management Account

```hcl
# DON'T — Activating cost allocation tags from a member account
# This will fail silently or apply only to that account's unblended costs
# For organizations, MUST be applied from the management (payer) account

provider "aws" {
  region = "us-east-1"
  # Missing: assume_role to management account
}

resource "aws_ce_cost_allocation_tag" "environment" {
  tag_key = "Environment"
  status  = "Active"
  # Applied to member account — will NOT appear across org Cost Explorer
}
```

- **Why**: Cost allocation tags for AWS Organizations must be activated in the **management (payer) account**; activating in a member account only affects that account's individual view, not the consolidated billing view
- **Instead**:
```hcl
# DO — Use a dedicated management account provider alias
provider "aws" {
  alias  = "management"
  region = "us-east-1"

  assume_role {
    role_arn = "arn:aws:iam::${var.management_account_id}:role/CostManagementRole"
  }
}

resource "aws_ce_cost_allocation_tag" "environment" {
  provider = aws.management  # Explicitly target management account
  tag_key  = "Environment"
  status   = "Active"
}
```
- **Impact**: Cost allocation tags ineffective in consolidated billing view; FinOps attribution broken
- **Severity**: MEDIUM
- **Source**: [Cost Allocation Tags — Activating Tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)

---

#### Anti-Pattern: Mixing `cost_filter` and `filter_expression` on Same Budget

```hcl
# DON'T — These two approaches conflict and cause an apply-time error
resource "aws_budgets_budget" "conflicting" {
  name         = "bad-budget"
  budget_type  = "COST"
  limit_amount = "500"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {                         # DON'T — Conflicts with filter_expression
    name   = "Service"
    values = ["Amazon EC2"]
  }

  metrics = ["UnblendedCost"]           # DON'T — Conflicts with cost_types
  filter_expression {
    dimensions {
      key    = "SERVICE"
      values = ["Amazon EC2"]
    }
  }
}
```

- **Why**: `filter_expression` and `cost_filter` are mutually exclusive; `metrics` and `cost_types` are mutually exclusive; using both causes an apply-time API error
- **Instead**: Choose one approach — use `filter_expression` + `metrics` for new resources, `cost_filter` only for migrating legacy budgets
- **Impact**: Terraform apply failure, budget not created
- **Severity**: MEDIUM
- **Source**: [aws_budgets_budget Argument Reference](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget#argument-reference)

---

#### Anti-Pattern: No Budget Action Execution Role with Least Privilege

```hcl
# DON'T — Reuse application role as budget action execution role
resource "aws_budgets_budget_action" "bad" {
  budget_name        = aws_budgets_budget.budget.name
  action_type        = "APPLY_IAM_POLICY"
  approval_model     = "AUTOMATIC"
  notification_type  = "ACTUAL"
  execution_role_arn = aws_iam_role.app_role.arn  # DON'T — Application role, not dedicated

  # No trust policy for budgets.amazonaws.com
}
```

- **Why**: Budget action execution role must have a trust policy for `budgets.amazonaws.com`; using an application role creates privilege confusion and audit trail gaps; dedicated role enables specific CloudTrail tracking of enforcement actions
- **Instead**:
```hcl
# DO — Dedicated execution role with budgets.amazonaws.com trust
data "aws_partition" "current" {}

data "aws_iam_policy_document" "budget_action_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["budgets.${data.aws_partition.current.dns_suffix}"]
    }
  }
}

resource "aws_iam_role" "budget_action_execution" {
  name               = "${var.environment}-budget-action-execution"
  assume_role_policy = data.aws_iam_policy_document.budget_action_assume_role.json
  description        = "Execution role for AWS Budget automated actions"

  tags = {
    ManagedBy = "terraform"
    Purpose   = "budget-action-execution"
  }
}

# Grant only the minimum permissions needed for the specific action
resource "aws_iam_role_policy_attachment" "budget_action_execution" {
  role       = aws_iam_role.budget_action_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSBudgetsActionsWithAWSResourceControlAccess"
}
```
- **Impact**: Budget action apply failures, unclear audit trail, potential privilege escalation
- **Severity**: HIGH
- **Source**: [Budget Actions IAM Role](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html#budgets-controls-prereqs)

---

## State Management Deep Dive

### Local Development State
```hcl
# Use local state only for development/learning
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
- **Risk**: No sharing, no locking; Cost Management resources are global billing configuration — concurrent applies could create duplicate budgets
- **When**: Solo development, learning; never for shared teams

### Production Remote State (S3 + DynamoDB)
```hcl
# Bootstrap DynamoDB lock table (run once via separate state)
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

# Backend configuration for cost management module
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/cost-management/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### State Sensitivity for Cost Management
Cost Management Terraform state contains:
- SNS topic ARNs (low sensitivity)
- Budget notification email addresses (medium — PII)
- IAM role ARNs for budget action execution (medium — operational detail)
- Budget thresholds and account IDs (low-medium)

State does **not** contain billing data, usage metrics, or actual costs (those are AWS managed).

```hcl
# Mark sensitive outputs appropriately
output "cost_alerts_sns_arn" {
  value       = aws_sns_topic.cost_anomaly_updates.arn
  description = "SNS topic ARN for cost anomaly alerts"
  sensitive   = false  # ARNs are not secret, but limit sharing
}

output "budget_action_role_arn" {
  value       = aws_iam_role.budget_action_execution.arn
  description = "IAM role ARN for budget action execution"
  sensitive   = false
}
```

---

## Module Architecture

### Standard Module Structure
```
modules/
├── cost-management/
│   ├── main.tf           # Budgets, anomaly monitors, subscriptions
│   ├── variables.tf      # Budget limits, thresholds, notification targets
│   ├── outputs.tf        # SNS ARNs, budget ARNs for cross-module consumption
│   ├── versions.tf       # Provider version constraints
│   └── README.md
├── cost-allocation/
│   ├── main.tf           # Cost allocation tags, cost categories
│   ├── variables.tf      # Tag keys to activate, category rules
│   ├── outputs.tf        # Activated tag keys, category ARNs
│   ├── versions.tf
│   └── README.md
└── budget-enforcement/
    ├── main.tf           # Budget actions, IAM deny policies, execution roles
    ├── variables.tf      # Action thresholds, target roles, approval model
    ├── outputs.tf        # Action ARNs, enforcement role ARN
    ├── versions.tf
    └── README.md
```

### Module Definition Example
```hcl
# modules/cost-management/variables.tf
variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "monthly_budget_usd" {
  type        = string
  description = "Monthly cost budget limit in USD"

  validation {
    condition     = can(tonumber(var.monthly_budget_usd)) && tonumber(var.monthly_budget_usd) > 0
    error_message = "Monthly budget must be a positive number string."
  }
}

variable "alert_sns_topic_arn" {
  type        = string
  description = "SNS topic ARN for cost alert delivery"

  validation {
    condition     = can(regex("^arn:aws[a-z-]*:sns:[a-z0-9-]+:[0-9]{12}:.+$", var.alert_sns_topic_arn))
    error_message = "Must be a valid SNS topic ARN."
  }
}

variable "anomaly_absolute_threshold" {
  type        = number
  description = "Minimum absolute cost anomaly (USD) to trigger alert"
  default     = 100
}

variable "anomaly_percentage_threshold" {
  type        = number
  description = "Minimum anomaly percentage above baseline to trigger alert"
  default     = 20
}

# modules/cost-management/outputs.tf
output "budget_arn" {
  value       = aws_budgets_budget.monthly_cost.arn
  description = "ARN of the monthly cost budget"
}

output "anomaly_monitor_arn" {
  value       = aws_ce_anomaly_monitor.aws_services.arn
  description = "ARN of the AWS services anomaly monitor"
}

output "anomaly_subscription_arn" {
  value       = aws_ce_anomaly_subscription.realtime.arn
  description = "ARN of the realtime anomaly subscription"
}

# root/main.tf — Consuming the module
module "cost_management_prod" {
  source = "./modules/cost-management"

  environment          = "prod"
  monthly_budget_usd   = "5000.00"
  alert_sns_topic_arn  = module.notifications.cost_alerts_sns_arn

  anomaly_absolute_threshold   = 500
  anomaly_percentage_threshold = 25
}
```

---

## Integration Patterns: Terraform ↔ Integration Partners

### Integration: Terraform ↔ SNS

- **Pattern**: SNS as alert delivery bus for both budget notifications and anomaly detection
- **Resources**: `aws_sns_topic`, `aws_sns_topic_policy`, `aws_sns_topic_subscription`
- **Data Sources**: `data.aws_iam_policy_document`
- **Example**:
```hcl
resource "aws_sns_topic" "cost_alerts" {
  name              = "${var.environment}-cost-alerts"
  kms_master_key_id = "alias/aws/sns"  # Use KMS for sensitive notifications

  tags = {
    Name        = "${var.environment}-cost-alerts"
    Environment = var.environment
    Purpose     = "cost-management-alerts"
  }
}

# Allow cost anomaly detection AND budget service to publish
data "aws_iam_policy_document" "cost_sns_policy" {
  statement {
    sid     = "AllowCostServicesPublish"
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type = "Service"
      identifiers = [
        "costalerts.amazonaws.com",   # Cost Anomaly Detection
        "budgets.amazonaws.com",       # AWS Budgets (for SNS subscriber notifications)
      ]
    }

    resources = [aws_sns_topic.cost_alerts.arn]
  }
}

resource "aws_sns_topic_policy" "cost_alerts" {
  arn    = aws_sns_topic.cost_alerts.arn
  policy = data.aws_iam_policy_document.cost_sns_policy.json
}
```
- **Issues**: SNS must be in the same region as the budget subscription; Cost Anomaly Detection uses `costalerts.amazonaws.com` (not `budgets.amazonaws.com`); missing service principal = silent delivery failure
- **Versions**:
  | Resource | Min Provider | Max Provider |
  |----------|-------------|-------------|
  | `aws_sns_topic` | 4.0 | 6.x |
  | `aws_sns_topic_policy` | 4.0 | 6.x |
- **Source**: [SNS Topic Policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_policy)

---

### Integration: Terraform ↔ IAM

- **Pattern**: IAM provides execution roles for budget actions and least-privilege access for Cost Explorer API calls
- **Resources**: `aws_iam_role`, `aws_iam_policy`, `aws_iam_role_policy_attachment`, `data.aws_iam_policy_document`
- **Example**:
```hcl
# IAM role for budget action execution
data "aws_partition" "current" {}

data "aws_iam_policy_document" "budget_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["budgets.${data.aws_partition.current.dns_suffix}"]
    }
  }
}

resource "aws_iam_role" "budget_action_execution" {
  name               = "${var.environment}-budget-action-role"
  assume_role_policy = data.aws_iam_policy_document.budget_trust.json
}

# Deny policy applied when budget threshold is breached
data "aws_iam_policy_document" "provisioning_deny" {
  statement {
    sid    = "DenyNewResourceProvisioning"
    effect = "Deny"
    actions = [
      "ec2:RunInstances",
      "ec2:CreateVolume",
      "rds:CreateDBInstance",
      "ecs:RunTask",
      "lambda:CreateFunction",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "provisioning_deny" {
  name   = "${var.environment}-budget-enforcement-deny"
  policy = data.aws_iam_policy_document.provisioning_deny.json
}

resource "aws_iam_role_policy_attachment" "budget_action_execution" {
  role       = aws_iam_role.budget_action_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSBudgetsActionsWithAWSResourceControlAccess"
}

resource "aws_budgets_budget_action" "enforcement" {
  budget_name        = aws_budgets_budget.monthly_cost.name
  action_type        = "APPLY_IAM_POLICY"
  approval_model     = "AUTOMATIC"
  notification_type  = "ACTUAL"
  execution_role_arn = aws_iam_role.budget_action_execution.arn

  action_threshold {
    action_threshold_type  = "PERCENTAGE"
    action_threshold_value = 110
  }

  definition {
    iam_action_definition {
      policy_arn = aws_iam_policy.provisioning_deny.arn
      roles      = var.target_role_names
    }
  }

  subscriber {
    address           = var.ops_email
    subscription_type = "EMAIL"
  }
}
```
- **Issues**: Budget action IAM policy is applied additively; roles/users/groups retain all existing permissions; actions fire once per threshold breach per period — they do not continuously re-enforce
- **Source**: [aws_budgets_budget_action IAM Definition](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget_action#iam-action-definition)

---

### Integration: Terraform ↔ Organizations (Multi-Account)

- **Pattern**: Management account deploys budgets and anomaly monitors for linked accounts; SCP actions require management account deployment
- **Resources**: `aws_budgets_budget` (with `account_id`), `aws_ce_anomaly_monitor` (LINKED_ACCOUNT dimension), `aws_budgets_budget_action` (SCP definition)
- **Data Sources**: `data.aws_organizations_organization`, `data.aws_organizations_organizational_units`
- **Example**:
```hcl
# Deploy per-account budgets from management account
data "aws_organizations_organization" "current" {}

# Linked account anomaly monitor (management account only)
resource "aws_ce_anomaly_monitor" "linked_accounts" {
  name              = "linked-account-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "LINKED_ACCOUNT"  # Tracks all member accounts
}

# Per-environment budget for a specific member account
resource "aws_budgets_budget" "member_account_budget" {
  for_each = var.member_account_ids

  account_id   = each.value
  name         = "${each.key}-monthly-budget"
  budget_type  = "COST"
  limit_amount = var.account_budget_limits[each.key]
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_alerts.arn]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_alerts.arn]
  }
}
```
- **Issues**: `LINKED_ACCOUNT` and `TAG` monitors can only be created from the management account; SCP budget actions only work from management account; `account_id` on `aws_budgets_budget` creates the budget in that account but requires cross-account permissions
- **Source**: [Budgets Multi-Account](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)

---

### Integration: Terraform ↔ CloudWatch

- **Pattern**: CloudWatch Alarms complement budget notifications with real-time metric-based alerting for specific service costs exposed via billing metrics
- **Resources**: `aws_cloudwatch_metric_alarm`
- **Example**:
```hcl
# CloudWatch billing alarm (requires enabling billing alerts in account settings)
# Note: Billing metrics are only available in us-east-1
resource "aws_cloudwatch_metric_alarm" "estimated_charges" {
  provider = aws.us_east_1  # Billing metrics only in us-east-1

  alarm_name          = "${var.environment}-estimated-charges"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = "86400"  # 24 hours (billing metrics updated daily)
  statistic           = "Maximum"
  threshold           = var.cloudwatch_billing_threshold
  alarm_description   = "Estimated monthly charges exceeded threshold"
  alarm_actions       = [aws_sns_topic.cost_alerts.arn]

  dimensions = {
    Currency = "USD"
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```
- **Issues**: `AWS/Billing` metrics are only available in `us-east-1`; metrics update every ~8 hours (not real-time); billing alerts must be enabled in account preferences before metrics appear; CloudWatch billing alarms complement (not replace) AWS Budgets — Budgets is more capable for cost governance
- **Source**: [CloudWatch Billing Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/monitor_estimated_charges_with_cloudwatch.html)

---

## Quality Control

### Verification Commands

```bash
# Format validation
terraform fmt -recursive -check=true
# Expected: Exit code 0, no formatting errors

# Syntax validation
terraform validate
# Expected: "Success! The configuration is valid."

# Security scanning — check for missing encryption, public resources
tfsec . --format compact
# Expected: No HIGH or CRITICAL findings

# Policy-as-code validation
checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks

# Plan — verify budget resources to create
terraform plan -out=tfplan -lock=true
# Expected: Plan output showing aws_budgets_budget, aws_ce_anomaly_monitor, etc.

terraform show tfplan | grep -E "(resource|aws_budgets|aws_ce_)"
# Expected: All cost management resources listed as additions

# State validation after apply
terraform state list | grep -E "(budgets|ce_)"
# Expected:
#   aws_budgets_budget.monthly_cost
#   aws_ce_anomaly_monitor.aws_services
#   aws_ce_anomaly_subscription.realtime
#   aws_ce_cost_allocation_tag.environment

# Verify budget was created in AWS
terraform output budget_arn
aws budgets describe-budget --account-id $(terraform output -raw account_id) \
  --budget-name $(terraform output -raw budget_name)
# Expected: Budget details with limit and notification configuration

# Verify anomaly monitor
terraform output anomaly_monitor_arn
# Expected: ARN like arn:aws:ce::123456789012:anomalymonitor/...
```

### Testing with Terratest
```go
package test

import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/stretchr/testify/assert"
)

func TestCostManagementDeployment(t *testing.T) {
  opts := &terraform.Options{
    TerraformDir: "../examples/cost-management",
    Vars: map[string]interface{}{
      "environment":         "test",
      "monthly_budget_usd":  "100.00",
      "billing_alert_emails": []string{"test@example.com"},
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  budgetArn := terraform.Output(t, opts, "budget_arn")
  assert.Contains(t, budgetArn, "arn:aws:budgets")

  monitorArn := terraform.Output(t, opts, "anomaly_monitor_arn")
  assert.Contains(t, monitorArn, "arn:aws:ce")

  subscriptionArn := terraform.Output(t, opts, "anomaly_subscription_arn")
  assert.Contains(t, subscriptionArn, "arn:aws:ce")
}
```

---

## Production Readiness

### API Limits and Quotas
- **AWS Budgets**: Maximum 20,000 budgets per account (AWS managed); maximum 5 email subscribers per notification; maximum 10 SNS topics per notification
- **Budget Actions**: Maximum 10 actions per budget
- **Cost Anomaly Monitors**: Maximum 500 monitors per account (customer managed); AWS managed monitors are unlimited by dimension
- **Cost Allocation Tags**: Maximum 500 user-defined activated tags per account; tag activation takes up to 24 hours to appear
- **Cost Categories**: Maximum 50 categories, 500 rules each; split charge rules up to 10 per category

### Cost of Cost Management Services
- **AWS Budgets**: First 2 budgets free; $0.01/day per additional budget; budget actions: $0.10/day per action
- **Cost Anomaly Detection**: Free
- **Cost Explorer API**: $0.01 per API request (monitor and subscription management via console is free)
- **Cost Allocation Tags**: Free

### Monitoring & Alerting
```hcl
# CloudWatch alarm for SNS topic delivery failures
resource "aws_cloudwatch_metric_alarm" "sns_delivery_failures" {
  alarm_name          = "${var.environment}-cost-sns-delivery-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "NumberOfNotificationsFailed"
  namespace           = "AWS/SNS"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Cost alert SNS topic delivery failures detected"
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    TopicName = aws_sns_topic.cost_alerts.name
  }
}
```

### Security Checklist
- [ ] Budget notification SNS topics encrypted with KMS (`kms_master_key_id`)
- [ ] Budget action execution role scoped to `budgets.amazonaws.com` trust only
- [ ] Budget action IAM deny policies scoped to specific actions (no `*` actions)
- [ ] State file encryption enabled (`encrypt = true` in S3 backend)
- [ ] Cost allocation tag activation from management account only
- [ ] Anomaly subscription SNS topic policy includes `costalerts.amazonaws.com` principal
- [ ] Budget action thresholds set conservatively (≥110% for AUTOMATIC enforcement)
- [ ] All cost management resources tagged for ownership tracking
- [ ] CloudWatch billing alerts enabled in account preferences

### Disaster Recovery Runbook
```bash
# 1. State corruption recovery for cost management
aws s3api list-object-versions \
  --bucket my-org-terraform-state \
  --prefix prod/cost-management/terraform.tfstate \
  --query 'Versions[*].{VersionId:VersionId,LastModified:LastModified}'

aws s3api get-object \
  --bucket my-org-terraform-state \
  --key prod/cost-management/terraform.tfstate \
  --version-id <VERSION_ID> \
  terraform.tfstate.backup

# 2. Import existing budget after state corruption
terraform import aws_budgets_budget.monthly_cost "123456789012:prod-monthly-cost-budget"

# 3. Import anomaly monitor (use ARN as ID)
terraform import aws_ce_anomaly_monitor.aws_services \
  "arn:aws:ce::123456789012:anomalymonitor/abc123"

# 4. Import anomaly subscription
terraform import aws_ce_anomaly_subscription.realtime \
  "arn:aws:ce::123456789012:anomalysubscription/xyz456"

# 5. Import cost allocation tag (key as ID)
terraform import aws_ce_cost_allocation_tag.environment "Environment"

# 6. Import budget action
terraform import aws_budgets_budget_action.enforcement \
  "123456789012:action-id:prod-monthly-cost-budget"

# 7. Verify state reconciliation
terraform plan
# Expected: No changes (state matches infrastructure)
```

---

## Reference Root Module Example

```hcl
# root/main.tf — Complete cost management stack
# Usage: terraform apply -var-file=prod.tfvars

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
    key            = "prod/cost-management/terraform.tfstate"
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
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}

# SNS topic for all cost alerts
resource "aws_sns_topic" "cost_alerts" {
  name              = "${var.environment}-cost-alerts"
  kms_master_key_id = "alias/aws/sns"
}

data "aws_iam_policy_document" "cost_alerts_policy" {
  statement {
    sid     = "AllowCostServicesPublish"
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type        = "Service"
      identifiers = ["costalerts.amazonaws.com", "budgets.amazonaws.com"]
    }

    resources = [aws_sns_topic.cost_alerts.arn]
  }
}

resource "aws_sns_topic_policy" "cost_alerts" {
  arn    = aws_sns_topic.cost_alerts.arn
  policy = data.aws_iam_policy_document.cost_alerts_policy.json
}

# Monthly cost budget
resource "aws_budgets_budget" "monthly_cost" {
  name         = "${var.environment}-monthly-cost"
  budget_type  = "COST"
  limit_amount = var.monthly_budget_usd
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_sns_topic_arns = [aws_sns_topic.cost_alerts.arn]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_alerts.arn]
    subscriber_email_addresses = var.billing_alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_alerts.arn]
    subscriber_email_addresses = var.billing_alert_emails
  }
}

# Anomaly detection
resource "aws_ce_anomaly_monitor" "aws_services" {
  name              = "${var.environment}-aws-services-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}

resource "aws_ce_anomaly_subscription" "realtime" {
  name      = "${var.environment}-realtime-anomaly-sub"
  frequency = "IMMEDIATE"

  monitor_arn_list = [aws_ce_anomaly_monitor.aws_services.arn]

  subscriber {
    type    = "SNS"
    address = aws_sns_topic.cost_alerts.arn
  }

  threshold_expression {
    and {
      dimension {
        key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
        match_options = ["GREATER_THAN_OR_EQUAL"]
        values        = [tostring(var.anomaly_absolute_threshold)]
      }
    }
    and {
      dimension {
        key           = "ANOMALY_TOTAL_IMPACT_PERCENTAGE"
        match_options = ["GREATER_THAN_OR_EQUAL"]
        values        = [tostring(var.anomaly_percentage_threshold)]
      }
    }
  }

  depends_on = [aws_sns_topic_policy.cost_alerts]
}

# Cost allocation tag activation
resource "aws_ce_cost_allocation_tag" "environment" {
  tag_key = "Environment"
  status  = "Active"
}

resource "aws_ce_cost_allocation_tag" "team" {
  tag_key = "Team"
  status  = "Active"
}

resource "aws_ce_cost_allocation_tag" "cost_center" {
  tag_key = "CostCenter"
  status  = "Active"
}

# Outputs
output "budget_arn" {
  value       = aws_budgets_budget.monthly_cost.arn
  description = "ARN of the monthly cost budget"
}

output "anomaly_monitor_arn" {
  value       = aws_ce_anomaly_monitor.aws_services.arn
  description = "ARN of the anomaly monitor"
}

output "anomaly_subscription_arn" {
  value       = aws_ce_anomaly_subscription.realtime.arn
  description = "ARN of the anomaly subscription"
}

output "cost_alerts_sns_arn" {
  value       = aws_sns_topic.cost_alerts.arn
  description = "SNS topic ARN for cost alerts"
}
```

```hcl
# root/variables.tf
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Account ID must be 12 digits."
  }
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "owner"       { type = string }
variable "cost_center" { type = string }

variable "monthly_budget_usd" {
  type = string
  validation {
    condition     = can(tonumber(var.monthly_budget_usd)) && tonumber(var.monthly_budget_usd) > 0
    error_message = "Monthly budget must be a positive number string."
  }
}

variable "billing_alert_emails" {
  type    = list(string)
  default = []
}

variable "anomaly_absolute_threshold" {
  type    = number
  default = 100
}

variable "anomaly_percentage_threshold" {
  type    = number
  default = 20
}
```

```hcl
# prod.tfvars
aws_region          = "us-east-1"
account_id          = "123456789012"
environment         = "prod"
owner               = "platform-team"
cost_center         = "engineering"
monthly_budget_usd  = "5000.00"
billing_alert_emails = ["finops@company.com", "cto@company.com"]
anomaly_absolute_threshold   = 500
anomaly_percentage_threshold = 25
```

---

## Reference Implementations

- [Terraform AWS Provider — Budgets](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget)
- [Terraform AWS Provider — Budget Actions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget_action)
- [Terraform AWS Provider — CE Anomaly Monitor](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_anomaly_monitor)
- [Terraform AWS Provider — CE Anomaly Subscription](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_anomaly_subscription)
- [Terraform AWS Provider — CE Cost Allocation Tag](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_allocation_tag)
- [Terraform AWS Provider — CE Cost Category](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_category)
- [AWS Cost Management Best Practices](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html)
- [AWS Budgets Actions Prerequisites](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html#budgets-controls-prereqs)

---

## Source Bibliography

### Primary Sources
- [Terraform AWS Provider Registry v6.47.0](https://registry.terraform.io/providers/hashicorp/aws/latest) — Published 2026-05-28
- [aws_budgets_budget Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget)
- [aws_budgets_budget_action Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/budgets_budget_action)
- [aws_ce_anomaly_monitor Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_anomaly_monitor)
- [aws_ce_anomaly_subscription Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_anomaly_subscription)
- [aws_ce_cost_allocation_tag Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_allocation_tag)
- [aws_ce_cost_category Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_category)
- [AWS Cost Management User Guide](https://docs.aws.amazon.com/cost-management/latest/userguide/what-is-costmanagement.html)
- [AWS Budgets Controls (Budget Actions)](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html)
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)

### Validation & Tools
- [tfsec](https://github.com/aquasecurity/tfsec) — Security scanner
- [Checkov](https://www.checkov.io/) — Policy-as-code validator
- [Terratest](https://terratest.gruntwork.io/) — Testing framework
- [hashicorp/terraform-provider-aws Issues](https://github.com/hashicorp/terraform-provider-aws/issues)

---

## Completion Checklist
- [x] All Terraform 1.9 and aws ~> 6.0 patterns validated
- [x] Code examples for every mandatory pattern
- [x] State management strategy documented
- [x] Module architecture fully defined
- [x] Every anti-pattern has tested alternative
- [x] CLI commands include expected outputs
- [x] SNS, IAM, Organizations, CloudWatch integration examples complete
- [x] Sources dated and linked to registry (2026-05-28 provider release confirmed)
- [x] Security checklist complete
- [x] Copy-paste working root module with `.tfvars` example
- [x] Disaster recovery import procedures documented

---

## Research Gaps

```
Gap: aws_costoptimizationhub_enrollment_status resource
Impact: Cannot manage Cost Optimization Hub enrollment via Terraform
Workaround: Enable via AWS Console or AWS CLI (aws cost-optimization-hub update-enrollment-status)
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs — search "costoptimizationhub"

Gap: BCM Data Exports (aws_bcm_data_exports_export) — CUR v2 replacement
Impact: Modern CUR exports may need manual configuration; bcm_data_exports resources may have
        limited coverage in current provider version
Workaround: Use aws_cur_report_definition (legacy CUR) or configure via Console
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/bcm_data_exports_export

Gap: Cost Anomaly Detection monitor dimension "COST_CATEGORY" requires existing cost categories
Impact: Creating a COST_CATEGORY monitor before the cost category exists causes apply failure
Workaround: Use depends_on = [aws_ce_cost_category.main] to ensure ordering
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Monthly cost budget creation with ACTUAL + FORECASTED notifications
- Cost Anomaly Monitor (DIMENSIONAL / SERVICE) deployment
- Cost allocation tag activation for standard tags (Environment, Team, CostCenter)
- SNS topic policy with `costalerts.amazonaws.com` principal
- Terraform state setup with S3 backend + DynamoDB locking
- Variable validation patterns for budget amounts and email addresses

### Medium Confidence (Validate with user)
- Budget action approval model (AUTOMATIC vs MANUAL)
- Anomaly threshold values (absolute dollar amount, percentage)
- Multi-account deployment targeting specific member account IDs
- Cost category rule definitions (complex matching logic)
- Budget auto-adjust vs static limit selection

### Low Confidence (Must ask user)
- SCP-based budget actions (requires Organizations management account permission)
- Custom anomaly monitor JSON expressions (domain-specific filter logic)
- BCM Data Exports (CUR v2) configuration (evolving resource support)
- Cross-account cost allocation tag strategies in complex org hierarchies

### Edge Cases (When to pause)
- Budget action threshold triggers unexpectedly and locks out application roles
- Cost allocation tag applied from wrong account level (member vs management)
- Anomaly subscription SNS delivery silently fails (missing service principal in policy)
- `filter_expression` and `cost_filter` both specified on same budget resource (apply error)
- Budget action EC2/RDS stop targeting resources in ASGs (ASG will restart — action ineffective alone)

### Emergency Stop
- Halt if budget action with AUTOMATIC approval and very low threshold (≤100%) targets production IAM roles
- Halt if cost allocation tag activation attempted from member account without management account provider alias
- Halt if anomaly subscription `depends_on` is missing — silent delivery failure guaranteed
