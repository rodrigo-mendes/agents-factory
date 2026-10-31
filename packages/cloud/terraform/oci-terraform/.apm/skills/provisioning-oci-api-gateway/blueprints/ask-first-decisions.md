### ⚠️ Ask First

**Decision Point**: PUBLIC vs. PRIVATE Gateway Endpoint

| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| **PUBLIC** | External access, simplicity, no VPN needed | Attack surface (mitigated by rate limit + auth) | APIs for SPAs, mobile apps, external partners |
| **PRIVATE** | Zero internet exposure, internal-only | External consumers need VPN/FastConnect | Microservice-to-microservice, internal APIs, B2B with FastConnect |

**Agent Behavior**:
"Before configuring the gateway, ask the user:
'Will this API be consumed by external clients (internet/mobile/SPA) or only by internal services (microservices, VPN)?'"

**Decision Factors**:
- Consumer location (internet vs. internal network)
- Security posture requirements (zero-trust vs. perimeter)
- Network infrastructure (VPN/FastConnect available?)

**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatinggateway.htm

---

**Decision Point**: Authentication Strategy (JWT vs. Custom vs. Token)

| Option | Best For | Tradeoff |
|--------|----------|----------|
| **JWT_AUTHENTICATION** | OIDC/OAuth2 with public JWKS endpoint (Auth0, Keycloak, OCI Identity Domains) | Local validation (fast), no introspection support |
| **CUSTOM_AUTHENTICATION** | Multi-tenant auth, API keys, token introspection, complex logic | +latency (Function cold start), +cost per invocation |
| **TOKEN_AUTHENTICATION** | OAuth2 token introspection, remote token discovery | Depends on external endpoint, +latency |

**Agent Behavior**:
"Before implementing authentication, ask the user:
'Which identity provider will be used? Does it expose a public JWKS endpoint? Do you need API key validation or custom authorization logic?'"

**Decision Factors**:
- Identity provider type (OIDC-compliant vs. custom)
- Latency budget (JWT = ~0ms validation; Custom = cold start)
- Complexity of authorization rules

**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingauthentication.htm

---

**Decision Point**: Backend Type Selection

| Option | Best For | Pitfall |
|--------|----------|--------|
| **ORACLE_FUNCTIONS_BACKEND** | Serverless, event-driven, auto-scaling | Cold starts (2-5s Java), 300s max timeout |
| **HTTP_BACKEND** | Containers (OKE), VMs, external services | Must manage backend infrastructure |
| **DYNAMIC_ROUTING_BACKEND** | Multi-tenant, canary, A/B testing | Complex routing rules configuration |
| **STOCK_RESPONSE_BACKEND** | Health checks, mocks, static responses | No dynamic logic |

**Agent Behavior**:
"Before defining routes, ask the user:
'Are the backends OCI Functions (serverless), containers/VMs (HTTP), or do you need multi-tenant routing? Are there endpoints that return static responses (health checks)?'"

**Decision Factors**:
- Backend infrastructure (serverless vs. managed)
- Latency tolerance (cold starts acceptable?)
- Routing complexity (single backend vs. conditional)

**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingoraclefunctionsbackend.htm

---

**Decision Point**: Response Caching Strategy

| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| **No cache** | Data freshness, real-time responses | More Function invocations, higher cost | User-specific data, frequently changing data |
| **Gateway cache (FIXED_TTL_STORE_POLICY)** | Reduced invocations, lower latency | Stale data during TTL window | GET endpoints with stable data, TTL > 60s |
| **External cache (Redis)** | High throughput, shared invalidation | Additional infrastructure cost | > 10K req/s, cross-gateway cache sharing |

**Agent Behavior**:
"Before configuring caching, ask the user:
'Are there GET endpoints returning data that changes infrequently (catalogs, configs)? What is the expected request volume?'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayresponsecaching.htm

---

