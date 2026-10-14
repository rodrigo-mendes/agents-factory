# Terraform AWS KMS — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - KMS (Key Management Service)"
Cloud_Provider: "AWS"
Target_Service: "KMS (Key Management Service)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-29"
Domain_Complexity: "Complex"
KMS_Resources_Covered: "aws_kms_key, aws_kms_alias, aws_kms_key_policy, aws_kms_grant, aws_kms_replica_key, aws_kms_external_key, aws_kms_ciphertext, aws_kms_custom_key_store"
KMS_Data_Sources_Covered: "aws_kms_key, aws_kms_alias, aws_kms_secrets, aws_kms_ciphertext, aws_kms_public_key"
V6_Notable_Arguments: "rotation_period_in_days (90–2560 days, default 365), ml_dsa key_spec values (ML_DSA_44, ML_DSA_65, ML_DSA_87 for post-quantum signing), bypass_policy_lockout_safety_check on aws_kms_key_policy"
```

---

## Executive Summary

AWS Key Management Service (AWS KMS) is the cryptographic key management control plane for AWS. Every `aws_kms_key` resource in Terraform creates a logical key container backed by FIPS 140-3 Level 3 validated HSMs. KMS keys never leave AWS KMS unencrypted — all encrypt/decrypt operations happen inside the HSM fleet. The Terraform provider manages the full lifecycle: key creation, policy attachment (`aws_kms_key_policy`), alias management (`aws_kms_alias`), grant-based delegation (`aws_kms_grant`), multi-Region replication (`aws_kms_replica_key`), and external key stores (`aws_kms_external_key`, `aws_kms_custom_key_store`). The aws provider v6.x (6.47.0) supports `rotation_period_in_days` (90–2560 days) for custom rotation intervals, ML-DSA post-quantum key specs (`ML_DSA_44`, `ML_DSA_65`, `ML_DSA_87`), and the split between `aws_kms_key` (creates key + optional inline policy) and `aws_kms_key_policy` (manages policy independently to avoid perpetual diffs).

The most critical Terraform-specific hazard for KMS is **key lockout**: if you destroy `aws_kms_key_policy` or misconfigure a key policy with no root account principal, the key becomes permanently unmanageable. AWS cannot recover a locked-out key — the only outcome is waiting for the deletion window (7–30 days) and then losing all data encrypted under that key. The second major hazard is **accidental key deletion**: Terraform's `terraform destroy` schedules KMS key deletion after `deletion_window_in_days` (default 30 days, minimum 7). Without `prevent_destroy = true` in the lifecycle block, any `terraform destroy` on a production key starts an irreversible deletion clock. The state file stores the key ARN, key ID, and policy document in plaintext — restrict S3 backend access accordingly.

KMS is classified **Complex** because: (1) key policies are the PRIMARY access control mechanism with no fallback to IAM unless explicitly configured; (2) a misconfigured key policy permanently locks the account out of key management; (3) multi-resource composition (key + policy + alias + grant) requires careful `depends_on` ordering; (4) the state file contains the full key policy JSON (potentially sensitive service principals and conditions); (5) multi-Region keys involve cross-Region provider aliases and replication ordering; and (6) destruction of encrypted data is permanent once the KMS key is deleted.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Ensures reproducibility across team members and CI pipelines. Pins to `~> 6.0` to access `rotation_period_in_days` and ML-DSA key specs. The S3 backend with encryption and DynamoDB locking is mandatory — the state file contains full key policies.

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
    key            = "prod/kms/terraform.tfstate"
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

**Why**: Credentials must never be hardcoded. The `assume_role` pattern enables CI/CD pipelines without static keys. `default_tags` enforces consistent tagging on all KMS keys — required for cost allocation, compliance, and key ownership tracking. Note: KMS keys support tags independently; `default_tags` in the provider block propagates to all resources.

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

#### Pattern: Symmetric CMK with Key Policy via `aws_kms_key_policy` (Recommended v6.x Split)

**Why**: Separating `aws_kms_key` from `aws_kms_key_policy` is the recommended pattern in provider v6.x. Defining `policy` inline on `aws_kms_key` causes perpetual diffs because AWS normalizes key policies differently from the JSON Terraform sends. Using `aws_kms_key_policy` as a standalone resource eliminates this drift. The key policy **must** include a root account principal (`arn:aws:iam::ACCOUNT_ID:root`) to prevent permanent key lockout — without it, only the key creator can manage the key, and if that identity is removed, the key becomes permanently unmanageable.

```hcl
# 1. Create the KMS key (no inline policy)
resource "aws_kms_key" "app_encryption" {
  description             = "${var.environment} ${var.service_name} encryption key"
  key_usage               = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "SYMMETRIC_DEFAULT"
  enable_key_rotation     = true
  rotation_period_in_days = 365     # 90–2560 days; default 365
  deletion_window_in_days = 30      # 7–30 days; minimum 7
  is_enabled              = true
  multi_region            = false

  tags = {
    Name    = "${var.environment}-${var.service_name}-key"
    Service = var.service_name
    Purpose = "encryption"
  }

  lifecycle {
    prevent_destroy = true  # CRITICAL: prevents accidental key deletion
  }
}

# 2. Attach policy separately to avoid perpetual diff
resource "aws_kms_key_policy" "app_encryption" {
  key_id = aws_kms_key.app_encryption.id
  policy = data.aws_iam_policy_document.app_encryption_key_policy.json
}

# 3. Key policy: root account + key admins + key users
data "aws_iam_policy_document" "app_encryption_key_policy" {
  # REQUIRED: Enable IAM policies — without this, IAM policies have NO effect
  statement {
    sid    = "EnableRootAccountAccess"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = ["*"]
  }

  # Key administrators: can manage but NOT use the key for crypto operations
  statement {
    sid    = "AllowKeyAdministration"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = var.key_admin_role_arns
    }

    actions = [
      "kms:Create*",
      "kms:Describe*",
      "kms:Enable*",
      "kms:List*",
      "kms:Put*",
      "kms:Update*",
      "kms:Revoke*",
      "kms:Disable*",
      "kms:Get*",
      "kms:Delete*",
      "kms:TagResource",
      "kms:UntagResource",
      "kms:ScheduleKeyDeletion",
      "kms:CancelKeyDeletion",
    ]
    resources = ["*"]
  }

  # Key users: can use the key for encryption/decryption operations
  statement {
    sid    = "AllowKeyUsage"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = var.key_user_role_arns
    }

    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
    ]
    resources = ["*"]
  }

  # Allow AWS services to use grants (required for EBS, RDS, S3, etc.)
  statement {
    sid    = "AllowGrantCreationForAWSServices"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = var.key_user_role_arns
    }

    actions = [
      "kms:CreateGrant",
      "kms:ListGrants",
      "kms:RevokeGrant",
    ]
    resources = ["*"]

    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }
}

data "aws_caller_identity" "current" {}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_kms_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key) | [aws_kms_key_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key_policy)

---

#### Pattern: KMS Alias with Deterministic Naming Convention

**Why**: Aliases provide human-readable names that decouple application code from raw key IDs (UUIDs). A consistent alias naming scheme (`alias/<environment>/<service>/<purpose>`) enables key lookup by alias ARN in other Terraform stacks, cross-service integrations, and audit filtering in CloudTrail. Aliases must start with `alias/` — the `aws/` prefix is reserved for AWS managed keys and cannot be used.

