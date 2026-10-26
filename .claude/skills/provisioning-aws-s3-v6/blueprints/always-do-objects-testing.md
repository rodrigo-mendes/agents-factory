# Always-Do — Objects and Testing (aws_s3_object, terraform test, CI)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 10. aws_s3_object

Use `source_hash = filemd5(...)` instead of `etag` for KMS-encrypted objects or multipart uploads
> 16 MB — `etag = filemd5(...)` is not compatible with KMS and is not MD5 for multipart.
Max 10 tags on an object; if combined `tags` + `default_tags` exceed 10, use
`override_provider { default_tags { tags = {} } }`.

```hcl
resource "aws_s3_object" "artifact" {
  bucket      = aws_s3_bucket.main.id
  key         = "releases/app-1.0.0.zip"
  source      = "dist/app-1.0.0.zip"
  source_hash = filemd5("dist/app-1.0.0.zip")   # state-only; correct for KMS / multipart

  # aws_kms_key.s3 is a placeholder for a key defined elsewhere
  server_side_encryption = "aws:kms"
  kms_key_id             = aws_kms_key.s3.arn
  bucket_key_enabled     = true

  checksum_algorithm = "SHA256"   # CRC32, CRC32C, CRC64NVME, SHA1, SHA256

  depends_on = [aws_s3_bucket_versioning.main]
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/s3_object.html.markdown
# Import: bucket/key or s3://bucket/key; identity { bucket, key }
```

Exactly one of `source`, `content` or `content_base64` is used per object (they conflict):
```hcl
resource "aws_s3_object" "readme" {
  bucket  = aws_s3_bucket.main.id
  key     = "README.txt"
  content = "Managed by Terraform."
}
```

## 11. terraform test and CI

Use `mock_provider "aws"` with `command = plan` for CI-safe unit tests (no credentials, no real
state). Mocking requires Terraform >= 1.7 (satisfied by ~> 1.16).

```hcl
# tests/s3_bucket.tftest.hcl
mock_provider "aws" {}

# Assertions use only top-level arguments; nested blocks are not indexed because the
# research does not document their schema shape (list vs set).
run "public_access_is_blocked" {
  command = plan

  assert {
    condition     = aws_s3_bucket_public_access_block.main.block_public_acls == true
    error_message = "block_public_acls must be true"
  }

  assert {
    condition     = aws_s3_bucket_public_access_block.main.restrict_public_buckets == true
    error_message = "restrict_public_buckets must be true"
  }

  assert {
    condition     = aws_s3_bucket_public_access_block.main.block_public_policy == true && aws_s3_bucket_public_access_block.main.ignore_public_acls == true
    error_message = "block_public_policy and ignore_public_acls must be true"
  }
}
# Source: https://developer.hashicorp.com/terraform/language/tests
# Source: https://developer.hashicorp.com/terraform/language/tests/mocking
```

CI pipeline commands (no real credentials required for plan-only tests):

```bash
# 1. Init without backend (CI-safe)
terraform init -backend=false

# 2. Validate syntax (requires init)
terraform validate -json

# 3. Plan with exit code detection
terraform plan -detailed-exitcode -input=false -out=tfplan
# Exit codes: 0 = no changes, 1 = error, 2 = changes pending

# 4. Run unit tests
terraform test -filter=tests/s3_bucket.tftest.hcl
# Source: https://developer.hashicorp.com/terraform/cli/commands/plan
# Source: https://developer.hashicorp.com/terraform/cli/commands/test
```
Commit `.terraform.lock.hcl`: https://developer.hashicorp.com/terraform/language/files/dependency-lock
