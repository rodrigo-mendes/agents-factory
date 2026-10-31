# Always-Do — Secrets (SecureString)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 4. SecureString with value_wo and a CMK

`value_wo` is never stored in state, requires `value_wo_version` and Terraform >= 1.11.
Changing `value_wo_version` triggers an update of `value_wo`. Without `key_id` AWS uses `aws/ssm`,
whose access cannot be controlled by policy; only symmetric KMS keys are supported. Standard tier
needs `kms:Encrypt`, Advanced needs `kms:GenerateDataKey`, decryption needs `kms:Decrypt`.

```hcl
resource "aws_ssm_parameter" "db_password" {
  name             = "/myapp/prod/db/password"   # example
  type             = "SecureString"
  key_id           = aws_kms_key.params.arn      # example: symmetric CMK declared elsewhere
  value_wo         = var.db_password_wo          # placeholder: declared elsewhere
  value_wo_version = 1                           # example; bump to rotate
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown
# Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/secure-string-parameter-kms-encryption.html
```

Writes that use `value` store the plaintext in state.
