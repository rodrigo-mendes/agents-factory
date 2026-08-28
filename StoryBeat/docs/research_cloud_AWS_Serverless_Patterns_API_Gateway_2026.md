# Cloud Architecture Research — AWS Serverless Patterns: API Gateway

## Metadata
```yaml
Full_Name: "AWS Serverless Patterns — Amazon API Gateway"
Cloud_Provider: "AWS"
Architecture_Domain: "Serverless Patterns - API Gateway"
Target_Edition: "AWS API Gateway 2026"
Architecture_Context: "Serverless / event-driven APIs (Lambda + API Gateway front door)"
Official_Source_URL: "https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-28"
Currency_Threshold: "2027-08-28 — review after this date; AWS API Gateway ships features monthly"
Research_Depth: exhaustive
Docs_Last_Updated_Upstream: "2025-12-02 (Document history page)"
Triangulation: "Developer Guide + Well-Architected Serverless Lens + Service Quotas + AWS What's New announcements"
```

> ⚠️ **Version pinning note.** This research is pinned to the **AWS API Gateway service state as documented on 2026-08-28** (upstream docs last updated 2025-12-02). API Gateway has **no semantic version number** — it is a continuously-delivered managed service. "AWS API Gateway 2026" here means the GA feature set current as of the research date. Any pattern that depends on a feature GA'd after 2025-12-02 is flagged inline.

---

## Executive Summary

Amazon API Gateway is AWS's managed "front door" service for creating, publishing, securing, monitoring, and throttling **REST**, **HTTP**, and **WebSocket** APIs at scale. Within the serverless architecture practice it is the app-facing tier that pairs with AWS Lambda to form the core of AWS serverless infrastructure — handling authorization, access control, traffic management, and API versioning so that backend compute (Lambda, containers behind an NLB/ALB, or direct AWS service integrations) does not have to. The central architecture decision an architect makes here is **API type selection**: REST API (v1, feature-rich), HTTP API (v2, ~71% cheaper / ~60% lower latency but minimal features), or WebSocket API (stateful, full-duplex). This choice is largely irreversible without a rebuild, so it is an Ask-First crossroads, not a default.

**What changed for the 2026 edition** (all confirmed against the official Document history, last updated 2025-12-02): (1) **Routing rules for REST APIs** (Jun 2025) — dynamic routing on host header, base path, or both, across a custom domain; (2) **Dual-stack IPv4/IPv6 endpoints** for REST, HTTP, and WebSocket APIs and custom domains (Mar 2025, no extra charge); (3) **SIGv4a** signing support for REST APIs (Aug 2025), enabling multi-Region signing; (4) a **fully-managed API Gateway Portal / developer portals** with portal products and interactive "Try it" (Nov 2025) — replacing the old self-hosted serverless developer portal; (5) **response streaming for REST API proxy integrations** (Nov 2025); (6) **private integrations with Application Load Balancers for REST APIs** (Nov 2025 — previously NLB-only for REST); (7) **enhanced TLS security policies for REST APIs and custom domains** including `SecurityPolicy_TLS13_1_3` (Nov 2025); and (8) **REST API as a target for Amazon Bedrock AgentCore Gateway / MCP** (Dec 2025), exposing existing REST APIs to AI agents.

**The three most critical guardrails for a serverless API context are:** (1) **default to HTTP APIs** for new Lambda-backed JSON APIs unless a REST-only feature (API keys/usage plans, per-client throttling, request validation, WAF, response caching, private endpoints, edge-optimized, X-Ray) is genuinely required — this is a first-order cost and latency decision; (2) **never expose a production API without an authorizer + throttling + (for REST) AWS WAF** — public unauthenticated, unthrottled endpoints are the top anti-pattern; and (3) **treat the account-level 10,000 RPS Regional throttle (2,500 RPS in some newer Regions) with a 5,000-request burst bucket as a shared, finite resource** — configure stage/method and per-client throttling so one API cannot starve every other API in the account/Region.

---

## Cloud Architecture Glossary

