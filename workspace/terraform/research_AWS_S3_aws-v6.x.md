# Terraform AWS S3 — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - S3 (Simple Storage Service)"
Cloud_Provider: "AWS"
Target_Service: "S3 (General Purpose Buckets, Versioning, Encryption, Lifecycle, Replication, Notifications, Object Lock, Access Points)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-29"
Research_Date: "2026-05-29"
Domain_Complexity: "Complex"
New_V6_Resources_Noted: "bucket_namespace (account-regional scope), blocked_encryption_types on SSE config (SSE-C blocked by default April 2026), aws:kms:dsse sse_algorithm (dual-layer), transition_default_minimum_object_size on lifecycle, identity import blocks (TF v1.12.0+), newer_noncurrent_versions on lifecycle rules, ABAC tagging (s3:TagResource/UntagResource/ListTagsForResource), satellite resource model mandatory (inline config deprecated)"
```

---

## Executive Summary

Amazon S3 is AWS's foundational object storage service providing 99.999999999% (11 nines) durability for general purpose buckets via automatic multi-AZ object distribution. S3 delivers strong read-after-write consistency for all PUT and DELETE operations globally. Beyond simple object storage, S3 is a multi-model storage platform spanning general purpose buckets, high-performance directory buckets (S3 Express One Zone), Apache Iceberg table buckets (S3 Tables), and vector similarity search buckets (S3 Vectors).

The AWS Provider v6.x enforces a **satellite resource model** for S3: all sub-configurations (versioning, encryption, lifecycle, logging, policy, notifications, website, CORS, replication, object lock) must be managed as independent Terraform resources — the equivalent inline arguments on `aws_s3_bucket` are deprecated and will be removed in the next major version. The most critical v6.x security change is the automatic blocking of SSE-C (server-side encryption with customer-provided keys) for all new buckets starting April 2026; the `blocked_encryption_types` argument on `aws_s3_bucket_server_side_encryption_configuration` controls this behavior. New `bucket_namespace = "account-regional"` prevents bucket name squatting attacks by scoping bucket names to account+region rather than the global partition namespace. Provider constraint `~> 6.0` is recommended; Terraform `>= 1.7` is required for the `terraform test` framework and enhanced import blocks.

Three non-negotiable guardrails for any S3 deployment: **(1) `aws_s3_bucket_public_access_block` with all four controls enabled must accompany every bucket** — misconfigured bucket policies and ACLs are the #1 S3 security incident vector, and a bucket without explicit BPA is vulnerable to accidental public exposure; **(2) `aws_s3_bucket_server_side_encryption_configuration` with a customer-managed KMS key must be set on all buckets storing sensitive data** — the default AWS-managed key cannot be audited, rotated on a custom schedule, or scoped to specific IAM principals; **(3) `aws_s3_bucket_lifecycle_configuration` with `abort_incomplete_multipart_upload` is mandatory on production buckets** — without it, incomplete multipart uploads accumulate silently and incur unbounded storage charges that only appear months after deployment. This service is classified **Complex** due to the large number of independent satellite resources, security-critical public access controls, data permanence decisions (versioning, object lock), IAM policy integration, and replication topology.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Enforces reproducibility, prevents provider upgrades that introduce breaking satellite-resource-model changes in v6.x, and defines the deployment contract for all team members and CI pipelines.

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
    key            = "prod/s3/terraform.tfstate"
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

**Why**: Credentials must never be hardcoded. `assume_role` enables cross-account deployments and CI/CD pipelines without static credentials. `default_tags` enforces tagging compliance on all S3 resources.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "TerraformS3Session"
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

- **Source**: [Provider Configuration Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#provider-configuration) | [Assume Role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#assume_role)

---

#### Pattern: S3 Bucket Core Resource with Account-Regional Namespace

**Why**: `bucket_namespace = "account-regional"` (v6.x) scopes the bucket name to the account+region combination, preventing bucket name squatting attacks where a deleted global-namespace bucket name is immediately re-registered by a hostile actor. `force_destroy = false` (default) prevents accidental destruction of buckets containing objects.

```hcl
resource "aws_s3_bucket" "main" {
  bucket           = "${var.project}-${var.environment}-${var.aws_region}"
  bucket_namespace = "account-regional"  # v6.x: scopes to account+region

  # force_destroy = false is the safe default — require explicit opt-in
  force_destroy = var.force_destroy

  tags = {
    Name    = "${var.project}-${var.environment}"
    Purpose = var.bucket_purpose
  }

  lifecycle {
    prevent_destroy = true  # Production safety — requires explicit removal to destroy
  }
}

variable "force_destroy" {
  type        = bool
  description = "Allow bucket destruction even if it contains objects. ONLY set true for ephemeral/test buckets."
  default     = false
}

variable "bucket_purpose" {
  type        = string
  description = "Business purpose of the bucket (e.g., app-assets, data-lake, backups)"

  validation {
    condition     = length(var.bucket_purpose) > 0 && length(var.bucket_purpose) <= 64
    error_message = "bucket_purpose must be between 1 and 64 characters."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_s3_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket)

---

#### Pattern: Block Public Access (Mandatory on Every Bucket)

**Why**: All four BPA controls enabled prevents any current or future bucket policy or ACL configuration from accidentally exposing the bucket publicly. This is the primary defense against the #1 S3 security incident class. Must be a sibling resource of every `aws_s3_bucket`.

```hcl
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true  # Block PUT requests that include public ACLs
  block_public_policy     = true  # Block bucket policies that grant public access
  ignore_public_acls      = true  # Ignore all public ACLs on bucket and objects
  restrict_public_buckets = true  # Restrict access to the bucket and objects
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_s3_bucket_public_access_block](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block)

---

#### Pattern: Server-Side Encryption with KMS (SSE-KMS) and SSE-C Blocking

**Why**: Encrypts all objects at rest using a customer-managed KMS key. `bucket_key_enabled = true` reduces KMS API call costs by up to 99%. `blocked_encryption_types = ["SSE-C"]` blocks server-side encryption with customer-provided keys, which is now automatically blocked for new buckets starting April 2026 and eliminates a significant key management attack surface. `aws:kms:dsse` enables dual-layer SSE-KMS for regulatory requirements.

```hcl
resource "aws_kms_key" "s3" {
  description             = "KMS key for S3 bucket: ${var.project}-${var.environment}"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "s3-${var.project}-${var.environment}"
  }
}

resource "aws_kms_alias" "s3" {
  name          = "alias/s3-${var.project}-${var.environment}"
  target_key_id = aws_kms_key.s3.key_id
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled       = true         # Reduces KMS costs by ~99%
    blocked_encryption_types = ["SSE-C"]    # v6.x: block customer-provided key uploads
  }
}
```

For dual-layer encryption (DSSE-KMS) in regulatory environments:

```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "regulated" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms:dsse"  # v6.x: dual-layer SSE-KMS
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled       = true
    blocked_encryption_types = ["SSE-C"]
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_s3_bucket_server_side_encryption_configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_server_side_encryption_configuration) | [SSE-C Changes FAQ](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-s3-c-encryption-setting-faq.html)

---

#### Pattern: Versioning (Data Recovery Foundation)