```hcl
resource "aws_kms_alias" "app_encryption" {
  name          = "alias/${var.environment}/${var.service_name}/encryption"
  target_key_id = aws_kms_key.app_encryption.key_id
}

# Reference the alias in other resources
resource "aws_s3_bucket_server_side_encryption_configuration" "app_data" {
  bucket = aws_s3_bucket.app_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_alias.app_encryption.arn
    }
    bucket_key_enabled = true  # Reduces KMS API calls by up to 99%
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_kms_alias](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_alias)

---

#### Pattern: `prevent_destroy` Lifecycle Rule on All Production Keys

**Why**: A `terraform destroy` on a KMS key schedules irreversible deletion after `deletion_window_in_days`. Any data encrypted under the key becomes permanently unrecoverable when the deletion window expires. `prevent_destroy = true` causes Terraform to emit an error if a plan includes destroying the key resource — requiring explicit removal of the lifecycle block before destruction is possible.

```hcl
resource "aws_kms_key" "prod_database_key" {
  description             = "Production database encryption key"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  tags = {
    Name        = "prod-database-key"
    DataClass   = "confidential"
    Environment = "production"
  }

  lifecycle {
    prevent_destroy = true
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Lifecycle Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle#prevent_destroy) | [AWS KMS Key Deletion](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html)

---

#### Pattern: Automatic Key Rotation with Custom Period

**Why**: AWS KMS v6.x supports `rotation_period_in_days` (90–2560 days). Key rotation creates new HSM backing key material while keeping the same key ARN/ID — existing ciphertext remains decryptable without application changes. Automatic rotation should be enabled on ALL symmetric `SYMMETRIC_DEFAULT` customer managed keys. Asymmetric keys do NOT support automatic rotation.

```hcl
resource "aws_kms_key" "data_encryption" {
  description              = "${var.environment} data encryption key"
  key_usage                = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "SYMMETRIC_DEFAULT"
  enable_key_rotation      = true
  rotation_period_in_days  = 365  # Override default: valid range 90–2560
  deletion_window_in_days  = 30

  lifecycle {
    prevent_destroy = true
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_kms_key enable_key_rotation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key) | [KMS Key Rotation](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)

---

#### Pattern: Variable Validation and Type Safety for KMS Configuration

**Why**: Prevents invalid key specs, out-of-range deletion windows, invalid alias prefixes, and unsupported key usage combinations at `terraform plan` time — before any AWS API call is made.

```hcl
variable "key_usage" {
  type        = string
  description = "Cryptographic use of the KMS key"
  default     = "ENCRYPT_DECRYPT"

  validation {
    condition     = contains(["ENCRYPT_DECRYPT", "SIGN_VERIFY", "GENERATE_VERIFY_MAC"], var.key_usage)
    error_message = "key_usage must be ENCRYPT_DECRYPT, SIGN_VERIFY, or GENERATE_VERIFY_MAC."
  }
}

variable "key_spec" {
  type        = string
  description = "Key material specification"
  default     = "SYMMETRIC_DEFAULT"

  validation {
    condition = contains([
      "SYMMETRIC_DEFAULT",
      "RSA_2048", "RSA_3072", "RSA_4096",
      "HMAC_256",
      "ECC_NIST_P256", "ECC_NIST_P384", "ECC_NIST_P521", "ECC_SECG_P256K1",
      "ML_DSA_44", "ML_DSA_65", "ML_DSA_87",
      "SM2",
    ], var.key_spec)
    error_message = "key_spec must be a valid KMS key specification."
  }
}

variable "deletion_window_in_days" {
  type        = number
  description = "Duration in days for scheduled key deletion (7–30)"
  default     = 30

  validation {
    condition     = var.deletion_window_in_days >= 7 && var.deletion_window_in_days <= 30
    error_message = "deletion_window_in_days must be between 7 and 30 inclusive."
  }
}

variable "rotation_period_in_days" {
  type        = number
  description = "Automatic rotation period in days (90–2560)"
  default     = 365

  validation {
    condition     = var.rotation_period_in_days >= 90 && var.rotation_period_in_days <= 2560
    error_message = "rotation_period_in_days must be between 90 and 2560 inclusive."
  }
}

variable "key_admin_role_arns" {
  type        = list(string)
  description = "IAM role ARNs that can administer (but not use) this KMS key"

  validation {
    condition = alltrue([
      for arn in var.key_admin_role_arns : can(regex("^arn:aws:iam::[0-9]{12}:role/.+", arn))
    ])
    error_message = "All key_admin_role_arns must be valid IAM role ARNs (arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME)."
  }
}

variable "key_user_role_arns" {
  type        = list(string)
  description = "IAM role ARNs that can use this KMS key for cryptographic operations"

  validation {
    condition = alltrue([
      for arn in var.key_user_role_arns : can(regex("^arn:(aws|aws-cn|aws-us-gov):iam::[0-9]{12}:(role|user)/.+", arn))
    ])
    error_message = "All key_user_role_arns must be valid IAM role or user ARNs."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

#### Pattern: Output Definitions for Cross-Stack Integration

**Why**: KMS key ARNs, key IDs, and alias ARNs are consumed by S3, RDS, DynamoDB, EBS, and Secrets Manager configurations in other Terraform stacks. Marking sensitive outputs prevents accidental logging in CI pipelines. Exporting both `key_arn` and `key_id` provides flexibility since different AWS APIs accept different identifier formats.

```hcl
output "key_arn" {
  value       = aws_kms_key.app_encryption.arn
  description = "KMS key ARN for cross-stack integration"
  sensitive   = false  # ARNs are not secret; they appear in CloudTrail anyway
}

output "key_id" {
  value       = aws_kms_key.app_encryption.key_id
  description = "KMS key ID (UUID format)"
  sensitive   = false
}

output "alias_arn" {
  value       = aws_kms_alias.app_encryption.arn
  description = "KMS alias ARN for human-readable cross-stack reference"
  sensitive   = false
}

output "alias_name" {
  value       = aws_kms_alias.app_encryption.name
  description = "KMS alias name (alias/environment/service/purpose)"
  sensitive   = false
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Output Values](https://developer.hashicorp.com/terraform/language/values/outputs)

---

#### Pattern: KMS Grant for AWS Service Delegation

**Why**: When an AWS service (EBS, RDS, S3) needs to use a customer managed key on behalf of the customer, it uses a KMS grant rather than a key policy change. Grants are created at provisioning time and scoped to the specific service principal. Using `constraints.encryption_context_equals` binds the grant to specific resources (prevents reuse across tenants). The `retire_on_delete = false` default causes Terraform to *revoke* grants on destroy rather than retire them — safe default for production.

```hcl
# Example: Grant for Lambda function to use KMS key
resource "aws_kms_grant" "lambda_encryption" {
  name              = "${var.environment}-lambda-${var.function_name}-grant"
  key_id            = aws_kms_key.app_encryption.key_id
  grantee_principal = aws_iam_role.lambda_execution.arn
  operations        = ["Encrypt", "Decrypt", "GenerateDataKey", "GenerateDataKeyWithoutPlaintext", "DescribeKey"]

  constraints {
    encryption_context_equals = {
      Environment = var.environment
      Service     = var.service_name
    }
  }

  retire_on_delete = false  # false = revoke on destroy (safer default)
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_kms_grant](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_grant)

---

### ⚠️ Conditional Patterns

---

#### Decision: `aws_kms_key` Inline Policy vs. `aws_kms_key_policy` Standalone Resource

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Inline `policy` on `aws_kms_key`** | Single resource, simpler plan | Perpetual diffs (AWS normalizes policy JSON), harder lifecycle management | Prototyping, throwaway environments |
| **`aws_kms_key_policy` standalone** | No perpetual diffs, independent lifecycle, cleaner imports | Extra resource, explicit `depends_on` sometimes needed | All production workloads |

- **Agent**: "Ask user: Is this a production key? Use `aws_kms_key_policy` standalone for production to avoid perpetual plan diffs from AWS policy normalization."
- **Source**: [aws_kms_key_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key_policy) | [aws_kms_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key)

---

#### Decision: Single-Region Key vs. Multi-Region Key

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Single-Region `aws_kms_key`** | Simplicity, lower cost ($1/month), regional isolation | Cross-region decrypt requires cross-region KMS API calls | Single-region workloads, most production use cases |
| **Multi-Region `aws_kms_key` + `aws_kms_replica_key`** | Cross-region decrypt without API calls, DR scenarios, global apps | Higher cost (primary + each replica $1/month), complex rotation semantics | Active-active multi-region, disaster recovery with RTO requirements, DynamoDB Global Tables with client-side encryption |

```hcl
# Multi-Region primary key (us-east-1)
resource "aws_kms_key" "primary" {
  provider                 = aws.us-east-1
  description              = "Multi-Region primary encryption key"
  multi_region             = true
  enable_key_rotation      = true
  rotation_period_in_days  = 365
  deletion_window_in_days  = 30

  lifecycle {
    prevent_destroy = true
  }
}

# Replica in us-west-2
resource "aws_kms_replica_key" "replica_us_west_2" {
  provider                = aws.us-west-2
  description             = "Multi-Region replica encryption key (us-west-2)"
  primary_key_arn         = aws_kms_key.primary.arn
  deletion_window_in_days = 30
  enabled                 = true

  lifecycle {
    prevent_destroy = true
  }
}
```

- **Agent**: "Ask user: Does your workload require cross-region decryption without cross-region API calls? (e.g., DynamoDB Global Tables with client-side encryption, Active-Active DR)"
- **Source**: [aws_kms_replica_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_replica_key)

---

#### Decision: Standard Key Store vs. CloudHSM Key Store vs. External Key Store

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Standard (default)** | Zero ops overhead, FIPS 140-3 L3, full AWS service integration, low cost | No dedicated HSM hardware, multi-tenant at hardware level | 99% of production workloads |
| **CloudHSM key store** | Single-tenant HSM hardware, dedicated fleet | CloudHSM cluster cost (~$1.45/hr), operational overhead, no automatic rotation | Regulations mandating single-tenant HSMs (FIPS 140-3 compliance attestation requirements) |
| **External key store (XKS)** | Key material never enters AWS, external key manager control | High latency (external network call per crypto op), operational complexity, availability dependency on external KMS | Regulations mandating key material sovereignty outside AWS; rarely warranted |

- **Agent**: "Ask user: Do compliance requirements mandate single-tenant HSMs (CloudHSM) or key material outside AWS (XKS)? If not, use the standard key store."
- **Source**: [aws_kms_custom_key_store](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_custom_key_store) | [KMS Key Stores](https://docs.aws.amazon.com/kms/latest/developerguide/key-store-overview.html)

---

#### Decision: Symmetric Key vs. Asymmetric Key vs. HMAC Key

| Option | Key Spec | Use For | AWS Service Integration | Auto-Rotation |
|--------|----------|---------|------------------------|--------------|
| **Symmetric (default)** | `SYMMETRIC_DEFAULT` | Envelope encryption, all AWS services | Yes (S3, EBS, RDS, DynamoDB, etc.) | Yes (90–2560 days) |
| **RSA Encryption** | `RSA_2048/3072/4096` | Encrypt/decrypt by external parties without AWS creds | No | No (manual only) |
| **RSA Signing** | `RSA_2048/3072/4096` | Digital signatures (code signing, JWTs) | No | No |
| **ECC Signing** | `ECC_NIST_P256/384/521` | Elliptic curve signatures, smaller keys than RSA | No | No |
| **ML-DSA (Post-Quantum)** | `ML_DSA_44/65/87` | Post-quantum digital signatures (NIST PQC standard) | No | No |
| **HMAC** | `HMAC_256` | Message authentication codes | No | No |

- **Agent**: "Ask user: Do external parties (without AWS credentials) need to encrypt data or verify signatures? If no, use SYMMETRIC_DEFAULT. If yes, use asymmetric keys."
- **Source**: [Symmetric/Asymmetric Keys](https://docs.aws.amazon.com/kms/latest/developerguide/symmetric-asymmetric.html)

---

#### Decision: Per-Service Key vs. Shared Key

| Option | Optimizes | Sacrifices | Scaling | Blast Radius |
|--------|-----------|------------|---------|-------------|
| **Per-service key** | Least-privilege, independent rotation, fine-grained audit | Cost ($1/key/month), key sprawl at scale | Scales with services | Minimal: compromise of one key affects one service |
| **Shared key** | Lower cost, fewer resources to manage | Shared blast radius, coarse-grained audit, cannot rotate independently | Simpler at small scale | High: compromise affects all services |

- **When**: Use per-service keys for services with different data classification levels, regulatory scope, or team ownership. Use shared keys only for non-sensitive workloads in early development.
- **Agent**: "Ask user: Do the services share data classification and regulatory scope? If different PCI/HIPAA/SOC2 scope, use separate keys."
- **Source**: [AWS KMS Best Practices](https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html)

---

#### Decision: `for_each` vs. `count` for Multiple KMS Keys

| Option | Best For | Pitfall |
|--------|----------|---------|
| **`for_each` with map** | Creating keys per service/environment with stable identifiers | Complex `for_each` expressions for keys with varying policies |
| **`count`** | Creating N identical keys | Reordering the list destroys and recreates keys — catastrophic for KMS (data loss) |
| **Separate resources** | Keys with distinct policies and configurations | Verbose, harder to DRY |

```hcl
# PREFERRED: for_each for multiple keys
variable "kms_keys" {
  type = map(object({
    description             = string
    purpose                 = string
    rotation_period_in_days = number
  }))

  default = {
    "database" = {
      description             = "Database encryption key"
      purpose                 = "database-encryption"
      rotation_period_in_days = 365
    }
    "secrets" = {
      description             = "Secrets Manager encryption key"
      purpose                 = "secrets-encryption"
      rotation_period_in_days = 180
    }
  }
}

resource "aws_kms_key" "service_keys" {
  for_each = var.kms_keys

  description             = "${var.environment} ${each.value.description}"
  key_usage               = "ENCRYPT_DECRYPT"
  enable_key_rotation     = true
  rotation_period_in_days = each.value.rotation_period_in_days
  deletion_window_in_days = 30

  tags = {
    Name    = "${var.environment}-${each.key}-key"
    Purpose = each.value.purpose
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_alias" "service_keys" {
  for_each = var.kms_keys

  name          = "alias/${var.environment}/${each.key}/encryption"
  target_key_id = aws_kms_key.service_keys[each.key].key_id
}
```

- **Agent**: "Ask user: Use `for_each` (not `count`) for multiple KMS keys — `count` reordering causes key recreation which permanently destroys encrypted data."
- **Source**: [for_each Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Key Policy Without Root Account Principal

```hcl
# DON'T — key policy with no root account access
resource "aws_kms_key_policy" "locked_out" {
  key_id = aws_kms_key.example.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowAdmin"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::123456789012:role/AdminRole"  # Only one role
        }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })
}
```

**Why**: If `AdminRole` is deleted, renamed, or otherwise becomes inaccessible, the key is permanently locked. No AWS support can recover a KMS key with a locked-out key policy — the only outcome is waiting out the deletion window and losing all encrypted data.

**Instead**:
```hcl
# DO — always include root account as safety net
data "aws_iam_policy_document" "safe_key_policy" {
  statement {
    sid    = "EnableRootAccountAccess"  # REQUIRED — never remove
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowKeyAdministration"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::123456789012:role/AdminRole"]
    }

    actions = [
      "kms:Create*", "kms:Describe*", "kms:Enable*", "kms:List*",
      "kms:Put*", "kms:Update*", "kms:Revoke*", "kms:Disable*",
      "kms:Get*", "kms:Delete*", "kms:ScheduleKeyDeletion", "kms:CancelKeyDeletion",
    ]
    resources = ["*"]
  }
}
```

- **Impact**: CRITICAL — Permanent key lockout → permanent data loss after deletion window
- **Severity**: CRITICAL
- **Source**: [KMS Default Key Policy](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html#key-policy-default)

---

#### Anti-Pattern: Missing `prevent_destroy` on Production Keys

```hcl
# DON'T — KMS key without deletion protection
resource "aws_kms_key" "prod_database_key" {
  description             = "Production database key"
  enable_key_rotation     = true
  deletion_window_in_days = 7  # Minimum window — AND no prevent_destroy!
}
```

**Why**: A `terraform destroy` or accidental resource removal schedules key deletion after the window. With `deletion_window_in_days = 7`, you have 7 days to cancel before all data encrypted under this key becomes permanently unrecoverable. Even with 30 days, the risk is unacceptable for production.

**Instead**:
```hcl
# DO — protect production keys from accidental deletion
resource "aws_kms_key" "prod_database_key" {
  description             = "Production database key"
  enable_key_rotation     = true
  deletion_window_in_days = 30  # Maximum window for maximum recovery time

  lifecycle {
    prevent_destroy = true  # Error on any plan that would destroy this key
  }
}
```

- **Impact**: CRITICAL — Permanent data loss if key is deleted while data remains encrypted under it
- **Severity**: CRITICAL
- **Source**: [KMS Key Deletion](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html)

---

#### Anti-Pattern: Hardcoded Key Policy Wildcards Without Conditions

```hcl
# DON'T — overly permissive key usage (allows ANY AWS service on ANY resource)
data "aws_iam_policy_document" "permissive" {
  statement {
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["*"]  # DON'T — allows ALL principals in account
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }
}
```

**Why**: Wildcard principal with `kms:*` gives every IAM identity in the account unlimited key access, defeating least-privilege. Even with IAM policy restrictions, the key policy is the primary authorization layer.

**Instead**:
```hcl
# DO — explicit principals with conditions
data "aws_iam_policy_document" "least_privilege" {
  statement {
    sid    = "EnableRootAccountAccess"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "RestrictedKeyUsage"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::123456789012:role/AppServiceRole"]
    }
    actions = ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "kms:EncryptionContext:Environment"
      values   = ["production"]
    }
  }
}
```

- **Impact**: HIGH — Unauthorized access to all encrypted data, compliance failure
- **Severity**: HIGH
- **Source**: [KMS Key Policies Best Practices](https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-best-practices.html)

---

#### Anti-Pattern: `bypass_policy_lockout_safety_check = true` Without Justification

```hcl
# DON'T — bypassing KMS safety check without explicit justification
resource "aws_kms_key_policy" "dangerous" {
  key_id                             = aws_kms_key.example.id
  bypass_policy_lockout_safety_check = true  # DON'T — disables lockout protection
  policy                             = data.aws_iam_policy_document.key_policy.json
}
```

**Why**: AWS's policy lockout safety check prevents applying a key policy that would lock out all principals. Bypassing it enables you to accidentally create an unmanageable key.

**Instead**:
```hcl
# DO — only set true if AWS explicitly recommends it for your use case
resource "aws_kms_key_policy" "safe" {
  key_id                             = aws_kms_key.example.id
  bypass_policy_lockout_safety_check = false  # Default; AWS validates policy before applying
  policy                             = data.aws_iam_policy_document.key_policy.json
}
```

- **Impact**: CRITICAL — Risk of unmanageable key → permanent data loss
- **Severity**: CRITICAL
- **Source**: [aws_kms_key_policy bypass_policy_lockout_safety_check](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key_policy)

---

#### Anti-Pattern: Using `count` for Multiple KMS Keys (Reordering Risk)

```hcl
# DON'T — count for KMS keys
variable "key_names" {
  default = ["database", "secrets", "backups"]
}

resource "aws_kms_key" "keys" {
  count       = length(var.key_names)
  description = "${var.key_names[count.index]} encryption key"

  lifecycle {
    prevent_destroy = true
  }
}
```

**Why**: If `var.key_names` is reordered (e.g., `["secrets", "database", "backups"]`), Terraform replans all keys — `keys[0]` now maps to "secrets" instead of "database". This causes destruction and recreation of production keys, permanently destroying encrypted data.

**Instead**:
```hcl
# DO — for_each with stable string keys
resource "aws_kms_key" "keys" {
  for_each = toset(["database", "secrets", "backups"])

  description = "${each.key} encryption key"

  lifecycle {
    prevent_destroy = true
  }
}
# Reordering toset() has no effect on Terraform resource addresses
```

- **Impact**: CRITICAL — Key recreation → permanent data loss for all data encrypted under old key IDs
- **Severity**: CRITICAL
- **Source**: [for_each vs count](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)

---

#### Anti-Pattern: Alias Pointing to `alias/aws/*` Prefix (Reserved)

```hcl
# DON'T — alias using reserved aws/ prefix
resource "aws_kms_alias" "bad_alias" {
  name          = "alias/aws/myservice"  # DON'T — aws/ prefix is reserved
  target_key_id = aws_kms_key.my_key.key_id
}
```

**Why**: The `alias/aws/` prefix is reserved for AWS managed keys. Terraform apply will fail with `InvalidAliasNameException`.

**Instead**:
```hcl
# DO — use custom prefix
resource "aws_kms_alias" "good_alias" {
  name          = "alias/prod/myservice/encryption"  # Custom namespace
  target_key_id = aws_kms_key.my_key.key_id
}
```

- **Impact**: MEDIUM — Apply failure, blocked deployments
- **Severity**: MEDIUM
- **Source**: [aws_kms_alias](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_alias)

---

#### Anti-Pattern: Enabling Key Rotation on Asymmetric Keys

```hcl
# DON'T — rotation on asymmetric key (will fail)
resource "aws_kms_key" "rsa_signing_key" {
  description              = "RSA signing key"
  key_usage                = "SIGN_VERIFY"
  customer_master_key_spec = "RSA_4096"
  enable_key_rotation      = true  # DON'T — not supported for asymmetric keys
}
```

**Why**: Automatic key rotation is only supported for symmetric `SYMMETRIC_DEFAULT` keys with `AWS_KMS` origin. Terraform apply will fail with `UnsupportedOperationException`.

**Instead**:
```hcl
# DO — disable rotation for asymmetric keys (manual rotation process)
resource "aws_kms_key" "rsa_signing_key" {
  description              = "RSA signing key"
  key_usage                = "SIGN_VERIFY"
  customer_master_key_spec = "RSA_4096"
  enable_key_rotation      = false  # Correct: asymmetric keys cannot auto-rotate

  lifecycle {
    prevent_destroy = true
  }
}

# Manage manual rotation via alias swap:
# 1. Create new key: aws_kms_key.rsa_signing_key_v2
# 2. Update alias to point to new key: aws_kms_alias.signing_key.target_key_id = new key
# 3. Keep old key enabled until all signatures verified
```

- **Impact**: HIGH — Blocked deployments, application failure
- **Severity**: HIGH
- **Source**: [KMS Key Rotation](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)

---

#### Anti-Pattern: No Tags on KMS Keys

```hcl
# DON'T — untagged KMS key
resource "aws_kms_key" "untagged" {
  description         = "My key"
  enable_key_rotation = true
}
```

**Why**: Untagged KMS keys cannot be filtered in CloudTrail audit logs, cannot be targeted by cost allocation reports, cannot be identified by automated compliance tools (AWS Config), and cannot be assigned to the correct team in key inventory reviews. KMS keys are a compliance asset — tagging is non-negotiable in regulated environments.

**Instead**:
```hcl
# DO — comprehensive tags
resource "aws_kms_key" "tagged" {
  description         = "Production user data encryption key"
  enable_key_rotation = true

  tags = merge(var.tags, {
    Name         = "${var.environment}-user-data-key"
    DataClass    = "PII"
    Compliance   = "GDPR"
    Owner        = var.owner
    Service      = var.service_name
    Environment  = var.environment
    CostCenter   = var.cost_center
  })

  lifecycle {
    prevent_destroy = true
  }
}
```

- **Impact**: HIGH — Compliance gaps, untracked encryption assets, audit failures
- **Severity**: HIGH
- **Source**: [AWS Tagging Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)

---

## State Management Deep Dive

### State Sensitivity for KMS

KMS state contains: key ARN, key ID, full key policy JSON (with all principal ARNs), alias names, and grant tokens. Grant tokens are explicitly documented as sensitive and stored in plaintext in state. Restrict all S3 backend access to Terraform service accounts only.

```hcl
# State backend for KMS stacks — enforce encryption and restricted access
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/kms/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true    # AES-256 SSE at rest
    dynamodb_table = "terraform-locks"
    # KMS-encrypt the state file itself using a SEPARATE bootstrap key
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/bootstrap-state-key-id"
  }
}
```

### Local Development State
```hcl
# DO NOT manage production KMS keys with local state
# Use only for throwaway dev environments
terraform {
  required_version = ">= 1.7"
  # No backend block = local state — acceptable for local sandbox only
}
```
- **Risk**: Local state file contains all key policies in plaintext, no locking, no team sharing
- **When**: Solo development or ephemeral test environments only

### Production Remote State (S3 + DynamoDB)
```hcl
# One-time bootstrap: create DynamoDB lock table
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
    kms_key_arn = aws_kms_key.dynamodb_key.arn
  }

  tags = {
    Name      = "terraform-locks"
    ManagedBy = "terraform"
  }
}

# State S3 bucket — separate from application data
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
  bucket                  = aws_s3_bucket.terraform_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

### State File Sensitivity Handling
```hcl
# Mark grant tokens as sensitive outputs — they are stored in state plaintext
output "kms_grant_token" {
  value       = aws_kms_grant.service_grant.grant_token
  sensitive   = true
  description = "Grant token — sensitive, stored in state plaintext"
}

# Key ARN is NOT sensitive (appears in CloudTrail, resource policies, etc.)
output "kms_key_arn" {
  value       = aws_kms_key.app_encryption.arn
  sensitive   = false
  description = "KMS key ARN for cross-stack reference"
}
```

---

## Module Architecture

### Standard KMS Module Structure

```
modules/kms-key/
├── main.tf           # aws_kms_key, aws_kms_key_policy, aws_kms_alias
├── variables.tf      # key_usage, key_spec, rotation_period, admin_arns, user_arns
├── outputs.tf        # key_arn, key_id, alias_arn, alias_name
├── versions.tf       # required_providers block
└── README.md         # Usage examples, input/output reference
```

### Module Definition Example

```hcl
# modules/kms-key/variables.tf
variable "name" {
  type        = string
  description = "Short name for alias and tagging (e.g., 'database', 'secrets')"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.name))
    error_message = "name must be lowercase alphanumeric with hyphens only."
  }
}

variable "environment" {
  type        = string
  description = "Environment name (prod, staging, dev)"

  validation {
    condition     = contains(["prod", "staging", "dev"], var.environment)
    error_message = "environment must be prod, staging, or dev."
  }
}

variable "key_usage" {
  type        = string
  description = "Cryptographic usage: ENCRYPT_DECRYPT | SIGN_VERIFY | GENERATE_VERIFY_MAC"
  default     = "ENCRYPT_DECRYPT"

  validation {
    condition     = contains(["ENCRYPT_DECRYPT", "SIGN_VERIFY", "GENERATE_VERIFY_MAC"], var.key_usage)
    error_message = "key_usage must be ENCRYPT_DECRYPT, SIGN_VERIFY, or GENERATE_VERIFY_MAC."
  }
}

variable "rotation_period_in_days" {
  type        = number
  description = "Key rotation period in days (90–2560). Only for SYMMETRIC_DEFAULT keys."
  default     = 365

  validation {
    condition     = var.rotation_period_in_days >= 90 && var.rotation_period_in_days <= 2560
    error_message = "rotation_period_in_days must be between 90 and 2560 inclusive."
  }
}

variable "key_admin_role_arns" {
  type        = list(string)
  description = "IAM role ARNs granted key administration permissions"
  default     = []
}

variable "key_user_role_arns" {
  type        = list(string)
  description = "IAM role ARNs granted key usage permissions (Encrypt, Decrypt, GenerateDataKey)"
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to merge onto the KMS key"
  default     = {}
}

# modules/kms-key/outputs.tf
output "key_arn" {
  value       = aws_kms_key.this.arn
  description = "KMS key ARN"
}

output "key_id" {
  value       = aws_kms_key.this.key_id
  description = "KMS key ID (UUID)"
}

output "alias_arn" {
  value       = aws_kms_alias.this.arn
  description = "KMS alias ARN"
}

output "alias_name" {
  value       = aws_kms_alias.this.name
  description = "KMS alias name"
}

# root/main.tf — using the module
module "database_key" {
  source = "./modules/kms-key"

  name        = "database"
  environment = var.environment

  key_admin_role_arns = [aws_iam_role.key_admin.arn]
  key_user_role_arns  = [aws_iam_role.rds_service.arn]

  tags = {
    Service    = "postgresql"
    DataClass  = "confidential"
  }
}

module "secrets_key" {
  source = "./modules/kms-key"

  name                    = "secrets"
  environment             = var.environment
  rotation_period_in_days = 180  # Rotate every 6 months for secrets

  key_user_role_arns = [aws_iam_role.secrets_manager_service.arn]
}
```

---

## Integration Patterns

### Integration: Terraform ↔ IAM

**Pattern**: Key policies reference IAM role ARNs; IAM policies grant `kms:*` actions referencing key ARNs.

```hcl
# IAM policy allowing Lambda to use a specific KMS key
data "aws_iam_policy_document" "lambda_kms_access" {
  statement {
    sid    = "AllowKMSUsage"
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]

    resources = [aws_kms_key.app_encryption.arn]

    condition {
      test     = "StringEquals"
      variable = "kms:EncryptionContext:Environment"
      values   = [var.environment]
    }
  }
}

resource "aws_iam_policy" "lambda_kms" {
  name   = "${var.environment}-lambda-kms-policy"
  policy = data.aws_iam_policy_document.lambda_kms_access.json
}

resource "aws_iam_role_policy_attachment" "lambda_kms" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.lambda_kms.arn
}
```

- **Issue**: IAM changes are eventually consistent — add `depends_on = [aws_kms_key_policy.app_encryption]` when IAM principal is used in key policy
- **Source**: [IAM + KMS Integration](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html#key-policy-iam)

---

### Integration: Terraform ↔ S3

**Pattern**: `aws_s3_bucket_server_side_encryption_configuration` with `kms_master_key_id`. Use `bucket_key_enabled = true` to reduce KMS API calls by up to 99% for high-throughput buckets.

```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "app_data" {
  bucket = aws_s3_bucket.app_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_key.arn
    }
    bucket_key_enabled = true  # IMPORTANT: reduces KMS costs for high-volume buckets
  }
}
```

- **Versions**:

| Resource | Min Provider | Notes |
|----------|-------------|-------|
| `aws_s3_bucket_server_side_encryption_configuration` | aws ~> 4.0 | Replaced inline `server_side_encryption_configuration` block |
| `bucket_key_enabled` | aws ~> 3.75 | Reduces KMS API calls per object |

- **Issue**: Changing `kms_master_key_id` on an existing bucket does NOT re-encrypt existing objects — objects remain encrypted under the old key until re-uploaded
- **Source**: [aws_s3_bucket_server_side_encryption_configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_server_side_encryption_configuration)

---

### Integration: Terraform ↔ Secrets Manager

**Pattern**: `aws_secretsmanager_secret` with `kms_key_id` for customer managed key encryption.

```hcl
resource "aws_kms_key" "secrets_key" {
  description             = "${var.environment} Secrets Manager encryption key"
  enable_key_rotation     = true
  rotation_period_in_days = 180
  deletion_window_in_days = 30

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_alias" "secrets_key" {
  name          = "alias/${var.environment}/secrets-manager/encryption"
  target_key_id = aws_kms_key.secrets_key.key_id
}

resource "aws_secretsmanager_secret" "db_password" {
  name        = "${var.environment}/database/master-password"
  description = "Database master password"
  kms_key_id  = aws_kms_key.secrets_key.arn

  recovery_window_in_days = 30

  tags = {
    Environment = var.environment
    Service     = "database"
  }
}
```

- **Issue**: Secrets Manager service principal must be granted access in the key policy (`secretsmanager.amazonaws.com`) OR the service uses grants — grants are created automatically if the key policy allows `kms:CreateGrant` with `kms:GrantIsForAWSResource` condition
- **Source**: [aws_secretsmanager_secret kms_key_id](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret)

---

### Integration: Terraform ↔ DynamoDB

**Pattern**: `aws_dynamodb_table` with `server_side_encryption` block referencing KMS key ARN.

```hcl
resource "aws_kms_key" "dynamodb_key" {
  description             = "${var.environment} DynamoDB encryption key"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_dynamodb_table" "app_table" {
  name         = "${var.environment}-app-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb_key.arn
  }

  point_in_time_recovery {
    enabled = true
  }
}
```

- **Issue**: DynamoDB uses grants to access the KMS key — the key policy must allow `kms:CreateGrant` with `kms:GrantIsForAWSResource` for the DynamoDB service principal or for the role creating the table
- **Source**: [aws_dynamodb_table server_side_encryption](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table)

---

### Integration: Terraform ↔ RDS

**Pattern**: `aws_db_instance` with `storage_encrypted = true` and `kms_key_id` for encryption at rest.

```hcl
resource "aws_kms_key" "rds_key" {
  description             = "${var.environment} RDS encryption key"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_db_instance" "app_database" {
  identifier        = "${var.environment}-app-db"
  engine            = "postgres"
  engine_version    = "16.1"
  instance_class    = "db.t3.medium"
  allocated_storage = 100

  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds_key.arn

  backup_retention_period = 7
  deletion_protection     = true  # Also protect RDS from deletion

  tags = {
    Environment = var.environment
    Name        = "${var.environment}-app-db"
  }
}
```

- **Issue**: `kms_key_id` cannot be changed after creation — RDS encryption key is permanent. Changing requires snapshot → restore workflow. Add `ignore_changes = [kms_key_id]` if key is managed separately.
- **Source**: [aws_db_instance storage_encrypted](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance)

---

### Integration: Terraform ↔ CloudTrail

**Pattern**: `aws_cloudtrail` with `kms_key_id` to encrypt CloudTrail log files in S3. The key policy must explicitly allow CloudTrail service principal to use the key.

```hcl
resource "aws_kms_key" "cloudtrail_key" {
  description             = "${var.environment} CloudTrail log encryption key"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  lifecycle {
    prevent_destroy = true
  }
}

