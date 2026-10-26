# Never-Do — Identity, Provider, and Region

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Setting region on IAM Resources

IAM is a **global service**. `aws_iam_*` resources are listed as non-region-aware in the enhanced
region support guide. Setting `region` on them triggers an unsupported-argument error.

```hcl
# WRONG — region is not supported on aws_iam_*
resource "aws_iam_role" "bad" {
  region             = "us-east-1"   # unsupported argument — error on plan
  name               = "bad-role"
  assume_role_policy = jsonencode({ ... })
}
```

```hcl
# CORRECT — omit region entirely on aws_iam_*
resource "aws_iam_role" "good" {
  name               = "good-role"
  assume_role_policy = jsonencode({ ... })
}
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

## 2. Using `id@region` Import IDs for IAM Resources

IAM resources are non-region-aware. Region-scoped import IDs (`name@us-east-1`) are only
supported by regional resources. Use plain name or ARN for all IAM imports.

```bash
# WRONG — @region suffix not supported for IAM
terraform import aws_iam_role.good good-role@us-east-1

# CORRECT — import by name only
terraform import aws_iam_role.good good-role
# Or with identity import (Terraform >= 1.12):
# import { to = aws_iam_role.good; id = "good-role" }
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

## 3. Using Deprecated `data.aws_region.current.name`

The `name` attribute on `data.aws_region` is **deprecated in 6.0**. Use `.region` instead in ARN
interpolation and any other context where the region string is needed.

```hcl
# WRONG — .name is deprecated in 6.0
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

resource "aws_iam_policy" "bad" {
  name   = "bad-arn-policy"
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogGroup"]
      Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
    }]                                                                # .name is deprecated ^^^
  })
}
```

```hcl
# CORRECT — use .region
resource "aws_iam_policy" "good" {
  name   = "good-arn-policy"
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogGroup"]
      Resource = "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:*"
    }]                                                               # .region ^^^
  })
}
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

## 4. Missing or Wildcard `sub` in GitHub OIDC Trust Policy

IAM **rejects any create or update** of a trust policy for the GitHub provider when the `sub`
condition is missing, is wildcard-only (`*`), or is null. Always scope to specific repos/branches.

```hcl
# WRONG — missing sub condition; IAM will reject this trust policy
data "aws_iam_policy_document" "bad_github" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    # sub condition missing — IAM rejects the policy
  }
}
```

```hcl
# CORRECT — scoped sub condition
data "aws_iam_policy_document" "good_github" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    # Non-wildcard sub: use StringEquals for exact match, StringLike for wildcard prefix
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:MyOrg/MyRepo:ref:refs/heads/main"]
    }
  }
}
```
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html

## 5. Long-Term Access Keys for Users or Workloads

`aws_iam_access_key.secret` is written to the **Terraform state in plaintext**. AWS best
practices require temporary credentials via IAM roles for workloads and human users.

```hcl
# WRONG — long-term key for a workload; secret in state in plaintext
resource "aws_iam_access_key" "bad" {
  user = aws_iam_user.alice.name
  # secret is written to state in plaintext
}
```

When long-term credentials are unavoidable (e.g. some third-party clients without role support):
- Use `pgp_key` to encrypt the secret at rest (`encrypted_secret` instead of `secret`).
- Note: on import, `secret`, `encrypted_secret`, `key_fingerprint`, and the SES password cannot
  be read from the IAM API and will be absent from state.
- Rotate regularly (Security Hub IAM.3: ≤ 90 days) and use "access last used" to remove stale keys.

```hcl
# BETTER — encrypt the secret with a PGP key or Keybase user
resource "aws_iam_access_key" "encrypted" {
  user    = aws_iam_user.alice.name
  pgp_key = "keybase:alice"   # or a raw base64-encoded PGP public key
  # encrypted_secret is in state instead of plaintext secret
}
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_access_key.html.markdown
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
