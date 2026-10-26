# Evaluation Scenarios — provisioning-oci-api-gateway

## Scenario 1: Canonical — JWT-authenticated deployment with Function backend

```json
{
  "skills": ["provisioning-oci-api-gateway"],
  "query": "Provision an OCI API Gateway with a JWT-authenticated deployment that routes /api/orders POST to an OCI Function. The gateway should be public, have rate limiting, and CORS enabled.",
  "expected_behavior": [
    "Creates oci_apigateway_gateway with endpoint_type = 'PUBLIC' in a public subnet",
    "Creates oci_apigateway_deployment with specification block containing routes and policies",
    "Sets JWT authentication_policy with remote_jwks_uri pointing to IdP",
    "Adds rate_limiting block at deployment level with rate_in_requests_per_second and rate_key = 'CLIENT_IP'",
    "Adds cors_policy block with allowed_origins and allowed_methods",
    "Route backend uses type = 'ORACLE_FUNCTIONS_BACKEND' with function_id from module output",
    "Deployment has depends_on = [oci_identity_policy.this] to handle 60s IAM propagation",
    "IAM policy includes 'use fn-invocation' verb for the API Gateway service principal"
  ]
}
```

## Scenario 2: Edge — Missing IAM policy causes 502 Bad Gateway

```json
{
  "skills": ["provisioning-oci-api-gateway"],
  "query": "My API Gateway deployment was created successfully but every Function invocation returns 502 Bad Gateway. The Function works when invoked directly via OCI CLI.",
  "expected_behavior": [
    "Identifies missing or not-yet-propagated IAM policy as root cause",
    "Points to the required policy statement: 'allow service apigateway to use fn-invocation in compartment <name>'",
    "Explains 60-second IAM propagation delay after policy creation",
    "Recommends adding depends_on = [oci_identity_policy.this] to the oci_apigateway_deployment resource",
    "Does NOT suggest disabling authentication or changing Function code",
    "May reference the Verification Loop troubleshooting entry for 502 errors"
  ]
}
```

## Scenario 3: Edge — Private gateway endpoint for internal VCN consumers

```json
{
  "skills": ["provisioning-oci-api-gateway"],
  "query": "I need an API Gateway only accessible from within my VCN. Other teams' services running in private subnets should call it. It must not be reachable from the internet.",
  "expected_behavior": [
    "Sets endpoint_type = 'PRIVATE' on oci_apigateway_gateway",
    "Places gateway in a private subnet (no Internet Gateway route required)",
    "Creates NSG with ingress rule allowing TCP 443 from VCN CIDR only",
    "Asks whether DNS resolution should use OCI private DNS zones or service endpoints",
    "Does NOT use a public subnet for a PRIVATE gateway",
    "Does NOT skip NSG — private endpoint still benefits from NSG to restrict source CIDRs within VCN"
  ]
}
```

## Scenario 4: Edge — Quota / scalability ceiling hit

```json
{
  "skills": ["provisioning-oci-api-gateway"],
  "query": "My Terraform plan is failing with: 'LimitExceeded: Maximum number of deployments (100) per gateway reached'. How should I restructure?",
  "expected_behavior": [
    "Confirms the 100 deployments per gateway service limit",
    "Recommends adding a second gateway resource for the overflow deployments",
    "Explains that routes per deployment is also limited to 100 — suggest consolidating routes before splitting gateways",
    "Does NOT suggest simply deleting unused deployments without checking if any are still referenced",
    "May reference the Quick Reference limits table"
  ]
}
```

## Scenario 5: Misuse — Anti-pattern: Functions exposed without API Gateway

```json
{
  "skills": ["provisioning-oci-api-gateway"],
  "query": "To simplify our setup, can I just expose the OCI Function's invoke endpoint directly to external users? I'll handle auth in the Function code.",
  "expected_behavior": [
    "Identifies this as a 'Never Do' anti-pattern: Functions exposed without API Gateway",
    "Explains missing capabilities: no rate limiting (DDoS risk), no CORS handling, no centralized logging, no JWT validation",
    "Points out that Function invoke endpoint requires OCI IAM signature — not suitable for external consumer auth patterns",
    "Recommends placing API Gateway in front, even if auth is initially ANONYMOUS for internal tools",
    "Does NOT generate code that bypasses API Gateway for external-facing Functions"
  ]
}
```
