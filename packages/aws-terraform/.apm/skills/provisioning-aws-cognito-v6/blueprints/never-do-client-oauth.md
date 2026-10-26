# Never-Do — App Client, OAuth, Auth Flows

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. All values are examples; blocks are fragments
that reference `aws_cognito_user_pool.main` defined elsewhere.

## 1. allowed_oauth_flows without the flag

Provider page: `allowed_oauth_flows_user_pool_client = true` must be set before `allowed_oauth_flows`.

```hcl
# WRONG
resource "aws_cognito_user_pool_client" "bad" {
  name                 = "web-client"   # example
  user_pool_id         = aws_cognito_user_pool.main.id
  allowed_oauth_flows  = ["code"]       # WRONG — flag not set
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_client.html.markdown

# CORRECT
resource "aws_cognito_user_pool_client" "ok" {
  name                                 = "web-client"   # example
  user_pool_id                         = aws_cognito_user_pool.main.id
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
}
```

## 2. default_redirect_uri missing from callback_urls

```hcl
# WRONG
resource "aws_cognito_user_pool_client" "bad" {
  name                 = "web-client"   # example
  user_pool_id         = aws_cognito_user_pool.main.id
  callback_urls        = ["https://app.example.org/callback"]   # example
  default_redirect_uri = "https://app.example.org/other"        # WRONG — not in callback_urls
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_client.html.markdown

# CORRECT
resource "aws_cognito_user_pool_client" "ok" {
  name                                 = "web-client"   # example
  user_pool_id                         = aws_cognito_user_pool.main.id
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid"]
  callback_urls                        = ["https://app.example.org/callback"]   # example
  default_redirect_uri                 = "https://app.example.org/callback"     # example
}
```

## 3. Legacy auth-flow values combined with ALLOW_*

AWS: legacy values (`ADMIN_NO_SRP_AUTH`, `CUSTOM_AUTH_FLOW_ONLY`, `USER_PASSWORD_AUTH`) cannot be combined with `ALLOW_*`.

```hcl
# WRONG
resource "aws_cognito_user_pool_client" "bad" {
  name                = "web-client"   # example
  user_pool_id        = aws_cognito_user_pool.main.id
  explicit_auth_flows = ["USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH"]   # WRONG — legacy + ALLOW_* in one list
}
# Source: https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html

# CORRECT
resource "aws_cognito_user_pool_client" "ok" {
  name                = "web-client"   # example
  user_pool_id        = aws_cognito_user_pool.main.id
  explicit_auth_flows = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
}
```

## 4. client_credentials combined with other flows

AWS: when `client_credentials` is used it must be the only flow; it requires a client secret.

```hcl
# WRONG
resource "aws_cognito_user_pool_client" "bad" {
  name                                 = "m2m-client"   # example
  user_pool_id                         = aws_cognito_user_pool.main.id
  generate_secret                      = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["client_credentials", "code"]   # WRONG — mixed flows
}
# Source: https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html

# CORRECT
resource "aws_cognito_user_pool_client" "ok" {
  name                                 = "m2m-client"   # example
  user_pool_id                         = aws_cognito_user_pool.main.id
  generate_secret                      = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["client_credentials"]
}
```

## 5. Non-localhost http callback URLs

AWS: HTTPS is required except `http://localhost`, `http://127.0.0.1`, `http://[::1]` (testing).

```hcl
# WRONG
resource "aws_cognito_user_pool_client" "bad" {
  name          = "web-client"   # example
  user_pool_id  = aws_cognito_user_pool.main.id
  callback_urls = ["http://app.example.org/callback"]   # WRONG — http on a non-localhost host
}
# Source: https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html

# CORRECT
resource "aws_cognito_user_pool_client" "ok" {
  name                                 = "web-client"   # example
  user_pool_id                         = aws_cognito_user_pool.main.id
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid"]
  callback_urls                        = ["https://app.example.org/callback"]   # example
}
```