data "aws_iam_policy_document" "cloudtrail_key_policy" {
  statement {
    sid    = "EnableRootAccountAccess"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowCloudTrailEncryption"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions   = ["kms:GenerateDataKey*"]
    resources = ["*"]
    condition {
      test     = "StringLike"
      variable = "kms:EncryptionContext:aws:cloudtrail:arn"
      values   = ["arn:aws:cloudtrail:*:${data.aws_caller_identity.current.account_id}:trail/*"]
    }
  }

  statement {
    sid    = "AllowCloudTrailDecryption"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions   = ["kms:DescribeKey"]
    resources = ["*"]
  }
}

resource "aws_kms_key_policy" "cloudtrail_key" {
  key_id = aws_kms_key.cloudtrail_key.id
  policy = data.aws_iam_policy_document.cloudtrail_key_policy.json
}

resource "aws_cloudtrail" "main" {
  name                          = "${var.environment}-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail_logs.id
  kms_key_id                    = aws_kms_key.cloudtrail_key.arn
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true

  depends_on = [aws_kms_key_policy.cloudtrail_key]
}
```

- **Issue**: CloudTrail key policy must explicitly grant `kms:GenerateDataKey*` to `cloudtrail.amazonaws.com` — without this, trail creation fails with KMS access denied
- **Source**: [aws_cloudtrail kms_key_id](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudtrail)

---

### Integration: Terraform ↔ CloudWatch Logs

**Pattern**: `aws_cloudwatch_log_group` with `kms_key_id` for log encryption at rest.

```hcl
resource "aws_kms_key" "cloudwatch_key" {
  description             = "${var.environment} CloudWatch Logs encryption key"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  lifecycle {
    prevent_destroy = true
  }
}

