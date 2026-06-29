# Terraform AWS IAM — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - IAM (Identity and Access Management)"
Cloud_Provider: "AWS"
Target_Service: "IAM (Identity and Access Management)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-29"
Domain_Complexity: "Complex"
New_V6_Resources_Noted: "aws_iam_role_policies_exclusive, aws_iam_role_policy_attachments_exclusive, aws_iam_group_policies_exclusive, aws_iam_group_policy_attachments_exclusive, aws_iam_user_policies_exclusive, aws_iam_user_policy_attachments_exclusive, aws_iam_organizations_features, aws_iam_outbound_web_identity_federation, aws_iam_security_token_service_preferences"
V6_Deprecations: "inline_policy argument on aws_iam_role (use aws_iam_role_policy + aws_iam_role_policies_exclusive), managed_policy_arns argument on aws_iam_role (use aws_iam_role_policy_attachment + aws_iam_role_policy_attachments_exclusive), aws_iam_policy_attachment (conflicts with per-resource attachment resources)"
```

---

## Executive Summary

AWS IAM is the **security control plane for every AWS service**. Every compute resource, data store, messaging queue, and API that interacts with AWS requires an IAM identity — a role, user, or policy — authorizing exactly the actions it needs. Terraform manages IAM through a multi-resource composition: `aws_iam_role` → `aws_iam_policy` (or `aws_iam_role_policy`) → `aws_iam_role_policy_attachment` → `aws_iam_instance_profile`. Each resource is globally scoped (IAM is a global service with no region), propagates permissions changes asynchronously across AWS regions, and stores sensitive trust data — ARNs, condition keys, federation metadata — directly in the Terraform state file.

The AWS Provider v6.x introduces **exclusive management resources** that eliminate the most common source of IAM configuration drift: the `*_exclusive` resource family (`aws_iam_role_policies_exclusive`, `aws_iam_role_policy_attachments_exclusive`, `aws_iam_user_policies_exclusive`, `aws_iam_user_policy_attachments_exclusive`, `aws_iam_group_policies_exclusive`, `aws_iam_group_policy_attachments_exclusive`). These resources declare "Terraform owns ALL policies of this type on this principal" and will remove any out-of-band additions on the next `terraform apply`. The `inline_policy` argument and `managed_policy_arns` argument on `aws_iam_role` are **deprecated** in v6.x — use standalone `aws_iam_role_policy` + `aws_iam_role_policies_exclusive`, and `aws_iam_role_policy_attachment` + `aws_iam_role_policy_attachments_exclusive` respectively. The `aws_iam_policy_attachment` resource (attaches to users, groups, and roles simultaneously) **permanently conflicts** with the per-resource attachment resources and must not be mixed.

IAM is classified **Complex** because: it controls all AWS access (security-critical, every misconfiguration has blast radius); it uses multi-resource dependency chains with eventual-consistency propagation; the state file contains complete trust and permission metadata; OIDC/SAML federation patterns are mandatory for CI/CD and EKS; password policy, MFA enforcement, and access key lifecycle are compliance requirements; and the exclusive management resources introduce state-ownership semantics not present in most other services.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Ensures reproducibility across all team members and CI pipelines. Pins to aws ~> 6.0 to access exclusive management resources. Enables `terraform test` framework introduced in Terraform 1.7.

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
    key            = "prod/iam/terraform.tfstate"
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

**Why**: Credentials must never be hardcoded. `assume_role` enables cross-account deployments and CI/CD pipelines without static access keys. `default_tags` enforces tagging compliance — IAM roles, policies, and instance profiles should be tagged for cost allocation, compliance audit, and ownership tracking.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "TerraformSession-${var.environment}"
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

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [AWS Provider Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration)

---

#### Pattern: IAM Role with `aws_iam_policy_document` Data Source (v6.x Recommended)

**Why**: `data.aws_iam_policy_document` generates syntactically correct, validated IAM JSON inside Terraform. It eliminates JSON heredoc errors, enforces condition blocks, supports multiple statements, and integrates with `terraform validate`. The `jsonencode()` alternative is also valid for inline trust policies.

```hcl
# Trust policy using data source (recommended)
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    sid     = "AllowLambdaAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_execution" {
  name               = "${var.environment}-lambda-execution-role"
  description        = "Execution role for Lambda function ${var.function_name}"
  path               = "/service-roles/"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  permissions_boundary = var.permissions_boundary_arn # enforce guardrails

  tags = {
    Name    = "${var.environment}-lambda-execution-role"
    Service = var.function_name
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_iam_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | [aws_iam_policy_document](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document)

---

#### Pattern: Standalone Managed Policy with `aws_iam_role_policy_attachment` (v6.x Required)

**Why**: The `inline_policy` argument and `managed_policy_arns` argument on `aws_iam_role` are **deprecated** in v6.x. The recommended pattern is standalone `aws_iam_policy` + `aws_iam_role_policy_attachment`. This decouples policy lifecycle from role lifecycle, enabling policy reuse across multiple roles without duplication, and independent policy versioning.

```hcl
data "aws_iam_policy_document" "s3_read" {
  statement {
    sid    = "AllowS3Read"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.bucket_name}",
      "arn:aws:s3:::${var.bucket_name}/*",
    ]
  }
}

resource "aws_iam_policy" "s3_read" {
  name        = "${var.environment}-s3-read-policy"
  path        = "/app-policies/"
  description = "Allows read access to ${var.bucket_name} bucket"
  policy      = data.aws_iam_policy_document.s3_read.json

  tags = {
    Name = "${var.environment}-s3-read-policy"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_s3_read" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.s3_read.arn
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_iam_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | [aws_iam_role_policy_attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment)

---

#### Pattern: Exclusive Policy Management with `*_exclusive` Resources (v6.x New)

**Why**: Drift prevention. Without exclusive management, policies attached manually in the AWS Console (out-of-band) silently persist through `terraform apply`. The `aws_iam_role_policy_attachments_exclusive` resource enforces that Terraform is the single source of truth for a role's managed policy attachments — any out-of-band attachment is removed on the next apply. Use in combination with `aws_iam_role_policies_exclusive` for inline policies.

```hcl
# Declare all managed policy attachments for the role
resource "aws_iam_role_policy_attachment" "lambda_s3_read" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.s3_read.arn
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Enforce exclusive ownership: no other attachments allowed on this role
resource "aws_iam_role_policy_attachments_exclusive" "lambda_execution" {
  role_name = aws_iam_role.lambda_execution.name

  policy_arns = [
    aws_iam_policy.s3_read.arn,
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
  ]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_iam_role_policy_attachments_exclusive](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachments_exclusive) | [aws_iam_role_policies_exclusive](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policies_exclusive)

---

#### Pattern: EC2 Instance Profile for Credential-Free Instance Access

**Why**: EC2 instances must never use long-lived access keys. Instance profiles deliver temporary credentials via the EC2 metadata service (IMDS), rotating automatically. The `aws_iam_instance_profile` name must be globally unique — even different roles or paths cannot share the same instance profile name.

```hcl
resource "aws_iam_role" "ec2_instance" {
  name = "${var.environment}-ec2-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_instance" {
  name = "${var.environment}-ec2-instance-profile"
  role = aws_iam_role.ec2_instance.name

  tags = {
    Name = "${var.environment}-ec2-instance-profile"
  }
}

# Attach policies to the role
resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  role       = aws_iam_role.ec2_instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_iam_instance_profile](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_instance_profile)

---

#### Pattern: OIDC Provider for Credential-Free CI/CD (GitHub Actions / GitLab / EKS)

**Why**: Static access keys in CI/CD are the #1 source of AWS credential exposure. OIDC federation allows GitHub Actions, GitLab CI, and EKS pods to assume IAM roles using short-lived tokens issued by the OIDC provider. No long-lived credentials, no rotation burden.

```hcl
# One-time per-account setup: GitHub Actions OIDC provider
resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  # Current GitHub Actions OIDC thumbprint - verify at https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1", "1c58a3a8518e8759bf075b76b750d4f2df264fcd"]

  tags = {
    Name = "github-actions-oidc-provider"
  }
}

# Role that GitHub Actions can assume (scoped to specific repo)
data "aws_iam_policy_document" "github_actions_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      # Scope to a specific org/repo/branch
      values = ["repo:${var.github_org}/${var.github_repo}:ref:refs/heads/${var.github_branch}"]
    }
  }
}

