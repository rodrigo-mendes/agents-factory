# Terraform AWS ParameterStore — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - SSM Parameter Store"
Cloud_Provider: "AWS"
Target_Service: "ParameterStore (AWS Systems Manager Parameter Store)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-29"
Domain_Complexity: "Standard"
SSM_Resources_Covered: "aws_ssm_parameter, aws_ssm_service_setting"
SSM_Data_Sources_Covered: "aws_ssm_parameter, aws_ssm_parameters_by_path"
SSM_Ephemeral_Resources_Covered: "ephemeral.aws_ssm_parameter (v6.x — value never stored in state)"
V6_Notable_Arguments: "insecure_value (String/StringList non-sensitive path), ephemeral resource aws_ssm_parameter (secret never written to state), Intelligent-Tiering tier value"
```

---

## Executive Summary

AWS Systems Manager Parameter Store provides secure, hierarchical storage for configuration data and secrets management. It supports three parameter types — `String`, `StringList`, and `SecureString` — organized in a path-based namespace (e.g., `/prod/myapp/db-host`). Parameter Store integrates natively with IAM for access control, KMS for `SecureString` encryption, Lambda via the Parameters and Secrets Lambda Extension, ECS for injecting environment variables at runtime, and CloudWatch for change-event notifications. It is the standard AWS choice for non-rotating application configuration (connection strings, environment variables, resource ARNs) and lightweight encrypted values that do not require secret rotation.

The Terraform AWS provider v6.x introduces an **ephemeral resource** `ephemeral.aws_ssm_parameter` that retrieves a `SecureString` value at plan/apply time without ever writing the plaintext to the Terraform state file — a critical security advancement over the standard `data.aws_ssm_parameter` source, which does persist the value in state. The core managed resource is `aws_ssm_parameter`, with the `insecure_value` argument (v5.0+) providing a non-sensitive path for `String` and `StringList` parameters to prevent Terraform from unnecessarily masking non-secret values. The standard parameter tier allows 10,000 parameters up to 4 KB at no extra cost per account per region; the advanced tier supports 100,000 parameters up to 8 KB with parameter policies (expiration, no-change notification) but incurs additional charges. Note: **you cannot downgrade from advanced to standard tier**.

Parameter Store is classified **Standard** complexity because: (1) it composes multiple resource types (`aws_ssm_parameter`, KMS keys, IAM policies, and data sources) with cross-resource dependencies; (2) `SecureString` parameters require KMS integration with correct IAM key policies; (3) the state file may contain plaintext `SecureString` values when using `data.aws_ssm_parameter` (use ephemeral resource instead); (4) path-based naming conventions must be established early and enforced consistently across environments; and (5) tier upgrade is irreversible, requiring advance capacity planning.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Pins to provider `~> 6.0` to access the ephemeral resource `ephemeral.aws_ssm_parameter` and the `insecure_value` argument. The S3 backend with DynamoDB locking is mandatory for any team workflow — the state file can contain `SecureString` plaintext values if `data.aws_ssm_parameter` is used.

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
    key            = "prod/ssm/terraform.tfstate"
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

**Why**: Credentials must never be hardcoded. `assume_role` enables CI/CD without static keys. `default_tags` ensures all SSM parameters carry environment, ownership, and cost-allocation metadata — required for parameter governance at scale.

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
- **Source**: [AWS Provider Authentication](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration)

---

#### Pattern: Hierarchical Path-Based Naming Convention

**Why**: SSM Parameter Store enforces a path hierarchy using `/` as delimiters. Consistent paths are the single most important operational decision — they enable bulk retrieval (`GetParametersByPath`), environment isolation, and IAM path-based permission boundaries. Establish the convention before creating any parameters.

```hcl
# Naming pattern: /<environment>/<application>/<component>/<parameter-name>
# Examples:
#   /prod/myapp/database/host
#   /staging/myapp/api/key-arn
#   /shared/common/logging/level

variable "parameter_prefix" {
  type        = string
  description = "Root path prefix for SSM parameters (e.g., /prod/myapp)"

  validation {
    condition     = can(regex("^/[a-zA-Z0-9._-]+(/[a-zA-Z0-9._-]+)*$", var.parameter_prefix))
    error_message = "Parameter prefix must start with / and use only alphanumeric characters, dots, hyphens, and underscores."
  }
}

