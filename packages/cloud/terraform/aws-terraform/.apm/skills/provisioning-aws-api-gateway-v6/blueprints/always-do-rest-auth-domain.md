# Always-Do — REST authorizers, usage plans, custom domains

hashicorp/aws 6.x · Terraform ~> 1.16 · Per-source read dates: see the bibliography in unverified-and-risks.md. REST (v1) only. Blocks referencing
resources defined elsewhere are fragments; `# example` / `# placeholder` values are not from the docs.

## 8. Authorizer

`type` defaults to `TOKEN` (`REQUEST`, `COGNITO_USER_POOLS`); `authorizer_uri` is required for
TOKEN/REQUEST; `provider_arns` is required for COGNITO_USER_POOLS (user pool: `provisioning-aws-cognito-v6`;
Lambda: `provisioning-aws-lambda-v6`). `identity_source` defaults to `method.request.header.Authorization`;
`authorizer_result_ttl_in_seconds` defaults to `300`. On the method, `authorizer_id` applies to
`CUSTOM`/`COGNITO_USER_POOLS` only and `authorization_scopes` to `COGNITO_USER_POOLS` only.

```hcl
# Fragment — REST API, resource and integration defined in always-do-rest-core.md
resource "aws_api_gateway_authorizer" "example" {
  name           = "example-authorizer"      # example
  rest_api_id    = aws_api_gateway_rest_api.example.id
  type           = "TOKEN"                   # default
  authorizer_uri = var.authorizer_uri        # placeholder
}

resource "aws_api_gateway_method" "protected" {
  rest_api_id   = aws_api_gateway_rest_api.example.id
  resource_id   = aws_api_gateway_resource.example.id
  http_method   = "POST"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.example.id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_authorizer.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method.html.markdown
```

## 9. API Keys and Usage Plans

AWS: "Don't use API keys for authentication or authorization". A key valid for one API in a plan accesses
all APIs in that plan. Usage-plan throttling and quotas are best-effort; AWS says not to rely on them to
control costs or block access (use Budgets or WAF — `provisioning-aws-waf-v6`).
Usage plans are required to associate keys with stages.
(https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html)

```hcl
# Fragment — stage defined in always-do-rest-deployment.md
resource "aws_api_gateway_api_key" "example" {
  name = "example-key" # example; enabled defaults to true
}

resource "aws_api_gateway_usage_plan" "example" {
  name = "example-plan" # example

  api_stages {
    api_id = aws_api_gateway_rest_api.example.id
    stage  = aws_api_gateway_stage.example.stage_name
  }

  quota_settings {
    limit  = 1000  # example
    period = "DAY" # DAY | WEEK | MONTH
  }
}

resource "aws_api_gateway_usage_plan_key" "example" {
  key_id        = aws_api_gateway_api_key.example.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.example.id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_api_key.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_usage_plan.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_usage_plan_key.html.markdown
```

## 10. Custom Domain and Base Path Mapping

`certificate_arn` (edge) and `regional_certificate_arn` (regional) conflict with each other. ACM
certificates are required; the page expects a dependency on `aws_acm_certificate_validation`
(`provisioning-aws-acm-v6`). All arguments, including the private key, are stored in state in plain text.
`endpoint_access_mode` (`BASIC`|`STRICT`) is required when `security_policy` starts with `SecurityPolicy_`.
APIGateway.11 lists the recommended policies: `SecurityPolicy_TLS13_1_3_2025_09`, the `..._FIPS_2025_09`
and `..._1_2_PFS_PQ_2025_09` variants (full names on the control page), `SecurityPolicy_TLS13_2025_EDGE`
and `SecurityPolicy_TLS12_PFS_2025_EDGE`; the control FAILs for HTTP API domains (suppress if legitimate).
DNS records: `provisioning-aws-route53-v6`.

```hcl
# Fragment — domain name, ACM validation and stage are defined elsewhere
resource "aws_api_gateway_domain_name" "example" {
  domain_name              = var.domain_name                 # placeholder
  regional_certificate_arn = var.regional_certificate_arn    # placeholder: ACM certificate
  security_policy          = "SecurityPolicy_TLS13_1_3_2025_09" # APIGateway.11 list
  endpoint_access_mode     = "BASIC"                         # example

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  depends_on = [aws_acm_certificate_validation.example] # defined in the ACM skill
}

resource "aws_api_gateway_base_path_mapping" "example" {
  api_id      = aws_api_gateway_rest_api.example.id
  domain_name = aws_api_gateway_domain_name.example.domain_name
  stage_name  = aws_api_gateway_stage.example.stage_name
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_domain_name.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_base_path_mapping.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html
```

Also on the domain page: `mutual_tls_authentication { truststore_uri, truststore_version }`,
`ownership_verification_certificate_arn`, `policy` (private custom domains only) and `routing_mode`
(`BASE_PATH_MAPPING_ONLY` | `ROUTING_RULE_ONLY` | `ROUTING_RULE_THEN_BASE_PATH_MAPPING`). Whether an
edge-optimized domain certificate must be in `us-east-1` is not stated on the provider page
(unverified).
