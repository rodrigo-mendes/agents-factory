# Always-Do — App Client, Domain, Identity Pool

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. All names, ARNs and URLs are examples.

## 4. User Pool Client (OAuth)

`allowed_oauth_flows_user_pool_client = true` must be set before `allowed_oauth_flows` (`code`, `implicit`,
`client_credentials`), `allowed_oauth_scopes`, `callback_urls` and `logout_urls`; `default_redirect_uri` must be in
`callback_urls`. `explicit_auth_flows` accepts `ALLOW_USER_AUTH`, `ALLOW_USER_SRP_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH`,
`ALLOW_USER_PASSWORD_AUTH`, `ALLOW_ADMIN_USER_PASSWORD_AUTH`, `ALLOW_CUSTOM_AUTH` (plus legacy values).

```hcl
# Fragment: references aws_cognito_user_pool.main from always-do-pool.md section 2.
resource "aws_cognito_user_pool_client" "web" {
  name         = "web-client"   # example
  user_pool_id = aws_cognito_user_pool.main.id

  explicit_auth_flows = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email"]
  callback_urls                        = ["https://app.example.org/callback"]   # example
  default_redirect_uri                 = "https://app.example.org/callback"     # example; also in callback_urls
  logout_urls                          = ["https://app.example.org/logout"]     # example
  supported_identity_providers         = ["COGNITO"]

  prevent_user_existence_errors = "ENABLED"   # values LEGACY | ENABLED
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_client.html.markdown
# Source: https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html
```

## 5. User Pool Domain, Prefix and Custom

Required: `domain`, `user_pool_id`. A prefix domain is just the prefix (for example `auth`). A custom domain is the FQDN plus
`certificate_arn` of an ISSUED ACM certificate in us-east-1 (provider page; AWS page: it fronts a CloudFront distribution,
so us-east-1 applies regardless of the pool Region). Parent domain must resolve via an A record; public hosted zone only.
Creating the certificate through a `us-east-1` provider alias is (medium confidence); so is `region = "us-east-1"` on
`aws_acm_certificate`, inferred from the enhanced-region guide. ACM details: provisioning-aws-acm-v6.

```hcl
# Fragment: aws_acm_certificate_validation.cognito (us-east-1) and var.zone_id are defined elsewhere.
resource "aws_cognito_user_pool_domain" "custom" {
  domain          = "auth.example.org"   # example
  user_pool_id    = aws_cognito_user_pool.main.id
  certificate_arn = aws_acm_certificate_validation.cognito.certificate_arn
}

# Fragment: only the alias block of an aws_route53_record is shown (record attributes: provisioning-aws-route53-v6).
  alias {
    name                   = aws_cognito_user_pool_domain.custom.cloudfront_distribution
    zone_id                = aws_cognito_user_pool_domain.custom.cloudfront_distribution_zone_id
    evaluate_target_health = false
  }
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_domain.html.markdown
# Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html
```

`managed_login_version`: `1` = classic hosted UI, `2` = managed login. Import: the domain value (for example
`auth.example.org`). `aws_cognito_user_pool_ui_customization` requires a domain on the pool (page:
"the user pool must have a domain associated with it").

## 6. Identity Pool and Roles Attachment

Required: `identity_pool_name`, `allow_unauthenticated_identities`. For `role_mapping` of type `Token` or `Rules`,
`ambiguous_role_resolution` is required; `mapping_rule` allows up to 25 entries. Security Hub Cognito.2 says
identity pools should not allow unauthenticated identities.

```hcl
# Fragment: aws_iam_role.authenticated is defined elsewhere (provisioning-aws-iam-v6).
resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = "example_identity_pool"   # example
  allow_unauthenticated_identities = false

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.web.id
    provider_name           = "<provider-name>"   # placeholder; see the provider page
    server_side_token_check = true
  }
}

resource "aws_cognito_identity_pool_roles_attachment" "main" {
  identity_pool_id = aws_cognito_identity_pool.main.id
  roles = {
    authenticated = aws_iam_role.authenticated.arn
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_identity_pool.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_identity_pool_roles_attachment.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cognito-controls.html
```