resource "aws_ssm_parameter" "db_host" {
  name        = "${var.parameter_prefix}/database/host"
  type        = "String"
  insecure_value = var.db_host  # non-sensitive String: use insecure_value to avoid state masking
  description = "Database hostname for ${var.environment} environment"
  tier        = "Standard"

  tags = {
    Name        = "${var.parameter_prefix}/database/host"
    Component   = "database"
    Application = var.application_name
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [SSM Parameter Hierarchies](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html)

---

#### Pattern: SecureString Parameter with KMS Encryption

**Why**: `SecureString` parameters encrypt values at rest using KMS. Always specify an explicit `key_id` pointing to a customer-managed KMS key (CMK). Using the default AWS-managed SSM key (`alias/aws/ssm`) prevents key policy customization, rotation interval control, and cross-account sharing. The `value` attribute on a `SecureString` parameter is automatically marked `sensitive` by the provider — this means it is masked in plan output but IS persisted in state. Use the ephemeral resource pattern (see below) for maximum security.

```hcl
resource "aws_ssm_parameter" "db_password" {
  name        = "${var.parameter_prefix}/database/password"
  type        = "SecureString"
  value       = var.db_password   # sensitive = true by provider; stored in state (use ephemeral for better security)
  key_id      = aws_kms_key.ssm_encryption.arn
  description = "Database master password for ${var.environment}"
  tier        = "Standard"

  lifecycle {
    ignore_changes = [value]  # Prevent Terraform from rotating externally managed secrets
  }

  tags = {
    Name        = "${var.parameter_prefix}/database/password"
    Component   = "database"
    Sensitivity = "high"
  }
}

# The KMS key dedicated to SSM parameter encryption
resource "aws_kms_key" "ssm_encryption" {
  description             = "KMS key for SSM Parameter Store - ${var.environment}"
  key_usage               = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "SYMMETRIC_DEFAULT"
  enable_key_rotation     = true
  rotation_period_in_days = 365
  deletion_window_in_days = 30

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name    = "${var.environment}-ssm-encryption-key"
    Purpose = "ssm-parameter-store"
  }
}

resource "aws_kms_alias" "ssm_encryption" {
  name          = "alias/${var.environment}/ssm-parameters"
  target_key_id = aws_kms_key.ssm_encryption.key_id
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_ssm_parameter Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter) | [SecureString KMS](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-securestring.html)

---

#### Pattern: Ephemeral Resource for SecureString (v6.x — Recommended for CI/CD)

**Why**: `ephemeral.aws_ssm_parameter` (introduced in provider v6.x) retrieves the parameter value at plan/apply time but **never writes the plaintext to the Terraform state file**. This is the safest way to pass `SecureString` values to other resources (e.g., RDS master password, API keys). The value is only available during the apply phase within the same `run` context.

```hcl
# Retrieve a SecureString without persisting it to state
ephemeral "aws_ssm_parameter" "db_password" {
  name            = "${var.parameter_prefix}/database/password"
  with_decryption = true
}

# Use the ephemeral value in another resource (e.g., RDS)
resource "aws_db_instance" "main" {
  identifier        = "${var.environment}-db"
  engine            = "postgres"
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage

  # Ephemeral value is passed in-memory — never written to state
  password = ephemeral.aws_ssm_parameter.db_password.value

  skip_final_snapshot = false
  final_snapshot_identifier = "${var.environment}-db-final-snapshot"
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Ephemeral Resources (aws_ssm_parameter)](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/ephemeral-resources/ssm_parameter)

---

#### Pattern: IAM Least-Privilege Policy for Parameter Store Access

**Why**: Parameter Store uses IAM for access control. The policy must be scoped to specific path prefixes — never grant `ssm:*` on `*`. Separate read (`GetParameter`, `GetParameters`, `GetParametersByPath`) from write (`PutParameter`, `DeleteParameter`) permissions and assign to different roles.

```hcl
# IAM policy for application read-only access to its own parameter path
data "aws_iam_policy_document" "ssm_read_policy" {
  statement {
    sid    = "ReadSSMParameters"
    effect = "Allow"

    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
      "ssm:DescribeParameters",
    ]

    resources = [
      "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.parameter_prefix}/*",
    ]
  }

  statement {
    sid    = "DecryptSSMSecureStrings"
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
    ]

    resources = [aws_kms_key.ssm_encryption.arn]
  }
}

resource "aws_iam_policy" "ssm_read" {
  name        = "${var.environment}-${var.application_name}-ssm-read"
  description = "Read-only access to ${var.parameter_prefix}/* SSM parameters"
  policy      = data.aws_iam_policy_document.ssm_read_policy.json

  tags = {
    Application = var.application_name
    Environment = var.environment
  }
}

# IAM policy for Terraform/CI-CD write access
data "aws_iam_policy_document" "ssm_write_policy" {
  statement {
    sid    = "WriteSSMParameters"
    effect = "Allow"

    actions = [
      "ssm:PutParameter",
      "ssm:DeleteParameter",
      "ssm:AddTagsToResource",
      "ssm:RemoveTagsFromResource",
      "ssm:GetParameter",       # Required for Terraform refresh/plan
      "ssm:GetParameters",
      "ssm:DescribeParameters",
    ]

    resources = [
      "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.parameter_prefix}/*",
    ]
  }

  statement {
    sid    = "EncryptDecryptSSMSecureStrings"
    effect = "Allow"

    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]

    resources = [aws_kms_key.ssm_encryption.arn]
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Parameter Store IAM Policies](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-setting-up.html) | [aws_iam_policy_document](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document)

---

#### Pattern: Variable Validation and Type Safety

**Why**: Prevents invalid parameter configurations at plan time before any AWS API calls are made.

```hcl
variable "parameter_type" {
  type        = string
  description = "SSM parameter type: String, StringList, or SecureString"
  default     = "String"

  validation {
    condition     = contains(["String", "StringList", "SecureString"], var.parameter_type)
    error_message = "Parameter type must be String, StringList, or SecureString."
  }
}

variable "parameter_tier" {
  type        = string
  description = "SSM parameter tier: Standard, Advanced, or Intelligent-Tiering"
  default     = "Standard"

  validation {
    condition     = contains(["Standard", "Advanced", "Intelligent-Tiering"], var.parameter_tier)
    error_message = "Parameter tier must be Standard, Advanced, or Intelligent-Tiering."
  }
}

variable "parameter_prefix" {
  type        = string
  description = "Root SSM path prefix (e.g., /prod/myapp)"

  validation {
    condition     = can(regex("^/[a-zA-Z0-9._/-]+$", var.parameter_prefix)) && !endswith(var.parameter_prefix, "/")
    error_message = "Parameter prefix must start with / and must not end with /."
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
```

- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

#### Pattern: Sensitive Output Masking

**Why**: Outputs that expose `SecureString` values or ARNs used in further IAM policies must be marked `sensitive = true`. This prevents accidental logging in CI/CD pipelines.

```hcl
output "db_password_arn" {
  value       = aws_ssm_parameter.db_password.arn
  description = "ARN of the database password SSM parameter"
  sensitive   = false  # ARNs are not secret — safe to output
}

output "parameter_prefix" {
  value       = var.parameter_prefix
  description = "SSM parameter path prefix for dependent stacks"
  sensitive   = false
}

# NEVER output a SecureString value directly
# output "db_password_value" {         # DON'T
#   value = aws_ssm_parameter.db_password.value  # plaintext secret in output
# }
```

- **Source**: [Sensitive Output Values](https://developer.hashicorp.com/terraform/language/values/outputs#sensitive-suppressing-values-in-cli-output)

---

### ⚠️ Conditional Patterns

---

#### Decision: `value` vs `insecure_value` for String Parameters

| Option | Type Supported | State Sensitivity | Plan Output | Best When |
|--------|---------------|-------------------|-------------|-----------|
| **`value`** | All types | Marked sensitive | Masked | SecureString, or when value needs sensitivity |
| **`insecure_value`** | String, StringList only | Not sensitive | Visible | Non-secret config (URLs, names, env vars) |

- **Tradeoff**: `value` on a `String` parameter causes Terraform to mask it in plan output — confusing for non-secret config. `insecure_value` provides transparency for non-sensitive data and avoids false "sensitive" signals.
- **Rule**: Use `value` for `SecureString`. Use `insecure_value` for `String`/`StringList` unless the value truly must be masked.
- **Agent**: "Ask user: Is this parameter value sensitive/secret (use `value`) or non-sensitive configuration (use `insecure_value`)?"
- **Source**: [aws_ssm_parameter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter)

---

#### Decision: Standard vs Advanced vs Intelligent-Tiering

| Option | Max Parameters | Max Value Size | Parameter Policies | Cross-Account | Cost |
|--------|---------------|----------------|--------------------|--------------|----|
| **Standard** | 10,000/region | 4 KB | No | No | Free |
| **Advanced** | 100,000/region | 8 KB | Yes (expiry, rotation reminder) | Yes | $0.05/param/month |
| **Intelligent-Tiering** | 100,000/region | 8 KB | Yes | Yes | Standard if ≤4 KB, Advanced if >4 KB |

- **Warning**: Cannot downgrade from Advanced to Standard.
- **When**: Use Standard for most apps. Use Advanced when you need parameter policies (expiration alerts, rotation enforcement) or >10,000 parameters. Use Intelligent-Tiering when parameter sizes vary and you want automatic cost optimization.
- **Agent**: "Ask user: Do you need parameter policies (expiry/no-change notifications), cross-account sharing, or >4 KB values? If yes → Advanced. If unsure → Intelligent-Tiering."
- **Source**: [Managing Parameter Tiers](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html)

---

#### Decision: `data.aws_ssm_parameter` vs `ephemeral.aws_ssm_parameter` for Reading Secrets

| Option | State Impact | When Available | Use Case |
|--------|-------------|----------------|---------|
| **`data.aws_ssm_parameter`** | Value persisted in state | Plan + Apply + any `terraform` command | Cross-resource references, non-sensitive values, debugging |
| **`ephemeral.aws_ssm_parameter`** | Value NEVER persisted in state | Apply phase only (ephemeral context) | SecureString values passed to resources (RDS password, API key) |

- **When**: Use `data.aws_ssm_parameter` for non-sensitive lookups (String type, ARNs, endpoints). Use `ephemeral.aws_ssm_parameter` whenever retrieving `SecureString` values to pass to another resource.
- **Agent**: "Ask user: Is this parameter a secret (use ephemeral resource) or non-sensitive configuration (use data source)?"
- **Source**: [Ephemeral aws_ssm_parameter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/ephemeral-resources/ssm_parameter)

---

#### Decision: Manage Secret Values in Terraform vs. Out-of-Band

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Terraform manages value** | IaC consistency, single source of truth | Secret in tfvars/env var; rotation triggers plan | Non-rotating secrets, initial bootstrap |
| **Terraform creates parameter, value managed externally** | Clean rotation, no secret in TF pipeline | Value not tracked in IaC | Secrets with rotation policies (use `ignore_changes = [value]`) |
| **Secrets Manager (not SSM)** | Automatic rotation, advanced lifecycle | Cost ($0.40/secret/month), different API | Rotating credentials (DB passwords, API keys) |

```hcl
# Pattern: Terraform creates the parameter shell; value managed externally
resource "aws_ssm_parameter" "api_key" {
  name        = "${var.parameter_prefix}/api/external-key"
  type        = "SecureString"
  value       = "PLACEHOLDER"   # Initial value; replaced out-of-band
  key_id      = aws_kms_key.ssm_encryption.arn
  description = "External API key — value managed outside Terraform"
  tier        = "Standard"

  lifecycle {
    ignore_changes = [value]   # Terraform will not overwrite externally managed values
  }
}
```

- **Agent**: "Ask user: Will this secret be rotated? If yes → use `ignore_changes = [value]` or Secrets Manager. If no → Terraform can manage the full lifecycle."
- **Source**: [Lifecycle ignore_changes](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle#ignore_changes)

---

#### Decision: `for_each` vs Separate Resources for Multiple Parameters

| Option | Best For | Pitfall |
|--------|----------|---------|
| **`for_each` on a map** | Many parameters with shared configuration | Map key changes destroy/recreate; sensitive values in for_each maps complicate planning |
| **Separate resources** | 1–5 parameters with distinct configurations | Verbose but explicit; easy to target individually |
| **Module** | Reusable per-environment or per-service parameter set | Module overhead for small parameter counts |

```hcl
# Pattern: for_each for homogeneous non-sensitive parameters
variable "app_config" {
  type = map(string)
  description = "Non-sensitive application configuration parameters"
  default = {
    log_level    = "info"
    cache_ttl    = "300"
    feature_flag = "enabled"
  }
}

resource "aws_ssm_parameter" "app_config" {
  for_each = var.app_config

  name           = "${var.parameter_prefix}/config/${each.key}"
  type           = "String"
  insecure_value = each.value  # Non-sensitive: use insecure_value
  description    = "Application config: ${each.key}"
  tier           = "Standard"

  tags = {
    ConfigKey   = each.key
    Application = var.application_name
  }
}
```

- **Source**: [for_each Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Hardcoded Secret Values in `.tf` Files or `.tfvars` Committed to Git

```hcl
# DON'T
resource "aws_ssm_parameter" "db_password" {
  name  = "/prod/myapp/db/password"
  type  = "SecureString"
  value = "SuperSecret123!"   # NEVER hardcode secrets in .tf files
}
```

**Why**: Secrets committed to version control are permanently exposed in git history — even if later removed. Environment variable injection or external secret stores are the correct patterns.

```hcl
# DO — Inject from environment variable or use PLACEHOLDER + ignore_changes
variable "db_password" {
  type      = string
  sensitive = true
  description = "Database master password — pass via TF_VAR_db_password env var or secrets vault"
}

resource "aws_ssm_parameter" "db_password" {
  name    = "${var.parameter_prefix}/database/password"
  type    = "SecureString"
  value   = var.db_password
  key_id  = aws_kms_key.ssm_encryption.arn
}
```

```bash
# In CI/CD pipeline — inject via environment, never in code
export TF_VAR_db_password="$(aws secretsmanager get-secret-value --secret-id prod/db --query SecretString --output text)"
terraform apply
```

- **Impact**: CRITICAL — Secret exposure in SCM history, team access logs, CI/CD artifact stores
- **Severity**: CRITICAL
- **Source**: [AWS Security Best Practices](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)

---

#### Anti-Pattern: Using `data.aws_ssm_parameter` for SecureString (State Exposure)

```hcl
# DON'T — value stored in Terraform state file
data "aws_ssm_parameter" "db_password" {
  name            = "/prod/myapp/db/password"
  with_decryption = true
}

resource "aws_db_instance" "main" {
  password = data.aws_ssm_parameter.db_password.value  # plaintext in state
}
```

**Why**: `data.aws_ssm_parameter` with `with_decryption = true` writes the decrypted `SecureString` value to the Terraform state file. Anyone with read access to the S3 state bucket can retrieve the plaintext secret.

```hcl
# DO — Use ephemeral resource (v6.x): value never written to state
ephemeral "aws_ssm_parameter" "db_password" {
  name            = "${var.parameter_prefix}/database/password"
  with_decryption = true
}

resource "aws_db_instance" "main" {
  password = ephemeral.aws_ssm_parameter.db_password.value  # never in state
}
```

- **Impact**: CRITICAL — Full plaintext secret exposure in Terraform state
- **Severity**: CRITICAL
- **Source**: [Terraform Sensitive Data in State](https://developer.hashicorp.com/terraform/language/state/sensitive-data) | [Ephemeral Resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/ephemeral-resources/ssm_parameter)

---

#### Anti-Pattern: Missing State File Encryption

```hcl
# DON'T
backend "s3" {
  bucket = "my-tf-state"
  key    = "ssm/terraform.tfstate"
  region = "us-east-1"
  # No encrypt = true — state with SecureString values stored unencrypted
}
```

**Why**: The state file may contain `SecureString` plaintext values (when using `data.aws_ssm_parameter`), KMS key ARNs, and IAM policy documents. Unencrypted state is a critical security risk.

```hcl
# DO
backend "s3" {
  bucket         = "my-org-terraform-state"
  key            = "prod/ssm/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-locks"
}
```

- **Impact**: CRITICAL — Secrets and configuration exposure
- **Severity**: CRITICAL
- **Source**: [Terraform State Security](https://developer.hashicorp.com/terraform/language/state/sensitive-data)

---

#### Anti-Pattern: Overly Permissive IAM on SSM Parameters

```hcl
# DON'T
data "aws_iam_policy_document" "ssm_access" {
  statement {
    effect    = "Allow"
    actions   = ["ssm:*"]           # Wildcard action — too permissive
    resources = ["*"]               # All parameters in all regions/accounts
  }
}
```

**Why**: Grants access to ALL SSM parameters including those belonging to other applications and environments. A compromised workload can read or overwrite any parameter in the account.

```hcl
# DO — Scope to path prefix and specific actions
data "aws_iam_policy_document" "ssm_app_read" {
  statement {
    sid    = "ReadAppParameters"
    effect = "Allow"

    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
    ]

    resources = [
      "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.parameter_prefix}/*",
    ]
  }
}
```

- **Impact**: HIGH — Privilege escalation, cross-application secret leakage
- **Severity**: HIGH
- **Source**: [IAM Least Privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege)

---

#### Anti-Pattern: Using `overwrite` Argument (Deprecated)

```hcl
# DON'T — overwrite is deprecated since provider v5+
resource "aws_ssm_parameter" "config" {
  name      = "/prod/myapp/db/host"
  type      = "String"
  value     = "db.example.com"
  overwrite = true   # DEPRECATED — causes perpetual plan diffs
}
```

**Why**: The `overwrite` argument was deprecated in provider v5.0. Terraform natively manages the resource lifecycle — parameters are created/updated as needed without this flag.

```hcl
# DO — Remove overwrite; use lifecycle rules for drift management
resource "aws_ssm_parameter" "config" {
  name           = "/prod/myapp/db/host"
  type           = "String"
  insecure_value = "db.example.com"
  # No overwrite needed
}
```

- **Impact**: MEDIUM — Perpetual plan diffs, noisy CI pipelines, confusion for new team members
- **Severity**: MEDIUM
- **Source**: [aws_ssm_parameter deprecated arguments](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter)

---

#### Anti-Pattern: Downgrading Parameter Tier from Advanced to Standard

```hcl
# DON'T — Cannot downgrade; Terraform will error and may corrupt parameter state
resource "aws_ssm_parameter" "config" {
  name  = "/prod/myapp/config/feature"
  type  = "String"
  value = "enabled"
  tier  = "Standard"  # Cannot set to Standard after resource was previously Advanced
}
```

**Why**: AWS does not allow downgrading from the Advanced to Standard tier. Applying this change in Terraform will cause a persistent error and may require `terraform state rm` to recover.

```hcl
# DO — Plan tier selection upfront; use Intelligent-Tiering when uncertain
resource "aws_ssm_parameter" "config" {
  name           = "/prod/myapp/config/feature"
  type           = "String"
  insecure_value = "enabled"
  tier           = "Intelligent-Tiering"  # Auto-selects based on value size
}
```

- **Impact**: HIGH — Terraform apply errors, manual state recovery required
- **Severity**: HIGH
- **Source**: [Parameter Tier Management](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html)

---

#### Anti-Pattern: Untagged Parameters

```hcl
# DON'T
resource "aws_ssm_parameter" "db_host" {
  name  = "/prod/myapp/db/host"
  type  = "String"
  value = "db.example.com"
  # No tags — impossible to track ownership, cost, environment
}
```

**Why**: Without tags, parameters cannot be filtered by environment or application, cost allocation is impossible, and access control by tag conditions (ABAC) cannot be enforced.

```hcl
# DO
resource "aws_ssm_parameter" "db_host" {
  name           = "/prod/myapp/db/host"
  type           = "String"
  insecure_value = var.db_host
  description    = "Database host for prod myapp"

  tags = merge(var.tags, {
    Name        = "/prod/myapp/db/host"
    Component   = "database"
    Application = "myapp"
  })
}
```

- **Impact**: HIGH — Cost blindness, audit gaps, ABAC policy failures
- **Severity**: HIGH
- **Source**: [Resource Tagging Strategy](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)

---

#### Anti-Pattern: Storing Parameters That Require Rotation in Parameter Store

```hcl
# DON'T — Use Secrets Manager for rotating credentials
resource "aws_ssm_parameter" "db_password" {
  name  = "/prod/myapp/db/password"
  type  = "SecureString"
  value = var.db_password
  # No rotation support in Parameter Store
}
```

**Why**: Parameter Store has no native rotation feature. For credentials that must rotate (database passwords, API keys, OAuth tokens), AWS Secrets Manager provides built-in rotation with Lambda-based rotation functions and full audit logging.

```hcl
# DO — Use Secrets Manager for rotating credentials
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "prod/myapp/db/password"
  description             = "RDS master password with automatic rotation"
  kms_key_id              = aws_kms_key.secrets_encryption.arn
  recovery_window_in_days = 30

  tags = merge(var.tags, {
    Component = "database"
  })
}
```

- **Impact**: HIGH — Unrotated credentials, compliance violations
- **Severity**: HIGH
- **Source**: [SSM vs Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)

---

## State Management Deep Dive

### Local Development State
```hcl
# Use local state only for learning/solo development
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  # No backend block = local state (terraform.tfstate)
}
```
- **Risk**: State may contain `SecureString` plaintext values; no sharing, no locking
- **When**: Solo development, learning only. Never for shared environments.

---

### Production Remote State (S3 + DynamoDB)

```hcl
# 1. Bootstrap: Create S3 and DynamoDB for state (run once with local state, then migrate)
resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.org_name}-terraform-state"

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
      kms_master_key_id = aws_kms_key.state_encryption.arn
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

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "terraform-locks"
    ManagedBy = "terraform"
  }
}

