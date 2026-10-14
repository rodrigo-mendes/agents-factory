# Terraform AWS Organization — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - Organizations (Multi-Account Management)"
Cloud_Provider: "AWS"
Target_Service: "Organizations (Multi-Account Management)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-29"
Domain_Complexity: "Complex"
Primary_Resources:
  - aws_organizations_organization
  - aws_organizations_account
  - aws_organizations_organizational_unit
  - aws_organizations_policy
  - aws_organizations_policy_attachment
  - aws_organizations_delegated_administrator
  - aws_organizations_resource_policy
Primary_Data_Sources:
  - data.aws_organizations_organization
  - data.aws_organizations_organizational_unit
  - data.aws_organizations_organizational_units
New_V6_Policy_Types: "BEDROCK_POLICY, CHATBOT_POLICY, INSPECTOR_POLICY, RESOURCE_CONTROL_POLICY (RCP), SECURITYHUB_POLICY, UPGRADE_ROLLOUT_POLICY"
```

---

## Executive Summary

AWS Organizations is the foundational governance layer for managing multiple AWS accounts as a single entity. Terraform manages the full Organizations lifecycle through a tightly ordered dependency chain: `aws_organizations_organization` (root creation) → `aws_organizations_organizational_unit` (OU hierarchy) → `aws_organizations_account` (member accounts placed in OUs) → `aws_organizations_policy` (SCP/RCP/Tag definitions) → `aws_organizations_policy_attachment` (policy-to-target binding) → `aws_organizations_delegated_administrator` (service delegation). All resources must be created from the management account — Terraform has no mechanism to switch mid-run to a member account context for org-level operations.

The AWS Provider v6.x expanded `enabled_policy_types` to include `RESOURCE_CONTROL_POLICY` (RCP), `BEDROCK_POLICY`, `CHATBOT_POLICY`, `INSPECTOR_POLICY`, `SECURITYHUB_POLICY`, and `UPGRADE_ROLLOUT_POLICY` in addition to the existing `SERVICE_CONTROL_POLICY`, `TAG_POLICY`, `AISERVICES_OPT_OUT_POLICY`, `BACKUP_POLICY`, `DECLARATIVE_POLICY_EC2`, and `S3_POLICY`. The `aws_organizations_policy` resource `type` argument now accepts all these types. The `status` attribute on `aws_organizations_account` is deprecated in favor of `state`. The `aws_organizations_organization` `return_organization_only` argument is available to avoid API throttling in large organizations.

The three non-negotiable guardrails: **(1) `feature_set = "ALL"` is mandatory for any governance use case** — `CONSOLIDATED_BILLING` only disables SCPs, RCPs, Tag Policies, and all service integrations; **(2) the management account must never host workloads** — it is exempt from SCPs (but not RCPs or declarative policies) and its compromise grants control over the entire organization; **(3) every `aws_organizations_policy` of type `SERVICE_CONTROL_POLICY` must be attached to an OU, not individual accounts** — attaching to individual accounts breaks inheritance-based governance and scales poorly. This service is classified **Complex** due to irreversible account creation operations, cross-account IAM trust dependency chains, policy evaluation logic spanning principal-side (SCP) and resource-side (RCP) authorization layers, delegated administration patterns, and compliance obligations affecting every member account.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Pins to Terraform >=1.7 for `terraform test` support and `import` block identity schema. Provider `~> 6.0` enables all policy types including RCP. S3 backend with DynamoDB locking is mandatory — Organizations state contains account IDs, OU IDs, and policy ARNs that dozens of downstream stacks consume via remote state.

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
    key            = "org/management/terraform.tfstate"
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

#### Pattern: Provider Configuration for Management Account

**Why**: Organizations operations must be performed from the management account. Using `assume_role` with a dedicated Terraform role in the management account is the only safe pattern — it avoids using the root user, creates an audit trail in CloudTrail, and works with CI/CD pipelines. `default_tags` enforces tagging on accounts and policies for cost allocation.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.management_account_id}:role/TerraformOrganizationsRole"
    session_name = "TerraformOrganizationsSession"
  }

  default_tags {
    tags = {
      Environment = "management"
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [AWS Provider Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration)

---

#### Pattern: Organization Resource with All Features Enabled

**Why**: `feature_set = "ALL"` is required to use SCPs, RCPs, Tag Policies, Backup Policies, and any AWS service integration. `CONSOLIDATED_BILLING` disables all governance controls. Enabling service access principals via `aws_service_access_principals` is required for CloudTrail, Config, IAM Access Analyzer, and other org-wide services — without it, delegated administrators cannot operate. `enabled_policy_types` must explicitly list every policy type you intend to use before attaching policies of that type.

```hcl
resource "aws_organizations_organization" "this" {
  feature_set = "ALL"

  aws_service_access_principals = [
    "cloudtrail.amazonaws.com",
    "config.amazonaws.com",
    "sso.amazonaws.com",
    "guardduty.amazonaws.com",
    "securityhub.amazonaws.com",
    "access-analyzer.amazonaws.com",
    "backup.amazonaws.com",
    "tagpolicies.tag.amazonaws.com",
  ]

  enabled_policy_types = [
    "SERVICE_CONTROL_POLICY",
    "TAG_POLICY",
    "BACKUP_POLICY",
    "RESOURCE_CONTROL_POLICY",
  ]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_organizations_organization](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_organization)

---

#### Pattern: OU Hierarchy with Explicit Parent Dependency

**Why**: OUs are the governance boundary for policy inheritance. Every `aws_organizations_organizational_unit` must explicitly reference `parent_id` to build a correct hierarchy. Using `aws_organizations_organization.this.roots[0].id` for top-level OUs ensures the organization exists before the OU is created. Terraform does not infer cross-resource ordering for Organizations resources — `depends_on` is often required.

