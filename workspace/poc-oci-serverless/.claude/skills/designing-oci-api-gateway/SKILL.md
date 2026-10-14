---
name: designing-oci-api-gateway
description: "Designs, secures, and operates REST APIs with OCI API Gateway for serverless architectures. Use when making API Gateway architecture decisions for OCI Functions, API Gateway, and IAM."
---

## Version Context

**Technology**: Oracle Cloud Infrastructure (OCI) API Gateway
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Architecture Domain**: API Gateway — serverless REST API architecture
**Target Edition**: OCI API Gateway (current stable, GA)
**Architecture Context**: Serverless API architecture with OCI Functions, API Gateway, and IAM
**Official Documentation**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/home.htm
**Support Status**: Active (GA, continuously updated)

**Key Capabilities (current stable)**:
- **Usage Plans & Subscriptions** — subscriber tiers with quotas and rate limits for API monetization
- **Response Caching** — server-side caching with configurable TTL, reducing backend invocations
- **Request Body Validation** — JSON Schema validation at the gateway before backend invocation
- **Dynamic Routing** — content-based routing (headers, query params, body) for multi-tenant and canary
- **Mutual TLS (mTLS)** — bidirectional certificate authentication for B2B scenarios
- **WebSocket support** — persistent bidirectional connections via protocol upgrade
- **Custom Domains with Certificates Service** — native TLS certificate management and auto-renewal

