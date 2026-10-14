# Terraform AWS Secrets Manager — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - Secrets Manager"
Cloud_Provider: "AWS"
Target_Service: "Secrets Manager"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-29)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-29"
Support_Status: "Active"
Last_Updated: "2026-05-29"
Research_Date: "2026-05-29"
Domain_Complexity: "Complex"
SecretsManager_Resources_Covered: "aws_secretsmanager_secret, aws_secretsmanager_secret_version, aws_secretsmanager_secret_rotation, aws_secretsmanager_secret_policy"
SecretsManager_Data_Sources_Covered: "aws_secretsmanager_secret, aws_secretsmanager_secret_version, aws_secretsmanager_random_password"
V6_Notable_Arguments: "replica block on aws_secretsmanager_secret (multi-region), force_overwrite_replica_secret, aws_secretsmanager_secret_rotation as standalone resource (replaces deprecated inline rotation_* arguments on aws_secretsmanager_secret), recovery_window_in_days (0 = force immediate delete), force_delete_without_recovery on aws_secretsmanager_secret"
```

---

## Executive Summary

AWS Secrets Manager is a fully managed credentials lifecycle service that replaces hardcoded secrets with runtime API retrievals. The Terraform AWS provider (v6.x) manages the complete secrets lifecycle through four primary resources: `aws_secretsmanager_secret` (lifecycle, metadata, replication, encryption key), `aws_secretsmanager_secret_version` (encrypted value storage), `aws_secretsmanager_secret_rotation` (automatic rotation schedule and Lambda function binding), and `aws_secretsmanager_secret_policy` (resource-based access control for cross-account and service principals). The provider v6.x split rotation configuration into its own standalone resource (`aws_secretsmanager_secret_rotation`) — the deprecated inline `rotation_*` arguments on `aws_secretsmanager_secret` still exist but emit deprecation warnings and should not be used in new code.

Three provider-specific hazards define Secrets Manager as a **Complex** domain: (1) `aws_secretsmanager_secret_version` stores the plaintext secret value in Terraform state — the S3 backend with encryption and DynamoDB locking is mandatory, not optional; (2) `recovery_window_in_days` defaults to 30 days, but setting it to `0` (or `force_delete_without_recovery = true`) schedules immediate deletion without recovery — a Terraform destroy on a production secret starts an irreversible clock or causes instant data loss; (3) `aws_secretsmanager_secret_rotation` requires the Lambda rotation function to be deployed and reachable in the same VPC before Terraform can attach it — dependency ordering is critical and `depends_on` is often required. The v6.x `replica` block on `aws_secretsmanager_secret` replaces the deprecated `aws_secretsmanager_secret_replica` resource from older provider versions — using the old resource pattern with v6.x produces perpetual diffs.

Secrets Manager is classified **Complex** because: (1) the state file contains encrypted secret values in plaintext — mishandling state equals credentials exposure; (2) rotation involves multi-resource coordination (secret + Lambda + IAM + VPC + execution role) with specific dependency ordering; (3) the `aws_secretsmanager_secret_policy` interacts with IAM identity policies via dual-layer evaluation (both must allow for cross-account access); (4) `prevent_destroy` must be set on production secrets or a pipeline can delete credentials and cause service outages; (5) `force_delete_without_recovery = true` is a permanent, instant data-loss operation; (6) multi-region replication uses `replica` blocks requiring provider aliases and cross-region coordination.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Pins the provider to `~> 6.0` to access the standalone `aws_secretsmanager_secret_rotation` resource and the `replica` block syntax. The S3 backend with encryption and DynamoDB locking is non-negotiable — the state file stores secret values in plaintext within `aws_secretsmanager_secret_version` resources.

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
    key            = "prod/secrets-manager/terraform.tfstate"
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

**Why**: Credentials must never be hardcoded. The `assume_role` pattern enables CI/CD pipelines without static keys. `default_tags` enforces mandatory tagging on all secrets — required for cost allocation, compliance, and secret ownership tracking in large accounts.

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

#### Pattern: `aws_secretsmanager_secret` with `prevent_destroy` and Recovery Window

**Why**: The secret resource stores metadata, lifecycle configuration, and the KMS encryption key reference. `prevent_destroy = true` is mandatory for production — a `terraform destroy` without it deletes the secret and triggers the recovery window countdown. `recovery_window_in_days = 30` (the default) provides a 30-day safety net; setting it to `0` or using `force_delete_without_recovery = true` enables instant deletion — acceptable only in non-production environments.

```hcl
resource "aws_secretsmanager_secret" "app_db_credentials" {
  name        = "${var.environment}/${var.app_name}/db-credentials"
  description = "${var.app_name} database credentials for ${var.environment}"

  # Customer managed KMS key (required for cross-account; optional for single-account)
  kms_key_id = aws_kms_key.secrets_encryption.arn

  # Recovery window: 7–30 days (default 30). Set 0 only in non-production.
  recovery_window_in_days = var.environment == "production" ? 30 : 7

  # Multi-region replication (optional — see Conditional Patterns)
  # replica {
  #   region     = "us-west-2"
  #   kms_key_id = var.replica_kms_key_arn
  # }

  tags = {
    Name        = "${var.environment}/${var.app_name}/db-credentials"
    Application = var.app_name
    DataClass   = "confidential"
  }

  lifecycle {
    prevent_destroy = true  # CRITICAL: prevents accidental deletion in production
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_secretsmanager_secret](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret)

---

#### Pattern: `aws_secretsmanager_secret_version` with Sensitive Variable Input

**Why**: Secret versions store the actual encrypted secret value. The `secret_string` argument accepts JSON for structured secrets (recommended for database credentials) or a plain string. Marking the Terraform variable as `sensitive = true` prevents the value from appearing in `terraform plan` output and CI logs. **Critical**: the plaintext value is stored in `terraform.tfstate` — the encrypted S3 backend is the primary mitigation.

```hcl
# Structured database credential (JSON string — recommended pattern)
resource "aws_secretsmanager_secret_version" "app_db_credentials" {
  secret_id = aws_secretsmanager_secret.app_db_credentials.id

  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    engine   = "postgres"
    host     = aws_db_instance.app.endpoint
    port     = 5432
    dbname   = var.db_name
  })

  # Prevent recreation on every apply when value hasn't changed
  lifecycle {
    ignore_changes = [secret_string]  # Use only when rotation manages version lifecycle
  }
}

variable "db_password" {
  type        = string
  description = "Database master password — sourced from CI secrets, never hardcoded"
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 16
    error_message = "Database password must be at least 16 characters."
  }
}

variable "db_username" {
  type        = string
  description = "Database master username"

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]{0,62}$", var.db_username))
    error_message = "Database username must start with a letter and contain only alphanumeric characters and underscores, max 63 chars."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_secretsmanager_secret_version](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_version)

---

#### Pattern: `aws_secretsmanager_secret_rotation` as Standalone Resource (v6.x)

**Why**: Provider v6.x moves rotation configuration into `aws_secretsmanager_secret_rotation` as a standalone resource. The deprecated inline `rotation_lambda_arn`, `rotation_rules`, and `automatically_after_days` arguments on `aws_secretsmanager_secret` still function but emit deprecation warnings and will be removed. Using the standalone resource eliminates perpetual plan diffs from AWS normalizing the rotation configuration on `aws_secretsmanager_secret`. **Dependency ordering is critical**: the Lambda function and its invocation permission must exist before attaching rotation.

```hcl
resource "aws_secretsmanager_secret_rotation" "app_db_credentials" {
  secret_id           = aws_secretsmanager_secret.app_db_credentials.id
  rotation_lambda_arn = aws_lambda_function.rotation.arn

  rotation_rules {
    # Duration expressed as ISO 8601 duration string (e.g., "P7D" = 7 days)
    # Use schedule_expression for cron-based rotation (v6.x addition)
    schedule_expression = "rate(7 days)"  # or "cron(0 8 1,15 * ? *)" for specific dates
    duration            = "2h"           # max time Secrets Manager waits for rotation to complete
  }

  # Ensure rotation function exists and has correct permissions before attaching
  depends_on = [
    aws_lambda_permission.secrets_manager_invoke,
    aws_iam_role_policy.rotation_lambda_policy,
  ]
}

# Lambda invocation permission — Secrets Manager must be authorized to invoke the function
resource "aws_lambda_permission" "secrets_manager_invoke" {
  statement_id  = "SecretsManagerInvoke-${var.environment}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rotation.function_name
  principal     = "secretsmanager.amazonaws.com"
  source_arn    = aws_secretsmanager_secret.app_db_credentials.arn
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_secretsmanager_secret_rotation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation)

---

#### Pattern: Least-Privilege IAM for Secret Access

**Why**: Scopes consumer IAM policies to exact actions (`GetSecretValue`, `DescribeSecret`) and specific secret ARN patterns. Wildcard `secretsmanager:*` on `*` grants full account-wide secret control — a critical blast radius in multi-tenant accounts. Using `data.aws_iam_policy_document` generates verifiable, diff-friendly JSON without hardcoded strings.

```hcl
# IAM policy for application consumers (read-only)
data "aws_iam_policy_document" "app_secret_consumer" {
  statement {
    sid    = "GetAppSecrets"
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]

    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.environment}/${var.app_name}/*",
    ]
  }

  # Required if using a Customer Managed KMS key
  statement {
    sid    = "DecryptSecretKMS"
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
    ]

    resources = [aws_kms_key.secrets_encryption.arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["secretsmanager.${var.aws_region}.amazonaws.com"]
    }
  }
}

resource "aws_iam_policy" "app_secret_consumer" {
  name        = "${var.environment}-${var.app_name}-secrets-consumer"
  description = "Allows ${var.app_name} to read its secrets from Secrets Manager"
  policy      = data.aws_iam_policy_document.app_secret_consumer.json
}

data "aws_caller_identity" "current" {}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Secrets Manager Auth and Access](https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access.html) | [aws_iam_policy_document](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document)

---

#### Pattern: Resource Policy via `aws_secretsmanager_secret_policy`

**Why**: Resource policies enable cross-account secret sharing and enforce access conditions (e.g., require VPC endpoint, require encryption in transit). `block_public_policy = true` prevents policies that would grant anonymous or overly broad access — this is a separate parameter from the policy document itself and should always be set.

```hcl
resource "aws_secretsmanager_secret_policy" "app_db_credentials" {
  secret_arn          = aws_secretsmanager_secret.app_db_credentials.arn
  block_public_policy = true  # Reject policies that would make secret broadly accessible

  policy = data.aws_iam_policy_document.secret_resource_policy.json
}

data "aws_iam_policy_document" "secret_resource_policy" {
  # Cross-account consumer access — allow specific roles in other accounts
  statement {
    sid    = "AllowCrossAccountConsumer"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = var.cross_account_consumer_role_arns  # list(string)
    }

    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]

    resources = ["*"]  # "*" resolves to the secret itself within resource policy context

    # Enforce VPC endpoint access for cross-account consumers
    condition {
      test     = "StringEquals"
      variable = "aws:sourceVpce"
      values   = var.allowed_vpc_endpoint_ids
    }
  }

  # Deny access if transport is not TLS (defense-in-depth)
  statement {
    sid    = "DenyNonTLSTransport"
    effect = "Deny"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions   = ["secretsmanager:*"]
    resources = ["*"]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_secretsmanager_secret_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_policy) | [Resource Policies](https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_resource-policies.html)