```
Term: REST API (API Gateway v1)
Definition: The original, feature-rich API Gateway product. HTTP-based, stateless, supports API keys, usage plans, request validation, caching, WAF, private endpoints, edge-optimized endpoints, X-Ray, and mock/AWS-service/HTTP/Lambda integrations.
Provider Docs Section: "Choose between REST APIs and HTTP APIs" (http-api-vs-rest.html)
Architect Usage: Choose when you need any REST-only feature. Governed by the apigateway (v1) API.
Common Confusion: Confused with HTTP API — both are "RESTful", but HTTP API is the newer, cheaper, minimal-feature product, NOT the same thing.
```
```
Term: HTTP API (API Gateway v2)
Definition: A newer, minimal-feature API product designed for the lowest price and latency. Native JWT authorizer, built-in CORS, automatic deployments, OIDC/OAuth 2.0.
Provider Docs Section: "API Gateway HTTP APIs" (http-api.html)
Architect Usage: Default for new serverless JSON APIs fronting Lambda or an ALB/NLB when advanced management is not required. Governed by the apigatewayv2 API.
Common Confusion: The name implies it is "just HTTP" — but REST APIs are also HTTP-based. The real distinction is feature set + price, not protocol.
```
```
Term: WebSocket API
Definition: A stateful, full-duplex API adhering to RFC 6455, routing inbound messages by content via route selection expressions ($connect, $disconnect, $default, custom routes).
Provider Docs Section: "Overview of WebSocket APIs" (apigateway-websocket-api-overview.html)
Architect Usage: Real-time bidirectional workloads — chat, live dashboards, collaborative editing, notifications.
Common Confusion: Confused with HTTP/REST long-polling; WebSocket maintains a persistent connection with connection IDs, billed per message + connection-minute.
```
```
Term: Endpoint type (Edge-optimized / Regional / Private)
Definition: Where API Gateway terminates the API. Edge-optimized routes via CloudFront edge locations (REST only). Regional terminates in-Region (REST + HTTP). Private is only reachable via an interface VPC endpoint (REST only).
Provider Docs Section: "API endpoint types for REST APIs" (api-gateway-api-endpoint-types.html)
Architect Usage: Edge-optimized for globally-distributed public clients; Regional for in-Region clients or when fronting your own CloudFront; Private for internal-only APIs.
Common Confusion: HTTP APIs do NOT support edge-optimized or private endpoints — Regional only.
```
```
Term: Proxy integration (Lambda proxy / HTTP proxy)
Definition: A streamlined integration that passes the entire request to the backend and returns its response with minimal mapping. {proxy+} greedy path + ANY method is the catch-all form.
Provider Docs Section: "Set up a proxy integration" (api-gateway-set-up-simple-proxy.html)
Architect Usage: Default integration for Lambda-backed APIs — backend owns routing/response shaping.
Common Confusion: Confused with non-proxy (custom) integration, which uses VTL mapping templates (REST only) to transform request/response.
```
```
Term: Lambda authorizer (formerly "custom authorizer")
Definition: A Lambda function that authorizes API calls using bearer tokens (TOKEN type) or request parameters (REQUEST type), returning an IAM policy (REST) or simple allow/deny + context (HTTP).
Provider Docs Section: "Use API Gateway Lambda authorizers" (apigateway-use-lambda-authorizer.html)
Architect Usage: Custom auth logic (opaque tokens, third-party IdPs, fine-grained context). Cache authorizer results by TTL to reduce cost/latency.
Common Confusion: Confused with Cognito/JWT authorizers, which are managed and require no custom code for standard OIDC/OAuth.
```
```
Term: JWT authorizer
Definition: A native (no-code) HTTP-API authorizer that validates JSON Web Tokens from any OIDC/OAuth 2.0 issuer, including Amazon Cognito, against configured issuer + audience.
Provider Docs Section: "JWT authorizers for HTTP APIs" (http-api-jwt-authorizer.html)
Architect Usage: The preferred HTTP API auth for OIDC/OAuth. For REST APIs, use a Lambda authorizer to validate JWTs instead (REST has no native JWT authorizer).
Common Confusion: JWT authorizer is HTTP-API-only; REST APIs cannot use it natively.
```
```
Term: Usage plan + API key
Definition: A REST-only construct that meters and rate-limits API access per client, keyed by an API key, with configurable throttle (rate/burst) and quota (requests per day/week/month).
Provider Docs Section: "Usage plans and API keys for REST APIs" (api-gateway-api-usage-plans.html)
Architect Usage: SaaS tiering, partner APIs, per-tenant rate limiting, AWS Marketplace metering.
Common Confusion: API keys are NOT an authentication mechanism — they identify/meter a client but must be combined with an authorizer for security.
```
```
Term: Token bucket throttling (rate + burst)
Definition: Algorithm API Gateway uses to throttle: "rate" = tokens added per second (steady-state RPS); "burst" = max bucket capacity (concurrent requests). Exceeding either returns 429 Too Many Requests.
Provider Docs Section: "Throttle requests to your REST APIs" (api-gateway-request-throttling.html)
Architect Usage: Set stage/method and per-client throttles below the account limit to isolate blast radius.
Common Confusion: Throttles are best-effort targets, not hard guarantees — treat 429s as expected and implement client retry with backoff.
```
```
Term: Private integration + VPC link
Definition: Integration to resources inside a VPC (NLB, ALB, Cloud Map) without exposing them publicly, via a VpcLink resource.
Provider Docs Section: "Set up a private integration" (set-up-private-integration.html)
Architect Usage: Front private microservices behind an ALB/NLB. REST now supports ALB private integration (Nov 2025); HTTP APIs also support Cloud Map.
Common Confusion: "Private integration" (backend in VPC) is different from "Private API endpoint" (API only reachable from a VPC).
```
```
Term: Routing rules for REST APIs (2025)
Definition: Rules attached to a custom domain that dynamically route requests to different API stages based on HTTP header values, URL base path, or a combination.
Provider Docs Section: "Routing rules ... for REST APIs" (rest-api-routing-rules.html)
Architect Usage: Header-based versioning, blue/green at the domain layer, multi-API consolidation under one domain. Works on public AND private REST APIs.
Common Confusion: Different from WebSocket/HTTP route selection expressions and from base path mappings — routing rules are richer and header-aware.
```
```
Term: Mutual TLS (mTLS)
Definition: Two-way TLS where the client also presents a certificate, validated against an uploaded trust store (CA bundle in S3). Supported on REST and HTTP custom domains.
Provider Docs Section: "Configuring mutual TLS authentication" (rest-api-mutual-tls.html)
Architect Usage: B2B/partner and IoT APIs requiring strong client identity at the transport layer.
Common Confusion: mTLS requires a custom domain name and disabling the default execute-api endpoint; it is not automatic.
```
```
Term: Security policy (TLS version)
Definition: The minimum TLS version/cipher suite enforced on a custom domain. As of Nov 2025, enhanced policies including SecurityPolicy_TLS13_1_3 are available for REST APIs and custom domains; TLS 1.3 (Feb 2024) supported on Regional REST/HTTP/WebSocket.
Provider Docs Section: "Security policies for REST APIs" (apigateway-security-policies.html)
Architect Usage: Enforce TLS 1.2 minimum (TLS 1.3 for regulated workloads) on all custom domains.
Common Confusion: Security policy applies to custom domains; the default execute-api endpoint has its own AWS-managed TLS.
```
```
Term: Dual-stack (IPv4/IPv6) endpoint (2025)
Definition: An endpoint IP address type that accepts both IPv4 and IPv6 clients, available for REST, HTTP, WebSocket APIs and custom domains at no extra charge.
Provider Docs Section: "IP address types" (api-gateway-ip-address-type.html)
Architect Usage: Required for IPv6-only clients and some public-sector/telecom mandates.
Common Confusion: Not the default on older APIs — must be explicitly configured.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**HTTPS/TLS-only with a modern security policy**
- Pillar Alignment: Security
- Why: API Gateway mandates TLS for all endpoints; regulated workloads should enforce modern cipher suites/TLS versions. `[✓✓ Triangulated | Serverless Lens security guidance + Document history "Security policies for REST APIs" 2025-11-19]`
- AWS Services: API Gateway custom domain + ACM certificate + security policy (`SecurityPolicy_TLS13_1_3` or TLS 1.2 minimum)
- Architecture Decision: Terminate on a custom domain with an ACM cert; set the minimum TLS security policy to TLS 1.2 (TLS 1.3 for regulated workloads, GA on Regional REST/HTTP/WebSocket since 2024-02-15, enhanced policies since 2025-11-19).
- Verification: `aws apigateway get-domain-name --domain-name <d> --query 'securityPolicy'` → expect `TLS_1_2` or the enhanced 1.3 policy.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-security-policies.html (accessed 2026-08-28)

**Authorizer on every production route**
- Pillar Alignment: Security
- Why: Access control is a foundational best practice; API Gateway supports IAM, resource policies, Lambda authorizers, Cognito user pools, and (HTTP) native JWT. `[✓✓ Triangulated | "Control and manage access to REST APIs" + http-api-vs-rest.html authorization table]`
- AWS Services: IAM / Amazon Cognito user pools / JWT authorizer (HTTP) / Lambda authorizer
- Architecture Decision: Choose the least-code authorizer that fits — JWT authorizer (HTTP + OIDC), Cognito (managed user pools), IAM (service-to-service / SIGv4, and SIGv4a since 2025-08-19 for multi-Region), Lambda authorizer only when custom logic is required. Enable authorizer result caching (TTL) to cut latency and invocations.
- Verification: `aws apigateway get-method --rest-api-id <id> --resource-id <r> --http-method <m> --query 'authorizationType'` → expect not `NONE` (except intentional public/CORS-preflight routes).
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html (accessed 2026-08-28)

**Stage/method + per-client throttling to protect the account-level quota**
- Pillar Alignment: Reliability, Performance Efficiency
- Why: The account-level throttle (10,000 RPS steady-state, 5,000 burst; 2,500 RPS / 1,250 burst in some newer Regions) is shared across ALL HTTP, REST, WebSocket APIs in the account per Region. Without per-API limits, one API can starve every other. `[✓✓ Triangulated | "Amazon API Gateway quotas" limits.html + "Throttle requests" api-gateway-request-throttling.html]`
- AWS Services: API Gateway stage/method throttling + usage plans (REST) for per-client limits
- Architecture Decision: Set stage-level (and, where needed, method-level) rate/burst below the account limit. For multi-tenant/SaaS, add usage plans with per-key throttle + daily/weekly/monthly quota. Order of application: per-client/per-method (usage plan) → per-method (stage) → account → AWS Regional.
- Verification: `aws apigateway get-stage --rest-api-id <id> --stage-name <s> --query 'methodSettings'` → confirm `throttlingRateLimit`/`throttlingBurstLimit` are set (not defaulting to account max).
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html (accessed 2026-08-28)

**Structured access logging + CloudWatch metrics (and X-Ray for REST)**
- Pillar Alignment: Operational Excellence
- Why: API Gateway supports CloudWatch metrics + access/execution logs for both types, plus X-Ray tracing and Firehose access logs for REST only. Observability is a Serverless Lens core practice. `[✓✓ Triangulated | http-api-vs-rest.html monitoring table + welcome.html features list]`
- AWS Services: CloudWatch Logs (access + execution), CloudWatch metrics (`AWS/ApiGateway`), AWS X-Ray (REST), Amazon Data Firehose (REST access logs)
- Architecture Decision: Enable JSON access logging with `$context` variables to CloudWatch Logs; enable detailed CloudWatch metrics; enable X-Ray active tracing on REST APIs for latency triage. Alarm on `5XXError`, `4XXError`, `Latency` p99, and `Count`.
- Verification: `aws apigateway get-stage ... --query 'accessLogSettings'` returns a destinationArn + format; CloudWatch shows the `AWS/ApiGateway` namespace.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (accessed 2026-08-28)

**AWS WAF in front of production REST APIs (and public-facing HTTP APIs via CloudFront)**
- Pillar Alignment: Security
- Why: WAF protects against common web exploits; it is natively supported on REST APIs. `[✓✓ Triangulated | http-api-vs-rest.html security table (WAF: REST Yes / HTTP No) + welcome.html "Integration with AWS WAF"]`
- AWS Services: AWS WAF web ACL associated with the REST API stage; for HTTP APIs, front with Amazon CloudFront + WAF (WAF cannot attach directly to an HTTP API).
- Architecture Decision: Attach a WAF web ACL (AWS Managed Rules baseline + rate-based rule) to every internet-facing REST API stage. For HTTP APIs needing WAF, put CloudFront in front and attach WAF at CloudFront.
- Verification: `aws wafv2 list-resources-for-web-acl` or `aws apigateway get-stage ... --query 'webAclArn'` returns an ARN.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html (accessed 2026-08-28)

**Request validation at the gateway for REST APIs**
- Pillar Alignment: Security, Reliability
- Why: REST APIs can validate required parameters and JSON body schema before invoking the backend, rejecting malformed requests at the edge and reducing Lambda invocations. (REST-only feature.) `[✓✓ Triangulated | http-api-vs-rest.html development table + "Request validation" api-gateway-method-request-validation.html]`
- AWS Services: API Gateway request validators + models (JSON Schema)
- Architecture Decision: Attach a validator (params + body) to write endpoints. Note: HTTP APIs do NOT support request validation — validate in the Lambda/backend instead.
- Verification: `aws apigateway get-request-validators --rest-api-id <id>` returns validators; methods reference them.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-method-request-validation.html (accessed 2026-08-28)

### ⚠️ Architectural Decisions

**API type: REST vs HTTP vs WebSocket**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | HTTP API (v2) | API Gateway HTTP API | ~71% lower cost, ~60% lower latency, native JWT, auto-deploy, built-in CORS | No API keys/usage plans, no per-client throttling, no request validation, no WAF (direct), no caching, no private endpoint, no edge-optimized, no X-Ray, no execution logs, no mock/response-streaming | New serverless JSON APIs over Lambda/ALB/NLB; OIDC/OAuth auth; cost/latency sensitive |
  | REST API (v1) | API Gateway REST API | API keys + usage plans, per-client throttling, request validation, caching, WAF, private + edge-optimized endpoints, X-Ray, mock, response streaming, VTL transforms, routing rules | Higher price + latency; more config surface | SaaS metering, partner APIs, WAF/caching/validation/private required, edge-optimized global public API |
  | WebSocket API | API Gateway WebSocket API | Stateful, full-duplex, content-based routing | Not request/response; different pricing (per message + connection-minute); more complex | Real-time bidirectional (chat, live dashboards, notifications) |

- Cost Profile: HTTP API ≪ REST API for equivalent request volume (AWS-cited ~71% cheaper). WebSocket billed differently (messages + connection duration). Caching (REST) adds a per-hour dedicated cache instance cost.
- Lock-in Assessment: All three are AWS-proprietary control planes. HTTP↔REST is NOT a config toggle — switching is a rebuild (different APIs: apigatewayv2 vs apigateway). Choose deliberately up front.
- Architect Instruction: "Ask whether the API needs API keys/usage plans, per-client throttling, request validation, response caching, WAF-direct, private or edge-optimized endpoints, or X-Ray. If yes to any → REST API. If real-time bidirectional → WebSocket. Otherwise default to HTTP API."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (accessed 2026-08-28)

**Endpoint type: Edge-optimized vs Regional vs Private**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Edge-optimized (REST only) | API Gateway + CloudFront-managed edge | Global client latency via edge PoPs | REST-only; less control over the CloudFront distro; not for internal APIs | Globally distributed public consumers |
  | Regional (REST + HTTP) | API Gateway Regional endpoint | Lower latency for in-Region clients; front with your own CloudFront/WAF | No built-in global edge | In-Region clients, or you own the CDN layer |
  | Private (REST only) | API Gateway private endpoint + interface VPC endpoint | No public exposure; traffic stays on AWS network | REST-only; requires VPC endpoint + resource/endpoint policies | Internal-only APIs, regulated/no-egress workloads |

- Cost Profile: Regional is the baseline. Edge-optimized adds CloudFront data transfer. Private adds interface VPC endpoint hourly + data processing cost.
- Lock-in Assessment: Endpoint type is a property of the API; changing edge↔regional requires redeployment and DNS changes. Private endpoint requires networking rework.
- Architect Instruction: "Ask: are consumers internal-only (→ Private, REST), in-Region (→ Regional), or global public (→ Edge-optimized REST, or Regional HTTP behind CloudFront)? Custom domains for private APIs are supported since 2024-11-21."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-endpoint-types.html (accessed 2026-08-28)

**Authorizer strategy: IAM vs Cognito vs JWT vs Lambda**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | IAM (SigV4 / SigV4a) | IAM + STS | No custom code; native AWS identity; SigV4a for multi-Region (2025-08) | Callers must sign with AWS creds | Service-to-service, internal AWS callers |
  | Cognito user pools | Amazon Cognito | Managed user directory + OAuth scopes; no code | Cognito lock-in; user-pool cost | Consumer/app sign-in with a managed IdP |
  | JWT authorizer (HTTP only) | API Gateway native | Zero-code OIDC/OAuth validation | HTTP APIs only | HTTP API + any OIDC/OAuth IdP |
  | Lambda authorizer | AWS Lambda | Arbitrary custom logic; opaque tokens; rich context; result caching | Cold start + code to maintain; extra invocation cost | Custom/opaque tokens, third-party auth, fine-grained context; REST APIs validating JWTs |

- Cost Profile: IAM/Cognito/JWT ≈ no per-request Lambda cost; Lambda authorizer adds invocations (mitigate with TTL caching).
- Lock-in Assessment: Cognito and native JWT/IAM are AWS-coupled; a Lambda authorizer is the most portable auth logic (you own the code).
- Architect Instruction: "Ask: is the caller an AWS principal (→ IAM), a user from a managed pool (→ Cognito), a bearer of a standard OIDC/OAuth JWT on an HTTP API (→ JWT authorizer), or something custom/opaque or a JWT on a REST API (→ Lambda authorizer)?"
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (accessed 2026-08-28)

**Backend integration: Lambda proxy vs direct AWS-service vs private (VPC link) vs HTTP proxy**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Lambda proxy | AWS Lambda | Simplicity; backend owns routing | Cold starts; couples API to Lambda | Standard serverless business logic |
  | Direct AWS-service integration | API Gateway → DynamoDB/SQS/StepFunctions/etc. | No Lambda in the path (lower cost/latency, "no-code" for CRUD/enqueue) | VTL mapping complexity (REST); limited logic | High-volume pass-through (enqueue to SQS, put to DynamoDB) |
  | Private integration (VPC link) | NLB / ALB / Cloud Map | Reach private microservices without public exposure | VPC link + LB cost/ops | Containerized/EC2 microservices in a VPC |
  | HTTP proxy | Public HTTP endpoint | Front an existing external/public API | No AWS-native auth to backend | Wrapping a legacy or third-party HTTP API |

- Cost Profile: Direct AWS-service integration removes Lambda invocation cost. Private integration adds LB + VPC link cost. HTTP proxy is cheapest control-plane-wise.
- Lock-in Assessment: Direct-service integrations (esp. VTL on REST) are the least portable; Lambda proxy keeps logic portable.
- Architect Instruction: "Ask: is there real business logic (→ Lambda), a simple pass-through to an AWS service (→ direct integration), a private VPC backend (→ VPC link; REST now supports ALB since 2025-11-21, HTTP supports NLB/ALB/Cloud Map), or an existing public API (→ HTTP proxy)?"
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-integration-types.html (accessed 2026-08-28)

### 🚫 Anti-Patterns

**Public production API with no authorizer, no throttling, no WAF**
- Risk Level: CRITICAL
- Why: Violates Security + Reliability. Unauthenticated, unthrottled endpoints invite abuse, scraping, credential stuffing, and can exhaust the shared account-level 10,000 RPS quota, causing 429s across every API in the Region.
- ❌ Wrong: HTTP/REST API method with `authorizationType: NONE`, default stage throttle (= account max), no WAF web ACL.
- ✅ Correct: REST API with a Cognito/JWT/Lambda authorizer, stage + per-client (usage plan) throttling below account limits, and an AWS WAF web ACL (AWS Managed Rules + rate-based rule) attached. HTTP APIs: JWT authorizer + stage throttle + CloudFront/WAF in front.
- Detection: `aws apigateway get-method ... --query 'authorizationType'` = `NONE`; stage `webAclArn` empty; `methodSettings` throttles unset.
- Impact: Data breach, service outage (account-wide 429s), cost overrun.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html (accessed 2026-08-28)

**Using an HTTP API when you actually need REST-only features**
- Risk Level: HIGH
- Why: HTTP APIs lack API keys, usage plans, per-client throttling, request validation, response caching, WAF-direct, private/edge endpoints, and X-Ray. Discovering this after launch forces a costly rebuild (apigatewayv2 → apigateway).
- ❌ Wrong: SaaS product with per-tenant metering/billing built on an HTTP API, then bolting on ad-hoc DynamoDB counters because there are no usage plans.
- ✅ Correct: REST API with usage plans + API keys per tenant, per-client throttle + quota, request validation, and (optionally) AWS Marketplace SaaS metering.
- Detection: Requirement list includes "API keys / per-client quota / request validation / caching / WAF / private endpoint" but the deployed resource is `AWS::ApiGatewayV2::Api`.
- Impact: Rework cost, security gaps, compliance violation.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (accessed 2026-08-28)

**Leaving stage throttle at the account default (no blast-radius isolation)**
- Risk Level: HIGH
- Why: All APIs share one Regional token bucket (10,000 RPS / 5,000 burst; 2,500/1,250 in some Regions). An unbounded API can consume the whole bucket.
- ❌ Wrong: 12 production APIs in one account/Region, none with stage/method throttles — a traffic spike on one 429s all twelve.
- ✅ Correct: Each stage sets `throttlingRateLimit`/`throttlingBurstLimit` well under the account quota; multi-tenant APIs add usage-plan per-key throttles + quotas.
- Detection: `aws apigateway get-stage ... --query 'methodSettings."*/*".throttlingRateLimit'` returns null/unset.
- Impact: Cascading account-wide outage.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html (accessed 2026-08-28)

**Treating an API key as authentication**
- Risk Level: HIGH
- Why: API keys identify and meter clients but are NOT a security mechanism — they can leak and grant no cryptographic identity.
- ❌ Wrong: Public REST API "secured" only by an `x-api-key` header with `authorizationType: NONE`.
- ✅ Correct: Authorizer (IAM/Cognito/JWT/Lambda) for security PLUS an API key + usage plan for metering/rate-limiting.
- Detection: Method has `apiKeyRequired: true` but `authorizationType: NONE`.
- Impact: Unauthorized access, data breach.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html (accessed 2026-08-28)

**No access/execution logging or X-Ray tracing on production stages**
- Risk Level: MEDIUM
- Why: Violates Operational Excellence — without access logs, CloudWatch metrics alarms, and (REST) X-Ray, latency and error triage is guesswork.
- ❌ Wrong: Production stage with `accessLogSettings` unset, no CloudWatch alarms, no X-Ray.
- ✅ Correct: JSON access logs to CloudWatch Logs, detailed metrics enabled, alarms on 4XX/5XX/Latency, X-Ray active tracing on REST.
- Detection: `aws apigateway get-stage ... --query 'accessLogSettings'` is empty; `tracingEnabled` false.
- Impact: Prolonged outages, undiagnosed latency, SLA breaches.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html (accessed 2026-08-28)

**Hardcoding secrets/backend credentials in integration config or mapping templates**
- Risk Level: CRITICAL
- Why: Secrets in API definitions/VTL/stage variables (as plaintext) leak via exports, CloudFormation, and source control.
- ❌ Wrong: Stage variable `dbPassword=plaintext` or an HTTP-integration URL embedding an API token, committed to the repo.
- ✅ Correct: Store secrets in AWS Secrets Manager / SSM Parameter Store (SecureString); have the Lambda/backend fetch them at runtime via its execution role; use IAM auth for AWS-service integrations.
- Detection: Grep IaC/exported OpenAPI for credentials; audit stage variables for secret-like values.
- Impact: Data breach, compliance violation.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/security.html (accessed 2026-08-28)

---

## Cloud-Native Design Patterns

**API Gateway + Lambda "front door" (synchronous request/response)**
- Category: Communication
- Problem: Expose serverless business logic over HTTPS with auth, throttling, and observability without managing servers.
- Solution on AWS: HTTP API (default) or REST API → Lambda proxy integration; authorizer (JWT/Cognito/Lambda); stage throttling; CloudWatch + X-Ray (REST).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Ops | No servers; managed scaling to account quota | Cold starts; account-level throttle is shared |
  | Cost | Pay-per-request | REST pricier than HTTP; caching adds cost |

- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html (accessed 2026-08-28)

**Direct service integration (Lambda-less) for high-volume pass-through**
- Category: Scalability / Cost
- Problem: Simple CRUD or enqueue operations don't justify a Lambda in the hot path.
- Solution on AWS: API Gateway → DynamoDB / SQS / Step Functions / EventBridge direct integration (VTL mapping on REST; AWS-service integration on HTTP).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Latency/cost | Removes Lambda invocation + cold start | VTL/mapping complexity; limited logic |
  | Reliability | Fewer moving parts | Harder to unit-test mappings |

- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-integration-types.html (accessed 2026-08-28)

**Async ingestion: API Gateway → SQS/EventBridge (queue-based load leveling)**
- Category: Resilience / Scalability
- Problem: Spiky write traffic would overwhelm downstream processors or exhaust throttles.
- Solution on AWS: API Gateway direct integration to SQS or EventBridge; consumers (Lambda/containers) drain at their own rate; DLQ for poison messages.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Reliability | Absorbs spikes; decouples producer/consumer | Eventual consistency; 202 Accepted semantics |
  | Scalability | Smooths load | Requires idempotent consumers |

- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-integration-types.html (accessed 2026-08-28)

**Response caching at the gateway (REST only)**
- Category: Scalability / Performance
- Problem: Repeated identical reads hammer the backend and add latency.
- Solution on AWS: REST API stage cache (dedicated cache instance, TTL-based); by default only GET is cached when caching is enabled (safety). Combine with content encoding (gzip) to shrink payloads.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Performance | Lower latency + backend load | Per-hour cache instance cost; staleness risk |
  | Correctness | Cache keys per parameters | Must invalidate on writes |

- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-caching.html (accessed 2026-08-28)

**Canary release deployments (REST only)**
- Category: Migration / Change management
- Problem: Roll out a new API version to a percentage of traffic before full cutover.
- Solution on AWS: REST API stage canary — route N% of stage traffic to the new deployment with separate canary logs/metrics; promote or roll back.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Safety | Gradual rollout + fast rollback | REST-only; extra deployment discipline |

- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/canary-release.html (accessed 2026-08-28)

**Real-time bidirectional with WebSocket APIs**
- Category: Communication
- Problem: Push server-initiated messages to connected clients (chat, live data).
- Solution on AWS: WebSocket API with `$connect`/`$disconnect`/`$default` + custom routes; store connection IDs (e.g., DynamoDB); push via `@connections` management API.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | UX | True full-duplex, low-latency push | Connection-state management; different pricing model |

- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-overview.html (accessed 2026-08-28)

---

## Security Architecture

**Edge protection (Network / Application layer)**
- AWS Services: AWS WAF (REST direct, or via CloudFront for HTTP), AWS Shield (DDoS), resource policies (REST, IP/VPCE allow-deny), mTLS on custom domains.
- Architecture: WAF web ACL (managed rules + rate-based) on the REST stage or fronting CloudFront; resource policy restricting source IP ranges/VPC endpoints; mTLS for partner/IoT clients on a custom domain (default endpoint disabled).
- Compliance Alignment: Supports Security pillar controls for perimeter protection and client authentication (framework reference, not legal advice).
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html (accessed 2026-08-28)

**Identity & authorization (Identity layer)**
- AWS Services: IAM (SigV4/SigV4a since 2025-08-19), Amazon Cognito user pools, native JWT authorizer (HTTP), Lambda authorizers, OAuth 2.0 scopes.
- Architecture: Select the least-code authorizer per the decision table; enable authorizer caching; use Cognito OAuth scopes or JWT `aud`/`iss` validation for coarse authorization, custom context for fine-grained.
- Compliance Alignment: Least-privilege access control (Security pillar).
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html (accessed 2026-08-28)

**Private-only exposure (Network isolation)**
- AWS Services: Private REST API endpoint + interface VPC endpoint, VPC endpoint policies, custom domains for private APIs (since 2024-11-21), private integrations (VPC link → NLB/ALB/Cloud Map).
- Architecture: Deploy the API as Private; restrict access with a resource policy + VPC endpoint policy; reach private backends via VPC link. Traffic never traverses the public internet.
- Compliance Alignment: Data-in-transit isolation for regulated/no-egress workloads (Security pillar). See the AWS whitepaper "Best Practices for Designing Amazon API Gateway Private APIs and Private Integration."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-private-apis.html (accessed 2026-08-28)

---

## Operational Patterns

**Observability (Observability)**
- AWS Services: CloudWatch metrics (`AWS/ApiGateway`: Count, 4XXError, 5XXError, Latency, IntegrationLatency), CloudWatch Logs (access + execution — execution REST-only), X-Ray (REST-only), Amazon Data Firehose access logs (REST-only).
- Cost Profile: Low–Medium (log volume + metric storage are the drivers).
- Automation: Provision logging + alarms as IaC (CloudFormation/SAM/CDK); alarm on 5XX rate, p99 latency, and throttle (429) count.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/monitoring-cloudwatch.html (accessed 2026-08-28)

**Multi-Region DNS failover (High Availability / DR)**
- RTO/RPO: Minutes RTO (DNS TTL-bound); RPO depends on backend replication.
- AWS Services: Two Regional REST APIs (primary/secondary) + Route 53 health checks + failover routing (supported since 2022-10-31); SigV4a (2025-08-19) simplifies multi-Region request signing.
- Cost Profile: Medium–High (duplicate API + backend footprint).
- Automation: Route 53 health checks drive automatic DNS failover; deploy both Regions from the same IaC.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/dns-failover.html (accessed 2026-08-28)

**Cost optimization (FinOps)**
- AWS Services: HTTP API (vs REST) for ~71% lower cost; content encoding (gzip) to cut data-transfer bytes; caching only where hit-rate justifies the per-hour instance; direct service integrations to remove Lambda cost.
- Cost Profile: Choosing HTTP over REST and removing needless Lambda hops are the biggest levers.
- Automation: Tag stages (up to 50 tags) for cost allocation; budget alerts on API-attributable spend.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/amazon-api-gateway-2.html (accessed 2026-08-28)

---

## Reference Architectures

**Serverless REST/JSON API (single-Region, Lambda-backed)**
- AWS Source: AWS Serverless Developer Guide + API Gateway Developer Guide
- Context: Standard B2C/B2B JSON API over serverless compute.
- Services Composition:

  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Edge/security | AWS WAF + (CloudFront for HTTP) | Exploit + DDoS protection | Shield Advanced |
  | API tier | API Gateway HTTP API (default) / REST | Front door, auth, throttling | AppSync (GraphQL) |
  | Auth | JWT authorizer / Cognito / Lambda authorizer | Access control | IAM (service callers) |
  | Compute | AWS Lambda (proxy) | Business logic | ALB+Fargate via VPC link |
  | Data | DynamoDB / RDS Proxy | Persistence | Aurora Serverless v2 |
  | Observability | CloudWatch + X-Ray (REST) | Metrics/logs/traces | — |

- Key Decisions: HTTP vs REST (see decision table); authorizer type; direct-integration vs Lambda for hot paths.
- Scaling Path: Add usage plans + caching (migrate to REST) as tenants/read-volume grow; add multi-Region + Route 53 failover for HA.
- Cost Baseline: Low at moderate volume; dominated by Lambda + data. HTTP API minimizes the gateway line item.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html (accessed 2026-08-28)

**Private internal microservices API**
- AWS Source: AWS Whitepaper — Best Practices for Designing API Gateway Private APIs and Private Integration
- Context: Internal-only APIs for VPC-resident microservices, no public exposure.
- Services Composition:

  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Exposure | Private REST API + interface VPC endpoint | Internal-only access | — |
  | Access control | Resource policy + VPC endpoint policy + IAM | Restrict to VPCs/principals | — |
  | Integration | VPC link → ALB (2025-11-21) / NLB / Cloud Map | Reach private backends | — |
  | Domain | Custom domain for private API (2024-11-21) | Stable internal DNS | — |

- Key Decisions: NLB vs ALB private integration; resource-policy CIDR/VPCE scoping.
- Scaling Path: Add routing rules (2025) for header/base-path routing across internal API versions on one domain.
- Cost Baseline: Medium (VPC endpoint + LB hourly).
- Source: https://docs.aws.amazon.com/whitepapers/latest/best-practices-api-gateway-private-apis-integration/rest-api.html (accessed 2026-08-28)

---

## Service Equivalence Map

> Included as a decision aid for architects evaluating the API-management tier across providers. Equivalence ≠ feature parity — validate against each provider's current docs.

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|--------------|-------|--------------------|
| **Managed API gateway (lightweight)** | API Gateway HTTP API | API Gateway | API Management (Consumption) | OCI API Gateway |
| **Full API management** | API Gateway REST API | Apigee | API Management (Standard/Premium) | OCI API Gateway |
| **Real-time WebSocket** | API Gateway WebSocket API | (via Cloud Run / 3rd-party) | Web PubSub / SignalR | (via compute) |
| **GraphQL front door** | AWS AppSync | (via Apigee / self-managed) | API Management + backend | (self-managed) |
| **Serverless compute backend** | AWS Lambda | Cloud Functions / Cloud Run | Azure Functions | OCI Functions |
| **Edge WAF for APIs** | AWS WAF (+ CloudFront) | Cloud Armor | Azure WAF / Front Door | OCI WAF |
| **API auth (managed IdP)** | Cognito / IAM / JWT authorizer | Identity Platform / IAM | Entra ID | IAM / Identity Domains |

---

## Provider Differentiators (AWS API Gateway 2026)

```
Differentiator: Three distinct API products in one service (REST / HTTP / WebSocket)
Category: Communication
Unique Value: A single managed service spans full API management (REST), cost-optimized minimal APIs (HTTP), and stateful real-time (WebSocket) — with tight Lambda + direct AWS-service integrations.
Architecture Impact: The REST-vs-HTTP choice is a first-order cost/latency/feature decision unique to AWS's split product line.
When to Leverage: Any AWS-native serverless API tier.
Caveat: REST↔HTTP is a rebuild, not a toggle (different control-plane APIs). HTTP lacks WAF-direct, caching, API keys, private/edge endpoints, X-Ray.
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (accessed 2026-08-28)
```
```
Differentiator: Routing rules for REST APIs (2025-06-03)
Category: Communication
Unique Value: Dynamic routing on HTTP header value, URL base path, or both — on public AND private REST APIs, compatible with existing base-path mappings.
Architecture Impact: Enables header-based versioning and domain-layer blue/green without a separate proxy.
When to Leverage: Consolidating multiple APIs/versions under one custom domain.
Caveat: REST APIs + custom domain names only.
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-routing-rules.html (accessed 2026-08-28)
```
```
Differentiator: REST API as a target for Amazon Bedrock AgentCore Gateway / MCP (2025-12-02)
Category: AI/ML
Unique Value: Expose an existing REST API as a tool/target for AI agents via Amazon Bedrock AgentCore Gateway (MCP).
Architecture Impact: Reuse existing APIs as agent tools without rebuilding them for agentic workloads.
When to Leverage: Agentic/LLM applications needing governed access to existing REST APIs.
Caveat: Newest feature (Dec 2025); confirm Regional availability before committing.
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/mcp-server.html (accessed 2026-08-28)
```
```
Differentiator: Fully-managed API Gateway Portal + portal products (2025-11-19)
Category: Operational Excellence
Unique Value: Centralized, managed developer portal with interactive "Try it", API products, and documentation — replacing the older self-hosted serverless developer portal.
Architecture Impact: Removes the need to run a self-hosted portal/static site for API discoverability.
When to Leverage: Publishing APIs to internal or external consumers with self-service discovery.
Caveat: New (Nov 2025); has its own portal-specific throttle quotas (e.g., 250k RPS without access control / 10k RPS with access control per Region).
Source: https://aws.amazon.com/blogs/compute/improve-api-discoverability-with-the-new-amazon-api-gateway-portal/ (accessed 2026-08-28)
```

---

## Scenario Coverage

**Standard Case**: New serverless JSON API fronting Lambda.
- Approach: HTTP API (default) + JWT/Cognito authorizer + stage throttling + CloudWatch access logs + built-in CORS; direct SQS/DynamoDB integration for high-volume pass-through paths.
- Key Decisions: Confirm no REST-only feature is required (else switch to REST before build); pick authorizer type; set stage throttle below account quota.

**Edge Case**: SaaS with per-tenant metering, request validation, response caching, and WAF; some tenants require private/internal access.
- Approach: REST API (usage plans + API keys per tenant, per-client throttle + quota, request validation, stage caching, WAF web ACL). For internal tenants, a Private REST API + VPC link (ALB) with resource/endpoint policies; use routing rules (2025) to consolidate versions under one custom domain.

**Anti-Pattern Case**: Request to ship a public production endpoint with `authorizationType: NONE`, default throttles, no WAF, and an API key treated as authentication.
- Clarification: Refuse/flag. Ask: "What authorizer (IAM/Cognito/JWT/Lambda) secures this route? What per-stage and per-client throttles isolate it from the shared 10,000 RPS account quota? Is a WAF web ACL attached (REST) or CloudFront+WAF fronting (HTTP)? API keys meter clients — they are not authentication." Do not proceed until auth + throttling + WAF are defined.

---

## Source Bibliography

All sources are official AWS documentation/announcements, accessed **2026-08-28**. Upstream Developer Guide "Document history" last updated **2025-12-02**.

| # | Source | URL | Date/Currency |
|---|--------|-----|---------------|
| 1 | What is Amazon API Gateway? (Developer Guide) | https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html | Current (Dec 2025 guide) |
| 2 | Choose between REST APIs and HTTP APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html | Current |
| 3 | Control and manage access to REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html | Current |
| 4 | Amazon API Gateway quotas (limits) | https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html | Current |
| 5 | Throttle requests to your REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html | Current |
| 6 | Document history (changelog) | https://docs.aws.amazon.com/apigateway/latest/developerguide/history.html | Updated 2025-12-02 |
| 7 | Well-Architected Serverless Lens — Amazon API Gateway | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/amazon-api-gateway-2.html | Current lens |
| 8 | Use AWS WAF to protect REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html | Current |
| 9 | Request validation for REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-method-request-validation.html | Current |
| 10 | Security policies for REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-security-policies.html | New 2025-11-19 |
| 11 | Routing rules for REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-routing-rules.html | New 2025-06-03 |
| 12 | IP address types (dual-stack IPv6) | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-ip-address-type.html | New 2025-03-28 |
| 13 | Private REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-private-apis.html | Current |
| 14 | Whitepaper — Best Practices for Private APIs & Private Integration | https://docs.aws.amazon.com/whitepapers/latest/best-practices-api-gateway-private-apis-integration/rest-api.html | Current |
| 15 | Usage plans and API keys | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html | Current |
| 16 | Canary release deployments | https://docs.aws.amazon.com/apigateway/latest/developerguide/canary-release.html | Current |
| 17 | API caching | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-caching.html | Current |
| 18 | DNS failover (multi-Region) | https://docs.aws.amazon.com/apigateway/latest/developerguide/dns-failover.html | 2022-10-31 (feature stable) |
| 19 | AWS Blog — New API Gateway Portal | https://aws.amazon.com/blogs/compute/improve-api-discoverability-with-the-new-amazon-api-gateway-portal/ | 2025 |
| 20 | AWS What's New — Routing rules for REST APIs | https://aws.amazon.com/about-aws/whats-new/2025/06/amazon-api-gateway-routing-rules-rest-apis | 2025-06 |
| 21 | AWS Blog — Dual-stack IPv4/IPv6 endpoints | https://aws.amazon.com/blogs/aws/amazon-api-gateway-now-supports-dual-stack-ipv4-and-ipv6-endpoints/ | 2025-03 |

---

## §7 Research Iteration Changelog

| Iteration | Gap identified | Action | Resolution / Source |
|-----------|----------------|--------|---------------------|
| 0 (P2) | Baseline feature set (REST/HTTP/WebSocket, integrations, endpoints) | WebFetch welcome.html + http-api-vs-rest.html | Resolved — Sources 1, 2 |
| 0 (P2) | Access-control mechanisms | WebFetch apigateway-control-access-to-api.html | Resolved — Source 3 |
| 0 (P2) | Quotas/throttling numbers | WebFetch limits.html + api-gateway-request-throttling.html | Resolved — Sources 4, 5 (10k RPS / 5k burst; 2.5k/1.25k in newer Regions) |
| 0 (P2.changelog) | 2025-2026 breaking/new changes | WebFetch history.html (last updated 2025-12-02) | Resolved — Source 6 (routing rules, dual-stack, SIGv4a, portals, response streaming, ALB private integration, TLS policies, AgentCore target) |
| 0 (P2) | Well-Architected guidance | WebFetch serverless-applications-lens API Gateway page | Resolved — Source 7 (caching, content encoding, TLS, security-first) |
| 0 (P5.triangulate) | Confirm Always-Do patterns via ≥2 sources | Cross-checked docs + changelog + lens | All ✅ patterns triangulated (tags inline) |

**Unverified / irresolvable items:** None. All patterns cite an official AWS source with access date. Two features are the newest and flagged for Regional-availability confirmation before adoption: **Bedrock AgentCore Gateway REST target** (2025-12-02) and **API Gateway Portal** (2025-11-19).

---

### Verification Loop Result (self-check)

- [x] TARGET_EDITION ("AWS API Gateway 2026") stated in metadata and throughout.
- [x] All 6 mandatory sections present: Framework/guardrails (pillars via Serverless Lens), Always-Do, Ask-First, Never-Do, Service Equivalence Map, Source Bibliography.
- [x] Every pattern cites an official AWS URL + access date (2026-08-28).
- [x] Every Never-Do entry has side-by-side ❌ Wrong / ✅ Correct using exact AWS service names.
- [x] All sources dated; upstream currency noted (docs last updated 2025-12-02); currency threshold set (2027-08-28).
- [x] Service Equivalence Map covers the API-management/serverless classes researched.
- [x] Exact provider service names used throughout (no generic "object storage"/"message bus").

> **Recommended next step:** run `/skill-best-practices-validator` on this output, then `/skill-creator` if converting to a SKILL.md.
