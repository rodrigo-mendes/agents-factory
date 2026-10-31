# Never-Do — Resource Conflicts (Inline Mixing, Multi-Resource, etag, mfa_delete)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Mixing Inline Arguments with Satellite Resources

Deprecated inline blocks (e.g. `versioning {}`, `server_side_encryption_configuration {}`) and
their satellite resource on the same bucket cause Terraform to treat the satellite settings as drift.

```hcl
# WRONG — inline versioning block alongside aws_s3_bucket_versioning
resource "aws_s3_bucket" "bad" {
  bucket = "my-bucket"

  versioning {             # WRONG — deprecated; conflicts with aws_s3_bucket_versioning
    enabled = true
  }
  server_side_encryption_configuration {   # WRONG — deprecated; conflicts with satellite resource
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket.html.markdown

# CORRECT — standalone satellite resources only
resource "aws_s3_bucket" "main" {
  bucket = "my-bucket"
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
    blocked_encryption_types = ["SSE-C"]
  }
}
```

Note: inline arguments are deprecated but **not removed in 6.0** — the documented failure mode is
Terraform treating the standalone settings as drift, not a provider error. The inline `server_side_encryption_configuration` block does NOT support
`blocked_encryption_types`; use the satellite resource.

## 2. Multiple Single-Config Resources per Bucket

`PutBucketPolicy` and `PutBucketNotificationConfiguration` replace the whole configuration (the last
apply wins silently); duplicate lifecycle and CORS configurations cause a perpetual diff.

```hcl
# WRONG — two policies on one bucket; last apply wins
resource "aws_s3_bucket_policy" "tls" {
  bucket = aws_s3_bucket.main.id
  policy = data.aws_iam_policy_document.tls.json
}
resource "aws_s3_bucket_policy" "replication" {
  bucket = aws_s3_bucket.main.id   # WRONG — replaces tls policy on every apply
  policy = data.aws_iam_policy_document.replication.json
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_policy.html.markdown

# CORRECT — merge all statements into one policy document
data "aws_iam_policy_document" "combined" {
  source_policy_documents = [
    data.aws_iam_policy_document.tls.json,
    data.aws_iam_policy_document.replication.json,
  ]
}
resource "aws_s3_bucket_policy" "main" {
  bucket = aws_s3_bucket.main.id
  policy = data.aws_iam_policy_document.combined.json
}
```

For independent notification consumers (e.g. multiple Lambda functions), use EventBridge
(`eventbridge = true` on `aws_s3_bucket_notification`) and one `aws_cloudwatch_event_rule` each.

## 3. etag with KMS or Multipart Objects

`etag` is not MD5 when SSE-KMS is active or when the upload is multipart (> 16 MB).
`etag = filemd5(...)` is not compatible with KMS.

```hcl
# WRONG — etag is not MD5 for KMS-encrypted objects
resource "aws_s3_object" "bad" {
  bucket = aws_s3_bucket.main.id
  key    = "data/large-file.bin"
  source = "data/large-file.bin"
  etag   = filemd5("data/large-file.bin")   # WRONG — not MD5 with KMS or multipart
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_object.html.markdown

# CORRECT
resource "aws_s3_object" "good" {
  bucket      = aws_s3_bucket.main.id
  key         = "data/large-file.bin"
  source      = "data/large-file.bin"
  source_hash = filemd5("data/large-file.bin")   # state-only; correct for KMS / multipart
}
```

## 4. mfa_delete with Lifecycle Rules

AWS states MFA delete cannot be used with a lifecycle configuration (Security Hub
S3.20 vs S3.10/S3.13). Enabling both creates an unresolvable conflict.

```hcl
# WRONG — mfa_delete + lifecycle rules on same bucket
resource "aws_s3_bucket_versioning" "bad" {
  bucket = aws_s3_bucket.main.id
  mfa    = "arn:aws:iam::123456789012:mfa/root-account-mfa-device 123456"
  versioning_configuration {
    status     = "Enabled"
    mfa_delete = "Enabled"   # WRONG — conflicts with lifecycle rules
  }
}
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/s3-controls.html

# CORRECT — choose one: MFA delete (no lifecycle) OR lifecycle rules (no MFA delete)
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
    # mfa_delete omitted (defaults Disabled); only root user can enable it
  }
}
```
