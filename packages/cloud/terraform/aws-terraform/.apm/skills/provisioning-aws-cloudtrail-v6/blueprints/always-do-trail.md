# Always-Do — Trail (Terraform block, log bucket, trail)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Terraform block and region

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
  backend "s3" {
    # bucket / key / region supplied via -backend-config
    use_lockfile = true
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  trail_name = "org-audit"
  key_prefix = "cloudtrail"
  # .region, not .name (deprecated in 6.0)
  trail_arn = "arn:aws:cloudtrail:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:trail/${local.trail_name}"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
```

The ARN is built from a local so the bucket and key policies can reference the trail.

## 2. Log bucket, hardening and bucket policy

Use a dedicated bucket. The bucket must not be Requester Pays, and the prefix in the policy must
match `s3_key_prefix`. Bucket details belong to `provisioning-aws-s3-v6`.

```hcl
resource "aws_s3_bucket" "trail" {
  bucket = "example-cloudtrail-logs"
}

# CloudTrail.6: all four S3 Block Public Access settings (arguments: see provisioning-aws-s3-v6)
resource "aws_s3_bucket_public_access_block" "trail" {
  bucket                  = aws_s3_bucket.trail.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudTrail.7: server access logging (arguments: see provisioning-aws-s3-v6)
resource "aws_s3_bucket_logging" "trail" {
  bucket        = aws_s3_bucket.trail.id
  target_bucket = var.access_log_bucket_id  # placeholder
  target_prefix = "cloudtrail-bucket/"
}

data "aws_iam_policy_document" "trail_bucket" {
  statement {
    sid       = "AWSCloudTrailAclCheck"
    effect    = "Allow"
    actions   = ["s3:GetBucketAcl"]
    resources = [aws_s3_bucket.trail.arn]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [local.trail_arn]
    }
  }

  statement {
    sid       = "AWSCloudTrailWrite"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.trail.arn}/${local.key_prefix}/AWSLogs/${data.aws_caller_identity.current.account_id}/*"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [local.trail_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "trail" {
  bucket = aws_s3_bucket.trail.id
  policy = data.aws_iam_policy_document.trail_bucket.json
}
# Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html
# Policy-document syntax: see provisioning-aws-s3-v6
```

Organization trail: add the third statement (second PutObject) on `.../AWSLogs/<o-organizationID>/*`.
`aws:SourceArn` must be a trail ARN owned by the management account (its account ID). Keep the
account-level write statement.

If the bucket policy only allows SSE-KMS uploads and log file validation is on, allow `AES256` as
well, for example `"StringNotEquals": {"s3:x-amz-server-side-encryption": ["aws:kms","AES256"]}`,
or trail creation fails. Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html

## 3. The trail

```hcl
resource "aws_cloudtrail" "this" {
  name           = local.trail_name
  s3_bucket_name = aws_s3_bucket.trail.id
  s3_key_prefix  = local.key_prefix

  is_multi_region_trail         = true  # default false; resource lives in the home region
  include_global_service_events = true  # default true; needed for IAM and other global events
  enable_log_file_validation    = true  # default false
  enable_logging                = true  # default true

  # Always set a key: the default log encryption is stated differently by two AWS pages
  kms_key_id = var.trail_kms_key_arn  # key ARN (placeholder variable)

  # The ARN must end with :*
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.trail.arn}:*"
  cloud_watch_logs_role_arn  = var.cwl_delivery_role_arn  # placeholder; role permissions: (unverified)

  tags = { Name = local.trail_name }

  # The bucket policy must exist before the trail
  depends_on = [aws_s3_bucket_policy.trail]
}

resource "aws_cloudwatch_log_group" "trail" {
  name = "/aws/cloudtrail/${local.trail_name}"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html
# Log group arguments: see provisioning-aws-cloudwatch-v6
```

Selectors, data events and Insights are Ask First decisions (see SKILL.md); use only one selector
type. Log group details belong to `provisioning-aws-cloudwatch-v6`.

Organization trail: `is_organization_trail = true`, creatable only in the organization's management
account.

Import: `import { to = aws_cloudtrail.this  id = "arn:aws:cloudtrail:<region>:<account>:trail/<name>" }`
(`import` block needs Terraform >= 1.5; `identity { arn }` needs >= 1.12).
