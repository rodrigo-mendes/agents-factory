# Evaluation Scenarios — designing-oci-api-gateway

## Scenario 1: Canonical — JWT Authentication Decision

```json
{
  "skills": ["designing-oci-api-gateway"],
  "query": "We have an OCI Functions-based REST API that needs to be exposed via API Gateway. Users authenticate through an OCI IAM Identity Domain (IDCS). How should we configure authentication?",
  "expected_behavior": [
    "Recommends JWT authentication at the Deployment level (not per-route) using the JWKS URI from the IAM Identity Domain",
    "Specifies the issuer claim must match the Identity Domain issuer URL exactly",
    "Sets audience to the client_id of the registered application",
    "Advises setting allowed_issuers to a single value — not a wildcard",
    "Does NOT recommend Custom Authorizer for standard IDCS JWT (only needed for complex claim transformation logic)",
    "Notes that SSL verification on JWKS URI must remain enabled — disabling it is a Never Do pattern"
  ]
}
```

## Scenario 2: Edge — Private vs Public Gateway for Internal Microservices

```json
{
  "skills": ["designing-oci-api-gateway"],
  "query": "We have an OCI Functions microservice that is called only by other services inside the same VCN. A developer wants to put an API Gateway in front of it for rate limiting. Should we use a public or private gateway?",
  "expected_behavior": [
    "Recommends PRIVATE endpoint type — the gateway is assigned a hostname resolvable only within the VCN",
    "Explains that PUBLIC endpoint would unnecessarily expose the service to internet routing",
    "Notes that a private gateway still requires a public subnet for the gateway itself (subnet routing rules differ from endpoint type)",
    "Confirms rate limiting and authentication policies work identically on PRIVATE gateways",
    "Asks whether the VCN has a Service Gateway if Functions are in a private subnet (required for gateway-to-function path)",
    "Does NOT suggest skipping the gateway and calling Functions directly via HTTPS endpoint — that bypasses IAM policy enforcement and rate limiting"
  ]
}
```

## Scenario 3: Edge — Rate Limiting and Cost Explosion Risk

```json
{
  "skills": ["designing-oci-api-gateway"],
  "query": "Our API is public and we expect up to 500 req/s in normal conditions, but we are worried about DDoS causing runaway OCI Functions billing. What rate limiting strategy should we configure?",
  "expected_behavior": [
    "Recommends per-route rate limiting with type CLIENT_IP as a minimum baseline",
    "Notes the default max per-route rate limit is 1000 req/s and recommends setting it at or below expected peak plus a safety margin",
    "Recommends Usage Plans with subscriber quotas for authenticated clients where tenant-level billing attribution is needed",
    "Recommends enabling OCI WAF in front of the gateway for bot mitigation and geo-blocking before traffic reaches the gateway",
    "Notes that rate limits at the gateway do not replace WAF — WAF filters at the edge before requests hit gateway quota accounting",
    "Does NOT recommend relying solely on OCI Functions concurrency limits as a cost ceiling — Functions throttle with 429, not a billing cap"
  ]
}
```

## Scenario 4: Misuse — CORS Wildcard with Credentials

```json
{
  "skills": ["designing-oci-api-gateway"],
  "query": "A frontend developer asks to set allowed_origins = ['*'] on the CORS policy of our API Gateway deployment so they can test from any local machine. The API uses JWT bearer tokens.",
  "expected_behavior": [
    "Rejects allowed_origins = ['*'] when credentials (Authorization header / JWT) are present — this violates the CORS spec and browsers will reject it",
    "Explains that browsers block requests when Access-Control-Allow-Origin is '*' and credentials are included",
    "Recommends configuring explicit origins matching the development and production URLs",
    "Suggests using a dev-only deployment with specific localhost origins (e.g., http://localhost:3000) that is separate from the production deployment",
    "Flags this as a Never Do pattern in the skill (Wildcard CORS with Credentials)",
    "Does NOT suggest setting allowed_headers = ['*'] as a workaround — header wildcards have the same credential restriction"
  ]
}
```

## Scenario 5: Misuse — Exposing Functions Without Gateway

```json
{
  "skills": ["designing-oci-api-gateway"],
  "query": "To simplify the architecture, a team member suggests calling OCI Functions directly via their HTTPS endpoint and skipping API Gateway entirely. Is this acceptable?",
  "expected_behavior": [
    "Rejects direct Function invocation for any externally accessible endpoint — the Function HTTPS endpoint has no rate limiting, no authentication enforcement, and no CORS policy",
    "Explains that any OCI user/group with fn:InvokeFunctions permission in the tenancy can call the function, which is a broader attack surface than gateway-fronted APIs",
    "Notes cost explosion risk: without rate limiting, a DDoS or runaway client can invoke the function unboundedly at $0.20/million invocations",
    "Accepts direct invocation only for internal service-to-service calls within OCI using Resource Principals — not for external-facing APIs",
    "Flags this as the top Never Do pattern: Functions Exposed Without API Gateway"
  ]
}
```
