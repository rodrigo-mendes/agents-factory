# Never-Do — Trail (selectors, CloudWatch ARN, encryption, bucket policy, channel)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Mixing event_selector and advanced_event_selector

The two selector types conflict; use only one on a trail.

```hcl
# WRONG — both selector types on one trail
resource "aws_cloudtrail" "bad" {
  name           = "bad"
  s3_bucket_name = aws_s3_bucket.trail.id
  event_selector {                       # WRONG
    read_write_type = "All"
  }
  advanced_event_selector {              # WRONG — conflicts with event_selector
    name = "s3-data"
    field_selector {
      field  = "eventCategory"
      equals = ["Data"]
    }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown

# CORRECT — one selector type
resource "aws_cloudtrail" "good" {
  name           = "good"
  s3_bucket_name = aws_s3_bucket.trail.id
  kms_key_id     = var.trail_kms_key_arn  # placeholder
  advanced_event_selector {
    name = "s3-data"
    field_selector {
      field  = "eventSource"
      equals = ["s3.amazonaws.com"]  # example value (unverified)
    }
  }
}
```

`equals` is the only valid operator for `readOnly`, `eventCategory` and `resources.type`.

## 2. CloudWatch Logs group ARN without :*

```hcl
# WRONG — missing the log stream wildcard
cloud_watch_logs_group_arn = aws_cloudwatch_log_group.trail.arn

# CORRECT
cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.trail.arn}:*"
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown
```

## 3. Relying on a default log encryption

Two AWS pages disagree on the default (SSE-KMS on the best-practices page, SSE-S3 on the Security
Hub page) (medium confidence). Do not assert either; set `kms_key_id`. Security Hub CloudTrail.2
fails when `KmsKeyId` is undefined.

```hcl
# WRONG — no kms_key_id
resource "aws_cloudtrail" "bad" {
  name           = "bad"
  s3_bucket_name = aws_s3_bucket.trail.id
}

# CORRECT
resource "aws_cloudtrail" "good" {
  name           = "good"
  s3_bucket_name = aws_s3_bucket.trail.id
  kms_key_id     = var.trail_kms_key_arn
}
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html
# Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html
```

## 4. Bucket policy without aws:SourceArn or with a mismatched prefix

AWS lists an `aws:SourceArn` condition (value: the trail ARN) as a security best practice;
`aws:SourceAccount` is the documented alternative. A prefix in the bucket
policy that differs from `s3_key_prefix` gives "There is a problem with the bucket policy". A misconfigured trail makes CloudTrail retry delivery for 30 days, with charges; delete the
trail to stop them.

```hcl
# WRONG — PutObject statement with no aws:SourceArn, prefix differs from s3_key_prefix = "cloudtrail"
statement {
  actions   = ["s3:PutObject"]
  resources = ["${aws_s3_bucket.trail.arn}/other-prefix/AWSLogs/${data.aws_caller_identity.current.account_id}/*"]
  principals {
    type        = "Service"
    identifiers = ["cloudtrail.amazonaws.com"]
  }
}
# Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html
```

Correct form: [always-do-trail §2](./always-do-trail.md#2-log-bucket-hardening-and-bucket-policy).

## 5. HCL for aws_cloudtrail_channel

The provider doc page for `aws_cloudtrail_channel` returned HTTP 404 on 2026-10-23, so existence in
6.x is (unverified). Do not write HCL for it; ask the user how they integrate with CloudTrail Lake.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_channel.html.markdown
