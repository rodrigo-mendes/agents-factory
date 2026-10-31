# Always-Do — REST API core (v1: `aws_api_gateway_*`)

hashicorp/aws 6.x · Terraform ~> 1.16 · Per-source read dates: see the bibliography in unverified-and-risks.md. REST APIs use the Version 1 resources
(`aws_api_gateway_*`); HTTP and WebSocket APIs use `aws_apigatewayv2_*` — see
[always-do-http-websocket](./always-do-http-websocket.md). Never mix arguments between the two families.
Values marked `# example` or `# placeholder` are not from the provider docs. Blocks that reference
resources defined elsewhere are fragments.

## 1. Terraform Block and S3 Backend

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
  backend "s3" {
    bucket       = "example-tf-state"          # example
    key          = "api-gateway/terraform.tfstate" # example
    region       = "eu-west-1"                 # example
    use_lockfile = true
    encrypt      = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```

Every API Gateway resource accepts an optional `region` (default: provider region; changing it forces
replacement). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

## 2. REST API

`endpoint_configuration.types` defaults to `EDGE` if unspecified. With `body`, the OpenAPI spec
configures resources, methods and integrations. The provider recommends `aws_api_gateway_rest_api_policy`
over the `policy` argument.

```hcl
# Fragment — policy JSON is defined elsewhere (see provisioning-aws-iam-v6)
resource "aws_api_gateway_rest_api" "example" {
  name = "example-api" # example

  endpoint_configuration {
    types = ["REGIONAL"] # example; EDGE | REGIONAL | PRIVATE
  }
}

resource "aws_api_gateway_rest_api_policy" "example" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  policy      = var.api_policy_json # placeholder: JSON resource policy
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api_policy.html.markdown
```

OpenAPI-driven variant (the spec replaces existing methods, resources, integrations and endpoints by
default):

```hcl
# Fragment — spec file is defined elsewhere
resource "aws_api_gateway_rest_api" "from_spec" {
  name = "example-spec-api"            # example
  body = file("${path.module}/openapi.json") # example path
  # put_rest_api_mode: merge | overwrite (default overwrite); fail_on_warnings default false
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api.html.markdown
```

`aws_api_gateway_rest_api_put` exists (required `body` up to 6 MB, `rest_api_id`; optional
`fail_on_warnings`, `parameters`, `triggers`): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api_put.html.markdown

## 3. Resource, Method and Integration

```hcl
# Fragment — parent_id, URI and HTTP method are placeholders
resource "aws_api_gateway_resource" "example" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  parent_id   = var.parent_resource_id # placeholder: parent resource ID
  path_part   = "pets"                 # example
}

resource "aws_api_gateway_method" "get" {
  rest_api_id   = aws_api_gateway_rest_api.example.id
  resource_id   = aws_api_gateway_resource.example.id
  http_method   = "GET"
  authorization = "AWS_IAM" # NONE | CUSTOM | AWS_IAM | COGNITO_USER_POOLS
}

resource "aws_api_gateway_integration" "get" {
  rest_api_id             = aws_api_gateway_rest_api.example.id
  resource_id             = aws_api_gateway_resource.example.id
  http_method             = aws_api_gateway_method.get.http_method
  type                    = "AWS_PROXY"                   # HTTP | MOCK | AWS | AWS_PROXY | HTTP_PROXY
  integration_http_method = var.integration_http_method   # placeholder; required for all but MOCK
  uri                     = var.integration_uri           # placeholder; required for all but MOCK
  timeout_milliseconds    = 29000                         # default; min 50
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_resource.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_integration.html.markdown
```

Private integrations (provider integration page): `connection_type` is `INTERNET` (default) or `VPC_LINK`;
`connection_id` is the ID of the VpcLink, required if `connection_type` is `VPC_LINK`; `integration_target`
is "ALB or NLB ARN to send the request to. Used for private integrations with VPC Link V2"; the page's
VPC Link V2 example pairs `aws_api_gateway_rest_api` with `aws_apigatewayv2_vpc_link`. `tls_config` is
"Supported only for HTTP and HTTP_PROXY integrations". AWS lists NLB and ALB private integrations for both
REST and HTTP APIs
(https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html).

Integration timeout, AWS quota page: 50 ms to 29 s for Regional, edge-optimized and private APIs; Regional
and private can be raised above 29 s, "but this might require a reduction in your Region-level throttle
quota"
(https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html).
Provider page: `timeout_milliseconds` max 300000 (`BUFFERED`) / 900000 (`STREAM`). The two pages are not
reconciled here.
