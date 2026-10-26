# Never-Do — Bucket Naming and Provider Endpoint Settings

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Account-Regional Namespace Without Correct Suffix

Account-regional bucket names must follow `<prefix>-<12-digit-account-id>-<region-code>-an`.
The suffix counts toward the 63-char limit. Not available in me-south-1 (Bahrain) or me-central-1 (UAE).

```hcl
# WRONG — arbitrary name with account-regional namespace
resource "aws_s3_bucket" "bad" {
  bucket           = "my-data-bucket"   # WRONG — no account-id/region suffix
  bucket_namespace = "account-regional"
}
# Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/gpbucketnamespaces.html

# CORRECT — required naming pattern; data.aws_region.current.region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_s3_bucket" "main" {
  bucket           = "${var.prefix}-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.region}-an"
  bucket_namespace = "account-regional"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
```

## 2. s3_us_east_1_regional_endpoint Legacy

Provider setting `s3_us_east_1_regional_endpoint = "legacy"` is deprecated in 6.0 and removed in v7
(affects us-east-1 S3 resources, excluding directory buckets). Remove it or set `regional`.

```hcl
# WRONG — deprecated provider setting
provider "aws" {
  region                         = "us-east-1"
  s3_us_east_1_regional_endpoint = "legacy"   # WRONG — deprecated in 6.0; removed in v7
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

# CORRECT — remove or set to regional
provider "aws" {
  region                         = "us-east-1"
  s3_us_east_1_regional_endpoint = "regional"   # or omit entirely
}
```
