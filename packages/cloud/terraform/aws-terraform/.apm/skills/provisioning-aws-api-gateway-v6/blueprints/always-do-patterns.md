# Always-Do Patterns — provisioning-aws-api-gateway-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL and cites its source (read
dates in unverified-and-risks.md). REST (v1, `aws_api_gateway_*`) and HTTP/WebSocket (v2, `aws_apigatewayv2_*`) are kept in
separate files.

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`), S3 backend with `use_lockfile`, `region` | [always-do-rest-core](./always-do-rest-core.md#1-terraform-block-and-s3-backend) |
| 2 | REST API, endpoint type, OpenAPI `body`, REST API policy | [always-do-rest-core](./always-do-rest-core.md#2-rest-api) |
| 3 | REST resource, method, integration, private integrations, timeouts | [always-do-rest-core](./always-do-rest-core.md#3-resource-method-and-integration) |
| 4 | REST deployment with `triggers` and `create_before_destroy` | [always-do-rest-deployment](./always-do-rest-deployment.md#4-deployment-and-redeployment) |
| 5 | REST stage, access logs, execution-log group | [always-do-rest-deployment](./always-do-rest-deployment.md#5-stage-access-logs-and-execution-log-group) |
| 6 | REST method settings (logging, caching) | [always-do-rest-deployment](./always-do-rest-deployment.md#6-method-settings) |
| 7 | REST account CloudWatch role | [always-do-rest-deployment](./always-do-rest-deployment.md#7-account-cloudwatch-role) |
| 8 | REST authorizer | [always-do-rest-auth-domain](./always-do-rest-auth-domain.md#8-authorizer) |
| 9 | REST API keys and usage plans | [always-do-rest-auth-domain](./always-do-rest-auth-domain.md#9-api-keys-and-usage-plans) |
| 10 | REST custom domain and base path mapping | [always-do-rest-auth-domain](./always-do-rest-auth-domain.md#10-custom-domain-and-base-path-mapping) |
| 11 | HTTP/WebSocket API, integration, route, private integration | [always-do-http-websocket](./always-do-http-websocket.md#11-api-integration-and-route) |
| 12 | HTTP/WebSocket stage, authorizer, deployment | [always-do-http-websocket](./always-do-http-websocket.md#12-stage-authorizer-and-deployment) |
| 13 | v2 custom domain, API mapping, VPC link | [always-do-http-domain-access](./always-do-http-domain-access.md#13-custom-domain-api-mapping-and-vpc-link-v2) |
| 14 | Lambda invoke permission | [always-do-http-domain-access](./always-do-http-domain-access.md#14-lambda-invoke-permission-owned-by-the-lambda-skill) |
| 15 | Coverage notes (pages not researched in depth) | [always-do-http-domain-access](./always-do-http-domain-access.md#15-coverage-notes-not-researched-in-depth--no-hcl) |
