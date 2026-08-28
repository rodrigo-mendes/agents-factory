# AWS API Gateway — API Management Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS API Gateway — API Management Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "API Gateway Architecture"
Target_Edition: "AWS API Gateway 2024"
Architecture_Context: "API management for serverless and microservices architectures — covering REST APIs, HTTP APIs, WebSocket APIs, authentication/authorization patterns, throttling, request/response transformation, multi-stage deployment, and backend integration strategies"
Official_Source_URL: "https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to API Gateway feature updates and pricing changes"
```

---

## Executive Summary

Amazon API Gateway is AWS's fully managed service for creating, publishing, maintaining, monitoring, and securing REST, HTTP, and WebSocket APIs at any scale. API Gateway acts as the "front door" for applications to access backend services — Lambda functions, HTTP endpoints, AWS service integrations, and VPC-linked resources — while handling traffic management, authorization, throttling, monitoring, and API version management. The service supports three distinct API types: REST APIs (feature-rich, OpenAPI-compatible, supporting WAF/caching/request validation), HTTP APIs (low-latency, cost-optimized with minimal features), and WebSocket APIs (persistent full-duplex connections for real-time applications).

The 2024 edition's most architecturally significant advances are: (1) **Developer Portal (GA)** — enabling API providers to publish, share, and document APIs for consumers with product grouping and access control; (2) **Response streaming for REST APIs** — supporting chunked transfer encoding for large payloads and server-sent events via Lambda streaming integration; (3) **Mutual TLS authentication enhancements** — expanded certificate chain support and revocation list management; (4) **Private API custom domain names** — enabling private APIs to use custom domains via PrivateLink without Route 53 private hosted zone workarounds; (5) **Enhanced observability** — improved CloudWatch metrics granularity and access log format customization. These changes strengthen API Gateway's position as the default API management layer for AWS serverless architectures while addressing enterprise requirements for private networking and API productization.

The three most critical architecture guardrails for API Gateway are: (1) **always enable authorization on every route/method** — an API deployed without authorization is publicly accessible and exploitable within seconds of deployment; (2) **configure throttling at account, stage, and method levels** — without throttling, a single client can exhaust your account-level quota (10,000 RPS default) affecting all APIs in the region; (3) **enable CloudWatch access logging and CloudTrail for all APIs** — without logging, security incidents, abuse patterns, and integration failures are invisible to operations teams.

---

## Cloud Architecture Glossary

```
Term: REST API
Definition: An API Gateway API type that provides a full-featured RESTful API with support for edge-optimized, regional, and private endpoint types. REST APIs use the API Gateway V1 API and support API keys, usage plans, per-client throttling, request validation, request/response transformation (VTL mapping templates), caching, canary deployments, AWS WAF integration, and resource policies.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api.html
Architect Usage: Choose REST APIs when you need full API management capabilities: WAF protection, per-client rate limiting via usage plans, request body validation, response caching, or private API endpoints. REST APIs are the default choice for production APIs serving external consumers or requiring enterprise-grade control.
Common Confusion: REST API ≠ HTTP API. Despite both being "RESTful," they are distinct products with different pricing, features, and underlying infrastructure (V1 vs V2 API). REST APIs cost approximately 3.5x more per million requests than HTTP APIs but include features HTTP APIs lack entirely (WAF, caching, request validation, per-client throttling).

Term: HTTP API
Definition: A lightweight API Gateway API type optimized for low-latency and cost efficiency. HTTP APIs use the API Gateway V2 API and support Lambda proxy integration, HTTP proxy integration, private integrations (ALB/NLB/Cloud Map), JWT authorizers, CORS configuration, and automatic deployments. HTTP APIs do NOT support WAF, API keys, caching, request validation, request body transformation, or edge-optimized endpoints.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html
Architect Usage: Choose HTTP APIs for simple proxy scenarios where you need low latency and cost optimization: Lambda backends with JWT/OAuth2 authorization, internal microservice routing, or APIs where the backend handles its own validation and transformation. HTTP APIs reduce cost by ~70% vs REST APIs.
Common Confusion: HTTP API ≠ "HTTP endpoint integration." HTTP API is the API type (product). HTTP endpoint integration is a backend type (connecting to any HTTP URL). You can use HTTP endpoint integrations with both REST APIs and HTTP APIs.

Term: WebSocket API
Definition: An API Gateway API type that maintains persistent, full-duplex WebSocket connections between clients and API Gateway. Messages are routed to backend integrations (Lambda, HTTP, AWS services) based on a route selection expression that inspects the message content. Supports $connect, $disconnect, and $default routes plus custom route keys.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-overview.html
Architect Usage: Use WebSocket APIs for real-time bidirectional communication: chat applications, live dashboards, gaming, collaborative editing, IoT device communication. The @connections API enables the backend to push messages to connected clients. Connection state must be managed externally (DynamoDB is the standard pattern).
Common Confusion: API Gateway does NOT maintain persistent connections to the backend — only between client and API Gateway. Backend Lambda functions are invoked per-message, not per-connection. Long-lived backend processing requires external state management and callback URL patterns.

Term: Stage
Definition: A named reference to a deployment of an API (e.g., 'dev', 'staging', 'prod', 'v1', 'v2'). Each stage is independently configurable with its own stage variables, throttling settings, access logging, caching (REST APIs only), and canary settings. The stage name becomes part of the API's invoke URL: {api-id}.execute-api.{region}.amazonaws.com/{stage-name}.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-stages.html
Architect Usage: Use stages for environment separation (dev/staging/prod) with stage variables for environment-specific configuration (Lambda aliases, endpoint URLs, feature flags). Avoid using stages for API versioning — use path-based versioning (/v1/, /v2/) or custom domain name base path mappings instead.
Common Confusion: Stage ≠ deployment. A deployment is a snapshot of the API configuration. A stage points to a deployment. Multiple stages can point to the same deployment. Updating a stage (changing variables, throttling) does NOT require a new deployment. Changing routes/methods/integrations DOES require a new deployment.

Term: Integration
Definition: The connection between an API Gateway method/route and a backend service. Integration types: Lambda (proxy or custom), HTTP (proxy or custom), AWS Service (direct service action invocation), Mock (API Gateway generates response without backend), and VPC Link (private integration to resources in a VPC via NLB or ALB).
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-integration-settings.html
Architect Usage: Use Lambda proxy integration as the default (simplest, passes full request context to Lambda). Use AWS service integrations for direct service invocation without Lambda (e.g., SQS SendMessage, Step Functions StartExecution, DynamoDB PutItem) to reduce latency, cost, and failure surface. Use VPC Link for private backend services not accessible from the public internet.
Common Confusion: "Proxy integration" passes the raw request to the backend and expects the backend to format the response. "Custom integration" uses mapping templates (VTL) to transform request/response. Proxy integration is simpler but gives the backend responsibility for response formatting. Custom integration is more complex but enables request/response reshaping without backend changes.

Term: Lambda Authorizer
Definition: A Lambda function that API Gateway invokes to perform authentication and authorization before the integration is called. Two payload types: TOKEN (receives authorization header value) and REQUEST (receives full request context including headers, query strings, path parameters, stage variables, and context). Returns an IAM policy document that API Gateway caches for subsequent requests from the same caller.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
Architect Usage: Use Lambda authorizers for custom authentication logic (validating proprietary tokens, calling external identity providers, implementing complex RBAC). Configure authorization caching (TTL 0-3600 seconds, default 300) to reduce Lambda invocations. Set TTL=0 for per-request authorization (no caching). Use REQUEST type over TOKEN type for more granular authorization decisions.
Common Confusion: Lambda authorizer ≠ Cognito authorizer. Lambda authorizer is custom code you write. Cognito authorizer is a built-in integration that validates Cognito user pool tokens without custom code. Lambda authorizer cache key is derived from the identity source — ensure the identity source uniquely identifies the caller, or different callers may share cached policies.

Term: Usage Plan
Definition: A configuration that associates API stages and API keys with throttling limits (requests per second, burst) and quota limits (requests per day/week/month). Usage plans enable per-client rate limiting and consumption tracking. Only available for REST APIs and WebSocket APIs — NOT supported on HTTP APIs.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html
Architect Usage: Use usage plans for B2B API monetization, partner integrations, and tiered access control. Create separate usage plans for different consumer tiers (free, basic, premium). API keys are identifiers, NOT authorization mechanisms — always combine with a proper authorizer (IAM, Lambda, Cognito).
Common Confusion: API keys are NOT a security mechanism. They are identifiers for usage tracking and throttling. An API key alone does not authenticate or authorize a caller. Never use API keys as the sole access control — they can be easily shared, leaked, or brute-forced. Always pair API keys with a proper authorization mechanism.

Term: Resource Policy
Definition: A JSON-based resource policy attached to a REST API that controls which AWS principals, IP addresses, VPC endpoints, or source VPCs can invoke the API. Resource policies use IAM policy syntax with Conditions. Available only for REST APIs — not supported on HTTP APIs or WebSocket APIs.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-resource-policies.html
Architect Usage: Use resource policies to: (1) restrict private API access to specific VPC endpoints; (2) whitelist IP ranges for public APIs; (3) enable cross-account API invocation; (4) deny access from specific IP ranges (blocklist). Resource policies are evaluated together with IAM policies and Lambda authorizers — all must allow for access to succeed.
Common Confusion: Resource policy changes require an API redeployment to take effect — they are NOT immediately active. Resource policies on REST APIs interact with IAM policies via an evaluation matrix: explicit deny in either = deny; if resource policy is present, both must explicitly allow.

Term: VPC Link
Definition: A resource that enables API Gateway to access private resources inside a VPC. For REST APIs, VPC Links connect to Network Load Balancers (NLB). For HTTP APIs, VPC Links connect to Application Load Balancers (ALB), Network Load Balancers (NLB), or AWS Cloud Map services. VPC Links use AWS PrivateLink under the hood.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/getting-started-with-private-integration.html
Architect Usage: Use VPC Links for private integrations — connecting API Gateway to backend services running in private subnets (ECS tasks, EKS pods, EC2 instances, RDS proxies). For REST APIs, you must use an NLB as the VPC Link target. For HTTP APIs, you can target ALBs directly (simpler for HTTP-based backends) or use Cloud Map for service discovery.
Common Confusion: VPC Link ≠ Private API. A VPC Link enables API Gateway (public or private) to reach private backends. A Private API restricts who can call the API to VPC endpoints. They solve different problems: VPC Link = backend accessibility; Private API = frontend accessibility. You can combine both for fully private end-to-end communication.