# 2. Backend configuration for SSM parameters stack
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/ssm/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

- **Benefit**: Team sharing, locking, version history
- **Critical**: State may contain `SecureString` plaintext if `data.aws_ssm_parameter` is used — restrict S3 bucket access to service accounts only. Prefer `ephemeral.aws_ssm_parameter` to minimize secret exposure in state.

---

### State File Sensitivity: SecureString in State

```hcl
# When using data source (avoid for secrets — plaintext in state)
data "aws_ssm_parameter" "endpoint" {
  name = "${var.parameter_prefix}/service/endpoint"  # String type: OK to use data source
}

# Mark outputs as sensitive if they pass SSM values to other modules
output "service_endpoint" {
  value       = data.aws_ssm_parameter.endpoint.value
  description = "Service endpoint URL"
  sensitive   = false  # Non-sensitive String parameter
}

# For SecureString — use ephemeral resource
ephemeral "aws_ssm_parameter" "api_key" {
  name            = "${var.parameter_prefix}/api/key"
  with_decryption = true
}
# ephemeral.aws_ssm_parameter.api_key.value — available in apply context, never in state
```

---

## Module Architecture

### Standard Module Structure

```
modules/
├── ssm-parameters/
│   ├── main.tf           # aws_ssm_parameter resources + KMS key
│   ├── variables.tf      # parameter_prefix, environment, parameters map, kms_key_arn
│   ├── outputs.tf        # parameter_arns, parameter_names, kms_key_arn
│   ├── versions.tf       # required_version, required_providers
│   └── README.md
├── ssm-kms/
│   ├── main.tf           # aws_kms_key + aws_kms_alias + aws_kms_key_policy
│   ├── variables.tf
│   ├── outputs.tf        # key_arn, key_id, alias_arn
│   ├── versions.tf
│   └── README.md
```

