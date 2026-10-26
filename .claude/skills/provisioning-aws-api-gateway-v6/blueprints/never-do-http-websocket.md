# Never-Do — HTTP and WebSocket APIs (v2) and family mixing

hashicorp/aws 6.x · Terraform ~> 1.16 · Per-source read dates: see the bibliography in unverified-and-risks.md. Blocks referencing resources defined
elsewhere are fragments; `# example` / `# placeholder` values are not from the docs.

## 1. Separate integrations or routes on an API that has a body

With `body` on `aws_apigatewayv2_api`, do not manage integrations or routes as separate resources;
"updates may cause manual resource updates to be overwritten". `name`, `description`, `cors_configuration`,
`tags` and `version` set in Terraform override the spec.

```hcl
# WRONG
resource "aws_apigatewayv2_api" "bad" {
  name          = "example"                          # example
  protocol_type = "HTTP"
  body          = file("${path.module}/openapi.json") # example path
}
resource "aws_apigatewayv2_route" "bad" {              # WRONG — separate route alongside body
  api_id    = aws_apigatewayv2_api.bad.id
  route_key = "GET /pets"                              # example
}

# CORRECT — define routes and integrations in the spec, or omit body and use separate resources
resource "aws_apigatewayv2_api" "good" {
  name          = "example"                          # example
  protocol_type = "HTTP"
  body          = file("${path.module}/openapi.json") # example path; no separate routes
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api.html.markdown
```

## 2. logging_level or data_trace_enabled on an HTTP API stage

On `aws_apigatewayv2_stage`, `data_trace_enabled` and `logging_level` are WebSocket only.

```hcl
# WRONG — HTTP API stage
resource "aws_apigatewayv2_stage" "bad" {
  api_id = aws_apigatewayv2_api.http.id
  name   = "example" # example
  default_route_settings {
    logging_level = "ERROR" # WRONG — WebSocket only
  }
}

# CORRECT — set these only on a WebSocket API stage
resource "aws_apigatewayv2_stage" "good" {
  api_id = aws_apigatewayv2_api.ws.id
  name   = "example" # example
  default_route_settings {
    logging_level = "ERROR"
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_stage.html.markdown
```

## 3. JWT authorization type on a WebSocket route

WebSocket routes accept `NONE`, `AWS_IAM` or `CUSTOM`; `JWT` is HTTP only (as is `jwt_configuration`).

```hcl
# WRONG
resource "aws_apigatewayv2_route" "bad" {
  api_id             = aws_apigatewayv2_api.ws.id
  route_key          = "$default"
  authorization_type = "JWT" # WRONG — HTTP only
}

# CORRECT
resource "aws_apigatewayv2_route" "good" {
  api_id             = aws_apigatewayv2_api.ws.id
  route_key          = "$default"
  authorization_type = "AWS_IAM"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_route.html.markdown
```

## 4. AWS, HTTP or MOCK integration type on an HTTP API

`AWS`, `HTTP` and `MOCK` are WebSocket only on `aws_apigatewayv2_integration`.

```hcl
# WRONG — fragment (other integration arguments are on the integration page)
resource "aws_apigatewayv2_integration" "bad" {
  api_id           = aws_apigatewayv2_api.http.id
  integration_type = "MOCK" # WRONG — WebSocket only
}

# CORRECT — fragment, HTTP API
resource "aws_apigatewayv2_integration" "good" {
  api_id           = aws_apigatewayv2_api.http.id
  integration_type = "AWS_PROXY" # or HTTP_PROXY
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_integration.html.markdown
```

## 5. Integration timeout outside the protocol range

`timeout_milliseconds` is 50-30000 for HTTP APIs and 50-29000 for WebSocket APIs.

```hcl
# WRONG — fragment, WebSocket integration
resource "aws_apigatewayv2_integration" "bad" {
  api_id               = aws_apigatewayv2_api.ws.id
  integration_type     = "AWS_PROXY"
  timeout_milliseconds = 30000 # WRONG — WebSocket maximum is 29000
}

# CORRECT — fragment
resource "aws_apigatewayv2_integration" "good" {
  api_id               = aws_apigatewayv2_api.ws.id
  integration_type     = "AWS_PROXY"
  timeout_milliseconds = 29000
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_integration.html.markdown
```

## 6. Version 1 resources for an HTTP or WebSocket API

"Amazon API Gateway Version 1 resources are used for creating and deploying REST APIs"; WebSocket and HTTP
APIs use Version 2 resources.

```hcl
# WRONG — HTTP API built from v1 resources
resource "aws_api_gateway_rest_api" "bad" {
  name = "example-http-api" # example; intended as an HTTP API — WRONG family
}

# CORRECT
resource "aws_apigatewayv2_api" "good" {
  name          = "example-http-api" # example
  protocol_type = "HTTP"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api.html.markdown
```