Term: Endpoint Type
Definition: Determines how API Gateway routes client traffic to the API. Three types: Regional (API deployed in a specific region, clients connect directly), Edge-optimized (API fronted by CloudFront distribution for global client access, requests routed to nearest POP), Private (API accessible only from within a VPC via interface VPC endpoints).
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-endpoint-types.html
Architect Usage: Use Regional for same-region clients and when you manage your own CloudFront distribution (more control over caching/WAF). Use Edge-optimized for geographically distributed clients without custom CloudFront configuration (API Gateway manages the distribution). Use Private for internal-only APIs that must never be accessible from the public internet.
Common Confusion: Edge-optimized does NOT mean the API runs at the edge — only the CloudFront POP is at the edge. The API Gateway execution and Lambda backend still run in the specified region. Edge-optimized reduces TLS handshake latency for distant clients but does NOT reduce backend processing latency. HTTP APIs only support Regional endpoints.

Term: Mapping Template
Definition: A script written in Apache Velocity Template Language (VTL) that transforms request or response payloads between the client format and the backend format. Used in REST API custom (non-proxy) integrations to reshape data, extract parameters, set headers, and construct backend-specific request formats.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-data-transformations.html
Architect Usage: Use mapping templates when you need to adapt between different API contract versions, extract/inject parameters, call AWS services directly (constructing service-specific request bodies), or maintain backward compatibility during backend refactoring. Avoid mapping templates for simple Lambda proxy scenarios — they add complexity and make debugging harder.
Common Confusion: Mapping templates are REST API only — HTTP APIs do NOT support request/response body transformation. VTL templates have access to $input (request body), $context (request context), $stageVariables, and $util (utility functions). VTL execution failures return 500 errors without clear error messages unless CloudWatch execution logging is enabled.

Term: Canary Release Deployment
Definition: A deployment strategy for REST APIs where a percentage of API traffic is directed to a canary (new version) while the remainder continues to the current production deployment. Configurable traffic percentage (0-100%), with independent stage variables and CloudWatch metrics for the canary.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/canary-release.html
Architect Usage: Use canary deployments for safe rollout of API changes — start with 5-10% traffic to canary, monitor error rates and latency in CloudWatch, then promote (100% to canary = new production) or rollback (0% to canary = revert). Canary deployments are REST API only — HTTP APIs use automatic deployments with no built-in canary support.
Common Confusion: Canary deployment in API Gateway is NOT the same as Lambda weighted aliases. API Gateway canary splits traffic at the API stage level (different API configurations). Lambda aliases split traffic at the function version level (same API, different function code). For full canary coverage, use both: API Gateway canary for API-level changes + Lambda aliases for code-only changes.

Term: Custom Domain Name
Definition: A user-owned domain name (e.g., api.example.com) mapped to an API Gateway API via DNS (Route 53 alias or CNAME). Requires an ACM certificate. Supports base path mappings to route different URL paths to different APIs or stages. Available for REST APIs (regional, edge-optimized) and HTTP APIs (regional only). Private custom domain names are available for Private REST APIs.
Provider Docs Section: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html
Architect Usage: Always use custom domain names for production APIs — the default execute-api URL embeds the API ID, is not meaningful to consumers, and changes if you recreate the API. Use base path mappings for API versioning (api.example.com/v1 → REST API v1, api.example.com/v2 → REST API v2). Use separate custom domains per environment (api-dev.example.com, api.example.com).
Common Confusion: Custom domain names for edge-optimized APIs require ACM certificates in us-east-1 (N. Virginia) regardless of the API's region. Regional API custom domain names require ACM certificates in the same region as the API. If you use your own CloudFront distribution in front of a Regional API, the ACM certificate must be in us-east-1 (for CloudFront).
```

---

## Architecture Framework Analysis: AWS Well-Architected — API Gateway

```
Pillar: Security
Definition: The ability to protect data, systems, and assets while delivering business value through risk assessments and mitigation strategies.
Key Design Principles:
  - Implement a strong identity foundation (IAM, Lambda authorizers, Cognito, JWT)
  - Enable traceability (CloudTrail for API management operations, CloudWatch access logs for invocations)
  - Apply security at all layers (WAF at edge, authorization at API Gateway, validation at integration)
  - Automate security best practices (resource policies, SCPs to enforce encryption and authorization)
  - Protect data in transit (TLS 1.2 mandatory, mutual TLS for client certificate authentication)
Applies To API Management: Every API Gateway API must have authorization configured on every route/method. Public-facing REST APIs must have AWS WAF web ACL attached. Access logging must be enabled for all stages. TLS 1.2 is enforced by default (minimum version). Mutual TLS provides client certificate authentication for B2B integrations. Resource policies restrict API access by IP, VPC endpoint, or AWS account.
Assessment Questions:
  1. Is authorization (IAM, Lambda authorizer, Cognito, or JWT) configured on every API method/route?
  2. Is AWS WAF attached to all public-facing REST APIs with rate-based rules?
  3. Are CloudWatch access logs enabled for all production stages?
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html

Pillar: Reliability
Definition: The ability of a workload to perform its intended function correctly and consistently when it's expected to.
Key Design Principles:
  - Automatically recover from failure (API Gateway is multi-AZ by default — no user configuration required)
  - Scale horizontally (API Gateway auto-scales — configure throttling to protect downstream dependencies)
  - Stop guessing capacity (serverless model — no provisioning required)
  - Manage change through automation (IaC for API definitions, canary deployments for safe rollout)
  - Test recovery procedures (test throttling behavior, test Lambda authorizer failures, test integration timeouts)
Applies To API Management: API Gateway is inherently highly available (multi-AZ, managed service). The reliability concern shifts to protecting backend services from being overwhelmed. Configure stage-level and method-level throttling. Set integration timeouts appropriately (max 29 seconds for REST APIs, 30 seconds for HTTP APIs). Implement circuit breaker patterns in Lambda authorizers and backend integrations.
Assessment Questions:
  1. Are throttling limits configured at stage and method level to protect backend services?
  2. Are integration timeouts set appropriately for each backend (not using the 29s default for all)?
  3. Is there a canary deployment or staged rollout strategy for API changes?
Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html

Pillar: Performance Efficiency
Definition: The ability to use computing resources efficiently to meet system requirements and to maintain that efficiency as demand changes and technologies evolve.
Key Design Principles:
  - Use serverless architectures (API Gateway + Lambda eliminates infrastructure management)
  - Go global in minutes (edge-optimized endpoints or CloudFront for global distribution)
  - Experiment more often (canary deployments, A/B testing via stage variables)
  - Consider mechanical sympathy (REST API caching, connection reuse, response compression)
Applies To API Management: Enable API caching for REST APIs to reduce backend invocations and improve latency (TTL 0-3600 seconds). Use edge-optimized endpoints or your own CloudFront distribution for global clients. Minimize mapping template complexity. Use Lambda proxy integration to reduce API Gateway processing overhead. Enable response compression (gzip) for payloads > 1 KB.
Assessment Questions:
  1. Is API caching enabled for read-heavy endpoints with appropriate TTL and cache key parameters?
  2. Is the endpoint type (Regional vs Edge-optimized) appropriate for client geography?
  3. Are integration types (proxy vs custom) chosen to minimize unnecessary transformation overhead?
Source: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html

Pillar: Cost Optimization
Definition: The ability to run systems to deliver business value at the lowest price point.
Key Design Principles:
  - Adopt a consumption model (API Gateway charges per request — pay only for what you use)
  - Measure overall efficiency (cost per API call, cache hit ratio, unnecessary invocations)
  - Analyze and attribute expenditure (per-API cost tracking via CloudWatch dimensions)
  - Stop spending money on undifferentiated heavy lifting (managed API management vs self-hosted)
Applies To API Management: Choose HTTP APIs over REST APIs when REST API-specific features are not required (70% cost reduction). Enable API caching to reduce backend invocations. Use direct AWS service integrations (API Gateway → SQS, Step Functions, DynamoDB) to eliminate Lambda invocation costs for simple operations. Monitor and optimize Lambda authorizer caching to reduce invocations.
Assessment Questions:
  1. Is the API type (REST vs HTTP) appropriate for the feature requirements — are you paying for unused capabilities?
  2. Is API caching enabled with a high cache hit ratio for cacheable responses?
  3. Are direct service integrations used where Lambda adds no value (simple data pass-through)?
Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html

Pillar: Operational Excellence
Definition: The ability to support development and run workloads effectively, gain insight into their operations, and continuously improve supporting processes and procedures.
Key Design Principles:
  - Perform operations as code (OpenAPI/Swagger definitions, CloudFormation/CDK/SAM for API deployment)
  - Make frequent, small, reversible changes (canary deployments, stage-based rollback)
  - Refine operations procedures frequently (monitor 4XX/5XX rates, optimize throttling, tune caching)
  - Anticipate failure (test integration timeouts, test throttle handling, test authorizer failures)
  - Learn from all operational failures (access log analysis, X-Ray tracing for latency root cause)
Applies To API Management: All API definitions must be managed via IaC (SAM/CDK/CloudFormation with OpenAPI specifications). CloudWatch dashboards must display: request count, 4XX rate, 5XX rate, latency (p50/p90/p99), integration latency, cache hit/miss ratio. Alarms must trigger on sustained 5XX rates > 1% and latency P99 breaching SLA. API changes must use canary deployments or blue-green via custom domain name base path mapping switches.
Assessment Questions:
  1. Are all API configurations defined as code (OpenAPI + IaC) with version control?
  2. Are CloudWatch alarms configured for 5XX error rates and latency SLA breaches?
  3. Is there a documented rollback procedure for failed API deployments?
Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html

Pillar: Sustainability
Definition: Minimizing the environmental impact of running cloud workloads.
Key Design Principles:
  - Minimize idle resources (API Gateway is serverless — zero idle compute)
  - Maximize utilization of provisioned resources (API caching reduces redundant backend compute)
  - Use managed services (no self-hosted API gateway infrastructure to maintain)
