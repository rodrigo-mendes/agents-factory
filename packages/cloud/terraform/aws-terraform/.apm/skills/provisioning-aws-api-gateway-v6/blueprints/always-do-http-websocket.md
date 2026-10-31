# Always-Do — HTTP and WebSocket APIs (v2: `aws_apigatewayv2_*`)

hashicorp/aws 6.x · Terraform ~> 1.16 · Per-source read dates: see the bibliography in unverified-and-risks.md. HTTP and WebSocket APIs use the Version 2
resources; REST APIs use `aws_api_gateway_*` (see [always-do-rest-core](./always-do-rest-core.md)). Do not
carry arguments across families. Blocks referencing resources defined elsewhere are fragments;
`# example` / `# placeholder` values are not from the docs.

## 11. API, Integration and Route

`protocol_type` is `HTTP` or `WEBSOCKET`. `route_selection_expression` defaults to
`$request.method $request.path`; `ip_address_type` defaults to `ipv4`. Quick-create `target`/`route_key`/
`credentials_arn` are HTTP only. With `body`, do not manage integrations or routes as separate resources.

Integration: `integration_type` is `AWS_PROXY` or `HTTP_PROXY` (`AWS`/`HTTP`/`MOCK` are WebSocket only;
`HTTP_PROXY` is used for HTTP private integrations). `payload_format_version` defaults to `1.0` (`2.0`
allowed). `timeout_milliseconds` is 50-30000 for HTTP (default 30 s) and 50-29000 for WebSocket (default
29 s). Route: `route_key` is `$default` or `GET /pets`; `authorization_type` defaults to `NONE`
(HTTP: NONE|JWT|AWS_IAM|CUSTOM; WebSocket: NONE|AWS_IAM|CUSTOM); `target = "integrations/<id>"`.
APIGateway.8 checks that routes specify an authorization type (`AWS_IAM`, `CUSTOM` or `JWT`).

```hcl
# Fragment — remaining integration arguments (target URI etc.) are on the integration page
resource "aws_apigatewayv2_api" "http" {
  name          = "example-http-api" # example
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "example" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000 # HTTP maximum
}

resource "aws_apigatewayv2_route" "get_pets" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "GET /pets" # example
  authorization_type = "AWS_IAM"
  target             = "integrations/${aws_apigatewayv2_integration.example.id}"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_integration.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_route.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html
```

Private integration over a VPC link: `connection_type = "VPC_LINK"` with `connection_id`;
`tls_config.server_name_to_verify` applies to HTTP private integrations. APIGateway.10 checks that V2
integrations use HTTPS for private connections (the integration page does not say an https URI is
required, and how HTTPS is configured here is (medium confidence)). AWS lists NLB and ALB private integrations for both REST
and HTTP APIs (https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html).

```hcl
# Fragment — VPC link is in always-do-http-domain-access.md; no https URI is shown (not stated on the page)
resource "aws_apigatewayv2_integration" "private" {
  api_id           = aws_apigatewayv2_api.http.id
  integration_type = "HTTP_PROXY"
  connection_type  = "VPC_LINK"
  connection_id    = aws_apigatewayv2_vpc_link.example.id

  tls_config {
    server_name_to_verify = "backend.example.internal" # example
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_integration.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html
```

## 12. Stage, Authorizer and Deployment

Stage: `auto_deploy` defaults to `false` (HTTP); AWS says HTTP APIs support automatic deployments and REST
APIs do not (https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html).
`access_log_settings.destination_arn` has a trailing `:*` trimmed. `logging_level` (default `OFF`) and
`data_trace_enabled` (default `false`) are WebSocket only, as is `client_certificate_id`.
APIGateway.9 checks access logging on V2 stages; APIGateway.1 checks `loggingLevel` ERROR or INFO on
WebSocket stages.

```hcl
# Fragment — destination and format are placeholders
resource "aws_apigatewayv2_stage" "http" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "example" # example
  auto_deploy = true

  access_log_settings {
    destination_arn = var.access_log_destination_arn # placeholder
    format          = var.access_log_format          # placeholder
  }

  default_route_settings {
    detailed_metrics_enabled = true
  }
}

resource "aws_apigatewayv2_api" "ws" {
  name          = "example-ws-api" # example
  protocol_type = "WEBSOCKET"
}

resource "aws_apigatewayv2_stage" "ws" {
  api_id = aws_apigatewayv2_api.ws.id
  name   = "example" # example

  default_route_settings {
    logging_level      = "ERROR" # WebSocket only; OFF default
    data_trace_enabled = false   # WebSocket only
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_stage.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html
```

Authorizer (`authorizer_type` is `JWT` or `REQUEST`). JWT needs `jwt_configuration { audience, issuer }`
(HTTP only) and a single `identity_sources` entry. REQUEST uses `authorizer_uri` and
`authorizer_credentials_arn`; HTTP Lambda authorizers require `authorizer_payload_format_version`;
`authorizer_result_ttl_in_seconds` defaults to 300 (max 3600, 0 disables; HTTP only).

```hcl
# Fragment — issuer, audience and identity source are placeholders (Cognito: provisioning-aws-cognito-v6)
resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.http.id
  authorizer_type  = "JWT"
  name             = "example-jwt" # example
  identity_sources = [var.identity_source] # placeholder; single entry

  jwt_configuration {
    audience = var.jwt_audience # placeholder
    issuer   = var.jwt_issuer   # placeholder
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_authorizer.html.markdown
```

Deployment: needs at least one route; use `triggers` references or `depends_on` to avoid races; enable
`create_before_destroy`. With `auto_deploy = true` on the stage no explicit deployment is needed.

```hcl
# Fragment — route from §11
resource "aws_apigatewayv2_deployment" "example" {
  api_id = aws_apigatewayv2_api.http.id

  triggers = {
    redeployment = sha1(jsonencode([aws_apigatewayv2_route.get_pets.id])) # example reference list
  }

  lifecycle {
    create_before_destroy = true
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_deployment.html.markdown
```
