### ⚠️ Ask First

**Decision Point 1: Compute Shape — X86 vs ARM**

| Option | Optimizes | Sacrifices | Choose When |
|--------|-----------|------------|-------------|
| `GENERIC_X86` | Compatibility — all libraries work | Cost (higher per-invocation) | Java with x86 native deps, Oracle JDBC, legacy libraries |
| `GENERIC_ARM` | Cost — ~20% cheaper per GB-second | Library compatibility (some native libs x86-only) | Python/Node.js/Go workloads, cost-sensitive |
| `GENERIC_X86_ARM` | Flexibility — OCI chooses optimal | Deterministic behavior | Polyglot apps with mixed requirements |

**Agent Behavior**:
"Before configuring the Functions Application shape, ask:
'Does your function use native libraries that require x86 (e.g., Oracle JDBC, native C extensions)? Or can it run on ARM for ~20% cost savings?'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingapps.htm

---

**Decision Point 2: Cold Start Mitigation — Provisioned Concurrency vs On-Demand**

| Option | Optimizes | Sacrifices | Choose When |
|--------|-----------|------------|-------------|
| On-Demand (default) | Cost — pay only for executions | Latency — cold starts 1–10s | Background processing, event handlers, non-latency-sensitive |
| Provisioned Concurrency (`CONSTANT`) | Latency — sub-second guaranteed | Cost — 25% of execution rate for idle instances | API-facing functions, P99 < 1s SLA, Java runtimes |
| Scheduled Warm-up (cron) | Balance cost/latency | Operational complexity | Predictable traffic patterns |

**Agent Behavior**:
"Before configuring concurrency, ask:
'What is the P99 latency SLA for this API route? If < 1 second, provisioned concurrency is required — especially for Java runtimes with heavier cold starts.'"

**Decision Factors**:
- P99 latency SLA requirement
- Runtime cold start profile (Java 1–10s, Python/Node 0.5–3s)
- Invocation frequency (break-even analysis vs idle cost)
- Budget for 25% idle-capacity billing

**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingprovisionedconcurrency.htm

---

**Decision Point 3: Invocation Pattern — Synchronous vs Detached (Async)**

| Option | Optimizes | Sacrifices | Choose When |
|--------|-----------|------------|-------------|
| Synchronous | Simplicity — request/response | Timeout limit (300s function, 60s API GW default) | CRUD operations, queries, short computations |
| Detached Mode | Duration — long-running ops | Immediate response — client gets 202 only | File processing, report generation, ML inference, batch ops |

**Agent Behavior**:
"Before implementing, ask:
'Will this operation complete within API Gateway's timeout (configurable up to 300s)? If not, use detached mode with a result queue or stream for completion tracking.'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsinvoking.htm

---

**Decision Point 4: Authentication — JWT Validation vs Custom Authorizer**

| Option | Optimizes | Sacrifices | Choose When |
|--------|-----------|------------|-------------|
| `JWT_AUTHENTICATION` | Performance — no extra invocation | Flexibility — standard JWT claims only | Standard OIDC/OAuth2 (Auth0, Okta, OCI Identity Domains) |
| `TOKEN_AUTHENTICATION` | Standards — opaque token support | Latency — remote validation call | Opaque tokens requiring introspection |
| `CUSTOM_AUTHENTICATION` | Flexibility — arbitrary auth logic | Cost + latency — extra function per request | API keys, multi-tenant auth, legacy tokens |
| Anonymous | Simplicity | Zero security | Health checks, truly public read-only endpoints |

**Agent Behavior**:
"Before configuring authentication, ask:
'What identity provider is in use and does it support standard OIDC flows? Prefer built-in JWT_AUTHENTICATION for standard IdPs — it avoids the cost and latency of an additional function invocation per request.'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingauthenticationandrequestpolicies.htm

---

**Decision Point 5: API Gateway Endpoint Type — PUBLIC vs PRIVATE**

| Option | Optimizes | Sacrifices | Choose When |
|--------|-----------|------------|-------------|
| PUBLIC | Accessibility — internet-facing | Exposure — requires WAF/DDoS | External APIs, mobile backends, third-party integrations |
| PRIVATE | Security — VCN-only access | Accessibility — no internet | Internal microservices, service-to-service, private backends |

**Agent Behavior**:
"Before provisioning the API Gateway, ask:
'Are the API consumers external (internet) or internal (within VCN / on-premises via FastConnect)?'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatinggateway.htm

---

**Decision Point 6: Subnet Strategy for Functions**

| Option | Optimizes | Sacrifices | Choose When |
|--------|-----------|------------|-------------|
| Private Subnet + NAT Gateway | Security + internet access for external APIs | Cost (~$9.50/mo for NAT GW) | Functions need to call third-party APIs |
| Private Subnet + Service Gateway only | Security + OCI-internal performance | No internet access | Functions only access OCI services (Vault, DB, Object Storage) |
| Public Subnet | Simplicity of setup | Security (exposes invoke endpoint) | **Never in production** |

**Agent Behavior**:
"Before configuring the Function subnet, ask:
'Does the function need to call external third-party APIs (outside OCI), or does it only access OCI-internal services like Vault, Object Storage, and Autonomous DB?'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringnetworking.htm

---