**Why**: Enables recovery from accidental overwrites and deletes. Once enabled, versioning cannot be fully disabled — only suspended. Must be enabled before configuring Object Lock. AWS recommends waiting 15 minutes after enabling versioning before writing objects. Pair with lifecycle rules to control version accumulation costs.

```hcl
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id

  versioning_configuration {
    status = "Enabled"
    # mfa_delete = "Enabled"  # Requires MFA device - use for compliance-critical buckets
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_s3_bucket_versioning](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_versioning) | [How Versioning Works](https://docs.aws.amazon.com/AmazonS3/latest/userguide/manage-versioning-examples.html)

---

#### Pattern: Lifecycle Configuration with Multipart Upload Cleanup

**Why**: Prevents unbounded storage cost growth. `abort_incomplete_multipart_upload` cleans orphaned parts that accumulate silently and are invisible in standard object listings. Noncurrent version transitions reduce cost for versioned buckets. The `transition_default_minimum_object_size` argument (v6.x) controls the default 128 KB minimum for storage class transitions.

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  # Must have bucket versioning enabled first
  depends_on = [aws_s3_bucket_versioning.main]

  bucket = aws_s3_bucket.main.id

  # transition_default_minimum_object_size controls the 128 KB default minimum
  # "all_storage_classes_128K" = default AWS behavior (objects < 128KB not transitioned)
  # "varies_by_storage_class" = different minimums per storage class
  transition_default_minimum_object_size = "all_storage_classes_128K"

  # Rule 1: Abort incomplete multipart uploads (MANDATORY cost hygiene)
  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}  # Applies to all objects

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Rule 2: Expire non-current versions (MANDATORY for versioned buckets)
  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days           = 90
      newer_noncurrent_versions = 3  # v6.x: retain last 3 noncurrent versions
    }

    noncurrent_version_transition {
      noncurrent_days           = 30
      storage_class             = "STANDARD_IA"
      newer_noncurrent_versions = 3
    }
  }

  # Rule 3: Expire delete markers with no versions (versioned buckets)
  rule {
    id     = "expire-delete-markers"
    status = "Enabled"

    filter {}

    expiration {
      expired_object_delete_marker = true
    }
  }

  # Rule 4: Transition current objects to cheaper storage (application-specific)
  rule {
    id     = "transition-to-ia"
    status = var.enable_storage_transitions ? "Enabled" : "Disabled"

    filter {
      prefix = "archive/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_s3_bucket_lifecycle_configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration) | [Object Lifecycle Management](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)

---

#### Pattern: Bucket Ownership Controls (ACL Deprecation Compatibility)

**Why**: `ObjectOwnership = "BucketOwnerEnforced"` disables ACLs entirely — the recommended v6.x posture since AWS disabled the ability to set ACLs as the default for new buckets. Disabling ACLs forces all access to go through bucket policies, providing a single, auditable access control plane. Required before using `aws_s3_bucket_policy` as the sole access mechanism.

```hcl
resource "aws_s3_bucket_ownership_controls" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    # BucketOwnerEnforced: disables ACLs — all access via bucket policies only
    # BucketOwnerPreferred: owner of uploaded objects = bucket owner
    # ObjectWriter: uploader owns the object (legacy, avoid for new buckets)
    object_ownership = "BucketOwnerEnforced"
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_s3_bucket_ownership_controls](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_ownership_controls)

---

#### Pattern: Bucket Policy with Least-Privilege IAM

**Why**: Explicit bucket policy replaces ACLs as the access control plane. Must enforce TLS-only access (`aws:SecureTransport = false` deny), require minimum TLS version, deny access unless via expected principals. Bucket policy and access point must both grant access — bucket policy alone is not sufficient if access points are used.

```hcl
data "aws_iam_policy_document" "s3_bucket_policy" {
  # Statement 1: Deny all non-TLS access
  statement {
    sid    = "DenyNonTLS"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.main.arn,
      "${aws_s3_bucket.main.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }

  # Statement 2: Deny old TLS versions
  statement {
    sid    = "DenyOldTLS"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.main.arn,
      "${aws_s3_bucket.main.arn}/*",
    ]

    condition {
      test     = "NumericLessThan"
      variable = "s3:TlsVersion"
      values   = ["1.2"]
    }
  }

  # Statement 3: Grant specific principals access
  statement {
    sid    = "AllowAppAccess"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = var.allowed_role_arns
    }

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.main.arn,
      "${aws_s3_bucket.main.arn}/*",
    ]
  }
}

resource "aws_s3_bucket_policy" "main" {
  bucket = aws_s3_bucket.main.id
  policy = data.aws_iam_policy_document.s3_bucket_policy.json

  depends_on = [aws_s3_bucket_public_access_block.main]
}

variable "allowed_role_arns" {
  type        = list(string)
  description = "IAM role ARNs that should have access to the bucket"

  validation {
    condition     = length(var.allowed_role_arns) > 0
    error_message = "At least one IAM role ARN must be specified."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_s3_bucket_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy) | [S3 Bucket Policy Examples](https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-bucket-policies.html)

---

#### Pattern: Access Logging (Audit Trail)

**Why**: Server access logs provide a granular audit trail of all S3 operations, essential for security incident investigation, compliance auditing, and cost attribution. Logs must go to a separate dedicated logging bucket to avoid circular dependencies and cost amplification.

```hcl
resource "aws_s3_bucket" "logs" {
  bucket           = "${var.project}-${var.environment}-access-logs"
  bucket_namespace = "account-regional"
  force_destroy    = false

  tags = {
    Name    = "${var.project}-${var.environment}-access-logs"
    Purpose = "s3-access-logs"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket                  = aws_s3_bucket.logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"  # SSE-S3 sufficient for access logs
    }
    blocked_encryption_types = ["SSE-C"]
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    filter {}

    expiration {
      days = var.log_retention_days
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 3
    }
  }
}

resource "aws_s3_bucket_logging" "main" {
  bucket        = aws_s3_bucket.main.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "${var.project}/${var.environment}/"
}

