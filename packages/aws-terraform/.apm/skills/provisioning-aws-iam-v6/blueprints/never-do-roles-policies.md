# Never-Do — Roles, Policies, and Attachments

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Using Deprecated `inline_policy` or `managed_policy_arns`

`inline_policy` (deprecated since **5.68.0**) and `managed_policy_arns` (deprecated since **5.72.0**)
are still present in 6.x but must not be used. They are incompatible with the separate attachment
resources and cause "resource cycling and/or errors".

```hcl
# WRONG — inline_policy deprecated; incompatible with aws_iam_role_policy
resource "aws_iam_role" "bad" {
  name               = "bad-role"
  assume_role_policy = jsonencode({ ... })
  inline_policy {
    name   = "bad-inline"
    policy = jsonencode({ ... })
  }
  managed_policy_arns = ["arn:aws:iam::aws:policy/ReadOnlyAccess"]
}
```

```hcl
# CORRECT — use separate resources + exclusive management
resource "aws_iam_role" "good" {
  name               = "good-role"
  assume_role_policy = jsonencode({ ... })
  # No inline_policy, no managed_policy_arns
}
resource "aws_iam_role_policy" "good_inline" {
  name   = "good-inline"
  role   = aws_iam_role.good.name
  policy = jsonencode({ ... })
}
resource "aws_iam_role_policies_exclusive" "good" {
  role_name    = aws_iam_role.good.name
  policy_names = [aws_iam_role_policy.good_inline.name]
}
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role.html.markdown

## 2. Mixing `aws_iam_policy_attachment` with Role-Scoped Attachments

Combining `aws_iam_policy_attachment` and `aws_iam_role_policy_attachment` on the same role
causes a permanent diff in the Terraform plan.

```hcl
# WRONG — mixing attachment resources on the same role
resource "aws_iam_policy_attachment" "bad" {
  name       = "bad-attach"
  roles      = [aws_iam_role.app.name]
  policy_arn = aws_iam_policy.s3_read.arn
}
resource "aws_iam_role_policy_attachment" "also_bad" {   # permanent diff
  role       = aws_iam_role.app.name
  policy_arn = aws_iam_policy.s3_read.arn
}
```

```hcl
# CORRECT — single mechanism per role
resource "aws_iam_role_policy_attachment" "good" {
  role       = aws_iam_role.app.name
  policy_arn = aws_iam_policy.s3_read.arn
}
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy_attachment.html.markdown

## 3. `aws_iam_policy_attachment` Exclusive Blast Radius

`aws_iam_policy_attachment` creates **account-wide exclusive attachments**. Every user, role, and
group holding the policy must be declared in one resource. Any holder managed elsewhere — including
through other Terraform resources — has the policy silently revoked.

```hcl
# WRONG — another Terraform resource or manual attachment will be revoked
resource "aws_iam_policy_attachment" "bad" {
  name       = "exclusive-attach"
  roles      = [aws_iam_role.app.name]    # any other role not listed is detached
  users      = []
  groups     = []
  policy_arn = aws_iam_policy.s3_read.arn
}
```

```hcl
# CORRECT — use scoped attachment resources; one per role/user/group
resource "aws_iam_role_policy_attachment" "app" {
  role       = aws_iam_role.app.name
  policy_arn = aws_iam_policy.s3_read.arn
}
```
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_policy_attachment.html.markdown

## 4. Admin Wildcard in Customer Managed Policy

Security Hub IAM.1 checks for `Action *` on `Resource *` in customer managed policies.
Boundary policies are excluded from IAM.1 checks, but admin wildcards should still be avoided.

```hcl
# WRONG — admin policy violates IAM.1
resource "aws_iam_policy" "bad_admin" {
  name   = "bad-admin"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"          # IAM.1 violation
      Resource = "*"
    }]
  })
}
```

```hcl
# CORRECT — least-privilege, scoped to specific actions and resources
resource "aws_iam_policy" "good" {
  name   = "s3-read"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Resource = ["arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket/*"]
    }]
  })
}
```
Source: https://docs.aws.amazon.com/securityhub/latest/userguide/iam-controls.html