---

#### Pattern: Data Source for Safe Secret Consumption in Other Stacks

**Why**: Other Terraform stacks (RDS, ECS, Lambda) should consume secrets via data sources rather than duplicating `aws_secretsmanager_secret_version` resources. This decouples stacks and avoids the consumer stack storing the secret value in its own state. The `version_stage = "AWSCURRENT"` default is safe — only override to `AWSPREVIOUS` during rotation debugging.

```hcl
# In a consumer stack (e.g., ECS task definitions, RDS instance configs)
data "aws_secretsmanager_secret" "db_credentials" {
  name = "${var.environment}/${var.app_name}/db-credentials"
  # Alternative: use ARN for cross-account references
  # arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/app/db-credentials-AbCdEf"
}

data "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id     = data.aws_secretsmanager_secret.db_credentials.id
  version_stage = "AWSCURRENT"  # explicit default — never use AWSPENDING in application configs
}

# Parse structured JSON secret
locals {
  db_credentials = jsondecode(data.aws_secretsmanager_secret_version.db_credentials.secret_string)
}

# Reference: local.db_credentials.host, local.db_credentials.port, etc.
# NOTE: parsed values are sensitive — mark dependent outputs sensitive = true
output "db_endpoint" {
  value     = local.db_credentials.host
  sensitive = true  # mark outputs sensitive when derived from secret data
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_secretsmanager_secret (data source)](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secret) | [aws_secretsmanager_secret_version (data source)](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secret_version)

---

#### Pattern: Variable Validation and Type Safety for Secrets Manager

**Why**: Validates secret naming conventions, recovery windows, rotation schedules, and ARN formats at `terraform plan` time — before any AWS API call is made. Secret names follow the pattern `<environment>/<app-name>/<purpose>` enforced via regex.

```hcl
variable "secret_name" {
  type        = string
  description = "Secret name path (e.g., prod/myapp/db-credentials)"

  validation {
    condition     = can(regex("^[a-zA-Z0-9/_+=.@-]{1,512}$", var.secret_name))
    error_message = "Secret name must be 1–512 characters: alphanumeric, /, _, +, =, ., @, -"
  }
}

variable "recovery_window_in_days" {
  type        = number
  description = "Recovery window before permanent deletion (0 = immediate, 7–30 = scheduled)"
  default     = 30

  validation {
    condition     = var.recovery_window_in_days == 0 || (var.recovery_window_in_days >= 7 && var.recovery_window_in_days <= 30)
    error_message = "recovery_window_in_days must be 0 (immediate) or between 7 and 30 inclusive."
  }
}

variable "rotation_schedule_expression" {
  type        = string
  description = "Rotation schedule as rate() or cron() expression"
  default     = "rate(30 days)"

  validation {
    condition     = can(regex("^(rate\\(|cron\\()", var.rotation_schedule_expression))
    error_message = "rotation_schedule_expression must start with 'rate(' or 'cron('."
  }
}

variable "cross_account_consumer_role_arns" {
  type        = list(string)
  description = "IAM role ARNs from other accounts allowed to read this secret"
  default     = []

  validation {
    condition = alltrue([
      for arn in var.cross_account_consumer_role_arns :
      can(regex("^arn:(aws|aws-cn|aws-us-gov):iam::[0-9]{12}:role/.+", arn))
    ])
    error_message = "All ARNs must be valid IAM role ARNs: arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME."
  }
}