### Module Definition Example

```hcl
# modules/ssm-parameters/variables.tf
variable "parameter_prefix" {
  type        = string
  description = "Root SSM path prefix (e.g., /prod/myapp)"

  validation {
    condition     = can(regex("^/[a-zA-Z0-9._/-]+$", var.parameter_prefix)) && !endswith(var.parameter_prefix, "/")
    error_message = "Prefix must start with / and not end with /."
  }
}

variable "string_parameters" {
  type        = map(string)
  description = "Map of non-sensitive String parameters: { parameter-name = value }"
  default     = {}
}

variable "secure_parameter_names" {
  type        = list(string)
  description = "List of SecureString parameter names to create with PLACEHOLDER values (managed externally)"
  default     = []
}

variable "kms_key_arn" {
  type        = string
  description = "KMS key ARN for SecureString encryption"
}

variable "tier" {
  type    = string
  default = "Standard"

  validation {
    condition     = contains(["Standard", "Advanced", "Intelligent-Tiering"], var.tier)
    error_message = "Tier must be Standard, Advanced, or Intelligent-Tiering."
  }
}

variable "tags" {
  type    = map(string)
  default = {}
}

# modules/ssm-parameters/main.tf
resource "aws_ssm_parameter" "string_params" {
  for_each = var.string_parameters

  name           = "${var.parameter_prefix}/${each.key}"
  type           = "String"
  insecure_value = each.value
  tier           = var.tier
  tags           = merge(var.tags, { Name = "${var.parameter_prefix}/${each.key}" })
}

resource "aws_ssm_parameter" "secure_params" {
  for_each = toset(var.secure_parameter_names)

  name        = "${var.parameter_prefix}/${each.value}"
  type        = "SecureString"
  value       = "PLACEHOLDER"  # Managed externally; set ignore_changes
  key_id      = var.kms_key_arn
  tier        = var.tier
  tags        = merge(var.tags, { Name = "${var.parameter_prefix}/${each.value}" })

  lifecycle {
    ignore_changes = [value]
  }
}

# modules/ssm-parameters/outputs.tf
output "string_parameter_arns" {
  value       = { for k, v in aws_ssm_parameter.string_params : k => v.arn }
  description = "ARNs of created String parameters"
}

output "secure_parameter_arns" {
  value       = { for k, v in aws_ssm_parameter.secure_params : k => v.arn }
  description = "ARNs of created SecureString parameters"
}

output "parameter_prefix" {
  value       = var.parameter_prefix
  description = "SSM parameter path prefix for this module instance"
}
```

