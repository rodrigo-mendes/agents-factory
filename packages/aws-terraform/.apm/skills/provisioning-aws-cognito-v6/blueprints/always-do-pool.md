# Always-Do — User Pool (Terraform Block, Sign-in, MFA, Email, Schema)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. All names, ARNs, emails and numbers are examples.

## 1. Terraform Block and Region

Root modules use `~>`; reusable modules set only a minimum (`>=`). Cognito resources document the optional `region`
argument (default = provider Region); changing it forces replacement and import uses `id@region`.

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
}
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
```

## 2. User Pool Sign-in, MFA, Recovery, and Email

- `username_attributes` (`email`, `phone_number`) conflicts with `alias_attributes`; set only one.
- `mfa_configuration` is `OFF` (default), `ON` or `OPTIONAL`; `ON`/`OPTIONAL` need at least one MFA method block.
- `email_mfa_configuration` needs an `email_configuration` block. Provider page wording: "requires at least 2
  `account_recovery_setting` entries"; the page's own example uses one `account_recovery_setting` block with two
  `recovery_mechanism` blocks (`verified_email` priority 1, `verified_phone_number` priority 2). The wording and the
  example differ (medium confidence); the HCL below follows the page's example.
- `DEVELOPER` is required if `from_email_address` is set; `source_arn` (SES verified identity ARN) is required with it.

```hcl
# Fragment: var.ses_identity_arn references an SES identity defined elsewhere (provisioning-aws-ses-v6).
resource "aws_cognito_user_pool" "main" {
  name                     = "example-pool"   # example
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  mfa_configuration        = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true
  }

  email_mfa_configuration {
    subject = "Your sign-in code"             # example
    message = "Your code is {####}"           # example; message must contain {####}
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
    recovery_mechanism {
      name     = "verified_phone_number"
      priority = 2
    }
  }

  email_configuration {
    email_sending_account = "DEVELOPER"
    from_email_address    = "no-reply@example.org"   # example
    source_arn            = var.ses_identity_arn
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown
```

To disable the software token method without `sms_configuration`, set `mfa_configuration = "OFF"` and remove the block
(same page). Verified-attribute behavior and the immutability of sign-in identifiers are described by AWS:
https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html

## 3. Schema, Password Policy, and Deletion Protection

`schema` is add-only: "Attributes can be added, but not modified or removed." (maximum 50). `attribute_data_type`
is `Boolean`, `Number`, `String` or `DateTime`; `number_attribute_constraints` / `string_attribute_constraints`
are required for Number/String (their arguments are on the provider page). AWS: custom attributes "are permanent".
`password_history_size` (0–24) requires advanced security features to be active.

```hcl
# Fragment: additional arguments inside resource "aws_cognito_user_pool" "main" (section 2).
  deletion_protection = "ACTIVE"   # valid: ACTIVE | INACTIVE (default); INACTIVE before deleting; Cognito.6 posture

  password_policy {
    minimum_length                   = 12      # example
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7       # example
  }

  schema {
    name                = "marketing_opt_in"   # example
    attribute_data_type = "Boolean"
    mutable             = true
  }
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown
# Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cognito-controls.html (Cognito.3, Cognito.6)
```

Other optional blocks documented on the provider page: `admin_create_user_config`, `verification_message_template`,
`user_attribute_update_settings` (each value must also be in `auto_verified_attributes`), `lambda_config`, `tags`.
