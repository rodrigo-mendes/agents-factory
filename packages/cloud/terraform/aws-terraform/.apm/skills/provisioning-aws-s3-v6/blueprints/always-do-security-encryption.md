# Always-Do — Security and Encryption (SSE, TLS Policy, Access Logging)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 5. SSE Configuration

Use `aws_s3_bucket_server_side_encryption_configuration` (never the deprecated inline block).
`bucket_key_enabled` turns on S3 Bucket Keys for SSE-KMS; its cost effect is (unverified).
SSE-C is blocked since April 2026 for new buckets and existing buckets without SSE-C objects
(except Bahrain/UAE) — do not configure it; set `blocked_encryption_types = ["SSE-C"]` to enforce.

```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn   # omit to use aws/s3 managed key
    }
    bucket_key_enabled       = true             # S3 Bucket Keys; cost effect (unverified)
    blocked_encryption_types = ["SSE-C"]        # Optional+Computed since 6.40.0
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_server_side_encryption_configuration.html.markdown
# Source (SSE-C): https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-s3-c-encryption-setting-faq.html
# Security Hub: S3.17 requires SSE-KMS or DSSE-KMS (SSE-S3 fails S3.17)
# aws_kms_key.s3 is a placeholder for a key defined elsewhere (see provisioning-aws-kms-v6)
```

SSE-S3 alternative (this configuration fails Security Hub S3.17, which requires SSE-KMS or DSSE-KMS):
```hcl
rule {
  apply_server_side_encryption_by_default {
    sse_algorithm = "AES256"
  }
  blocked_encryption_types = ["SSE-C"]
}
```

## 6. TLS Enforcement via Bucket Policy

Deny all requests where `aws:SecureTransport = false` (S3.5). The bucket policy replaces the
whole policy — keep all statements in one `aws_s3_bucket_policy` resource per bucket.

```hcl
data "aws_iam_policy_document" "bucket_policy" {
  statement {
    sid    = "DenyNonTLS"
    effect = "Deny"
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    actions   = ["s3:*"]
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
}

resource "aws_s3_bucket_policy" "main" {
  bucket = aws_s3_bucket.main.id
  policy = data.aws_iam_policy_document.bucket_policy.json

  depends_on = [aws_s3_bucket_public_access_block.main]
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_policy.html.markdown
# Security Hub: S3.5 (Require TLS — Medium)
```

## 7. Access Logging

Grant access to `logging.s3.amazonaws.com` via bucket policy on the target bucket.
Do NOT use `acl = "log-delivery-write"` — incompatible with `BucketOwnerEnforced`.
The target bucket must be in the same Region and must not have a default Object Lock retention (S3.9).

```hcl
# aws_s3_bucket.access_logs is a placeholder for the log target bucket defined elsewhere
# On the logging TARGET bucket (must be same-Region)
data "aws_iam_policy_document" "logging_target" {
  statement {
    sid    = "AllowS3LogDelivery"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["logging.s3.amazonaws.com"]
    }
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.access_logs.arn}/*"]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id
  policy = data.aws_iam_policy_document.logging_target.json
}

# On the SOURCE bucket
resource "aws_s3_bucket_logging" "main" {
  bucket        = aws_s3_bucket.main.id
  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "s3/main/"

  # Optional: structured prefix
  target_object_key_format {
    partitioned_prefix {
      partition_date_source = "EventTime"
    }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_bucket_logging.html.markdown
# Source (ownership): https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html
# Security Hub: S3.9 (server access logging — Medium)
```