```hcl
# Top-level OUs
resource "aws_organizations_organizational_unit" "security" {
  name      = "Security"
  parent_id = aws_organizations_organization.this.roots[0].id

  tags = {
    Purpose = "security-tooling"
  }
}

resource "aws_organizations_organizational_unit" "workloads" {
  name      = "Workloads"
  parent_id = aws_organizations_organization.this.roots[0].id
}

resource "aws_organizations_organizational_unit" "sandbox" {
  name      = "Sandbox"
  parent_id = aws_organizations_organization.this.roots[0].id
}

# Nested OUs under Workloads
resource "aws_organizations_organizational_unit" "workloads_prod" {
  name      = "Production"
  parent_id = aws_organizations_organizational_unit.workloads.id
}

resource "aws_organizations_organizational_unit" "workloads_nonprod" {
  name      = "NonProduction"
  parent_id = aws_organizations_organizational_unit.workloads.id
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_organizations_organizational_unit](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_organizational_unit)

---

#### Pattern: Member Account with Placement in OU

**Why**: `parent_id` is the mechanism that places an account into an OU and determines which SCPs apply to it. Without explicit `parent_id`, accounts default to the organization root — meaning they inherit root-level policies only. `role_name` specifies the cross-account IAM role that Terraform (and administrators) will use to access the account — this role is created automatically by Organizations. `close_on_deletion` prevents accidental account closure during development; only set `true` when you explicitly want account closure (quota-constrained, irreversible).

```hcl
resource "aws_organizations_account" "log_archive" {
  name      = "log-archive"
  email     = var.log_archive_email
  parent_id = aws_organizations_organizational_unit.security.id
  role_name = "OrganizationAccountAccessRole"

  tags = {
    AccountType = "security"
    Purpose     = "centralized-logging"
  }

  # role_name is unreadable after creation; suppress perpetual diff on import
  lifecycle {
    ignore_changes = [role_name]
  }
}

resource "aws_organizations_account" "security_tooling" {
  name      = "security-tooling"
  email     = var.security_tooling_email
  parent_id = aws_organizations_organizational_unit.security.id
  role_name = "OrganizationAccountAccessRole"

  tags = {
    AccountType = "security"
    Purpose     = "guardrails-and-detection"
  }

  lifecycle {
    ignore_changes = [role_name]
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_organizations_account](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_account)

---

#### Pattern: SCP with Deny Strategy Using IAM Policy Document

**Why**: SCPs must be deny-based guardrails for security controls — not allow-based permissions (allow-based SCPs are redundant with the default `FullAWSAccess`). Using `data.aws_iam_policy_document` instead of a JSON heredoc enables Terraform-native validation, syntax checking, and variable interpolation. `skip_destroy = true` prevents the last attached SCP from being removed, which would violate the AWS minimum-1-SCP requirement.

```hcl
data "aws_iam_policy_document" "deny_non_approved_regions" {
  statement {
    sid    = "DenyNonApprovedRegions"
    effect = "Deny"

    not_actions = [
      "a4b:*",
      "acm:*",
      "aws-marketplace-management:*",
      "aws-marketplace:*",
      "budgets:*",
      "ce:*",
      "chime:*",
      "cloudfront:*",
      "config:*",
      "cur:*",
      "directconnect:*",
      "ec2:DescribeRegions",
      "globalaccelerator:*",
      "health:*",
      "iam:*",
      "importexport:*",
      "kms:*",
      "mobileanalytics:*",
      "organizations:*",
      "route53:*",
      "route53domains:*",
      "s3:GetBucketLocation",
      "s3:ListAllMyBuckets",
      "shield:*",
      "sts:*",
      "support:*",
      "trustedadvisor:*",
      "waf-regional:*",
      "waf:*",
      "wafv2:*",
      "wellarchitected:*",
    ]

    resources = ["*"]

    condition {
      test     = "StringNotEquals"
      variable = "aws:RequestedRegion"
      values   = var.approved_regions
    }
  }
}

resource "aws_organizations_policy" "deny_non_approved_regions" {
  name        = "DenyNonApprovedRegions"
  description = "Prevents use of AWS regions not in the approved list"
  content     = data.aws_iam_policy_document.deny_non_approved_regions.json
  type        = "SERVICE_CONTROL_POLICY"

  skip_destroy = true

  tags = {
    PolicyType  = "security-guardrail"
    ManagedBy   = "terraform"
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_organizations_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_policy)

---

#### Pattern: Policy Attachment to OU (Not Individual Accounts)

**Why**: Attaching SCPs to OUs enforces inheritance — all current and future accounts placed in the OU automatically receive the policy. Attaching to individual accounts is brittle, does not scale, and creates governance gaps when new accounts are added. `skip_destroy = true` prevents Terraform from leaving an OU with zero SCPs (AWS requires minimum one SCP attached at all times when SCPs are enabled).

```hcl
resource "aws_organizations_policy_attachment" "deny_regions_workloads" {
  policy_id = aws_organizations_policy.deny_non_approved_regions.id
  target_id = aws_organizations_organizational_unit.workloads.id

  skip_destroy = true
}

resource "aws_organizations_policy_attachment" "deny_regions_sandbox" {
  policy_id = aws_organizations_policy.deny_non_approved_regions.id
  target_id = aws_organizations_organizational_unit.sandbox.id

  skip_destroy = true
}

# Attach deny-disable-security-services SCP to root for org-wide enforcement
resource "aws_organizations_policy_attachment" "deny_disable_security_root" {
  policy_id = aws_organizations_policy.deny_disable_security_services.id
  target_id = aws_organizations_organization.this.roots[0].id

  skip_destroy = true
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_organizations_policy_attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_policy_attachment)

---

#### Pattern: Delegated Administrator for Security Services

**Why**: The management account must be used as little as possible. Registering delegated administrators allows security accounts to manage GuardDuty, Security Hub, and Config for the entire organization without requiring management account access for day-to-day operations. The service principal must match exactly — incorrect principals silently fail in some cases.

```hcl
resource "aws_organizations_delegated_administrator" "guardduty" {
  account_id        = aws_organizations_account.security_tooling.id
  service_principal = "guardduty.amazonaws.com"

  depends_on = [aws_organizations_organization.this]
}

resource "aws_organizations_delegated_administrator" "securityhub" {
  account_id        = aws_organizations_account.security_tooling.id
  service_principal = "securityhub.amazonaws.com"

  depends_on = [aws_organizations_organization.this]
}

resource "aws_organizations_delegated_administrator" "config" {
  account_id        = aws_organizations_account.security_tooling.id
  service_principal = "config.amazonaws.com"

  depends_on = [aws_organizations_organization.this]
}

resource "aws_organizations_delegated_administrator" "access_analyzer" {
  account_id        = aws_organizations_account.security_tooling.id
  service_principal = "access-analyzer.amazonaws.com"

  depends_on = [aws_organizations_organization.this]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_organizations_delegated_administrator](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_delegated_administrator)

---

#### Pattern: Variable Validation and Type Safety

**Why**: Incorrect `feature_set`, invalid email addresses, or invalid region lists applied to Organizations resources create irreversible configurations (accounts cannot be deleted, SCPs cannot be reverted once applied at root). Validation at plan time prevents irreversible mistakes.

```hcl
variable "feature_set" {
  type        = string
  description = "AWS Organizations feature set. Must be ALL for governance use cases."
  default     = "ALL"

  validation {
    condition     = contains(["ALL", "CONSOLIDATED_BILLING"], var.feature_set)
    error_message = "feature_set must be 'ALL' (recommended) or 'CONSOLIDATED_BILLING'."
  }
}

variable "approved_regions" {
  type        = list(string)
  description = "List of AWS regions approved for use across the organization."
  default     = ["us-east-1", "us-west-2"]

  validation {
    condition     = length(var.approved_regions) >= 1
    error_message = "At least one approved region must be specified."
  }
}

variable "management_account_id" {
  type        = string
  description = "AWS account ID of the organization management account."

  validation {
    condition     = can(regex("^[0-9]{12}$", var.management_account_id))
    error_message = "management_account_id must be a 12-digit AWS account ID."
  }
}

variable "log_archive_email" {
  type        = string
  description = "Email address for the log archive account owner. Must be unique across all AWS accounts."
  sensitive   = true

  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}$", var.log_archive_email))
    error_message = "log_archive_email must be a valid email address."
  }
}
```

- **Terraform Version**: >= 1.7
- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

#### Pattern: Outputs for Cross-Stack Consumption

**Why**: Organizations state is the foundational dependency for dozens of downstream stacks. Account IDs, OU IDs, organization ID, and root ID must all be exported as outputs and consumed via `terraform_remote_state` or SSM Parameter Store. Marking account emails as `sensitive` prevents them from appearing in CI/CD logs.

```hcl
output "organization_id" {
  value       = aws_organizations_organization.this.id
  description = "AWS Organizations organization ID (o-xxxxxxxxxx)"
}