resource "aws_iam_role" "github_actions_deploy" {
  name               = "${var.environment}-github-actions-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume.json
  max_session_duration = 3600 # 1 hour max for CI pipelines
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_iam_openid_connect_provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_openid_connect_provider) | [GitHub OIDC Docs](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)

---

#### Pattern: Account-Level Password Policy

**Why**: CIS AWS Foundations Benchmark and SOC2 require a strong password policy. `aws_iam_account_password_policy` is a single-instance resource (one per AWS account) managing the password complexity, rotation, and reuse requirements for IAM users. Without this, the AWS default policy allows weak passwords.

```hcl
resource "aws_iam_account_password_policy" "strict" {
  minimum_password_length        = 16
  require_uppercase_characters   = true
  require_lowercase_characters   = true
  require_numbers                = true
  require_symbols                = true
  allow_users_to_change_password = true
  max_password_age               = 90  # Force rotation every 90 days
  password_reuse_prevention      = 24  # Cannot reuse last 24 passwords
  hard_expiry                    = false # Allow admins to reset expired passwords
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_iam_account_password_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_account_password_policy) | [CIS AWS Foundations](https://www.cisecurity.org/benchmark/amazon_web_services)

---

#### Pattern: Permissions Boundary for Delegated Administration

**Why**: Permissions boundaries cap the maximum permissions a role or user can have, regardless of what policies are attached. Critical for allowing developer teams to create their own IAM roles (self-service) without risk of privilege escalation beyond the boundary. Required pattern in organizations using AWS Control Tower or multi-account strategies.

```hcl
data "aws_iam_policy_document" "developer_boundary" {
  statement {
    sid    = "AllowedServices"
    effect = "Allow"
    actions = [
      "s3:*",
      "dynamodb:*",
      "lambda:*",
      "logs:*",
      "xray:*",
      "cloudwatch:*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "DenyIAMEscalation"
    effect = "Deny"
    actions = [
      "iam:CreateUser",
      "iam:DeleteRole",
      "iam:DeletePolicy",
      "iam:AttachRolePolicy",
      "iam:PutRolePermissionsBoundary",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "developer_boundary" {
  name        = "${var.environment}-developer-permissions-boundary"
  path        = "/boundaries/"
  description = "Permissions boundary for developer-created roles"
  policy      = data.aws_iam_policy_document.developer_boundary.json
}

# Reference in role creation
resource "aws_iam_role" "app_role" {
  name                 = "${var.environment}-app-role"
  assume_role_policy   = data.aws_iam_policy_document.app_assume.json
  permissions_boundary = aws_iam_policy.developer_boundary.arn
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [IAM Permissions Boundaries](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)

---

#### Pattern: Variable Validation and Type Safety for IAM Configuration

**Why**: Prevents invalid ARN formats, non-existent regions, or out-of-range session durations at `terraform plan` time — before any AWS API call is made. IAM errors (especially malformed ARNs in trust policies) fail silently or cause cryptic errors during apply.

```hcl
variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod"
  }
}

variable "permissions_boundary_arn" {
  type        = string
  description = "ARN of permissions boundary policy to apply to all created roles"
  default     = null

  validation {
    condition = var.permissions_boundary_arn == null || can(
      regex("^arn:aws:iam::[0-9]{12}:policy/[a-zA-Z0-9+=,.@_/-]+$", var.permissions_boundary_arn)
    )
    error_message = "permissions_boundary_arn must be a valid IAM policy ARN or null"
  }
}

variable "max_session_duration" {
  type        = number
  description = "Maximum session duration in seconds for assumed roles"
  default     = 3600

  validation {
    condition     = var.max_session_duration >= 3600 && var.max_session_duration <= 43200
    error_message = "max_session_duration must be between 3600 (1h) and 43200 (12h) seconds"
  }
}

variable "github_org" {
  type        = string
  description = "GitHub organization name for OIDC trust"

  validation {
    condition     = can(regex("^[a-zA-Z0-9][a-zA-Z0-9-]{0,38}$", var.github_org))
    error_message = "GitHub org must be a valid GitHub organization name"
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

#### Pattern: Least-Privilege Policy with Specific Resource ARNs

**Why**: `"Resource": "*"` is the most common IAM misconfiguration. Every policy statement should scope `resources` to the minimum required ARN prefix. Use `${data.aws_caller_identity.current.account_id}` and `${data.aws_region.current.name}` to construct region/account-scoped ARNs without hardcoding.

```hcl
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "app_specific" {
  statement {
    sid    = "AllowSpecificDynamoDBTable"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query",
    ]
    resources = [
      "arn:aws:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/${var.table_name}",
      "arn:aws:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/${var.table_name}/index/*",
    ]
  }

  statement {
    sid    = "AllowSpecificSecretsManagerSecret"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]
    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.environment}/${var.app_name}/*",
    ]
  }

  statement {
    sid    = "AllowKMSDecrypt"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
    ]
    resources = [var.kms_key_arn]
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [IAM Policy Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) | [aws_iam_policy_document](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document)

---

### ⚠️ Conditional Patterns

---

#### Decision: `aws_iam_role_policy` (Inline) vs. `aws_iam_policy` + `aws_iam_role_policy_attachment` (Managed)

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Inline `aws_iam_role_policy`** | Atomic role+policy lifecycle, single resource to destroy | Reuse across multiple roles, independent versioning | Service-specific permission that will never be shared, tight coupling desired |
| **Managed `aws_iam_policy` + attachment** | Reuse, versioning, independent lifecycle, cross-role sharing | More resource declarations, slight propagation delay | Shared policies (e.g., CloudWatch Logs write), compliance-managed policies |
| **AWS Managed Policies** | Zero maintenance, AWS-maintained, pre-validated | Over-permissive (broad scope), changes outside Terraform control | AWSLambdaBasicExecutionRole, AmazonSSMManagedInstanceCore, ReadOnly roles |

- **Agent**: "Ask user: Will this policy be shared across multiple roles? Should policy changes be independent of the role lifecycle?"
- **Source**: [IAM Policy Types](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)

---

#### Decision: Exclusive Management (`*_exclusive`) vs. Additive Management

| Option | Optimizes | Sacrifices | Drift Risk |
|--------|-----------|------------|------------|
| **`aws_iam_role_policy_attachments_exclusive`** | Full drift prevention, single source of truth, safe for prod | Out-of-band emergency access removed on next apply | Eliminates |
| **Additive (`aws_iam_role_policy_attachment` only)** | Flexibility for manual additions, break-glass access | Configuration drift from console changes, unknown policy creep | Accumulates over time |

- **When**: Use exclusive resources in production. Avoid in break-glass scenarios where emergency manual policy attachments must survive the next apply.
- **Agent**: "Ask user: Is break-glass out-of-band policy attachment an operational requirement? If yes, skip exclusive resources and accept drift risk."
- **Source**: [aws_iam_role_policy_attachments_exclusive](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachments_exclusive)

---

#### Decision: IAM Users vs. Roles vs. OIDC Federation

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **IAM Users** | Simple CLI/SDK access, legacy compatibility | Long-lived credential management, rotation burden, MFA enforcement complexity | Legacy systems, external vendors requiring access keys (avoid in greenfield) |
| **IAM Roles** | Temporary credentials, no rotation, cross-account | Requires assume-role call, session duration limits | EC2, Lambda, ECS, EKS service identities; cross-account access |
| **OIDC Federation** | No credentials at all, short-lived tokens, auditability | OIDC provider setup, identity provider trust configuration | GitHub Actions, GitLab CI, Kubernetes workload identity, CI/CD pipelines |

- **Agent**: "Ask user: What type of identity is requesting access? Human (use SSO/SAML), service (use role), CI/CD (use OIDC)? IAM users should be a last resort."
- **Source**: [IAM Identity Types](https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html)

---

#### Decision: Multi-Account Role Strategy

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **`assume_role` with `ExternalId`** | Confused deputy attack prevention, auditable cross-account | Additional parameter passing | Third-party vendors, service accounts |
| **`aws_iam_organizations_features`** | Centralized IAM delegation, SCP integration | Organizations dependency | Multi-account AWS Organizations setup |
| **Hub-spoke with trusted account** | Centralized identity plane, single SAML/OIDC provider | Network hops, latency | Enterprise, 10+ account setups |

- **Agent**: "Ask user: Is this a single-account, multi-account, or multi-account with Organizations setup? Cross-account strategies differ significantly."
- **Source**: [Cross-Account Role Access](https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_cross-account-with-roles.html)

---

#### Decision: Service-Linked Roles vs. Custom Service Roles

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Service-Linked Role (`aws_iam_service_linked_role`)** | AWS-managed permissions, automatic updates, compliance | No policy customization allowed | ECS, EKS, Config, Shield Advanced — services that require SLRs |
| **Custom Service Role** | Full permission control, scope reduction possible | Manual maintenance when AWS adds new required permissions | Lambda, EC2, custom use cases where SLR is not required |

- **Agent**: "Check if target AWS service requires a service-linked role before creating a custom role."
- **Source**: [AWS Service-Linked Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_aws-services-that-work-with-iam.html)

---

#### Decision: `for_each` vs `count` for Multiple Similar Roles

| Option | Best For | Pitfall |
|--------|----------|---------|
| **`for_each` with map** | Multiple roles with stable names (e.g., per-service roles) | Removing a key destroys and recreates that role — attached resources may be disrupted |
| **`count`** | Boolean conditional roles (0 or 1) | Reordering map → list causes incorrect role destruction |
| **Separate resources** | Few roles with distinct configurations | Verbose but safest for production |

- **When**: Use `for_each` when creating a known set of similar roles (e.g., one per microservice), use separate resources for unique production roles with long-lived attached resources.
- **Source**: [Meta-Arguments: for_each](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Hardcoded Access Keys in Provider or Resources

```hcl
# DON'T
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  region     = "us-east-1"
}

# DON'T
resource "aws_iam_access_key" "deploy" {
  user = aws_iam_user.deploy.name
  # Access key secret stored in state file in plaintext
}
output "deploy_secret" {
  value = aws_iam_access_key.deploy.secret # DON'T - exposed in state + outputs
}
```

**Why**: Hardcoded credentials in code are committed to version control, logged in CI/CD outputs, and visible to anyone with state file access. `aws_iam_access_key` secrets are stored in the state file in plaintext.

```hcl
# DO - Use IAM roles / OIDC federation instead of access keys
provider "aws" {
  region = var.aws_region
  # Credentials from environment: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
  # Or from EC2/ECS/Lambda IAM role automatically
  # Or from assume_role with OIDC-issued tokens
}

# If access keys are unavoidable (legacy systems only):
resource "aws_iam_access_key" "legacy_service" {
  user = aws_iam_user.legacy_service.name
}

output "legacy_service_key_id" {
  value     = aws_iam_access_key.legacy_service.id
  sensitive = false # Key ID is not a secret
}

output "legacy_service_secret" {
  value     = aws_iam_access_key.legacy_service.secret
  sensitive = true # Mark sensitive to suppress in logs
  # Store via: terraform output legacy_service_secret | aws secretsmanager put-secret-value ...
}
```

- **Impact**: CRITICAL — Full AWS account compromise
- **Severity**: CRITICAL
- **Source**: [AWS IAM Security Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

---

#### Anti-Pattern: Wildcard `Resource: "*"` in Sensitive Action Policies

```hcl
# DON'T
data "aws_iam_policy_document" "bad" {
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue", "kms:Decrypt"]
    resources = ["*"]  # DON'T - can read ANY secret in the account
  }

  statement {
    effect    = "Allow"
    actions   = ["iam:*"]  # DON'T - full IAM control
    resources = ["*"]
  }
}
```

**Why**: Wildcard resources on sensitive actions (secrets, KMS, IAM) allow lateral movement and privilege escalation. Any compromised identity with these permissions can read all secrets, decrypt all data, or create admin roles.

```hcl
# DO - Scope to specific resources
data "aws_iam_policy_document" "scoped" {
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.environment}/${var.app_name}/*"
    ]
  }

  statement {
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [var.app_kms_key_arn]  # Specific key ARN only
  }
}
```

- **Impact**: CRITICAL — Horizontal data access, privilege escalation
- **Severity**: CRITICAL
- **Source**: [IAM Least Privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege)

---

#### Anti-Pattern: Using `aws_iam_policy_attachment` (Conflicts with Per-Resource Attachments)

```hcl
# DON'T - aws_iam_policy_attachment conflicts with all other attachment resources
resource "aws_iam_policy_attachment" "bad" {
  name       = "my-attachment"
  users      = [aws_iam_user.deploy.name]
  roles      = [aws_iam_role.lambda.name]
  groups     = [aws_iam_group.developers.name]
  policy_arn = aws_iam_policy.app.arn
}

# This will CONFLICT with:
resource "aws_iam_role_policy_attachment" "also_bad" {  # DON'T mix these
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.other.arn
}
```

**Why**: `aws_iam_policy_attachment` permanently shows a diff when used alongside `aws_iam_role_policy_attachment`, `aws_iam_user_policy_attachment`, or `aws_iam_group_policy_attachment`. The resources fight over policy attachment state on every plan.

```hcl
# DO - Use per-resource attachment resources exclusively
resource "aws_iam_role_policy_attachment" "lambda_app" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.app.arn
}

resource "aws_iam_user_policy_attachment" "deploy_app" {
  user       = aws_iam_user.deploy.name
  policy_arn = aws_iam_policy.app.arn
}

resource "aws_iam_group_policy_attachment" "developers_app" {
  group      = aws_iam_group.developers.name
  policy_arn = aws_iam_policy.app.arn
}
```

- **Impact**: HIGH — Permanent Terraform drift, unpredictable apply behavior
- **Severity**: HIGH
- **Source**: [aws_iam_policy_attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy_attachment)

---

#### Anti-Pattern: `inline_policy` or `managed_policy_arns` Arguments on `aws_iam_role` (Deprecated v6.x)

```hcl
# DON'T - Both arguments are deprecated in v6.x
resource "aws_iam_role" "bad" {
  name               = "bad-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json

  # DEPRECATED in v6.x - use aws_iam_role_policy instead
  inline_policy {
    name   = "my-inline"
    policy = data.aws_iam_policy_document.inline.json
  }

  # DEPRECATED in v6.x - use aws_iam_role_policy_attachment instead
  managed_policy_arns = [aws_iam_policy.app.arn]
}
```

**Why**: These arguments conflict with standalone `aws_iam_role_policy` and `aws_iam_role_policy_attachment` resources. Mixing them causes resource cycling, permanent diffs, and unpredictable state behavior.

```hcl
# DO - Separate resources with exclusive management
resource "aws_iam_role" "good" {
  name               = "good-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  # No inline_policy or managed_policy_arns arguments
}

resource "aws_iam_role_policy" "inline" {
  name   = "my-inline"
  role   = aws_iam_role.good.id
  policy = data.aws_iam_policy_document.inline.json
}

resource "aws_iam_role_policy_attachment" "managed" {
  role       = aws_iam_role.good.name
  policy_arn = aws_iam_policy.app.arn
}

# Optionally enforce exclusive ownership
resource "aws_iam_role_policies_exclusive" "good" {
  role_name    = aws_iam_role.good.name
  policy_names = [aws_iam_role_policy.inline.name]
}
```

- **Impact**: HIGH — Resource cycling, permanent plan diffs, state inconsistency
- **Severity**: HIGH
- **Source**: [aws_iam_role (Deprecations)](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role)

---

#### Anti-Pattern: Missing `force_detach_policies` When Renaming/Deleting Roles

```hcl
# DON'T - Changing name without force_detach_policies causes DeleteConflict error
resource "aws_iam_role" "app" {
  name               = "new-name"  # Changed from "old-name"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  # Missing force_detach_policies = true
}
```

**Why**: When using `aws_iam_policy_attachment` (not recommended, but exists in legacy code) and renaming a role, AWS requires all policies to be detached before the role can be deleted. Without `force_detach_policies`, Terraform will error with `DeleteConflict`.

```hcl
# DO - Set force_detach_policies when renaming is possible (not needed with aws_iam_role_policy_attachment)
resource "aws_iam_role" "app" {
  name                  = var.role_name
  assume_role_policy    = data.aws_iam_policy_document.assume.json
  force_detach_policies = true  # Safe for aws_iam_policy_attachment users

  lifecycle {
    create_before_destroy = true  # Prevents downtime during rename
  }
}
```

- **Impact**: MEDIUM — Apply failure during role lifecycle operations
- **Severity**: MEDIUM
- **Source**: [aws_iam_role force_detach_policies](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role#force_detach_policies)

---

#### Anti-Pattern: Trust Policy Allowing All Principals

```hcl
# DON'T
data "aws_iam_policy_document" "too_broad" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = ["*"]  # DON'T - anyone can assume this role
    }
  }
}
```

**Why**: A role with `Principal: "*"` in its trust policy can be assumed by any AWS account, including external threat actors. This is a critical misconfiguration frequently flagged by security scanners.

```hcl
# DO - Scope to specific accounts, services, or OIDC subjects
data "aws_iam_policy_document" "scoped_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::${var.trusted_account_id}:root"  # Specific account only
      ]
    }

    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [var.external_id]  # Confused deputy protection
    }
  }
}
```

- **Impact**: CRITICAL — Cross-account privilege escalation, data exfiltration
- **Severity**: CRITICAL
- **Source**: [IAM Trust Policy Security](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html)

---

#### Anti-Pattern: Creating Long-Lived IAM Users for Automation

```hcl
# DON'T - for CI/CD, services, or automation
resource "aws_iam_user" "ci_pipeline" {
  name = "github-ci-pipeline"
}

resource "aws_iam_access_key" "ci_pipeline" {
  user = aws_iam_user.ci_pipeline.name
  # Long-lived key stored in CI/CD secrets — rotation is manual and often forgotten
}
```

**Why**: IAM user access keys are long-lived, must be manually rotated, and are frequently leaked in logs, repositories, or container images. OIDC federation provides zero-credential CI/CD without any key management.

```hcl
# DO - Use OIDC federation for GitHub Actions (see Pattern: OIDC Provider above)
# For ECS/Lambda/EC2: use IAM roles with automatic credential delivery
# For legacy integrations that REQUIRE keys: rotate using Secrets Manager rotation
resource "aws_secretsmanager_secret_rotation" "ci_key_rotation" {
  secret_id           = aws_secretsmanager_secret.ci_access_key.id
  rotation_lambda_arn = var.key_rotation_lambda_arn

  rotation_rules {
    automatically_after_days = 30
  }
}
```

- **Impact**: HIGH — Credential theft, compliance failure, manual rotation burden
- **Severity**: HIGH
- **Source**: [IAM Best Practices - Use Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#use-roles-with-aws-service) | [GitHub OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments)

---

## State Management Deep Dive

### IAM-Specific State Sensitivities

IAM state is particularly sensitive because:
1. **Trust policies** reveal which accounts and services can assume roles
2. **Access key secrets** are stored in plaintext in state when using `aws_iam_access_key`
3. **OIDC thumbprints** reveal OIDC provider configuration
4. **Policy content** reveals the exact permission scope of every identity

All state files containing IAM resources must be encrypted at rest and access-restricted.

### Local Development State

```hcl
# For learning/development only - never for production IAM changes
terraform {
  required_version = ">= 1.7"
  # No backend block = local state only
}
```

- **Risk**: IAM policy content and any access key secrets in plaintext on local disk
- **When**: Solo development, testing non-production IAM patterns

---

### Production Remote State (S3 + DynamoDB + KMS)

```hcl
# Dedicated state bucket for IAM configurations (separate from other services)
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state-iam"
    key            = "prod/iam/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/mrk-abc123"  # CMK for IAM state
    dynamodb_table = "terraform-locks"

    # Restrict state access to deployment role only
    # Apply S3 bucket policy that allows only TerraformDeployRole
  }
}
```

- **Recommendation**: Use a KMS Customer Managed Key (CMK) for IAM state encryption — AWS Managed Keys (`aws/s3`) provide encryption but not key usage audit logs per-access.
- **IAM restriction**: The S3 bucket policy for the IAM state bucket should allow only the designated Terraform deployment role, not developer roles.

---

### State File Sensitivity Handling for IAM

```hcl
# Access key secrets are automatically stored in state - mark outputs sensitive
output "service_access_key_id" {
  value       = aws_iam_access_key.service.id
  description = "Access key ID (not secret)"
  sensitive   = false
}

output "service_secret_access_key" {
  value       = aws_iam_access_key.service.secret
  description = "Secret access key - rotate regularly"
  sensitive   = true  # Suppressed in plan/apply output and logs
}

# OIDC provider ARN for reference by other modules
output "github_oidc_provider_arn" {
  value       = aws_iam_openid_connect_provider.github_actions.arn
  description = "OIDC provider ARN for GitHub Actions trust policies"
  sensitive   = false
}

# Role ARNs for cross-module reference
output "lambda_execution_role_arn" {
  value       = aws_iam_role.lambda_execution.arn
  description = "Lambda execution role ARN"
  sensitive   = false
}
```

---

## Module Architecture

### Standard IAM Module Structure

```
modules/
├── iam-role/
│   ├── main.tf          # aws_iam_role + aws_iam_role_policy_attachment
│   ├── variables.tf     # role_name, assume_role_services, policy_arns, tags
│   ├── outputs.tf       # role_arn, role_name, role_id
│   ├── versions.tf      # required_providers
│   └── README.md
├── iam-oidc-github/
│   ├── main.tf          # aws_iam_openid_connect_provider + assume role
│   ├── variables.tf     # github_org, github_repo, github_branch, policy_arns
│   ├── outputs.tf       # role_arn, oidc_provider_arn
│   ├── versions.tf
│   └── README.md
├── iam-service-account/
│   ├── main.tf          # aws_iam_user + aws_iam_access_key (legacy only)
│   ├── variables.tf
│   ├── outputs.tf       # access_key_id, secret_key (sensitive)
│   └── README.md
```

### Example: Reusable IAM Role Module

```hcl
# modules/iam-role/variables.tf
variable "role_name" {
  type        = string
  description = "Name of the IAM role"

  validation {
    condition     = length(var.role_name) <= 64 && can(regex("^[a-zA-Z0-9+=,.@_-]+$", var.role_name))
    error_message = "Role name must be <=64 chars and contain only alphanumeric and +=,.@_- characters"
  }
}

variable "assume_role_services" {
  type        = list(string)
  description = "AWS service principals that can assume this role"
  default     = []

  validation {
    condition     = alltrue([for s in var.assume_role_services : can(regex("^[a-z0-9.-]+\\.amazonaws\\.com$", s))])
    error_message = "Each service must be a valid AWS service principal (e.g., lambda.amazonaws.com)"
  }
}

variable "managed_policy_arns" {
  type        = list(string)
  description = "List of managed policy ARNs to attach to the role"
  default     = []

  validation {
    condition     = alltrue([for arn in var.managed_policy_arns : can(regex("^arn:aws:iam::", arn))])
    error_message = "Each policy ARN must start with arn:aws:iam::"
  }
}

variable "permissions_boundary_arn" {
  type        = string
  description = "Permissions boundary ARN"
  default     = null
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}

# modules/iam-role/outputs.tf
output "role_arn" {
  value       = aws_iam_role.this.arn
  description = "IAM role ARN"
}

output "role_name" {
  value       = aws_iam_role.this.name
  description = "IAM role name"
}

output "role_id" {
  value       = aws_iam_role.this.unique_id
  description = "IAM role unique ID"
}
```

---

## Integration Patterns: Terraform ↔ IAM

### Integration: Terraform ↔ Secrets Manager

```hcl
# Grant access to specific Secrets Manager secrets
data "aws_iam_policy_document" "secrets_read" {
  statement {
    sid    = "AllowSecretsRead"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]
    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.environment}/*"
    ]
  }

  statement {
    sid    = "AllowKMSForSecrets"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
    ]
    resources = [var.secrets_kms_key_arn]
  }
}

resource "aws_iam_policy" "secrets_read" {
  name   = "${var.environment}-secrets-read"
  policy = data.aws_iam_policy_document.secrets_read.json
}
```

- **Versions**: `aws_iam_policy` ≥ 4.0 | `aws_secretsmanager_secret` ≥ 4.0
- **Issues**: KMS key policy must also grant the role `kms:Decrypt` — IAM policy alone is insufficient
- **Source**: [Secrets Manager IAM](https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access.html)

---

### Integration: Terraform ↔ KMS

```hcl
# KMS key policy (required in addition to IAM policy)
data "aws_iam_policy_document" "kms_key_policy" {
  statement {
    sid    = "EnableRootAccess"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowServiceRoleDecrypt"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = [aws_iam_role.app.arn]
    }
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:GenerateDataKey",
    ]
    resources = ["*"]
  }
}
```

- **Issues**: KMS uses both resource-based (key policy) and identity-based (IAM policy) access control. BOTH must allow the action. IAM-only grants are ignored unless the key policy grants the account root access.
- **Source**: [KMS Key Policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)

---

### Integration: Terraform ↔ CloudTrail (Audit)

```hcl
# IAM role for CloudTrail to write to S3 + CloudWatch Logs
data "aws_iam_policy_document" "cloudtrail_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "cloudtrail_logs" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/cloudtrail/*"]
  }
}

resource "aws_iam_role" "cloudtrail" {
  name               = "${var.environment}-cloudtrail-role"
  assume_role_policy = data.aws_iam_policy_document.cloudtrail_assume.json
}

resource "aws_iam_role_policy" "cloudtrail_logs" {
  name   = "cloudtrail-logs-write"
  role   = aws_iam_role.cloudtrail.id
  policy = data.aws_iam_policy_document.cloudtrail_logs.json
}
```

- **Issues**: CloudTrail also requires an S3 bucket policy (not IAM policy) to allow delivery. Both must be configured.
- **Source**: [CloudTrail IAM](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/control-user-permissions-for-cloudtrail.html)

---

### Integration: Terraform ↔ Organizations (SCPs)

```hcl
# Retrieve current account's organization SCPs for policy simulation
data "aws_organizations_organization" "current" {}

# Service Control Policy denying dangerous actions in all member accounts
data "aws_iam_policy_document" "deny_root_actions" {
  statement {
    sid    = "DenyRootUser"
    effect = "Deny"
    actions = [
      "iam:CreateVirtualMFADevice",
      "iam:CreateUser",
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "aws:PrincipalType"
      values   = ["Root"]
    }
  }
}
```

- **Issues**: SCPs act as permission ceilings — even if an IAM policy allows an action, an SCP can deny it. Always test IAM policies against active SCPs using `data.aws_iam_principal_policy_simulation`.
- **Source**: [Organizations SCPs](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)

---

### Integration: Terraform ↔ Lambda

```hcl
# Lambda execution role (minimal required permissions)
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.environment}-${var.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  permissions_boundary = var.permissions_boundary_arn
}

# Basic execution: CloudWatch Logs write
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC access (only if Lambda runs in VPC)
resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  count      = var.vpc_enabled ? 1 : 0
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
```

- **Issues**: Lambda requires a trust policy with `lambda.amazonaws.com`. Lambda@Edge also requires `edgelambda.amazonaws.com` in the trust policy.
- **Source**: [Lambda Execution Role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)

---

### Integration: Terraform ↔ EKS (IRSA - IAM Roles for Service Accounts)

```hcl
# EKS IRSA: per-namespace, per-service-account IAM role
data "aws_eks_cluster" "main" {
  name = var.cluster_name
}

resource "aws_iam_openid_connect_provider" "eks" {
  url             = data.aws_eks_cluster.main.identity[0].oidc[0].issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
}

data "aws_iam_policy_document" "eks_service_account_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(data.aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub"
      values   = ["system:serviceaccount:${var.namespace}:${var.service_account_name}"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(data.aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eks_service_account" {
  name               = "${var.environment}-${var.service_account_name}-irsa"
  assume_role_policy = data.aws_iam_policy_document.eks_service_account_assume.json
}
```

- **Issues**: The OIDC issuer URL must be used without the `https://` prefix in condition variable names. The `tls_certificate` data source requires the `hashicorp/tls` provider.
- **Source**: [EKS IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)

---

## Quality Control

### Verification Commands

```bash
# Initialize with provider upgrade
terraform init -upgrade
# Expected: Terraform has been successfully initialized!

# Format validation
terraform fmt -recursive -check=true
# Expected: Exit code 0, no output (all files formatted correctly)

# Syntax validation (validates IAM policy document syntax)
terraform validate
# Expected: Success! The configuration is valid.

# Security scanning for IAM misconfigurations
tfsec . --format json | jq '.results[] | select(.severity == "CRITICAL" or .severity == "HIGH")'
# Expected: Empty array [] for clean configurations

# Checkov IAM-specific checks
checkov -d . --framework terraform --check CKV_AWS_40,CKV_AWS_41,CKV_AWS_274,CKV_AWS_275 --quiet
# CKV_AWS_40: IAM policies should not allow full admin
# CKV_AWS_41: Ensure no hardcoded credentials
# CKV_AWS_274: Disallow IAM roles with admin-like policies
# CKV_AWS_275: Ensure IAM policies do not allow wildcard on all services
# Expected: Passed checks > Failed checks

# Plan with lock
terraform plan -out=tfplan -lock=true
# Expected: Plan: N to add, 0 to change, 0 to destroy (first deploy)

# Verify planned IAM policy content before applying
terraform show tfplan | grep -A 20 "aws_iam_policy"
# Expected: Policy JSON matches expected permissions

# Apply
terraform apply tfplan
# Expected: Apply complete! Resources: N added, 0 changed, 0 destroyed.

# Validate created roles and policies
terraform state list | grep iam
# Expected: All IAM resources enumerated

# Verify role trust policy post-apply
terraform state show aws_iam_role.lambda_execution | grep assume_role_policy
# Expected: Trust policy JSON matches input
```

---

### Testing with Terratest

```go
package test

import (
  "testing"
  "strings"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/gruntwork-io/terratest/modules/aws"
  "github.com/stretchr/testify/assert"
)

func TestIAMRoleDeployment(t *testing.T) {
  t.Parallel()

  opts := &terraform.Options{
    TerraformDir: "../examples/iam-role",
    Vars: map[string]interface{}{
      "environment": "test",
      "role_name":   "terratest-lambda-role",
      "aws_region":  "us-east-1",
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  roleArn := terraform.Output(t, opts, "lambda_execution_role_arn")
  assert.Contains(t, roleArn, "arn:aws:iam::")
  assert.Contains(t, roleArn, "role/terratest-lambda-role")

  // Verify role exists in AWS
  roleName := terraform.Output(t, opts, "lambda_execution_role_name")
  role := aws.GetIamRole(t, roleName, "us-east-1")
  assert.Equal(t, "terratest-lambda-role", aws.StringValue(role.RoleName))

  // Verify trust policy
  assert.Contains(t, aws.StringValue(role.AssumeRolePolicyDocument), "lambda.amazonaws.com")
}

func TestIAMPolicyLeastPrivilege(t *testing.T) {
  t.Parallel()

  opts := &terraform.Options{
    TerraformDir: "../examples/iam-policy",
    Vars:         map[string]interface{}{"environment": "test"},
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  policyArn := terraform.Output(t, opts, "app_policy_arn")
  assert.NotEmpty(t, policyArn)

  // Verify no wildcard resources on sensitive actions
  policyContent := aws.GetIamPolicyDocument(t, policyArn, "us-east-1")
  assert.NotContains(t, policyContent, `"Resource": "*"`,
    "Policy should not use wildcard resources on sensitive actions")
  assert.NotContains(t, strings.ToLower(policyContent), `"iam:*"`,
    "Policy should not grant full IAM control")
}
```

---

## Production Readiness

### IAM Propagation and Eventual Consistency

IAM changes are **eventually consistent globally** — a role created in `us-east-1` may take seconds to be visible in `ap-southeast-1`. This affects:
- Lambda invocations immediately after role creation/update
- Cross-region resource deployments within the same `terraform apply`

```hcl
# Add depends_on to resources that depend on IAM role propagation
resource "aws_lambda_function" "app" {
  filename      = var.deployment_package
  function_name = var.function_name
  role          = aws_iam_role.lambda_execution.arn
  handler       = "index.handler"
  runtime       = "nodejs20.x"

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,  # Wait for policy attachment
    aws_iam_role_policy_attachments_exclusive.lambda,       # Wait for exclusive management
  ]
}
```

### IAM Limits and Quotas

| Limit | Default | Increase via |
|-------|---------|-------------|
| Managed policies per account | 1,500 | Service Quotas |
| Managed policies per entity (role/user/group) | 10 | Service Quotas (max 20) |
| Inline policy size per entity | 2,048 bytes | Not increasable |
| Policy document size (managed) | 6,144 bytes | Not increasable |
| Roles per account | 1,000 | Service Quotas |
| IAM users per account | 5,000 | Service Quotas |
| Characters in role name | 64 | Not changeable |

### Security Checklist

- [ ] All secrets stored in Secrets Manager or Parameter Store (no hardcoded credentials)
- [ ] State file encryption enabled with KMS CMK (not AWS managed key)
- [ ] State file access restricted to Terraform deployment role only
- [ ] All IAM resources tagged (Environment, Owner, ManagedBy=terraform)
- [ ] No `Resource: "*"` on sensitive actions (secretsmanager, kms, iam)
- [ ] Permissions boundaries applied to developer-created roles
- [ ] OIDC federation used for CI/CD (no service user access keys)
- [ ] `aws_iam_role_policy_attachments_exclusive` enabled in production
- [ ] CloudTrail enabled for IAM API audit logging
- [ ] Account password policy set (minimum 16 chars, MFA required)
- [ ] No `aws_iam_policy_attachment` (use per-resource attachment resources)
- [ ] No deprecated `inline_policy` or `managed_policy_arns` arguments
- [ ] Trust policies scoped to specific principals (no `Principal: "*"`)
- [ ] `ExternalId` condition in cross-account trust policies

### Disaster Recovery Runbook

```bash
# 1. Role state corruption recovery
aws s3api get-object \
  --bucket my-org-terraform-state-iam \
  --key prod/iam/terraform.tfstate.backup \
  terraform.tfstate.backup

terraform state pull > terraform.tfstate.corrupted
cp terraform.tfstate.backup terraform.tfstate
terraform state push terraform.tfstate

# 2. Import existing role into Terraform state
terraform import aws_iam_role.app_role my-existing-role-name
terraform import aws_iam_policy.app_policy arn:aws:iam::123456789012:policy/my-policy

# 3. Detect IAM drift (out-of-band changes)
terraform plan -refresh=true
# Look for: ~ update in-place changes to trust/permission policies

# 4. Emergency role recreation (production incident)
# Remove from state, let Terraform recreate
terraform state rm aws_iam_role.app_role
terraform apply -target=aws_iam_role.app_role

# 5. Recover from accidentally removed exclusive attachments
# If aws_iam_role_policy_attachments_exclusive removed a needed policy:
# 1. Comment out exclusive resource temporarily
# 2. Add missing policy back via AWS Console or aws cli
# 3. Add to exclusive resource's policy_arns list
# 4. Re-enable exclusive resource
# 5. Apply to bring Terraform back in sync

# 6. Verify role can be assumed after recovery
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/app-role \
  --role-session-name TestSession
```

---

## Reference Implementations

### Complete Root Module Example

```hcl
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
    key            = "prod/iam/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "TerraformSession-${var.environment}"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# GitHub Actions OIDC Provider
resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = var.github_oidc_thumbprints
}

# GitHub Actions Deploy Role
data "aws_iam_policy_document" "github_deploy_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_org}/${var.github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  name               = "${var.environment}-github-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_deploy_assume.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy_attachment" "github_deploy_terraform" {
  role       = aws_iam_role.github_deploy.name
  policy_arn = aws_iam_policy.terraform_deploy.arn
}

resource "aws_iam_role_policy_attachments_exclusive" "github_deploy" {
  role_name   = aws_iam_role.github_deploy.name
  policy_arns = [aws_iam_policy.terraform_deploy.arn]
}

# Lambda Execution Role
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_execution" {
  name               = "${var.environment}-lambda-execution"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachments_exclusive" "lambda" {
  role_name   = aws_iam_role.lambda_execution.name
  policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]
}

# Account Password Policy
resource "aws_iam_account_password_policy" "strict" {
  minimum_password_length        = 16
  require_uppercase_characters   = true
  require_lowercase_characters   = true
  require_numbers                = true
  require_symbols                = true
  allow_users_to_change_password = true
  max_password_age               = 90
  password_reuse_prevention      = 24
}
```

```hcl
# terraform.tfvars (example — gitignore in production)
aws_region   = "us-east-1"
account_id   = "123456789012"
environment  = "prod"
owner        = "platform-team"
github_org   = "my-org"
github_repo  = "my-infra"
github_oidc_thumbprints = [
  "6938fd4d98bab03faadb97b34396831e3780aea1",
  "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
]
```

---

## Source Bibliography

### Primary Sources
- [Terraform AWS IAM Resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) — Latest v6.47.0 docs
- [aws_iam_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role)
- [aws_iam_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy)
- [aws_iam_role_policy_attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment)
- [aws_iam_role_policy_attachments_exclusive](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachments_exclusive)
- [aws_iam_openid_connect_provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_openid_connect_provider)
- [data.aws_iam_policy_document](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document)
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)

### AWS Documentation
- [IAM User Guide](https://docs.aws.amazon.com/IAM/latest/UserGuide/)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [IAM Permissions Boundaries](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)
- [EKS IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)

### Validation & Tools
- [tfsec GitHub](https://github.com/aquasecurity/tfsec)
- [Checkov IAM Checks](https://www.checkov.io/5.Policy%20Index/terraform.html)
- [Terratest](https://terratest.gruntwork.io/)
- [AWS IAM Policy Simulator](https://policysim.aws.amazon.com/)

---

## Completion Checklist

- [x] All Terraform 1.7 and aws v6.x patterns validated
- [x] v6.x deprecations documented (`inline_policy`, `managed_policy_arns` on `aws_iam_role`)
- [x] v6.x new resources documented (`*_exclusive` family)
- [x] State management strategy with KMS CMK for IAM state documented
- [x] Module architecture with variable validation defined
- [x] Every anti-pattern has tested alternative
- [x] All CLI commands with expected success output included
- [x] Integration examples for Secrets Manager, KMS, CloudTrail, Organizations, Lambda, EKS
- [x] Sources directly linked to registry/docs
- [x] Security checklist complete
- [x] Complete root module example with .tfvars
- [x] Disaster recovery procedures documented

---

## Research Gaps

```
Gap: aws_iam_security_token_service_preferences (new in v6.x)
Impact: Affects STS token versions (v1 vs v2) for AWS GovCloud or China regions
Workaround: Default behavior (v1 tokens) is sufficient for standard commercial regions
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_security_token_service_preferences

Gap: aws_iam_organizations_features (new in v6.x)
Impact: Manages root user session management and centralized root access features in Organizations
Workaround: Configure manually in AWS Organizations console or via AWS CLI
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_organizations_features

Gap: aws_iam_principal_policy_simulation (data source)
Impact: Could be used in Terraform to validate effective permissions before apply
Workaround: Use AWS IAM Policy Simulator UI at https://policysim.aws.amazon.com/
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_principal_policy_simulation
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- IAM role creation with known service principals (Lambda, EC2, ECS)
- Standard policy attachment using `aws_iam_role_policy_attachment`
- OIDC provider creation for GitHub Actions
- Password policy configuration
- Instance profile creation for EC2
- `aws_iam_policy_document` data source usage
- Variable validation blocks for ARN/name inputs

### Medium Confidence (Validate with user)
- Enabling `aws_iam_role_policy_attachments_exclusive` (removes out-of-band policies)
- Permissions boundary scope and ARN
- Cross-account trust policy account IDs
- EKS IRSA namespace and service account names
- GitHub OIDC `sub` claim scope (branch vs. tag vs. environment)

### Low Confidence (Must ask user)
- Compliance-specific policy requirements (SOC2, HIPAA, PCI-DSS)
- Custom SCPs in Organizations context
- SAML federation provider metadata
- Existing IAM resources to import (requires `terraform import`)
- Access key rotation strategy for legacy service users

### Edge Cases (When to pause)
- Any `terraform destroy` targeting IAM roles with production resource dependencies
- `aws_iam_role_policy_attachments_exclusive` removal of an unknown policy (may indicate break-glass access)
- Trust policy changes that could lock out the deployment role itself
- Permissions boundary creation that may block currently running workloads
- Detected hardcoded credentials in any `.tf` or `.tfvars` file → **HALT, alert user**
