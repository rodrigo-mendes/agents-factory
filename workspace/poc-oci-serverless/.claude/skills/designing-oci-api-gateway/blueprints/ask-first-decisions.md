### ⚠️ Ask First

**Decision Point 1: Authentication Strategy**

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| JWT Validation (built-in) | Performance (no backend call), simplicity | Flexibility, real-time token revocation | IdP emits standard JWTs (Auth0, Okta, OCI IDCS, Keycloak) |
| Custom Authorizer (Function) | Full flexibility, complex multi-tenant logic | Latency (+50–2000ms cold start), additional cost | Complex auth, API key + secret, multi-tenant routing |
| OAuth2 Token Introspection | Real-time revocation | Latency (network call per request), IdP dependency | Tokens that MUST be instantly revocable |
| Mutual TLS (mTLS) | Strongest machine-to-machine auth | Client certificate distribution complexity | B2B, financial services, PCI-DSS environments |
| Usage Plan (API Key) | Identification + quotas per subscriber | Not real authentication (keys can leak) | Public APIs with access tiers, rate limiting per subscriber |
| Anonymous | Simplicity | Zero security | Health checks, truly public read-only endpoints |

**Agent Behavior**:
"Before choosing an authentication strategy, ask the user:
'What identity provider will issue tokens? Are the tokens standard JWTs, or do you need custom validation logic?'"

**Decision Factors**:
- Identity Provider type (OIDC-compliant vs custom)
- Token format (JWT vs opaque)
- Revocation requirements (real-time vs TTL-based)
- Cost sensitivity (custom auth = +1 invocation per request)

**Cost Profile**: JWT validation is "free" (local processing); Custom Authorizer costs additional Function invocations; Token Introspection adds network latency per request.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingauthenticationandrequestpolicies.htm

---

**Decision Point 2: API Gateway Endpoint Type**

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| PUBLIC | Accessibility — internet-facing | Exposure — requires WAF/DDoS | External APIs, mobile backends, third-party integrations |
| PRIVATE | Security — VCN-only access | Accessibility — no internet | Internal microservices, service-to-service, private backends |

**Agent Behavior**:
"Before provisioning the API Gateway, ask:
'Are the API consumers external (internet) or internal (within VCN / on-premises via FastConnect)?'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatinggateway.htm

---

**Decision Point 3: Rate Limiting Strategy**

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| CLIENT_IP rate key | Simple DDoS protection | Shared NAT IPs count as one | Basic protection, internal APIs |
| Usage Plans + API Keys | Per-subscriber quotas, monetization | Complexity, key management | Public APIs with tiers, paid APIs |
| Custom Authorizer + rate limiting | Dynamic rate per tenant/user | Latency + cost (extra invocation) | SaaS multi-tenant with per-tenant limits |

**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingratelmiting.htm

---

