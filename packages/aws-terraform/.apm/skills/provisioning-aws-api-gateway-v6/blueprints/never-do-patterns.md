# Never-Do Patterns — provisioning-aws-api-gateway-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (read dates in unverified-and-risks.md), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `stage_name` / `stage_description` / `canary_settings` / `invoke_url` / `execution_arn` on `aws_api_gateway_deployment` (removed in 6.0) | [never-do-provider-migration](./never-do-provider-migration.md#1-removed-arguments-on-aws_api_gateway_deployment) |
| `reset_on_delete` on `aws_api_gateway_account` (removed in 6.0) | [never-do-provider-migration](./never-do-provider-migration.md#2-reset_on_delete-on-aws_api_gateway_account) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-provider-migration](./never-do-provider-migration.md#3-s3-backend-with-dynamodb_table) |
| Pinning withdrawn provider 6.57.0 | [never-do-provider-migration](./never-do-provider-migration.md#4-pinning-version-6570) |
| Both `certificate_arn` and `regional_certificate_arn` on a domain name | [never-do-rest](./never-do-rest.md#1-both-certificate_arn-and-regional_certificate_arn-on-a-domain-name) |
| Removing `response_transfer_mode` to revert to `BUFFERED` | [never-do-rest](./never-do-rest.md#2-removing-response_transfer_mode-to-revert-to-buffered) |
| API keys as authentication or authorization | [never-do-rest](./never-do-rest.md#3-api-keys-as-authentication-or-authorization) |
| Usage-plan throttling or quotas to control costs or block access | [never-do-rest](./never-do-rest.md#4-usage-plan-throttling-or-quotas-to-control-costs-or-block-access) |
| Separate routes or integrations on a v2 API that has `body` | [never-do-http-websocket](./never-do-http-websocket.md#1-separate-integrations-or-routes-on-an-api-that-has-a-body) |
| `logging_level` / `data_trace_enabled` on an HTTP API stage | [never-do-http-websocket](./never-do-http-websocket.md#2-logging_level-or-data_trace_enabled-on-an-http-api-stage) |
| `JWT` authorization type on a WebSocket route | [never-do-http-websocket](./never-do-http-websocket.md#3-jwt-authorization-type-on-a-websocket-route) |
| `AWS` / `HTTP` / `MOCK` integration type on an HTTP API | [never-do-http-websocket](./never-do-http-websocket.md#4-aws-http-or-mock-integration-type-on-an-http-api) |
| Integration timeout outside the protocol range | [never-do-http-websocket](./never-do-http-websocket.md#5-integration-timeout-outside-the-protocol-range) |
| Version 1 resources for an HTTP or WebSocket API | [never-do-http-websocket](./never-do-http-websocket.md#6-version-1-resources-for-an-http-or-websocket-api) |
