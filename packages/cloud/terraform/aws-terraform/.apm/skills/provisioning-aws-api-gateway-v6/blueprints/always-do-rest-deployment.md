# Always-Do — REST deployment, stage, logging, account

hashicorp/aws 6.x · Terraform ~> 1.16 · Per-source read dates: see the bibliography in unverified-and-risks.md. REST (v1) only. Blocks referencing
resources defined in other sections are fragments; `# example` / `# placeholder` values are not from the docs.

## 4. Deployment and Redeployment

AWS: "Every time you update an API, you must redeploy the API to an existing stage or to a new stage.
Updating an API includes modifying routes, methods, integrations, authorizers, resource policies, and
anything else other than stage settings."
(https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-deploy-api.html)

The deployment page says `triggers` (a map; a change causes redeployment; force with `-replace`) "should be
preferred over `depends_on`", because `depends_on` only orders and does not redeploy on upstream changes.
Enable `create_before_destroy` "to properly order redeployments"; without it, recreation can fail with
`BadRequestException: Active stages pointing to this deployment must be moved or deleted`.

```hcl
# Fragment — the referenced resources are defined in always-do-rest-core.md
resource "aws_api_gateway_deployment" "example" {
  rest_api_id = aws_api_gateway_rest_api.example.id

  triggers = {
    # hash-of-references form; the exact reference list is (medium confidence) — see unverified-and-risks.md
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.example.id,
      aws_api_gateway_method.get.id,
      aws_api_gateway_integration.get.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_deployment.html.markdown
```

Staleness pitfall: a method, integration, authorizer or policy change that is not reflected in `triggers`
leaves the stage on the old snapshot while the plan is clean. `triggers` and `variables` cannot be
imported. For `body`-only APIs, referencing the REST API `id` is enough unless other resources customize
the API. `CreateDeployment` is limited to 1 request per 5 s per account and cannot be increased
(https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html).

## 5. Stage, Access Logs and Execution-Log Group

`stage_name` is a stage argument; `xray_tracing_enabled` defaults to `false`. The provider example manages
the execution-log group `API-Gateway-Execution-Logs_${rest_api_id}/${stage_name}` with `depends_on` on
the stage, "to prevent ordering issues with API Gateway automatically creating the log group first";
import the group once if it already exists. Access logs use `access_log_settings`; access logs can go to any log
group.

```hcl
# Fragment — deployment from §4; destination and format are placeholders
resource "aws_api_gateway_stage" "example" {
  rest_api_id   = aws_api_gateway_rest_api.example.id
  deployment_id = aws_api_gateway_deployment.example.id
  stage_name    = "example" # example

  xray_tracing_enabled  = true                         # APIGateway.3 checks X-Ray tracing
  client_certificate_id = var.client_certificate_id    # placeholder; APIGateway.2 checks backend SSL certificate
  cache_cluster_enabled = true                         # example, only when caching
  cache_cluster_size    = "0.5"                        # example; 0.5 ... 237

  access_log_settings {
    destination_arn = var.access_log_destination_arn   # placeholder; log group: see provisioning-aws-cloudwatch-v6
    format          = var.access_log_format            # placeholder
  }

  depends_on = [aws_cloudwatch_log_group.execution]
}

resource "aws_cloudwatch_log_group" "execution" {
  name = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.example.id}/example" # example stage name
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_stage.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html
```

`canary_settings { deployment_id, percent_traffic, stage_variable_overrides, use_stage_cache }` is now on
the stage (removed from the deployment in 6.0).

## 6. Method Settings

Use `aws_api_gateway_method_settings` with `aws_api_gateway_stage`. `method_path` is `*/*` or
`{resource_path}/{METHOD}` with the leading `/` stripped (for example `trimprefix(path, "/")`).
`throttling_burst_limit` / `throttling_rate_limit` default to `-1` (throttling disabled);
`caching_enabled` needs a stage cache cluster.

```hcl
# Fragment — stage from §5
resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  stage_name  = aws_api_gateway_stage.example.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled      = true
    logging_level        = "ERROR" # OFF | ERROR | INFO; APIGateway.1 checks ERROR or INFO
    caching_enabled      = true    # example, only with a cache cluster
    cache_data_encrypted = true    # APIGateway.5 checks cache data encrypted at rest
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method_settings.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html
```

The provider page states no default for `logging_level`, `metrics_enabled` or `data_trace_enabled`
(medium confidence; see unverified-and-risks.md, medium-confidence items).

## 7. Account (CloudWatch role)

Settings are "applied region-wide per `provider` block" (one per account and Region). Execution logging
(APIGateway.1) needs it; per the account page the role must trust `apigateway.amazonaws.com`; role and
policy belong to the IAM skill (`provisioning-aws-iam-v6`). `reset_on_delete` was removed in 6.0.

```hcl
# Fragment — role is defined elsewhere
resource "aws_api_gateway_account" "this" {
  cloudwatch_role_arn = var.cloudwatch_role_arn # placeholder
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_account.html.markdown
```