output "organization_root_id" {
  value       = aws_organizations_organization.this.roots[0].id
  description = "AWS Organizations root ID (r-xxxx)"
}

output "management_account_id" {
  value       = aws_organizations_organization.this.master_account_id
  description = "Management account ID"
}

output "ou_ids" {
  value = {
    security     = aws_organizations_organizational_unit.security.id
    workloads    = aws_organizations_organizational_unit.workloads.id
    prod         = aws_organizations_organizational_unit.workloads_prod.id
    nonprod      = aws_organizations_organizational_unit.workloads_nonprod.id
    sandbox      = aws_organizations_organizational_unit.sandbox.id
  }
  description = "Map of OU names to OU IDs for use in downstream stacks"
}

output "account_ids" {
  value = {
    log_archive      = aws_organizations_account.log_archive.id
    security_tooling = aws_organizations_account.security_tooling.id
  }
  description = "Map of account names to account IDs"
}

output "scp_ids" {
  value = {
    deny_non_approved_regions = aws_organizations_policy.deny_non_approved_regions.id
  }
  description = "Map of SCP names to policy IDs"
}
```

- **Terraform Version**: >= 1.7
- **Source**: [Output Values](https://developer.hashicorp.com/terraform/language/values/outputs)

---

### ⚠️ Conditional Patterns

---

#### Decision: Single Root Module vs. Multi-Module Organizations Structure

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Single root module** | Simplicity, single state file, easy cross-resource references | Scale, separation of concerns, blast radius | <20 accounts, single-team org management |
| **Separate modules by layer** (`org/`, `policies/`, `accounts/`) | Blast radius isolation, team ownership, targeted applies | Cross-module references require remote state | 20+ accounts, multi-team, separate policy and account lifecycles |
| **Layered stacks with remote state** | Full isolation, independent deployment of accounts vs policies | Complexity, data source dependencies, bootstrapping order | Enterprise, regulated, 50+ accounts |

- Agent: "Ask user: How many AWS accounts will the organization manage? Will different teams own account creation vs. policy management?"
- **Source**: [Terraform Module Best Practices](https://developer.hashicorp.com/terraform/language/modules/develop/structure)

---

#### Decision: for_each vs. count for Account and OU Creation

| Option | Best For | Pitfall |
|--------|----------|---------|
| **`for_each` with map** | Multiple accounts/OUs with stable string keys | Complex map construction; adding to middle of map is safe |
| **`count`** | Conditional single resource (0 or 1) | Inserting to list reindexes all resources, corrupting state for Organizations (account destruction/recreation) |
| **Individual named resources** | Foundational accounts (log-archive, security-tooling) | Verbose but safest for irreversible resources |

```hcl
# SAFE — for_each with stable keys
variable "workload_accounts" {
  type = map(object({
    email     = string
    parent_ou = string
  }))
  default = {
    "payments-prod" = {
      email     = "aws-payments-prod@company.com"
      parent_ou = "prod"
    }
    "payments-dev" = {
      email     = "aws-payments-dev@company.com"
      parent_ou = "nonprod"
    }
  }
}

resource "aws_organizations_account" "workloads" {
  for_each = var.workload_accounts

  name      = each.key
  email     = each.value.email
  parent_id = aws_organizations_organizational_unit.workloads_prod.id
  role_name = "OrganizationAccountAccessRole"

  lifecycle {
    ignore_changes = [role_name]
  }
}
```

- Agent: "Ask user: Is account count stable, or will accounts be added/removed over time? For 3+ accounts of the same type, prefer for_each."
- **Source**: [for_each Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)

---

#### Decision: Tag Policy Strategy — Enforce vs. Report Only

| Option | Optimizes | Sacrifices | Best When |
|--------|----------|------------|-----------|
| **Report-only** (no enforcement) | Non-disruptive, visibility into compliance | Non-compliant tags continue to exist | Starting compliance journey, brownfield org |
| **Enforce at OU level** | Blocks non-compliant tagging at resource creation | May block legitimate resource creation if policy is overly strict | Greenfield org, mature tagging strategy |
| **No Tag Policy** | Zero management overhead | No compliance visibility or enforcement | Sandbox OU only |

```hcl
data "aws_iam_policy_document" "tag_policy" {
  statement {
    # Note: Tag Policies use a different JSON schema from IAM policies
    # Use heredoc for Tag Policy JSON — aws_iam_policy_document is for IAM only
  }
}

