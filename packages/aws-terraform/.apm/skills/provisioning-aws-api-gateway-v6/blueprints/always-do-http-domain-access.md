# Always-Do — HTTP API domains, VPC link, Lambda invoke permission

hashicorp/aws 6.x · Terraform ~> 1.16 · Per-source read dates: see the bibliography in unverified-and-risks.md. v2 resources (`aws_apigatewayv2_*`) plus
the cross-reference to the Lambda permission. Blocks referencing resources defined elsewhere are
fragments; `# example` / `# placeholder` values are not from the docs.

## 13. Custom Domain, API Mapping and VPC Link (v2)

`aws_apigatewayv2_domain_name`: `domain_name_configuration` takes `certificate_arn` (ACM only),
`endpoint_type = "REGIONAL"`, `security_policy = "TLS_1_2"`, `ip_address_type` (`ipv4` default |
`dualstack`) and `ownership_verification_certificate_arn`. `routing_mode` is `API_MAPPING_ONLY` |
`ROUTING_RULE_ONLY` | `ROUTING_RULE_THEN_API_MAPPING`. `aws_apigatewayv2_api_mapping` requires `api_id`,
`domain_name`, `stage`; `api_mapping_key` is optional. `aws_apigatewayv2_vpc_link` requires `name`,
`security_group_ids`, `subnet_ids` (see always-do-rest-core.md §3 for its use in REST private integrations).
Subnets and security groups: `provisioning-aws-vpc-v6`.

```hcl
# Fragment — certificate, subnets and security groups are defined elsewhere
resource "aws_apigatewayv2_domain_name" "example" {
  domain_name = var.domain_name # placeholder

  domain_name_configuration {
    certificate_arn = var.certificate_arn # placeholder: ACM certificate
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_apigatewayv2_api_mapping" "example" {
  api_id      = aws_apigatewayv2_api.http.id
  domain_name = aws_apigatewayv2_domain_name.example.domain_name
  stage       = aws_apigatewayv2_stage.http.name
}

resource "aws_apigatewayv2_vpc_link" "example" {
  name               = "example-vpc-link"       # example
  security_group_ids = var.security_group_ids   # placeholder
  subnet_ids         = var.subnet_ids           # placeholder
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_domain_name.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api_mapping.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_vpc_link.html.markdown
```

The APIGateway.11 control FAILs for HTTP API domains (suppress if legitimate)
(https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html).

## 14. Lambda Invoke Permission (owned by the Lambda skill)

The provider's `aws_lambda_permission` example uses `action = "lambda:InvokeFunction"`,
`principal = "apigateway.amazonaws.com"` and `source_arn = "${aws_api_gateway_rest_api.X.execution_arn}/*"`
("any stage, method and resource path"). Since 6.0 `execution_arn` comes from the REST API (or stage), not
the deployment. The exact `source_arn` path layout for HTTP API routes and for narrowing to
`/<stage>/<METHOD>/<path>` is (medium confidence) — see unverified-and-risks.md. Full Lambda
configuration: `provisioning-aws-lambda-v6`.

```hcl
# Fragment — the function is defined in the Lambda skill
resource "aws_lambda_permission" "apigw" {
  function_name = var.function_name # placeholder
  action        = "lambda:InvokeFunction"
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.example.execution_arn}/*" # REST example (v1 execution_arn); the v2 layout is (medium confidence)
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_permission.html.markdown
```

## 15. Coverage Notes (not researched in depth — no HCL)

Coverage limit — pages not researched in depth: `aws_api_gateway_method_response`, `aws_api_gateway_integration_response`,
`aws_api_gateway_vpc_link`, `aws_api_gateway_request_validator`, `aws_api_gateway_gateway_response`,
`aws_api_gateway_client_certificate`, `aws_api_gateway_domain_name_access_association`,
`aws_apigatewayv2_routing_rule`. Read the provider page for each before authoring them.