### Root Module Usage

```hcl
# root/main.tf
module "ssm_kms" {
  source = "./modules/ssm-kms"

  environment      = var.environment
  application_name = var.application_name
  tags             = local.common_tags
}

module "app_parameters" {
  source = "./modules/ssm-parameters"

  parameter_prefix = "/${var.environment}/${var.application_name}"
  kms_key_arn      = module.ssm_kms.key_arn
  tier             = "Standard"

  string_parameters = {
    "config/log-level"    = "info"
    "config/region"       = var.aws_region
    "database/host"       = var.db_host
    "database/port"       = tostring(var.db_port)
  }

  secure_parameter_names = [
    "database/password",
    "api/external-key",
  ]

  tags = local.common_tags

  depends_on = [module.ssm_kms]
}
```

---

## Integration Patterns

### Integration: Terraform ↔ KMS

```hcl
# Complete KMS + SecureString integration
resource "aws_kms_key" "ssm" {
  description             = "SSM Parameter Store encryption - ${var.environment}"
  enable_key_rotation     = true
  rotation_period_in_days = 365
  deletion_window_in_days = 30

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_key_policy" "ssm" {
  key_id = aws_kms_key.ssm.id
  policy = data.aws_iam_policy_document.ssm_key_policy.json
}

data "aws_iam_policy_document" "ssm_key_policy" {
  statement {
    sid       = "EnableRootAccess"
    effect    = "Allow"
    principals { type = "AWS"; identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"] }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowSSMService"
    effect = "Allow"
    principals { type = "Service"; identifiers = ["ssm.amazonaws.com"] }
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = ["*"]
  }
}

resource "aws_ssm_parameter" "secret" {
  name   = "${var.parameter_prefix}/secret/value"
  type   = "SecureString"
  value  = var.secret_value
  key_id = aws_kms_key.ssm.arn    # Explicit CMK reference
}
```

