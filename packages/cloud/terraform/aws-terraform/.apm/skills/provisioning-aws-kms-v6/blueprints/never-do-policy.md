# Never-Do — Policy Configuration (Mixing Mechanisms, Lockout, Wildcard IAM)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Mixing Policy Mechanisms

Setting `policy` in `aws_kms_key` AND using `aws_kms_key_policy` for the same key causes
"inconsistencies and may overwrite configuration". Choose one mechanism.

```hcl
# WRONG — policy set in both aws_kms_key and aws_kms_key_policy for the same key
resource "aws_kms_key" "bad" {
  description = "Mixed policy example"
  policy      = data.aws_iam_policy_document.kms.json   # WRONG — do not use both
}
resource "aws_kms_key_policy" "bad" {
  key_id = aws_kms_key.bad.id
  policy = data.aws_iam_policy_document.kms.json         # WRONG — inconsistencies result
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown

# CORRECT — option A: inline policy only
resource "aws_kms_key" "ok_inline" {
  description = "Inline policy"
  policy      = data.aws_iam_policy_document.kms.json
}

# CORRECT — option B: standalone resource only (separate lifecycle)
resource "aws_kms_key" "ok_standalone" {
  description = "Standalone policy"
}
resource "aws_kms_key_policy" "ok_standalone" {
  key_id = aws_kms_key.ok_standalone.id
  policy = data.aws_iam_policy_document.kms.json
}
```

## 2. Omitting Root-Account Principal

Without the root-account delegation statement, IAM policies that allow access to the key are
ineffective. If the only named user or role is deleted, the key becomes unmanageable and you must
contact AWS Support to regain access.

```hcl
# WRONG — root-account delegation statement omitted
data "aws_iam_policy_document" "bad" {
  statement {
    sid     = "AdminOnly"
    actions = ["kms:*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::111122223333:user/key-admin"]
    }
    resources = ["*"]
    # WRONG: if this user is deleted, the key becomes unmanageable.
    # You must contact AWS Support to regain access.
  }
}
# Source: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html

# CORRECT — root-account statement present first
data "aws_iam_policy_document" "ok" {
  statement {
    sid     = "EnableIAMUserPermissions"
    actions = ["kms:*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    resources = ["*"]
    # This delegates to IAM; it does not by itself grant any IAM principal access.
  }
  # Add admin and user statements below...
}
```

## 3. Bypass Policy Lockout Safety Check

`bypass_policy_lockout_safety_check = true` prevents the calling principal from making a subsequent
`PutKeyPolicy` request. The docs state "Do not set this value to true indiscriminately." Leave it at
the default `false` in all standard configurations.

```hcl
# WRONG — bypass set to true by default
resource "aws_kms_key_policy" "bad" {
  key_id                             = aws_kms_key.app.id
  policy                             = data.aws_iam_policy_document.kms.json
  bypass_policy_lockout_safety_check = true   # WRONG: prevents future PutKeyPolicy by caller
}
# Source: https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateKey.html

# CORRECT — leave at default false (omit or set explicitly)
resource "aws_kms_key_policy" "ok" {
  key_id = aws_kms_key.app.id
  policy = data.aws_iam_policy_document.kms.json
  # bypass_policy_lockout_safety_check = false  # default; omit in normal use
}
```

## 4. Wildcard Resource in IAM Decrypt Policies

Allowing `kms:Decrypt` or `kms:ReEncryptFrom` on `"Resource": "*"` in an IAM policy fails Security
Hub KMS.1 (customer-managed policies) and KMS.2 (inline policies). It also covers keys in other
AWS accounts, not just the current account.

```hcl
# WRONG — decrypt on all keys (fails KMS.1 / KMS.2)
data "aws_iam_policy_document" "bad" {
  statement {
    actions   = ["kms:Decrypt", "kms:ReEncryptFrom"]
    resources = ["*"]   # WRONG: applies to every key in and beyond this account
  }
}
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html

# CORRECT — specific key ARNs
data "aws_iam_policy_document" "ok" {
  statement {
    actions = ["kms:Decrypt", "kms:ReEncryptFrom"]
    resources = [
      aws_kms_key.app.arn,
    ]   # CORRECT: scoped to specific key(s)
  }
}
# NOTE: "Resource": "*" is required ONLY for these actions:
# CreateKey, GenerateRandom, ListAliases, ListKeys, and custom key store actions.
# Source: https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html
```