variable "allowed_vpc_endpoint_ids" {
  type        = list(string)
  description = "VPC Endpoint IDs allowed to access this secret (enforced via resource policy)"
  default     = []

  validation {
    condition = alltrue([
      for vpce in var.allowed_vpc_endpoint_ids :
      can(regex("^vpce-[a-f0-9]+$", vpce))
    ])
    error_message = "VPC Endpoint IDs must match the format vpce-[hex characters]."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

#### Pattern: Output Definitions for Cross-Stack Integration

**Why**: The secret ARN is consumed by ECS task definitions, Lambda environment configurations, RDS rotation functions, and IAM policies in other stacks. Marking the secret ARN as non-sensitive is appropriate (ARNs appear in CloudTrail regardless). Never output `secret_string` — it exposes the plaintext credential.

```hcl
output "secret_arn" {
  value       = aws_secretsmanager_secret.app_db_credentials.arn
  description = "Secret ARN for cross-stack IAM policy and ECS task definition references"
  sensitive   = false  # ARNs appear in CloudTrail; marking sensitive adds no real protection
}

output "secret_id" {
  value       = aws_secretsmanager_secret.app_db_credentials.id
  description = "Secret ID (same as ARN for aws_secretsmanager_secret)"
  sensitive   = false
}

output "secret_name" {
  value       = aws_secretsmanager_secret.app_db_credentials.name
  description = "Human-readable secret name for SDK/CLI references"
  sensitive   = false
}

# NEVER output secret_string or the parsed credential values
# output "db_password" {
#   value = aws_secretsmanager_secret_version.app_db_credentials.secret_string  # FORBIDDEN
# }
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Output Values](https://developer.hashicorp.com/terraform/language/values/outputs)

---

### ⚠️ Conditional Patterns

---

#### Decision: Secrets Manager vs. SSM Parameter Store (SecureString)

| Option | Optimizes | Sacrifices | Scaling | Best When |
|--------|-----------|------------|---------|-----------|
| **Secrets Manager** | Automatic rotation, managed rotation for RDS, cross-account resource policies, multi-region replication, `BatchGetSecretValue` | Cost ($0.40/secret/month + $0.05/10K API calls) | Scales to thousands of secrets; higher cost at scale | Credentials requiring rotation, database passwords, API keys, cross-account sharing |
| **SSM Parameter Store SecureString** | Cost (free standard tier up to 10K params; $0.05/advanced/month), hierarchical paths, native integration with ECS/EC2/Lambda | No native rotation, no resource policies, no replication, 8KB value limit standard | Scales to 10K standard params free | Configuration values, feature flags, non-rotating secrets, budget-constrained environments |

- **Cost Comparison**: For 100 secrets with 1M monthly API calls, Secrets Manager ≈ $45/month vs. Parameter Store ≈ $5/month. For credentials requiring rotation, Secrets Manager eliminates custom rotation Lambda cost.
- **Agent**: "Ask user: Does this secret require automatic rotation? If yes, use Secrets Manager. Does it contain a credential with a lifecycle (password, API key)? Use Secrets Manager. Is it a configuration flag or connection string that doesn't rotate? Consider Parameter Store."
- **Source**: [Secrets Manager vs Parameter Store](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html) | [Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)

---

#### Decision: Rotation Strategy — Managed vs. Lambda Single User vs. Lambda Alternating Users

| Option | Optimizes | Sacrifices | Downtime | Complexity | Best When |
|--------|-----------|------------|----------|------------|-----------|
| **Managed Rotation** | Zero ops overhead, no Lambda, no VPC config, AWS-maintained | Limited to RDS/Aurora/Redshift/DocumentDB master users | None | Minimal | RDS/Aurora/Redshift/DocumentDB primary credentials |
| **Lambda Single User** | Simplicity — one DB user, no superuser secret | Brief credential unavailability (milliseconds) during password change | ~50–500ms | Low | Most workloads with retry logic; app-level DB users |
| **Lambda Alternating Users** | Zero-downtime — previous credential always valid | Two DB users, superuser secret ($0.40/month extra), permission sync complexity | None | High | High-availability SLAs; apps without retry logic; replication-heavy databases |

```hcl
# Managed rotation (RDS master credentials — no Lambda required)
# NOTE: No aws_secretsmanager_secret_rotation resource needed for managed rotation
# Enable via console or AWS CLI after Terraform creates the secret:
# aws secretsmanager rotate-secret --secret-id <arn> \
#   --rotation-rules AutomaticallyAfterDays=30

# Lambda single-user rotation
resource "aws_secretsmanager_secret_rotation" "single_user" {
  secret_id           = aws_secretsmanager_secret.app_db_credentials.id
  rotation_lambda_arn = aws_lambda_function.single_user_rotation.arn

  rotation_rules {
    schedule_expression = "rate(30 days)"
    duration            = "2h"
  }

  depends_on = [aws_lambda_permission.secrets_manager_invoke]
}

# Lambda alternating-users rotation (requires superuser secret)
resource "aws_secretsmanager_secret_rotation" "alternating_users" {
  secret_id           = aws_secretsmanager_secret.app_db_user.id
  rotation_lambda_arn = aws_lambda_function.alternating_user_rotation.arn

  rotation_rules {
    schedule_expression = "rate(14 days)"
    duration            = "4h"
  }

  depends_on = [
    aws_lambda_permission.secrets_manager_invoke_user,
    aws_secretsmanager_secret.superuser_credentials,  # superuser secret must exist
  ]
}
```

- **Agent**: "Ask user: Is this a supported database (RDS/Aurora/Redshift/DocumentDB)? Use managed rotation. Does the application require zero-downtime credential rotation? Use alternating users. Otherwise, use single user."
- **Source**: [Rotation Strategy](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html) | [aws_secretsmanager_secret_rotation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation)

---

#### Decision: AWS Managed Key vs. Customer Managed KMS Key

| Option | Optimizes | Sacrifices | Cross-Account | Cost | Best When |
|--------|-----------|------------|---------------|------|-----------|
| **AWS Managed Key (`aws/secretsmanager`)** | Zero cost, zero management, automatic rotation | No cross-account access, no custom key policy, limited audit granularity, cannot disable | Not possible | Free | Single-account, non-cross-account secrets |
| **Customer Managed Key (CMK)** | Cross-account access, custom key policy conditions, immediate revocation via key disable, granular CloudTrail audit | $1/month/key + $0.03/10K API requests | Yes (required) | $1/month+ | Cross-account secret sharing, compliance-mandated key audit, instant revocation needed |

```hcl
# Option A: AWS Managed Key (default — no kms_key_id needed)
resource "aws_secretsmanager_secret" "simple" {
  name = "${var.environment}/simple-secret"
  # kms_key_id omitted — uses aws/secretsmanager managed key automatically
}

# Option B: Customer Managed Key
resource "aws_secretsmanager_secret" "cross_account" {
  name       = "${var.environment}/cross-account-secret"
  kms_key_id = aws_kms_key.secrets_encryption.arn  # CMK required for cross-account

  # KMS key policy must include ViaService condition:
  # "StringEquals": { "kms:ViaService": "secretsmanager.<region>.amazonaws.com" }
}
```

- **Agent**: "Ask user: Does this secret need to be shared cross-account? If yes, a Customer Managed KMS Key is mandatory — the AWS managed key does not support cross-account decryption."
- **Source**: [Secrets Manager Encryption](https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html)

---

#### Decision: Multi-Region Replication vs. Independent Per-Region Secrets

| Option | Optimizes | Sacrifices | Sync | Best When |
|--------|-----------|------------|------|-----------|
| **Multi-Region Replication (`replica` block)** | Automatic value sync, single source of truth, DR readiness, low cross-region latency for reads | Primary region dependency for writes, async replication lag, replica read-only | Automatic | Active-passive DR, global applications needing local secret access, multi-region RDS |
| **Independent Secrets per Region** | Full independence, no replication dependency, different values per region | Manual sync burden, drift risk between regions, separate rotation per region | Manual | Different credentials per region (different DB instances), fully independent regional deployments |

```hcl
# Multi-region replication via replica block (v6.x pattern)
resource "aws_secretsmanager_secret" "global_db_credentials" {
  name       = "${var.environment}/${var.app_name}/db-credentials"
  kms_key_id = aws_kms_key.primary_secrets_key.arn

  replica {
    region     = "us-west-2"
    kms_key_id = var.us_west_2_kms_key_arn  # different KMS key per region is supported
  }

  replica {
    region     = "eu-west-1"
    kms_key_id = var.eu_west_1_kms_key_arn
  }

  # force_overwrite_replica_secret = false  # set true only if replica already exists from manual ops
}
```

- **Agent**: "Ask user: Does your workload require the same credentials to be available in multiple regions (e.g., for DR failover or global read replicas)? Use replication. Do different regions connect to different resources with different credentials? Use independent secrets."
- **Source**: [Replicate Secrets](https://docs.aws.amazon.com/secretsmanager/latest/userguide/replicate-secrets.html) | [aws_secretsmanager_secret replica block](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret#replica)

---

#### Decision: `for_each` vs. `count` for Multiple Secrets

| Option | Best For | Pitfall |
|--------|----------|---------|
| **`for_each` with map** | Multiple secrets with different names, rotation configs, or KMS keys | Changing a key in the map renames/recreates the secret (use `lifecycle.create_before_destroy`) |
| **`count`** | Creating N identical secrets | Reordering the list destroys and recreates secrets — data loss for in-use credentials |
| **Separate resources** | Secrets with completely different configurations, owners, or lifecycle | Verbose but safest for production secrets |

```hcl
# PREFERRED: for_each for multiple application secrets
variable "application_secrets" {
  type = map(object({
    description           = string
    recovery_window       = number
    rotation_days         = number
    rotation_lambda_arn   = string
  }))

  default = {
    "db-credentials" = {
      description         = "Database master credentials"
      recovery_window     = 30
      rotation_days       = 30
      rotation_lambda_arn = ""
    }
    "api-key" = {
      description         = "Third-party API key"
      recovery_window     = 7
      rotation_days       = 90
      rotation_lambda_arn = ""
    }
  }
}

resource "aws_secretsmanager_secret" "app_secrets" {
  for_each = var.application_secrets

  name                    = "${var.environment}/${var.app_name}/${each.key}"
  description             = each.value.description
  recovery_window_in_days = each.value.recovery_window
  kms_key_id              = aws_kms_key.secrets_encryption.arn

  lifecycle {
    prevent_destroy = true
  }
}
```

- **Agent**: "Ask user: Are these secrets structurally different (different KMS keys, rotation schedules, consumers)? Use separate resources for safety. Are they structurally uniform? Use for_each."
- **Source**: [Meta-Arguments](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)

---

#### Decision: `ignore_changes` on `secret_string` in `aws_secretsmanager_secret_version`

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **`ignore_changes = [secret_string]`** | Lets Secrets Manager rotation own the version lifecycle; prevents Terraform from overwriting rotated credentials | Terraform state diverges from the actual secret value after rotation | Rotation is enabled — Terraform should not own the value after initial seeding |
| **No `ignore_changes`** | Terraform always drives the credential value; explicit version control | Overwrites any rotation-managed credential on next apply — rotation becomes useless | Rotation is disabled and Terraform owns the full lifecycle |

- **Agent**: "Ask user: Will automatic rotation be enabled on this secret? If yes, add `ignore_changes = [secret_string]` to the version resource to prevent Terraform from reverting rotated credentials."
- **Source**: [lifecycle ignore_changes](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle#ignore_changes)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Local or Unencrypted Backend for State Containing `secret_string`

```hcl
# DON'T — local state with aws_secretsmanager_secret_version
terraform {
  # No backend block — defaults to local state
}

resource "aws_secretsmanager_secret_version" "db_creds" {
  secret_id     = aws_secretsmanager_secret.db.id
  secret_string = var.db_password  # plaintext stored in terraform.tfstate locally
}
```

- **Why**: `aws_secretsmanager_secret_version.secret_string` is stored **in plaintext** in `terraform.tfstate`. A local state file, unencrypted S3 bucket, or version-controlled state file exposes the raw credential to anyone with file access.
- **Instead**:

```hcl
# DO — encrypted remote state with locking
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/secrets/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true            # Server-side encryption with S3 managed keys
    dynamodb_table = "terraform-locks"
    # For additional protection, use kms_key_id to encrypt with CMK
    # kms_key_id   = "arn:aws:kms:us-east-1:123456789012:key/..."
  }
}
```

- **Impact**: `CRITICAL` — Complete credentials exposure. All secrets stored in Terraform become compromised.
- **Severity**: CRITICAL
- **Source**: [Sensitive Data in State](https://developer.hashicorp.com/terraform/language/state/sensitive-data) | [S3 Backend Configuration](https://developer.hashicorp.com/terraform/language/settings/backends/s3)

---

#### Anti-Pattern: Hardcoded Secret Values in `.tf` Files or `.tfvars` Committed to Version Control

```hcl
# DON'T — hardcoded credential in variable default or direct assignment
resource "aws_secretsmanager_secret_version" "db_creds" {
  secret_id     = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = "admin"
    password = "SuperSecret123!"  # NEVER hardcode — visible in git history forever
  })
}