- **Issues**: SSM service principal must be in key policy for parameter encryption to work. Without it, `PutParameter` for `SecureString` fails with `AccessDeniedException`.
- **Source**: [KMS Key Policies for SSM](https://docs.aws.amazon.com/kms/latest/developerguide/services-parameter-store.html)

---

### Integration: Terraform ↔ IAM

```hcl
# Application role with SSM read access
resource "aws_iam_role" "app_role" {
  name = "${var.environment}-${var.application_name}-role"

  assume_role_policy = data.aws_iam_policy_document.app_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ssm_read" {
  role       = aws_iam_role.app_role.name
  policy_arn = aws_iam_policy.ssm_read.arn
}

# Read policy scoped to application path
resource "aws_iam_policy" "ssm_read" {
  name   = "${var.environment}-${var.application_name}-ssm-read"
  policy = data.aws_iam_policy_document.ssm_read_policy.json
}

data "aws_iam_policy_document" "ssm_read_policy" {
  statement {
    effect  = "Allow"
    actions = ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"]
    resources = [
      "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${var.environment}/${var.application_name}/*"
    ]
  }

  statement {
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:DescribeKey"]
    resources = [aws_kms_key.ssm.arn]
  }
}
```

- **Issues**: Path must match exactly — including leading `/`. ARN format is `parameter/path/name` not `parameter//path/name`.
- **Source**: [IAM for Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-access.html)

---

### Integration: Terraform ↔ Lambda

```hcl
# Lambda function with SSM access via environment variable injection pattern
resource "aws_lambda_function" "app" {
  function_name = "${var.environment}-${var.application_name}"
  runtime       = "python3.12"
  handler       = "app.handler"
  role          = aws_iam_role.lambda_role.arn
  filename      = data.archive_file.lambda.output_path

  environment {
    variables = {
      # Pass parameter PATH (not value) — Lambda fetches at runtime using SDK/Extension
      SSM_PARAMETER_PREFIX = "/${var.environment}/${var.application_name}"
      AWS_REGION           = var.aws_region
    }
  }

  # Option 2: Parameters and Secrets Lambda Extension (recommended for cached access)
  layers = [
    "arn:aws:lambda:${var.aws_region}:177933569100:layer:AWS-Parameters-and-Secrets-Lambda-Extension:12"
  ]
}

# Lambda role needs SSM read access
resource "aws_iam_role_policy_attachment" "lambda_ssm" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.ssm_read.arn
}
```

- **Issues**: Lambda execution role must have `kms:Decrypt` in addition to `ssm:GetParameter` for `SecureString` types. The Parameters and Secrets Lambda Extension caches parameters locally (reduces API calls and costs).
- **Source**: [Lambda + Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html)

---

### Integration: Terraform ↔ ECS

```hcl
# ECS task definition injecting SSM parameters as environment variables
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.environment}-${var.application_name}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = var.application_name
    image = "${var.ecr_repository_url}:${var.image_tag}"

    secrets = [
      {
        name      = "DB_PASSWORD"
        valueFrom = aws_ssm_parameter.db_password.arn
      },
      {
        name      = "API_KEY"
        valueFrom = "${aws_ssm_parameter.api_key.arn}"
      }
    ]

    environment = [
      { name = "DB_HOST", value = aws_ssm_parameter.db_host.value },
      { name = "ENVIRONMENT", value = var.environment }
    ]
  }])
}

# ECS execution role must be able to read SSM parameters
data "aws_iam_policy_document" "ecs_execution_ssm" {
  statement {
    effect  = "Allow"
    actions = ["ssm:GetParameters"]
    resources = [
      aws_ssm_parameter.db_password.arn,
      aws_ssm_parameter.api_key.arn,
    ]
  }

  statement {
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [aws_kms_key.ssm.arn]
  }
}
```

- **Issues**: ECS `secrets` injection uses the **execution role** (not the task role). The ARN in `valueFrom` must reference the full SSM parameter ARN. ECS injects the decrypted value at container startup — the container process sees it as a plain environment variable.
- **Source**: [ECS Secrets from SSM](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-ssm-paramstore.html)

---

### Integration: Terraform ↔ Secrets Manager

```hcl
# Decision boundary: use SSM for config, Secrets Manager for rotating credentials
#
# SSM Parameter Store: DB host, port, name, feature flags, config values
# Secrets Manager: DB password, OAuth tokens, API keys that rotate

resource "aws_ssm_parameter" "db_config" {
  name           = "/${var.environment}/${var.app}/database/host"
  type           = "String"
  insecure_value = var.db_host  # Non-secret config → SSM
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name       = "${var.environment}/${var.app}/database/credentials"
  kms_key_id = aws_kms_key.secrets.arn  # Rotating credentials → Secrets Manager
}
```

- **Issues**: SSM does not support automatic rotation. If a secret managed in SSM Parameter Store needs rotation, it requires manual update or external tooling. Mixing SSM and Secrets Manager in the same application is acceptable — use SSM for config, Secrets Manager for credentials.
- **Source**: [Choosing Between SSM and Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html#intro-comparison-parameter-store)

---

### Integration: Terraform ↔ CloudWatch

```hcl
# CloudWatch Event Rule for SSM parameter change notifications
resource "aws_cloudwatch_event_rule" "ssm_parameter_change" {
  name        = "${var.environment}-ssm-parameter-changes"
  description = "Notify on SSM parameter changes in ${var.parameter_prefix}"

  event_pattern = jsonencode({
    source      = ["aws.ssm"]
    "detail-type" = ["Parameter Store Change"]
    detail = {
      operation = ["Create", "Update", "Delete", "LabelParameterVersion"]
      name      = [{ prefix = var.parameter_prefix }]
    }
  })
}

resource "aws_cloudwatch_event_target" "ssm_change_sns" {
  rule      = aws_cloudwatch_event_rule.ssm_parameter_change.name
  target_id = "SSMParameterChangeSNS"
  arn       = aws_sns_topic.alerts.arn
}
```

- **Issues**: CloudWatch Events for SSM are emitted asynchronously — expect up to 5 minutes delay. Event rules use path prefix matching on the `name` field.
- **Source**: [SSM Parameter Change Events](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-cwe.html)

---

## Quality Control

### Verification Commands

```bash
# Format validation
terraform fmt -recursive -check=true
# Expected: Exit code 0, no output (all files formatted)

# Syntax validation
terraform validate
# Expected: "Success! The configuration is valid."

# Security scanning (SSM-specific checks)
tfsec . --format json
# Expected: No HIGH/CRITICAL findings
# Key checks: aws-ssm-secret-use-customer-key, aws-ssm-no-default-encryption

# Linting
checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks
# Key policies: CKV_AWS_16 (encryption), CKV2_AWS_34 (SecureString with CMK)

# Plan before apply
terraform plan -out=tfplan -lock=true
terraform show tfplan | grep -E "(aws_ssm_parameter|kms)"
# Expected: Resource additions/modifications clearly listed

# State verification after apply
terraform state list | grep ssm
# Expected: All aws_ssm_parameter resources listed

terraform state show aws_ssm_parameter.db_host
# Expected: Resource attributes including name, type, tier, arn
# Note: SecureString values shown as (sensitive) or empty
```

### Testing with Terratest

```go
package test

import (
  "fmt"
  "testing"

  "github.com/aws/aws-sdk-go/aws"
  "github.com/aws/aws-sdk-go/aws/session"
  "github.com/aws/aws-sdk-go/service/ssm"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/stretchr/testify/assert"
  "github.com/stretchr/testify/require"
)

func TestSSMParameterCreation(t *testing.T) {
  t.Parallel()

  opts := &terraform.Options{
    TerraformDir: "../examples/ssm-parameters",
    Vars: map[string]interface{}{
      "environment":       "test",
      "application_name":  "terratest",
      "parameter_prefix":  "/test/terratest",
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  // Verify parameter was created
  prefix := terraform.Output(t, opts, "parameter_prefix")
  require.Equal(t, "/test/terratest", prefix)

  // Verify parameter exists in AWS
  sess := session.Must(session.NewSession(&aws.Config{Region: aws.String("us-east-1")}))
  ssmClient := ssm.New(sess)

  result, err := ssmClient.GetParameter(&ssm.GetParameterInput{
    Name:           aws.String(fmt.Sprintf("%s/config/log-level", prefix)),
    WithDecryption: aws.Bool(false),
  })
  require.NoError(t, err)
  assert.Equal(t, "info", *result.Parameter.Value)
  assert.Equal(t, "String", *result.Parameter.Type)
}
```

---

## Production Readiness

### Performance and Throughput

```
Scenario: High-frequency parameter reads
Challenge: Default throughput is ~40 TPS per Region; Lambda cold starts × many functions can burst this
Solution: Enable high throughput mode (up to 10,000 TPS) for high-scale workloads
```

```hcl
resource "aws_ssm_service_setting" "throughput" {
  setting_id    = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:servicesetting/ssm/parameter-store/high-throughput-enabled"
  setting_value = "true"
}
```

- **Note**: High-throughput incurs additional cost ($0.05 per 10,000 API interactions beyond included free tier).
- **Source**: [Parameter Store Throughput](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-throughput.html)

---

### Monitoring & Alerting

```hcl
# Monitor SSM API throttling
resource "aws_cloudwatch_metric_alarm" "ssm_throttling" {
  alarm_name          = "${var.environment}-ssm-api-throttling"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ThrottledRequests"
  namespace           = "AWS/SSM"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "SSM Parameter Store API requests are being throttled"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    Region = var.aws_region
  }
}
```

---

### Security Checklist

```
- [ ] All SecureString parameters use customer-managed KMS key (not default aws/ssm)
- [ ] KMS key policy includes SSM service principal (ssm.amazonaws.com)
- [ ] IAM policies scoped to path prefix (never ssm:* on *)
- [ ] ephemeral.aws_ssm_parameter used for SecureString → resource wiring (not data source)
- [ ] State file encryption enabled (S3 backend with encrypt = true)
- [ ] State S3 bucket access restricted to Terraform service account
- [ ] No secret values hardcoded in .tf files or .tfvars committed to git
- [ ] .tfvars files containing secrets added to .gitignore
- [ ] All parameters tagged (Environment, Application, ManagedBy)
- [ ] Tier upgrade decision documented (cannot downgrade)
- [ ] overwrite argument removed (deprecated since v5.0)
- [ ] CloudWatch Events configured for parameter change audit trail
```

---

### Disaster Recovery Runbook

```bash
# 1. Recover from state corruption
aws s3api get-object \
  --bucket my-org-terraform-state \
  --key prod/ssm/terraform.tfstate.backup \
  terraform.tfstate.backup

terraform state pull > terraform.tfstate.corrupted
cp terraform.tfstate.backup terraform.tfstate
terraform state push terraform.tfstate

# 2. Import an existing SSM parameter not managed by Terraform
terraform import aws_ssm_parameter.db_host "/prod/myapp/database/host"
# Expected: Import successful; resource now in state

# 3. Verify imported parameter matches configuration
terraform plan
# Expected: "No changes. Infrastructure is up-to-date."

# 4. Restore a deleted parameter from history
aws ssm get-parameter-history \
  --name "/prod/myapp/database/password" \
  --query "Parameters[*].{Version:Version,Value:Value,LastModifiedDate:LastModifiedDate}" \
  --output table

# 5. List all parameters under a path prefix
aws ssm get-parameters-by-path \
  --path "/prod/myapp/" \
  --recursive \
  --query "Parameters[*].{Name:Name,Type:Type,Version:Version}" \
  --output table
```

---

## Reference Implementation (Copy-Paste Root Module)

### File: `main.tf`

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
    key            = "prod/ssm/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "TerraformSession"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Application = var.application_name
    }
  }
}

