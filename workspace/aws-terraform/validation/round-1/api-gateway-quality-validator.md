# Quality validation round 1 — provisioning-aws-api-gateway-v6

Written by the orchestrator from the validator's returned report (the validator could not write files and had no WebFetch). Counts: HIGH 3 · MEDIUM 10 · LOW 6. ~60 claims sampled.

## HIGH
- H1 Never row 16 (SKILL.md:108, never-do-http-websocket.md §6): "using aws_apigatewayv2_vpc_link for REST is wrong" contradicts SKILL.md:86 and always-do-rest-core.md:107 ("REST integration_target takes an ALB/NLB ARN or VPC Link V2"). ORCHESTRATOR VERIFIED on the provider aws_api_gateway_integration page (2026-10-23): `integration_target` = "ALB or NLB ARN to send the request to. Used for private integrations with VPC Link V2"; the page's own VPC Link V2 example pairs aws_api_gateway_rest_api with aws_apigatewayv2_vpc_link; `connection_id` = "ID of the VpcLink… Required if connection_type is VPC_LINK" (V1 vs V2 not stated). The Never row is WRONG → remove.
- H2 Blanket "read 2026-10-23" dates on facts-file sources (SKILL.md:17,:113,:163; unverified-and-risks.md:3,:54; headers of all topic/index blueprints).
- H3 SKILL.md:68 "Use HTTPS (tls_config) for v2 private integrations; APIGateway.10 checks it" is an inference. Provider integration page (2026-10-23): `tls_config` is "Supported only for HTTP and HTTP_PROXY integrations"; `insecure_skip_verification` not recommended; for private integrations `uri` is used for the Host header and certificate validation; the page does NOT say an https URI is required. Security Hub says only "HTTPS for private connections".

## MEDIUM
M1 23 Always bullets (not 20); M2 Never row 9 ✅ ("IAM, custom authorizer, Cognito") not in research; M3 "Edge cannot exceed 29 s" is the converse of "Regional/private can be raised"; provider 300000/900000 max not reconciled; M4 Never row 5 turns "authorizer_id applies when CUSTOM/COGNITO" into a prohibition; M5 absence claims untagged (SKILL.md:150,:152); M6 SKILL.md:159 upgrade path unsourced; M7 Ask First "Private integration" row cites AWS page for a provider claim; M8 tag/register inconsistencies (M3 untagged in always-do-rest-deployment.md:108-109, "(unverified)" at evaluation-scenarios.md:112 unmapped, U2 orphan); M9 internal wording ("(IAM unit)", "not re-read in this pass"); M10 Always bullets 1-2 cite releases listings for the `~>` rule (constraints page).

## LOW
L1 APIGateway.11 policy names abbreviated; L2 bullets with two claims, "depends_on on the stage" ambiguous; L3 "Role must trust apigateway.amazonaws.com" unattributed; L4 v2 integration HCL not clearly incomplete; L5 `~> 6.69` cited to CHANGELOG; L6 "access logs separate from execution-log group" basis thin.
