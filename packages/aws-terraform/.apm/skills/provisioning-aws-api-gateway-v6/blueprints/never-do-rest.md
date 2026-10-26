# Never-Do — REST APIs (v1: `aws_api_gateway_*`)

hashicorp/aws 6.x · Terraform ~> 1.16 · Per-source read dates: see the bibliography in unverified-and-risks.md. Each WRONG block is an
anti-pattern for the REST family only; blocks referencing resources defined elsewhere are fragments;
`# example` / `# placeholder` values are not from the docs.

## 1. Both certificate_arn and regional_certificate_arn on a domain name

The two arguments conflict with each other.

```hcl
# WRONG
resource "aws_api_gateway_domain_name" "bad" {
  domain_name              = var.domain_name         # placeholder
  certificate_arn          = var.edge_certificate    # WRONG — conflicts with regional_certificate_arn
  regional_certificate_arn = var.regional_certificate # WRONG
}

# CORRECT — fragment; regional endpoint (use certificate_arn alone for edge)
resource "aws_api_gateway_domain_name" "good" {
  domain_name              = var.domain_name          # placeholder
  regional_certificate_arn = var.regional_certificate # placeholder
  endpoint_configuration { types = ["REGIONAL"] }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_domain_name.html.markdown
```

## 2. Removing response_transfer_mode to revert to BUFFERED

Once `response_transfer_mode` is set, revert by writing `BUFFERED` explicitly, not by removing it.

```hcl
# WRONG — fragment; attribute deleted after having been STREAM
resource "aws_api_gateway_integration" "bad" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  resource_id = aws_api_gateway_resource.example.id
  http_method = aws_api_gateway_method.get.http_method
  type        = "HTTP_PROXY"
  uri         = var.integration_uri # placeholder
  # response_transfer_mode removed here — WRONG
}

# CORRECT — fragment
resource "aws_api_gateway_integration" "good" {
  rest_api_id            = aws_api_gateway_rest_api.example.id
  resource_id            = aws_api_gateway_resource.example.id
  http_method            = aws_api_gateway_method.get.http_method
  type                   = "HTTP_PROXY"
  uri                    = var.integration_uri # placeholder
  response_transfer_mode = "BUFFERED"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_integration.html.markdown
```

## 3. API keys as authentication or authorization

AWS: "Don't use API keys for authentication or authorization"; a key valid for one API in a plan accesses
all APIs in that plan. The method page lists `authorization` values `NONE`, `CUSTOM`, `AWS_IAM` and
`COGNITO_USER_POOLS`.

```hcl
# WRONG — fragment; the key is the only protection
resource "aws_api_gateway_method" "bad" {
  rest_api_id      = aws_api_gateway_rest_api.example.id
  resource_id      = aws_api_gateway_resource.example.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true # WRONG as the only access control
}

# CORRECT — fragment; set an authorization type on the method
resource "aws_api_gateway_method" "good" {
  rest_api_id      = aws_api_gateway_rest_api.example.id
  resource_id      = aws_api_gateway_resource.example.id
  http_method      = "GET"
  authorization    = "AWS_IAM"
  api_key_required = true
}
# Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method.html.markdown
```

## 4. Usage-plan throttling or quotas to control costs or block access

AWS: usage-plan throttling and quotas are best-effort; do not rely on them to control costs or block access.

```hcl
# WRONG — quota used as the cost / access control
resource "aws_api_gateway_usage_plan" "bad" {
  name = "cost-cap" # example
  quota_settings {  # WRONG as the only cost or access control
    limit  = 100    # example
    period = "DAY"
  }
}
# CORRECT — keep the plan for client identification; use AWS Budgets for cost and AWS WAF
# (provisioning-aws-waf-v6) for blocking access; no Terraform fragment for Budgets in this skill.
# Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html
```