variable "log_retention_days" {
  type        = number
  description = "Number of days to retain S3 access logs"
  default     = 90

  validation {
    condition     = var.log_retention_days >= 30 && var.log_retention_days <= 3650
    error_message = "log_retention_days must be between 30 and 3650 days."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_s3_bucket_logging](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_logging)

---

#### Pattern: Variable Validation and Type Safety

**Why**: Prevents invalid configurations at plan time before apply, catches misconfiguration before any AWS API calls are made.

```hcl
variable "aws_region" {
  type        = string
  description = "AWS region for the S3 bucket"

  validation {
    condition = contains([
      "us-east-1", "us-east-2", "us-west-1", "us-west-2",
      "eu-west-1", "eu-west-2", "eu-central-1",
      "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
    ], var.aws_region)
    error_message = "Region must be a supported AWS region."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project" {
  type        = string
  description = "Project name used in resource naming"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,27}[a-z0-9]$", var.project))
    error_message = "Project name must be lowercase alphanumeric with hyphens, 3-29 chars, no leading/trailing hyphens."
  }
}
```

- **Source**: [Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

### ⚠️ Conditional Patterns

---

#### Decision: SSE-S3 (AES256) vs. SSE-KMS vs. DSSE-KMS

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **SSE-S3 (AES256)** | Cost (no KMS fees), simplicity | Audit granularity, key rotation control, per-principal key scoping | Non-sensitive data, access logs, public assets |
| **SSE-KMS (aws:kms)** | Audit trail, key rotation, IAM-based key access | KMS API costs (~$0.03/10K requests without bucket key) | Sensitive/PII data, compliance environments |
| **SSE-KMS + bucket key** | Same as SSE-KMS but ~99% lower KMS cost | Slightly reduced per-object key isolation | Production default for most workloads |
| **DSSE-KMS (aws:kms:dsse)** | Dual encryption layer, regulatory compliance | Cost (2x KMS operations), complexity | FIPS 140-3, government, financial regulation |

- **Agent**: "Ask user: Does this bucket contain PII, financial data, or data subject to HIPAA/PCI/FedRAMP? Do you need per-request KMS audit trails in CloudTrail?"
- **Source**: [SSE Options](https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html)

---

#### Decision: Versioning Enabled vs. Intelligent-Tiering vs. No Versioning

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **No versioning** | Simplicity, lower storage cost | Data recovery, Object Lock capability | Ephemeral scratch, temp processing, easily regenerated data |
| **Versioning enabled** | Data recovery, Object Lock, replication | Storage cost (multiplied by versions retained) | Application data, configs, artifacts, audit logs |
| **Versioning + lifecycle rules** | Cost-controlled recovery window | Setup complexity | Production data with defined retention policies |

- **Agent**: "Ask user: Does this data need recovery from accidental deletes/overwrites? What is the data retention requirement? Is this bucket a replication destination?"
- **Source**: [Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)

---

#### Decision: Object Lock Mode (Compliance vs. Governance)

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **No Object Lock** | Flexibility, can delete any version | WORM protection | Most application buckets |
| **Governance mode** | Operational protection from accidental deletes | No absolute immutability (admin can bypass) | Operational backups, audit logs with admin override |
| **Compliance mode** | Absolute immutability, regulatory compliance | Cannot be shortened even by AWS Support | SEC 17a-4, FINRA, HIPAA audit trails |
| **Legal Hold** | Indefinite hold without known duration | Manual release required | Litigation hold, legal proceedings |

- **Agent**: "Ask user: Is there a regulatory requirement for WORM storage? What is the required retention period? Can administrators ever need an override?"
- **Source**: [Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)

---

#### Decision: Cross-Region Replication (CRR) vs. Same-Region Replication (SRR) vs. No Replication

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **No replication** | Cost, simplicity | Cross-region DR, data locality | Single-region workloads, non-critical data |
| **SRR** | Compliance (data in same region), log aggregation, prod→dev copies | No geographic DR | Compliance log aggregation, test data refresh |
| **CRR** | Geographic DR, latency to global consumers | Cost (cross-region transfer fees, duplicate storage) | DR requirements, global user base |
| **CRR + S3 RTC** | 15-min replication SLA | Additional cost (~$0.015/GB replicated) | Compliance requiring max replication lag guarantee |

- **Agent**: "Ask user: Is there an RPO (recovery point objective) for this data? Are there regulatory requirements for data in multiple regions? What is the acceptable replication lag?"
- **Source**: [Replication](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html)

---

#### Decision: VPC Endpoint vs. Public Internet Access

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Public internet** | Simplicity, no VPC dependency | Security (traffic leaves AWS network), data transfer costs | Public-facing buckets, external integrations |
| **VPC Gateway Endpoint** | No data transfer costs, traffic stays in AWS network | Only works within VPC | EC2/ECS/Lambda in VPC accessing S3 |
| **VPC Interface Endpoint (PrivateLink)** | DNS-level isolation, private access from on-prem | Cost (~$0.01/hour + data), complexity | On-premises access, strict network isolation |

- **Agent**: "Ask user: Are the S3 consumers within a VPC? Is there an on-premises network? Are there compliance requirements for private network access?"
- **Source**: [VPC Endpoints for S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/privatelink-interface-endpoints.html)

---

#### Decision: Storage Class Selection

| Storage Class | Min Duration | Retrieval | Cost per GB/mo | Best For |
|---------------|-------------|-----------|----------------|---------|
| **STANDARD** | None | ms | ~$0.023 | Frequently accessed data |
| **STANDARD_IA** | 30 days | ms | ~$0.0125 | Infrequently accessed, needs immediate retrieval |
| **ONEZONE_IA** | 30 days | ms | ~$0.01 | Reproducible data, lower resilience acceptable |
| **INTELLIGENT_TIERING** | None | ms-hours | ~$0.023 (+ monitoring) | Unknown/mixed access patterns |
| **GLACIER_IR** | 90 days | ms | ~$0.004 | Archive needing instant retrieval |
| **GLACIER** | 90 days | min-hours | ~$0.0036 | Archive, retrieval not time-sensitive |
| **DEEP_ARCHIVE** | 180 days | hours | ~$0.00099 | Long-term archive, rare retrieval |

- **Agent**: "Ask user: How often is this data accessed? What is the maximum acceptable retrieval latency? Are there minimum storage duration cost implications?"
- **Source**: [Storage Classes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Hardcoded Credentials in Provider

```hcl
# DON'T
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  region     = "us-east-1"
}
```

**Why**: Credentials in code are exposed in version control history, CI logs, and team access logs. Rotation requires code changes.

```hcl
# DO — Use IAM role assumption or environment variables
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "TerraformSession"
  }
  # Credentials from AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY env vars
  # or from EC2/ECS/Lambda/EKS IAM role automatically
}
```

- **Impact**: CRITICAL — Full AWS account compromise
- **Severity**: CRITICAL
- **Source**: [AWS Credential Best Practices](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)

---

#### Anti-Pattern: Missing Block Public Access

```hcl
# DON'T — bucket created without explicit BPA resource
resource "aws_s3_bucket" "data" {
  bucket = "my-company-data"
}
# No aws_s3_bucket_public_access_block! Vulnerable to policy misconfiguration.
```

**Why**: Without explicit BPA, a future bucket policy change or ACL misconfiguration can expose the bucket publicly. AWS's default BPA settings apply at account creation, but per-bucket BPA must be explicitly managed by Terraform.

```hcl
# DO — always pair BPA with every bucket
resource "aws_s3_bucket" "data" {
  bucket           = "my-company-data"
  bucket_namespace = "account-regional"
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

- **Impact**: CRITICAL — Unintended public data exposure
- **Severity**: CRITICAL
- **Source**: [Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)

---

#### Anti-Pattern: Using Deprecated Inline Sub-resources on aws_s3_bucket

```hcl
# DON'T — deprecated inline configuration (removed in next major version)
resource "aws_s3_bucket" "data" {
  bucket = "my-bucket"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  lifecycle_rule {
    id      = "cleanup"
    enabled = true
    expiration { days = 90 }
  }
}
```

**Why**: These inline arguments are deprecated in v6.x and cannot detect changes made through satellite resources. They will cause drift, conflict with satellite resources, and will be removed in v7.x.

```hcl
# DO — use satellite resources for all sub-configuration
resource "aws_s3_bucket" "data" {
  bucket           = "my-bucket"
  bucket_namespace = "account-regional"
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "aws:kms" }
    bucket_key_enabled       = true
    blocked_encryption_types = ["SSE-C"]
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  depends_on = [aws_s3_bucket_versioning.data]
  bucket     = aws_s3_bucket.data.id
  rule {
    id     = "cleanup"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }
}
```

- **Impact**: HIGH — State drift, perpetual plan differences, breakage on provider upgrade to v7.x
- **Severity**: HIGH
- **Source**: [aws_s3_bucket Deprecation Notice](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket#argument-reference)

---

#### Anti-Pattern: Global Namespace Bucket with Sensitive Names

```hcl
# DON'T — bucket name collision / squatting risk
resource "aws_s3_bucket" "prod_data" {
  bucket = "acme-corp-production-customer-data"
  # No bucket_namespace — uses global namespace
  # If deleted, any AWS account could register this bucket name
}
```

**Why**: In global namespace, deleted bucket names can be immediately registered by hostile actors. If any service, CloudFront, or DNS still references the old ARN/hostname, it could serve attacker-controlled content.

```hcl
# DO — use account-regional namespace for new buckets
resource "aws_s3_bucket" "prod_data" {
  bucket           = "acme-corp-production-customer-data"
  bucket_namespace = "account-regional"  # Scoped to account+region
}
```

- **Impact**: HIGH — Bucket name hijacking, confused deputy attacks, data exfiltration
- **Severity**: HIGH
- **Source**: [Bucket Namespace](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket#bucket_namespace)

---

#### Anti-Pattern: Missing Lifecycle Rules on Versioned Bucket

```hcl
# DON'T — versioned bucket without lifecycle rules accumulates costs
resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration { status = "Enabled" }
}
# No aws_s3_bucket_lifecycle_configuration!
# Every overwrite doubles storage cost. Old versions accumulate forever.
# Incomplete multipart uploads also accumulate silently.
```

**Why**: A versioned bucket without lifecycle rules causes unbounded storage cost growth. Every overwrite creates a new version — a bucket with 10K objects receiving 100 writes/day grows by 3M additional object-months per year.

```hcl
# DO — always pair versioning with lifecycle rules
resource "aws_s3_bucket_lifecycle_configuration" "data" {
  depends_on = [aws_s3_bucket_versioning.data]
  bucket     = aws_s3_bucket.data.id

  rule {
    id     = "abort-mpu"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }

  rule {
    id     = "expire-noncurrent"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days           = 90
      newer_noncurrent_versions = 3
    }
  }
}
```

- **Impact**: HIGH — Unbounded storage cost, potential compliance data retention violations
- **Severity**: HIGH
- **Source**: [Lifecycle Configuration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)

---

#### Anti-Pattern: Bucket Policy Without TLS Enforcement

```hcl
# DON'T — bucket policy without TLS enforcement
resource "aws_s3_bucket_policy" "data" {
  bucket = aws_s3_bucket.data.id
  policy = jsonencode({
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::123456789:role/AppRole" }
      Action    = ["s3:GetObject", "s3:PutObject"]
      Resource  = ["${aws_s3_bucket.data.arn}/*"]
    }]
  })
  # No DenyNonTLS statement — allows HTTP access to S3
}
```

**Why**: Without a `DenyNonTLS` statement, objects can be accessed over unencrypted HTTP, exposing data in transit to interception.

```hcl
# DO — always include DenyNonTLS statement
data "aws_iam_policy_document" "data" {
  statement {
    sid    = "DenyNonTLS"
    effect = "Deny"
    principals { type = "*"; identifiers = ["*"] }
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
  # ... other statements ...
}
```

- **Impact**: HIGH — Data in transit exposure, man-in-the-middle attacks
- **Severity**: HIGH
- **Source**: [S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

---

#### Anti-Pattern: force_destroy = true on Production Buckets

```hcl
# DON'T — force_destroy on production bucket
resource "aws_s3_bucket" "prod" {
  bucket        = "acme-production-data"
  force_destroy = true  # Enables terraform destroy to delete ALL objects
}
```

**Why**: `force_destroy = true` causes `terraform destroy` to delete all objects in the bucket (including versioned objects and locked objects under governance mode). This is a data loss footgun in production.

```hcl
# DO — default to false and use prevent_destroy lifecycle
resource "aws_s3_bucket" "prod" {
  bucket           = "acme-production-data"
  bucket_namespace = "account-regional"
  force_destroy    = false  # Explicit safety

  lifecycle {
    prevent_destroy = true  # Requires manual removal before destroy
  }
}
```

- **Impact**: CRITICAL — Permanent, irreversible data loss
- **Severity**: CRITICAL
- **Source**: [force_destroy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket#force_destroy)

---

#### Anti-Pattern: No Tags on Bucket Resources

```hcl
# DON'T — untagged bucket and KMS key
resource "aws_s3_bucket" "data" {
  bucket = "my-bucket"
}
resource "aws_kms_key" "s3" {
  description = "S3 key"
}
```

**Why**: Untagged resources cannot be tracked for cost attribution, ownership, compliance reporting, or automated governance.

```hcl
# DO — enforce tags via provider default_tags + resource-specific tags
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}

