---
name: architecting-oci-serverless
description: Architects serverless API backends with OCI Functions and API Gateway. Use when designing serverless patterns following OCI best practices for Functions, API Gateway, IAM, and networking.
---

## Version Context

**Technology**: Oracle Cloud Infrastructure — OCI Functions + API Gateway
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Architecture Domain**: Serverless API Patterns — Functions + API Gateway + IAM
**Target Edition**: OCI Best Practices (current — verify at https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm)
**Key Services**: OCI Functions (Fn Project, Apache 2.0), OCI API Gateway, OCI IAM (Identity Domains)
**Support Status**: Active (GA — all features production-ready)

**Key Capabilities**:
- **Provisioned Concurrency**: `CONSTANT` strategy for cold start elimination (25% idle cost)
- **Detached Mode**: Async invocations with success/failure destinations (Streaming, Queue, Notifications)
- **ARM Shapes**: `GENERIC_ARM` for ~20% cost savings over X86
- **Image Signature Verification**: KMS-backed supply chain security
- **Pre-Built Functions (PBF)**: Catalog of managed, versioned function implementations
- **Identity Domains**: Unified IAM layer (replaces legacy IDCS separation)
- **Resource Principals**: Service-to-service authentication via Dynamic Groups
- **Custom Container Images**: Beyond pre-defined runtimes
- **API Gateway**: WebSocket support, mutual TLS (mTLS), native response caching

**Service Limits**:

| Parameter | Default/Limit |
|-----------|--------------|
| Memory per function | 128 MB – 2048 MB |
| Timeout per function | Up to 300 seconds |
| Config size (keys+values) | 4 KB maximum |
| API Gateway deployments per gateway | 10 (soft limit) |

⚠️ **CRITICAL — Agent Warning**:
This skill covers **architecture decisions, patterns, and operational guidance** for serverless. For Terraform implementation, use `provisioning-oci-functions`, `provisioning-oci-api-gateway`, and `provisioning-oci-iam`. For Java function development, use `developing-oci-functions-java` and related Java skills. Functions are Docker containers (not code zips). Always use Resource Principal for service-to-service auth — never hardcoded credentials. Tenancies created after 2023 use Identity Domains by default.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases
- **[Reference Architecture Diagram](./blueprints/reference-architecture-diagram.md)** — Visual topology diagram
- **[Verification Loop](./blueprints/verification-loop.md)** — Validation commands and expected outputs
- **[Environment Validation Checklist](./blueprints/environment-validation-checklist.md)** — Pre-production sign-off checklist
- **[Quick Reference](./blueprints/quick-reference.md)** — Memory/CPU mapping, free tier, multi-cloud equivalence, CLI commands, skill cross-references
- **[PoC Worked Examples](./blueprints/poc-worked-examples.md)** — API Facade and REST Proxy patterns from the reference PoC
- **Integration Patterns** (below) — Cross-service integration examples
- **External Resources** (below) — Official documentation links

---

## Reference Architecture Diagram

See [blueprints/reference-architecture-diagram.md](./blueprints/reference-architecture-diagram.md) — ASCII topology showing tenancy → compartment → VCN with API Gateway in public subnet and Functions in private subnet, connected to downstream OCI services via Service Gateway.

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **API Gateway as Single Entry Point** — All traffic via API Gateway. Direct function endpoints MUST NEVER be exposed. Adds 5-15ms latency
- **Functions in Private Subnet** — NSG-controlled. API Gateway in separate public subnet. Service Gateway for OCI API access
- **IAM Least-Privilege** — Dynamic Groups scoped to compartment. Policies grant only needed verbs on specific resource types
- **Vault for Secrets** — External API keys, DB passwords in OCI Vault. Function config for non-sensitive values only
- **Observability Stack** — OCI Logging (function logs), APM (distributed tracing), Monitoring (custom metrics/alarms), **Management Dashboards** (custom dashboards for multi-function visibility: ops golden-signals, APM trace widgets, metric aggregation). Provision via `provisioning-custom-dashboard-oci-observability` (owner: `@oci-observability`); render-valid widget shape comes only from the Console `{JSON}` editor — see the gotchas in `.claude/rules/observability-skills.md`.

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Compute Shape — X86 vs ARM** — ARM 20% cheaper but limited availability. X86 default
- **Cold Start Mitigation — Provisioned Concurrency vs On-Demand** — Provisioned for <100ms SLAs
- **Invocation Pattern — Sync vs Detached (Async)** — Sync max 300s, Detached max 720s
- **Authentication — JWT vs Custom Authorizer** — JWT for standard IdP, Custom for complex logic
- **API Gateway Endpoint — PUBLIC vs PRIVATE** — Public for external, Private for VCN-only
- **Subnet Strategy** — Shared vs dedicated subnets for Functions applications

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Hardcoded credentials in function config** — Visible in Console, API, and Terraform state
- **Functions in public subnet** — Direct internet traffic bypasses API Gateway protections
- **Wildcard IAM policies** — `manage all-resources in tenancy` cannot be scoped down (additive-only)
- **No timeout configuration** — Hung functions run until 300s platform max. Cost and resource waste
- **API Gateway without rate limiting** — Unbounded requests exhaust concurrency, cascading failures
- **Logging/tracing disabled in production** — Ephemeral functions: no observability = no debugging
- **Single compartment for all resources** — Any policy change affects everything. No blast radius control