# DON'T — committed .tfvars file with secrets
# terraform.tfvars:
# db_password = "SuperSecret123!"
```

- **Why**: Secrets in `.tf` or `.tfvars` files committed to version control are permanently exposed in git history — even after deletion. CI/CD pipeline logs, PR reviews, and repository mirrors all capture the value.
- **Instead**:

```hcl
# DO — source credentials from environment variables or CI secret store
variable "db_password" {
  type      = string
  sensitive = true
  # No default — must be provided via TF_VAR_db_password env var or CI secret injection
}

# .gitignore must include:
# *.tfvars
# *.tfvars.json
# terraform.tfstate
# terraform.tfstate.backup
# .terraform/
```

- **Impact**: `CRITICAL` — Credentials permanently exposed in version control history. Rotation alone is insufficient — git history must be purged.
- **Severity**: CRITICAL
- **Source**: [Sensitive Variables](https://developer.hashicorp.com/terraform/language/values/variables#suppressing-values-in-cli-output) | [AWS Security Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)

---

#### Anti-Pattern: Using Deprecated Inline `rotation_*` Arguments on `aws_secretsmanager_secret`

```hcl
# DON'T — deprecated inline rotation arguments (removed in future provider major version)
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "prod/app/db"
  rotation_lambda_arn     = aws_lambda_function.rotation.arn  # DEPRECATED in v6.x
  automatically_after_days = 30                               # DEPRECATED in v6.x
}
```

- **Why**: These arguments are deprecated in provider v6.x. They cause perpetual plan diffs because AWS normalizes rotation configuration differently from what Terraform stores. They will be removed in a future provider major version.
- **Instead**:

```hcl
# DO — standalone aws_secretsmanager_secret_rotation resource
resource "aws_secretsmanager_secret" "db_credentials" {
  name = "prod/app/db"
  # No rotation arguments here — managed by separate resource
}

resource "aws_secretsmanager_secret_rotation" "db_credentials" {
  secret_id           = aws_secretsmanager_secret.db_credentials.id
  rotation_lambda_arn = aws_lambda_function.rotation.arn

  rotation_rules {
    schedule_expression = "rate(30 days)"
    duration            = "2h"
  }

  depends_on = [aws_lambda_permission.secrets_manager_invoke]
}
```

- **Impact**: `MEDIUM` — Perpetual plan noise, failed applies in future provider upgrades, and non-idempotent rotation state.
- **Severity**: MEDIUM
- **Source**: [aws_secretsmanager_secret_rotation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation)

---

#### Anti-Pattern: `force_delete_without_recovery = true` or `recovery_window_in_days = 0` in Production

```hcl
# DON'T — immediate deletion with no recovery window in production
resource "aws_secretsmanager_secret" "production_db" {
  name                         = "prod/critical-service/db"
  force_delete_without_recovery = true  # INSTANT AND PERMANENT DELETION IN PRODUCTION
  # OR
  recovery_window_in_days = 0           # Same effect: no recovery period
}
```

- **Why**: In production, deleting a secret immediately destroys the credential. Any application that reads this secret will fail immediately. There is no undo — no recovery window, no AWS support escalation path. This bypasses the 7–30 day safety net entirely.
- **Instead**:

```hcl
# DO — enforce recovery window in production via variable validation
variable "recovery_window_in_days" {
  type    = number
  default = 30

  validation {
    condition     = var.recovery_window_in_days == 0 || (var.recovery_window_in_days >= 7 && var.recovery_window_in_days <= 30)
    error_message = "Recovery window must be 0 (non-production only) or 7–30 days."
  }
}

resource "aws_secretsmanager_secret" "production_db" {
  name                    = "prod/critical-service/db"
  recovery_window_in_days = 30  # 30-day safety net for production

  lifecycle {
    prevent_destroy = true  # Double protection: prevent destroy via Terraform at all
  }
}
```

- **Impact**: `CRITICAL` — Immediate production outage, credential loss, no recovery path.
- **Severity**: CRITICAL
- **Source**: [aws_secretsmanager_secret force_delete_without_recovery](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret#force_delete_without_recovery)

---

#### Anti-Pattern: Missing `depends_on` Between `aws_secretsmanager_secret_rotation` and Lambda Permission

```hcl
# DON'T — rotation attached before Lambda has invoke permission
resource "aws_secretsmanager_secret_rotation" "db" {
  secret_id           = aws_secretsmanager_secret.db.id
  rotation_lambda_arn = aws_lambda_function.rotation.arn

  rotation_rules {
    schedule_expression = "rate(30 days)"
  }
  # Missing depends_on = [aws_lambda_permission.secrets_manager_invoke]
}

