# Never-Do — Secrets (insecure_value, value, Data Sources, Ephemeral)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. insecure_value on a SecureString

`insecure_value` is never marked sensitive and cannot be used with `SecureString`.

```hcl
# WRONG — insecure_value with SecureString
resource "aws_ssm_parameter" "bad" {
  name           = "/myapp/prod/db/password"   # example
  type           = "SecureString"
  insecure_value = var.db_password             # WRONG — not allowed with SecureString
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown

# CORRECT — write-only value
resource "aws_ssm_parameter" "good" {
  name             = "/myapp/prod/db/password"   # example
  type             = "SecureString"
  value_wo         = var.db_password_wo          # placeholder: declared elsewhere
  value_wo_version = 1                           # example
}
```

## 2. value for a SecureString expecting a clean state

The page states the unencrypted value of a `SecureString` is stored in state as plain text when
using `value`. Only `value_wo` avoids this.

```hcl
# WRONG — plaintext lands in state
resource "aws_ssm_parameter" "bad" {
  name  = "/myapp/prod/api/token"   # example
  type  = "SecureString"
  value = var.api_token             # WRONG — stored in state as plain text
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown

# CORRECT
resource "aws_ssm_parameter" "good" {
  name             = "/myapp/prod/api/token"   # example
  type             = "SecureString"
  value_wo         = var.api_token_wo          # placeholder: declared elsewhere
  value_wo_version = 1                         # example
}
```

## 3. aws_ssm_parameter data source expecting a clean state

The data source page documents that a decrypted `SecureString` value is stored in the raw state as
plain text.

```hcl
# WRONG — decrypted value stored in raw state
data "aws_ssm_parameter" "bad" {
  name            = "/myapp/prod/db/password"   # WRONG — example
  with_decryption = true                        # default
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameter.html.markdown

# CORRECT — do not read the value through the data source when you need a clean state.
# For an ephemeral alternative see ask-first-ephemeral.md (Ask First).
```

## 4. aws_ssm_parameters_by_path with decryption expecting a clean state

With `with_decryption = true` the by-path data source stores decrypted values in state as plain text.

```hcl
# WRONG — decrypted values stored in state
data "aws_ssm_parameters_by_path" "bad" {
  path            = "/myapp/prod"   # WRONG — example
  with_decryption = true            # default
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameters_by_path.html.markdown

# CORRECT — do not decrypt through this data source when you need a clean state.
# For an ephemeral alternative see ask-first-ephemeral.md (Ask First).
```

## 5. name on the ephemeral aws_ssm_parameter

```hcl
# WRONG — ephemeral resource takes arn, not name
ephemeral "aws_ssm_parameter" "bad" {
  name = "/myapp/prod/db/password"   # WRONG — example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/ssm_parameter.html.markdown

# CORRECT
ephemeral "aws_ssm_parameter" "good" {
  arn = "arn:aws:ssm:eu-west-1:111122223333:parameter/myapp/prod/db/password"   # example
}
```