**Quick anti-pattern reference** (credentials — most critical):

```hcl
# 🚫 WRONG — plaintext credential visible in state file and OCI Console
config = {
  "DB_PASSWORD" = "s3cr3t!"
}

# ✅ CORRECT — pass only the Vault secret OCID; function reads value at runtime
config = {
  "DB_SECRET_OCID" = oci_vault_secret.db_password.id
}
```

For full wrong/correct examples on all prohibited patterns, see [Never Do Patterns](./blueprints/never-do-patterns.md).

---

## Integration Patterns

### OCI Functions ↔ API Gateway (Primary Pattern)

**Architecture**: API Gateway routes HTTP requests to Functions via `ORACLE_FUNCTIONS_BACKEND` — an internal OCI service mesh (not HTTP proxy).

```
Client → [HTTPS/TLS 1.2+] → API Gateway (JWT + rate limit + CORS)
  → [VCN Internal] → Function (Resource Principal)
```

**Required IAM**:
- `Allow dynamic-group <gw-dg> to use fn-invocation in compartment <name>`
- `Allow service FaaS to use virtual-network-family in compartment <name>`

**Network setup**: API Gateway in public subnet (NSG: 443 inbound from `0.0.0.0/0`). Functions in private subnet (NSG: inbound only from API Gateway subnet CIDR).

> 📎 **Implementation**: For Terraform, use `provisioning-oci-serverless-stack`. For Java function handling API Gateway requests, use `implementing-oci-functions-events`.

---

### OCI Functions ↔ OCI Vault (Secret Retrieval)

**Pattern**: Retrieve secrets at runtime using Resource Principal instead of storing credentials in function config.

**How it works**: Function uses `ResourcePrincipalAuthenticationDetailsProvider` to authenticate to Vault → fetches secret bundle → decodes Base64 content. No credentials stored anywhere in code or config.

**Required IAM**: `Allow dynamic-group <fn-dg> to read secret-bundles in compartment <name>`

> 📎 **Implementation**: For Java Vault integration, use `invoking-rest-apis-from-oci-functions`. For Vault architecture decisions, use `designing-oci-vault-security`.

---

### OCI Functions ↔ OCI Object Storage

**Pattern**: Read/write files in Object Storage using Resource Principal for authentication.

**Required IAM**: `Allow dynamic-group <fn-dg> to manage objects in compartment <name> where target.bucket.name = '<bucket>'`

> 📎 **Implementation**: For Java Object Storage integration, use `integrating-oci-functions-objectstorage`.

---

### OCI Functions ↔ OCI Streaming (Event-Driven)

**Pattern**: Asynchronous processing — API Gateway → Function A (publishes to stream, acks fast) → OCI Streaming → Consumer Function B.

```
API Gateway → Function A (publish to stream) → OCI Streaming → Function B (consume)
```

**Use when**: Synchronous processing creates coupling and bottlenecks under load.

**Trade-offs**:
| Dimension | Benefit | Cost |
|-----------|---------|------|
| Throughput | Decoupled, scales independently | Eventual consistency |
| Cost | Pay-per-use across the chain | More services to operate |
| Debug | Distributed tracing via logging | Correlation complexity |

> 📎 **Implementation**: For Java event publishing, use `publishing-events-from-oci-functions`. For Terraform Streaming provisioning, use `provisioning-oci-streaming`.

---

### OCI Functions ↔ OCI Events (Infrastructure Automation)

**Pattern**: OCI Events rule matches resource lifecycle events → invokes Function with event payload.

