# Ask-First — Ephemeral Read

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## Ephemeral Read by arn (medium confidence)

The ephemeral `aws_ssm_parameter` requires `arn` (not `name`); `with_decryption` defaults to `true`.
The page calls ephemeral resources a new feature whose usage may change and states no minimum
Terraform version (unverified). That ephemeral values stay out of state and plan and are usable only
in ephemeral contexts (write-only arguments, provider configuration, other ephemeral resources)
is general Terraform behavior, not restated on the page (medium confidence). For metadata without
the value, the page directs you to the data source.

```hcl
ephemeral "aws_ssm_parameter" "source" {
  arn = "arn:aws:ssm:eu-west-1:111122223333:parameter/myapp/prod/db/password"   # example
}

# (medium confidence) relies on the ephemeral-context semantics above
resource "aws_ssm_parameter" "replica" {
  name             = "/myapp/replica/db/password"                  # example
  type             = "SecureString"
  value_wo         = ephemeral.aws_ssm_parameter.source.value
  value_wo_version = 1                                             # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/ssm_parameter.html.markdown
```

`value = ...` stores the plaintext in state (provider page); a write-only `value_wo` is the alternative the provider page documents.