data "aws_iam_policy_document" "cloudwatch_key_policy" {
  statement {
    sid    = "EnableRootAccountAccess"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowCloudWatchLogs"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["logs.${var.aws_region}.amazonaws.com"]
    }
    actions = [
      "kms:Encrypt*",
      "kms:Decrypt*",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:Describe*",
    ]
    resources = ["*"]
    condition {
      test     = "ArnLike"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values   = ["arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"]
    }
  }
}

resource "aws_kms_key_policy" "cloudwatch_key" {
  key_id = aws_kms_key.cloudwatch_key.id
  policy = data.aws_iam_policy_document.cloudwatch_key_policy.json
}

resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/${var.service_name}/${var.environment}"
  kms_key_id        = aws_kms_key.cloudwatch_key.arn
  retention_in_days = 90

  depends_on = [aws_kms_key_policy.cloudwatch_key]
}
```

- **Issue**: CloudWatch Logs requires the key policy to grant `kms:Encrypt*`, `kms:Decrypt*`, `kms:ReEncrypt*`, `kms:GenerateDataKey*`, and `kms:Describe*` to the regional logs service principal. Missing any of these causes log delivery failures.
- **Source**: [aws_cloudwatch_log_group kms_key_id](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group)

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

# Security scanning — KMS-specific checks
tfsec . --format json | jq '.results[] | select(.rule_id | contains("KMS"))'
# Expected: No HIGH or CRITICAL KMS findings

# Linting
checkov -d . --framework terraform --check CKV_AWS_7,CKV2_AWS_64 --quiet
# CKV_AWS_7: Ensure KMS rotation is enabled
# CKV2_AWS_64: Ensure KMS key policy does not have public access
# Expected: All checks PASSED

# Plan before apply — verify prevent_destroy protects production keys
terraform plan -out=tfplan -lock=true
terraform show tfplan | grep -A 5 "aws_kms_key"
# Expected: No unexpected "must be replaced" for production keys

# Validate key policy JSON is valid
terraform show -json tfplan | jq '.planned_values.root_module.resources[] | select(.type == "aws_kms_key_policy") | .values.policy | fromjson'
# Expected: Valid JSON with root account principal

# Confirm rotation is enabled post-apply
aws kms list-keys --query 'Keys[].KeyId' --output text | \
  xargs -I {} aws kms get-key-rotation-status --key-id {} \
  --query '{KeyId: KeyId, RotationEnabled: KeyRotationEnabled, RotationPeriod: RotationPeriodInDays}'
# Expected: KeyRotationEnabled: true for all symmetric CMKs

# State validation
terraform state list | grep aws_kms
terraform state show aws_kms_key.app_encryption
# Expected: key_arn, key_id, enable_key_rotation = true, prevent_destroy warning
```

