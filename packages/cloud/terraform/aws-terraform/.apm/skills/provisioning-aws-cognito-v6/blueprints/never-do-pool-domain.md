# Never-Do — User Pool, MFA, Custom Domain, Provider Version

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. All values are examples; blocks are fragments.

## 1. username_attributes together with alias_attributes

The provider page documents that `username_attributes` (`email`, `phone_number`) conflicts with `alias_attributes`.

```hcl
# WRONG — both sign-in identifier arguments on one pool
resource "aws_cognito_user_pool" "bad" {
  name                = "example-pool"    # example
  username_attributes = ["email"]         # WRONG — conflicts with alias_attributes
  alias_attributes    = ["preferred_username"]
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown

# CORRECT — one of the two
resource "aws_cognito_user_pool" "ok" {
  name                = "example-pool"    # example
  username_attributes = ["email"]
}
```

## 2. Removing sms_configuration in place

Provider page WARNING: "Due to Cognito API restrictions, the SMS configuration cannot be removed without recreating the
Cognito User Pool." Drift detection is disabled for this block; the page says to use `taint` to force recreation.

```hcl
# WRONG — deleting this block from an existing pool and expecting an in-place update
resource "aws_cognito_user_pool" "main" {
  name = "example-pool"                                # example
  sms_configuration {                                  # WRONG to remove later without recreation
    external_id    = "example-external-id"             # example
    sns_caller_arn = "arn:aws:iam::111122223333:role/example-sns"   # example
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown

# CORRECT — plan to recreate the pool when SMS must go: taint the resource as the provider page
# instructs, then remove the block (exact command line not stated on the page)
```

## 3. MFA ON or OPTIONAL without a method block

`ON`/`OPTIONAL` require at least one of `email_mfa_configuration`, `sms_configuration`,
`software_token_mfa_configuration`.

```hcl
# WRONG — mfa_configuration set, no method block
resource "aws_cognito_user_pool" "bad" {
  name              = "example-pool"   # example
  mfa_configuration = "ON"             # WRONG — no MFA method configured
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown

# CORRECT — add a method
resource "aws_cognito_user_pool" "ok" {
  name              = "example-pool"   # example
  mfa_configuration = "ON"
  software_token_mfa_configuration {
    enabled = true
  }
}
```

## 4. Custom domain certificate outside us-east-1

AWS: the custom domain fronts a CloudFront distribution, so the certificate must be in us-east-1 regardless of the
user pool Region; the provider page requires an ISSUED ACM certificate in us-east-1.

```hcl
# WRONG — certificate from a non-us-east-1 provider (fragment; aws_acm_certificate.eu defined elsewhere)
resource "aws_cognito_user_pool_domain" "bad" {
  domain          = "auth.example.org"            # example
  user_pool_id    = aws_cognito_user_pool.main.id
  certificate_arn = aws_acm_certificate.eu.arn    # WRONG — eu-west-1 certificate
}
# Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_domain.html.markdown

# CORRECT — ISSUED certificate created in us-east-1 (fragment; see provisioning-aws-acm-v6)
resource "aws_cognito_user_pool_domain" "ok" {
  domain          = "auth.example.org"            # example
  user_pool_id    = aws_cognito_user_pool.main.id
  certificate_arn = aws_acm_certificate_validation.us_east_1.certificate_arn
}
```

## 5. Pinning version 6.57.0

6.57.0 was withdrawn from GitHub and the Registry.

```hcl
# WRONG
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.57.0" }   # WRONG — withdrawn
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

# CORRECT
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```