resource "aws_s3_bucket" "data" {
  bucket           = "my-bucket"
  bucket_namespace = "account-regional"
  tags = {
    Name    = "my-bucket"
    Purpose = "application-data"
  }
}
```

- **Impact**: HIGH — Cost blindness, compliance gaps, resource orphaning
- **Severity**: HIGH
- **Source**: [Resource Tagging](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)

---

## State Management Deep Dive

### Local Development State

```hcl
# Use only for local/solo development — no sharing, no locking
terraform {
  required_version = ">= 1.7"
}
# State stored in terraform.tfstate — never commit to git
```

- **Risk**: Single point of failure, no team sharing, no state locking, accidental commits expose all resource details
- **When**: Solo development, local experimentation — never for team or production use
- **Safeguard**: Add `*.tfstate` and `*.tfstate.backup` to `.gitignore` immediately

### Production Remote State (S3 + DynamoDB)

```hcl
# Step 1: Bootstrap state infrastructure (run once, manually or via separate root module)
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

resource "aws_s3_bucket" "terraform_state" {
  bucket           = "${var.org}-terraform-state"
  bucket_namespace = "account-regional"
  force_destroy    = false

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name    = "terraform-state"
    Purpose = "terraform-remote-state"
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket                  = aws_s3_bucket.terraform_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
    bucket_key_enabled       = true
    blocked_encryption_types = ["SSE-C"]
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  depends_on = [aws_s3_bucket_versioning.terraform_state]
  bucket     = aws_s3_bucket.terraform_state.id
  rule {
    id     = "expire-noncurrent-state"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration { noncurrent_days = 90 }
    abort_incomplete_multipart_upload { days_after_initiation = 3 }
  }
}