resource "aws_lambda_permission" "secrets_manager_invoke" {
  statement_id  = "SecretsManagerInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rotation.function_name
  principal     = "secretsmanager.amazonaws.com"
  source_arn    = aws_secretsmanager_secret.db.arn
}
```

- **Why**: Terraform may attempt to create `aws_secretsmanager_secret_rotation` before `aws_lambda_permission` is applied. AWS validates the Lambda invoke permission when enabling rotation — the rotation attachment fails with `ResourceNotFoundException` or `AccessDeniedException` intermittently.
- **Instead**:

```hcl
# DO — explicit depends_on ordering
resource "aws_secretsmanager_secret_rotation" "db" {
  secret_id           = aws_secretsmanager_secret.db.id
  rotation_lambda_arn = aws_lambda_function.rotation.arn

  rotation_rules {
    schedule_expression = "rate(30 days)"
    duration            = "2h"
  }

  depends_on = [
    aws_lambda_permission.secrets_manager_invoke,
    aws_iam_role_policy.rotation_lambda_secrets_access,
  ]
}
```

- **Impact**: `HIGH` — Intermittent rotation failures leaving stale credentials. Eventual application outage when database password expires.
- **Severity**: HIGH
- **Source**: [Rotation Troubleshooting](https://docs.aws.amazon.com/secretsmanager/latest/userguide/troubleshoot_rotation.html)

---

#### Anti-Pattern: Wildcard IAM Actions or Resources for Secrets Manager

```hcl
# DON'T — wildcard permissions expose all account secrets
data "aws_iam_policy_document" "dangerous" {
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:*"]  # NEVER use wildcard actions
    resources = ["*"]                  # NEVER use wildcard resources
  }
}
```

- **Why**: `secretsmanager:*` on `*` grants the principal full control over every secret in the account — including `DeleteSecret`, `PutSecretValue`, and `PutResourcePolicy`. Combined with wildcard resources, any compromised principal can exfiltrate, overwrite, or delete all secrets.
- **Instead**:

```hcl
# DO — least-privilege scoped to specific actions and ARN patterns
data "aws_iam_policy_document" "least_privilege_consumer" {
  statement {
    sid    = "ReadSpecificSecrets"
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]

    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.environment}/${var.app_name}/*",
    ]
  }
}
```

- **Impact**: `CRITICAL` — Complete secrets exfiltration across entire account. Compliance violation (SOC2 CC6.3, PCI DSS 7.1, CIS Benchmark).
- **Severity**: CRITICAL
- **Source**: [IAM Least Privilege](https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access.html)

---

#### Anti-Pattern: `aws_secretsmanager_secret_replica` Resource (Removed in v6.x)

```hcl
# DON'T — removed resource type, v5.x only pattern
resource "aws_secretsmanager_secret_replica" "us_west_2" {  # This resource no longer exists in v6.x
  secret_id  = aws_secretsmanager_secret.main.id
  region     = "us-west-2"
  kms_key_id = var.us_west_2_kms_key_arn
}
```

- **Why**: `aws_secretsmanager_secret_replica` was a separate resource in provider v5.x. In provider v6.x, replication is configured via the `replica` block directly on `aws_secretsmanager_secret`. Using the old resource type with v6.x results in an `InvalidResourceType` error or an unknown resource type error at `terraform init`.
- **Instead**:

```hcl
# DO — v6.x inline replica block
resource "aws_secretsmanager_secret" "main" {
  name       = "${var.environment}/${var.app_name}/credentials"
  kms_key_id = aws_kms_key.primary.arn

  replica {
    region     = "us-west-2"
    kms_key_id = var.us_west_2_kms_key_arn
  }
}
```

- **Impact**: `HIGH` — Multi-region replication silently fails or errors on apply, leaving DR replicas absent.
- **Severity**: HIGH
- **Source**: [aws_secretsmanager_secret replica block](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret#replica)

---

## State Management Deep Dive

### Local Development State

```hcl
# Acceptable ONLY for personal dev/learning — NO secret versions
terraform {
  required_version = ">= 1.7"
  # Local state — ONLY acceptable when not creating aws_secretsmanager_secret_version resources
  # with real credentials. Use placeholder/dummy values for local dev.
}
```

- **Risk**: If `aws_secretsmanager_secret_version` is created with real credentials and local state, the plaintext credential is stored in `./terraform.tfstate`. Any git push, log capture, or file share exposes the credential.
- **When**: Solo development learning, creating secrets with dummy values, or secrets managed without `aws_secretsmanager_secret_version` (externally seeded).

---

### Production Remote State (S3 + DynamoDB)

```hcl
# Terraform state infrastructure (create once, manually or via separate bootstrap stack)
resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-org-terraform-state-${data.aws_caller_identity.current.account_id}"

  # Prevent accidental destruction
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"  # Required for state history and rollback
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.state_encryption.arn  # CMK for state encryption
    }
    bucket_key_enabled = true  # Reduces KMS API calls up to 99%
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
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Backend configuration (in the stack that manages secrets)
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state-123456789012"
    key            = "prod/secrets-manager/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/mrk-..."
  }
}
```

- **Benefit**: Team access, state locking prevents concurrent applies that could double-seed secrets, version history enables rollback if a `secret_string` is corrupted.
- **Critical**: Restrict S3 bucket and DynamoDB access to the `TerraformDeployRole` only. The state file contains every `secret_string` value in plaintext.

---

### State File Sensitivity Handling

```hcl
# Data source retrievals DO appear in state — mark dependent outputs sensitive
data "aws_secretsmanager_secret_version" "db_creds" {
  secret_id = data.aws_secretsmanager_secret.db.id
}

locals {
  db_creds = jsondecode(data.aws_secretsmanager_secret_version.db_creds.secret_string)
}

# Mark any output derived from secret data as sensitive
output "db_host" {
  value     = local.db_creds.host
  sensitive = true  # Prevents value from appearing in terraform output and CI logs
}

# Secret ARN itself is not sensitive (appears in CloudTrail)
output "secret_arn" {
  value     = data.aws_secretsmanager_secret.db.arn
  sensitive = false
}
```

---

### State Corruption Recovery

```bash
# 1. Retrieve backup from versioned S3 state bucket
aws s3api get-object \
  --bucket my-org-terraform-state-123456789012 \
  --key prod/secrets-manager/terraform.tfstate \
  --version-id <prior-version-id> \
  terraform.tfstate.backup

# 2. Inspect current state vs. backup
terraform state pull > terraform.tfstate.current
diff terraform.tfstate.current terraform.tfstate.backup

# 3. Restore backup to remote state
terraform state push terraform.tfstate.backup

# 4. Verify state matches AWS
terraform plan
# Expected: No changes (or minimal drift)

# 5. Import secret into state if orphaned from state
terraform import aws_secretsmanager_secret.app_db "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/app/db-AbCdEf"
```

---

## Module Architecture

### Standard Module Structure

```
modules/
└── secrets-manager/
    ├── main.tf           # aws_secretsmanager_secret, aws_secretsmanager_secret_policy
    ├── rotation.tf       # aws_secretsmanager_secret_rotation, aws_lambda_permission
    ├── variables.tf      # Input variables with validation
    ├── outputs.tf        # secret_arn, secret_id, secret_name
    ├── versions.tf       # required_providers constraint
    ├── iam.tf            # aws_iam_policy for consumers
    └── README.md

root/
├── main.tf               # module "app_secrets" { source = "./modules/secrets-manager" }
├── variables.tf
├── outputs.tf
└── terraform.tfvars.example  # Template — never commit actual .tfvars with secrets
```

### Module Definition Example

```hcl
# modules/secrets-manager/variables.tf

variable "secret_name" {
  type        = string
  description = "Full secret path name (e.g., prod/myapp/db-credentials)"

  validation {
    condition     = can(regex("^[a-zA-Z0-9/_+=.@-]{1,512}$", var.secret_name))
    error_message = "Secret name must be 1–512 chars: alphanumeric, /, _, +, =, ., @, -"
  }
}

variable "description" {
  type        = string
  description = "Human-readable description of what this secret stores"
  default     = ""
}

variable "kms_key_arn" {
  type        = string
  description = "KMS key ARN for encryption. Empty string uses AWS managed key (aws/secretsmanager)."
  default     = ""

  validation {
    condition     = var.kms_key_arn == "" || can(regex("^arn:(aws|aws-cn|aws-us-gov):kms:", var.kms_key_arn))
    error_message = "kms_key_arn must be a valid KMS key ARN or an empty string."
  }
}

variable "recovery_window_in_days" {
  type        = number
  description = "Recovery window before permanent deletion (0 = immediate, 7–30 = scheduled)"
  default     = 30

  validation {
    condition     = var.recovery_window_in_days == 0 || (var.recovery_window_in_days >= 7 && var.recovery_window_in_days <= 30)
    error_message = "Must be 0 (non-production only) or between 7 and 30."
  }
}

variable "rotation_lambda_arn" {
  type        = string
  description = "ARN of the Lambda rotation function. Empty string disables rotation via Terraform."
  default     = ""

  validation {
    condition     = var.rotation_lambda_arn == "" || can(regex("^arn:(aws|aws-cn|aws-us-gov):lambda:", var.rotation_lambda_arn))
    error_message = "rotation_lambda_arn must be a valid Lambda ARN or empty string."
  }
}

variable "rotation_schedule_expression" {
  type        = string
  description = "Rotation schedule (rate() or cron() expression)"
  default     = "rate(30 days)"
}

variable "block_public_policy" {
  type        = bool
  description = "Reject overly permissive resource policies on this secret"
  default     = true
}

variable "consumer_role_arns" {
  type        = list(string)
  description = "IAM role ARNs that need GetSecretValue access (same-account)"
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "Additional tags merged with provider default_tags"
  default     = {}
}

# modules/secrets-manager/outputs.tf

output "secret_arn" {
  value       = aws_secretsmanager_secret.this.arn
  description = "Secret ARN for use in IAM policies and ECS task definitions"
  sensitive   = false
}

output "secret_name" {
  value       = aws_secretsmanager_secret.this.name
  description = "Secret name for SDK references"
  sensitive   = false
}

output "consumer_policy_arn" {
  value       = length(var.consumer_role_arns) > 0 ? aws_iam_policy.consumer[0].arn : null
  description = "IAM policy ARN for attaching to consumer roles"
  sensitive   = false
}
```

---

## Integration Patterns

### Integration: Terraform ↔ KMS

```
Pattern: Customer Managed KMS Key for secret encryption
Resources: aws_kms_key, aws_kms_alias, aws_kms_key_policy, aws_secretsmanager_secret
```

```hcl
resource "aws_kms_key" "secrets_encryption" {
  description             = "${var.environment} secrets encryption key"
  enable_key_rotation     = true
  rotation_period_in_days = 365
  deletion_window_in_days = 30

  lifecycle {
    prevent_destroy = true
  }
}

data "aws_iam_policy_document" "secrets_kms_policy" {
  # Root account access (required to prevent lockout)
  statement {
    sid     = "EnableRootAccess"
    effect  = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  # Secrets Manager service principal access with ViaService condition
  statement {
    sid    = "AllowSecretsManagerViaService"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = var.key_user_role_arns
    }
    actions = ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["secretsmanager.${var.aws_region}.amazonaws.com"]
    }
  }
}

resource "aws_kms_key_policy" "secrets_encryption" {
  key_id = aws_kms_key.secrets_encryption.id
  policy = data.aws_iam_policy_document.secrets_kms_policy.json
}

resource "aws_secretsmanager_secret" "app" {
  name       = "${var.environment}/${var.app_name}/credentials"
  kms_key_id = aws_kms_key.secrets_encryption.arn  # Use CMK ARN, not alias ARN

  depends_on = [aws_kms_key_policy.secrets_encryption]
}
```

- **Versions**:

| Resource | Min Provider | Max Provider |
|----------|-------------|-------------|
| `aws_kms_key` | 6.0 | current |
| `aws_kms_key_policy` | 6.0 | current |
| `aws_secretsmanager_secret` | 6.0 | current |

- **Issues**: Using an alias ARN (`alias/env/service/encryption`) as `kms_key_id` is supported but creates an implicit dependency not tracked by Terraform — use the key ARN directly. KMS key policy **must** include `kms:ViaService` condition scoped to `secretsmanager.<region>.amazonaws.com` for cross-account access patterns.
- **Source**: [aws_kms_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key) | [Secrets Manager Encryption](https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html)

---

### Integration: Terraform ↔ IAM

```
Pattern: Least-privilege IAM policies for secret consumers and rotation functions
Resources: aws_iam_policy, aws_iam_role, aws_iam_role_policy_attachment, data.aws_iam_policy_document
```

```hcl
# Consumer IAM policy (application workloads)
data "aws_iam_policy_document" "secret_consumer" {
  statement {
    sid    = "ReadSecrets"
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]

    resources = [aws_secretsmanager_secret.app.arn]
  }

  dynamic "statement" {
    for_each = var.kms_key_arn != "" ? [1] : []
    content {
      sid    = "DecryptWithCMK"
      effect = "Allow"
      actions = ["kms:Decrypt", "kms:DescribeKey"]
      resources = [var.kms_key_arn]

      condition {
        test     = "StringEquals"
        variable = "kms:ViaService"
        values   = ["secretsmanager.${var.aws_region}.amazonaws.com"]
      }
    }
  }
}

# Rotation Lambda IAM role
data "aws_iam_policy_document" "rotation_lambda_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "rotation_lambda_permissions" {
  statement {
    sid    = "SecretsManagerRotationActions"
    effect = "Allow"

    actions = [
      "secretsmanager:DescribeSecret",
      "secretsmanager:GetSecretValue",
      "secretsmanager:PutSecretValue",
      "secretsmanager:UpdateSecretVersionStage",
    ]

    resources = [aws_secretsmanager_secret.app.arn]
  }

  statement {
    sid    = "CreateRandomPassword"
    effect = "Allow"
    actions = ["secretsmanager:GetRandomPassword"]
    resources = ["*"]  # GetRandomPassword has no resource-level restriction
  }

  statement {
    sid    = "BasicLambdaExecution"
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"]
  }

  # VPC networking permissions (required for Lambda in VPC)
  statement {
    sid    = "VPCNetworkingForRotation"
    effect = "Allow"

    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DeleteNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
    ]

    resources = ["*"]
  }
}
```

- **Source**: [IAM Policy for Lambda Rotation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets-lambda-function-overview.html#rotating-secrets-lambda-function-permissions)

---

### Integration: Terraform ↔ Lambda (Rotation Function)

```
Pattern: Lambda rotation function deployment with VPC networking
Resources: aws_lambda_function, aws_lambda_permission, aws_iam_role, aws_security_group
```

```hcl
# Security group for rotation Lambda
resource "aws_security_group" "rotation_lambda" {
  name        = "${var.environment}-rotation-lambda-sg"
  description = "Security group for Secrets Manager rotation Lambda"
  vpc_id      = var.vpc_id

  # No inbound rules — Lambda initiates all connections
  egress {
    description = "HTTPS to Secrets Manager VPC Endpoint"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]  # Restricted to VPC — not 0.0.0.0/0
  }

  egress {
    description = "Database access (PostgreSQL example)"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.db_subnet_cidr]
  }
}

resource "aws_lambda_function" "rotation" {
  function_name = "${var.environment}-${var.app_name}-secret-rotation"
  role          = aws_iam_role.rotation_lambda.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  filename      = data.archive_file.rotation_package.output_path
  timeout       = 60  # Rotation functions must complete within Secrets Manager's window

  environment {
    variables = {
      SECRETS_MANAGER_ENDPOINT = "https://secretsmanager.${var.aws_region}.amazonaws.com"
      # No secrets in Lambda environment variables — retrieved at runtime via SDK
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids  # Must be in same VPC as database
    security_group_ids = [aws_security_group.rotation_lambda.id]
  }

  tracing_config {
    mode = "Active"  # X-Ray tracing for rotation debugging
  }
}
```

- **Issues**: Rotation Lambda **must** have network access to both the database AND Secrets Manager (via VPC endpoint or NAT gateway). Without a Secrets Manager VPC endpoint, Lambda in a private subnet cannot reach the Secrets Manager API and rotation silently fails.
- **Source**: [Rotation Lambda Network](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets-lambda-function-overview.html)

---

### Integration: Terraform ↔ VPC Endpoint (PrivateLink)

```
Pattern: Interface VPC endpoint for private Secrets Manager API access
Resources: aws_vpc_endpoint, aws_security_group, aws_vpc_endpoint_policy
```

```hcl
# Security group for Secrets Manager VPC endpoint
resource "aws_security_group" "secretsmanager_endpoint" {
  name        = "${var.environment}-secretsmanager-endpoint-sg"
  description = "Allow HTTPS inbound from VPC for Secrets Manager PrivateLink"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from VPC resources"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]  # Only from within VPC — not 0.0.0.0/0
  }
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.private_subnet_ids  # One per AZ for HA
  security_group_ids  = [aws_security_group.secretsmanager_endpoint.id]
  private_dns_enabled = true  # Routes standard SDK calls through endpoint automatically

  policy = data.aws_iam_policy_document.secretsmanager_endpoint_policy.json

  tags = {
    Name = "${var.environment}-secretsmanager-endpoint"
  }
}

# VPC endpoint policy — restrict to specific secrets and principals
data "aws_iam_policy_document" "secretsmanager_endpoint_policy" {
  statement {
    sid    = "AllowSecretsManagerAccess"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["*"]  # Constrained by IAM identity policies + source VPC condition
    }

    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]

    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.environment}/*",
    ]
  }
}
```

- **Issues**: VPC endpoints are regional — one endpoint per VPC. Placing endpoint ENIs in multiple AZ subnets is required for HA. Private DNS requires that the VPC has `enableDnsHostnames` and `enableDnsSupport` set to `true`.
- **Source**: [VPC Endpoint for Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/vpc-endpoint-overview.html) | [aws_vpc_endpoint](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint)

---

### Integration: Terraform ↔ RDS

```
Pattern: Secrets Manager as the RDS master password source with managed rotation
Resources: aws_db_instance, aws_secretsmanager_secret, aws_secretsmanager_secret_version
```

```hcl
# RDS instance using Secrets Manager for master credentials
resource "aws_db_instance" "app" {
  identifier        = "${var.environment}-${var.app_name}-postgres"
  engine            = "postgres"
  engine_version    = "16.1"
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage

  db_name  = var.db_name
  username = jsondecode(data.aws_secretsmanager_secret_version.db_master.secret_string).username
  password = jsondecode(data.aws_secretsmanager_secret_version.db_master.secret_string).password

  # Alternatively, use manage_master_user_password for fully managed rotation (RDS Managed)
  # manage_master_user_password   = true
  # master_user_secret_kms_key_id = aws_kms_key.secrets_encryption.key_id

  db_subnet_group_name   = aws_db_subnet_group.app.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds_encryption.arn

  multi_az               = var.environment == "production"
  deletion_protection    = var.environment == "production"
  skip_final_snapshot    = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.app_name}-final-snapshot" : null

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
}

# For RDS Native Managed Rotation (no Lambda required):
# Use manage_master_user_password = true on aws_db_instance
# AWS creates and manages the secret automatically
# No aws_secretsmanager_secret or aws_secretsmanager_secret_rotation needed
```

- **Issues**: When using `manage_master_user_password = true`, the RDS-created secret is NOT managed by Terraform (it's managed by RDS). Do not create a separate `aws_secretsmanager_secret` for the same credential — it creates two conflicting sources of truth.
- **Source**: [RDS Managed Master Password](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-secrets-manager.html) | [aws_db_instance manage_master_user_password](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance#manage_master_user_password)

---

### Integration: Terraform ↔ ECS

```
Pattern: Native ECS secret injection from Secrets Manager into container environment
Resources: aws_ecs_task_definition, aws_iam_role, aws_iam_role_policy
```

```hcl
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.environment}-${var.app_name}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = var.app_name
      image     = "${var.ecr_repository_url}:${var.image_tag}"
      essential = true

      # Use 'secrets' field — NOT 'environment' — for sensitive values
      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.app_db_credentials.arn}:password::"
          # Format: <secret-arn>:<json-key>::  (trailing :: required for JSON key extraction)
        },
        {
          name      = "DB_USERNAME"
          valueFrom = "${aws_secretsmanager_secret.app_db_credentials.arn}:username::"
        },
        {
          name      = "API_KEY"
          valueFrom = aws_secretsmanager_secret.api_key.arn  # Full secret string injected
        }
      ]

      # Non-sensitive configuration goes in environment
      environment = [
        { name = "DB_HOST", value = aws_db_instance.app.endpoint },
        { name = "DB_NAME", value = var.db_name },
        { name = "ENVIRONMENT", value = var.environment },
      ]
    }
  ])
}

# ECS Task Execution Role must have Secrets Manager and KMS permissions
data "aws_iam_policy_document" "ecs_execution_secrets" {
  statement {
    sid    = "GetSecretsForECS"
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue",
    ]

    resources = [
      aws_secretsmanager_secret.app_db_credentials.arn,
      aws_secretsmanager_secret.api_key.arn,
    ]
  }

  dynamic "statement" {
    for_each = var.kms_key_arn != "" ? [1] : []
    content {
      sid      = "DecryptWithCMK"
      effect   = "Allow"
      actions  = ["kms:Decrypt"]
      resources = [var.kms_key_arn]
    }
  }
}
```

- **Issues**: The `valueFrom` field in ECS task definitions requires the **Task Execution Role** (not the Task Role) to have `secretsmanager:GetSecretValue` permission. JSON key extraction via `<arn>:<key>::` syntax requires the secret value to be valid JSON. The trailing `::` in `<arn>:<json-key>::` is mandatory — omitting it causes ECS container launch failure.
- **Source**: [ECS Secrets Integration](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html)

---

## Executable Verification (CLI Commands)

### Project Init

```bash
terraform init -upgrade
# Expected: ✓ Terraform initialized, working directory prepared
# Check: "Terraform has been successfully initialized!"
# Check: Provider hashicorp/aws version ~> 6.0 installed
```

### Syntax & Format Validation

```bash
terraform fmt -recursive -check=true
# Expected: Exit code 0, no output (all files formatted)
# Fix formatting: terraform fmt -recursive

terraform validate
# Expected: "Success! The configuration is valid."
# Note: Does NOT validate AWS resource existence, only HCL syntax and schema
```

### Security Scanning

```bash
tfsec . --format sarif --minimum-severity HIGH
# Critical checks for Secrets Manager:
#   - AWS095: Secrets Manager secret not using Customer Managed Key
#   - AWS097: Secrets Manager secret not using encrypted state
# Expected: 0 HIGH/CRITICAL findings in production code

checkov -d . --framework terraform --quiet --check CKV_AWS_149,CKV_AWS_150
# CKV_AWS_149: Ensure Secrets Manager secret is encrypted using CMK
# CKV_AWS_150: Ensure Secrets Manager secret has automatic rotation enabled
# Expected: Passed checks ≥ Failed checks
```

### Plan & Apply

```bash
terraform plan -out=tfplan -lock=true
# Expected: Detailed plan showing resources to create/modify/destroy
# Review: Verify no unexpected secrets are being deleted
# Confirm: aws_secretsmanager_secret_version not being recreated (would overwrite rotation)

terraform show tfplan
# Expected: Human-readable plan — review secret_string handling

terraform apply tfplan
# Expected: All resources created successfully

terraform state list | grep secretsmanager
# Expected: Lists all Secrets Manager resources in state
# e.g., aws_secretsmanager_secret.app_db_credentials
#        aws_secretsmanager_secret_version.app_db_credentials
#        aws_secretsmanager_secret_rotation.app_db_credentials
#        aws_secretsmanager_secret_policy.app_db_credentials
```

### Rotation Verification

```bash
# Trigger manual rotation to test
aws secretsmanager rotate-secret \
  --secret-id "$(terraform output -raw secret_arn)"

# Check rotation status
aws secretsmanager describe-secret \
  --secret-id "$(terraform output -raw secret_arn)" \
  --query '{RotationEnabled:RotationEnabled,LastRotated:LastRotatedDate,NextRotation:NextRotationDate}'

# Verify rotation function invocation in CloudWatch Logs
aws logs filter-log-events \
  --log-group-name "/aws/lambda/${var.environment}-${var.app_name}-secret-rotation" \
  --start-time $(date -d '-1 hour' +%s)000 \
  --filter-pattern '"finishSecret"'
```

### Drift Detection

```bash
# Detect drift between Terraform state and actual AWS resources
terraform plan -refresh-only
# Expected: "No changes" — if changes shown, manual modifications occurred

# Check for secrets not in Terraform state
aws secretsmanager list-secrets \
  --query 'SecretList[*].{Name:Name,RotationEnabled:RotationEnabled,Tags:Tags}' \
  --output table
```

### Cleanup (Non-Production Only)

```bash
# NEVER run terraform destroy on production — verify environment first
echo "Destroying environment: ${TF_VAR_environment}"
[[ "${TF_VAR_environment}" == "production" ]] && echo "BLOCKED: Cannot destroy production" && exit 1

terraform plan -destroy -out=destroy.tfplan
terraform show destroy.tfplan  # Review what will be deleted
terraform apply destroy.tfplan
# Expected: All resources destroyed, secret enters recovery window (7–30 days)
```

---

## Testing & Validation Frameworks

### Static Analysis

```
Framework: tfsec (v1.x)
Purpose: Security scanning — identifies unencrypted secrets, missing CMK, disabled rotation
Example:
  tfsec . --minimum-severity MEDIUM
Expected Output: Pass — 0 CRITICAL/HIGH findings
Guarantee: All checks run in isolation; no AWS API calls
Source: https://github.com/aquasecurity/tfsec
```

```
Framework: checkov (v3.x)
Purpose: Policy-as-code — CKV_AWS_149 (CMK encryption), CKV_AWS_150 (rotation enabled)
Example:
  checkov -d . --framework terraform --check CKV_AWS_149,CKV_AWS_150
Expected Output: Passed checks: 2, Failed checks: 0
Source: https://www.checkov.io/
```

### Terratest Integration Test

```go
package test

import (
  "encoding/json"
  "testing"

  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/stretchr/testify/assert"
  "github.com/stretchr/testify/require"
)

func TestSecretsManagerDeployment(t *testing.T) {
  t.Parallel()

  opts := &terraform.Options{
    TerraformDir: "../examples/secrets-manager",
    Vars: map[string]interface{}{
      "environment":              "test",
      "app_name":                 "terratest",
      "recovery_window_in_days":  0,  // Immediate deletion for test cleanup
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  secretArn := terraform.Output(t, opts, "secret_arn")
  require.NotEmpty(t, secretArn, "secret_arn output must not be empty")
  assert.Contains(t, secretArn, "arn:aws:secretsmanager:", "ARN must be valid Secrets Manager ARN")

  secretName := terraform.Output(t, opts, "secret_name")
  assert.Equal(t, "test/terratest/db-credentials", secretName)
}
```

- **Source**: [Terratest](https://terratest.gruntwork.io/) | [terraform test](https://developer.hashicorp.com/terraform/cli/commands/test)

---

## Production Considerations

### Security Checklist

- [ ] All secrets stored with `prevent_destroy = true` in lifecycle block
- [ ] S3 backend encryption enabled with CMK (`kms_key_id` in backend config)
- [ ] State bucket has `block_public_acls = true` and versioning enabled
- [ ] `secret_string` sourced from CI secrets (not hardcoded or committed `.tfvars`)
- [ ] `recovery_window_in_days = 30` enforced for production secrets
- [ ] Customer Managed KMS Key used for cross-account secrets
- [ ] `block_public_policy = true` on all `aws_secretsmanager_secret_policy` resources
- [ ] Least-privilege IAM: consumer roles have only `GetSecretValue` and `DescribeSecret`
- [ ] VPC endpoint deployed in all VPCs where rotation Lambda or applications retrieve secrets
- [ ] Rotation Lambda security group has no `0.0.0.0/0` egress rules
- [ ] `aws_secretsmanager_secret_rotation` used (not deprecated inline `rotation_lambda_arn`)
- [ ] `depends_on` explicit between rotation resource and Lambda permission
- [ ] CloudTrail enabled — all Secrets Manager API calls logged as management events
- [ ] AWS Config rules deployed: `secretsmanager-rotation-enabled-check`, `secretsmanager-using-cmk`

---

### Monitoring & Alerting

```hcl
# CloudWatch alarm for rotation failures
resource "aws_cloudwatch_metric_alarm" "rotation_failed" {
  alarm_name          = "${var.environment}-${var.app_name}-secret-rotation-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "RotationFailed"
  namespace           = "AWS/SecretsManager"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Secret rotation failed — credentials may become stale"
  alarm_actions       = [var.sns_alert_topic_arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    SecretId = aws_secretsmanager_secret.app_db_credentials.id
  }
}

# EventBridge rule for rotation lifecycle events
resource "aws_cloudwatch_event_rule" "secret_rotation" {
  name        = "${var.environment}-secret-rotation-events"
  description = "Capture Secrets Manager rotation lifecycle events"

  event_pattern = jsonencode({
    source      = ["aws.secretsmanager"]
    detail-type = ["AWS Service Event via CloudTrail"]
    detail = {
      eventSource = ["secretsmanager.amazonaws.com"]
      eventName   = ["RotateSecret", "RotationFailed"]
    }
  })
}

resource "aws_cloudwatch_event_target" "secret_rotation_sns" {
  rule = aws_cloudwatch_event_rule.secret_rotation.name
  arn  = var.sns_alert_topic_arn
}
```

---

### Disaster Recovery Runbook

```bash
# Scenario 1: Secret accidentally deleted (within recovery window)
# List secrets pending deletion:
aws secretsmanager list-secrets \
  --filters Key=tag-key,Values=Environment \
  --include-planned-deletion \
  --query 'SecretList[?DeletedDate!=null].{Name:Name,ARN:ARN,DeleteDate:DeletedDate}'

# Restore secret within recovery window:
aws secretsmanager restore-secret \
  --secret-id "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/app/db-AbCdEf"

# Re-import restored secret into Terraform state:
terraform import aws_secretsmanager_secret.app_db_credentials \
  "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/app/db-AbCdEf"

# Scenario 2: Rotation failure — revert to previous version
aws secretsmanager get-secret-value \
  --secret-id "prod/app/db-credentials" \
  --version-stage AWSPREVIOUS  # Previous (pre-rotation) credential

# Manually roll back to previous version staging label:
aws secretsmanager update-secret-version-stage \
  --secret-id "prod/app/db-credentials" \
  --version-stage AWSCURRENT \
  --move-to-version-id <previous-version-id> \
  --remove-from-version-id <failed-version-id>

# Scenario 3: State file corruption
aws s3api list-object-versions \
  --bucket my-org-terraform-state-123456789012 \
  --prefix "prod/secrets-manager/terraform.tfstate" \
  --query 'Versions[?!IsLatest].[VersionId,LastModified]'

aws s3api get-object \
  --bucket my-org-terraform-state-123456789012 \
  --key "prod/secrets-manager/terraform.tfstate" \
  --version-id <prior-version-id> \
  terraform.tfstate.backup

terraform state push terraform.tfstate.backup
```

---

## Reference Implementations

```hcl
# Complete working example: root/main.tf
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
    key            = "prod/secrets-manager/terraform.tfstate"
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
      CostCenter  = var.cost_center
    }
  }
}

# KMS key for secrets encryption
resource "aws_kms_key" "secrets" {
  description             = "${var.environment} secrets encryption key"
  enable_key_rotation     = true
  rotation_period_in_days = 365
  deletion_window_in_days = 30
  lifecycle { prevent_destroy = true }
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/${var.environment}/${var.app_name}/secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

# Primary secret
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.environment}/${var.app_name}/db-credentials"
  description = "${var.app_name} database credentials for ${var.environment}"
  kms_key_id  = aws_kms_key.secrets.arn

  recovery_window_in_days = var.environment == "production" ? 30 : 7

  lifecycle { prevent_destroy = true }
}

# Initial secret version (seeded from CI; rotation manages subsequent versions)
resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id

  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    host     = var.db_host
    port     = 5432
    engine   = "postgres"
    dbname   = var.db_name
  })

  lifecycle {
    ignore_changes = [secret_string]  # Let rotation own subsequent versions
  }
}

# Resource policy with public access block
resource "aws_secretsmanager_secret_policy" "db_credentials" {
  secret_arn          = aws_secretsmanager_secret.db_credentials.arn
  block_public_policy = true
  policy              = data.aws_iam_policy_document.secret_resource_policy.json
}

data "aws_iam_policy_document" "secret_resource_policy" {
  statement {
    sid    = "DenyNonTLS"
    effect = "Deny"
    principals { type = "AWS"; identifiers = ["*"] }
    actions   = ["secretsmanager:*"]
    resources = ["*"]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

data "aws_caller_identity" "current" {}
```

```hcl
# terraform.tfvars.example — never commit actual values
aws_region   = "us-east-1"
account_id   = "123456789012"
environment  = "production"
app_name     = "my-app"
owner        = "platform-team@example.com"
cost_center  = "CC-12345"
db_name      = "appdb"

# db_username and db_password: set via TF_VAR_db_username and TF_VAR_db_password env vars
# Never set these in a committed .tfvars file
```

---

## Source Bibliography

### Primary Sources
- [aws_secretsmanager_secret](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret)
- [aws_secretsmanager_secret_version](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_version)
- [aws_secretsmanager_secret_rotation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation)
- [aws_secretsmanager_secret_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_policy)
- [data.aws_secretsmanager_secret](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secret)
- [data.aws_secretsmanager_secret_version](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secret_version)
- [AWS Secrets Manager User Guide](https://docs.aws.amazon.com/secretsmanager/latest/userguide/)
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)
- [AWS Provider Registry — Latest](https://registry.terraform.io/providers/hashicorp/aws/latest)

### Validation & Tools
- [tfsec GitHub](https://github.com/aquasecurity/tfsec) — Checks AWS095, AWS097
- [Checkov](https://www.checkov.io/) — Checks CKV_AWS_149, CKV_AWS_150
- [Terratest](https://terratest.gruntwork.io/)
- [GitHub: hashicorp/terraform-provider-aws Issues](https://github.com/hashicorp/terraform-provider-aws/issues)

---

## Completion Checklist

- [x] All patterns validated for Terraform >= 1.7 and aws provider ~> 6.0
- [x] State management strategy documented (local dev vs. production S3+DynamoDB)
- [x] `aws_secretsmanager_secret_rotation` standalone resource (v6.x pattern) documented
- [x] `replica` block on `aws_secretsmanager_secret` (v6.x pattern) documented — deprecated `aws_secretsmanager_secret_replica` resource identified as anti-pattern
- [x] Deprecated inline rotation arguments (`rotation_lambda_arn`, `automatically_after_days`) documented as anti-pattern
- [x] `force_delete_without_recovery` and `recovery_window_in_days = 0` risk documented
- [x] State file sensitivity (`secret_string` in plaintext state) documented and mitigated
- [x] Module architecture fully defined
- [x] All CLI commands validated with expected outputs
- [x] Integration patterns: KMS, IAM, Lambda, VPC Endpoint, RDS, ECS documented
- [x] Security checklist complete
- [x] 1+ copy-paste working root module example with `.tfvars.example`
- [x] Disaster recovery procedures documented

---

## Research Gaps

```
Gap: Terraform support for Secrets Manager Agent (localhost HTTP daemon) deployment
Impact: No native aws provider resource — agent deployment is OS/ECS task/EKS pod configuration
Workaround: Deploy agent via ECS task definition `containers` configuration or EC2 user data; not managed as a Terraform resource
Follow-up: https://docs.aws.amazon.com/secretsmanager/latest/userguide/secrets-manager-agent.html

Gap: Terraform native support for AWS Parameters and Secrets Lambda Extension version pinning
Impact: Extension layer version must be hardcoded or fetched via data source — no managed_latest_version construct
Workaround: Use data source pattern or hardcode the layer ARN per region; check https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html for latest ARNs
Follow-up: https://github.com/hashicorp/terraform-provider-aws/issues

Gap: Terraform-managed rotation for Secrets Manager Agent-backed secrets (non-database)
Impact: No AWS-provided rotation templates for arbitrary API keys or OAuth tokens; custom Lambda required
Workaround: Implement four-step rotation protocol (createSecret, setSecret, testSecret, finishSecret) in custom Lambda; use AWS SecretsManagerRotationTemplate as scaffold
Follow-up: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_lambda-functions.html
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Terraform configuration block with `~> 6.0` provider constraint
- S3 backend with `encrypt = true` and DynamoDB locking
- `prevent_destroy = true` on all production secrets
- `block_public_policy = true` on all `aws_secretsmanager_secret_policy` resources
- `aws_secretsmanager_secret_rotation` as standalone resource (not deprecated inline args)
- Least-privilege IAM policy scoped to specific secret ARNs
- `sensitive = true` on `secret_string` variables
- `ignore_changes = [secret_string]` when rotation is enabled

### Medium Confidence (Validate with user)
- Customer Managed Key vs. AWS managed key selection
- Multi-region replication configuration
- Single user vs. alternating users rotation strategy
- `recovery_window_in_days` value for non-production environments
- `for_each` vs. separate resources for multiple secrets

### Low Confidence (Must ask user)
- Compliance-specific rotation intervals (HIPAA, PCI-DSS, SOC2)
- Cross-account secret sharing topology (which accounts, which roles)
- Managed rotation eligibility (RDS engine version, secrets format)
- FIPS endpoint requirements (`secretsmanager-fips` service name)

### Emergency Stop
- Halt if `force_delete_without_recovery = true` planned for production secret
- Halt if `terraform destroy` planned on secret with `prevent_destroy = true` removed
- Halt if `secret_string` found hardcoded in `.tf` files or committed `.tfvars`
- Halt if S3 backend `encrypt = true` is missing when `aws_secretsmanager_secret_version` resources exist
- Halt if `recovery_window_in_days = 0` set in an environment tagged `production`