resource "aws_organizations_policy" "required_tags" {
  name    = "RequiredTags"
  type    = "TAG_POLICY"
  content = jsonencode({
    tags = {
      Environment = {
        tag_key = {
          "@@assign" = "Environment"
        }
        tag_value = {
          "@@assign" = ["production", "staging", "development", "sandbox"]
        }
        enforced_for = {
          "@@assign" = ["ec2:instance", "rds:db", "s3:bucket"]
        }
      }
    }
  })
}
```

- Agent: "Ask user: Is this a new organization (greenfield) or existing (brownfield)? Enforcement on brownfield organizations will immediately flag non-compliant resources."
- **Source**: [Tag Policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html)

---

#### Decision: Resource Control Policy (RCP) Deployment Scope

| Option | Optimizes | Sacrifices | Best When |
|--------|----------|------------|-----------|
| **RCP at root (org-wide)** | Universal data exfiltration prevention | Blocks legitimate cross-org access patterns | Full org control, no external vendor access |
| **RCP at OU level** | Targeted protection for production OUs | Non-production accounts remain unprotected | Phased rollout, sandbox exemptions needed |
| **No RCP** | Zero friction for cross-account access | No resource-side exfiltration controls | Early-stage org, evaluation phase |

```hcl
data "aws_iam_policy_document" "rcp_restrict_to_org" {
  statement {
    sid    = "RestrictS3AccessToOrganization"
    effect = "Deny"
    actions = [
      "s3:*",
    ]
    resources = ["*"]
    condition {
      test     = "StringNotEquals"
      variable = "aws:PrincipalOrgID"
      values   = [aws_organizations_organization.this.id]
    }
    condition {
      test     = "BoolIfExists"
      variable = "aws:PrincipalIsAWSService"
      values   = ["false"]
    }
  }
}

resource "aws_organizations_policy" "rcp_restrict_to_org" {
  name    = "RestrictResourcesToOrganization"
  type    = "RESOURCE_CONTROL_POLICY"
  content = data.aws_iam_policy_document.rcp_restrict_to_org.json
}
```

- Agent: "Ask user: Do any workloads require granting access to AWS principals outside your organization (third-party vendors, AWS services cross-account)? RCPs require explicit exceptions for these patterns."
- **Source**: [Resource Control Policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Deploying Workloads in the Management Account

```hcl
# DON'T — Creating workload resources in the same provider context
# as the management account
resource "aws_lambda_function" "app" {
  function_name = "my-app"
  # ... deployed to management account
}
```

**Why**: The management account is exempt from SCPs — a compromise of any IAM principal in the management account bypasses all SCP guardrails across the entire organization. Management account access is also unaffected by most automated security controls.

**Instead**:
```hcl
# DO — Use a separate provider with assume_role for each workload account
provider "aws" {
  alias  = "workload_prod"
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.workload_prod_account_id}:role/TerraformDeployRole"
  }
}

resource "aws_lambda_function" "app" {
  provider      = aws.workload_prod
  function_name = "my-app"
  # ... deployed to workload account, subject to SCPs
}
```

- **Impact**: state corruption | security breach
- **Severity**: CRITICAL
- **Source**: [AWS Organizations Security Best Practices](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html)

---

#### Anti-Pattern: `CONSOLIDATED_BILLING` Feature Set

```hcl
# DON'T
resource "aws_organizations_organization" "this" {
  feature_set = "CONSOLIDATED_BILLING"
}
```

**Why**: `CONSOLIDATED_BILLING` disables SCPs, RCPs, Tag Policies, Backup Policies, and all service integrations. The organization becomes a billing container only — no governance controls are possible. Migrating from `CONSOLIDATED_BILLING` to `ALL` requires all member accounts to accept an invitation and manual confirmation in the AWS Console; Terraform will show a perpetual diff until this is completed.

**Instead**:
```hcl
# DO — Always use ALL for any governance use case
resource "aws_organizations_organization" "this" {
  feature_set = "ALL"

  enabled_policy_types = [
    "SERVICE_CONTROL_POLICY",
    "TAG_POLICY",
  ]
}
```

- **Impact**: security breach | unmanaged drift
- **Severity**: CRITICAL
- **Source**: [Organizations Feature Sets](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html#feature-set)

---

#### Anti-Pattern: Hardcoded Account Emails

```hcl
# DON'T
resource "aws_organizations_account" "prod" {
  name  = "production"
  email = "aws-prod@mycompany.com"  # Hardcoded, leaks in state file and logs
}
```

**Why**: Account emails are globally unique identifiers. Hardcoding them in source code exposes them to version control, CI/CD logs, and Terraform plan outputs. They cannot be changed after account creation — a leaked email address becomes a permanent organizational identifier.

**Instead**:
```hcl
# DO — Use variables with sensitive = true
variable "account_emails" {
  type = map(string)
  sensitive = true
  description = "Map of account names to owner email addresses. Managed via tfvars, not committed to source."
}

resource "aws_organizations_account" "prod" {
  name  = "production"
  email = var.account_emails["production"]
}
```

- **Impact**: data loss | security breach
- **Severity**: HIGH
- **Source**: [Sensitive Variables](https://developer.hashicorp.com/terraform/language/values/variables#suppressing-values-in-cli-output)

---

#### Anti-Pattern: Using `count` for Account Creation

```hcl
# DON'T
variable "account_names" {
  type    = list(string)
  default = ["dev", "staging", "prod"]
}

resource "aws_organizations_account" "accounts" {
  count = length(var.account_names)
  name  = var.account_names[count.index]
  email = "aws-${var.account_names[count.index]}@company.com"
}
```

**Why**: `count` uses list index as state key. Adding an account in the middle of the list reindexes all subsequent accounts, causing Terraform to plan destruction and recreation of real AWS accounts. AWS account deletion is quota-constrained, rate-limited, and irreversible.

**Instead**:
```hcl
# DO — Use for_each with stable string keys
variable "accounts" {
  type = map(object({
    email     = string
    parent_id = string
  }))
}