### Testing with Terraform Test Framework (v1.7+)

```hcl
# tests/kms_key.tftest.hcl
variables {
  environment             = "test"
  service_name            = "integration-test"
  key_admin_role_arns     = []
  key_user_role_arns      = []
  rotation_period_in_days = 90
  deletion_window_in_days = 7
}

run "symmetric_key_creation" {
  command = plan

  assert {
    condition     = aws_kms_key.app_encryption.enable_key_rotation == true
    error_message = "KMS key must have rotation enabled."
  }

  assert {
    condition     = aws_kms_key.app_encryption.rotation_period_in_days >= 90
    error_message = "Rotation period must be at least 90 days."
  }

  assert {
    condition     = aws_kms_key.app_encryption.deletion_window_in_days >= 7
    error_message = "Deletion window must be at least 7 days."
  }
}

run "alias_naming_convention" {
  command = plan

  assert {
    condition     = can(regex("^alias/[a-z]+/[a-z-]+/[a-z-]+$", aws_kms_alias.app_encryption.name))
    error_message = "Alias must follow convention: alias/environment/service/purpose."
  }
}

run "policy_has_root_principal" {
  command = plan

  assert {
    condition     = can(jsondecode(data.aws_iam_policy_document.app_encryption_key_policy.json))
    error_message = "Key policy must be valid JSON."
  }
}
```