Applies To API Management: API Gateway is inherently sustainable — fully serverless with no idle capacity. API caching reduces downstream compute. Direct service integrations eliminate unnecessary Lambda executions. Response compression reduces data transfer. HTTP APIs have lower per-request overhead than REST APIs.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Authorization on Every Method/Route**
- Pillar Alignment: Security
- Why: An API method/route deployed without authorization is immediately accessible to the public internet (unless it's a Private API). The Well-Architected Security pillar mandates "implement a strong identity foundation." Every public API endpoint is a potential attack surface — unauthorized access enables data exfiltration, resource abuse, and cost amplification attacks.
- AWS Services: Amazon API Gateway (IAM authorization, Lambda authorizers, Cognito user pools, JWT authorizers), AWS WAF (additional protection layer)
- Architecture Decision:
  Every method (REST API) or route (HTTP API) must have an authorization type configured: `AWS_IAM` (for service-to-service), `COGNITO_USER_POOLS` or `JWT` (for user-facing with OAuth2/OIDC), or `CUSTOM` Lambda authorizer (for proprietary token schemes). The only acceptable exception is health check endpoints (`GET /health`) that return no sensitive data and are needed for external monitoring.
- Verification:
  ```bash
  # REST API — check all methods for authorization
  aws apigateway get-resources --rest-api-id <API_ID> --query "items[].resourceMethods" | grep -i "authorizationType"
  # All methods must return NONE only for explicitly documented health check endpoints

  # HTTP API — check all routes
  aws apigatewayv2 get-routes --api-id <API_ID> --query "Items[].AuthorizationType"
  # Must NOT return "NONE" for any production route
  ```
- Trade-offs: Authorization adds latency (Lambda authorizer cold start: 100-500ms first invocation; cached: 0ms). Cognito/JWT validation adds ~5-15ms. IAM SigV4 validation adds ~1-5ms. Caching Lambda authorizer results (TTL 300s default) eliminates repeated latency.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html

**AWS WAF on All Public-Facing REST APIs**
- Pillar Alignment: Security
- Why: Public APIs are exposed to automated attacks: credential stuffing, SQL injection, bot scraping, DDoS, and API abuse. The Well-Architected Security pillar requires "protect at all layers." AWS WAF provides rate-based rules (DDoS mitigation), managed rule groups (OWASP top 10), IP reputation lists, and bot control — none of which API Gateway provides natively.
- AWS Services: AWS WAF (web ACL), Amazon API Gateway (REST API WAF association), AWS Managed Rules (AWSManagedRulesCommonRuleSet, AWSManagedRulesKnownBadInputsRuleSet, AWSManagedRulesBotControlRuleSet)
- Architecture Decision:
  Attach a WAF web ACL to every public-facing REST API stage. At minimum, include: (1) AWSManagedRulesCommonRuleSet (OWASP protections), (2) AWSManagedRulesKnownBadInputsRuleSet (Log4j, path traversal), (3) Rate-based rule at 2000-10000 requests per 5 minutes per IP (adjust per use case). Add AWSManagedRulesBotControlRuleSet for consumer-facing APIs. Note: WAF is NOT available for HTTP APIs — this is a primary reason to choose REST APIs for public-facing production APIs.
- Verification:
  ```bash
  aws apigateway get-stage --rest-api-id <API_ID> --stage-name prod --query "webAclArn"
  # Must return a valid WAF web ACL ARN — empty/null = unprotected
  ```
- Trade-offs: WAF adds ~1-2ms latency per request. WAF costs: $5/month per web ACL + $1/month per rule + $0.60 per million requests evaluated. For high-traffic APIs (>100M requests/month), WAF cost becomes significant. WAF is REST API only — HTTP APIs rely on backend-level protections.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html

**CloudWatch Access Logging on All Stages**
- Pillar Alignment: Operational Excellence, Security
- Why: Without access logging, you cannot: detect abuse patterns, debug integration failures, measure API performance, investigate security incidents, or demonstrate compliance. The Well-Architected Operational Excellence pillar mandates "anticipate failure" and "learn from operational events." Access logs provide per-request visibility into caller identity, response codes, latency, and errors.
- AWS Services: Amazon API Gateway (access logging configuration), Amazon CloudWatch Logs (log group), AWS IAM (CloudWatch Logs role for API Gateway)
- Architecture Decision:
  Enable access logging on every stage with a dedicated CloudWatch Logs log group per API/stage. Use JSON format for structured querying. Include at minimum: `requestId`, `ip`, `caller`, `user`, `requestTime`, `httpMethod`, `resourcePath`, `status`, `protocol`, `responseLength`, `integrationLatency`, `responseLatency`. Set log group retention to 30-90 days for cost optimization (longer for compliance). Grant API Gateway the `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` permissions via the account-level CloudWatch Logs role.
- Verification:
  ```bash
  aws apigateway get-stage --rest-api-id <API_ID> --stage-name prod --query "accessLogSettings"
  # Must return destinationArn (CloudWatch Logs ARN) and format (non-empty)
  ```
- Trade-offs: Access logging adds negligible latency (<1ms). CloudWatch Logs costs: $0.50/GB ingested + $0.03/GB stored. For high-traffic APIs, log volume can become a cost factor — use log filtering or sampling for non-production stages. Enable execution logging only for debugging (verbose, expensive).
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html

**Throttling Configuration at Multiple Levels**
- Pillar Alignment: Reliability, Security
- Why: API Gateway has a default account-level throttle of 10,000 RPS (burst 5,000) shared across ALL APIs in a region. Without stage-level and method-level throttling, a single API or client can exhaust the account quota, causing 429 errors for all APIs. The Well-Architected Reliability pillar requires "scale horizontally to increase aggregate workload availability" — throttling prevents cascading failures.
- AWS Services: Amazon API Gateway (stage throttling, usage plans, method throttling), Amazon CloudWatch (throttle metrics)
- Architecture Decision:
  Configure throttling at three levels: (1) Account level — request increase from AWS Support for production workloads requiring >10,000 RPS; (2) Stage level — set per-stage default throttle below account limit (e.g., 5,000 RPS for prod API, leaving headroom for other APIs); (3) Method level — set per-method limits for expensive operations (e.g., POST methods at 1,000 RPS, GET methods at 8,000 RPS). For multi-tenant APIs, use usage plans with per-client throttles to prevent noisy-neighbor problems.
- Verification:
  ```bash
  aws apigateway get-stage --rest-api-id <API_ID> --stage-name prod --query "methodSettings.'*/*'.throttlingRateLimit"
  # Must return a value less than account-level quota
  ```
- Trade-offs: Overly aggressive throttling rejects legitimate traffic (false positive 429s). Overly permissive throttling risks backend overload. Start with conservative limits and increase based on observed traffic patterns. Throttling limits are "targets" (best-effort) — brief bursts may exceed configured limits.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html

**Custom Domain Names for Production APIs**
- Pillar Alignment: Operational Excellence, Reliability
- Why: The default API Gateway URL (`{api-id}.execute-api.{region}.amazonaws.com/{stage}`) embeds implementation details (API ID, region), is unmemorable, and — critically — changes if you recreate the API. This creates hard dependencies between consumers and your internal API infrastructure. The Well-Architected Operational Excellence pillar requires "make frequent, small, reversible changes" — custom domains enable API replacement without consumer impact.
- AWS Services: Amazon API Gateway (custom domain names, base path mappings), AWS Certificate Manager (TLS certificates), Amazon Route 53 (DNS alias records)
- Architecture Decision:
  Create custom domain names for all production APIs (e.g., `api.example.com`). Use base path mappings for versioning (`/v1` → API v1 stage, `/v2` → API v2 stage). Use ACM-managed certificates (auto-renewal). Create Route 53 alias records pointing to the API Gateway domain name. For Regional APIs, use the regional domain name; for edge-optimized, use the CloudFront distribution domain name.
- Verification:
  ```bash
  aws apigateway get-domain-names --query "items[].domainName"
  # Production APIs must have custom domain names configured
  aws apigateway get-base-path-mappings --domain-name api.example.com
  # Must show mappings to production stages
  ```
- Trade-offs: Custom domain names add DNS resolution hop. ACM certificates require domain validation (DNS or email). For edge-optimized APIs, certificates must be in us-east-1. Custom domain name changes require DNS propagation time (TTL-dependent). Base path mappings add marginal routing overhead.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html

**TLS 1.2 Minimum and Mutual TLS for B2B**
- Pillar Alignment: Security
- Why: All data in transit to and from API Gateway must be encrypted. TLS 1.2 is the minimum supported version (enforced by default). For B2B integrations where you need to authenticate the client (not just authorize), mutual TLS (mTLS) provides cryptographic client identity verification via X.509 certificates.
- AWS Services: Amazon API Gateway (TLS policy, mTLS configuration), AWS Certificate Manager (server certificates), Amazon S3 (truststore for client CA certificates)
- Architecture Decision:
  TLS 1.2 is enforced by default — no configuration required. For B2B APIs requiring client certificate authentication: enable mutual TLS on the custom domain name, upload a truststore (PEM-encoded CA certificates) to S3, and reference the S3 URI in the domain name configuration. Clients must present a certificate signed by a CA in your truststore. Combine mTLS with Lambda authorizer or IAM for multi-factor authentication.
- Verification:
  ```bash
  aws apigateway get-domain-name --domain-name api.example.com --query "mutualTlsAuthentication"
  # For B2B APIs: must return truststoreUri pointing to S3 truststore
  # For all APIs: attempt connection with TLS 1.0/1.1 — must be rejected
  ```
- Trade-offs: mTLS requires certificate lifecycle management (issuance, rotation, revocation). Clients must manage client certificates. Certificate revocation requires updating the truststore in S3 and redeploying. mTLS adds TLS handshake overhead (~10-30ms) for the certificate chain validation.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-mutual-tls.html

**Infrastructure as Code for API Definitions**
- Pillar Alignment: Operational Excellence
- Why: Manual API Gateway configuration via console is error-prone, unreproducible, and un-auditable. The Well-Architected Operational Excellence pillar mandates "perform operations as code." API definitions must be version-controlled, peer-reviewed, and deployed through CI/CD pipelines.
- AWS Services: AWS SAM (simplified API definition), AWS CDK (programmatic API construction), AWS CloudFormation (declarative API definition), OpenAPI/Swagger (API specification)
- Architecture Decision:
  Define APIs using OpenAPI 3.0 specifications with API Gateway extensions (`x-amazon-apigateway-*`). Deploy via AWS SAM (`AWS::Serverless::Api` or `AWS::Serverless::HttpApi`) or CDK (`@aws-cdk/aws-apigateway`). Store OpenAPI specs in version control alongside application code. Use SAM/CDK for Lambda + API Gateway co-deployment. Never make manual console changes to production APIs — treat all console changes as drift requiring remediation.
- Verification:
  ```bash
  # Export current API and diff against source-controlled definition
  aws apigateway get-export --rest-api-id <API_ID> --stage-name prod --export-type oas30 --accepts application/json api-export.json
  diff api-export.json source-controlled-spec.json
  # Drift = manual changes that must be reconciled
  ```
- Trade-offs: IaC adds deployment pipeline complexity. OpenAPI specifications can become verbose for large APIs. SAM/CDK abstractions may not expose all API Gateway features. Escape hatches (CloudFormation overrides) are sometimes needed for advanced configurations.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-import-api.html

---

### ⚠️ Architectural Decisions

**REST API vs HTTP API**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | REST API | API Gateway REST (V1) | Features (WAF, caching, validation, usage plans, resource policies, canary, edge-optimized, private endpoints) | Cost (3.5x more expensive), slightly higher latency | Public-facing APIs needing WAF, per-client throttling, request validation, caching, or private endpoint access |
  | HTTP API | API Gateway HTTP (V2) | Cost (~70% cheaper), lower latency (~60% faster), simpler configuration, automatic deployments | Features (no WAF, no caching, no request validation, no API keys, no resource policies, no edge-optimized) | Internal APIs, Lambda proxy scenarios, JWT-based auth, cost-sensitive workloads without WAF/caching requirements |

- Cost Profile: REST API = $3.50/million requests + data transfer. HTTP API = $1.00/million requests (first 300M), $0.90/million (300M+) + data transfer. For 100M requests/month: REST = $350, HTTP = $100. Caching (REST only) adds $0.02-$3.80/hour depending on cache size.
- Lock-in Assessment: Both are AWS-specific. OpenAPI export provides some portability of API definitions. Migration between REST and HTTP APIs requires recreating the API (different underlying services). HTTP API → REST API migration is straightforward (additive features). REST API → HTTP API may lose functionality.
- Architect Instruction: "Ask 'Does this API require WAF protection, response caching, request body validation, per-client rate limiting (usage plans), or private API endpoints?' — if YES to any, use REST API. If NO to all, use HTTP API for cost savings."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html

**Endpoint Type: Regional vs Edge-Optimized vs Private**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Regional | API Gateway Regional endpoint | Control (own CloudFront, custom WAF at CF), same-region latency | Global latency without custom CDN | Clients are in the same region; you want your own CloudFront distribution; HTTP APIs (only option) |
  | Edge-Optimized | API Gateway + managed CloudFront | Global client latency (nearest POP), simplified global distribution | Control (can't customize the CloudFront distribution), REST API only | Geographically distributed clients, no custom CloudFront requirements |
  | Private | API Gateway + VPC Interface Endpoint | Security (zero public internet exposure) | Accessibility (VPC-only), REST API only, no edge/regional fallback | Internal-only APIs, regulated workloads, zero-trust architectures |

- Cost Profile: Regional and Edge-optimized have the same API Gateway request pricing. Edge-optimized adds no explicit CloudFront charges (bundled). Private endpoints incur VPC endpoint costs ($0.01/hour + $0.01/GB data processed per AZ).
- Scaling Characteristics: All types share the same 10,000 RPS account-level default. Edge-optimized benefits from CloudFront's global capacity for burst absorption. Private APIs share the VPC endpoint's network interface throughput limits.
- Architect Instruction: "Ask 'Where are the API consumers located?' — same region = Regional. Global = Edge-optimized (or Regional + your own CloudFront). VPC-only = Private."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-endpoint-types.html

**Authorization Strategy: IAM vs Lambda Authorizer vs Cognito vs JWT**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | IAM Authorization | API Gateway + IAM (SigV4) | AWS-native security, fine-grained resource policies, no custom code | External client complexity (SigV4 signing), not suitable for browser-based apps | Service-to-service (AWS → AWS), cross-account invocation, programmatic access from AWS SDKs |
  | Lambda Authorizer | API Gateway + Lambda function | Flexibility (any auth scheme, external IdP, custom logic, RBAC/ABAC) | Cold start latency, Lambda invocation cost, custom code maintenance | Proprietary tokens, complex authorization logic, external IdPs not compatible with JWT/Cognito |
  | Cognito User Pools | API Gateway + Amazon Cognito | Managed user identity (signup, MFA, federation), zero custom code for token validation | Cognito dependency, limited to Cognito token format, REST API only (as native authorizer) | User-facing APIs with Cognito as the identity provider |
  | JWT Authorizer | API Gateway HTTP API + any OIDC provider | Standard OAuth2/OIDC, no custom code, any compliant IdP (Auth0, Okta, Cognito, Azure AD) | HTTP API only, limited claim-based routing (no custom policy generation) | HTTP APIs with standard OIDC/OAuth2 identity providers |

- Cost Profile: IAM = free (no additional cost). Lambda authorizer = Lambda invocation cost per uncached request ($0.20/M invocations). Cognito = per-MAU pricing (free tier 50,000 MAU). JWT = free (validation is built-in).
- Operational Burden: IAM = zero. JWT = zero. Cognito = managed (Cognito handles user management). Lambda authorizer = you own the code, testing, deployment, and monitoring.
- Architect Instruction: "Ask 'Is this service-to-service (AWS workloads)?' — if YES, use IAM. 'Is this user-facing with a standard OIDC provider?' — if YES and HTTP API, use JWT authorizer. If YES and REST API, use Cognito or Lambda authorizer. 'Is custom authorization logic needed?' — use Lambda authorizer."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html

**Integration Type: Lambda Proxy vs AWS Service vs HTTP Proxy vs VPC Link**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Lambda Proxy | API Gateway + Lambda | Simplicity, full request context in Lambda, flexible response format | Lambda cold starts, 15-min timeout, Lambda concurrency limits | General-purpose backend logic, any computation requiring custom code |
  | AWS Service (direct) | API Gateway + target AWS service (SQS, Step Functions, DynamoDB, S3, SNS, Kinesis) | Eliminates Lambda (lower cost, lower latency, fewer failure points) | VTL mapping template complexity, limited to service API operations | Simple operations: queue a message, start a workflow, write to DB, put an object — no custom logic needed |
  | HTTP Proxy | API Gateway + HTTP endpoint | Backend-agnostic, existing HTTP services, multi-cloud backends | No transformation (proxy), API Gateway adds latency to the call | Existing HTTP microservices, third-party APIs, legacy backends |
  | VPC Link (Private) | API Gateway + NLB/ALB + private resources | Security (backends stay private), ECS/EKS/EC2 backends | VPC Link setup complexity, NLB/ALB cost, networking configuration | Private microservices in VPC, Kubernetes services, RDS Proxy, internal HTTP services |

- Cost Profile: Lambda proxy = API Gateway + Lambda cost. Direct service = API Gateway cost only (no Lambda). HTTP proxy = API Gateway + data transfer. VPC Link = API Gateway + NLB/ALB ($0.0225/hour + LCU charges).
- Architect Instruction: "Ask 'Does the integration require custom business logic?' — if NO (just routing to SQS, Step Functions, DynamoDB), use direct AWS service integration. If YES, use Lambda proxy. 'Is the backend in a VPC?' — add VPC Link. 'Is the backend external?' — use HTTP proxy."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-integration-settings.html

**Caching Strategy: API Gateway Cache vs CloudFront vs Application-Level**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | API Gateway Cache | REST API built-in cache (0.5-237 GB) | Backend offload, per-stage per-method control, cache key customization | REST API only, cost ($0.02-$3.80/hour), single-region | Reducing Lambda/backend invocations for repeated identical requests |
  | CloudFront Cache | CloudFront distribution + Regional API | Global caching (edge POPs), larger cache, more control (behaviors, invalidation) | Configuration complexity, separate service to manage, cache invalidation propagation delay | Global APIs, static or semi-static responses, high read:write ratio |
  | Application-Level | DynamoDB/ElastiCache in backend | Full control, complex invalidation logic, shared across multiple APIs | Custom code, infrastructure management, not transparent to API Gateway | Complex cache invalidation requirements, data shared across multiple services |

- Cost Profile: API Gateway Cache: $0.02/hour (0.5 GB) to $3.80/hour (237 GB) — 24/7 cost regardless of usage. CloudFront: $0.01/10,000 requests + $0.085/GB (varies by region). Application-level: DynamoDB ($1.25/M read units) or ElastiCache ($0.017/hour for cache.t3.micro).
- Architect Instruction: "Ask 'Is the API response cacheable (same input → same output)?' — if YES: 'Is it REST API?' → use API Gateway cache. 'Need global caching?' → use CloudFront. 'Need complex invalidation?' → use application-level cache."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-caching.html

**Deployment Strategy: Canary vs Blue-Green vs Automatic**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Canary (REST API) | API Gateway canary deployment settings | Gradual traffic shift, risk reduction, isolated metrics | REST API only, manual promotion/rollback, limited to single stage | High-risk API changes, REST APIs, production deployments requiring validation |
  | Blue-Green (Custom Domain) | Custom domain name + base path mapping switch | Instant rollback (switch mapping back), zero-downtime, any API type | Requires two deployed APIs simultaneously, DNS/mapping propagation time | Major version transitions, API type migrations, any API type (REST or HTTP) |
  | Automatic (HTTP API) | HTTP API auto-deploy | Speed (changes deploy immediately on save), simplicity | No gradual rollout, no canary, immediate exposure of all changes | Development stages, low-risk changes, HTTP APIs, rapid iteration environments |

- Architect Instruction: "Ask 'What is the blast radius if this deployment fails?' — high blast radius (public production API) → canary (REST) or blue-green (any). Low blast radius (internal, dev) → automatic deployment."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/canary-release.html

---

### 🚫 Anti-Patterns

**Deploying APIs Without Authorization**
- Risk Level: CRITICAL
- Why: Security pillar violation — "Implement a strong identity foundation." An unauthorized API Gateway endpoint is publicly accessible immediately upon deployment. Attackers continuously scan for open API endpoints. An open endpoint enables data exfiltration, backend abuse, cost amplification (attacker triggers millions of Lambda invocations at your expense), and regulatory violations.
- Instead:
  Configure authorization on EVERY method/route. Use `AWS_IAM` for service-to-service, `COGNITO_USER_POOLS` or `JWT` for user-facing, `CUSTOM` Lambda authorizer for custom schemes. For REST APIs, set the method's `authorizationType` to a non-NONE value. For HTTP APIs, set the route's `authorizationType`.
- Detection:
  ```bash
  # REST APIs — find unauthorized methods
  aws apigateway get-resources --rest-api-id <API_ID> --query "items[].resourceMethods" | grep '"authorizationType": "NONE"'
  # HTTP APIs — find unauthorized routes
  aws apigatewayv2 get-routes --api-id <API_ID> --query "Items[?AuthorizationType=='NONE'].RouteKey"
  # AWS Config Rule: api-gw-associated-with-waf (for WAF check)
  ```
- Impact: Data breach, unauthorized data access, cost amplification attack, compliance violation (PCI-DSS, SOC2, GDPR), regulatory fines.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html

**Using API Keys as the Sole Authorization Mechanism**
- Risk Level: CRITICAL
- Why: Security pillar violation — API keys are identifiers, NOT security credentials. AWS documentation explicitly states: "Don't rely on API keys as your only means of authentication and authorization for your APIs." API keys can be easily guessed (alphanumeric strings), shared without audit, embedded in client applications, leaked in logs, and brute-forced. They provide zero cryptographic proof of caller identity.
- Instead:
  Use API keys ONLY for usage tracking and throttling (via usage plans). ALWAYS combine API keys with a proper authorizer: IAM (SigV4), Lambda authorizer (token validation), Cognito, or JWT. The API key identifies *which client* is calling; the authorizer validates *who* the caller is.
- Detection:
  ```bash
  # Find REST API methods with apiKeyRequired=true but authorizationType=NONE
  # This combination means "API key required but no real authorization" — anti-pattern
  aws apigateway get-resources --rest-api-id <API_ID> --query "items[].resourceMethods"
  # Look for methods with apiKeyRequired: true AND authorizationType: NONE
  ```
- Impact: Unauthorized access, data breach, API abuse, cost amplification — with no audit trail of WHO accessed the API (only which API key was used, which can be shared among many users).
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html

**No Throttling — Relying on Default Account Limits**
- Risk Level: HIGH
- Why: Reliability pillar violation — "Scale horizontally to increase aggregate workload availability." The default account-level throttle (10,000 RPS, 5,000 burst) is shared across ALL APIs in the region. Without per-stage and per-method throttling, one API can monopolize the entire account quota, causing 429 errors for unrelated APIs. Additionally, backends (Lambda, databases) have their own limits — unthrottled API traffic can overwhelm downstream services.
- Instead:
  Configure throttling at three levels: (1) Request account-level increase from AWS Support to match production requirements; (2) Set stage-level defaults below account limit; (3) Set method-level limits for expensive operations. Use usage plans for per-client throttling in multi-tenant scenarios.
- Detection:
  ```bash
  aws apigateway get-stage --rest-api-id <API_ID> --stage-name prod --query "methodSettings"
  # If empty or all values are 0 (unlimited) — anti-pattern
  # Check for 429 errors in CloudWatch: AWS/ApiGateway metric "Count" with 429 status
  ```
- Impact: Service outage (all APIs in region throttled), backend service overload, cascading failures, degraded user experience, SLA violations.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html

**Public REST APIs Without AWS WAF**
- Risk Level: HIGH
- Why: Security pillar violation — "Apply security at all layers." A public REST API without WAF is exposed to: SQL injection, cross-site scripting (XSS), path traversal, bot attacks, credential stuffing, HTTP flood DDoS, and known vulnerability exploitation. API Gateway's native throttling does not provide application-layer protection.
- Instead:
  Attach a WAF web ACL to every public REST API stage with: AWSManagedRulesCommonRuleSet, AWSManagedRulesKnownBadInputsRuleSet, and a rate-based rule (IP-level rate limit). For APIs accepting user-generated content, add AWSManagedRulesSQLiRuleSet.
- Detection:
  ```bash
  aws apigateway get-stages --rest-api-id <API_ID> --query "item[?webAclArn==null || webAclArn==''].stageName"
  # Any production stage without webAclArn = unprotected
  ```
- Impact: Data breach via injection, service degradation via DDoS, bot abuse, compliance violation, financial loss from credential stuffing.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html

**Disabling Access Logging in Production**
- Risk Level: HIGH
- Why: Operational Excellence and Security pillar violation — "Enable traceability" and "Anticipate failure." Without access logging, you cannot: detect abnormal traffic patterns, investigate 4XX/5XX spikes, identify slow integrations, trace security incidents, measure SLA compliance, or demonstrate audit compliance. Operations teams are blind to API behavior.
- Instead:
  Enable CloudWatch access logging on EVERY production stage with JSON format. Include: requestId, ip, caller, user, requestTime, httpMethod, resourcePath, status, responseLength, integrationLatency, responseLatency. Set log group retention policy (30-90 days). Configure metric filters for 5XX rates and latency thresholds.
- Detection:
  ```bash
  aws apigateway get-stage --rest-api-id <API_ID> --stage-name prod --query "accessLogSettings"
  # null or empty = access logging disabled — anti-pattern
  ```
- Impact: Blind to security incidents, unable to debug production issues, SLA measurement impossible, compliance audit failure, extended MTTR for outages.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html

**Using Default execute-api Domain in Production**
- Risk Level: MEDIUM
- Why: Operational Excellence pillar violation — "Make frequent, small, reversible changes." The default URL (`{api-id}.execute-api.{region}.amazonaws.com`) creates a hard dependency between consumers and your API implementation. Recreating an API (for any reason) generates a new API ID, breaking all consumers. You cannot do blue-green deployments, API migrations, or disaster recovery without consumer impact.
- Instead:
  Always configure custom domain names for production APIs. Use Route 53 alias records. Use base path mappings for versioning. This enables: API replacement without consumer impact, blue-green deployments (switch base path mapping), multi-region failover (Route 53 health checks + failover routing).
- Detection:
  ```bash
  # Check if any production API is invoked via execute-api URL
  # Review access logs for Host header containing "execute-api.amazonaws.com"
  # Check if custom domain names are configured
  aws apigateway get-domain-names --query "items[].domainName"
  ```
- Impact: Consumer breakage on API recreation, inability to perform blue-green deployments, no multi-region failover capability, no clean URL structure for API consumers.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html

**Hardcoding Stage-Specific Values in API Definition**
- Risk Level: MEDIUM
- Why: Operational Excellence pillar violation — "Perform operations as code" with environment-agnostic definitions. Hardcoding Lambda ARNs, endpoint URLs, or configuration values in the API definition creates per-environment API definitions that drift, require separate maintenance, and make promotions between stages error-prone.
- Instead:
  Use stage variables (`${stageVariables.variableName}`) in integration URIs, Lambda function names, and HTTP endpoints. Define stage variables per stage (dev, staging, prod) to inject environment-specific values at runtime. Use Lambda aliases (dev, staging, prod) referenced via stage variables: `arn:aws:lambda:{region}:{account}:function:${stageVariables.functionName}`.
- Detection:
  ```bash
  aws apigateway get-resources --rest-api-id <API_ID> --query "items[].resourceMethods"
  # Inspect integration URIs — if they contain specific account IDs, region names, or
  # environment identifiers rather than stageVariables references = hardcoded
  ```
- Impact: Environment drift, deployment errors when promoting between stages, inability to use single API definition across environments, increased maintenance burden.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/aws-api-gateway-stage-variables-reference.html

**29-Second Integration Timeout Without Backend Optimization**
- Risk Level: MEDIUM
- Why: Performance Efficiency pillar violation. REST APIs have a maximum (and default) integration timeout of 29 seconds. HTTP APIs have a maximum of 30 seconds. If backends regularly approach this limit, clients experience unacceptable latency, and timeout errors appear as 504 Gateway Timeout. This often indicates a synchronous operation that should be asynchronous.
- Instead:
  Set integration timeouts to the expected P99 backend response time + buffer (e.g., if P99 = 3s, set timeout = 5s). For long-running operations (>10s), convert to asynchronous pattern: API Gateway → Lambda → SQS/Step Functions → callback/polling. Use API Gateway response streaming for large payloads. Return 202 Accepted with a status polling URL for operations that cannot complete within timeout.
- Detection:
  ```bash
  # Check for 504 errors in CloudWatch metrics
  # AWS/ApiGateway → 5XXError (filtered for IntegrationTimeout)
  # Review integrationLatency P99 approaching 29 seconds
  aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway --metric-name IntegrationLatency \
    --dimensions Name=ApiName,Value=<API_NAME> --statistics p99 --period 300
  ```
- Impact: 504 timeout errors returned to clients, degraded user experience, potential cascading timeouts upstream, wasted Lambda compute time for requests that will timeout regardless.
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html

---

## Cloud-Native Design Patterns

**API Gateway as Backend-for-Frontend (BFF)**
- Category: Communication
- Problem: Different client types (web, mobile, IoT, third-party) have different data requirements, latency tolerances, and protocol needs. A single monolithic API forces all clients to consume the same response format.
- Solution on AWS:
  Deploy separate API Gateway APIs per client type: (1) Web BFF (REST API with caching for browser clients), (2) Mobile BFF (HTTP API with minimal payloads for mobile clients), (3) Partner API (REST API with usage plans, API keys, throttling for third-party consumers). Each BFF aggregates calls to shared microservices via Lambda orchestration or Step Functions.
- Services Used: API Gateway REST API (web BFF, partner API), API Gateway HTTP API (mobile BFF), Lambda (orchestration), Step Functions (complex aggregation), CloudFront (web caching)
- When to Apply: Multiple client types with divergent needs; mobile requiring smaller payloads; partners requiring rate limiting; different authorization models per consumer type
- When NOT to Apply: Single client type; simple CRUD with uniform requirements; premature optimization before client divergence is real
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Flexibility | Each client gets optimized API contract | Multiple APIs to maintain |
  | Performance | Tailored response sizes per client | Duplication of some routing logic |
  | Security | Per-consumer-type authorization | More authorization configurations |

- Complements: Microservices decomposition, CQRS (read-optimized BFF), GraphQL (alternative to multiple BFFs)
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/bff-pattern.html

**API Gateway Direct Service Integration (Lambda-less)**
- Category: Communication / Cost Optimization
- Problem: Many API operations are simple pass-through to AWS services — queue a message, start a workflow, store data. Using Lambda as middleware adds cold start latency, invocation cost, and a failure point without adding business logic.
- Solution on AWS:
  Use API Gateway AWS service integration type to directly invoke AWS services without Lambda. Configure VTL mapping templates to transform the API request into the target service's API format. Examples: `POST /orders` → SQS SendMessage; `POST /workflows` → Step Functions StartExecution; `GET /items/{id}` → DynamoDB GetItem; `PUT /files/{key}` → S3 PutObject.
- Services Used: API Gateway REST API (AWS service integration, VTL mapping templates), target services (SQS, Step Functions, DynamoDB, S3, SNS, Kinesis, EventBridge)
- When to Apply: Simple operations with no business logic between API and service; cost-sensitive workloads; latency-sensitive operations where Lambda cold start is unacceptable
- When NOT to Apply: Complex business logic required; multi-step operations; error handling beyond simple mapping; operations requiring orchestration across multiple services
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Eliminates Lambda invocation cost entirely | VTL templates are harder to test/debug |
  | Latency | Removes Lambda cold start (50-500ms savings) | Limited error handling capabilities |
  | Reliability | Fewer components in the request path | Tighter coupling to AWS service APIs |

- Complements: Event-driven architecture (API → SQS → Lambda), Step Functions orchestration (API → Step Functions → multiple services)
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/getting-started-aws-proxy.html

**Asynchronous Request-Response via API Gateway**
- Category: Resilience / Scalability
- Problem: Long-running operations (file processing, ML inference, batch jobs, report generation) cannot complete within API Gateway's 29-second timeout. Synchronous patterns fail for operations taking minutes to hours.
- Solution on AWS:
  Implement the async request-response pattern: (1) Client sends request → API Gateway → Lambda (fast) → writes job to DynamoDB + sends to SQS/Step Functions → returns 202 Accepted with `Location: /jobs/{jobId}`; (2) Backend processes asynchronously; (3) Client polls `GET /jobs/{jobId}` (API Gateway → DynamoDB GetItem) or receives callback via WebSocket/SNS/webhook. Alternative: use API Gateway + Step Functions with `StartSyncExecution` for Express workflows (up to 5 minutes) or `StartExecution` for Standard workflows (up to 1 year).
- Services Used: API Gateway (REST/HTTP API), Lambda (request acceptor), DynamoDB (job state), SQS/Step Functions (async processing), WebSocket API or SNS (completion notification)
- When to Apply: Operations exceeding 10-second response time; batch processing; ML inference; file conversions; report generation; any operation where the client doesn't need an immediate result
- When NOT to Apply: Sub-second operations; operations where immediate response is business-critical; simple CRUD
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scalability | Decouples request rate from processing rate | Client must handle async flow (polling/callbacks) |
  | Reliability | Request never times out; retries are backend-managed | Additional state management (DynamoDB job table) |
  | User Experience | Fast acknowledgment (202 Accepted) | Eventual consistency; client complexity |

- Complements: CQRS, Event sourcing, Saga pattern (for multi-step async operations)
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/async-api.html

**API Gateway + Lambda + Step Functions Orchestration**
- Category: Communication / Resilience
- Problem: Complex API operations require orchestrating multiple downstream services (validate → transform → store → notify → respond). Implementing orchestration in a single Lambda creates monolithic functions that are hard to test, debug, and maintain.
- Solution on AWS:
  API Gateway → Lambda (thin adapter: validate input, return 202) → Step Functions (orchestrate workflow: parallel branches, retries, error handling, wait states) → multiple service integrations (DynamoDB, SQS, SNS, Lambda tasks). For synchronous orchestration under 5 minutes, use Express Workflows with `StartSyncExecution` integration from API Gateway. For longer processes, use Standard Workflows with async pattern.
- Services Used: API Gateway (entry point), Step Functions Express/Standard (orchestration), Lambda (business logic tasks), DynamoDB (state), SNS/SQS (notifications, buffering)
- When to Apply: Multi-step business processes; operations requiring retries, parallel execution, or conditional branching; workflows needing human approval steps; saga pattern implementation
- When NOT to Apply: Single-step operations; simple CRUD; operations completing in <1 second with no orchestration needs
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Reliability | Built-in retries, error handling, compensation | Step Functions pricing ($25/M state transitions) |
  | Observability | Visual workflow execution, built-in tracing | Additional service to learn and manage |
  | Maintainability | Each step is independently testable | State machine definition complexity (ASL) |

- Complements: Saga pattern (compensating transactions), Event sourcing, CQRS
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/connect-api-gateway.html

**Multi-Region API with Route 53 Failover**
- Category: Resilience
- Problem: A single-region API Gateway deployment fails if the entire region becomes unavailable. For mission-critical APIs with aggressive availability SLAs (99.99%+), single-region architecture is insufficient.
- Solution on AWS:
  Deploy identical API Gateway APIs in two or more regions. Use custom domain name with regional endpoints in each region. Create Route 53 health checks for each regional API. Configure Route 53 failover routing policy (primary/secondary) or latency-based routing (active-active). Backend state must be replicated cross-region (DynamoDB Global Tables, Aurora Global Database). Use ACM certificates in each region for the custom domain.
- Services Used: API Gateway Regional endpoints (multi-region), Route 53 (health checks, failover/latency routing), ACM (per-region certificates), DynamoDB Global Tables or Aurora Global DB (data replication)
- When to Apply: 99.99%+ availability requirements; global user base needing low-latency access; regulatory requirements for data residency; DR requirements with RTO < 5 minutes
- When NOT to Apply: Standard availability requirements (99.9%); single-region user base; cost-sensitive workloads where regional redundancy is prohibitive
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Survives full region failure | 2x+ infrastructure cost |
  | Latency | Users routed to nearest region | Data replication lag (DynamoDB: <1s, Aurora: <1s) |
  | Complexity | Transparent failover for clients | Cross-region deployment pipeline, data consistency challenges |

- Complements: DynamoDB Global Tables, Aurora Global Database, CloudFront (edge caching), Route 53 health checks
- Source: https://docs.aws.amazon.com/whitepapers/latest/real-time-communication-on-aws/cross-region-active-active-pattern.html

**Request Validation at API Gateway (Shift-Left)**
- Category: Resilience / Performance
- Problem: Invalid requests that pass through to backend services waste Lambda invocations, increase latency, and complicate error handling. Backends must defensively validate every request, duplicating validation logic.
- Solution on AWS:
  Enable request validation on REST APIs using JSON Schema models. Validate: request body (JSON Schema), required headers, required query parameters, required path parameters. Invalid requests return 400 Bad Request directly from API Gateway without invoking the backend. Define reusable models for common request structures.
- Services Used: API Gateway REST API (request validators, models/schemas)
- When to Apply: All REST APIs with structured request bodies; APIs with required parameters; APIs where backend invocation cost should be minimized; APIs with strict contract enforcement
- When NOT to Apply: HTTP APIs (not supported); APIs with dynamic/unstructured payloads; file upload endpoints; APIs where backend needs to provide custom validation error messages
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Avoids Lambda invocations for invalid requests | JSON Schema maintenance |
  | Latency | Invalid requests rejected immediately | Schema validation adds ~1-2ms |
  | Reliability | Backend receives only valid requests | Limited to JSON Schema validation (no business rule validation) |

- Complements: Lambda input validation (business rules), API contract-first design (OpenAPI), contract testing
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-method-request-validation.html

---

## Security Architecture

**Identity & Access Management for API Gateway**
- AWS Services:
  - IAM (SigV4 authorization for service-to-service, resource policies for cross-account/IP restriction)
  - Lambda Authorizers (custom token validation, external IdP integration, RBAC/ABAC)
  - Amazon Cognito (managed user pools, OAuth2/OIDC, MFA, federation with SAML/social providers)
  - JWT Authorizers (HTTP APIs only, standard OIDC token validation with any compliant IdP)
  - AWS WAF (rate limiting, IP blocking, geo-blocking, managed rule groups)
  - API Keys + Usage Plans (client identification and throttling — NOT authentication)
- Architecture:
  Layer authorization: (1) Network-level: resource policies restrict by IP/VPC endpoint; (2) Authentication: verify caller identity (IAM SigV4, Cognito token, JWT, custom token via Lambda authorizer); (3) Authorization: determine permitted actions (IAM policy, Lambda authorizer policy document, Cognito scopes); (4) Rate control: usage plans enforce per-client throttles; (5) Application-layer protection: WAF rules filter malicious requests. Each layer operates independently — a request must pass ALL layers.
- Configuration Essentials:
  - Lambda authorizer cache TTL: 300 seconds (default) — reduce for high-security scenarios, increase for cost optimization
  - Resource policy conditions: use `aws:SourceVpc`, `aws:SourceVpce`, `aws:SourceIp` for network restrictions
  - Cognito scopes: define resource servers and scopes for fine-grained access control
  - WAF rate-based rules: 100-10,000 requests per 5-minute window per IP
- Verification:
  ```bash
  # Verify all methods have authorization
  aws apigateway get-resources --rest-api-id <API_ID> --query "items[].resourceMethods"
  # Verify WAF association
  aws wafv2 get-web-acl-for-resource --resource-arn arn:aws:apigateway:<region>::/restapis/<API_ID>/stages/prod
  # Verify resource policy
  aws apigateway get-rest-api --rest-api-id <API_ID> --query "policy"
  ```
- Compliance Alignment: SOC2 CC6.1 (logical access), PCI-DSS 7.1 (access controls), HIPAA 164.312(a)(1) (access control), GDPR Art.32 (security of processing)
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html

**Network Security — Private APIs and VPC Integration**
- AWS Services:
  - API Gateway Private Endpoints (REST APIs accessible only via VPC interface endpoints)
  - VPC Interface Endpoints (PrivateLink-powered, private connectivity to API Gateway)
  - VPC Links (connect API Gateway to private backends via NLB/ALB)
  - Security Groups (control traffic to VPC endpoints and VPC Link targets)
  - Resource Policies (restrict API access to specific VPC endpoints or source VPCs)
  - VPC Endpoint Policies (restrict which APIs a VPC endpoint can access)
- Architecture:
  For internal-only APIs: Deploy as Private REST API → create VPC Interface Endpoint for `execute-api` service → attach resource policy restricting access to specific VPC endpoint IDs → attach VPC endpoint policy restricting which APIs the endpoint can invoke. For public APIs with private backends: Deploy as Regional REST/HTTP API → create VPC Link (NLB for REST, ALB/NLB for HTTP API) → connect integration to VPC Link → backends remain in private subnets. For fully private end-to-end: combine Private API endpoint + VPC Link to private backend.
- Configuration Essentials:
  - Private API resource policy MUST include `aws:SourceVpce` condition — without it, the API is inaccessible
  - Enable Private DNS on VPC endpoint for cleaner invocation URLs
  - VPC Link targets (NLB/ALB) must have health checks configured
  - Security groups on VPC endpoint: allow inbound from client subnets on port 443
- Verification:
  ```bash
  # Verify VPC endpoint exists for execute-api
  aws ec2 describe-vpc-endpoints --filters Name=service-name,Values=com.amazonaws.<region>.execute-api
  # Verify private API resource policy includes VPC endpoint condition
  aws apigateway get-rest-api --rest-api-id <PRIVATE_API_ID> --query "policy"
  # Verify VPC Link status
  aws apigateway get-vpc-links --query "items[].status"
  # Must be AVAILABLE
  ```
- Compliance Alignment: SOC2 CC6.6 (network controls), PCI-DSS 1.3 (network segmentation), HIPAA 164.312(e)(1) (transmission security)
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-private-apis.html

**Data Security — Encryption and Data Protection**
- AWS Services:
  - TLS 1.2 (enforced for all API Gateway endpoints — in-transit encryption)
  - Mutual TLS (client certificate authentication for B2B)
  - AWS Certificate Manager (TLS certificate management, auto-renewal)
  - CloudTrail (audit trail for API management operations)
  - CloudWatch Logs (access logs — optionally encrypted with KMS)
  - Request validation (prevent malformed data from reaching backends)
- Architecture:
  All data in transit is encrypted via TLS 1.2 (minimum, non-configurable downgrade). API Gateway does not store request/response data at rest (ephemeral processing only). Logs stored in CloudWatch can be encrypted with KMS customer-managed keys. For B2B with client identity requirements, enable mutual TLS on custom domain names. Certificate chains in S3 truststore, revocation via CRL (Certificate Revocation List) in truststore.
- Configuration Essentials:
  - TLS 1.2 is the default minimum — REST APIs support TLS policy selection for TLS 1.2 only
  - mTLS truststore: S3 bucket with PEM-encoded CA certificates, versioned for rollback
  - CloudWatch Logs encryption: configure KMS key on log group for sensitive access log data
  - Client certificates for backend authentication (REST API only): API Gateway presents a certificate to backend for mutual auth
- Verification:
  ```bash
  # Test TLS minimum version (should reject TLS 1.0/1.1)
  openssl s_client -connect <api-id>.execute-api.<region>.amazonaws.com:443 -tls1_1
  # Should fail with handshake error

  # Verify mTLS configuration
  aws apigateway get-domain-name --domain-name api.example.com --query "mutualTlsAuthentication"
  ```
- Compliance Alignment: PCI-DSS 4.1 (encryption in transit), HIPAA 164.312(e)(2)(ii) (encryption), SOC2 CC6.7 (data in transit)
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-mutual-tls.html

---

## Operational Patterns

**Observability: API Gateway Monitoring Stack**
- AWS Services:
  - CloudWatch Metrics (request count, latency, 4XX/5XX errors, integration latency, cache hit/miss)
  - CloudWatch Access Logs (per-request details: caller, method, status, latency)
  - CloudWatch Execution Logs (detailed request/response logging for debugging — REST APIs)
  - AWS X-Ray (distributed tracing across API Gateway → Lambda → downstream)
  - CloudWatch Alarms (threshold-based alerting on error rates and latency)
  - CloudWatch Dashboards (operational visibility)
- Architecture:
  Three monitoring tiers: (1) Metrics — CloudWatch metrics per API/stage/method for aggregate behavior (request rate, error rate, latency percentiles); (2) Logs — access logs for per-request analysis (who called what, when, response code, latency breakdown); (3) Traces — X-Ray for end-to-end latency root cause across API Gateway → Lambda → DynamoDB/SQS/etc. Dashboard shows: requests/sec, 4XX rate, 5XX rate, P50/P90/P99 latency, integration latency, cache hit ratio. Alarms trigger on: 5XX > 1% sustained 5 minutes, P99 latency > SLA threshold, throttle count > 0.
- Cost Profile: Medium. CloudWatch Metrics: free (API Gateway publishes default metrics at no cost). Access Logs: $0.50/GB ingested + $0.03/GB stored. X-Ray: $5.00/M traces sampled. Dashboards: $3.00/month per dashboard.
- Automation:
  - Auto-scaling: API Gateway auto-scales (no user action); configure Lambda reserved concurrency to prevent cold starts under load
  - Alarms → SNS → Lambda: automated runbook execution (e.g., block abusive IP via WAF rule update)
  - Execution logs: enable on-demand for debugging, disable after resolution (expensive in production)
- Runbook Skeleton:
  1. Detection: CloudWatch alarm fires (5XX > 1% for 5 minutes)
  2. Triage: Check access logs — is it one method or all? One client or all? Check integration latency — is backend slow?
  3. Resolution: If backend timeout → scale backend / invoke failover. If Lambda error → check Lambda logs/X-Ray. If throttling → check account limits / increase stage throttle.
  4. Post-mortem: Document root cause, update throttle limits, add missing alarms
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/monitoring-cloudwatch.html

**High Availability: Multi-AZ and Regional Resilience**
- RTO/RPO: API Gateway is inherently multi-AZ (managed by AWS). RTO = 0 for AZ failure (automatic). For regional failure: RTO = DNS TTL (60-300 seconds with Route 53 health checks), RPO depends on data replication strategy.
- AWS Services:
  - API Gateway (inherently multi-AZ, managed HA)
  - Route 53 (health checks, failover routing for multi-region)
  - CloudFront (edge-optimized endpoint provides additional resilience layer)
  - DynamoDB Global Tables (cross-region data replication for stateful backends)
- Architecture:
  Single-region: API Gateway is multi-AZ by default — no user configuration for AZ-level HA. Multi-region active-passive: deploy API in two regions, Route 53 failover routing with health checks on primary, DNS failover to secondary on primary failure. Multi-region active-active: deploy in multiple regions, Route 53 latency-based routing, all regions serve traffic, data replicated via DynamoDB Global Tables or Aurora Global Database.
- Cost Profile: Single-region HA = included (no extra cost). Multi-region = 2x API Gateway cost + Route 53 health checks ($0.50-$0.75/month per check) + data replication cost (DynamoDB Global Tables: 2x write cost for replicated writes).
- Automation:
  - Route 53 health checks: automated failover (no human intervention)
  - CloudWatch cross-region dashboards: single pane of glass for multi-region APIs
  - Infrastructure as Code: identical deployments to multiple regions via CI/CD pipeline
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/plan-for-disaster-recovery-dr.html

**Cost Optimization: API Gateway FinOps**
- AWS Services:
  - API Gateway (pricing per request type: REST $3.50/M, HTTP $1.00/M, WebSocket $1.00/M messages + $0.25/M connection minutes)
  - API Caching (REST only: $0.02-$3.80/hour depending on size)
  - CloudWatch (usage metrics for cost attribution)
  - AWS Cost Explorer (API Gateway cost breakdown)
- Architecture:
  Cost optimization levers: (1) Choose HTTP API over REST API when features permit (70% cost reduction); (2) Enable API caching for read-heavy endpoints (reduces backend invocations); (3) Use direct AWS service integrations (eliminates Lambda cost for simple operations); (4) Optimize Lambda authorizer caching (reduce invocations); (5) Use long-running WebSocket connections instead of HTTP polling (reduces request count); (6) Implement request validation to reject invalid requests before backend invocation.
- Cost Profile:
  | Traffic (requests/month) | REST API Cost | HTTP API Cost | Savings |
  |--------------------------|---------------|---------------|---------|
  | 1M | $3.50 | $1.00 | 71% |
  | 100M | $350 | $100 | 71% |
  | 1B | $3,500 | $900 | 74% |
- Automation:
  - Budget alerts: CloudWatch billing alarm at 80%/100% of monthly API Gateway budget
  - Cost anomaly detection: AWS Cost Anomaly Detection for unexpected API traffic spikes
  - Cache hit ratio monitoring: if < 80%, review cache key parameters and TTL settings
- Source: https://aws.amazon.com/api-gateway/pricing/

**Change Management: Safe Deployment Patterns**
- AWS Services:
  - API Gateway Canary Deployments (REST API traffic splitting)
  - Custom Domain Base Path Mappings (blue-green deployment)
  - Stage Variables (environment-specific configuration without redeployment)
  - CloudFormation/SAM/CDK (infrastructure as code for reproducible deployments)
  - Lambda Aliases + Weighted Routing (code-level canary within API Gateway)
- Architecture:
  Deployment pipeline stages: (1) PR validation — deploy to ephemeral stage, run integration tests; (2) Dev — automatic deployment on merge to main; (3) Staging — deploy with canary (10% traffic for 15 minutes), monitor error rates and latency; (4) Production — promote canary to 100% if metrics are green, rollback if degraded. For HTTP APIs (no canary support): use blue-green via custom domain name — deploy new version to new stage, switch base path mapping, monitor, rollback mapping if needed.
- Cost Profile: Low. Canary deployments: no additional cost (same API). Blue-green: brief period of two active deployments (negligible for API Gateway serverless pricing). Stage variables: free.
- Automation:
  - CI/CD pipeline: CodePipeline/GitHub Actions → SAM deploy → canary configuration → CloudWatch alarm-based auto-rollback
  - Canary auto-promote: Step Functions workflow monitoring CloudWatch metrics, promoting or rolling back automatically
  - Rollback: SAM `sam deploy --rollback` or CloudFormation stack rollback
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/canary-release.html

---

## Reference Architectures

**Serverless REST API (Standard Pattern)**
- Context: Production API serving external consumers with authentication, throttling, caching, and WAF protection
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge Protection | AWS WAF | Application-layer firewall, rate limiting, bot control |
  | API Management | API Gateway REST API (Regional) | Routing, authorization, validation, caching, throttling |
  | Custom Domain | Route 53 + ACM | DNS routing, TLS termination |
  | Authorization | Cognito User Pools OR Lambda Authorizer | User authentication, token validation |
  | Compute | AWS Lambda | Business logic execution |
  | Data | DynamoDB | Primary data store |
  | Async Processing | SQS + Lambda | Background job processing |
  | Monitoring | CloudWatch + X-Ray | Metrics, logging, tracing |

- Key Decisions: REST vs HTTP API (choose REST for WAF + caching + validation); Regional vs Edge-optimized (choose Regional if managing own CloudFront); Cognito vs Lambda authorizer (choose Cognito for standard OAuth2; Lambda for custom schemes)
- Scaling Path: Start with default account limits → request increase as traffic grows → add caching to reduce backend load → add multi-region deployment for HA requirements → consider AppSync for GraphQL needs at scale
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/create-a-rest-api-for-microservices-by-using-amazon-api-gateway-and-aws-lambda.html

**Internal Microservices API (Private)**
- Context: Internal API accessible only from within VPC for service-to-service communication
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Network Isolation | VPC Interface Endpoint | Private access to API Gateway |
  | API Management | API Gateway Private REST API | Internal API routing, IAM authorization |
  | Authorization | IAM (SigV4) | Service-to-service identity verification |
  | Network Policy | Resource Policy + VPC Endpoint Policy | Access restriction to specific VPCs/endpoints |
  | Compute | Lambda OR ECS (via VPC Link) | Backend services |
  | Service Discovery | Cloud Map (HTTP API) OR NLB (REST API) | Private backend routing |
  | Monitoring | CloudWatch + X-Ray | Observability |

- Key Decisions: Private REST API vs HTTP API with VPC Link (Private endpoint restricts callers; VPC Link connects to private backends — different concerns); IAM vs Lambda authorizer (IAM for AWS service-to-service; Lambda for non-AWS callers within VPC)
- Scaling Path: Start with single Private API → add VPC Links as backend services grow → add Cloud Map service discovery for dynamic backends → consider service mesh (App Mesh) if inter-service communication becomes complex
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-private-apis.html

**Event-Driven API (Async Pattern)**
- Context: API that accepts requests for long-running operations and processes them asynchronously
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Entry Point | API Gateway REST API | Request acceptance, validation |
  | Authorization | Lambda Authorizer OR Cognito | Caller authentication |
  | Request Acceptance | Lambda (fast) OR Direct SQS Integration | Validate and enqueue |
  | Job State | DynamoDB | Job status tracking |
  | Processing | Step Functions Standard Workflow | Orchestrated async processing |
  | Notification | SNS OR WebSocket API | Completion notification to clients |
  | Status Polling | API Gateway → DynamoDB GetItem (direct integration) | Job status retrieval |

- Key Decisions: Lambda request acceptor vs direct SQS integration (Lambda for complex validation; direct SQS for simple enqueue); SNS callback vs WebSocket vs polling (polling for simplest client; WebSocket for real-time; SNS for server-to-server)
- Scaling Path: Start with polling-based status → add WebSocket API for real-time notifications → add Step Functions for complex orchestration → add DynamoDB Streams for event-driven status updates
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/async-api.html

---

## Provider Differentiators

```
Differentiator: API Gateway Direct AWS Service Integration
Category: Communication / Cost Optimization
Unique Value: API Gateway can directly invoke 100+ AWS service actions without intermediate compute (Lambda). No other major API gateway (Kong, Apigee, Azure APIM) offers direct AWS service invocation with request/response transformation built into the gateway.
Architecture Impact: Enables zero-Lambda architectures for simple CRUD operations. API Gateway → DynamoDB, SQS, Step Functions, S3, SNS, Kinesis, EventBridge — all without Lambda invocation cost or cold start latency.
When to Leverage: Simple pass-through operations; cost-sensitive workloads at scale; latency-critical paths where Lambda cold start is unacceptable; simple queue/notification/storage operations.
Caveat: Requires VTL (Velocity Template Language) mapping templates which are poorly documented, difficult to debug, and have limited tooling. REST API only (HTTP APIs support limited service integrations via EventBridge). Error handling in VTL is limited compared to Lambda code.
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/getting-started-aws-proxy.html

Differentiator: WebSocket API (Managed Persistent Connections)
Category: Communication / Real-Time
Unique Value: Fully managed WebSocket connections at scale with per-message routing to different Lambda functions based on message content. Combined with the @connections API, enables backends to push messages to specific connected clients without managing connection state infrastructure.
Architecture Impact: Eliminates the need for self-managed WebSocket infrastructure (Socket.io, SignalR backends on EC2/ECS). Scales to hundreds of thousands of concurrent connections. Integrates with IAM and Lambda authorizers for connection-level authentication.
When to Leverage: Real-time applications (chat, live dashboards, gaming, collaborative editing); IoT device communication; scenarios requiring server-push to specific clients; replacing polling-based architectures.
Caveat: Connection state must be managed externally (DynamoDB for connection IDs). Maximum connection duration: 2 hours (idle timeout: 10 minutes). No built-in message ordering guarantees. 128 KB maximum frame size. Pricing: $1.00/M messages + $0.25/M connection minutes.
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-overview.html

Differentiator: Usage Plans + API Keys (B2B API Monetization)
Category: API Management
Unique Value: Built-in per-client throttling and quota management without external API management platforms. Associates API keys with specific rate limits and monthly quotas, enabling tiered API access (free/basic/premium) directly in the gateway. Developer portal (GA 2024) provides self-service API discovery for consumers.
Architecture Impact: Enables SaaS API monetization, partner API tiering, and multi-tenant rate isolation without implementing rate limiting logic in application code or deploying external API management tools (Kong, Apigee).
When to Leverage: B2B SaaS API products; partner integrations with different SLA tiers; freemium API models; multi-tenant APIs requiring per-tenant rate limiting.
Caveat: REST and WebSocket APIs only (NOT available on HTTP APIs). API keys are NOT security credentials — must be combined with proper authorization. Maximum 10,000 API keys per account per region. Usage plan quotas reset at midnight UTC (not configurable).
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html

Differentiator: Canary Release Deployments (Native Traffic Splitting)
Category: Change Management
Unique Value: Built-in canary deployment support at the API gateway level — split traffic between current and new deployments by percentage with independent CloudWatch metrics per canary. No external traffic management or service mesh required.
Architecture Impact: Enables risk-free production deployments with automatic rollback capability. Each canary gets isolated metrics (error rate, latency) enabling automated promotion/rollback decisions via CloudWatch alarms.
When to Leverage: Production API deployments requiring validation before full rollout; breaking changes that need gradual exposure; APIs with strict SLA requirements where untested changes are unacceptable.
Caveat: REST APIs only — HTTP APIs have no canary support. Canary splits at the stage level (not route/method level). Stage variables can differ between canary and production portions. Must manually promote or delete canary — no auto-promote based on metrics without custom automation.
Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/canary-release.html
```

---

## Scenario Coverage

**Standard Case**: Production serverless API for a web/mobile application
- Approach: REST API (Regional endpoint) + Cognito User Pools (authorization) + Lambda proxy integration + DynamoDB + AWS WAF + CloudWatch access logging + custom domain name (Route 53 + ACM). API caching enabled for GET endpoints. Usage plans for any third-party consumers.
- Key Decisions: REST vs HTTP API (REST for WAF + caching + validation + canary). Cognito vs Lambda authorizer (Cognito if it's the identity provider; Lambda if using Auth0/Okta/custom). Cache TTL per endpoint (balance freshness vs backend cost).

**Edge Case**: High-throughput API exceeding account throttle limits
- Approach: Request account-level throttle increase from AWS Support (document sustained traffic requirements). Implement API caching to reduce backend requests. Use CloudFront with Regional API for additional burst absorption. Consider multiple API Gateway APIs across regions with Route 53 latency routing for geographic load distribution. For extreme scale (>100,000 RPS sustained), evaluate ALB + ECS/EKS as an alternative to API Gateway for compute-intensive endpoints.
- Key Decisions: When to scale out (multi-region) vs scale up (quota increase). When API Gateway hits architectural limits vs when backend is the bottleneck.

**Anti-Pattern Case**: API deployed without authorization "for testing" that remains in production
- Clarification: "Ask: 'Is this API accessible from the public internet?' If YES, authorization MUST be configured before deployment — there is no valid 'temporary' exception for public-facing APIs. For internal testing, use Private API endpoints restricted to a development VPC, or deploy to a non-production stage with IAM authorization and restrict access to developer IAM roles. Never deploy an unauthorized public API endpoint, even temporarily."

---

## Service Equivalence Context

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **API Management** | API Gateway (REST/HTTP/WebSocket) | API Gateway / Apigee | API Management (APIM) | API Gateway |
| **API Gateway (Simple)** | HTTP API | API Gateway | — | — |
| **API Gateway (Full)** | REST API | Apigee | API Management | API Gateway |
| **WebSocket** | WebSocket API | — (Cloud Run/GKE-based) | SignalR Service | — (OKE-based) |
| **Developer Portal** | API Gateway Developer Portal | Apigee Developer Portal | APIM Developer Portal | — |
| **API Throttling** | Usage Plans + Stage Throttling | Apigee Rate Limiting | APIM Policies (rate-limit) | Rate Limiting Policies |
| **Request Validation** | Request Validators (REST API) | — | APIM Validate Policies | — |
| **Response Caching** | API Gateway Cache (REST API) | Apigee Response Cache | APIM Cache Policies | Response Caching |

> **⚠️ Important**: AWS API Gateway's REST and HTTP APIs are architecturally distinct products (V1 vs V2 infrastructure). Most other cloud providers offer a single API management product with tiered pricing. AWS's split creates a unique decision point that doesn't exist on other platforms.
