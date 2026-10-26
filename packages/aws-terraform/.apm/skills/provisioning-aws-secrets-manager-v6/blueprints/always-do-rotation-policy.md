# Always-Do — Rotation and Resource Policy

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 5. Rotation

`rotation_lambda_arn` is required unless the secret is AWS-managed. `rotate_immediately` defaults to
`true`. `rotation_rules` takes `automatically_after_days` or `schedule_expression` (`cron()`/`rate()`),
and `duration` is the window length in hours. Enabling rotation rotates the secret once immediately.
For Aurora/clustered engines add `depends_on` on the cluster instance. Security Hub SecretsManager.4
checks rotation within 90 days (default).

```hcl
resource "aws_secretsmanager_secret_rotation" "db" {
  secret_id           = aws_secretsmanager_secret.db.id
  rotation_lambda_arn = var.rotation_lambda_arn   # required unless AWS-managed
  rotate_immediately  = true                      # default

  rotation_rules {
    automatically_after_days = 30                 # example value
    duration                 = "3h"               # hours, not ISO-8601
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/secretsmanager-controls.html (SecretsManager.4)
```

Disable rotation (configurable since 6.62.0) with `rotation_enabled = false` and no `rotation_rules`;
toggle with a `dynamic` block:

```hcl
resource "aws_secretsmanager_secret_rotation" "toggle" {
  secret_id        = aws_secretsmanager_secret.db.id
  rotation_enabled = var.rotation_enabled

  dynamic "rotation_rules" {
    for_each = var.rotation_enabled ? [1] : []
    content {
      automatically_after_days = 30
    }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md (6.62.0)
```

Notes: removing rotation mid-rotation can leave `AWSPENDING` on a partial version; destroying the
resource does not re-enable AWS-configured rotation. Import by secret ARN.

## 6. Resource policy

`secret_arn` and `policy` (JSON) are required; `"{}"` is rejected here. `block_public_policy` calls
Zelkova to validate the policy against broad access; its default is not stated (unverified), so set it
explicitly. Manage the policy in one place only (medium confidence): the secret's inline `policy` and
this resource write the same underlying policy.

```hcl
resource "aws_secretsmanager_secret_policy" "db" {
  secret_arn          = aws_secretsmanager_secret.db.arn
  policy              = data.aws_iam_policy_document.secret.json   # placeholder: define this data source elsewhere
  block_public_policy = true
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_policy.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown
```
