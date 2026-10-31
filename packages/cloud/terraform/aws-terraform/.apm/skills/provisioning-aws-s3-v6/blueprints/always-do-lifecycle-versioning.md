# Always-Do — Lifecycle and Versioning

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 8. Lifecycle Configuration

One `aws_s3_bucket_lifecycle_configuration` per bucket — multiple resources cause perpetual diff.
Use `filter {}` for all-objects scope. Use `filter { prefix = "..." }` or sub-elements for
scoped rules. Rule-level `prefix` is deprecated by S3; use `filter`.
Add `abort_incomplete_multipart_upload` to clean up incomplete multipart uploads.

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  # Rule 1: abort stale multipart uploads
  rule {
    id     = "abort-incomplete-multipart"
    status = "Enabled"

    filter {}   # all objects

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Rule 2: expire noncurrent versions (requires versioning)
  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}   # all objects

    noncurrent_version_expiration {
      noncurrent_days           = 30
      newer_noncurrent_versions = 3   # version that introduced this argument is (unverified)
    }
  }

  # Rule 3: scoped transition example (objects >= 128 KB due to default minimum size)
  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    filter {
      prefix = "logs/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = 365
    }
  }

  depends_on = [aws_s3_bucket_versioning.main]
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_lifecycle_configuration.html.markdown
# Note: transition_default_minimum_object_size defaults to "all_storage_classes_128K";
#       objects < 128 KB do not transition unless an explicit object_size_greater_than filter overrides it.
# Timeouts: create 3m, update 3m.
# Security Hub: S3.10 (versioned buckets need lifecycle — Medium), S3.13 (lifecycle config — Low)
```

## 9. Versioning

Versioning, once `Enabled`, can only be `Suspended` (never `Disabled` again).
Object Lock makes versioning permanently irreversible.
AWS recommends waiting ~15 min after first enabling before writing critical objects that rely on `version_id`.
Resources needing `version_id` must reference or `depends_on` this resource.

```hcl
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id

  versioning_configuration {
    status = "Enabled"
    # mfa_delete omitted; only the root user can enable MFA delete;
    # MFA delete cannot be used together with lifecycle rules (conflict — S3.20 vs S3.10/S3.13).
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_versioning.html.markdown
# Note: 6.48.0 bug fix — perpetual drift on mfa_delete when status = "Disabled".
# Security Hub: S3.14 (versioning enabled — Low)
```

For objects that need a `version_id` add `depends_on`:

```hcl
resource "aws_s3_object" "config" {
  bucket      = aws_s3_bucket.main.id
  key         = "config/app.json"
  source      = "files/app.json"
  source_hash = filemd5("files/app.json")   # correct for KMS; see always-do-objects-testing section 10
  depends_on  = [aws_s3_bucket_versioning.main]
}
```
