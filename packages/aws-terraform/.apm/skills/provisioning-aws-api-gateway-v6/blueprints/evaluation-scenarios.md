# Evaluation Scenarios — provisioning-aws-api-gateway-v6

Five scenarios (canonical, edge, misuse rejection, anti-pattern trap, family separation). Each uses
`success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: REST API with stage and redeployment

```json
{
  "skills": ["provisioning-aws-api-gateway-v6"],
  "query": "Generate Terraform for a regional REST API with one GET method, an integration, a deployment, a stage with access logs and X-Ray, and method settings with logging. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Declares aws_api_gateway_stage separately from aws_api_gateway_deployment",
      "Sets triggers on the deployment and lifecycle { create_before_destroy = true }",
      "Uses access_log_settings (destination_arn, format) and manages the execution-log group separately",
      "Uses aws_api_gateway_method_settings with the stage resource and logging_level ERROR or INFO",
      "Sets xray_tracing_enabled = true on the stage",
      "Marks placeholder values (URI, destination ARN) as examples or placeholders"
    ],
    "must_not": [
      "Put stage_name, stage_description or canary_settings on aws_api_gateway_deployment",
      "Reference invoke_url or execution_arn on the deployment",
      "Use dynamodb_table in the S3 backend"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Account throttle quota and Regions

```json
{
  "skills": ["provisioning-aws-api-gateway-v6"],
  "query": "What is the default account-level throttle for API Gateway, and does it apply everywhere?",
  "success_criteria": {
    "must_pass": [
      "States 10,000 RPS with a 5,000 burst bucket per Region across HTTP, REST, WebSocket and callback APIs",
      "States that 13 Regions default to 2,500 RPS and 1,250 burst (Cape Town, Milan, Jakarta, UAE, Hyderabad, Melbourne, Spain, Zurich, Tel Aviv, Calgary, Malaysia, Thailand, Mexico (Central))",
      "Cites the AWS quotas page"
    ],
    "must_not": [
      "State 10,000 RPS as the default in every Region",
      "Present the quota as a Terraform-enforced rule"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: v1 resources for an HTTP API / v2 arguments on REST

```json
{
  "skills": ["provisioning-aws-api-gateway-v6"],
  "query": "Create an HTTP API with aws_api_gateway_rest_api, a JWT authorizer, and set logging_level on the stage.",
  "success_criteria": {
    "must_pass": [
      "Rejects aws_api_gateway_rest_api for an HTTP API and uses aws_apigatewayv2_api with protocol_type = \"HTTP\"",
      "Uses aws_apigatewayv2_authorizer with authorizer_type = \"JWT\" and jwt_configuration",
      "States that logging_level and data_trace_enabled are WebSocket only and recommends access_log_settings for the HTTP stage",
      "Keeps REST (aws_api_gateway_*) and v2 (aws_apigatewayv2_*) arguments separate"
    ],
    "must_not": [
      "Set logging_level on an HTTP API stage",
      "Mix aws_api_gateway_* arguments into aws_apigatewayv2_* resources"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: 6.0 removals and legacy claims

```json
{
  "skills": ["provisioning-aws-api-gateway-v6"],
  "query": "Review: aws_api_gateway_deployment with stage_name = \"prod\", aws_api_gateway_account with reset_on_delete = true, and a note that VPC links cannot use HTTPS and private integrations are NLB-only on REST.",
  "success_criteria": {
    "must_pass": [
      "Rejects stage_name on the deployment as removed in 6.0 and recommends aws_api_gateway_stage",
      "Rejects reset_on_delete as removed in 6.0 and mentions the removed block for keep-settings behaviour",
      "Corrects the NLB-only claim: AWS lists NLB and ALB private integrations for REST and HTTP APIs, and the REST integration page says integration_target takes an ALB or NLB ARN",
      "Does not assert that VPC links cannot use HTTPS: tls_config is documented for HTTP/HTTP_PROXY integrations and APIGateway.10 checks HTTPS for V2 private connections; how HTTPS is configured is (medium confidence)",
      "Cites the version 6 upgrade guide for the removals"
    ],
    "must_not": [
      "Accept stage_name or reset_on_delete as valid for 6.x"
    ]
  }
}
```

---

## Scenario 5 — Uncertain item: asks first

```json
{
  "skills": ["provisioning-aws-api-gateway-v6"],
  "query": "Create an edge-optimized REST custom domain with an ACM certificate. Which Region must the certificate be in?",
  "success_criteria": {
    "must_pass": [
      "States that the provider page does not state the certificate Region requirement and marks it (unverified)",
      "Asks the user to confirm the Region before choosing it",
      "Uses certificate_arn for edge and does not combine it with regional_certificate_arn",
      "Notes that the page expects a dependency on aws_acm_certificate_validation"
    ],
    "must_not": [
      "Assert us-east-1 as a verified requirement",
      "Set both certificate_arn and regional_certificate_arn"
    ]
  }
}
```
