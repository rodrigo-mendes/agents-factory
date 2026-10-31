# Always-Do — KMS policy, event data store, delegated admin, tests

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 4. KMS key policy for the trail

Three sections are needed: encrypt, decrypt, describe. Add these statements to the key policy
without changing its existing sections; a disabled key or a wrong policy stops delivery. Key
creation and administration belong to `provisioning-aws-kms-v6`. Key type constraints: (unverified). `var.*` values are placeholders.

```hcl
data "aws_iam_policy_document" "trail_key_statements" {
  statement {
    sid       = "AllowCloudTrailEncrypt"
    effect    = "Allow"
    actions   = ["kms:GenerateDataKey*"]
    resources = ["*"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [local.trail_arn]
    }
    condition {
      test     = "StringLike"
      variable = "kms:EncryptionContext:aws:cloudtrail:arn"
      values   = ["arn:aws:cloudtrail:*:${data.aws_caller_identity.current.account_id}:trail/*"]
    }
  }

  statement {
    sid       = "AllowReadersDecrypt"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = var.log_reader_principal_arns
    }
    condition {
      test     = "Null"
      variable = "kms:EncryptionContext:aws:cloudtrail:arn"
      values   = ["false"]
    }
  }

  statement {
    sid       = "AllowCloudTrailDecrypt"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = ["*"]
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
    sid       = "AllowCloudTrailDescribeKey"
    effect    = "Allow"
    actions   = ["kms:DescribeKey"]
    resources = ["*"]
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
}
# Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-kms-key-policy-for-cloudtrail.html
```

`aws:SourceArn` is recommended; `aws:SourceAccount` is supported but not recommended for trails.
For cross-account encryption, add the other account IDs to the encryption-context condition. With
an existing bucket using an S3 Bucket Key, `kms:Decrypt` is required to create or update a trail
with SSE-KMS.

## 5. Event data store (CloudTrail Lake)

CloudTrail Lake is closed to new customers since 2026-05-31; this resource is usable only by
already-onboarded accounts. Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html

```hcl
resource "aws_cloudtrail_event_data_store" "this" {
  name                           = "audit-lake"
  retention_period               = 2555  # value on the provider page (medium confidence)
  billing_mode                   = "EXTENDABLE_RETENTION_PRICING"
  termination_protection_enabled = true
  multi_region_enabled           = true
  organization_enabled           = false  # an organization store must be created in the management account
  suspend                        = false  # only "", true or false; never 0/1
  kms_key_id                     = var.eds_kms_key_arn  # cannot be removed or changed once associated

  tags = { Name = "audit-lake" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_event_data_store.html.markdown
# Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html
```

Key policy for the store: the service principal gets `kms:GenerateDataKey` and `kms:Decrypt` with
`aws:SourceAccount` and `aws:SourceArn = arn:aws:cloudtrail:<region>:<account>:eventdatastore/<id>`.
Add these conditions after the store is created. Users running queries need `kms:Decrypt` and
`kms:GenerateDataKey`. Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-kms-key-policy-for-cloudtrail.html

Import: `arn:aws:cloudtrail:<region>:<account>:eventdatastore/<id>` (`identity { arn }` needs
Terraform >= 1.12). Timeouts: create/update/delete 5m.

## 6. Organization delegated administrator (global)

Global resource: no `region` argument and no `@region` import (import by account ID only).

```hcl
resource "aws_cloudtrail_organization_delegated_admin_account" "this" {
  account_id = var.delegated_account_id  # member account to delegate (placeholder variable)
  # no region argument: global resource
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudtrail_organization_delegated_admin_account.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
```

Attributes: `arn`, `email`, `name`, `service_principal`. Which account creates it: (unverified).
Organizations setup belongs to `provisioning-aws-organizations-v6`.

## 7. terraform test and CI

```hcl
# tests/trail.tftest.hcl (fragment: assumes the root module defines aws_cloudtrail.this)
mock_provider "aws" {}

run "trail_is_hardened" {
  command = plan

  assert {
    condition     = aws_cloudtrail.this.is_multi_region_trail && aws_cloudtrail.this.enable_log_file_validation
    error_message = "Trail must be multi-region with log file validation."
  }
  assert {
    condition     = aws_cloudtrail.this.kms_key_id != null
    error_message = "Trail must set kms_key_id."
  }
}
# Source: https://developer.hashicorp.com/terraform/language/tests
```

CI: `terraform init -backend=false`, `terraform validate -json`, `terraform plan -detailed-exitcode`
(0 no changes, 1 error, 2 changes). Source: https://developer.hashicorp.com/terraform/cli/commands/plan
