# Evaluation report - provisioning-aws-api-gateway-v6 (round 1)

Method: SKILL.md and all linked blueprints read. Each response was written by the evaluator using only skill content (no sub-agents), then judged. Source: packages/aws-terraform/.apm/skills/provisioning-aws-api-gateway-v6/

## Scenario 1 - Canonical REST (PASS, 7/7 must_pass, 0/3 must_not)

Response summary: terraform block with `required_version = "~> 1.16"`, aws `~> 6.69`, S3 backend `use_lockfile = true` (rest-core §1). Regional `aws_api_gateway_rest_api`, resource, GET method, `AWS_PROXY` integration with placeholder `var.integration_uri` (§2-3). `aws_api_gateway_deployment` with `triggers = { redeployment = sha1(jsonencode([...])) }` and `lifecycle { create_before_destroy = true }` (deployment §4). Separate `aws_api_gateway_stage` with `xray_tracing_enabled = true`, `access_log_settings { destination_arn = var.access_log_destination_arn }`, and a distinct `aws_cloudwatch_log_group` for `API-Gateway-Execution-Logs_${id}/stage` with `depends_on` (§5). `aws_api_gateway_method_settings` on `aws_api_gateway_stage.example.stage_name`, `method_path = "*/*"`, `logging_level = "ERROR"` (§6). Also the `aws_api_gateway_account` note for execution logging (§7).

must_pass:
1. PASS - "required_version = \"~> 1.16\"" / "version = \"~> 6.69\"" (rest-core §1).
2. PASS - stage is its own resource, `deployment_id = ...deployment.example.id`.
3. PASS - `triggers` and `create_before_destroy = true` both present (§4).
4. PASS - `access_log_settings.destination_arn` placeholder, distinct from the execution log group (§5).
5. PASS - method_settings + `logging_level = "ERROR"` (§6).
6. PASS - `xray_tracing_enabled = true` (§5).
7. PASS - `# placeholder` / `# example` tags on URI, destination ARN.
must_not: all OK. No `stage_name` on the deployment, no `invoke_url`, no `dynamodb_table`.

Notes: the skill gives no access-log destination resource (CloudWatch is out of scope), so a placeholder variable is the only skill-backed option. This is fine for criterion 4 but the answer is thin. Family separation: only `aws_api_gateway_*` used.

## Scenario 2 - Account throttle quota (PASS, 3/3, 0/2)

Response (from the SKILL.md Ask First row "Account throttle quota"): the default is 10,000 RPS with a burst of 5,000 per Region, shared across HTTP, REST, WebSocket and callback APIs. 13 Regions (Cape Town, Milan, Jakarta, UAE, Hyderabad, Melbourne, Spain, Zurich, Tel Aviv, Calgary, Malaysia, Thailand, Mexico (Central)) default to 2,500 RPS, burst 1,250. Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html. The quota is an AWS service quota, not something Terraform enforces. I would ask which Region applies.

must_pass: all PASS (figures and the 13-Region list quoted verbatim from the row; AWS limits page cited).
must_not: OK (not stated as universal; framed as an AWS quota).
Notes: the skill never says "not Terraform-enforced" explicitly. The response stays OK because it only presents the AWS source. Content lives only in the SKILL.md Ask First table (no blueprint), which is acceptable. The criterion could be stronger if it required citing the limits.html URL.

## Scenario 3 - Misuse: HTTP API with v1 resource (PASS, 4/4, 0/2)

Response: `aws_api_gateway_rest_api` is the REST (v1) resource and cannot create an HTTP API (Never Do: "Build HTTP or WebSocket APIs from aws_api_gateway_* resources"). Use `aws_apigatewayv2_api { protocol_type = "HTTP" }`. JWT authorizer: `aws_apigatewayv2_authorizer { authorizer_type = "JWT", identity_sources = [single entry], jwt_configuration { audience, issuer } }`, route with `authorization_type = "JWT"` and `authorizer_id` (route types for HTTP: NONE|JWT|AWS_IAM|CUSTOM). `logging_level` and `data_trace_enabled` are WebSocket only (Never Do; http-websocket §12), so on the HTTP stage use `access_log_settings` (APIGateway.9) with `auto_deploy = true` and no `logging_level`. WebSocket stage is the only place for `logging_level`.

