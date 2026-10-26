# Always-Do — Foundation (Terraform Block, S3 Backend, Encryption Config)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23.

## 1. Terraform Block and S3 Backend

Root modules use `~>` for providers; reusable modules set only a minimum (`>=`).
Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

S3 backend with native locking (`dynamodb_table` is deprecated).
Source: https://developer.hashicorp.com/terraform/language/backend/s3

```hcl
# Fragment: add inside the terraform {} block above.
backend "s3" {
  bucket       = "my-tf-state"            # example
  key          = "xray/terraform.tfstate" # example
  region       = "eu-west-1"              # example
  use_lockfile = true
}
```

## 2. Encryption Config

`aws_xray_encryption_config` has Required `type` (`KMS` or `NONE`), Optional `key_id` (KMS key ARN)
and `region`; its `id` is the region name.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_encryption_config.html.markdown

X-Ray always encrypts at rest; `NONE` means default encryption. Keep a customer managed key
enabled, or X-Ray "stops storing data". Asymmetric KMS keys are not supported.
Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html

```hcl
# Default encryption
resource "aws_xray_encryption_config" "default" {
  type = "NONE"
}
```

```hcl
# Fragment: aws_kms_key.xray is defined elsewhere (see provisioning-aws-kms-v6).
resource "aws_xray_encryption_config" "cmk" {
  type   = "KMS"
  key_id = aws_kms_key.xray.arn
}
```

Use one of the two variants, not both. Whether a single config per region is enforced is
(medium confidence) — see the Ask First table in SKILL.md.
