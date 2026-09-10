---
name: designing-aws-api-gateway-serverless
description: "Architects AWS API Gateway serverless patterns (REST, HTTP, WebSocket) for Lambda-backed APIs. Use when designing, reviewing, or implementing API Gateway as the front door for serverless workloads — covering API type selection, authorization, throttling, WAF, TLS, observability, and private integrations."
---

## Function
Specialist in AWS API Gateway serverless architecture patterns — REST API (v1), HTTP API (v2), and WebSocket API — covering API type selection, authorization strategies, throttling, WAF, TLS security, observability, and private/VPC integrations.

## Version Context

**Technology**: Amazon API Gateway (AWS managed service)
**Target edition**: AWS API Gateway 2026 (GA feature set as of 2026-08-28; upstream Developer Guide last updated 2025-12-02)
**Release cadence**: Continuously delivered managed service — no semantic version number
**Support status**: Active (all three products: REST API, HTTP API, WebSocket API)
**Currency threshold**: Review after 2027-08-28

**Key 2025 additions** (confirmed against Document history, last updated 2025-12-02):
- Routing rules for REST APIs on custom domains (Jun 2025) — header/base-path dynamic routing
- Dual-stack IPv4/IPv6 endpoints for REST, HTTP, WebSocket, and custom domains (Mar 2025, no extra charge)
- SIGv4a signing support for REST APIs (Aug 2025) — multi-Region request signing
- Fully-managed API Gateway Portal with interactive "Try it" and portal products (Nov 2025)
- Response streaming for REST API proxy integrations (Nov 2025)
- Private integrations with ALB for REST APIs (Nov 2025 — previously NLB-only for REST)
- Enhanced TLS security policies incl. `SecurityPolicy_TLS13_1_3` (Nov 2025)
- REST API as target for Amazon Bedrock AgentCore Gateway / MCP (Dec 2025)

**Deprecated**: Self-hosted serverless developer portal (superseded by managed API Gateway Portal, Nov 2025)