resource "aws_organizations_account" "accounts" {
  for_each  = var.accounts
  name      = each.key
  email     = each.value.email
  parent_id = each.value.parent_id

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [role_name]
  }
}
```

- **Impact**: state corruption | data loss
- **Severity**: CRITICAL
- **Source**: [for_each vs count](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each#when-to-use-for_each-instead-of-count)

---

#### Anti-Pattern: Missing `prevent_destroy` on Foundational Accounts

```hcl
# DON'T — No lifecycle protection on irreplaceable accounts
resource "aws_organizations_account" "log_archive" {
  name  = "log-archive"
  email = var.log_archive_email
}
```

**Why**: Foundational accounts (log-archive, security-tooling, network) cannot be recreated without data loss and compliance gaps. A `terraform destroy` or accidental removal from the config would schedule them for closure. Account closure has quotas (cannot close more than 10% of accounts in the past 30 days) and is subject to a 90-day grace period — but compliance logs and security controls are lost immediately.

**Instead**:
```hcl
# DO — Protect foundational accounts from accidental destruction
resource "aws_organizations_account" "log_archive" {
  name             = "log-archive"
  email            = var.log_archive_email
  parent_id        = aws_organizations_organizational_unit.security.id
  close_on_deletion = false  # Only remove from org, do not close

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [role_name]
  }
}
```

- **Impact**: data loss | unmanaged drift
- **Severity**: HIGH
- **Source**: [aws_organizations_account](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_account)

---

#### Anti-Pattern: Attaching SCPs to Individual Accounts Instead of OUs

```hcl
# DON'T — Account-level attachment breaks governance inheritance
resource "aws_organizations_policy_attachment" "scp_account_level" {
  policy_id = aws_organizations_policy.deny_non_approved_regions.id
  target_id = aws_organizations_account.prod_workload.id  # Individual account
}
```

**Why**: Account-level SCP attachments require manual updates for every new account. New accounts placed in an OU are not protected until a policy attachment resource is added. This creates governance gaps, scales O(accounts) instead of O(OUs), and makes policy auditing complex.

**Instead**:
```hcl
# DO — Attach to OU; all current and future accounts inherit automatically
resource "aws_organizations_policy_attachment" "scp_ou_level" {
  policy_id = aws_organizations_policy.deny_non_approved_regions.id
  target_id = aws_organizations_organizational_unit.workloads_prod.id  # OU

  skip_destroy = true
}
```

- **Impact**: unmanaged drift | security breach
- **Severity**: HIGH
- **Source**: [SCP Best Practices](https://docs.aws.amazon.com/organizations/latest/userguide/best-practices_scp.html)

---

#### Anti-Pattern: Missing `skip_destroy` on Policy Attachments

```hcl
# DON'T
resource "aws_organizations_policy_attachment" "scp" {
  policy_id = aws_organizations_policy.baseline.id
  target_id = aws_organizations_organization.this.roots[0].id
  # No skip_destroy
}
```

**Why**: AWS requires at least one SCP to be attached to every entity when SCPs are enabled. If `skip_destroy = false` (default) and the last attached SCP is removed, Terraform will fail mid-apply with an API error. If the SCP is detached manually (or in a partial apply), all member accounts under that entity lose their permission boundary.

**Instead**:
```hcl
# DO
resource "aws_organizations_policy_attachment" "scp" {
  policy_id    = aws_organizations_policy.baseline.id
  target_id    = aws_organizations_organization.this.roots[0].id
  skip_destroy = true
}
```

- **Impact**: state corruption | security breach
- **Severity**: HIGH
- **Source**: [aws_organizations_policy_attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_policy_attachment)

---

## State Management Deep Dive

### Local Development State

```hcl
# Only for learning/prototyping — never for real organizations
terraform {
  required_version = ">= 1.7"
}
```

- **Risk**: No locking, no sharing, no encryption. Organizations state contains account IDs and policy ARNs referenced by all downstream stacks.
- **When**: Local testing against sandbox organization only.

---

### Production Remote State (S3 + DynamoDB)

```hcl
# Bootstrap: create state bucket BEFORE applying org resources
resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-org-terraform-state-${var.management_account_id}"

  lifecycle {
    prevent_destroy = true
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
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

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

# Backend configuration — separate file or passed via -backend-config
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state-123456789012"
    key            = "org/management/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/xxxxx"
  }
}
```

- **Benefit**: Team access, DynamoDB locking prevents concurrent apply conflicts, KMS encryption for state containing account IDs.
- **Safeguard**: State file contains ALL account IDs and policy content — restrict S3 bucket access to Terraform CI/CD role only.

---

### State File Sensitivity Handling for Organizations

```hcl
# Account emails are sensitive — mark outputs accordingly
output "account_emails" {
  value = {
    for k, v in aws_organizations_account.workloads : k => v.email
  }
  sensitive   = true
  description = "Account owner emails — never log or expose"
}

# Consume org state from downstream stacks
data "terraform_remote_state" "org" {
  backend = "s3"
  config = {
    bucket = "my-org-terraform-state-${var.management_account_id}"
    key    = "org/management/terraform.tfstate"
    region = "us-east-1"
  }
}

locals {
  security_ou_id = data.terraform_remote_state.org.outputs.ou_ids["security"]
}
```

---

## Module Architecture

### Standard Module Structure

```
modules/
├── organizations/
│   ├── main.tf           # aws_organizations_organization
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
├── organizational-units/
│   ├── main.tf           # aws_organizations_organizational_unit (recursive pattern)
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
├── member-account/
│   ├── main.tf           # aws_organizations_account + lifecycle
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
└── scp/
    ├── main.tf           # aws_organizations_policy + aws_organizations_policy_attachment
    ├── policies/
    │   ├── deny-regions.json.tpl
    │   ├── deny-disable-security.json.tpl
    │   └── deny-public-access.json.tpl
    ├── variables.tf
    ├── outputs.tf
    └── versions.tf
```

### Module Definition — SCP Module

```hcl
# modules/scp/variables.tf
variable "name" {
  type        = string
  description = "Policy name — must be unique within the organization"

  validation {
    condition     = length(var.name) >= 1 && length(var.name) <= 128
    error_message = "SCP name must be between 1 and 128 characters."
  }
}

variable "description" {
  type        = string
  description = "Policy description"
  default     = ""
}

variable "content" {
  type        = string
  description = "IAM policy JSON for the SCP (must be valid JSON, max 5120 characters)"

  validation {
    condition     = length(var.content) <= 5120
    error_message = "SCP content must not exceed 5120 characters."
  }
}

variable "target_ids" {
  type        = list(string)
  description = "List of OU IDs or account IDs to attach this SCP to"

  validation {
    condition     = length(var.target_ids) >= 1
    error_message = "At least one target_id must be specified."
  }
}

# modules/scp/outputs.tf
output "policy_id" {
  value       = aws_organizations_policy.this.id
  description = "SCP policy ID for cross-stack references"
}

output "policy_arn" {
  value       = aws_organizations_policy.this.arn
  description = "SCP policy ARN"
}

# root/main.tf — Using the module
module "scp_deny_regions" {
  source     = "./modules/scp"
  name       = "DenyNonApprovedRegions"
  content    = data.aws_iam_policy_document.deny_non_approved_regions.json
  target_ids = [aws_organizations_organizational_unit.workloads.id]
}
```

---

## Integration Patterns

### Integration: Terraform ↔ IAM (Cross-Account Access)

**Pattern**: `OrganizationAccountAccessRole` created in every member account by Organizations, consumed by Terraform to deploy into member accounts.

```hcl
# Terraform provider for a member account
provider "aws" {
  alias  = "member_account"
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${aws_organizations_account.workload.id}:role/OrganizationAccountAccessRole"
  }
}