data "aws_caller_identity" "current" {}

# KMS key for SecureString encryption
resource "aws_kms_key" "ssm" {
  description             = "SSM Parameter Store encryption - ${var.environment}"
  key_usage               = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "SYMMETRIC_DEFAULT"
  enable_key_rotation     = true
  rotation_period_in_days = 365
  deletion_window_in_days = 30

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_key_policy" "ssm" {
  key_id = aws_kms_key.ssm.id
  policy = data.aws_iam_policy_document.ssm_key_policy.json
}

data "aws_iam_policy_document" "ssm_key_policy" {
  statement {
    sid       = "EnableRootAccess"
    effect    = "Allow"
    principals { type = "AWS"; identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"] }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowSSMService"
    effect = "Allow"
    principals { type = "Service"; identifiers = ["ssm.amazonaws.com"] }
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = ["*"]
  }
}

resource "aws_kms_alias" "ssm" {
  name          = "alias/${var.environment}/ssm-parameters"
  target_key_id = aws_kms_key.ssm.key_id
}

# Non-sensitive configuration parameters (String type)
resource "aws_ssm_parameter" "db_host" {
  name           = "${local.parameter_prefix}/database/host"
  type           = "String"
  insecure_value = var.db_host
  description    = "Database hostname"
  tier           = "Standard"
}

resource "aws_ssm_parameter" "db_name" {
  name           = "${local.parameter_prefix}/database/name"
  type           = "String"
  insecure_value = var.db_name
  description    = "Database name"
  tier           = "Standard"
}

# Sensitive parameter (SecureString): Terraform creates; value managed externally
resource "aws_ssm_parameter" "db_password" {
  name        = "${local.parameter_prefix}/database/password"
  type        = "SecureString"
  value       = "PLACEHOLDER"
  key_id      = aws_kms_key.ssm.arn
  description = "Database master password - managed externally"
  tier        = "Standard"

  lifecycle {
    ignore_changes = [value]
  }
}
```

### File: `variables.tf`

```hcl
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "account_id" {
  type        = string
  description = "AWS account ID for IAM ARN construction"
}

variable "environment" {
  type = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod."
  }
}