must_pass: all PASS (cited fragments: "`logging_level` (default `OFF`) and `data_trace_enabled` ... are WebSocket only", "authorizer_type is JWT ... jwt_configuration { audience, issuer }"). Families kept separate.
must_not: OK. The route example in the skill only shows AWS_IAM, so wiring `authorization_type = "JWT"` + `authorizer_id` is inferred from the route type list, not a skill snippet (minor skill gap, not a failure).
Notes: quoting `logging_level` as a rejected example is allowed.

## Scenario 4 - 6.0 removals and legacy claims (PASS, 5/5, 0/2)

Response: (a) `stage_name` on the deployment was removed in 6.0 (also `stage_description`, `canary_settings`, `invoke_url`, `execution_arn`); declare `aws_api_gateway_stage` and import with `terraform import aws_api_gateway_stage.prod rest_api_id/stage_name`. (b) `reset_on_delete` was removed in 6.0; destroy always resets account settings; a `removed` block keeps the old behaviour. (c) The VPC link HTTPS claim is wrong: `tls_config` exists on integrations (REST `insecure_skip_verification`, v2 `server_name_to_verify`) and APIGateway.10 requires HTTPS for V2 private integrations. (d) NLB-only is wrong: AWS lists NLB and ALB for REST and HTTP APIs; REST `integration_target` takes an ALB/NLB ARN or VPC Link V2. (e) Source: version-6-upgrade guide URL.

must_pass: all PASS. must_not: OK (no default_tags or recreate claims; skill is silent on them).
Notes (criterion quality):
- must_pass 3 is only partly supported. The skill supports "tls_config exists on both" and APIGateway.10, but never states directly that a VPC link "can use HTTPS". HTTPS is inferred. The `aws_api_gateway_vpc_link` page is a listed coverage gap (L2).
- must_not 2 (default_tags / no destroy-recreate) tests content the skill never mentions. It is not checkable from the research. It reads like a trap from an earlier research draft, so treat it as an unsourced criterion; it passes only by silence.
- Family separation kept (REST vs v2 tls_config described per family).

## Scenario 5 - Uncertain item: ask first (PASS, 4/4, 0/2)

Response: the skill marks the edge certificate Region as (unverified): the provider domain page does not state it (U1) and the skill does not assert `us-east-1`. Before choosing a Region, I ask: "Confirm the Region of the ACM certificate for the edge-optimized domain." Use `aws_api_gateway_domain_name` with `certificate_arn` and `endpoint_configuration { types = ["EDGE"] }`; do not set `regional_certificate_arn` (they conflict). `depends_on = [aws_acm_certificate_validation.example]` (the page expects it; ACM skill owns it). Note state stores args in plaintext. Mention `aws_api_gateway_base_path_mapping`.

must_pass: all PASS. must_not: OK (us-east-1 raised only as an open question).
Notes: the skill HCL for the domain is the regional variant. The edge variant has to be adapted from prose (`certificate_arn` for edge). This is a minor gap, not a failure. The criterion "Asks the user" assumes an interactive turn.

## Summary

| Scenario | must_pass | must_not OK | Verdict |
|---|---|---|---|
| 1 Canonical REST | 7/7 | 3/3 | PASS |
| 2 Throttle quota | 3/3 | 2/2 | PASS |
| 3 HTTP vs REST misuse | 4/4 | 2/2 | PASS |
| 4 6.0 removals | 5/5 | 2/2 | PASS |
| 5 Ask first | 4/4 | 2/2 | PASS |

Overall: 5/5 scenarios PASS; must_pass 23/23; must_not 11/11.

REST vs v2 family separation held in all answers. No cross-family leakage was found.

## Fixes (short, all optional)

1. evaluation-scenarios.md S4 must_not 2: unsourced (skill never discusses default_tags or recreate on aws_api_gateway_account). Remove it or add the sourced fact to the skill.
2. evaluation-scenarios.md S4 must_pass 3: reword to "tls_config exists on REST and v2 integrations; APIGateway.10 requires HTTPS for V2 private integrations". Drop "VPC link can use HTTPS" unless sourced.
3. always-do-rest-auth-domain.md §10: add an edge-variant snippet (`certificate_arn`, `types = ["EDGE"]`) to back S5. Currently regional only.
4. always-do-http-websocket.md §12: add a route snippet with `authorization_type = "JWT"` + `authorizer_id` to back S3.
5. S2 criterion could require citing the limits.html URL explicitly.
6. S1 access-log destination has no concrete resource (CloudWatch is out of scope). Consider an explicit sibling-skill pointer.
