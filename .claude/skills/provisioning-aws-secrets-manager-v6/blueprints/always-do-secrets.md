# Always-Do — Secrets (Terraform Block, Secret, Version, Ephemeral)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Terraform block

Root modules pin providers with `~>`.

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```

## 2. Secret

No argument is required. `recovery_window_in_days` defaults to 30 (`0` = deletion without recovery,
otherwise 7–30). `kms_key_id` takes an ARN or ID (ARN for a key in another account); the default is the
account's `aws/secretsmanager` key. `replica` needs `region`; `kms_key_id` is optional per replica.
`tags` override matching `default_tags` keys.

```hcl
resource "aws_secretsmanager_secret" "db" {
  name                    = "app/db/password"   # letters, digits and /_+=.@-
  description             = "Database password"
  kms_key_id              = var.kms_key_arn     # ARN, required form for another account's key
  recovery_window_in_days = 30                  # default; 0 = no recovery

  replica {
    region     = "eu-west-1"                    # example Region
    kms_key_id = var.replica_kms_key_arn        # optional; default is that Region's aws/secretsmanager
  }

  tags = { Environment = "prod" }               # no PII in tags
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/secretsmanager-controls.html (SecretsManager.5)
```

Exports: `arn`, `id` (= ARN), `replica` (computed `status`, `status_message`, `last_accessed_date`), `tags_all`.
Import with identity `{ arn = "<secret-arn>" }` (Terraform ≥ 1.12) or `import { id = "<secret-arn>" }`.

## 3. Secret version with a write-only value

Exactly one value source. `secret_string_wo` needs Terraform ≥ 1.11 and `secret_string_wo_version`;
changing the version triggers the update. If `version_stages` is set, include `AWSCURRENT` when this
is the only version or the label is already on it, otherwise a perpetual diff.

```hcl
variable "db_password" {
  type      = string
  sensitive = true   # keeps it out of logs and console output
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id                = aws_secretsmanager_secret.db.id
  secret_string_wo         = var.db_password
  secret_string_wo_version = 1   # bump to push a new value
  # version_stages omitted: AWS moves AWSCURRENT to the new version on create
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown
# Source: https://developer.hashicorp.com/terraform/language/manage-sensitive-data
```

The resource tracks only its own version, even after rotation. Exports: `secret_arn`, `version_id`,
`has_secret_string_wo`.

## 4. Ephemeral and data source reads

The ephemeral `aws_secretsmanager_secret_version` takes the same arguments as the data source and
returns decrypted values; Terraform does not store ephemeral resources in state or plan files. The data
source defaults `version_stage` to `AWSCURRENT`, and returns `secret_arn` (`arn` is deprecated).
Data source values are persisted in state (medium confidence, inferred from the Terraform docs).

```hcl
ephemeral "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/secretsmanager_secret_version.html.markdown
# Source: https://developer.hashicorp.com/terraform/language/manage-sensitive-data

data "aws_secretsmanager_secret_version" "current" {
  secret_id     = aws_secretsmanager_secret.db.id
  version_stage = "AWSCURRENT"   # default
}

output "secret_arn" {
  value = data.aws_secretsmanager_secret_version.current.secret_arn   # not the deprecated arn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/secretsmanager_secret_version.html.markdown
```
