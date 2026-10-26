# Evaluation Scenarios — provisioning-aws-s3-v6

Four scenarios required for a hybrid knowledge skill (canonical, edge, misuse rejection, anti-pattern trap).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Secure S3 Bucket with Versioning and Lifecycle

```json
{
  "skills": ["provisioning-aws-s3-v6"],
  "query": "Generate Terraform for a secure S3 bucket with versioning, SSE-KMS, public access blocked at bucket and account level, TLS enforcement, and a lifecycle rule to expire noncurrent versions after 30 days. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69 (or >= 6.0)",
      "Uses use_lockfile = true in the S3 backend; does not include dynamodb_table",
      "Uses aws_s3_bucket_ownership_controls with object_ownership = \"BucketOwnerEnforced\"",
      "Sets all four BPA booleans to true on aws_s3_bucket_public_access_block",
      "Manages aws_s3_account_public_access_block without setting region on it",
      "Uses aws_s3_bucket_server_side_encryption_configuration (not inline block) with sse_algorithm = \"aws:kms\" and bucket_key_enabled = true",
      "Sets blocked_encryption_types = [\"SSE-C\"] on the encryption configuration",
      "Enforces TLS via bucket policy Deny on aws:SecureTransport = false",
      "Uses aws_s3_bucket_versioning standalone resource (not inline versioning block)",
      "Uses aws_s3_bucket_lifecycle_configuration with filter {} and noncurrent_version_expiration"
    ],
    "must_not": [
      "Mix inline versioning or server_side_encryption_configuration block with satellite resources",
      "Use dynamodb_table in the S3 backend",
      "Set region on aws_s3_account_public_access_block",
      "Use etag = filemd5() for KMS-encrypted objects",
      "Set expected_bucket_owner on any satellite resource"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Account-Regional Bucket Namespace

```json
{
  "skills": ["provisioning-aws-s3-v6"],
  "query": "I want to create a bucket in the account-regional namespace to prevent name squatting. Show me the correct Terraform configuration.",
  "success_criteria": {
    "must_pass": [
      "Sets bucket_namespace = \"account-regional\" on aws_s3_bucket",
      "Uses the naming pattern ending with -<account-id>-<region>-an",
      "Uses data.aws_caller_identity.current.account_id for the account ID",
      "Uses data.aws_region.current.region (not deprecated .name) for the region code",
      "Notes that account-regional namespace is not available in Bahrain (me-south-1) and UAE (me-central-1)",
      "Notes the naming constraint: the suffix counts toward the 63-char bucket name limit"
    ],
    "must_not": [
      "Use an arbitrary name (e.g. \"my-data-bucket\") with bucket_namespace = \"account-regional\"",
      "Use data.aws_region.current.name (deprecated in 6.0)"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: mfa_delete with Lifecycle Rules

```json
{
  "skills": ["provisioning-aws-s3-v6"],
  "query": "Can I enable MFA delete and also configure lifecycle rules on the same S3 bucket to satisfy both S3.20 and S3.10 Security Hub controls?",
  "success_criteria": {
    "must_pass": [
      "Explicitly rejects combining mfa_delete = \"Enabled\" with lifecycle rules on the same bucket",
      "States that AWS documentation explicitly prohibits MFA delete with a lifecycle configuration",
      "States that S3.20 (MFA delete) and S3.10/S3.13 (lifecycle) conflict; choose one",
      "Notes that only the root user can enable MFA delete",
      "Presents the choice as MFA delete or lifecycle rules (S3.10/S3.13) and asks which requirement takes priority, without declaring either universally better"
    ],
    "must_not": [
      "Silently permit configuring both mfa_delete and lifecycle on the same bucket",
      "Claim that both can be enabled simultaneously without consequences"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: 6.0 Breaking Changes and Deprecated Arguments

```json
{
  "skills": ["provisioning-aws-s3-v6"],
  "query": "Review this Terraform snippet: aws_s3_bucket with an inline versioning block alongside an aws_s3_bucket_versioning resource, reading aws_s3_bucket.main.region for the bucket's location, and s3_us_east_1_regional_endpoint = \"legacy\" in the provider. Is this correct for hashicorp/aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects the inline versioning block alongside aws_s3_bucket_versioning — states it causes drift",
      "States that inline bucket arguments are deprecated but not removed in 6.0; drift is the risk, not a provider error",
      "Rejects reading .region for the bucket's home region in 6.x; provides .bucket_region as the replacement",
      "Rejects s3_us_east_1_regional_endpoint = \"legacy\" as deprecated in 6.0 and removed in v7",
      "Recommends removing the inline versioning block and using only the satellite resource"
    ],
    "must_not": [
      "Accept the inline versioning block as valid alongside aws_s3_bucket_versioning",
      "Accept aws_s3_bucket.main.region as the bucket home region attribute in 6.x",
      "Accept s3_us_east_1_regional_endpoint = \"legacy\" as valid for 6.x"
    ]
  }
}
```