**Key requirements**:
- Function MUST be idempotent (events may be delivered more than once)
- Configure failure destination for retry/dead-letter pattern
- Event types: `com.oraclecloud.objectstorage.createobject`, `com.oraclecloud.databaseservice.autonomous.database.backup.end`, etc.

> 📎 **Implementation**: For Terraform Events provisioning, use `provisioning-oci-events`. For Java event handling, use `implementing-oci-functions-events`.

---

## Verification Loop

The agent MUST run after each serverless environment configuration. See [blueprints/verification-loop.md](./blueprints/verification-loop.md) for all 7 verification scripts with expected outputs and exit codes (Network Isolation, IAM Policies, Function Configuration, Credential Scan, API Gateway Validation, Observability, End-to-End Smoke Test).

**Quick troubleshooting**:
- `502 Bad Gateway` → Missing IAM policy: `Allow dynamic-group <gw-dg> to use fn-invocation`
- `404` on API GW → Deployment path-prefix + route path mismatch
- `504 timeout` → Function timeout too short OR Function subnet missing outbound connectivity
- `FunctionInvokeError` → Function image not in OCIR or not pullable (`Allow service FaaS to read repos in tenancy`)
- `404-NotAuthorizedOrNotFound` → Dynamic Group matching rule mismatch, or IAM propagation delay (wait 60s)

---

## Quick Reference

See [blueprints/quick-reference.md](./blueprints/quick-reference.md) for Memory→CPU mapping, Free Tier limits, multi-cloud service equivalence table, essential OCI CLI commands, and skill cross-references.

---

## Environment Validation Checklist

See [blueprints/environment-validation-checklist.md](./blueprints/environment-validation-checklist.md) — 24-item checklist covering compartments, network, IAM, Functions, API Gateway, observability, and cost attribution tagging.

---

## External Resources

### Official Documentation
- [OCI Functions — Home](https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm) (verified 2026-07-26)
- [OCI Functions — Concepts](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsconcepts.htm) (verified 2026-07-26)
- [OCI API Gateway — Overview](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayoverview.htm) (verified 2026-07-26)
- [Functions Networking Configuration](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringnetworking.htm) (verified 2026-07-26)
- [Functions IAM Policies](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingpolicies.htm) (verified 2026-07-26)
- [Functions — Accessing OCI Resources](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm) (verified 2026-07-26)
- [Provisioned Concurrency](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingprovisionedconcurrency.htm) (verified 2026-07-26)
- [Image Signature Verification](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingimagesignatureverification.htm) (verified 2026-07-26)
- [Logging & Tracing](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsexportingfunctionlogfiles.htm) (verified 2026-07-26)
- [Pre-Built Functions Catalog](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functions_pbf_catalog.htm) (verified 2026-07-26)
- [Function Customization (timeout, memory)](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscustomizing.htm) (verified 2026-07-26)
- [Creating Applications](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingapps.htm) (verified 2026-07-26)

### API Gateway
- [Authentication Policies](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingauthenticationandrequestpolicies.htm) (verified 2026-07-26)
- [Rate Limiting](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingratelmiting.htm) (verified 2026-07-26)
- [Using Functions Backend](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingoraclefunctionsbackend.htm) (verified 2026-07-26)
- [API Gateway Deployments](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatingdeployment.htm) (verified 2026-07-26)

### IAM & Security
- [IAM — Dynamic Groups](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm) (verified 2026-07-26)
- [IAM — Compartments](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcompartments.htm) (verified 2026-07-26)
- [IAM — Common Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm) (verified 2026-07-26)
- [IAM — Policy Reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policyreference.htm) (verified 2026-07-26)
- [Identity Domains](https://docs.oracle.com/en-us/iaas/Content/Identity/domains/overview.htm) (verified 2026-07-26)
- [Storing Secrets in Vault](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsstoringsecretsinvault.htm) (verified 2026-07-26)
- [OCI Key Management](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm) (verified 2026-07-26)

### Architecture & Pricing
- [Serverless REST API Reference Architecture](https://docs.oracle.com/en/solutions/serverless-func-api-gtw/index.html) (verified 2026-07-26)
- [OCI Events Overview](https://docs.oracle.com/en-us/iaas/Content/Events/Concepts/eventsoverview.htm) (verified 2026-07-26)
- [OCI Pricing](https://www.oracle.com/cloud/pricing/) (verified 2026-07-26)

### Open Source
- [Fn Project (Apache 2.0)](https://fnproject.io/) (verified 2026-07-26)
