# Never-Do — Key Usage (Asymmetric Rotation, Alias Prefix, Removed Resources)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Rotation on Asymmetric or HMAC Keys

AWS automatic rotation applies only to symmetric encryption keys with `AWS_KMS` origin. Asymmetric
keys (RSA, ECC) and HMAC keys do not support automatic rotation. The exact error name returned by
the API when this is attempted is (unverified — U2); the restriction itself is confirmed.

```hcl
# WRONG — automatic rotation on an asymmetric key
resource "aws_kms_key" "bad" {
  key_usage                = "SIGN_VERIFY"
  customer_master_key_spec = "RSA_2048"
  enable_key_rotation      = true   # WRONG: AWS does not support auto-rotation for
                                    # asymmetric or HMAC keys
}
# Source: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html

# CORRECT — rotation disabled (default); use manual rotation via new key + alias retarget
resource "aws_kms_key" "signing_key_v1" {
  key_usage                = "SIGN_VERIFY"
  customer_master_key_spec = "RSA_2048"
  enable_key_rotation      = false   # default; explicit for clarity
  description              = "RSA signing key — version 1"
  tags                     = { Version = "1" }
}

resource "aws_kms_alias" "signing" {
  name          = "alias/signing-key"
  target_key_id = aws_kms_key.signing_key_v1.key_id
  # Manual rotation: create new key version, update target_key_id here.
}
```

## 2. alias/aws/ Prefix

The `alias/aws/` prefix is reserved for AWS managed keys. Creating an alias with this prefix causes
`InvalidAliasNameException`. This rule comes from the AWS API; the provider resource page does not
repeat it.

```hcl
# WRONG — alias/aws/ prefix is reserved for AWS managed keys
resource "aws_kms_alias" "bad" {
  name          = "alias/aws/my-app"   # WRONG: InvalidAliasNameException
  target_key_id = aws_kms_key.app.key_id
}
# Source: https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateAlias.html

# CORRECT — use a custom prefix under alias/
resource "aws_kms_alias" "ok" {
  name          = "alias/my-app"   # CORRECT: alias/<custom-name>
  target_key_id = aws_kms_key.app.key_id
}
```

## 3. aws_kms_secret Data Source Removed in 6.0

`data "aws_kms_secret"` was removed in hashicorp/aws 6.0 (its functionality had already been
removed in v2.0.0). Using it causes a provider error. Use `data "aws_kms_secrets"` (plural) instead.

```hcl
# WRONG — data source removed in hashicorp/aws 6.0
data "aws_kms_secret" "bad" {   # WRONG: removed in 6.0; causes provider error
  secret {
    name    = "master_password"
    payload = var.encrypted_password_base64
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

# CORRECT — use aws_kms_secrets (plural)
data "aws_kms_secrets" "ok" {
  secret {
    name    = "master_password"
    payload = var.encrypted_password_base64
  }
}

output "master_password" {
  value     = data.aws_kms_secrets.ok.plaintext["master_password"]
  sensitive = true
}
```

## 4. rotation_period_in_days Without enable_key_rotation

The provider docs state that `rotation_period_in_days` "must be enabled if `rotation_period_in_days`
is set" — meaning `enable_key_rotation = true` is required when this argument is present.

```hcl
# WRONG — rotation_period_in_days set while enable_key_rotation is false (default)
resource "aws_kms_key" "bad" {
  enable_key_rotation     = false   # default
  rotation_period_in_days = 180     # WRONG: requires enable_key_rotation = true
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown

# CORRECT — enable rotation first, then set the period
resource "aws_kms_key" "ok" {
  enable_key_rotation     = true
  rotation_period_in_days = 180   # CORRECT: 90–2560 inclusive
  # Provider has no default for this argument. AWS uses 365 days when omitted on enable.
  # Source: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html
}
```