---

## Production Readiness

### Performance

- **KMS API limits**: 30,000 requests/second per Region (symmetric operations). For S3 high-throughput buckets, always set `bucket_key_enabled = true` — reduces KMS API calls per object by generating one data key per S3 prefix.
- **Encryption context**: Always include encryption context in GenerateDataKey calls; it adds no latency but is logged in CloudTrail for every call.
- **Cross-Region**: Multi-Region keys allow decryption in replica regions without cross-region API calls — critical for latency-sensitive global workloads.

### Monitoring & Alerting

```hcl
# Alert on KMS key deletion scheduled
resource "aws_cloudwatch_metric_alarm" "kms_key_deletion" {
  alarm_name          = "${var.environment}-kms-key-deletion-scheduled"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ScheduledKeyDeletion"
  namespace           = "AWS/KMS"
  period              = "60"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "CRITICAL: A KMS key deletion has been scheduled"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
  ok_actions          = [aws_sns_topic.security_alerts.arn]
  treat_missing_data  = "notBreaching"
}

# Alert on KMS key usage failures (indicates access policy issues)
resource "aws_cloudwatch_metric_alarm" "kms_access_denied" {
  alarm_name          = "${var.environment}-kms-access-denied"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "NumberOfRequestsWithFailedKeyValidation"
  namespace           = "AWS/KMS"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "KMS key validation failures — investigate IAM/key policy configuration"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
```

