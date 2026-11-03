# Research — AWS API Gateway (REST v1 + HTTP/WebSocket v2) with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `api-gateway`, aws-terraform fan-out).
> Single researcher, no sub-agents (flat fan-out per brief). Resource docs read from upstream raw
> markdown (`hashicorp/terraform-provider-aws`, `main`) because Registry pages are JS-only (F12).
> Coverage checklist only (not a source): `workspace/terraform/research_AWS_API-Gateway_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL).
> Service scope: **regional** — every resource below accepts optional `region` (F5); none is in the F14 global list.
> Bracketed numbers `[n]` refer to §Source Bibliography; all pages read 2026-10-23.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.16.6) — 1.17.0 stable but not the target | F1, F2 |
| hashicorp/aws | latest 6.70.0 (CHANGELOG header "October 21, 2026"); constraint `~> 6.69`; 6.71.0 "Unreleased"; no 7.x | F3, [1] |
| Withdrawn | 6.57.0 — never pin | F4 |
| `region` per resource | optional, default provider region, change forces replacement, import `id@region` | F5 |
| Identity-based import | `identity` block needs Terraform ≥ 1.12 — documented for `aws_api_gateway_rest_api`, `_resource`, `_method`, `_integration`, `_deployment`, `aws_apigatewayv2_api`, `_integration`, `_route` | F11, [3][4][7][8][2][14][17][18] |
| Two namespaces | "Amazon API Gateway Version 1 resources are used for creating and deploying REST APIs"; WebSocket and HTTP APIs use Version 2 resources | [12][14] |

## 2. Provider 6.x changes for API Gateway

### 2.1 6.0.0 breaking changes (upgrade guide, F13, [2a])
- `aws_api_gateway_account`: **`reset_on_delete` removed**; destroy now always resets the account settings; use a `removed` block to keep the old (keep-settings) behaviour.
- `aws_api_gateway_deployment`: **`stage_name`, `stage_description`, `canary_settings` removed** → use `aws_api_gateway_stage`. **`invoke_url` and `execution_arn` removed** from the deployment. Migration: declare `aws_api_gateway_stage` and `terraform import aws_api_gateway_stage.prod rest_api_id/stage_name`.
- No `aws_apigatewayv2_*` entries in the upgrade guide.

### 2.2 CHANGELOG 6.48.0 → 6.70.0 (in-scope resources) [1]
| Version | Type | Entry | PR |
|---|---|---|---|
| 6.48.0 | bug | `aws_api_gateway_rest_api`: OpenAPI-body-managed `x-amazon-apigateway-policy` no longer overwritten by prior policy state | #48118 |
| 6.53.0 | enhancement | `aws_api_gateway_rest_api` (+ data source): `security_policy`, `endpoint_access_mode` | #47973 |
| 6.58.0 | enhancement + bug | `aws_api_gateway_rest_api`: configurable timeouts; waits for availability on create/update and full deletion on delete | #49205 |
| 6.65.0 | feature + enhancement | `aws_api_gateway_deployment` list resource + resource identity | #49820 |
| 6.65.0 | feature + enhancement | `aws_apigatewayv2_integration` list resource + resource identity | #48425 |
| 6.69.0 | bug | `aws_api_gateway_method`: fixed `deserialization failed` on Read | #50444 |
- No breaking changes for API Gateway in this range. 6.70.0 had no API Gateway entries. Part of the 6.55.0 section fell between two read windows (see L1).

## 3. REST APIs — API Gateway v1 (`aws_api_gateway_*`)

### 3.1 `aws_api_gateway_rest_api` [3]
- Required: `name`. Optional: `body` (OpenAPI), `put_rest_api_mode` (`merge`|`overwrite`, **default `overwrite`**), `api_key_source` (`HEADER` default | `AUTHORIZER`), `disable_execute_api_endpoint` (default `false`), `fail_on_warnings` (default `false`), `minimum_compression_size` (-1..10485760; -1 disables), `binary_media_types`, `policy`, `parameters`, `security_policy`, `endpoint_access_mode` (`BASIC`|`STRICT`, required when `security_policy` starts with `SecurityPolicy_`).
- `endpoint_configuration { types = ["EDGE"|"REGIONAL"|"PRIVATE"] }` — **defaults to `EDGE` if unspecified**; `ip_address_type` `ipv4`|`dualstack` (PRIVATE supports only `dualstack`; drift detected only when set); `vpc_endpoint_ids` only for PRIVATE.
- WARN: with `body`, by default the REST API is replaced by the OpenAPI spec, "removing any existing methods, resources, integrations, or endpoints". NOTE: with `body`, the spec configures resources/methods/integrations.
- `policy` argument: drift detection only when present; provider **recommends `aws_api_gateway_rest_api_policy` instead**.
- Import: REST API ID (`12345abcde`); import **does not support `body`**. Timeouts configurable since 6.58.0 [1].

### 3.2 `aws_api_gateway_rest_api_policy` [12] / `aws_api_gateway_rest_api_put` [11]
- Policy: required `rest_api_id`, `policy` (JSON). Import: REST API ID.
- `aws_api_gateway_rest_api_put` **exists**: required `body` (OpenAPI JSON/YAML, 6 MB max), `rest_api_id`; optional `fail_on_warnings` (default `false`), `parameters` (e.g. `ignore = "documentation"`), `triggers` (forces redeployment). NOTE: `info.title` in the spec updates the API `name`; a mismatch shows as a diff. Timeout `create` 5m. Import: `rest_api_id`.

### 3.3 Resources / methods / integrations
- `aws_api_gateway_resource` [4]: required `rest_api_id`, `parent_id`, `path_part`; attribute `path`. Import `REST-API-ID/RESOURCE-ID`.
- `aws_api_gateway_method` [7]: required `rest_api_id`, `resource_id`, `http_method` (GET…ANY), `authorization` (`NONE`|`CUSTOM`|`AWS_IAM`|`COGNITO_USER_POOLS`); optional `authorizer_id` (CUSTOM/COGNITO only), `authorization_scopes` (COGNITO only), `api_key_required`, `request_parameters` (true = required), `request_models`, `request_validator_id`, `operation_name`. Import `REST-API-ID/RESOURCE-ID/HTTP-METHOD`.
- `aws_api_gateway_integration` [8]: required `rest_api_id`, `resource_id`, `http_method`, `type` (`HTTP`|`MOCK`|`AWS`|`AWS_PROXY`|`HTTP_PROXY`); `integration_http_method` + `uri` required for all but MOCK; `connection_type` default `INTERNET` (`VPC_LINK` needs `connection_id`); `integration_target` (ALB/NLB ARN, VPC Link V2); `timeout_milliseconds` min 50, default 29000, max 300000 (`BUFFERED`) / 900000 (`STREAM`); `response_transfer_mode` default `BUFFERED` — once set, revert by writing `BUFFERED` explicitly, not by removing it; `tls_config.insecure_skip_verification` (HTTP/HTTP_PROXY only); `passthrough_behavior` required with `request_templates`. Import `REST-API-ID/RESOURCE-ID/HTTP-METHOD`.
- AWS limit: integration timeout 50 ms–29 s for Regional/edge/private; Regional and private can be raised above 29 s, "but this might require a reduction in your Region-level throttle quota"; edge cannot [24].
- `aws_api_gateway_method_response` / `_integration_response`: not re-read in this pass (L2).

### 3.4 Deployment and the staleness pitfall
- AWS: "Every time you update an API, you must redeploy the API to an existing stage or to a new stage. Updating an API includes modifying routes, methods, integrations, authorizers, resource policies, and anything else other than stage settings." [21]
- `aws_api_gateway_deployment` [2]: required `rest_api_id`; optional `description`, `triggers` (map; change → redeployment; force with `-replace`), `variables`. **`triggers` "should be preferred over `depends_on`"** because `depends_on` only orders and does not redeploy on upstream changes. For `body`-only APIs, referencing the REST API `id` is enough unless other resources customize the API.
- NOTE: enable `lifecycle { create_before_destroy = true }` "to properly order redeployments"; without it recreation can fail with `BadRequestException: Active stages pointing to this deployment must be moved or deleted`.
- `triggers` and `variables` cannot be imported. Import `REST-API-ID/DEPLOYMENT-ID`. List resource + identity since 6.65.0.
- Staleness pitfall (synthesis of [2][21]): a change to a method/integration/authorizer/policy that is not reflected in `triggers` leaves the stage serving the old snapshot with a clean plan. Pattern: `triggers = { redeployment = sha1(jsonencode([<ids or full resources of every component>])) }` (the hash-of-references form is the provider's documented example; exact example list medium confidence, M1).
- AWS quota: `CreateDeployment` 1 request / 5 s per account, not increasable [23] — bulk redeploys of many APIs in one apply can be throttled.

### 3.5 `aws_api_gateway_stage` [5] and `aws_api_gateway_method_settings` [6]
- Stage required: `rest_api_id`, `deployment_id`, `stage_name`. Optional: `access_log_settings { destination_arn, format }`, `xray_tracing_enabled` (**default `false`**), `cache_cluster_enabled`, `cache_cluster_size` (0.5 … 237), `client_certificate_id`, `canary_settings { deployment_id, percent_traffic, stage_variable_overrides, use_stage_cache=false }`, `variables`. Import `REST-API-ID/STAGE-NAME`.
- Log group: execution logs land in `API-Gateway-Execution-Logs_${rest_api_id}/${stage_name}`; the example manages that group with `depends_on` on the stage "to prevent ordering issues with API Gateway automatically creating the log group first"; import the group once if it already exists.
- Method settings required: `rest_api_id`, `stage_name`, `method_path` (`*/*` or `{resource_path}/{METHOD}`, strip leading `/`, e.g. `trimprefix(path,"/")`), `settings`. Settings: `metrics_enabled`, `logging_level` (`OFF`|`ERROR`|`INFO`), `data_trace_enabled`, `throttling_burst_limit`/`throttling_rate_limit` (**default `-1` = throttling disabled**), `caching_enabled` (needs stage cache cluster), `cache_ttl_in_seconds`, `cache_data_encrypted`, `require_authorization_for_cache_control`, `unauthorized_cache_control_header_strategy`. NOTE: use with `aws_api_gateway_stage`, not deployment-created stages. Import `REST-API-ID/STAGE-NAME/METHOD-PATH`.

### 3.6 `aws_api_gateway_account` [9]
- Optional `cloudwatch_role_arn`; settings are "applied region-wide per `provider` block" (one per account+region). `reset_on_delete` gone in 6.0 (§2.1). Import: account ID.
- Needed for execution logging (APIGateway.1); role must trust `apigateway.amazonaws.com` — role/policy details belong to the IAM unit (L3).

### 3.7 Authorizers, API keys, usage plans
- `aws_api_gateway_authorizer` [10]: required `name`, `rest_api_id`; `type` default **`TOKEN`** (`REQUEST`, `COGNITO_USER_POOLS`); `authorizer_uri` required for TOKEN/REQUEST; `provider_arns` required for COGNITO; `identity_source` default `method.request.header.Authorization`; `authorizer_result_ttl_in_seconds` default `300`; `authorizer_credentials`, `identity_validation_expression`. Import `REST-API-ID/AUTHORIZER-ID`.
- `aws_api_gateway_api_key` [15]: required `name`; `value` (20–128 alphanumerics, generated if omitted), `enabled` default `true`, `customer_id`. Usage plans are required to associate keys with stages. Import: key ID.
- `aws_api_gateway_usage_plan` [16]: required `name`; `api_stages { api_id, stage, throttle { path, burst_limit, rate_limit } }`, `quota_settings { limit, period=DAY|WEEK|MONTH, offset }`, `throttle_settings`. Import: plan ID.
- `aws_api_gateway_usage_plan_key` [16b]: required `key_id`, `key_type = "API_KEY"`, `usage_plan_id`. Import `USAGE-PLAN-ID/USAGE-PLAN-KEY-ID`.
- AWS: "Don't use API keys for authentication or authorization"; a key valid for one API in a plan accesses **all** APIs in that plan; usage-plan throttling/quotas are best-effort — don't rely on them to control costs or block access (use Budgets/WAF) [22].

### 3.8 Custom domains (v1)
- `aws_api_gateway_domain_name` [13]: required `domain_name`; edge cert `certificate_arn` vs regional `regional_certificate_arn` (mutually conflicting); `endpoint_configuration { types, ip_address_type }`; `security_policy` (set it for drift detection); `endpoint_access_mode`; `mutual_tls_authentication { truststore_uri, truststore_version }`; `ownership_verification_certificate_arn`; `policy` (private custom domains only); `routing_mode` (`BASE_PATH_MAPPING_ONLY`|`ROUTING_RULE_ONLY`|`ROUTING_RULE_THEN_BASE_PATH_MAPPING`). NOTEs: ACM certificates required; expects dependency on `aws_acm_certificate_validation`; all arguments **including the private key are stored in state in plain text**. Timeouts create/update 60m. Import: domain name, or `domain/domain_name_id` for private.
- `aws_api_gateway_base_path_mapping` [13b]: required `api_id`, `domain_name`; optional `stage_name`, `base_path` (omit = root), `domain_name_id` (private only). Import `example.com/` or `example.com/base-path` (+ `/id` for private).
- Edge certificate region requirement is not stated on the provider page (U1).

## 4. HTTP and WebSocket APIs — API Gateway v2 (`aws_apigatewayv2_*`)

- `aws_apigatewayv2_api` [14]: required `name`, `protocol_type` (`HTTP`|`WEBSOCKET`). `route_selection_expression` default `$request.method $request.path`; `api_key_selection_expression` default `$request.header.x-api-key` (WebSocket); `ip_address_type` default `ipv4`; `body`, `fail_on_warnings`(false), `cors_configuration`, quick-create `target`/`route_key`/`credentials_arn` — HTTP only; `disable_execute_api_endpoint`. NOTE: with `body`, do not manage integrations/routes as separate resources ("updates may cause manual resource updates to be overwritten"); `name`, `description`, `cors_configuration`, `tags`, `version` set in Terraform override the spec. Import: API ID.
- `aws_apigatewayv2_stage` [17b]: required `api_id`, `name`. `auto_deploy` default `false` (HTTP); `deployment_id`; `access_log_settings { destination_arn (trailing :* trimmed), format }`; `default_route_settings` / `route_settings { route_key }` with `detailed_metrics_enabled`(false), `throttling_burst_limit`, `throttling_rate_limit`, and **WebSocket-only** `data_trace_enabled`(false), `logging_level`(`OFF` default; drift only when set); `client_certificate_id` (WebSocket only); `stage_variables`. Quick-create managed stage cannot be imported. Import `API-ID/STAGE-NAME`.
- `aws_apigatewayv2_route` [18]: required `api_id`, `route_key` (`$default` or `GET /pets`); `authorization_type` **default `NONE`** (HTTP: NONE|JWT|AWS_IAM|CUSTOM; WebSocket: NONE|AWS_IAM|CUSTOM); `authorizer_id`, `authorization_scopes` (JWT); `target = "integrations/<id>"`; WebSocket-only `api_key_required`(false), `request_models`, `model_selection_expression`, `route_response_selection_expression`, `request_parameter`. Import `API-ID/ROUTE-ID`.
- `aws_apigatewayv2_integration` [17]: required `api_id`, `integration_type` (`AWS_PROXY`, `HTTP_PROXY`; `AWS`/`HTTP`/`MOCK` WebSocket only; `HTTP_PROXY` for HTTP private integration). `payload_format_version` **default `1.0`** (`2.0` allowed); `connection_type` default `INTERNET`/`VPC_LINK` + `connection_id`; `integration_subtype` (AWS service action); `timeout_milliseconds` HTTP 50–30000 (default 30 s), WebSocket 50–29000 (default 29 s), drift only when set; `tls_config.server_name_to_verify` (HTTP private); `passthrough_behavior` default `WHEN_NO_MATCH` (WebSocket). Import `API-ID/INTEGRATION-ID`; list resource + identity since 6.65.0.
- `aws_apigatewayv2_authorizer` [19]: required `api_id`, `authorizer_type` (`JWT`|`REQUEST`), `name`. JWT needs `jwt_configuration { audience, issuer }` (HTTP only) and a single `identity_sources` entry. REQUEST: `authorizer_uri`, `authorizer_credentials_arn`; HTTP Lambda authorizers require `authorizer_payload_format_version`; `authorizer_result_ttl_in_seconds` default 300 (max 3600, 0 disables; HTTP only); `enable_simple_responses` (HTTP). Delete timeout 30m. Import `API-ID/AUTHORIZER-ID`.
- `aws_apigatewayv2_deployment` [20]: required `api_id`; `description`, `triggers`. NOTEs: needs at least one route; use `triggers` references or `depends_on` to avoid races; enable `create_before_destroy`. `triggers` not importable. Import `API-ID/DEPLOYMENT-ID`. With `auto_deploy = true` on the stage no explicit deployment is needed (AWS: HTTP APIs support automatic deployments, REST does not [25]).
- `aws_apigatewayv2_domain_name` [20b]: required `domain_name`, `domain_name_configuration { certificate_arn (ACM only), endpoint_type = REGIONAL, security_policy = TLS_1_2, ip_address_type (ipv4 default|dualstack), ownership_verification_certificate_arn }`; `mutual_tls_authentication`; `routing_mode` (`API_MAPPING_ONLY`|`ROUTING_RULE_ONLY`|`ROUTING_RULE_THEN_API_MAPPING`). Timeouts create 10m / update 60m. Import: domain name.
- `aws_apigatewayv2_api_mapping` [20c]: required `api_id`, `domain_name`, `stage`; optional `api_mapping_key`. Import `MAPPING-ID/DOMAIN`.
- `aws_apigatewayv2_vpc_link` [20d]: required `name`, `security_group_ids`, `subnet_ids`; for **HTTP APIs**; REST uses `aws_api_gateway_vpc_link`. Import: VPC link ID.

## 5. Cross-reference — Lambda permission (owned by the Lambda unit)
- `aws_lambda_permission` [26]: `action = "lambda:InvokeFunction"`, `principal = "apigateway.amazonaws.com"`, `source_arn = "${aws_api_gateway_rest_api.X.execution_arn}/*"` ("any stage, method and resource path"). Narrowing to `/<stage>/<METHOD>/<path>` is the execute-api ARN shape (medium confidence on exact v2 path form, M2). Import `function_name/statement_id`. Note: after 6.0 `execution_arn` comes from the REST API (or stage), not the deployment (§2.1).

## 6. Throttling and quotas (AWS)
- Account throttle per Region across HTTP, REST, WebSocket and callback APIs: **10,000 RPS, burst bucket 5,000**, increasable (RPS); burst set by AWS, not requestable. **2,500 RPS / 1,250 burst** default in Cape Town, Milan, Jakarta, UAE, Hyderabad, Melbourne, Spain, Zurich, Tel Aviv, Calgary, Malaysia, Thailand, Mexico (Central) [23].
- Order applied: (1) per-client/per-method limits in a usage plan, (2) per-method stage limits, (3) account per Region, (4) AWS Regional. Throttles and quotas are best-effort "targets rather than guaranteed request ceilings"; excess → `429 Too Many Requests` [27].
- REST [24]: Regional APIs 600/Region, edge 120, private 600 (not increasable); resources/API 300; stages/API 10; authorizers/API 10; API keys 10,000; usage plans 300; VPC links 20; payload 10 MB; cache TTL default 300 s (0–3600); OpenAPI import/put 6 MB; idle connection timeout 310 s.
- HTTP [28]: routes/API 300; integrations 300; max integration timeout 30 s (fixed); stages 10; payload 10 MB; authorizers 10; VPC links 10/Region; Lambda authorizer response 10 s.
- WebSocket [29]: 500 new connections/s per account/Region (increasable); connection 2 h; idle 10 min; frame 32 KB; message 128 KB; routes 300; integration timeout 50 ms–29 s.
- Control plane [23]: CreateRestApi edge 1/30 s, Regional/private 1/3 s; CreateDomainName 1/30 s; PutRestApi 1/s; UpdateAccount 1/20 s; total 10 rps burst 40.

## 7. REST vs HTTP API selection (AWS wording only) [25]
- AWS: "REST APIs support more features than HTTP APIs, while HTTP APIs are designed with minimal features so that they can be offered at a lower price. Choose REST APIs if you need features such as API keys, per-client throttling, request validation, AWS WAF integration, or private API endpoints. Choose HTTP APIs if you don't need the features included with REST APIs."
- REST-only (per AWS table): edge-optimized and private endpoints, backend certificates, AWS WAF, resource policies, API keys, per-client throttling, developer portal, test invocations, caching, custom gateway responses, canary, request validation, body transformation, Firehose access logs, execution logs, X-Ray, mock integrations, response streaming. HTTP-only: JWT authorizer, automatic deployments, Cloud Map private integrations. Both: mTLS, IAM, Cognito (HTTP via JWT), Lambda authorizer, custom domains, CORS, NLB **and ALB** private integrations.

## 8. Security Hub controls (APIGateway) [30]
| ID | Title | Severity | Resource / Terraform lever |
|---|---|---|---|
| APIGateway.1 | REST and WebSocket API execution logging enabled (`loggingLevel` ERROR or INFO) | Medium | `AWS::ApiGateway::Stage`, `AWS::ApiGatewayV2::Stage` → `aws_api_gateway_method_settings.settings.logging_level`; v2 `default_route_settings.logging_level` (WebSocket) + `aws_api_gateway_account` |
| APIGateway.2 | REST stages use SSL certificates for backend authentication | Medium | `aws_api_gateway_stage.client_certificate_id` |
| APIGateway.3 | REST stages have X-Ray tracing | Low | `xray_tracing_enabled = true` |
| APIGateway.4 | Associated with a WAF web ACL (REST stage) | Medium | `aws_wafv2_web_acl_association` (WAF unit) |
| APIGateway.5 | REST cache data encrypted at rest | Medium | `settings.cache_data_encrypted = true` when caching |
| APIGateway.8 | Routes specify an authorization type (`AWS_IAM`/`CUSTOM`/`JWT`) | Medium | `aws_apigatewayv2_route.authorization_type` (default `NONE` fails) |
| APIGateway.9 | Access logging configured for V2 stages | Medium | `aws_apigatewayv2_stage.access_log_settings` |
| APIGateway.10 | V2 integrations use HTTPS for private connections | Medium | `aws_apigatewayv2_integration.tls_config` with `VPC_LINK` |
| APIGateway.11 | Domain names use recommended security policies (`SecurityPolicy_TLS13_1_3_2025_09`, `…_FIPS_2025_09`, `…_1_2_PFS_PQ_2025_09`, `SecurityPolicy_TLS13_2025_EDGE`, `SecurityPolicy_TLS12_PFS_2025_EDGE`) | Medium | `AWS::ApiGateway::DomainName` → `security_policy` + `endpoint_access_mode`; FAILs for HTTP API domains (suppress if legitimate) |
- IDs 6 and 7 are not present on the page (retired/never listed).
- AWS security best practices [31]: least-privilege IAM; logging (CloudWatch Logs/Firehose); CloudWatch alarms; CloudTrail; AWS Config; Security Hub CSPM.

## 9. Unverified / medium confidence / coverage limits
- **U1** Edge-optimized custom domain certificate must be in us-east-1 — not stated on [13]; not re-verified on the AWS page (unverified).
- **U2** Pricing figures in the legacy file (~$3.50 vs ~$1.00 per million, "60% lower latency") — not on any page read (unverified; AWS only says HTTP APIs are "offered at a lower price").
- **M1** Exact list of references inside the provider's `triggers` example for `aws_api_gateway_deployment` (fetch summarised; pattern itself confirmed) (medium confidence).
- **M2** Exact `source_arn` path layout for HTTP API routes (`execution_arn/*/*` style) — only the REST `/*` example was read (medium confidence).
- **M3** No default stated for `logging_level`/`metrics_enabled`/`data_trace_enabled` in REST `method_settings` — treat as unset ⇒ console/API default (medium confidence).
- **L1** CHANGELOG read in two windows; the boundary fell inside 6.55.0, so some 6.55.0 entries were not visible.
- **L2** `aws_api_gateway_method_response`, `_integration_response`, `_vpc_link`, `_request_validator`, `_gateway_response`, `_client_certificate`, `_domain_name_access_association`, `aws_apigatewayv2_routing_rule` pages not re-read.
- **L3** IAM role for `aws_api_gateway_account`, WAF ACL, ACM validation, Lambda function — owned by sibling units.

### Legacy-file claims found wrong or unsupported
1. Uses `aws_api_gateway_deployment` without discussing that `stage_name`/`invoke_url`/`execution_arn`/`canary_settings` were removed in 6.0 — and claims "`aws_api_gateway_account` no longer requires a destroy/recreate cycle" / "`disable_execute_api_endpoint` can now be set at creation" / "`default_tags` now covers all API Gateway resources" as v6 changes: **none found** in the upgrade guide or CHANGELOG; the real 6.0 change is removal of `reset_on_delete` (wrong/unsupported).
2. Tradeoff table "Private Integration REST (NLB) / HTTP (NLB+ALB)": AWS now lists ALB private integrations for REST too [25] (wrong).
3. "VPC Link does not support HTTPS to backend": REST has `tls_config`, v2 has `tls_config` and Security Hub APIGateway.10 requires HTTPS for v2 private integrations (wrong).
4. Backend uses `dynamodb_table` and `required_version >= 1.7`: superseded (F7, F1).
5. "Default account-level throttling is 10,000 RPS": true only outside the 13 reduced-quota Regions (2,500/1,250) (incomplete).
6. Uses the execution-log group name `API-Gateway-Execution-Logs_…` as the **access-log** destination — the provider page uses that name for the execution-log group; access logs can go to any group (misleading).

## 10. Security note
No prompt-injection or instruction-like text observed in any fetched page. One fetch (wrong WebSocket quota URL) returned a model-generated answer from memory; it was discarded and replaced by the correct AWS page [29].

## Source Bibliography
All pages read 2026-10-23.
1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_deployment.html.markdown
2a. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_resource.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_stage.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method_settings.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_integration.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_account.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_authorizer.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api_put.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api_policy.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_domain_name.html.markdown
13b. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_base_path_mapping.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api.html.markdown
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_api_key.html.markdown
16. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_usage_plan.html.markdown
16b. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_usage_plan_key.html.markdown
17. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_integration.html.markdown
17b. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_stage.html.markdown
18. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_route.html.markdown
19. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_authorizer.html.markdown
20. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_deployment.html.markdown
20b. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_domain_name.html.markdown
20c. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api_mapping.html.markdown
20d. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_vpc_link.html.markdown
21. https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-deploy-api.html
22. https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html
23. https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html
24. https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html
25. https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
26. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_permission.html.markdown
27. https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html
28. https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html
29. https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html
30. https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html
31. https://docs.aws.amazon.com/apigateway/latest/developerguide/security-best-practices.html