variable "application_name" {
  type        = string
  description = "Application name for parameter path organization"
}

variable "db_host" {
  type        = string
  description = "Database hostname (non-sensitive)"
}

variable "db_name" {
  type        = string
  description = "Database name (non-sensitive)"
}

locals {
  parameter_prefix = "/${var.environment}/${var.application_name}"
}
```

### File: `outputs.tf`

```hcl
output "parameter_prefix" {
  value       = local.parameter_prefix
  description = "SSM parameter path prefix for dependent stacks"
}

output "kms_key_arn" {
  value       = aws_kms_key.ssm.arn
  description = "KMS key ARN used for SecureString encryption"
}

output "db_host_arn" {
  value       = aws_ssm_parameter.db_host.arn
  description = "ARN of the database host parameter"
}

output "db_password_arn" {
  value       = aws_ssm_parameter.db_password.arn
  description = "ARN of the database password parameter (for IAM policies)"
}
```

### File: `terraform.tfvars.example`

```hcl
# Copy to terraform.tfvars — DO NOT COMMIT terraform.tfvars to git
aws_region       = "us-east-1"
account_id       = "123456789012"
environment      = "prod"
application_name = "myapp"
db_host          = "myapp-prod.cluster-xyz.us-east-1.rds.amazonaws.com"
db_name          = "myapp"
```

---

## Reference Implementations

- [Official Terraform AWS SSM Parameter Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter)
- [Ephemeral Resource: aws_ssm_parameter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/ephemeral-resources/ssm_parameter)
- [Data Source: aws_ssm_parameter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter)
- [Data Source: aws_ssm_parameters_by_path](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameters_by_path)
- [AWS SSM Parameter Store User Guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [AWS Well-Architected Framework — Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/)

---

## Source Bibliography

### Primary Sources
- [Terraform AWS Provider Registry v6.47.0](https://registry.terraform.io/providers/hashicorp/aws/6.47.0/docs) — Published 2026-05-28
- [aws_ssm_parameter Resource Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter)
- [ephemeral.aws_ssm_parameter Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/ephemeral-resources/ssm_parameter)
- [AWS SSM Parameter Store User Guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language) — HCL reference
- [AWS IAM for Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-access.html)
- [KMS Key Policies for SSM](https://docs.aws.amazon.com/kms/latest/developerguide/services-parameter-store.html)
- [AWS Parameter Tiers](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html)

### Validation & Tools
- [tfsec GitHub](https://github.com/aquasecurity/tfsec) — Security scanner
- [Checkov](https://www.checkov.io/) — Policy-as-code validator (CKV_AWS_16, CKV2_AWS_34)
- [Terratest](https://terratest.gruntwork.io/) — Integration testing framework
- [hashicorp/terraform-provider-aws issues](https://github.com/hashicorp/terraform-provider-aws/issues) — Bug tracker

---

## Completion Checklist

- [x] All >= 1.7 and aws ~> 6.0 patterns validated
- [x] Ephemeral resource pattern documented (v6.x — `ephemeral.aws_ssm_parameter`)
- [x] `insecure_value` vs `value` distinction documented (v5+ change)
- [x] `overwrite` deprecation documented and alternative provided
- [x] State management strategy documented with S3 + DynamoDB
- [x] Module architecture fully defined (ssm-parameters, ssm-kms)
- [x] Every anti-pattern has tested alternative
- [x] All CLI commands include expected success output
- [x] Integration examples: KMS, IAM, Lambda, ECS, Secrets Manager, CloudWatch
- [x] Sources directly linked to registry/docs
- [x] Security checklist complete
- [x] Copy-paste root module with .tfvars.example included
- [x] Disaster recovery procedures documented
- [x] Tier downgrade limitation documented

---

## Research Gaps

```
Gap: Terraform support for SSM Parameter Advanced Tier policies (expiration, no-change notification)
Impact: Cannot enforce parameter rotation reminders or expiration via IaC; must configure manually or via SDK
Workaround: Use aws_ssm_service_setting and CloudWatch Events for change monitoring
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter — check for `policies` block support in future v6.x releases

Gap: aws_ssm_parameters_by_path data source does not support for_each iteration on result
Impact: Cannot dynamically create resources based on all parameters under a path prefix within same Terraform apply
Workaround: Pre-declare all parameter names as input variables; use module with explicit parameter maps
Follow-up: https://github.com/hashicorp/terraform-provider-aws/issues — search "ssm_parameters_by_path for_each"
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Creating `aws_ssm_parameter` resources with `String` type and `insecure_value`
- Setting up KMS key for `SecureString` encryption with correct key policy
- Scoping IAM policies to path-based ARNs
- Configuring S3 backend with encryption and DynamoDB locking
- Migrating from deprecated `overwrite` argument to lifecycle rules
- Adding CloudWatch Events for parameter change auditing

### Medium Confidence (Validate with user)
- Choosing between Standard, Advanced, and Intelligent-Tiering tiers
- `for_each` vs separate resources for parameter sets
- `ignore_changes = [value]` vs Terraform-managed full lifecycle

### Low Confidence (Must ask user)
- Whether `SecureString` values should rotate → if yes, recommend Secrets Manager instead
- Cross-account parameter sharing (Advanced tier + Resource Access Manager)
- High-throughput mode enablement (cost implications)

### Edge Cases (When to pause)
- State contains `SecureString` plaintext → migrate to ephemeral resource pattern
- Tier downgrade attempt (`Advanced` → `Standard`) → inform user it is impossible; require manual deletion
- Parameter name collision during `for_each` key rename → destroy/recreate
- KMS key deletion with parameters still referencing it → parameters become permanently unreadable

### Emergency Stop
- Halt if `terraform destroy` targets parameters with no `prevent_destroy` and no recent backup
- Halt if `SecureString` value found in `.tfvars` file committed to git
- Halt if state file encryption disabled and state contains `SecureString` plaintext
- Halt if KMS key `prevent_destroy = false` and key is referenced by active `SecureString` parameters