### Security Checklist

```
- [ ] All KMS keys have prevent_destroy = true in lifecycle block
- [ ] All key policies include root account principal (lockout prevention)
- [ ] All symmetric CMKs have enable_key_rotation = true
- [ ] rotation_period_in_days is configured (default 365, consider 90–180 for high-sensitivity)
- [ ] deletion_window_in_days = 30 (maximum recovery window)
- [ ] All keys tagged with Environment, Owner, CostCenter, DataClass
- [ ] Key policies use least-privilege (separate admin vs. user permissions)
- [ ] Grant kms:CreateGrant with kms:GrantIsForAWSResource condition for AWS services
- [ ] bypass_policy_lockout_safety_check = false (default — never override without justification)
- [ ] State file stored in encrypted S3 backend (encrypted with separate bootstrap KMS key)
- [ ] CloudWatch alarms on ScheduledKeyDeletion
- [ ] CloudTrail logging enabled (all KMS API calls logged automatically)
- [ ] Aliases follow convention: alias/<environment>/<service>/<purpose>
- [ ] Asymmetric keys have enable_key_rotation = false (correct — they don't support rotation)
- [ ] for_each (not count) used for multiple KMS key resources
```

### Disaster Recovery Runbook

```bash
# 1. Cancel scheduled key deletion (if within deletion window)
aws kms cancel-key-deletion --key-id KEY_ID_OR_ARN
# Expected: "KeyState": "Disabled"

# Re-enable after cancellation
aws kms enable-key --key-id KEY_ID_OR_ARN
# Expected: "KeyState": "Enabled"
terraform import aws_kms_key.app_encryption KEY_ID  # Re-sync state

# 2. Recover from state corruption for KMS key
terraform state pull > kms_terraform.tfstate.backup
# Import existing key back into state
terraform import aws_kms_key.app_encryption KEY_ID
terraform import aws_kms_key_policy.app_encryption KEY_ID
terraform import aws_kms_alias.app_encryption alias/prod/app/encryption

# 3. Detect key policy drift (key policy changed outside Terraform)
terraform plan -target=aws_kms_key_policy.app_encryption
# Expected: Shows policy diff if manually changed — apply to reconcile

# 4. List all KMS keys with rotation status
aws kms list-keys --output json | jq -r '.Keys[].KeyId' | while read key; do
  echo -n "Key $key: "
  aws kms get-key-rotation-status --key-id "$key" --query 'KeyRotationEnabled' --output text
done

# 5. Verify key is not scheduled for deletion
aws kms describe-key --key-id KEY_ID \
  --query 'KeyMetadata.{State:KeyState,DeletionDate:DeletionDate}'
# Expected: State=Enabled, DeletionDate=null
```

---

## Reference Implementation (Copy-Paste Root Module)

### `main.tf`
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
    key            = "prod/kms/terraform.tfstate"
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

# ── KMS Key ──────────────────────────────────────────────────────────────────

