---
name: architecting-oci-serverless
description: Architects serverless API backends with OCI Functions and API Gateway. Use when designing serverless patterns following OCI Best Practices 2024.
---

## Version Context

**Technology**: Oracle Cloud Infrastructure — OCI Functions + API Gateway
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Architecture Domain**: Serverless API Patterns — Functions + API Gateway + IAM
**Target Edition**: OCI Best Practices 2024
**Key Services**: OCI Functions (Fn Project, Apache 2.0), OCI API Gateway, OCI IAM (Identity Domains)
**Support Status**: Active (GA — all features production-ready)

**Key Capabilities (2024+)**:
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
- **[Integration Patterns](#integration-patterns)** — Cross-service integration examples
- **[Reference Architecture](#reference-architecture-diagram)** — Visual topology diagram
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Reference Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    OCI TENANCY                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Compartment: serverless-prod                 │  │
│  │                                                       │  │
│  │  ┌─── VCN (10.0.0.0/16) ────────────────────────┐   │  │
│  │  │                                                │   │  │
│  │  │  ┌── Public Subnet (10.0.0.0/24) ──────────┐ │   │  │
│  │  │  │  API Gateway ←── Internet Gateway        │ │   │  │
│  │  │  │  (rate limit, JWT, CORS)                 │ │   │  │
│  │  │  └──────────────┬───────────────────────────┘ │   │  │
│  │  │                 │ (VCN internal)               │   │  │
│  │  │  ┌── Private Subnet (10.0.1.0/24) ─────────┐ │   │  │
│  │  │  │  OCI Functions (Application)             │ │   │  │
│  │  │  │  ├── func-hello                          │ │   │  │
│  │  │  │  ├── func-orders                         │ │   │  │
│  │  │  │  └── func-users                          │ │   │  │
│  │  │  │       │                                  │ │   │  │
│  │  │  │       ├─→ Service GW → OCI Vault         │ │   │  │
│  │  │  │       ├─→ Service GW → Autonomous DB     │ │   │  │
│  │  │  │       ├─→ Service GW → Object Storage    │ │   │  │
│  │  │  │       └─→ NAT GW → External APIs        │ │   │  │
│  │  │  └──────────────────────────────────────────┘ │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │                                                       │  │
│  │  IAM: Dynamic Groups + Scoped Policies               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **API Gateway as Single Entry Point** — All traffic via API Gateway. Direct function endpoints MUST NEVER be exposed. Adds 5-15ms latency
- **Functions in Private Subnet** — NSG-controlled. API Gateway in separate public subnet. Service Gateway for OCI API access
- **IAM Least-Privilege** — Dynamic Groups scoped to compartment. Policies grant only needed verbs on specific resource types
- **Vault for Secrets** — External API keys, DB passwords in OCI Vault. Function config for non-sensitive values only
- **Observability Stack** — OCI Logging (function logs), APM (distributed tracing), Monitoring (custom metrics/alarms)

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

The agent MUST verify after each serverless environment configuration:

### 1. Network Isolation
```bash
# Verify Functions subnet is private
oci fn application get --application-id <OCID> --query 'data."subnet-ids"'
# Exit code: 0 (success) | 1 (auth/network error)
oci network subnet get --subnet-id <SUBNET_OCID> --query 'data."prohibit-public-ip-on-vnic"'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: true
```

### 2. IAM Policies
```bash
# Verify no wildcard policies on function dynamic groups
oci iam policy list --compartment-id <TENANCY_OCID> --all \
# Exit code: 0 (success) | 1 (auth/network error)
  | grep -i "manage all-resources"
  # Exit code: 0 (match found) | 1 (no match)
# Expected: empty (no matches)

# Verify dynamic group matching rule
oci iam dynamic-group get --dynamic-group-id <OCID> \
# Exit code: 0 (success) | 1 (auth/network error)
  --query 'data."matching-rule"'
# Expected: "ALL {resource.type = 'fnfunc', resource.compartment.id = '...'}"
```

### 3. Function Configuration
```bash
# Verify all functions have explicit timeout and memory
oci fn function list --application-id <app_ocid> \
# Exit code: 0 (success) | 1 (auth/network error)
  | jq '.data[] | {name: .["display-name"], timeout: .["timeout-in-seconds"], memory: .["memory-in-mbs"]}'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
# Flag any function with timeout=300 or null
```

### 4. Credential Scan
```bash
# Scan function configs for leaked secrets
oci fn function list --application-id <APP_OCID> --all \
# Exit code: 0 (success) | 1 (auth/network error)
  --query 'data[*].config' | grep -iE 'password|secret|key|token'
  # Exit code: 0 (match found) | 1 (no match)
# Expected: No matches for actual credential values (OCIDs are acceptable)
```

### 5. API Gateway Validation
```bash
# Verify deployment has rate limiting and auth
oci api-gateway deployment get --deployment-id <deployment_ocid> | \
  jq '.data.specification | {
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
    rate_limiting: .request_policies.rate_limiting,
    auth: .request_policies.authentication.type,
    access_log: .logging_policies.access_log.is_enabled,
    execution_log: .logging_policies.execution_log.is_enabled
  }'
```

### 6. Observability
```bash
oci fn application get --application-id <OCID> --query 'data."trace-config"."is-enabled"'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: true
```

### 7. End-to-End Smoke Test
```bash
# Health check (anonymous)
curl -s -o /dev/null -w "%{http_code}" https://<apigw-hostname>/v1/health
# Exit code: 0 (success) | 1 (connection error) | 22 (HTTP error with -f)
# Expected: 200

# Authenticated endpoint without token (should fail)
curl -s -o /dev/null -w "%{http_code}" https://<apigw-hostname>/v1/items
# Exit code: 0 (success) | 1 (connection error) | 22 (HTTP error with -f)
# Expected: 401
```

**Troubleshooting**:
- `502 Bad Gateway` → Missing IAM policy: `Allow dynamic-group <gw-dg> to use fn-invocation`
- `404` on API GW → Deployment path-prefix + route path mismatch
- `504 timeout` → Function timeout too short OR Function subnet missing outbound connectivity
- `FunctionInvokeError` → Function image not in OCIR or not pullable (`Allow service FaaS to read repos in tenancy`)
- `404-NotAuthorizedOrNotFound` → Dynamic Group matching rule mismatch, or IAM propagation delay (wait 60s)

---

## Quick Reference

### Memory → CPU Mapping
| Memory | CPU Fraction |
|--------|-------------|
| 128 MB | 1/8 CPU |
| 256 MB | 1/4 CPU |
| 512 MB | 1/2 CPU |
| 1024 MB | 3/4 CPU |
| 2048 MB | 1 CPU |

### Free Tier (per tenancy/month)
- 2 million invocations
- 400,000 GB-seconds
- API Gateway: 1M calls/month (Always Free)

### Service Equivalence (multi-cloud context)
| OCI | AWS | Azure | GCP |
|-----|-----|-------|-----|
| OCI Functions | Lambda | Azure Functions | Cloud Functions |
| API Gateway | API Gateway | API Management | Apigee |
| Dynamic Groups + Resource Principal | IAM Roles + STS | Managed Identity | Workload Identity |
| OCI Vault | Secrets Manager | Key Vault | Secret Manager |
| OCI Events | EventBridge | Event Grid | Eventarc |

### Essential OCI CLI Commands
```bash
# List functions in an application
oci fn function list --application-id <APP_OCID> --all

# Get function details
oci fn function get --function-id <FN_OCID>

# Invoke function (testing)
oci fn function invoke --function-id <FN_OCID> --body '{"key":"value"}' --file -

# Check application tracing
oci fn application get --application-id <APP_OCID> --query 'data."trace-config"'

# List API Gateway deployments
oci apigateway deployment list --compartment-id <COMP_OCID> --all

# Get deployment routes
oci api-gateway deployment get --deployment-id <deployment_ocid> | jq '.data.specification.routes'

# List Dynamic Groups
oci iam dynamic-group list --compartment-id <tenancy_ocid>

# List IAM Policies
oci iam policy list --compartment-id <compartment_ocid>

# Check Function logs
oci logging search --search-query 'search "<log_group_ocid>" | sort by datetime desc' --time-start <ISO8601> --time-end <ISO8601>
```

---

## Skill Cross-References

| Need | Use Skill |
|------|-----------|
| Terraform: Functions Application + Function | `provisioning-oci-functions` |
| Terraform: API Gateway + Deployment + Routes | `provisioning-oci-api-gateway` |
| Terraform: Dynamic Groups + IAM Policies | `provisioning-oci-iam` |
| Terraform: VCN + Subnets + NSGs + Gateways | `provisioning-oci-networking` |
| Terraform: Functions + API Gateway + IAM integrated | `provisioning-oci-serverless-stack` |
| Terraform: Events Rules for function triggers | `provisioning-oci-events` |
| Terraform: Streaming for async patterns | `provisioning-oci-streaming` |
| API Gateway architecture and design decisions | `designing-oci-api-gateway` |
| Network architecture and design decisions | `designing-oci-networking` |
| Vault security architecture | `designing-oci-vault-security` |
| Java: Function development with FDK | `developing-oci-functions-java` |
| Java: API Gateway typed events | `implementing-oci-functions-events` |
| Java: Object Storage integration | `integrating-oci-functions-objectstorage` |
| Java: REST API invocation | `invoking-rest-apis-from-oci-functions` |
| Java: Event publishing (Streaming, Notifications) | `publishing-events-from-oci-functions` |

---

## Environment Validation Checklist

Use this checklist to validate a complete serverless environment:

- [ ] Dedicated compartment(s) created (Network, Security, Serverless-{env})
- [ ] VCN with public subnet (API GW) and private subnet (Functions)
- [ ] Internet Gateway on public subnet route table
- [ ] NAT Gateway and/or Service Gateway for private subnet
- [ ] NSGs: 443 inbound on API GW; deny all on Functions except API GW CIDR
- [ ] Dynamic Group for Functions with correct matching rule (`fnfunc` + compartment)
- [ ] Dynamic Group for API Gateway with correct matching rule (`ApiGateway` + compartment)
- [ ] Policy: API GW can invoke Functions (`use fn-invocation`)
- [ ] Policy: FaaS service can use VCN (`use virtual-network-family`)
- [ ] Policy: FaaS service can read repos (`read repos in tenancy`)
- [ ] Policy: Functions can read secrets in Vault (if applicable)
- [ ] Policy: Developers can manage fn-family and api-gateway-family
- [ ] Application created in private subnet with tracing enabled
- [ ] Function deployed with explicit timeout and memory limits
- [ ] Function image pinned with digest in production
- [ ] API Gateway created in public subnet
- [ ] Deployment with routes pointing to Function(s)
- [ ] Rate limiting configured
- [ ] Authentication (JWT or custom) configured
- [ ] CORS configured if browser-based frontend exists
- [ ] Logging enabled (Functions tracing + API Gateway access + execution logs)
- [ ] Alarms configured (error rate, latency, invocations)
- [ ] Tagging applied for cost attribution
- [ ] No credentials in function config (verified via credential scan)

---

## External Resources

### Official Documentation
- [OCI Functions — Home](https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm)
- [OCI Functions — Concepts](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsconcepts.htm)
- [OCI API Gateway — Overview](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayoverview.htm)
- [Functions Networking Configuration](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringnetworking.htm)
- [Functions IAM Policies](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingpolicies.htm)
- [Functions — Accessing OCI Resources](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm)
- [Provisioned Concurrency](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingprovisionedconcurrency.htm)
- [Image Signature Verification](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingimagesignatureverification.htm)
- [Logging & Tracing](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsexportingfunctionlogfiles.htm)
- [Pre-Built Functions Catalog](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functions_pbf_catalog.htm)
- [Function Customization (timeout, memory)](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscustomizing.htm)
- [Creating Applications](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingapps.htm)

### API Gateway
- [Authentication Policies](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingauthenticationandrequestpolicies.htm)
- [Rate Limiting](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingratelmiting.htm)
- [Using Functions Backend](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingoraclefunctionsbackend.htm)
- [API Gateway Deployments](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatingdeployment.htm)

### IAM & Security
- [IAM — Dynamic Groups](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm)
- [IAM — Compartments](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcompartments.htm)
- [IAM — Common Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm)
- [IAM — Policy Reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policyreference.htm)
- [Identity Domains](https://docs.oracle.com/en-us/iaas/Content/Identity/domains/overview.htm)
- [Storing Secrets in Vault](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsstoringsecretsinvault.htm)
- [OCI Key Management](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm)

### Architecture & Pricing
- [Serverless REST API Reference Architecture](https://docs.oracle.com/en/solutions/serverless-func-api-gtw/index.html)
- [OCI Events Overview](https://docs.oracle.com/en-us/iaas/Content/Events/Concepts/eventsoverview.htm)
- [OCI Functions Pricing](https://www.oracle.com/cloud/cloud-native/functions/)

### Open Source
- [Fn Project (Apache 2.0)](https://fnproject.io/)
