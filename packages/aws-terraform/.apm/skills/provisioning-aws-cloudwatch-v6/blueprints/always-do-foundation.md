# Always-Do — Foundation (Terraform Block, S3 Backend, Log Group)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Terraform Block and S3 Backend

Use `use_lockfile = true` for S3-native locking. `dynamodb_table` is deprecated (will be removed).
Root modules pin `~> 6.69`; reusable modules use `>= 6.0`.

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
  backend "s3" {
    bucket       = "my-tf-state"
    key          = "cloudwatch/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true   # S3-native lock; dynamodb_table is deprecated
    encrypt      = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```

Commit `.terraform.lock.hcl`. For cross-platform CI hashes:
```
terraform providers lock -platform=linux_amd64 -platform=darwin_arm64
```
Source: https://developer.hashicorp.com/terraform/language/files/dependency-lock

## 2. Log Group with Retention and Deletion Protection

Always set `retention_in_days` — the default is indefinite retention.
Set `deletion_protection_enabled = false` explicitly when the group must be deletable:
removing the argument is not enough. AWS rejects deletion with `ValidationException`
("Disable deletion protection first") when the value is `true`.

Valid `retention_in_days` values: 0 (never expire), 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180,
365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653.

With `log_group_class = "DELIVERY"`, `retention_in_days` is **ignored and forced to 2**.
The `DELIVERY` class is limited to Lambda logs going to S3 or Firehose.

```hcl
resource "aws_cloudwatch_log_group" "app" {
  name                        = "/app/prod"
  retention_in_days           = 365               # CloudWatch.16: >= 365 (or 0 = COMPLIANT)
  deletion_protection_enabled = false              # explicit false required; omitting is not enough
  # log_group_class defaults to STANDARD; set explicitly if using INFREQUENT_ACCESS or DELIVERY
  tags = { Environment = "prod" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_group.html.markdown
# Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/protecting-log-groups-from-deletion.html
# Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html
```

To encrypt the log group with a KMS key (optional — default is server-side AES-256-GCM):

```hcl
resource "aws_cloudwatch_log_group" "app_encrypted" {
  name              = "/app/prod-encrypted"
  retention_in_days = 365
  kms_key_id        = aws_kms_key.logs.arn   # must be a symmetric key

  deletion_protection_enabled = false
  tags = { Environment = "prod" }
}

# Key policy statement — grant CloudWatch Logs the necessary KMS actions
# Add this statement to the key's policy alongside the account root grant
# Principal: { Service = "logs.<region>.amazonaws.com" }
# Actions:   kms:Encrypt, kms:Decrypt, kms:ReEncrypt*, kms:GenerateDataKey*, kms:Describe*
# Condition: ArnEquals { "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:<region>:<account>:log-group:/app/prod-encrypted" }
# Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html
```
