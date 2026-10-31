# Never-Do — Secrets (Secrets in State, Value Sources, Deprecated Attributes)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Secret values in secret_string

Terraform stores secrets added directly to configuration in state and plan files; `sensitive` values
are still stored there. Write-only arguments (Terraform ≥ 1.11) are not persisted.

```hcl
# WRONG — value lands in state and plan files
resource "aws_secretsmanager_secret_version" "bad" {
  secret_id     = aws_secretsmanager_secret.db.id
  secret_string = var.db_password   # WRONG — stored in state even if the variable is sensitive
}
# Source: https://developer.hashicorp.com/terraform/language/manage-sensitive-data

# CORRECT
resource "aws_secretsmanager_secret_version" "ok" {
  secret_id                = aws_secretsmanager_secret.db.id
  secret_string_wo         = var.db_password
  secret_string_wo_version = 1
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown
```

## 2. Two value sources on one version

Exactly one of `secret_string`, `secret_binary` (base64-encoded) or `secret_string_wo`.

```hcl
# WRONG
resource "aws_secretsmanager_secret_version" "bad" {
  secret_id                = aws_secretsmanager_secret.db.id
  secret_string            = "plain"   # WRONG — plus a write-only value below
  secret_string_wo         = var.db_password
  secret_string_wo_version = 1
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown

# CORRECT — see always-do-secrets, section 3
```

## 3. Deprecated arn on the version

`arn` is deprecated on `aws_secretsmanager_secret_version` and its data source; use `secret_arn`.

```hcl
# WRONG
output "bad" { value = aws_secretsmanager_secret_version.db.arn }   # WRONG — deprecated
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown

# CORRECT
output "ok" { value = aws_secretsmanager_secret_version.db.secret_arn }
```

## 4. Changing type after creation

`type` (managed external secret) cannot be changed after creation.

```hcl
# WRONG — editing type on an existing secret (example values)
resource "aws_secretsmanager_secret" "bad" {
  name = "app/ext"
  type = "SnowflakeKeyPairAuthentication"   # WRONG if changed later from another value
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown

# CORRECT — create a new secret with the desired type
resource "aws_secretsmanager_secret" "new_type" {
  name = "app/ext-v2"
  type = "SalesforceClientSecret"
}
```