# Deploy resources into the member account
resource "aws_iam_role" "deploy_role" {
  provider = aws.member_account
  name     = "TerraformDeployRole"

  assume_role_policy = data.aws_iam_policy_document.deploy_trust.json
}
```

- **Issues**: OrganizationAccountAccessRole has `AdministratorAccess` by default — replace it with a least-privilege role after account creation.
- **Source**: [Cross-Account Access](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_access.html)

---

### Integration: Terraform ↔ CloudTrail (Organization Trail)

**Pattern**: Org-wide CloudTrail managed from the management account, writing to the log-archive account S3 bucket.

```hcl
resource "aws_cloudtrail" "org_trail" {
  name                          = "org-management-trail"
  s3_bucket_name                = var.log_archive_bucket_name
  include_global_service_events = true
  is_multi_region_trail         = true
  is_organization_trail         = true
  enable_log_file_validation    = true

  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.cloudtrail.arn}:*"
  cloud_watch_logs_role_arn  = aws_iam_role.cloudtrail_cloudwatch.arn

  kms_key_id = var.cloudtrail_kms_key_arn

  depends_on = [aws_organizations_organization.this]
}
```

- **Issues**: `cloudtrail.amazonaws.com` must be in `aws_service_access_principals` before the trail can be created. The S3 bucket policy in the log-archive account must allow `cloudtrail.amazonaws.com` write access.
- **Versions**: `aws_cloudtrail` stable in aws >= 4.0, `is_organization_trail` since aws >= 2.x
- **Source**: [AWS CloudTrail Organization Trail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html)

---

### Integration: Terraform ↔ AWS Config (Organization Config Rules)

**Pattern**: Delegated administrator account deploys Config rules org-wide.

```hcl
# In security-tooling account (delegated admin for config)
resource "aws_config_organization_managed_rule" "root_mfa" {
  name            = "root-account-mfa-enabled"
  rule_identifier = "ROOT_ACCOUNT_MFA_ENABLED"

  depends_on = [aws_organizations_delegated_administrator.config]
}

resource "aws_config_organization_custom_rule" "tagging" {
  name              = "required-tags"
  lambda_function_arn = aws_lambda_function.config_tagging_rule.arn
  trigger_types     = ["CONFIGURATION_ITEM_CHANGE"]

  resource_types_scope = ["AWS::EC2::Instance", "AWS::S3::Bucket"]

  depends_on = [aws_organizations_delegated_administrator.config]
}
```

- **Issues**: Config must be enabled in each member account before organization rules apply. Use a StackSet or Terraform with `for_each` over account IDs to bootstrap Config recorders.
- **Source**: [AWS Config Organization Rules](https://docs.aws.amazon.com/config/latest/developerguide/config-rule-multi-account-deployment.html)

---

### Integration: Terraform ↔ SSO / IAM Identity Center

**Pattern**: SSO enabled via Organizations service access, permission sets and account assignments managed in Terraform.

```hcl
# Enable SSO via Organizations (declarative — SSO must be manually enabled in console first)
# Then manage via aws_ssoadmin_* resources

data "aws_ssoadmin_instances" "this" {}

resource "aws_ssoadmin_permission_set" "developer" {
  name             = "Developer"
  instance_arn     = tolist(data.aws_ssoadmin_instances.this.arns)[0]
  session_duration = "PT8H"
}