⚠️ **CRITICAL — Agent Warning**:
This skill targets the AWS API Gateway 2026 feature set.
REST API (v1) and HTTP API (v2) use different control-plane APIs (`apigateway` vs `apigatewayv2`).
Switching between REST and HTTP is a full rebuild — never treat them as equivalent or interchangeable.
Reject any pattern that conflates the two API types.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Mandatory patterns, decision points, and anti-patterns
- **[Integration Patterns](#integration-patterns)** — Cloud-native design patterns and reference architectures
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands and expected output
- **[Quick Reference](#quick-reference)** — API type feature matrix and critical account limits
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 LLM-as-judge test scenarios
- **[External Resources](#external-resources)** — Official AWS documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**1. HTTPS/TLS with a modern security policy on every custom domain**
Apply a custom domain with an ACM certificate. Set the minimum TLS security policy to `TLS_1_2`; use `SecurityPolicy_TLS13_1_3` for regulated workloads (enhanced policies GA 2025-11-19 for REST/custom domains).
```bash
aws apigateway get-domain-name --domain-name <domain> --query 'securityPolicy'
# Expected: "TLS_1_2" or enhanced TLS 1.3 policy name
```
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-security-policies.html (2026-08-28)

**2. Authorizer on every production route — never `authorizationType: NONE`**
Choose the least-code authorizer: JWT authorizer (HTTP API + OIDC/OAuth), Cognito user pools (managed IdP), IAM/SigV4a (service-to-service; SigV4a for multi-Region since Aug 2025), Lambda authorizer (custom logic or REST API + JWT). Enable authorizer result caching (TTL) to reduce latency and invocation cost.
```bash
# Verify (REST API)
aws apigateway get-method --rest-api-id <id> --resource-id <r> --http-method <m> \
  --query 'authorizationType'
# Expected: not "NONE" on production routes
```
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html (2026-08-28)

**3. Stage/method + per-client throttling explicitly set below the account-level quota**
The account-level Regional throttle (10,000 RPS / 5,000 burst; 2,500 / 1,250 in some newer Regions) is shared across ALL APIs in the account per Region. Without explicit limits, one API can exhaust the shared bucket. Application order: per-client/per-method (usage plan) → per-method (stage) → account → AWS Regional.
```bash
aws apigateway get-stage --rest-api-id <id> --stage-name <s> \
  --query 'methodSettings."*/*".{rate:throttlingRateLimit,burst:throttlingBurstLimit}'
# Expected: numeric values, not null
```
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html (2026-08-28)

**4. JSON access logging to CloudWatch Logs + detailed metrics + alarms (and X-Ray for REST)**
Enable JSON access logging with `$context` variables; enable detailed CloudWatch metrics (namespace `AWS/ApiGateway`); alarm on `5XXError`, `4XXError`, `Latency` p99, and throttle `Count`. Enable X-Ray active tracing on REST API stages for latency triage. Access logs and X-Ray are not available on HTTP API stages.
```bash
aws apigateway get-stage --rest-api-id <id> --stage-name <s> \
  --query '{logs:accessLogSettings,xray:tracingEnabled}'
# Expected: destinationArn present; tracingEnabled: true (REST)
```
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (2026-08-28)

**5. AWS WAF web ACL on every internet-facing REST API stage; CloudFront+WAF for public HTTP APIs**
WAF cannot attach directly to an HTTP API endpoint. For HTTP APIs needing WAF protection, place Amazon CloudFront in front and attach the web ACL there. REST APIs: attach a WAF web ACL (AWS Managed Rules baseline + rate-based rule) directly to the stage.
```bash
aws apigateway get-stage --rest-api-id <id> --stage-name <s> --query 'webAclArn'
# Expected: a WAF web ACL ARN (not empty)
```
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html (2026-08-28)

**6. Request validation at the gateway for REST API write endpoints**
Attach an API Gateway request validator (params + body, JSON Schema model) to all POST/PUT/PATCH endpoints to reject malformed requests before Lambda is invoked, reducing cost and surface area. HTTP APIs do not support request validation — validate inside the Lambda or backend instead.
```bash
aws apigateway get-request-validators --rest-api-id <id>
# Expected: non-empty list; each write method references a validator ID
```
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-method-request-validation.html (2026-08-28)

### ⚠️ Ask First

**1. API type: HTTP API (v2) vs REST API (v1) vs WebSocket API**
This is largely irreversible (different control-plane APIs; switching = rebuild). Ask before defaulting:
"Does this API require API keys/usage plans, per-client throttling, request validation, response caching, WAF-direct, private or edge-optimized endpoints, or X-Ray?"

| Option | Cost | Unique Features | Key Gaps |
|--------|------|-----------------|----------|
| HTTP API (v2) | ~71% lower | Native JWT, CORS, auto-deploy, OIDC | No API keys, WAF-direct, caching, validation, private/edge, X-Ray |
| REST API (v1) | Baseline | API keys, WAF, caching, validation, private, edge, X-Ray, routing rules | Higher cost and config surface |
| WebSocket API | Per msg + conn-min | Stateful full-duplex, content routing | Not request/response; different pricing model |

Decision rule: "Any REST-only feature required → REST API. Real-time bidirectional → WebSocket. Otherwise → HTTP API (default)."
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (2026-08-28)

**2. Endpoint type: Edge-optimized vs Regional vs Private**
HTTP APIs are Regional only — no edge-optimized or private endpoint options.
Ask: "Are consumers global/public (→ edge-optimized REST, or Regional HTTP+CloudFront), in-Region (→ Regional), or internal-only (→ Private REST + interface VPC endpoint)?"
Private custom domains for REST APIs are supported since Nov 2024; routing rules (Jun 2025) can consolidate versions on one private domain.
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-endpoint-types.html (2026-08-28)

**3. Authorizer strategy: IAM vs Cognito vs JWT vs Lambda**
Ask: "Is the caller an AWS principal (→ IAM/SigV4a), a user from a managed pool (→ Cognito), a standard OIDC/OAuth JWT on an HTTP API (→ JWT authorizer), or custom/opaque logic or a JWT on a REST API (→ Lambda authorizer with result caching)?"
Cost consideration: IAM/Cognito/JWT add no per-request Lambda cost; Lambda authorizer adds invocations mitigated by TTL caching.

**4. Backend integration: Lambda proxy vs direct AWS-service vs private VPC link vs HTTP proxy**
Ask: "Is there real business logic (→ Lambda proxy), a simple AWS-service pass-through (→ direct integration: DynamoDB / SQS / Step Functions / EventBridge), a private VPC backend (→ VPC link + NLB / ALB / Cloud Map; REST now supports ALB since Nov 2025), or an existing public API (→ HTTP proxy)?"
Direct AWS-service integration removes Lambda invocation cost; VTL mapping complexity (REST) is the trade-off.

### 🚫 Never Do

| Anti-Pattern | Risk | Correct Alternative |
|---|---|---|
| Public production endpoint with `authorizationType: NONE`, default stage throttle, no WAF | CRITICAL — data breach, account-wide 429s, cost overrun | Authorizer + explicit stage throttle + WAF web ACL (REST) or CloudFront+WAF (HTTP) |
| HTTP API for a workload that genuinely needs API keys, usage plans, request validation, caching, WAF-direct, or private/edge endpoint | HIGH — forces a full rebuild post-launch (apigatewayv2 → apigateway) | Apply the Ask-First decision table before committing; choose REST API upfront |
| Stage throttle left at account default across multiple production APIs in one Region | HIGH — one traffic spike can exhaust the shared 10,000 RPS / 5,000 burst bucket and 429 every other API | Set `throttlingRateLimit` / `throttlingBurstLimit` explicitly on every stage |
| API key as authentication (`apiKeyRequired: true` with `authorizationType: NONE`) | HIGH — API keys can leak and confer no cryptographic identity | Authorizer for security + API key + usage plan for metering — they are separate concerns |
| Production stage with no access logs, no CloudWatch alarms, no X-Ray (REST) | MEDIUM — error and latency triage is guesswork; SLA breaches go undetected | JSON access logs to CloudWatch Logs + alarms on 5XX/4XX/Latency p99 + X-Ray active tracing (REST) |
| Secrets or credentials in integration config, VTL mapping templates, or stage variables (plaintext) | CRITICAL — leak via CloudFormation exports and source control | Store in AWS Secrets Manager / SSM Parameter Store (SecureString); fetch at runtime via Lambda execution role |

---

## Integration Patterns

**API Gateway + Lambda "front door"** (synchronous, the core serverless pattern)
HTTP API (default) or REST API → Lambda proxy integration + authorizer + stage throttling + CloudWatch + X-Ray (REST). The backend owns routing and response shaping. Add CloudFront+WAF for HTTP APIs needing web protection.

**Lambda-less direct service integration** (high-volume pass-through)
API Gateway → DynamoDB / SQS / Step Functions / EventBridge. Removes Lambda invocation cost and cold starts from the hot path. Use VTL mapping templates (REST) or AWS-service integration. Best for simple CRUD or enqueue operations with no business logic.

**Async ingestion via SQS/EventBridge** (queue-based load leveling)
API Gateway direct integration → SQS or EventBridge; consumers drain asynchronously. Returns `202 Accepted`. Add a DLQ for poison messages and require idempotent consumers. Absorbs spiky write traffic without exhausting Lambda concurrency or API throttle.

**Response caching** (REST only)
REST API stage cache (dedicated per-hour instance, TTL-based). Only GET cached by default — safe for reads. Combine with gzip content encoding. Justified when cache hit rate offsets the instance cost.

**Canary release deployments** (REST only)
REST API stage canary: route N% of traffic to the new deployment with separate logs/metrics. Promote or roll back without DNS changes. REST-only feature.

**WebSocket API + DynamoDB connection store** (real-time bidirectional)
WebSocket API with `$connect` / `$disconnect` / `$default` + custom routes. Store connection IDs in DynamoDB; push via the `@connections` management API endpoint. Use for chat, live dashboards, collaborative editing, and notifications.

**Private internal microservices API**
Private REST API + interface VPC endpoint + resource/endpoint policies + VPC link → ALB (Nov 2025) / NLB / Cloud Map. Traffic stays on the AWS network. Combine with routing rules (Jun 2025) to consolidate API versions under one private custom domain.

**Multi-Region DNS failover**
Two Regional REST APIs (primary/secondary Regions) + Route 53 health checks + failover routing. SigV4a (Aug 2025) simplifies multi-Region request signing. RTO = minutes (DNS TTL-bound); RPO depends on backend data replication.

---

## Verification Loop

Run after any API Gateway configuration or IaC change:

### 1. Security posture
```bash
# Authorizer must not be NONE on production routes (REST)
aws apigateway get-method --rest-api-id <id> --resource-id <r> \
  --http-method <m> --query 'authorizationType'

# WAF web ACL must be attached (REST)
aws apigateway get-stage --rest-api-id <id> --stage-name prod --query 'webAclArn'

# TLS policy on custom domain
aws apigateway get-domain-name --domain-name api.example.com --query 'securityPolicy'
```

### 2. Throttling configuration
```bash
# Stage throttle must be explicitly set — not null
aws apigateway get-stage --rest-api-id <id> --stage-name prod \
  --query 'methodSettings."*/*".{rate:throttlingRateLimit,burst:throttlingBurstLimit}'
```

### 3. Observability
```bash
# Access logs destination must be present
aws apigateway get-stage --rest-api-id <id> --stage-name prod \
  --query 'accessLogSettings.destinationArn'

# X-Ray active tracing (REST)
aws apigateway get-stage --rest-api-id <id> --stage-name prod --query 'tracingEnabled'
# Expected: true
```

### 4. Request validation (REST)
```bash
aws apigateway get-request-validators --rest-api-id <id>
# Expected: non-empty list; each write method must reference a validator ID
```

**Troubleshooting**:
- Multiple unrelated APIs returning `429` simultaneously → account-level quota exhausted; add explicit per-stage throttle to every stage
- Authorizer adding latency → enable authorizer result caching with an appropriate TTL (up to 3,600s)
- WAF rules blocking CloudFront → confirm WAF is associated at CloudFront distribution, not at the HTTP API stage (HTTP APIs do not support direct WAF attachment)
- Security policy still `TLS_1_0` → `aws apigateway update-domain-name --domain-name <d> --patch-operations op=replace,path=/securityPolicy,value=TLS_1_2`

---

## Quick Reference

**API type feature matrix**:

| Feature | HTTP API (v2) | REST API (v1) | WebSocket |
|---------|:---:|:---:|:---:|
| Native JWT authorizer | Yes | No (use Lambda auth) | No |
| API keys + usage plans | No | Yes | No |
| Per-client throttling | No | Yes (usage plans) | No |
| Request validation | No | Yes | No |
| Response caching | No | Yes | No |
| WAF direct attach | No (use CloudFront) | Yes | No |
| Private endpoint | No | Yes | No |
| Edge-optimized endpoint | No | Yes | No |
| X-Ray active tracing | No | Yes | No |
| Execution logs | No | Yes | No |
| Routing rules (2025) | No | Yes | No |
| Cost vs REST | ~71% lower | Baseline | Per msg + conn-min |

**Critical account-level limits** (per Region):

| Quota | Default | Newer Regions |
|-------|---------|---------------|
| Account throttle (steady-state RPS) | 10,000 | 2,500 |
| Account burst (token bucket) | 5,000 | 1,250 |
| Stage/method throttle | Inherits account | Must set explicitly |
| Lambda authorizer result cache TTL max | 3,600s | — |
| Integration timeout (max) | 29s | — |

**2025 features — confirm Regional GA before committing**:
- Bedrock AgentCore Gateway REST target (Dec 2025)
- API Gateway Portal (Nov 2025)

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/designing-aws-api-gateway-serverless/
├── SKILL.md                           <- This file (guardrails + patterns + verification)
└── blueprints/
    └── evaluation-scenarios.md        <- 6 LLM-as-judge test scenarios
```

---

## External Resources

### Official Documentation
- [What is Amazon API Gateway?](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html) — Developer Guide entry point (Dec 2025 edition)
- [Choose between REST APIs and HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html) — Primary decision matrix; feature comparison tables
- [Amazon API Gateway quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html) — Account-level throttle numbers (authoritative)
- [Document history (changelog)](https://docs.aws.amazon.com/apigateway/latest/developerguide/history.html) — Updated 2025-12-02; source for all 2025 feature dates

### Security and Best Practices
- [Control and manage access to REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html) — Authorizer selection guide
- [Throttle requests to REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html) — Token bucket algorithm and application order
- [Use AWS WAF to protect REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html) — WAF integration for REST APIs
- [Security policies for REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-security-policies.html) — TLS version enforcement (updated 2025-11-19)
- [Request validation for REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-method-request-validation.html) — JSON Schema validators
- [Well-Architected Serverless Lens — API Gateway](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/amazon-api-gateway-2.html) — Architecture best practices
- [Best Practices for Private APIs (Whitepaper)](https://docs.aws.amazon.com/whitepapers/latest/best-practices-api-gateway-private-apis-integration/rest-api.html) — Private integration patterns

### 2025 Feature Announcements
- [Routing rules for REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-routing-rules.html) — Header/base-path dynamic routing (Jun 2025)
- [Dual-stack IPv4/IPv6 endpoints blog](https://aws.amazon.com/blogs/aws/amazon-api-gateway-now-supports-dual-stack-ipv4-and-ipv6-endpoints/) — Mar 2025
- [New API Gateway Portal blog](https://aws.amazon.com/blogs/compute/improve-api-discoverability-with-the-new-amazon-api-gateway-portal/) — Nov 2025
