# Always-Do — OIDC, Users, Groups, and Password Policy

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 6. GitHub Actions OIDC Provider and Trust Role

`thumbprint_list` is **optional** for GitHub — AWS uses its own trusted root CA library and ignores
configured thumbprints for GitHub, Auth0, GitLab, Google, and S3-hosted JWKS providers.

The `sub` condition is **mandatory and must be non-wildcard**. IAM rejects any trust policy
create or update for the GitHub provider when the `sub` key is missing, is wildcard-only, or is null.

```hcl
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  # thumbprint_list omitted: AWS uses its own CA library for GitHub (thumbprints are kept but not used)
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_openid_connect_provider.html.markdown

data "aws_iam_policy_document" "github_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    # aud condition: audience must be sts.amazonaws.com for GitHub OIDC
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    # sub condition: REQUIRED and must be non-wildcard-only. IAM rejects if missing or wildcard-only.
    # Use StringEquals for exact match, StringLike for wildcard prefix patterns.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:MyOrg/MyRepo:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_ci" {
  name               = "github-ci"
  assume_role_policy = data.aws_iam_policy_document.github_assume.json
  tags = { Purpose = "GitHub Actions CI" }
}
# Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html
```

## 7. IAM Users and Groups

Attach policies to groups, not directly to users (Security Hub IAM.2). Use `aws_iam_user_group_membership`
for non-exclusive membership; `aws_iam_group_membership` is exclusive per group (only one resource per group).

```hcl
resource "aws_iam_group" "developers" {
  name = "developers"
  path = "/"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_group.html.markdown

resource "aws_iam_group_policy_attachment" "dev_read" {
  group      = aws_iam_group.developers.name
  policy_arn = aws_iam_policy.s3_read.arn
}

resource "aws_iam_user" "alice" {
  name          = "alice"
  path          = "/"
  force_destroy = true  # needed to destroy non-Terraform-managed access keys, login profiles, MFA devices
  tags = { Team = "platform" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_user.html.markdown

# Non-exclusive group membership — safe to declare in multiple resources
resource "aws_iam_user_group_membership" "alice_groups" {
  user   = aws_iam_user.alice.name
  groups = [aws_iam_group.developers.name]
}
```

Instance profile (for EC2 roles):
```hcl
resource "aws_iam_instance_profile" "app" {
  name = "app-profile"   # must be unique regardless of path — reusing a name gives EntityAlreadyExists
  role = aws_iam_role.app.name
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_instance_profile.html.markdown
```

## 8. Password Policy

All arguments are optional. The AWS defaults are: minimum 8 characters, 3 of 4 character types,
passwords never expire. CIS-safe settings (IAM.15/16/17) require length ≥ 14, all four `require_*`
true, reuse prevention 12–24, expiry ≤ 90 days.

**WARNING:** expiry changes take effect **immediately** on existing passwords. Destroy behavior is
not documented (U5) — changes may leave the AWS default.

```hcl
resource "aws_iam_account_password_policy" "cis" {
  minimum_password_length        = 14       # IAM.15: minimum 14 (AWS allows 6–128)
  require_uppercase_characters   = true     # IAM.11
  require_lowercase_characters   = true     # IAM.12
  require_symbols                = true     # IAM.13
  require_numbers                = true     # IAM.14
  password_reuse_prevention      = 24       # IAM.16: 1–24; max reuse prevention
  max_password_age               = 90       # IAM.17: 1–1095 days; applies immediately to existing passwords
  allow_users_to_change_password = true
  hard_expiry                    = false
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_account_password_policy.html.markdown
# AWS ranges: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html
```

Note: there is only one password policy per AWS account. This resource overwrites any existing policy.
Import ID: literal `iam-account-password-policy`.
