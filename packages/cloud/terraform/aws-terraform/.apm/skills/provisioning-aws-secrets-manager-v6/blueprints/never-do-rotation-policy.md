# Never-Do — Rotation, Policy Removal, Withdrawn Version

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. ISO-8601 rotation duration

`duration` is the window length in hours.

```hcl
# WRONG
rotation_rules {
  automatically_after_days = 30   # example value
  duration                 = "P7D"   # WRONG — ISO-8601
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown

# CORRECT
rotation_rules {
  automatically_after_days = 30
  duration                 = "3h"
}
```

## 2. rotation_rules with rotation_enabled = false

`rotation_rules` is optional and must be omitted when rotation is disabled (`rotation_enabled`
configurable since 6.62.0).

```hcl
# WRONG
resource "aws_secretsmanager_secret_rotation" "bad" {
  secret_id        = aws_secretsmanager_secret.db.id
  rotation_enabled = false
  rotation_rules { automatically_after_days = 30 }   # WRONG
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

# CORRECT
resource "aws_secretsmanager_secret_rotation" "ok" {
  secret_id        = aws_secretsmanager_secret.db.id
  rotation_enabled = false
}
```

## 3. Removing a policy the wrong way

On the secret, `null` or `""` does not delete the policy; use `"{}"`. The policy resource rejects `"{}"`.

```hcl
# WRONG
resource "aws_secretsmanager_secret" "bad" {
  name   = "app/bad"
  policy = null   # WRONG — does not delete the existing policy
}
# (aws_iam_policy_document data sources are placeholders in these examples)
resource "aws_secretsmanager_secret_policy" "bad" {
  secret_arn = aws_secretsmanager_secret.bad.arn
  policy     = "{}"   # WRONG — rejected by the policy resource
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_policy.html.markdown

# CORRECT
resource "aws_secretsmanager_secret" "ok" {
  name   = "app/ok"
  policy = "{}"   # deletes the policy
}
```

## 4. Pinning version 6.57.0

```hcl
# WRONG
aws = { source = "hashicorp/aws", version = "6.57.0" }   # WRONG — withdrawn from GitHub and the Registry
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

# CORRECT
aws = { source = "hashicorp/aws", version = "~> 6.69" }
```
