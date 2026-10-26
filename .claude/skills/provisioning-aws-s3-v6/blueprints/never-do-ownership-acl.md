# Never-Do — Ownership, ACLs and Deprecated Owner Argument

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. ACL log-delivery-write with BucketOwnerEnforced

ACL `log-delivery-write` is incompatible with `BucketOwnerEnforced` (ACLs disabled).
Setting it causes a `400 AccessControlListNotSupported` error.

```hcl
# WRONG — ACL grant on a BucketOwnerEnforced target bucket
resource "aws_s3_bucket_acl" "logging_target" {
  bucket = aws_s3_bucket.access_logs.id
  acl    = "log-delivery-write"   # WRONG — fails when BucketOwnerEnforced is set
}
# Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html

# CORRECT — bucket policy grant (see always-do-security-encryption section 7)
resource "aws_s3_bucket_policy" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id
  policy = data.aws_iam_policy_document.logging_target.json   # s3:PutObject for logging.s3.amazonaws.com
}
```

## 2. expected_bucket_owner on Satellite Resources

`expected_bucket_owner` is deprecated on satellite resources and was dropped from Resource
Identity in 6.31.0. It forces replacement when set.

```hcl
# WRONG — expected_bucket_owner on satellite resource
resource "aws_s3_bucket_versioning" "bad" {
  bucket                = aws_s3_bucket.main.id
  expected_bucket_owner = "111122223333"   # WRONG — deprecated; forces new if changed
  versioning_configuration { status = "Enabled" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md (#46262, #46272)

# CORRECT — remove it
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration { status = "Enabled" }
}
```
