# Evaluation Scenarios — designing-aws-api-gateway-serverless

## How to use

Run via `/evaluating-skill-scenarios designing-aws-api-gateway-serverless`.
Each scenario verifies the skill guides the agent to the correct AWS API Gateway architectural decision.

---

## Scenario 1 — Canonical: New serverless JSON API (HTTP API default)

```json
{
  "skills": ["designing-aws-api-gateway-serverless"],
  "query": "We are building a new serverless JSON API backed by Lambda for a B2C mobile app. Authentication uses Auth0 (OIDC/OAuth 2.0 JWT). We need no special metering, caching, or private access. What API type should we use and what mandatory guardrails apply?",
  "expected_behavior": [
    "Recommends HTTP API (v2) as the default — ~71% lower cost and ~60% lower latency than REST API",
    "Specifies the native JWT authorizer for Auth0 OIDC — no Lambda authorizer needed for standard OIDC/OAuth on HTTP API",
    "Requires explicit stage-level throttling below the account-level quota (10,000 RPS / 5,000 burst or 2,500/1,250 in newer Regions)",
    "Requires JSON access logging to CloudWatch Logs with $context variables and CloudWatch alarms on 5XX/4XX/Latency",
    "Notes WAF cannot attach directly to an HTTP API — recommends CloudFront + WAF web ACL for WAF protection",
    "Does NOT recommend REST API unless a REST-only feature is specifically required"
  ]
}
```

---

## Scenario 2 — API Type Crossroads: SaaS with metering, validation, and WAF

```json
{
  "skills": ["designing-aws-api-gateway-serverless"],
  "query": "We are building a SaaS API that needs per-tenant metering (different call quotas per pricing tier), per-tenant rate limiting, WAF protection, and request body validation before Lambda is invoked. We started building on an HTTP API (apigatewayv2). Is this correct?",
  "expected_behavior": [
    "Flags that HTTP API is the WRONG choice — it lacks API keys/usage plans, per-client throttling, direct WAF attachment, and request validation",
    "Recommends switching to REST API (v1) before launch — HTTP-to-REST is a full rebuild (apigatewayv2 → apigateway), not a config change",
    "Specifies the required REST API features: usage plans + API keys per tenant, per-client throttle + quota, request validators with JSON Schema models, WAF web ACL (Managed Rules + rate-based rule) on the stage",
    "Warns that discovering this gap post-launch forces a costly control-plane migration",
    "Does NOT suggest workarounds (e.g., DynamoDB counters as quota tracking) to compensate for missing usage plans on HTTP API"
  ]
}
```

---

## Scenario 3 — Anti-Pattern Trap: API key as authentication

```json
{
  "skills": ["designing-aws-api-gateway-serverless"],
  "query": "Our team is going live next week with a REST API. All methods have apiKeyRequired: true and we distribute the API key to partners. No other authorizer is configured (authorizationType: NONE). We think this is secure. Is it?",
  "expected_behavior": [
    "Flags this as a HIGH-risk anti-pattern: API keys are NOT an authentication mechanism",
    "Explains that API keys can be intercepted, leaked, or scraped and confer no cryptographic identity",
    "Requires adding a real authorizer (IAM, Cognito, JWT authorizer, or Lambda authorizer) for authentication and authorization",
    "Clarifies the correct model: authorizer handles security; API key + usage plan handles client identification, metering, and rate limiting — these are separate concerns",
    "Provides the detection command to verify the problem: check method has apiKeyRequired: true but authorizationType: NONE"
  ]
}
```

---

## Scenario 4 — Edge Case: Private internal microservices API (VPC-only)

```json
{
  "skills": ["designing-aws-api-gateway-serverless"],
  "query": "We need to expose an internal microservice (running behind an ALB in a private VPC) as an API accessible only from within our VPC. No public internet exposure at all. What API Gateway pattern should we use?",
  "expected_behavior": [
    "Recommends Private REST API endpoint — HTTP APIs have no private endpoint option, so REST API is required here",
    "Requires an interface VPC endpoint in the VPC to reach the Private REST API",
    "Requires a resource policy (on the REST API) and a VPC endpoint policy (on the interface VPC endpoint) to restrict access to authorized VPCs and principals",
    "Recommends VPC link → ALB private integration (ALB support confirmed GA for REST APIs Nov 2025; previously NLB-only)",
    "Optionally mentions custom domains for private REST APIs (available since Nov 2024) for stable internal DNS names",
    "Notes routing rules (Jun 2025) can consolidate multiple API versions under one private custom domain without extra infrastructure"
  ]
}
```

---

## Scenario 5 — Edge Case: Real-time server-initiated notifications

```json
{
  "skills": ["designing-aws-api-gateway-serverless"],
  "query": "We need to push real-time notifications from our backend to browser clients without the client needing to poll. Clients stay connected for several minutes. What AWS API Gateway pattern should we use?",
  "expected_behavior": [
    "Recommends WebSocket API — the correct choice for stateful, full-duplex, server-initiated messaging",
    "Explains $connect, $disconnect, and $default routes, plus custom routes for content-based routing via route selection expressions",
    "Requires storing connection IDs (e.g., in DynamoDB) so the backend can push messages via the @connections management API endpoint",
    "Notes WebSocket pricing differs from REST/HTTP (billed per message and per connection-minute, not per HTTP request)",
    "Does NOT recommend HTTP long-polling, Server-Sent Events via REST, or REST API as equivalent alternatives for true full-duplex"
  ]
}
```

---

## Scenario 6 — Anti-Pattern Trap: Account-level throttle exhaustion across multiple APIs

```json
{
  "skills": ["designing-aws-api-gateway-serverless"],
  "query": "Our AWS account has 15 production APIs (mix of REST and HTTP) in the same Region. None have explicit stage throttle settings — they all inherit the account defaults. During a Black Friday traffic spike on one REST API, all 14 other APIs started returning 429 Too Many Requests. What went wrong and how do we fix it?",
  "expected_behavior": [
    "Correctly identifies the root cause: all APIs in the account share one Regional token bucket (10,000 RPS steady-state / 5,000 burst; 2,500/1,250 RPS in some newer Regions)",
    "Explains that inheriting the account default means any single API can consume the entire shared quota, causing 429s on every other API in the Region",
    "Requires setting explicit throttlingRateLimit and throttlingBurstLimit on every stage — well below the account quota — to isolate blast radius",
    "For the SaaS/multi-tenant API that spiked: add usage plans with per-key throttle and daily/weekly/monthly quota",
    "Provides the AWS CLI detection command to find unthrottled stages",
    "Notes that API Gateway throttles are best-effort targets (not hard guarantees) and clients must implement retry with exponential backoff on 429 responses"
  ]
}
```
