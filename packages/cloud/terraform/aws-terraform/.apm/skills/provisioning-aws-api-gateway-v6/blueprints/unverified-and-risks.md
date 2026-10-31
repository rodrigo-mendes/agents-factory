# Unverified Claims and Risks — hashicorp/aws 6.x API Gateway

Per-source read dates in the Source Bibliography. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- hashicorp/aws latest is 6.70.0 (CHANGELOG header "October 21, 2026"); constraint stays `~> 6.69`; 6.71.0 is
  "Unreleased"; no 7.x released. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Terraform 1.16.7 (2026-10-22, newest 1.16.x) is the target (`~> 1.16`). Terraform 1.17.0 is stable since 2026-10-21 and is not the
  target of this skill. Source: https://releases.hashicorp.com/terraform/
- 6.57.0 was withdrawn from GitHub and the Registry — never pin it.
- v7 is planned (the upgrade guide documents removals "in v7.0.0"). When v7 ships, create a new skill.
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Resource docs were read from the `main` branch (Registry pages render only with JavaScript), which can
  run slightly ahead of 6.70.0.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Whether an edge-optimized custom domain certificate must be in `us-east-1` — not stated on the provider domain page and not re-verified on an AWS page | (unverified) — ask before choosing a certificate Region |
| U2 | Pricing figures and latency comparisons between REST and HTTP APIs — not on any page read; AWS only says HTTP APIs are "offered at a lower price" | Registered only; not used in this skill |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Exact list of references inside the provider's `triggers` example for `aws_api_gateway_deployment`; the hash-of-references pattern itself is confirmed | (medium confidence) — the example list in always-do-rest-deployment.md §4 is illustrative |
| M2 | Exact `source_arn` path layout for HTTP API routes (only the REST `/*` example was read) | (medium confidence) — verify before narrowing the permission |
| M4 | How HTTPS is configured for v2 private integrations: APIGateway.10 requires HTTPS for private connections; the integration page does not say an https URI is required and does not mention `server_name_to_verify` in the REST page | (medium confidence) — ask before choosing |
| M5 | Absence claims: no `aws_apigatewayv2_*` entry seen in the 6.0 upgrade guide; no API Gateway breaking changes seen in CHANGELOG 6.48.0-6.70.0 (part of 6.55.0 not visible) | (medium confidence, absence of evidence) |
| M3 | No default is stated for `logging_level`, `metrics_enabled`, `data_trace_enabled` in REST `method_settings`; treat as unset | (medium confidence) — set them explicitly |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG was read in two windows; the boundary fell inside 6.55.0, so some 6.55.0 entries were not visible |
| L2 | Pages not researched in depth: `aws_api_gateway_method_response`, `_integration_response`, `_vpc_link`, `_request_validator`, `_gateway_response`, `_client_certificate`, `_domain_name_access_association`, `aws_apigatewayv2_routing_rule` — no HCL in this skill |
| L3 | IAM role for `aws_api_gateway_account`, WAF ACL, ACM validation and the Lambda function belong to sibling skills |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (medium confidence) | always-do-rest-deployment.md §4 Deployment and Redeployment — `triggers` reference list | M1 |
| (medium confidence) | always-do-http-domain-access.md §14 Lambda Invoke Permission — HTTP API `source_arn` layout | M2 |
| (unverified) | always-do-rest-auth-domain.md §10 Custom Domain and Base Path Mapping — edge certificate Region | U1 |
| (medium confidence) | SKILL.md Ask First — `triggers` reference list | M1 |
| (medium confidence) | SKILL.md Ask First — HTTP API `source_arn` layout | M2 |
| (medium confidence) | SKILL.md Ask First — REST `method_settings` defaults | M3 |
| (unverified) | SKILL.md Ask First — edge certificate Region | U1 |
| (medium confidence) | SKILL.md Ask First — v2 private integration HTTPS | M4 |
| (medium confidence) | always-do-http-websocket.md §11 — v2 private integration HTTPS | M4 |
| (medium confidence) | evaluation-scenarios.md Scenario 4 — HTTPS configuration for private integrations | M4 |
| (medium confidence, absence of evidence) | SKILL.md 5.x to 6.x Migration — upgrade guide v2 entries, CHANGELOG range, 6.55.0 | M5 |
| (medium confidence) | always-do-rest-deployment.md §6 Method Settings — no stated defaults | M3 |
| (unverified) | evaluation-scenarios.md Scenario 5 — edge certificate Region | U1 |

## Source Bibliography

Read dates: items 1, 39, 40, 41, 42, 43 are marked individually (the withdrawn 6.57.0 fact was read 2026-10-14); all other pages 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.48.0 to 6.70.0 entries (listing 2026-10-22; withdrawn 6.57.0 2026-10-14)
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_deployment.html.markdown — triggers, create_before_destroy
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — 6.0 breaking changes
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_resource.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_stage.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method_settings.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_method.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_integration.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_account.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_authorizer.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api_put.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_rest_api_policy.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_domain_name.html.markdown
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_base_path_mapping.html.markdown
16. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api.html.markdown
17. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_api_key.html.markdown
18. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_usage_plan.html.markdown
19. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_usage_plan_key.html.markdown
20. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_integration.html.markdown
21. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_stage.html.markdown
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_route.html.markdown
23. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_authorizer.html.markdown
24. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_deployment.html.markdown
25. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_domain_name.html.markdown
26. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_api_mapping.html.markdown
27. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/apigatewayv2_vpc_link.html.markdown
28. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_permission.html.markdown
29. https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-deploy-api.html — redeploy after updates
30. https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html — API keys, usage plans
31. https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html — account throttle, control-plane quotas
32. https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html — REST quotas
33. https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html — REST vs HTTP comparison
34. https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html — throttle order
35. https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html — HTTP API quotas
36. https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html — WebSocket quotas
37. https://docs.aws.amazon.com/securityhub/latest/userguide/apigateway-controls.html — Security Hub APIGateway controls
38. https://docs.aws.amazon.com/apigateway/latest/developerguide/security-best-practices.html — security best practices
39. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — `region` argument (2026-10-23)
40. https://developer.hashicorp.com/terraform/language/backend/s3 — `use_lockfile`; `dynamodb_table` deprecated (2026-10-23)
41. https://developer.hashicorp.com/terraform/language/expressions/version-constraints — `~>` for root modules (2026-10-23)
42. https://releases.hashicorp.com/terraform/ — Terraform 1.16.7 (2026-10-23) newest 1.16.x, 1.17.0 stable (2026-10-23); https://releases.hashicorp.com/terraform-provider-aws/ — latest 6.70.0 (2026-10-23)
43. https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md — Terraform 1.17.0 release notes (2026-10-23)