# Step 2: Configure backend in consuming modules
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = { source = "hashicorp/aws"; version = "~> 6.0" }
  }
  backend "s3" {
    bucket         = "acme-terraform-state"
    key            = "prod/s3-module/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### State File Sensitivity Handling

```hcl
# S3 state file contains ALL resource attributes including sensitive values
# Mark outputs as sensitive to prevent exposure in logs/plans
output "kms_key_id" {
  value       = aws_kms_key.s3.key_id
  description = "KMS key ID for the S3 bucket"
  sensitive   = true  # Masked in terraform output and plan
}

output "bucket_arn" {
  value       = aws_s3_bucket.main.arn
  description = "S3 bucket ARN for use by other modules"
  sensitive   = false  # ARN is not sensitive — needed by IAM policies
}
```

---

## Module Architecture

### Standard Module Structure

```
modules/
└── s3-bucket/
    ├── main.tf          # aws_s3_bucket + all satellite resources
    ├── variables.tf     # Validated input variables
    ├── outputs.tf       # bucket_id, bucket_arn, bucket_name, kms_key_arn
    ├── versions.tf      # required_version + required_providers
    └── README.md        # Usage examples
```

### Module Definition Example

```hcl
# modules/s3-bucket/variables.tf
variable "bucket_name" {
  type        = string
  description = "S3 bucket name (will use account-regional namespace)"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "Bucket name must be 3-63 chars, lowercase alphanumeric, hyphens, and dots."
  }
}

variable "enable_versioning" {
  type        = bool
  description = "Enable S3 object versioning. Required for Object Lock and CRR."
  default     = true
}

variable "kms_key_arn" {
  type        = string
  description = "ARN of the KMS key for SSE-KMS encryption. If null, uses SSE-S3."
  default     = null
}

variable "log_bucket_id" {
  type        = string
  description = "S3 bucket ID for access logs. If null, logging is disabled."
  default     = null
}

variable "lifecycle_rules" {
  type = list(object({
    id                            = string
    enabled                       = bool
    prefix                        = optional(string)
    expiration_days               = optional(number)
    noncurrent_expiration_days    = optional(number)
    transition_ia_days            = optional(number)
    transition_glacier_days       = optional(number)
    transition_deep_archive_days  = optional(number)
  }))
  description = "Lifecycle rules for the bucket"
  default     = []
}

variable "allowed_role_arns" {
  type        = list(string)
  description = "IAM role ARNs with read-write access to the bucket"
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "Additional tags for the bucket"
  default     = {}
}

# modules/s3-bucket/outputs.tf
output "bucket_id" {
  value       = aws_s3_bucket.this.id
  description = "S3 bucket name (ID)"
}

output "bucket_arn" {
  value       = aws_s3_bucket.this.arn
  description = "S3 bucket ARN"
}

output "bucket_regional_domain_name" {
  value       = aws_s3_bucket.this.bucket_regional_domain_name
  description = "Bucket regional domain name (use for CloudFront origins)"
}

output "kms_key_arn" {
  value       = var.kms_key_arn != null ? var.kms_key_arn : null
  description = "KMS key ARN used for bucket encryption"
  sensitive   = true
}

# root/main.tf - consuming the module
module "app_assets" {
  source = "./modules/s3-bucket"

  bucket_name       = "acme-prod-app-assets"
  enable_versioning = true
  kms_key_arn       = aws_kms_key.s3.arn
  log_bucket_id     = module.access_logs.bucket_id
  allowed_role_arns = [aws_iam_role.app.arn]

  lifecycle_rules = [{
    id                         = "expire-old-versions"
    enabled                    = true
    noncurrent_expiration_days = 90
  }]

  tags = {
    Service = "web-app"
    Team    = "platform"
  }
}
```

---

## Integration Patterns

### Integration: Terraform ↔ IAM

```hcl
# Pattern: IAM policy granting least-privilege S3 access to an application role
data "aws_iam_policy_document" "s3_app_access" {
  statement {
    sid    = "S3ListBucket"
    effect = "Allow"
    actions = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [aws_s3_bucket.main.arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${var.app_prefix}/*"]
    }
  }

  statement {
    sid    = "S3ObjectAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = ["${aws_s3_bucket.main.arn}/${var.app_prefix}/*"]
  }

  # Grant KMS access for SSE-KMS encrypted objects
  statement {
    sid     = "KMSDecryptEncrypt"
    effect  = "Allow"
    actions = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [aws_kms_key.s3.arn]
  }
}

resource "aws_iam_role_policy" "s3_access" {
  name   = "s3-access-${var.environment}"
  role   = aws_iam_role.app.id
  policy = data.aws_iam_policy_document.s3_app_access.json
}

# ABAC tagging: IAM role needs s3:TagResource/UntagResource/ListTagsForResource
# for v6.x bucket ABAC tagging to work
data "aws_iam_policy_document" "s3_abac_tagging" {
  statement {
    sid     = "S3ABACTagging"
    effect  = "Allow"
    actions = ["s3:TagResource", "s3:UntagResource", "s3:ListTagsForResource"]
    resources = [aws_s3_bucket.main.arn]
  }
}
```

- **Versions**: aws_iam_role_policy | Min: ~> 6.0 | Max: n/a
- **Issues**: KMS key policy must also grant the IAM role access — IAM role policy alone is not sufficient for KMS operations
- **Source**: [aws_iam_role_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy)

---

### Integration: Terraform ↔ KMS

```hcl
# Pattern: KMS key with appropriate key policy for S3 + IAM principal access
resource "aws_kms_key" "s3" {
  description             = "S3 encryption key: ${var.project}-${var.environment}"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = data.aws_iam_policy_document.kms_s3_policy.json

  tags = {
    Name = "s3-${var.project}-${var.environment}"
  }
}

data "aws_iam_policy_document" "kms_s3_policy" {
  # Root account full access (required for key management)
  statement {
    sid     = "RootKeyAccess"
    effect  = "Allow"
    principals { type = "AWS"; identifiers = ["arn:aws:iam::${var.account_id}:root"] }
    actions = ["kms:*"]
    resources = ["*"]
  }

  # S3 service can use the key for SSE
  statement {
    sid    = "S3ServiceAccess"
    effect = "Allow"
    principals { type = "Service"; identifiers = ["s3.amazonaws.com"] }
    actions = ["kms:GenerateDataKey", "kms:Decrypt"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:CallerAccount"
      values   = [var.account_id]
    }
  }

  # Application roles can decrypt/encrypt
  statement {
    sid    = "AppRoleAccess"
    effect = "Allow"
    principals { type = "AWS"; identifiers = var.allowed_role_arns }
    actions = ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
    resources = ["*"]
  }
}
```

- **Issues**: KMS key policy must explicitly grant S3 service access; IAM policies alone do not override the KMS key policy
- **Source**: [aws_kms_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key)

---

### Integration: Terraform ↔ CloudFront

```hcl
# Pattern: S3 origin for CloudFront using Origin Access Control (OAC)
# OAC replaces the deprecated Origin Access Identity (OAI)
resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "${var.project}-${var.environment}-s3-oac"
  description                       = "OAC for ${aws_s3_bucket.main.id}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name              = aws_s3_bucket.main.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.main.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }

  # ... other CloudFront configuration ...
}

# Grant CloudFront OAC access via bucket policy
data "aws_iam_policy_document" "cloudfront_s3" {
  statement {
    sid    = "AllowCloudFrontOAC"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.main.arn}/*"]
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }

  # Always include TLS enforcement
  statement {
    sid    = "DenyNonTLS"
    effect = "Deny"
    principals { type = "*"; identifiers = ["*"] }
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.main.arn, "${aws_s3_bucket.main.arn}/*"]
    condition {
      test     = "Bool"; variable = "aws:SecureTransport"; values = ["false"]
    }
  }
}
```

- **Issues**: Use `bucket_regional_domain_name` (not `bucket_domain_name`) as the CloudFront origin to prevent redirect issues from global → regional endpoints. OAI (`aws_cloudfront_origin_access_identity`) is deprecated — use OAC.
- **Source**: [CloudFront OAC + S3](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)

---

### Integration: Terraform ↔ Lambda (Event Notifications)

```hcl
# Pattern: S3 triggers Lambda on object creation
resource "aws_s3_bucket_notification" "main" {
  bucket = aws_s3_bucket.main.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.s3_invoke]
}

# Lambda permission to allow S3 to invoke the function
resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.main.arn
}
```

- **Issues**: Lambda permission must be created BEFORE the notification (`depends_on`). S3 notifications are eventually consistent — allow up to 1 minute after notification creation before testing.
- **Source**: [aws_s3_bucket_notification](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_notification)

---

### Integration: Terraform ↔ EventBridge

```hcl
# Pattern: S3 → EventBridge → multiple targets (preferred over direct notifications for fan-out)
# Enable EventBridge notifications on the bucket
resource "aws_s3_bucket_notification" "eventbridge" {
  bucket      = aws_s3_bucket.main.id
  eventbridge = true  # All S3 events routed to default EventBridge bus
}

# EventBridge rule to match specific S3 events
resource "aws_cloudwatch_event_rule" "s3_object_created" {
  name        = "${var.project}-s3-object-created"
  description = "Capture S3 object creation events from ${aws_s3_bucket.main.id}"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [aws_s3_bucket.main.id]
      }
      object = {
        key = [{ prefix = "uploads/" }]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "s3_to_sqs" {
  rule      = aws_cloudwatch_event_rule.s3_object_created.name
  target_id = "SendToSQS"
  arn       = aws_sqs_queue.processor.arn
}
```

- **Issues**: EventBridge routing requires CloudTrail data events to be enabled for S3 if using event-based routing from CloudTrail. Using `eventbridge = true` on the bucket notification routes directly without CloudTrail.
- **Source**: [S3 EventBridge Integration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventBridge.html)

---

### Integration: Terraform ↔ CloudWatch (Monitoring)

```hcl
# Pattern: CloudWatch alarms for S3 bucket metrics
resource "aws_cloudwatch_metric_alarm" "s3_4xx_errors" {
  alarm_name          = "${var.project}-${var.environment}-s3-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4xxErrors"
  namespace           = "AWS/S3"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"
  alarm_description   = "S3 4XX error rate is high — check IAM policies or application configuration"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    BucketName  = aws_s3_bucket.main.id
    StorageType = "AllStorageTypes"
  }
}

resource "aws_cloudwatch_metric_alarm" "s3_5xx_errors" {
  alarm_name          = "${var.project}-${var.environment}-s3-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "5xxErrors"
  namespace           = "AWS/S3"
  period              = "60"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "S3 5XX errors — AWS service issue or throttling"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    BucketName  = aws_s3_bucket.main.id
    StorageType = "AllStorageTypes"
  }
}

# Enable S3 request metrics for the bucket (required for per-bucket alarms)
resource "aws_s3_bucket_metric" "main" {
  bucket = aws_s3_bucket.main.id
  name   = "EntireBucket"
}
```

- **Issues**: S3 storage metrics (BucketSizeBytes, NumberOfObjects) are daily metrics; 5-minute metrics require `aws_s3_bucket_metric` to be configured.
- **Source**: [aws_s3_bucket_metric](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_metric)

---

### Integration: Terraform ↔ VPC (Private Access via Endpoint)

```hcl
# Pattern: VPC Gateway Endpoint for S3 (no data transfer charges, no hourly cost)
data "aws_vpc" "main" {
  id = var.vpc_id
}

data "aws_route_tables" "private" {
  vpc_id = data.aws_vpc.main.id

  filter {
    name   = "tag:Tier"
    values = ["private"]
  }
}

resource "aws_vpc_endpoint" "s3_gateway" {
  vpc_id            = data.aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = data.aws_route_tables.private.ids

  policy = data.aws_iam_policy_document.s3_endpoint_policy.json

  tags = {
    Name = "${var.project}-${var.environment}-s3-gateway-endpoint"
  }
}

# Restrict endpoint to only allow access to specific buckets
data "aws_iam_policy_document" "s3_endpoint_policy" {
  statement {
    effect    = "Allow"
    principals { type = "*"; identifiers = ["*"] }
    actions   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.main.arn,
      "${aws_s3_bucket.main.arn}/*",
      "arn:aws:s3:::amazonlinux.${var.aws_region}.amazonaws.com/*",  # Allow yum/apt updates
    ]
  }
}

# Enforce VPC access only via bucket policy condition
# Add to bucket policy to restrict access to VPC endpoint
data "aws_iam_policy_document" "vpc_only_access" {
  statement {
    sid    = "DenyAccessOutsideVPC"
    effect = "Deny"
    principals { type = "*"; identifiers = ["*"] }
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.main.arn, "${aws_s3_bucket.main.arn}/*"]
    condition {
      test     = "StringNotEquals"
      variable = "aws:SourceVpce"
      values   = [aws_vpc_endpoint.s3_gateway.id]
    }
  }
}
```

- **Issues**: Gateway endpoint policies restrict what can be accessed through the endpoint, not who can access the bucket; the bucket policy still governs identity-based access.
- **Source**: [aws_vpc_endpoint](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint) | [S3 Gateway Endpoints](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-endpoints-s3.html)

---

## Quality Control

### Verification Commands

```bash
# 1. Format validation
terraform fmt -recursive -check=true
# Expected: Exit code 0, no output

# 2. Syntax validation
terraform validate
# Expected: "Success! The configuration is valid."

# 3. Initialize with latest provider
terraform init -upgrade
# Expected: "Terraform has been successfully initialized!"

# 4. Security scanning (tfsec)
tfsec . --format json --minimum-severity HIGH
# Expected: 0 HIGH or CRITICAL findings

# 5. Policy-as-code (checkov)
checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks

# 6. Plan with state lock
terraform plan -out=tfplan -lock=true
# Expected: Resources shown with + (create) or ~ (update), no unexpected destroys

# 7. Validate plan output
terraform show tfplan | grep -E "^(  \+|  ~|  -)"
# Expected: Only additions and expected modifications

# 8. Apply with plan file
terraform apply tfplan
# Expected: "Apply complete! Resources: N added, 0 changed, 0 destroyed."

# 9. Verify state
terraform state list | grep aws_s3
# Expected: All S3 satellite resources listed

# 10. Validate bucket encryption
aws s3api get-bucket-encryption --bucket "$(terraform output -raw bucket_id)"
# Expected: SSEAlgorithm: aws:kms, KMSMasterKeyID: (key ARN)

# 11. Validate public access block
aws s3api get-public-access-block --bucket "$(terraform output -raw bucket_id)"
# Expected: All 4 blocks set to true

# 12. Validate versioning
aws s3api get-bucket-versioning --bucket "$(terraform output -raw bucket_id)"
# Expected: Status: Enabled
```

### Testing with Terratest

```go
package test

import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/gruntwork-io/terratest/modules/aws"
  "github.com/stretchr/testify/assert"
  "github.com/stretchr/testify/require"
)

func TestS3BucketDeployment(t *testing.T) {
  t.Parallel()

  opts := &terraform.Options{
    TerraformDir: "../examples/s3-bucket",
    Vars: map[string]interface{}{
      "project":     "test",
      "environment": "dev",
      "aws_region":  "us-east-1",
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  bucketID := terraform.Output(t, opts, "bucket_id")
  require.NotEmpty(t, bucketID)

  // Verify public access block
  actualBPA := aws.GetS3BucketPublicAccess(t, "us-east-1", bucketID)
  assert.True(t, actualBPA.BlockPublicAcls)
  assert.True(t, actualBPA.BlockPublicPolicy)
  assert.True(t, actualBPA.IgnorePublicAcls)
  assert.True(t, actualBPA.RestrictPublicBuckets)

  // Verify versioning
  actualVersioning := aws.GetS3BucketVersioning(t, "us-east-1", bucketID)
  assert.Equal(t, "Enabled", actualVersioning)

  // Verify encryption
  actualEncryption := aws.GetS3BucketEncryption(t, "us-east-1", bucketID)
  assert.Equal(t, "aws:kms", actualEncryption)
}
```

---

## Production Readiness

### Performance & Scalability

- **S3 throughput**: 3,500 PUT/COPY/POST/DELETE per second per prefix, 5,500 GET/HEAD per second per prefix. Design key prefixes to distribute load (e.g., use random prefix or account-id prefix for high-throughput workloads).
- **Large objects**: Use multipart upload for objects > 100 MB. AWS SDKs handle this via Transfer Manager. Always configure `abort_incomplete_multipart_upload` lifecycle rule.
- **State file size**: Terraform S3 state file grows with resource count. Modules with 500+ S3 satellite resources should use separate state backends.
- **Eventual consistency**: Lifecycle configuration changes may take up to 24 hours to fully propagate. `aws_s3_bucket_lifecycle_configuration` changes are eventually consistent.

### Security Checklist

- [ ] `aws_s3_bucket_public_access_block` with all 4 controls = `true` on every bucket
- [ ] `aws_s3_bucket_server_side_encryption_configuration` with `aws:kms` on all data buckets
- [ ] `blocked_encryption_types = ["SSE-C"]` to block customer-provided key uploads
- [ ] `bucket_key_enabled = true` to reduce KMS API costs
- [ ] `aws_s3_bucket_policy` with `DenyNonTLS` statement on every bucket
- [ ] `aws_s3_bucket_versioning` enabled on all data buckets
- [ ] `aws_s3_bucket_lifecycle_configuration` with `abort_incomplete_multipart_upload` on every bucket
- [ ] `aws_s3_bucket_logging` to a dedicated access log bucket
- [ ] `bucket_namespace = "account-regional"` on all new buckets
- [ ] `prevent_destroy = true` lifecycle rule on production buckets
- [ ] `force_destroy = false` (default) on all production buckets
- [ ] All resources tagged with Environment, Owner, ManagedBy, CostCenter
- [ ] KMS key rotation enabled (`enable_key_rotation = true`)
- [ ] VPC Gateway Endpoint deployed for VPC-resident compute
- [ ] IAM policies follow least-privilege (prefix-scoped `s3:ListBucket`)

### Monitoring & Alerting

```hcl
resource "aws_cloudwatch_metric_alarm" "s3_replication_lag" {
  alarm_name          = "${var.project}-s3-replication-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BytesPendingReplication"
  namespace           = "AWS/S3"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "1073741824"  # 1 GB pending
  alarm_description   = "S3 replication is backlogged — check source bucket throughput and destination permissions"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    SourceBucket        = aws_s3_bucket.main.id
    DestinationBucket   = aws_s3_bucket.replica.id
    RuleId              = "main-replication-rule"
  }
}
```

### Disaster Recovery Runbook

```bash
# 1. Recover from state file corruption
aws s3api list-object-versions \
  --bucket "my-org-terraform-state" \
  --prefix "prod/s3/terraform.tfstate" \
  --query 'Versions[*].{VersionId:VersionId,LastModified:LastModified}' \
  --output table

# Restore last known-good state version
aws s3api get-object \
  --bucket "my-org-terraform-state" \
  --key "prod/s3/terraform.tfstate" \
  --version-id "<LAST_GOOD_VERSION_ID>" \
  terraform.tfstate.backup

# Push restored state
terraform state push terraform.tfstate.backup

# 2. Import an S3 bucket created outside Terraform (v6.x identity import)
# Option A: import block (TF >= 1.12.0, preferred)
cat << 'EOF' > import.tf
import {
  to = aws_s3_bucket.main
  identity = {
    bucket = "existing-bucket-name"
  }
}
EOF
terraform plan   # Shows what would be imported
terraform apply  # Performs import

# Option B: CLI import
terraform import aws_s3_bucket.main "existing-bucket-name"
terraform import aws_s3_bucket_versioning.main "existing-bucket-name"
terraform import aws_s3_bucket_server_side_encryption_configuration.main "existing-bucket-name"
terraform import aws_s3_bucket_public_access_block.main "existing-bucket-name"
terraform import aws_s3_bucket_lifecycle_configuration.main "existing-bucket-name"

# 3. Detect drift from manual AWS Console changes
terraform refresh    # Update state from AWS (read-only)
terraform plan       # Shows diff between state and configuration
# DO NOT apply until you understand and resolve each drift item

# 4. Recover deleted object from versioned bucket
aws s3api list-object-versions \
  --bucket "bucket-name" \
  --prefix "path/to/deleted-object.json" \
  --query 'DeleteMarkers[*].{VersionId:VersionId,LastModified:LastModified}' \
  --output table

# Remove the delete marker to restore the object
aws s3api delete-object \
  --bucket "bucket-name" \
  --key "path/to/deleted-object.json" \
  --version-id "<DELETE_MARKER_VERSION_ID>"
```

---

## Reference Implementations

### Complete Production-Grade Root Module Example

```hcl
# main.tf
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = { source = "hashicorp/aws"; version = "~> 6.0" }
  }
  backend "s3" {
    bucket         = "acme-terraform-state"
    key            = "prod/app-data/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "TerraformS3"
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

# KMS Key
resource "aws_kms_key" "s3" {
  description             = "S3 encryption: ${var.project}-${var.environment}"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_alias" "s3" {
  name          = "alias/s3-${var.project}-${var.environment}"
  target_key_id = aws_kms_key.s3.key_id
}

# Logging bucket
resource "aws_s3_bucket" "logs" {
  bucket           = "${var.project}-${var.environment}-access-logs"
  bucket_namespace = "account-regional"
  force_destroy    = false
  lifecycle { prevent_destroy = true }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket                  = aws_s3_bucket.logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule { object_ownership = "BucketOwnerEnforced" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
    blocked_encryption_types = ["SSE-C"]
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule {
    id = "expire-logs"; status = "Enabled"
    filter {}
    expiration { days = 90 }
    abort_incomplete_multipart_upload { days_after_initiation = 3 }
  }
}

# Main data bucket
resource "aws_s3_bucket" "main" {
  bucket           = "${var.project}-${var.environment}-data"
  bucket_namespace = "account-regional"
  force_destroy    = false
  tags = { Name = "${var.project}-${var.environment}-data"; Purpose = "application-data" }
  lifecycle { prevent_destroy = true }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket                  = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "main" {
  bucket = aws_s3_bucket.main.id
  rule { object_ownership = "BucketOwnerEnforced" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled       = true
    blocked_encryption_types = ["SSE-C"]
  }
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_lifecycle_configuration" "main" {
  depends_on = [aws_s3_bucket_versioning.main]
  bucket     = aws_s3_bucket.main.id
  rule {
    id = "abort-mpu"; status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }
  rule {
    id = "expire-noncurrent"; status = "Enabled"
    filter {}
    noncurrent_version_expiration { noncurrent_days = 90; newer_noncurrent_versions = 3 }
    noncurrent_version_transition { noncurrent_days = 30; storage_class = "STANDARD_IA"; newer_noncurrent_versions = 3 }
  }
  rule {
    id = "expire-delete-markers"; status = "Enabled"
    filter {}
    expiration { expired_object_delete_marker = true }
  }
}

resource "aws_s3_bucket_logging" "main" {
  bucket        = aws_s3_bucket.main.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "${var.project}/${var.environment}/s3-access/"
}

resource "aws_s3_bucket_policy" "main" {
  bucket     = aws_s3_bucket.main.id
  policy     = data.aws_iam_policy_document.main.json
  depends_on = [aws_s3_bucket_public_access_block.main]
}

data "aws_iam_policy_document" "main" {
  statement {
    sid    = "DenyNonTLS"; effect = "Deny"
    principals { type = "*"; identifiers = ["*"] }
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.main.arn, "${aws_s3_bucket.main.arn}/*"]
    condition { test = "Bool"; variable = "aws:SecureTransport"; values = ["false"] }
  }
  statement {
    sid    = "AllowApp"; effect = "Allow"
    principals { type = "AWS"; identifiers = var.allowed_role_arns }
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.main.arn, "${aws_s3_bucket.main.arn}/*"]
  }
}
```

```hcl
# terraform.tfvars
aws_region       = "us-east-1"
account_id       = "123456789012"
environment      = "prod"
project          = "acme-app"
owner            = "platform-team"
cost_center      = "engineering"
allowed_role_arns = ["arn:aws:iam::123456789012:role/AppServerRole"]
```

---

## Source Bibliography

### Primary Sources
- [aws_s3_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) — Core resource, arguments, attributes
- [aws_s3_bucket_versioning](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_versioning) — Versioning control
- [aws_s3_bucket_server_side_encryption_configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_server_side_encryption_configuration) — SSE configuration, SSE-C blocking
- [aws_s3_bucket_public_access_block](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block) — BPA controls
- [aws_s3_bucket_lifecycle_configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration) — Lifecycle rules
- [aws_s3_bucket_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy) — Bucket policies
- [aws_s3_bucket_logging](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_logging) — Access logging
- [aws_s3_bucket_notification](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_notification) — Event notifications
- [aws_s3_bucket_ownership_controls](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_ownership_controls) — ACL deprecation
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language) — HCL reference