resource "aws_ssoadmin_account_assignment" "developer_prod" {
  instance_arn       = tolist(data.aws_ssoadmin_instances.this.arns)[0]
  permission_set_arn = aws_ssoadmin_permission_set.developer.arn

  principal_id   = var.developer_group_id
  principal_type = "GROUP"

  target_id   = aws_organizations_account.workload_prod.id
  target_type = "AWS_ACCOUNT"
}
```

- **Issues**: `sso.amazonaws.com` must be in `aws_service_access_principals`. SSO instance must be enabled via console before Terraform can manage it. SSO is a global service — use `us-east-1` provider for SSO admin resources.
- **Source**: [AWS SSO Terraform](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssoadmin_permission_set)

---

### Integration: Terraform ↔ S3 (Centralized Logging Bucket)

**Pattern**: Log-archive account S3 bucket with bucket policy allowing CloudTrail and Config write access from the entire organization.

```hcl
# In log-archive account
data "aws_iam_policy_document" "log_bucket_policy" {
  statement {
    sid    = "AWSCloudTrailAclCheck"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions   = ["s3:GetBucketAcl"]
    resources = [aws_s3_bucket.logs.arn]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceOrgID"
      values   = [var.organization_id]
    }
  }

  statement {
    sid    = "AWSCloudTrailWrite"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.logs.arn}/AWSLogs/*"]
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceOrgID"
      values   = [var.organization_id]
    }
  }
}
```

- **Issues**: `aws:SourceOrgID` condition is the correct way to scope bucket policies to your org — more secure than listing individual account IDs.
- **Source**: [S3 Bucket Policy for CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html)

---

## Executable Verification

### Project Init

```bash
terraform init -upgrade
# Expected: ✓ Terraform initialized, provider hashicorp/aws ~> 6.0 installed
```

### Syntax & Format Validation

```bash
terraform fmt -recursive -check=true
# Expected: Exit code 0

terraform validate
# Expected: Success! The configuration is valid.
```

### Security Scanning

```bash
tfsec . --format sarif
# Expected: No CRITICAL findings. HIGH findings for missing MFA enforcement are expected to be addressed by SCPs.

checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks
# Common findings: CKV_AWS_274 (IAM user creation) — correct if your SCP blocks this
```

### Plan & Dry Run

```bash
terraform plan -out=tfplan
terraform show tfplan
# Expected: Clear list of resources to create/modify
# Key check: aws_organizations_account shows CORRECT parent_id (OU, not root)
# Key check: aws_organizations_policy_attachment shows OU targets, not account targets
```

### Apply with Safeguards

```bash
terraform plan -out=tfplan
terraform apply tfplan

terraform state list | grep organizations
# Expected output includes:
# aws_organizations_organization.this
# aws_organizations_organizational_unit.security
# aws_organizations_organizational_unit.workloads
# aws_organizations_account.log_archive
# aws_organizations_policy.deny_non_approved_regions
# aws_organizations_policy_attachment.deny_regions_workloads
# aws_organizations_delegated_administrator.guardduty
```

### Import Existing Resources

```bash
# Import an existing organization
terraform import aws_organizations_organization.this o-exampleorgid11

# Import using import block (Terraform >= 1.5)
# main.tf
import {
  to = aws_organizations_organization.this
  id = "o-exampleorgid11"
}

# Import existing OU
terraform import aws_organizations_organizational_unit.security ou-exampleou11

# Import existing account
terraform import aws_organizations_account.log_archive 111111111111
# For accounts with iam_user_access_to_billing set:
terraform import aws_organizations_account.log_archive 111111111111_ALLOW

# Import existing SCP
terraform import aws_organizations_policy.deny_regions p-12345678

# Import existing policy attachment (account target)
terraform import aws_organizations_policy_attachment.example 123456789012:p-12345678
# For OU target:
terraform import aws_organizations_policy_attachment.example ou-1234:p-12345678
# For root target:
terraform import aws_organizations_policy_attachment.example r-1234:p-12345678
```

---

## Configuration Validation & Type Safety

```hcl
variable "enabled_policy_types" {
  type        = list(string)
  description = "List of policy types to enable in the organization root."
  default     = ["SERVICE_CONTROL_POLICY"]

  validation {
    condition = alltrue([
      for pt in var.enabled_policy_types :
      contains([
        "AISERVICES_OPT_OUT_POLICY",
        "BACKUP_POLICY",
        "BEDROCK_POLICY",
        "CHATBOT_POLICY",
        "DECLARATIVE_POLICY_EC2",
        "INSPECTOR_POLICY",
        "RESOURCE_CONTROL_POLICY",
        "S3_POLICY",
        "SECURITYHUB_POLICY",
        "SERVICE_CONTROL_POLICY",
        "TAG_POLICY",
        "UPGRADE_ROLLOUT_POLICY",
      ], pt)
    ])
    error_message = "All values in enabled_policy_types must be valid Organizations policy types."
  }
}

variable "aws_service_access_principals" {
  type        = list(string)
  description = "AWS service principals to enable for Organizations integration."
  default     = ["cloudtrail.amazonaws.com", "config.amazonaws.com"]

  validation {
    condition     = length(var.aws_service_access_principals) >= 1
    error_message = "At least one service access principal must be specified."
  }
}

variable "ou_hierarchy" {
  type = map(object({
    name      = string
    parent_key = optional(string, "root")
  }))
  description = "Map of OU keys to OU configuration. parent_key references another key in this map, or 'root'."
  default     = {}
}
```

---

## Drift Detection & Reconciliation

### Scenario: Account Moved Between OUs Outside Terraform

```
Detection: terraform plan shows
  ~ resource "aws_organizations_account" "workload" {
      ~ parent_id = "ou-xxxx-prod" -> "ou-xxxx-staging"  (drift)
    }
Recovery: terraform apply  # Moves account back to Terraform-managed OU
Note: OU moves are non-destructive but policy changes are immediate
```

### Scenario: SCP Attached Manually in Console

```
Detection: terraform plan shows
  + resource "aws_organizations_policy_attachment" "manual_scp" {
      policy_id = "p-xxxxxxxx"
      target_id = "ou-xxxx-prod"
    }
# OR plan does not show it (not tracked in state)
Recovery:
  terraform import aws_organizations_policy_attachment.manual_scp ou-xxxx-prod:p-xxxxxxxx
  # Then add to config to bring under management
```

### Scenario: Account Created Outside Terraform

```bash
# 1. Get the account ID from the console
# 2. Write the resource config
# 3. Import
terraform import aws_organizations_account.new_account 222222222222

# 4. Add lifecycle ignore_changes for role_name (unreadable post-creation)
# 5. Run terraform plan — verify no unexpected changes
```

### Lifecycle Rules for Organizations Resources

```hcl
resource "aws_organizations_account" "critical" {
  name      = "critical-workload"
  email     = var.critical_account_email
  parent_id = aws_organizations_organizational_unit.workloads_prod.id

  lifecycle {
    prevent_destroy = true          # Block accidental account closure
    ignore_changes  = [role_name]   # role_name unreadable after creation
  }
}
```

- **Source**: [Lifecycle Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle)

---

## Secrets & Sensitive Data Management

```
Secret Type: Account owner email addresses
Storage: tfvars file (gitignored) or AWS Secrets Manager / SSM Parameter Store
Retrieval: variable with sensitive = true, or data source

Secret Type: Management account IAM role ARN
Storage: Environment variable TF_VAR_management_account_id, CI/CD secret
Retrieval: var.management_account_id

Secret Type: Organization ID (for use in policies)
Storage: Terraform output (not sensitive but should be scoped)
Retrieval: data.terraform_remote_state.org.outputs.organization_id
```

```hcl
# Safe pattern — emails via Secrets Manager
data "aws_secretsmanager_secret_version" "account_emails" {
  secret_id = "terraform/org/account-emails"
}

locals {
  account_emails = jsondecode(data.aws_secretsmanager_secret_version.account_emails.secret_string)
}

resource "aws_organizations_account" "workload" {
  name  = "workload-prod"
  email = local.account_emails["workload-prod"]
}
```

- **Source**: [AWS Secrets Manager Terraform](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret)

---

## Testing & Validation Frameworks

### Static Analysis

```
Framework: terraform validate
Purpose: HCL syntax and provider schema validation
Command: terraform validate
Expected Output: "Success! The configuration is valid."
```

```
Framework: tfsec >= 1.28.0
Purpose: Security misconfiguration detection
Command: tfsec . --format json --minimum-severity HIGH
Expected Output: No findings for "organizations" checks related to SCP missing encryption controls
```

```
Framework: checkov >= 3.x
Purpose: Policy-as-code compliance checks
Command: checkov -d . --framework terraform --check CKV_AWS_274,CKV_AWS_355
Expected Output: PASSED for hardcoded credential checks
```

### Terratest Integration Test

```go
package test

import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/stretchr/testify/assert"
)

func TestOrganizationsOUCreation(t *testing.T) {
  t.Parallel()

  opts := &terraform.Options{
    TerraformDir: "../examples/organizations",
    Vars: map[string]interface{}{
      "feature_set":   "ALL",
      "approved_regions": []string{"us-east-1"},
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  orgId := terraform.Output(t, opts, "organization_id")
  assert.Contains(t, orgId, "o-", "Organization ID should start with o-")

  ouIds := terraform.OutputMap(t, opts, "ou_ids")
  assert.Contains(t, ouIds, "security", "Security OU should exist")
}
```

---

## Production Considerations

### Performance & Scalability

```
Scenario: Large organization (200+ accounts)
Challenge: aws_organizations_organization with return_organization_only = false lists all accounts on every refresh, hitting API rate limits
Solution: Set return_organization_only = true in the organization resource; use data.aws_organizations_organizational_units for targeted listing
Metrics: Monitor Organizations API throttle errors in CloudWatch

resource "aws_organizations_organization" "this" {
  feature_set          = "ALL"
  return_organization_only = true  # Only returns org-level attributes, not full account list
}
```

```
Scenario: SCP size limit exceeded
Challenge: Maximum SCP size is 5120 characters per policy, max 5 SCPs per entity
Solution: Decompose large deny policies into domain-specific SCPs (region-control, security-services, network-controls)
```

### Disaster Recovery Runbook

```bash
# 1. State file corruption/loss for org module
aws s3api get-object \
  --bucket my-org-terraform-state-123456789012 \
  --key org/management/terraform.tfstate.backup \
  terraform.tfstate.backup

terraform state push terraform.tfstate.backup

# 2. Re-import all organization resources after state loss
terraform import aws_organizations_organization.this o-exampleorgid11

# 3. Recover from partial SCP detachment (account loses guardrails)
terraform apply -target=aws_organizations_policy_attachment.deny_regions_workloads

# 4. Verify SCP coverage after recovery
aws organizations list-policies-for-target \
  --target-id ou-xxxx-workloadsprod \
  --filter SERVICE_CONTROL_POLICY \
  --query 'Policies[*].{Name:Name,Id:Id}'
```

### Security Checklist

- [ ] `feature_set = "ALL"` — governance controls enabled
- [ ] Management account has no workloads deployed
- [ ] All SCPs attached to OUs (not individual accounts)
- [ ] `skip_destroy = true` on all policy attachments
- [ ] `prevent_destroy = true` on foundational accounts (log-archive, security-tooling)
- [ ] `close_on_deletion = false` on all non-sandbox accounts
- [ ] `lifecycle { ignore_changes = [role_name] }` on all accounts
- [ ] CloudTrail organization trail enabled (org-wide audit logging)
- [ ] Delegated administrators registered for security services
- [ ] State bucket KMS-encrypted with restricted access
- [ ] Account emails stored in Secrets Manager (not in source code)
- [ ] RCP deployed to prevent cross-org data exfiltration (production OUs)
- [ ] MFA enforced on management account root user (out-of-band)

---

## Reference Implementations

- [Terraform AWS Provider — Organizations Resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_organization)
- [AWS Organizations User Guide](https://docs.aws.amazon.com/organizations/latest/userguide/)
- [AWS Multi-Account Architecture Landing Zone](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/welcome.html)
- [AWS Control Tower Terraform](https://registry.terraform.io/modules/aws-ia/control_tower_account_factory/aws/latest)
- [SCP Examples](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_examples.html)
- [RCP Examples](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps_examples.html)

---

## Source Bibliography

### Primary Sources
- [aws_organizations_organization](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_organization)
- [aws_organizations_account](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_account)
- [aws_organizations_organizational_unit](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_organizational_unit)
- [aws_organizations_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_policy)
- [aws_organizations_policy_attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_policy_attachment)
- [aws_organizations_delegated_administrator](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_delegated_administrator)
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)
- [AWS Organizations API Reference](https://docs.aws.amazon.com/organizations/latest/APIReference/)

### Validation & Tools
- [tfsec](https://github.com/aquasecurity/tfsec)
- [Checkov](https://www.checkov.io/)
- [Terratest](https://terratest.gruntwork.io/)
- [GitHub Issues — hashicorp/terraform-provider-aws](https://github.com/hashicorp/terraform-provider-aws/issues?q=label%3Aservice%2Forganizations)

---

## Research Gaps

```
Gap: aws_organizations_resource_policy full argument surface
Impact: Organization resource policy (delegated admin boundary) not fully documented
Workaround: Use AWS Console for org resource policy until provider docs expand
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_resource_policy

Gap: Terraform test framework for cross-account Organizations scenarios
Impact: Unit tests cannot verify actual account creation (quota-constrained)
Workaround: Use moto or LocalStack for mocked tests; Terratest for sandbox org
Follow-up: https://developer.hashicorp.com/terraform/language/tests

Gap: Root access management (new 2024 feature) — no Terraform resource yet
Impact: Centralized root credential management not automatable via Terraform
Workaround: Use AWS Console or CLI (aws organizations enable-root-credentials-management)
Follow-up: https://github.com/hashicorp/terraform-provider-aws/issues — search "root credentials management"
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Organization resource with `feature_set = "ALL"` and standard service principals
- SCP creation using `aws_iam_policy_document` with deny statements
- OU hierarchy creation with explicit `parent_id` references
- Policy attachment to OUs with `skip_destroy = true`
- `prevent_destroy` and `ignore_changes = [role_name]` on all accounts
- State backend with encryption and DynamoDB locking
- Delegated administrator registration for security services

### Medium Confidence (Validate with user)
- Number and names of OUs (depends on org structure)
- Which policy types to enable (TAG_POLICY, RESOURCE_CONTROL_POLICY)
- Approved regions list for region-deny SCP
- Which accounts are foundational vs. workload (determines `prevent_destroy`)
- RCP scope (root vs. production OU only)

### Low Confidence (Must ask user)
- Account email addresses (unique identifiers, cannot change post-creation)
- Management account ID (required for provider assume_role)
- Specific SCP content for business-specific controls
- SSO / IAM Identity Center permission set structure
- Cross-account CI/CD pipeline architecture

### Edge Cases (When to pause)
- Any `terraform destroy` targeting accounts or the organization root
- Detected removal of `skip_destroy = true` from policy attachments
- `feature_set` change from `ALL` to `CONSOLIDATED_BILLING` (impossible — would require org recreation)
- State shows accounts without `parent_id` configured (will cause perpetual diff)
- Any plan showing account destruction — pause and verify explicitly

### Emergency Stop
- Halt if management account email or ID found hardcoded in `.tf` files
- Halt if `feature_set = "CONSOLIDATED_BILLING"` is detected in new resources
- Halt if `terraform destroy` is planned for the organization or foundational accounts
- Halt if `prevent_destroy = false` is being set on log-archive or security-tooling accounts
- Halt if an SCP policy attachment is being removed without `skip_destroy = true`