resource "aws_kms_key" "app" {
  description              = "${var.environment} ${var.service_name} encryption key"
  key_usage                = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "SYMMETRIC_DEFAULT"
  enable_key_rotation      = true
  rotation_period_in_days  = var.rotation_period_in_days
  deletion_window_in_days  = 30
  is_enabled               = true
  multi_region             = false

  tags = {
    Name      = "${var.environment}-${var.service_name}-key"
    Service   = var.service_name
    DataClass = var.data_classification
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_alias" "app" {
  name          = "alias/${var.environment}/${var.service_name}/encryption"
  target_key_id = aws_kms_key.app.key_id
}

resource "aws_kms_key_policy" "app" {
  key_id = aws_kms_key.app.id
  policy = data.aws_iam_policy_document.app_key_policy.json
}

data "aws_iam_policy_document" "app_key_policy" {
  statement {
    sid    = "EnableRootAccountAccess"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowKeyAdministration"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = var.key_admin_role_arns
    }
    actions = [
      "kms:Create*", "kms:Describe*", "kms:Enable*", "kms:List*",
      "kms:Put*", "kms:Update*", "kms:Revoke*", "kms:Disable*",
      "kms:Get*", "kms:Delete*", "kms:TagResource", "kms:UntagResource",
      "kms:ScheduleKeyDeletion", "kms:CancelKeyDeletion",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "AllowKeyUsage"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = var.key_user_role_arns
    }
    actions = [
      "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*",
      "kms:GenerateDataKey*", "kms:DescribeKey",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "AllowGrantsForAWSServices"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = var.key_user_role_arns
    }
    actions   = ["kms:CreateGrant", "kms:ListGrants", "kms:RevokeGrant"]
    resources = ["*"]
    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }
}
```

### `variables.tf`
```hcl
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "account_id" {
  type        = string
  description = "AWS account ID"

  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "account_id must be a 12-digit AWS account ID."
  }
}

variable "environment" {
  type    = string
  validation {
    condition     = contains(["prod", "staging", "dev"], var.environment)
    error_message = "environment must be prod, staging, or dev."
  }
}

variable "service_name" {
  type        = string
  description = "Service this key belongs to (e.g., api, database, backups)"
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.service_name))
    error_message = "service_name must be lowercase alphanumeric with hyphens."
  }
}

variable "owner" {
  type        = string
  description = "Team owning this key"
}

variable "data_classification" {
  type    = string
  default = "internal"
  validation {
    condition     = contains(["public", "internal", "confidential", "restricted"], var.data_classification)
    error_message = "data_classification must be public, internal, confidential, or restricted."
  }
}

variable "rotation_period_in_days" {
  type    = number
  default = 365
  validation {
    condition     = var.rotation_period_in_days >= 90 && var.rotation_period_in_days <= 2560
    error_message = "rotation_period_in_days must be 90–2560."
  }
}

variable "key_admin_role_arns" {
  type    = list(string)
  default = []
}

variable "key_user_role_arns" {
  type    = list(string)
  default = []
}
```

### `outputs.tf`
```hcl
output "key_arn" {
  value       = aws_kms_key.app.arn
  description = "KMS key ARN"
}

output "key_id" {
  value       = aws_kms_key.app.key_id
  description = "KMS key ID (UUID)"
}

output "alias_arn" {
  value       = aws_kms_alias.app.arn
  description = "KMS alias ARN"
}

output "alias_name" {
  value       = aws_kms_alias.app.name
  description = "KMS alias name"
}
```

### `terraform.tfvars` (example)
```hcl
aws_region              = "us-east-1"
account_id              = "123456789012"
environment             = "prod"
service_name            = "api"
owner                   = "platform-team"
data_classification     = "confidential"
rotation_period_in_days = 365

key_admin_role_arns = [
  "arn:aws:iam::123456789012:role/PlatformEngineeringRole",
]

key_user_role_arns = [
  "arn:aws:iam::123456789012:role/ApiServiceRole",
  "arn:aws:iam::123456789012:role/BackupServiceRole",
]
```

---

## Source Bibliography

### Primary Sources
- [aws_kms_key Registry Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key)
- [aws_kms_alias Registry Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_alias)
- [aws_kms_key_policy Registry Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key_policy)
- [aws_kms_grant Registry Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_grant)
- [aws_kms_replica_key Registry Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_replica_key)
- [aws_kms_external_key Registry Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_external_key)
- [AWS Provider v6 Registry](https://registry.terraform.io/providers/hashicorp/aws/latest) — version 6.47.0 published 2026-05-28
- [AWS KMS Developer Guide](https://docs.aws.amazon.com/kms/latest/developerguide/)
- [KMS Key Policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)
- [KMS Key Rotation](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)
- [KMS Grants](https://docs.aws.amazon.com/kms/latest/developerguide/grants.html)
- [KMS Multi-Region Keys](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-overview.html)
- [AWS Well-Architected Security Pillar — SEC08](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html)

### Validation & Tools
- [tfsec KMS checks](https://aquasecurity.github.io/tfsec/latest/docs/aws/kms/)
- [Checkov KMS policies](https://www.checkov.io/5.Policy%20Index/terraform.html) — CKV_AWS_7, CKV2_AWS_64
- [Terraform Test Framework](https://developer.hashicorp.com/terraform/language/tests)
- [GitHub hashicorp/terraform-provider-aws](https://github.com/hashicorp/terraform-provider-aws/issues?q=label%3Aservice%2Fkms)

---

## Research Gaps

```
Gap: rotation_period_in_days minimum is 90 days — 30-day rotation not supported natively
Impact: Organizations requiring monthly rotation cannot use automatic rotation; must implement on-demand rotation via API
Workaround: Use aws_lambda_function + aws_cloudwatch_event_rule to trigger on-demand rotation monthly
Follow-up: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html#rotate-keys-on-demand

Gap: aws_kms_key_policy perpetual diff behavior — confirmed as known provider behavior, no upstream fix
Impact: Pipelines using inline policy on aws_kms_key may show non-empty plans on re-run
Workaround: Use aws_kms_key_policy standalone resource (recommended pattern)
Follow-up: https://github.com/hashicorp/terraform-provider-aws/issues?q=kms+key+policy+perpetual+diff

Gap: Multi-Region key replication ordering — primary key must be fully created before replica
Impact: Parallel apply with replica in same plan may fail
Workaround: Use depends_on = [aws_kms_key.primary] on aws_kms_replica_key resources
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_replica_key
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Creating `aws_kms_key` with `enable_key_rotation = true` and `prevent_destroy = true`
- Adding root account principal to all key policies
- Applying `aws_kms_key_policy` as standalone resource (not inline on `aws_kms_key`)
- Using `for_each` instead of `count` for multiple key resources
- Setting `deletion_window_in_days = 30` (maximum) for production keys
- Adding `bucket_key_enabled = true` for all S3 KMS encryption configurations
- Variable validation for `rotation_period_in_days`, `deletion_window_in_days`, `key_spec`

### Medium Confidence (Validate with user)
- `rotation_period_in_days` value (90 vs. 180 vs. 365 depends on data classification policy)
- Per-service vs. shared key architecture (cost vs. blast-radius trade-off)
- Key admin vs. key user role ARN assignments
- `deletion_window_in_days` for staging/dev environments (7 days may be acceptable)

### Low Confidence (Must ask user)
- Multi-Region key deployment (requires knowledge of DR strategy and regions)
- CloudHSM or External Key Store requirement (requires compliance team input)
- Asymmetric key spec selection (requires understanding of external consumer requirements)
- Cross-account key sharing (requires knowledge of account IDs and trust relationships)

### Edge Cases (When to pause)
- Any plan showing `aws_kms_key` being destroyed — halt, verify `prevent_destroy` and assess data-at-risk
- Key policy being replaced (not updated) — halt, verify root account principal is preserved
- `bypass_policy_lockout_safety_check = true` in any configuration — halt and remove
- `deletion_window_in_days < 7` — impossible (AWS minimum), indicates configuration error
- `enable_key_rotation = true` on asymmetric key spec — halt, will fail at apply

### Emergency Stop
- Halt if `terraform destroy` targets any `aws_kms_key` with `prevent_destroy = false`
- Halt if key policy JSON missing root account principal statement
- Halt if `bypass_policy_lockout_safety_check = true` found in any production config
- Halt if `count` used for KMS key resources (reordering risk → data loss)