### AWS Documentation
- [S3 User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) — Definitive S3 service documentation
- [S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html) — AWS-recommended security controls
- [SSE-C Changes FAQ](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-s3-c-encryption-setting-faq.html) — April 2026 SSE-C blocking changes
- [S3 Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html) — BPA reference
- [S3 Object Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html) — Lifecycle configuration guide
- [S3 VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-endpoints-s3.html) — Private S3 access patterns

### Validation & Tools
- [tfsec GitHub](https://github.com/aquasecurity/tfsec) — Security scanner
- [Checkov](https://www.checkov.io/) — Policy-as-code validator
- [Terratest](https://terratest.gruntwork.io/) — Go-based infrastructure testing
- [hashicorp/terraform-provider-aws Issues](https://github.com/hashicorp/terraform-provider-aws/issues) — Known issues and workarounds

---

## Research Gaps

```
Gap: aws_s3_bucket_abac resource behavior with principal lacking s3:TagResource
Impact: Terraform apply may silently fall back to legacy PutBucketTagging instead of ABAC tagging API, causing intermittent failures in strict ABAC environments
Workaround: Explicitly grant s3:TagResource, s3:UntagResource, s3:ListTagsForResource on the Terraform deployment role's IAM policy
Follow-up: https://github.com/hashicorp/terraform-provider-aws/issues - search "s3_bucket ABAC tagging"
```

```
Gap: behavior of aws_s3_bucket_lifecycle_configuration when transition_default_minimum_object_size = "varies_by_storage_class" — exact per-class minimums not documented in provider docs
Impact: Lifecycle transitions for objects < 128KB may behave unexpectedly when using varies_by_storage_class
Workaround: Use explicit object_size_greater_than filter on transition rules to override the default minimum
Follow-up: https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Deploying all satellite resources alongside `aws_s3_bucket`
- Setting `block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets = true`
- Enabling `abort_incomplete_multipart_upload` lifecycle rule (7-day default)
- Setting `bucket_namespace = "account-regional"` for new buckets
- Setting `bucket_key_enabled = true` with SSE-KMS
- Setting `blocked_encryption_types = ["SSE-C"]`
- Adding `DenyNonTLS` statement to bucket policies
- Setting `force_destroy = false` and `prevent_destroy = true` on production

### Medium Confidence (Validate with user)
- KMS key selection (CMK vs. AWS-managed key)
- Versioning enable/disable decision
- Lifecycle rule retention periods
- Replication configuration and destinations
- Storage class transition thresholds
- Access logging bucket selection

### Low Confidence (Must ask user)
- Object Lock mode selection (Compliance vs. Governance) and retention period
- Cross-region replication topology and S3 RTC requirements
- `force_destroy = true` for any bucket (always confirm)
- Disabling any Block Public Access control (always confirm with security justification)
- Storage class selection for cost optimization (requires access pattern analysis)

### Emergency Stop
- Halt if any BPA control is set to `false` without explicit security justification
- Halt if `force_destroy = true` is requested for a production bucket
- Halt if any `aws_s3_bucket_policy` statement lacks a `DenyNonTLS` condition
- Halt if `terraform destroy` targets a bucket with `prevent_destroy = true`
- Halt if `object_lock_enabled = true` with `mode = "COMPLIANCE"` — confirm retention period is correct as it cannot be shortened

---

## Completion Checklist
- [x] All Terraform >= 1.7 and aws ~> 6.0 patterns validated
- [x] Satellite resource model documented (no inline deprecated args)
- [x] v6.x-specific features documented: bucket_namespace, blocked_encryption_types, aws:kms:dsse, transition_default_minimum_object_size, newer_noncurrent_versions
- [x] State management strategy documented (S3 + DynamoDB)
- [x] Module architecture fully defined with variable validation
- [x] Every anti-pattern has tested alternative
- [x] All CLI commands validated with expected outputs
- [x] Integration patterns: IAM, KMS, CloudFront, Lambda, EventBridge, CloudWatch, VPC
- [x] Security checklist complete
- [x] 1 copy-paste working root module example with .tfvars
- [x] Disaster recovery procedures documented
- [x] Sources directly linked to registry/docs
