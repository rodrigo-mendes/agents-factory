---
name: provisioning-aws-api-gateway-v6
description: "API Gateway Terraform (aws 6.x): REST (aws_api_gateway_*) and HTTP/WebSocket (aws_apigatewayv2_*) APIs. Use when writing HCL for API Gateway. Not for Lambda, WAF, ACM, Cognito, SAM."
---

# Provisioning AWS API Gateway with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = the **6.x major line**; reference patch 6.69.0/6.70.0 (latest 6.70.0), Terraform
> **~> 1.16**. Research date **2026-10-23**. Claims tagged (unverified) or (medium confidence) were not fully
> confirmed against an official page. A new major (v7) is a new skill.

Two resource families, never mixed: **REST (v1)** = `aws_api_gateway_*`; **HTTP and WebSocket (v2)** =
`aws_apigatewayv2_*`.

## Version Context

| Item | Value | Source (read date) |
|---|---|---|
| Terraform CLI | `~> 1.16` (1.16.7, 2026-10-22, newest 1.16.x) | https://releases.hashicorp.com/terraform/ (2026-10-23) |
| hashicorp/aws | latest 6.70.0; constraint `~> 6.69`; no 7.x released | https://releases.hashicorp.com/terraform-provider-aws/ (2026-10-23) |
| Withdrawn | 6.57.0 — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md (2026-10-23) |
| `region` | optional on every resource; default provider region; change forces replacement | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown (2026-10-23) |
| Identity import | `identity` block needs Terraform >= 1.12 (documented on several REST and v2 resources) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api.html.markdown (2026-10-23) |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable since 2026-10-21 and is not the target of this skill: https://releases.hashicorp.com/terraform/ (2026-10-23); https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (2026-10-23).
- 6.57.0 is withdrawn; v7 is planned (upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails) · [Quick Reference](#quick-reference)
- REST (v1): [core](./blueprints/always-do-rest-core.md) · [deployment, stage, logs](./blueprints/always-do-rest-deployment.md) · [authorizers, keys, domains](./blueprints/always-do-rest-auth-domain.md)
- HTTP/WebSocket (v2): [API, integration, route, stage](./blueprints/always-do-http-websocket.md) · [domain, VPC link, Lambda permission](./blueprints/always-do-http-domain-access.md)
- Never-do: [provider migration](./blueprints/never-do-provider-migration.md) · [REST](./blueprints/never-do-rest.md) · [HTTP/WebSocket](./blueprints/never-do-http-websocket.md)
- [Always-do index](./blueprints/always-do-patterns.md) · [Never-do index](./blueprints/never-do-patterns.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md) · [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

Both families
- **Constrain the provider with `~>` in root modules** (this skill uses `~> 6.69`): https://developer.hashicorp.com/terraform/language/expressions/version-constraints — [rest-core §1](./blueprints/always-do-rest-core.md#1-terraform-block-and-s3-backend)
- **Constrain `required_version` with `~>`** (this skill uses `~> 1.16`): https://developer.hashicorp.com/terraform/language/expressions/version-constraints — [rest-core §1](./blueprints/always-do-rest-core.md#1-terraform-block-and-s3-backend)
- **Set `use_lockfile = true` on the S3 backend**: https://developer.hashicorp.com/terraform/language/backend/s3 — [rest-core §1](./blueprints/always-do-rest-core.md#1-terraform-block-and-s3-backend)
- **Use `aws_api_gateway_*` for REST APIs and `aws_apigatewayv2_*` for WebSocket and HTTP APIs**: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api.html.markdown — [index](./blueprints/always-do-patterns.md)

REST (v1) — `aws_api_gateway_*`
- **Create stages with `aws_api_gateway_stage`**: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — [deployment §5](./blueprints/always-do-rest-deployment.md#5-stage-access-logs-and-execution-log-group)
- **Set `triggers` on `aws_api_gateway_deployment`**; the page says it should be preferred over `depends_on`: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_deployment.html.markdown — [deployment §4](./blueprints/always-do-rest-deployment.md#4-deployment-and-redeployment)
- **Enable `lifecycle { create_before_destroy = true }` on the deployment** to order redeployments: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_deployment.html.markdown — [deployment §4](./blueprints/always-do-rest-deployment.md#4-deployment-and-redeployment)
- **Redeploy after every API update** other than stage settings: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-deploy-api.html — [deployment §4](./blueprints/always-do-rest-deployment.md#4-deployment-and-redeployment)
- **Use `aws_api_gateway_method_settings` with `aws_api_gateway_stage`**: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method_settings.html.markdown — [deployment §6](./blueprints/always-do-rest-deployment.md#6-method-settings)
- **Strip the leading `/` from `method_path`**: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method_settings.html.markdown — [deployment §6](./blueprints/always-do-rest-deployment.md#6-method-settings)
- **Manage the execution-log group in Terraform and make the stage `depends_on` it**, to avoid ordering issues with API Gateway creating the group first: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_stage.html.markdown — [deployment §5](./blueprints/always-do-rest-deployment.md#5-stage-access-logs-and-execution-log-group)
- **Configure access logs through `access_log_settings`** (`destination_arn`, `format`): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_stage.html.markdown — [deployment §5](./blueprints/always-do-rest-deployment.md#5-stage-access-logs-and-execution-log-group)
- **Treat access logs as separate from the execution-log group**: the page's `API-Gateway-Execution-Logs_...` name is for execution logs, and access logs can go to any log group: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_stage.html.markdown — [deployment §5](./blueprints/always-do-rest-deployment.md#5-stage-access-logs-and-execution-log-group)
- **Set `logging_level` to `ERROR` or `INFO`**; APIGateway.1 checks it: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html — [deployment §6](./blueprints/always-do-rest-deployment.md#6-method-settings)
- **Configure `aws_api_gateway_account` once per account and Region**: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_account.html.markdown — [deployment §7](./blueprints/always-do-rest-deployment.md#7-account-cloudwatch-role)
- **Set `xray_tracing_enabled = true` on REST stages**; APIGateway.3 checks X-Ray tracing: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html — [deployment §5](./blueprints/always-do-rest-deployment.md#5-stage-access-logs-and-execution-log-group)
- **Set `cache_data_encrypted = true` when caching**; APIGateway.5 checks it: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html — [deployment §6](./blueprints/always-do-rest-deployment.md#6-method-settings)
- **Use `aws_api_gateway_rest_api_policy`** rather than the `policy` argument; the provider recommends it: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api.html.markdown — [core §2](./blueprints/always-do-rest-core.md#2-rest-api)
- **Depend custom domains on `aws_acm_certificate_validation`**; the page expects ACM certificates: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_domain_name.html.markdown — [auth-domain §10](./blueprints/always-do-rest-auth-domain.md#10-custom-domain-and-base-path-mapping)

HTTP and WebSocket (v2) — `aws_apigatewayv2_*`
- **Set `authorization_type` on every v2 route**; APIGateway.8 checks for `AWS_IAM`, `CUSTOM` or `JWT`: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html — [http §11](./blueprints/always-do-http-websocket.md#11-api-integration-and-route)
- **Configure `access_log_settings` on v2 stages**; APIGateway.9 checks it: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html — [http §12](./blueprints/always-do-http-websocket.md#12-stage-authorizer-and-deployment)
- **Use `auto_deploy = true` on an HTTP stage instead of an explicit deployment**; AWS says HTTP APIs support automatic deployments: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html — [http §12](./blueprints/always-do-http-websocket.md#12-stage-authorizer-and-deployment)

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| REST vs HTTP API | AWS: "Choose REST APIs if you need features such as API keys, per-client throttling, request validation, AWS WAF integration, or private API endpoints. Choose HTTP APIs if you don't need the features included with REST APIs." HTTP-only: JWT authorizer, automatic deployments, Cloud Map private integrations. ([source](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)) | "Do you need REST-only features (API keys, WAF, private endpoints, caching, canary) or is an HTTP API enough?" |
| Endpoint type | `endpoint_configuration.types` is `EDGE`, `REGIONAL` or `PRIVATE`; EDGE if unspecified; `vpc_endpoint_ids` only for PRIVATE. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api.html.markdown)) | "Edge-optimized, Regional or private?" |
| OpenAPI `body` | With `body` the spec replaces existing methods, resources, integrations and endpoints by default (`put_rest_api_mode` default `overwrite`); `aws_api_gateway_rest_api_put` also exists. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api.html.markdown)) | "Is the API defined by an OpenAPI spec or by separate resources?" |
| Deployment `triggers` contents | The hash-of-references pattern is documented; the exact reference list in the provider example is (medium confidence). | "Which components (resources, methods, integrations, authorizers, policy) should force a redeployment?" |
| Integration timeout | AWS quota page: 50 ms-29 s for Regional, edge and private; Regional and private can be raised above 29 s, "but this might require a reduction in your Region-level throttle quota" ([source](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html)). The provider page documents `timeout_milliseconds` max 300000 (`BUFFERED`) / 900000 (`STREAM`) ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_integration.html.markdown)); the two pages are not reconciled. | "Is a timeout above 29 s needed, for which endpoint type, and may the Region throttle quota be reduced?" |
| Account throttle quota | Per Region across HTTP, REST, WebSocket and callback APIs: 10,000 RPS, burst 5,000; 13 Regions (Cape Town, Milan, Jakarta, UAE, Hyderabad, Melbourne, Spain, Zurich, Tel Aviv, Calgary, Malaysia, Thailand, Mexico (Central)) default to 2,500 RPS, burst 1,250. ([source](https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html)) | "Which Region, and does the expected load fit the default quota?" |
| `aws_api_gateway_account` removal | Destroy always resets account settings since 6.0; a `removed` block keeps the old behaviour. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | "Should account settings be kept when this resource is removed?" |
| HTTP API `source_arn` for Lambda | The REST example is `execution_arn/*`; the exact path layout for HTTP API routes is (medium confidence). | "Allow any stage/route, or narrow the permission?" |
| REST `method_settings` defaults | The page states no default for `logging_level`, `metrics_enabled`, `data_trace_enabled` (medium confidence). | "Which logging and metrics values should be set explicitly?" |
| Edge custom-domain certificate Region | Not stated on the provider page (unverified). | "Confirm the Region of the ACM certificate for the edge-optimized domain." |
| Private integration (REST) | `integration_target` is "ALB or NLB ARN to send the request to. Used for private integrations with VPC Link V2"; `connection_id` is the ID of the VpcLink, required if `connection_type` is `VPC_LINK`; the page's VPC Link V2 example pairs `aws_api_gateway_rest_api` with `aws_apigatewayv2_vpc_link`. `tls_config` is supported only for `HTTP` and `HTTP_PROXY`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_integration.html.markdown)) | "Which load balancer and which VPC link?" |
| Private integration (v2) HTTPS | APIGateway.10 checks that V2 integrations use HTTPS for private connections; `tls_config.server_name_to_verify` applies to HTTP private integrations; the integration page does not say an https URI is required (medium confidence). ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html); [integration page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_integration.html.markdown)) | "Confirm how HTTPS is configured for the private integration." |
| `authorizer_id` and scopes (REST method) | `authorizer_id` applies to `CUSTOM` / `COGNITO_USER_POOLS`; `authorization_scopes` to `COGNITO_USER_POOLS`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method.html.markdown)) | "Which authorization type does this method use?" |
| Coverage gaps | Not researched in depth, no HCL here: `aws_api_gateway_method_response`, `_integration_response`, `_vpc_link`, `_request_validator`, `_gateway_response`, `_client_certificate`, `_domain_name_access_association`, `aws_apigatewayv2_routing_rule`. | "Read the provider page first — proceed?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `stage_name`, `stage_description`, `canary_settings` on `aws_api_gateway_deployment`, or read its `invoke_url` / `execution_arn` — removed in 6.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | Declare `aws_api_gateway_stage`; import with `terraform import aws_api_gateway_stage.prod rest_api_id/stage_name` |
| Set `reset_on_delete` on `aws_api_gateway_account` — removed in 6.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | Drop it; use a `removed` block to keep settings |
| Use `dynamodb_table` in the S3 backend — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |
| Pin `version = "6.57.0"` — withdrawn. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` ([constraints page](https://developer.hashicorp.com/terraform/language/expressions/version-constraints)) |
| Set both `certificate_arn` and `regional_certificate_arn` on `aws_api_gateway_domain_name` — they conflict. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_domain_name.html.markdown)) | `certificate_arn` for edge or `regional_certificate_arn` for regional |
| Remove `response_transfer_mode` to revert to buffering. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_integration.html.markdown)) | Write `response_transfer_mode = "BUFFERED"` explicitly |
| Use API keys for authentication or authorization; a key valid for one API in a plan accesses all APIs in that plan. ([source](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html)) | Set `authorization` on the method to `CUSTOM`, `AWS_IAM` or `COGNITO_USER_POOLS` ([method page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method.html.markdown)) |
| Rely on usage-plan throttling or quotas to control costs or block access — best-effort. ([source](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html)) | AWS Budgets for cost, AWS WAF (`provisioning-aws-waf-v6`) for blocking |
| Manage routes or integrations as separate resources on an `aws_apigatewayv2_api` that has `body`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api.html.markdown)) | Define them in the spec, or omit `body` |
| Set `logging_level` or `data_trace_enabled` on an HTTP API stage — WebSocket only. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_stage.html.markdown)) | Set them only on WebSocket stages |
| Use `authorization_type = "JWT"` on a WebSocket route. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_route.html.markdown)) | `NONE`, `AWS_IAM` or `CUSTOM` |
| Use `AWS`, `HTTP` or `MOCK` `integration_type` on an HTTP API — WebSocket only. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_integration.html.markdown)) | `AWS_PROXY` or `HTTP_PROXY` |
| Set v2 `timeout_milliseconds` outside 50-30000 (HTTP) or 50-29000 (WebSocket). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_integration.html.markdown)) | Stay in the protocol range |
| Build HTTP or WebSocket APIs from `aws_api_gateway_*` resources. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api.html.markdown)) | `aws_apigatewayv2_*` resources |

## Quick Reference

Provider and AWS pages read 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| REST endpoint default | `EDGE` if `types` unspecified | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api.html.markdown |
| REST `put_rest_api_mode` | `merge` or `overwrite`; default `overwrite` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api.html.markdown |
| REST integration timeout | min 50, default 29000; max 300000 (`BUFFERED`) / 900000 (`STREAM`) on the provider page | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_integration.html.markdown |
| REST stage `xray_tracing_enabled` | default `false` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_stage.html.markdown |
| Method settings throttling | `-1` default = throttling disabled | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method_settings.html.markdown |
| Authorizer defaults | `type` `TOKEN`; `authorizer_result_ttl_in_seconds` 300 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_authorizer.html.markdown |
| v2 route `authorization_type` | default `NONE` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_route.html.markdown |
| v2 integration | `payload_format_version` default `1.0`; `connection_type` default `INTERNET` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_integration.html.markdown |
| v2 stage | `auto_deploy` default `false` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_stage.html.markdown |
| v2 authorizer TTL | default 300, max 3600, 0 disables (HTTP only) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_authorizer.html.markdown |
| `CreateDeployment` quota | 1 request per 5 s per account, not increasable | https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html |
| Throttle order | usage plan per-client/per-method, stage per-method, account per Region, AWS Regional; excess returns `429` | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html |
| HTTP API quotas | 300 routes; 300 integrations; max integration timeout 30 s; 10 MB payload | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html |
| WebSocket quotas | 500 new connections/s per account/Region; 2 h connection; 10 min idle; 32 KB frame; 128 KB message | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html |
| REST quotas | 300 resources/API; 10 stages/API; 10 authorizers/API; 10 MB payload; OpenAPI import/put 6 MB | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html |
| Security Hub controls | APIGateway.1-5 and 8-11 (see below) | https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html |
| APIGateway.1 | REST and WebSocket execution logging (`loggingLevel` ERROR or INFO) | https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html |
| APIGateway.2 | REST stages use SSL certificates for backend authentication (`client_certificate_id`) | https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html |
| APIGateway.3 | REST stages have X-Ray tracing | https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html |
| APIGateway.4 | REST stage associated with a WAF web ACL (`aws_wafv2_web_acl_association`, WAF skill) | https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html |
| APIGateway.5 | REST cache data encrypted at rest | https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html |
| APIGateway.8-11 | v2 routes specify an authorization type; v2 stages have access logging; v2 private integrations use HTTPS; domains use recommended security policies | https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html |

## 5.x → 6.x Migration (API Gateway)

Breaking changes in 6.0.0 that affect API Gateway
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-23):

- **`aws_api_gateway_account`**: `reset_on_delete` removed; destroy now always resets the account settings;
  use a `removed` block to keep the old (keep-settings) behaviour.
- **`aws_api_gateway_deployment`**: `stage_name`, `stage_description`, `canary_settings` removed → use
  `aws_api_gateway_stage`; `invoke_url` and `execution_arn` removed from the deployment. Migration: declare
  `aws_api_gateway_stage` and `terraform import aws_api_gateway_stage.prod rest_api_id/stage_name`.
- No `aws_apigatewayv2_*` entries were seen in the upgrade guide (medium confidence, absence of evidence).

No API Gateway breaking changes were seen in the CHANGELOG 6.48.0 → 6.70.0 (medium confidence, absence of
evidence)
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)); notable
additions: `security_policy` and `endpoint_access_mode` on `aws_api_gateway_rest_api` (6.53.0), configurable
REST API timeouts (6.58.0), list resources for `aws_api_gateway_deployment` and `aws_apigatewayv2_integration`
(6.65.0), a `Read` fix on `aws_api_gateway_method` (6.69.0). Part of the 6.55.0 entries was not visible
(medium confidence, absence of evidence; see [coverage limits](./blueprints/unverified-and-risks.md#coverage-limits)).

Upgrade path, per the 6.0 upgrade guide
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)):
"Before upgrading to version `6.0.0`, first upgrade to the latest available `5.x` version of the provider."
Run a plan that completes "without errors or unexpected changes", update the version constraints to allow
the `6.x` series, then run `terraform init -upgrade` "to download the new version". This skill uses `~> 6.69`.

## External Resources

Read dates in parentheses.

- Provider CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md (2026-10-23)
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown (2026-10-23)
- Deployment (AWS): https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-deploy-api.html (2026-10-23)
- REST vs HTTP APIs: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (2026-10-23)
- Quotas: https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html (2026-10-23)
- Security Hub API Gateway controls: https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html (2026-10-23)
- Security best practices: https://docs.aws.amazon.com/apigateway/latest/developerguide/security-best-practices.html (2026-10-23)
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3 (2026-10-23)
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