⚠️ **CRITICAL — Agent Warning**:
This skill covers **architecture and design decisions** for OCI API Gateway. For Terraform implementation, use the skill `provisioning-oci-api-gateway`. For Java function development behind API Gateway, use skills `developing-oci-functions-java` and `implementing-oci-functions-events`.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Design Patterns](#design-patterns)** — Architecture patterns and blueprints
- **[Security Architecture](#security-architecture)** — Defense in depth and WAF
- **[Advanced Patterns Documentation](#advanced-patterns)** — official docs: usage plans, dynamic routing, custom domains, response transforms
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **API Gateway as Single Entry Point** — All external traffic through Gateway. Never expose Functions directly
- **IAM Policies for Gateway-to-Function** — Three mandatory policies: fn-invocation, virtual-network-family, read repos
- **JWT Authentication at Gateway** — Edge validation with JWKS. Fail-fast before reaching Functions
- **Rate Limiting per Route** — Prevent cost explosion from DDoS (Functions billed per invocation)
- **CORS with explicit origins** — Never use wildcard with credentials

---

### ⚠️ Ask First

For complete decision matrices with examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Authentication Strategy** — JWT (standard IdP), Custom Authorizer (complex logic), Token (simple API keys)
- **Gateway Endpoint Type** — PUBLIC (internet-facing) vs PRIVATE (VCN-only)
- **Rate Limiting Strategy** — Per-route, per-client, or tiered limits

---

### 🚫 Never Do

For complete anti-patterns with examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Functions Exposed Without API Gateway** — Cost explosion, DDoS, unauthorized access
- **Wildcard CORS with Credentials** — Violates CORS spec, enables CSRF
- **No Rate Limiting** — Unbounded invocations, cost spike, resource exhaustion
- **Disabled SSL Verification on JWKS** — MITM attack enables authentication bypass

## Design Patterns

### API Façade Pattern
**Problem**: Clients interact with multiple backend services with different protocols, formats, and endpoints.
**Solution**: API Gateway aggregates backends under a single endpoint with request/response transformation.
```
/v1/orders     → ORACLE_FUNCTIONS_BACKEND (orders-service)
/v1/products   → HTTP_BACKEND (OKE container)
/v1/users      → ORACLE_FUNCTIONS_BACKEND (user-service)
/v1/config     → STOCK_RESPONSE_BACKEND (feature flags)
```
**When to apply**: Multiple backends with heterogeneous clients (web, mobile, third-party).
**When NOT to apply**: Single backend with single client (over-engineering).
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayoverview.htm

### API Versioning Pattern (Path-based)
**Problem**: APIs evolve but legacy clients cannot be forced to update.
**Solution**: Separate Deployments per version on the same Gateway.
```
/v1/* → Deployment: api-v1 (stable, deprecated)
/v2/* → Deployment: api-v2 (current)
/v3/* → Deployment: api-v3 (beta)
```
**When to apply**: Public APIs with multiple consumers that cannot be coordinated.
**When NOT to apply**: Internal APIs with full control over consumers (deploy lock-step).
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatingdeployment.htm

### Strangler Fig (API Migration) Pattern
**Problem**: Migrate monolithic API to microservices without downtime.
**Solution**: Gateway as "strangler proxy" — routes migrate incrementally from HTTP_BACKEND (monolith) to ORACLE_FUNCTIONS_BACKEND (new Functions).
```
Phase 1: All routes          → HTTP_BACKEND (monolith)
Phase 2: /v1/orders migrated → ORACLE_FUNCTIONS_BACKEND
         /v1/users           → HTTP_BACKEND (not yet migrated)
Phase 3: All routes          → ORACLE_FUNCTIONS_BACKEND
```
**When to apply**: Gradual migration from monolith to microservices.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingroutes.htm

### Multi-Tenant Routing Pattern
**Problem**: SaaS application with multiple tenants requiring compute/data isolation.
**Solution**: Dynamic Routing Backend based on tenant header or JWT claim.
```
Route: /v1/orders
Dynamic Routing Rules:
  if header "X-Tenant-Id" == "tenant-a" → Function: orders-tenant-a
  if header "X-Tenant-Id" == "tenant-b" → Function: orders-tenant-b
  default → Function: orders-shared
```
**When to apply**: SaaS with per-tenant isolation (compliance, performance guarantees).
**When NOT to apply**: Tenants with identical requirements (shared Function with tenant context suffices).
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingdynamicrouting.htm

---

## Security Architecture

### Defense in Depth — Layered Authentication

```
Client → [HTTPS/TLS 1.2+] → API Gateway
  Layer 1: mTLS (optional, B2B) — validate client certificate
  Layer 2: JWT Validation — validate token (issuer, audience, expiry, scope)
  Layer 3: Authorization Policy per route — AUTHENTICATION_ONLY, ANY_OF, ANONYMOUS
  Layer 4: Usage Plan — identify subscriber, enforce quota
  → [VCN Private Network] → Function
    Layer 5: Resource Principal — Function authenticates to OCI services
    Layer 6: IAM Policy — least-privilege access to specific services
      → [Service Gateway] → Autonomous DB / Vault / Object Storage
```

Each layer adds defense — compromise of one does not bypass others.

### WAF Integration (Public APIs)
OCI WAF deployed as Edge Policy provides:
- Bot detection and mitigation
- SQL injection / XSS protection
- Rate limiting at edge (before reaching gateway)
- Geo-blocking and IP reputation filtering
- Custom protection rules (regex on headers/body)

```bash
# Verify WAF protects against SQL injection
curl "https://<gw>/v1/users?id=1%20OR%201=1"
# Expected: 403 Forbidden (blocked by WAF)
```

**Source**: https://docs.oracle.com/en-us/iaas/Content/WAF/Concepts/overview.htm

---

## Verification Loop

The agent MUST execute after each API Gateway configuration change:

### 1. Validate IAM Policies
```bash
# Verify Dynamic Groups exist
oci iam dynamic-group list --compartment-id <tenancy_ocid> | \
# Exit code: 0 (success) | 1 (auth/network error)
  jq '.data[] | select(.name | contains("apigw")) | {name, matching_rule: .["matching-rule"]}'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)

# Verify policies exist
oci iam policy list --compartment-id <compartment_ocid> | \
# Exit code: 0 (success) | 1 (auth/network error)
  jq '.data[].statements[]' | grep -i "fn-invocation\|FaaS"
  # Exit code: 0 (match found) | 1 (no match)
```
**Expected output**: Dynamic Group with `ApiGateway` type and policies for `fn-invocation`, `virtual-network-family`, `read repos`.

### 2. Validate Gateway & Deployment
```bash
# Verify Gateway is in public subnet
oci api-gateway gateway get --gateway-id <gw_ocid> | jq '.data | {hostname, "endpoint-type", "subnet-id"}'
# Exit code: 0 (success) | 1 (parse error) | 5 (no output)

# Verify Deployment has rate limiting, auth, and logging
oci api-gateway deployment get --deployment-id <dep_ocid> | \
  jq '.data.specification | {
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
    rate_limiting: .request_policies.rate_limiting,
    auth: .request_policies.authentication.type,
    access_log: .logging_policies.access_log.is_enabled,
    execution_log: .logging_policies.execution_log.is_enabled
  }'
```
**Expected output**: `endpoint-type: PUBLIC`, rate_limiting configured, auth type set, both logs enabled.

### 3. Validate Network Isolation
```bash
# Verify Functions subnet is private (no public IPs)
APP_SUBNET=$(oci fn application get --application-id <app_ocid> | jq -r '.data["subnet-ids"][0]')
# Exit code: 0 (success) | 1 (auth/network error)
oci network subnet get --subnet-id "$APP_SUBNET" | jq '.data["prohibit-public-ip-on-vnic"]'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: true

# Verify NSG allows only 443 inbound
oci network nsg rules list --nsg-id <nsg_ocid> | \
# Exit code: 0 (success) | 1 (auth/network error)
  jq '.data[] | select(.source == "0.0.0.0/0" and .direction == "INGRESS")' | grep -v "443"
  # Exit code: 0 (match found) | 1 (no match)
# Expected: no output (only 443 allowed)
```

### 4. End-to-End Health Check
```bash
# Test health endpoint (anonymous)
curl -s https://<gateway-hostname>/v1/health | jq .
# Exit code: 0 (success) | 1 (connection error) | 22 (HTTP error with -f)
# Expected: {"status":"healthy"}, HTTP 200

# Test authenticated endpoint without token (should fail)
curl -s -o /dev/null -w "%{http_code}" https://<gateway-hostname>/v1/orders
# Exit code: 0 (success) | 1 (connection error) | 22 (HTTP error with -f)
# Expected: 401

# Test CORS preflight
curl -I -X OPTIONS \
# Exit code: 0 (success) | 1 (connection error) | 22 (HTTP error with -f)
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  https://<gateway-hostname>/v1/orders
# Expected: Access-Control-Allow-Origin header present
```

### 5. Validate TLS
```bash
# Verify TLS 1.2+ is active
openssl s_client -connect <gateway-hostname>:443 -tls1_2 < /dev/null 2>&1 | grep "Protocol\|Cipher"
# Exit code: 0 (match found) | 1 (no match)

# Verify TLS 1.0/1.1 are rejected
openssl s_client -connect <gateway-hostname>:443 -tls1 < /dev/null 2>&1 | grep "handshake failure"
# Exit code: 0 (match found) | 1 (no match)
# Expected: handshake failure
```

**Troubleshooting**:
- **502 Bad Gateway** → Missing IAM policy: `Allow dynamic-group <gw-group> to use fn-invocation`
- **401 Unauthorized (unexpected)** → JWT issuer/audience mismatch or JWKS URL unreachable
- **CORS errors in browser** → Missing or incorrect `allowed_origins` in CORS policy
- **Timeout on Function invoke** → Function timeout too short or cold start; consider provisioned concurrency
- **404 on route** → Path mismatch: route path is relative to Deployment path_prefix

---

## Quick Reference

### Service Limits (OCI API Gateway)

| Resource | Default Limit | Scope |
|----------|---------------|-------|
| Gateways per compartment | 50 | Regional |
| Deployments per gateway | 50 | Per gateway |
| Routes per deployment | 50 | Per deployment |
| Max rate limit per route | 1000 req/s | Per route |
| Request/Response body size | 10 MB | Per request |
| Custom domains per gateway | 5 | Per gateway |
| Request timeout (max) | 300 seconds | Per route |
| Response cache entry size | 5 MB | Per route |
| Usage plans per compartment | 50 | Regional |
| Subscribers per usage plan | 1000 | Per plan |

**Full limits**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Reference/apigatewaylimits.htm

### Pricing (OCI API Gateway)

Pricing changes without notice — always verify current rates before estimating costs.
See [OCI Pricing](https://www.oracle.com/cloud/pricing/) and [OCI Always Free](https://www.oracle.com/cloud/free/).

### Key Metrics to Monitor

| Metric | Alarm Threshold | Severity |
|--------|----------------|----------|
| `5xxCount / HttpRequests` | > 5% over 5 min | CRITICAL |
| `Latency` P99 | > 3000ms over 5 min | WARNING |
| `4xxCount` sudden increase | > 200% baseline over 1 min | HIGH |

### Essential OCI CLI Commands
```bash
# List gateways
oci api-gateway gateway list --compartment-id <compartment_ocid>

# Get deployment details
oci api-gateway deployment get --deployment-id <dep_ocid>

# List deployments for a gateway
oci api-gateway deployment list --compartment-id <compartment_ocid> --gateway-id <gw_ocid>

# Check execution logs for errors
oci logging search --search-query 'search "<log-group-ocid>" | where logContent = "*502*"' \
  --time-start <ISO> --time-end <ISO>
```

---

## Skill Cross-References

| Need | Use Skill |
|------|-----------|
| Terraform provisioning of Gateway, Deployments, Routes | `provisioning-oci-api-gateway` |
| Terraform provisioning of Dynamic Groups and IAM Policies | `provisioning-oci-iam` |
| Terraform provisioning of VCN, Subnets, NSGs | `provisioning-oci-networking` |
| Java function development for API Gateway backends | `developing-oci-functions-java` |
| Typed API Gateway request/response with fn-events | `implementing-oci-functions-events` |

---

## Production Readiness Checklist

- [ ] Gateway in public subnet with NSG (443 only inbound)
- [ ] Functions in private subnet (`prohibit_public_ip = true`)
- [ ] TLS 1.2+ verified (default, not disabled)
- [ ] Custom domain configured with certificate auto-renewal (if external-facing)
- [ ] JWT Authentication configured at Deployment level
- [ ] Rate limiting configured (CLIENT_IP or Usage Plans)
- [ ] CORS configured with explicit origins (no wildcard with credentials)
- [ ] Request body validation configured for routes with input
- [ ] Response caching enabled for cacheable GET routes
- [ ] Health check route (`/health`) with STOCK_RESPONSE_BACKEND and ANONYMOUS
- [ ] Access logs enabled (always)
- [ ] Execution logs enabled (ERROR in prod, INFO in staging)
- [ ] Dynamic Group for API Gateway created
- [ ] IAM Policy: gateway → fn-invocation (MANDATORY)
- [ ] IAM Policy: FaaS → virtual-network-family (MANDATORY)
- [ ] IAM Policy: FaaS → read repos (MANDATORY)
- [ ] OCI WAF configured fronting the gateway (public APIs)
- [ ] Monitoring alarms: 5xx rate, P99 latency, error spike
- [ ] Load test validated rate limits and latency under load

---

## External Resources

### Official Documentation
- [API Gateway Overview](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayoverview.htm) (verified 2026-07-26)
- [Creating a Gateway](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatinggateway.htm) (verified 2026-07-26)
- [Creating Deployments](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatingdeployment.htm) (verified 2026-07-26)
- [Adding Routes](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingroutes.htm) (verified 2026-07-26)
- [Using Functions Backend](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingoraclefunctionsbackend.htm) (verified 2026-07-26)

### Authentication & Security
- [Authentication Policies](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingauthenticationandrequestpolicies.htm) (verified 2026-07-26)
- [Custom Authorizer Functions](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingauthorizerfunction.htm) (verified 2026-07-26)
- [Mutual TLS (mTLS)](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaymtls.htm) (verified 2026-07-26)
- [CORS Configuration](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingcors.htm) (verified 2026-07-26)
- [Request Body Validation](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingbodyvalidation.htm) (verified 2026-07-26)
- [OCI WAF](https://docs.oracle.com/en-us/iaas/Content/WAF/Concepts/overview.htm) (verified 2026-07-26)
- [Network Security Groups](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm) (verified 2026-07-26)

### Operations & Monitoring
- [Rate Limiting](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingratelmiting.htm) (verified 2026-07-26)
- [Response Caching](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayresponsecaching.htm) (verified 2026-07-26)
- [Logging](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaymanaginglogs.htm) (verified 2026-07-26)
- [Metrics Reference](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Reference/apigatewaymetrics.htm) (verified 2026-07-26)
- [Service Limits](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Reference/apigatewaylimits.htm) (verified 2026-07-26)

### Advanced Patterns
- [Usage Plans & Subscriptions](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingusageplans.htm) (verified 2026-07-26)
- [Dynamic Routing](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingdynamicrouting.htm) (verified 2026-07-26)
- [Custom Domains](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingcustomdomains.htm) (verified 2026-07-26)
- [Response Transformations](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingresponsetransformations.htm) (verified 2026-07-26)

### Pricing & Free Tier
- [OCI Pricing](https://www.oracle.com/cloud/pricing/) — current rates (verify before cost estimation) (verified 2026-07-26)
- [OCI Always Free](https://www.oracle.com/cloud/free/) (verified 2026-07-26)
