# Always-Do — Key Policy and Grants (Root Principal, Admin/User Separation, aws_kms_grant)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 4. Key Policy and Separation of Duties

The key policy must always include the root-account principal. Without it, IAM policies that allow
access to the key are ineffective. If the only named user is deleted, the key becomes unmanageable
and you must contact AWS Support to regain access.
Source: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html

Use `aws_kms_key_policy` (standalone) OR set `policy` inline in `aws_kms_key` — never both.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown

```hcl
data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "kms_key_policy" {
  # Statement 1 — CRITICAL: root account delegation.
  # Without this, IAM policies that allow access to the key are ineffective.
  statement {
    sid     = "EnableIAMUserPermissions"
    actions = ["kms:*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    resources = ["*"]
  }

  # Statement 2 — key administrators: management only, no cryptographic use.
  # kms:Delete* does NOT include ScheduleKeyDeletion — list it separately.
  # Source: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html
  statement {
    sid = "AllowKeyAdministration"
    actions = [
      "kms:Create*", "kms:Describe*", "kms:Enable*", "kms:List*",
      "kms:Put*", "kms:Update*", "kms:Revoke*", "kms:Disable*",
      "kms:Get*", "kms:Delete*", "kms:TagResource", "kms:UntagResource",
      "kms:ScheduleKeyDeletion", "kms:CancelKeyDeletion",
      "kms:RotateKeyOnDemand",
    ]
    principals {
      type        = "AWS"
      identifiers = var.key_admin_arns
    }
    resources = ["*"]
  }

  # Statement 3 — key users: symmetric encryption.
  # HMAC and asymmetric keys use different action sets.
  statement {
    sid = "AllowKeyUsage"
    actions = [
      "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*",
      "kms:GenerateDataKey*", "kms:DescribeKey",
    ]
    principals {
      type        = "AWS"
      identifiers = var.key_user_arns
    }
    resources = ["*"]
  }

  # Statement 4 — allow AWS services to create grants; restrict with kms:ViaService.
  # For service principals, add aws:SourceArn / aws:SourceAccount (confused deputy).
  statement {
    sid     = "AllowAttachmentOfPersistentResources"
    actions = ["kms:CreateGrant", "kms:ListGrants", "kms:RevokeGrant"]
    principals {
      type        = "AWS"
      identifiers = var.key_user_arns
    }
    resources = ["*"]
    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }
}

# Option A — standalone resource (separates policy lifecycle from key lifecycle)
resource "aws_kms_key_policy" "app" {
  key_id = aws_kms_key.app.id
  policy = data.aws_iam_policy_document.kms_key_policy.json
  # bypass_policy_lockout_safety_check defaults to false — do not set to true routinely.
  # Source: https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateKey.html
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key_policy.html.markdown

# Option B — inline (simpler; single-module ownership)
# resource "aws_kms_key" "app" {
#   ...
#   policy = data.aws_iam_policy_document.kms_key_policy.json
# }
# Use Option A or Option B; never both.
```

Policy limits and lockout safety:
- Maximum policy size: 32 768 characters.
- Policy must allow the calling principal to make a subsequent `PutKeyPolicy` request.
- `bypass_policy_lockout_safety_check = true` prevents this check. Use only when intentionally
  preventing future policy changes.
- Principals must exist and be visible to KMS; newly created principals may need a delay due to
  IAM eventual consistency.

## 5. aws_kms_grant

Use grants for programmatic, service-level access when key policies are not sufficient.
All required arguments (`key_id`, `grantee_principal`, `operations`) force replacement.

```hcl
resource "aws_kms_grant" "rds_access" {
  key_id = aws_kms_key.app.key_id
  # For cross-account keys, use the key ARN instead of key_id.

  grantee_principal = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/rds-monitoring-role"

  operations = [
    "Decrypt",
    "Encrypt",
    "GenerateDataKey",
    "DescribeKey",
  ]
  # The full valid operations list has 14 values (medium confidence — M2).
  # Confirmed values include: Decrypt, Encrypt, GenerateDataKey, Sign, Verify,
  # DescribeKey, RetireGrant, and others. Re-read the raw resource page to copy the full list.
  # Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_grant.html.markdown

  # retire_on_delete = false  # default: revokes the grant on delete (requires no extra perms)
  #                           # true: retires instead; needs additional permissions
}
# State warning: ALL arguments including grant_token are stored as plain-text in Terraform state.
# grant_token is not documented as a sensitive attribute.
# IAM eventual consistency on grantee_principal may cause state drift.
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_grant.html.markdown
```
