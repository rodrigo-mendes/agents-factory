### ✅ Always Do

**1. API Gateway as Single Entry Point**: All client traffic MUST enter through API Gateway. Routes use `ORACLE_FUNCTIONS_BACKEND` type with function OCID. Direct function invoke endpoints MUST NEVER be exposed to clients.

**Required configuration**:
- API Gateway with `endpoint_type = PUBLIC` in a public subnet
- Functions Application in a private subnet with no public IP
- Deployment with rate limiting, authentication, CORS, and logging enabled
- Health check route (`/health`) with `STOCK_RESPONSE_BACKEND` and `ANONYMOUS` authorization
- Business routes with `ORACLE_FUNCTIONS_BACKEND` pointing to function OCIDs

**Why it is mandatory**: Direct function invocation bypasses authentication, rate limiting, CORS, and request validation. API Gateway provides unified security and policy enforcement.
**Failure if omitted**: Unprotected endpoints, no rate limiting, unauthorized access, cost explosion (unlimited invocations).
**Trade-off**: API Gateway adds 5–15ms latency per request.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayoverview.htm

> 📎 **Implementation**: For Terraform provisioning of Gateway + Deployment + Routes, use `provisioning-oci-api-gateway`. For API Gateway architecture decisions, use `designing-oci-api-gateway`.

---

**2. Network Isolation — Functions in Private Subnet**: Functions Applications MUST run in private subnets with NSGs. API Gateway in a separate public subnet. Service Gateway provides OCI API access without internet traversal.

**Required topology**:
- Functions Application in private subnet (`prohibit_public_ip_on_vnic = true`)
- API Gateway in public subnet with Internet Gateway
- NSG for Functions: ingress only from API Gateway subnet CIDR
- NSG for API Gateway: ingress TCP 443 from `0.0.0.0/0`
- Private route table: `0.0.0.0/0 → NAT Gateway` + `Service CIDR → Service Gateway`
- Tracing enabled at Application level with APM domain OCID

**Verification**:
```bash
# Verify subnet is private (no public IP)
oci fn application get --application-id <OCID> --query 'data."subnet-ids"'
oci network subnet get --subnet-id <SUBNET_OCID> --query 'data."prohibit-public-ip-on-vnic"'
# Expected: true
```

**Why it is mandatory**: Functions in public subnets receive direct internet traffic, bypassing API Gateway's authentication, rate limiting, and request validation.
**Failure if omitted**: Unauthorized invocation, DDoS exposure, authentication bypass.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringnetworking.htm

> 📎 **Implementation**: For Terraform provisioning of VCN, Subnets, NSGs, use `provisioning-oci-networking`.

---

**3. Resource Principal Authentication (Dynamic Groups)**: Functions MUST use Dynamic Groups and IAM Policies for service-to-service authentication. Function code uses Resource Principal — NEVER hardcoded credentials in code, env vars, or function config.

**Required IAM resources**:
- **Dynamic Group for Functions**: matching rule `ALL {resource.type = 'fnfunc', resource.compartment.id = '<compartment_ocid>'}`
- **Dynamic Group for API Gateway**: matching rule `ALL {resource.type = 'ApiGateway', resource.compartment.id = '<compartment_ocid>'}` (note: `ApiGateway` is PascalCase — case-sensitive)
- **Policy**: `Allow dynamic-group <gw-dg> to use fn-invocation in compartment <name>`
- **Policy**: `Allow service FaaS to use virtual-network-family in compartment <name>`
- **Policy**: `Allow service FaaS to read repos in tenancy`
- **Policy**: Least-privilege grants for Functions accessing OCI services (e.g., `read secret-bundles`, `use objects`)

**Why it is mandatory**: Credentials in code, env vars, or config files are visible in OCI Console, API responses, and Terraform state. Resource Principal provides secure, auto-rotated, auditable authentication.
**Failure if omitted**: Data breach, credential exposure, compliance violation.
**Trade-off**: Dynamic Group matching rules use eventual consistency — propagation delay up to 5 minutes for new functions.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingpolicies.htm

> 📎 **Implementation**: For Terraform provisioning of Dynamic Groups and Policies, use `provisioning-oci-iam`. For Java Resource Principal usage, use `developing-oci-functions-java`.

---

**4. Compartment Segregation**: Isolation of blast radius — compromise of one compartment does not affect others. Enables granular governance, billing, and auditing.

**Recommended hierarchy**:
```
Root Tenancy
├── Network          (VCN, Subnets, Gateways, Load Balancers)
├── Security         (Vault, Keys, Audit configs)
├── Serverless-Dev
│   ├── Functions
│   └── API Gateways
├── Serverless-Staging
│   ├── Functions
│   └── API Gateways
└── Serverless-Prod
    ├── Functions
    └── API Gateways
```

**Verification**:
```bash
# Verify compartment structure exists
oci iam compartment list --compartment-id <tenancy_ocid> --lifecycle-state ACTIVE
```

**Why it is mandatory**: Without segregation, any policy change or compromise affects all resources; impossible to do granular governance.
**Failure if omitted**: Blast radius = entire tenancy; no granular auditing or billing possible.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcompartments.htm

---

**5. Function with Explicit Memory, Timeout, and Image Pinning**: Every function MUST set memory, timeout, and pin images with digest.

**Configuration requirements**:
- `memory_in_mbs`: Set based on profiling — determines proportional CPU allocation (see Memory→CPU table below)
- `timeout_in_seconds`: Set to minimum viable value — API-facing: 30–60s, background: scale appropriately. NEVER leave at default 300s
- `image_digest`: Use `sha256:...` for exact pinning in production
- `image`: Full OCIR path `<region-key>.ocir.io/<namespace>/<repo>:<tag>`

**Why it is mandatory**: Functions without explicit timeouts may run up to 300s on hung connections. Memory determines proportional CPU allocation. Without `image_digest`, image updates may not be detected.
**Failure if omitted**: Cost overrun from runaway functions, inconsistent deployments, resource exhaustion.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscustomizing.htm

---

**6. Encryption in Transit and at Rest**: All data MUST be encrypted in transit (TLS 1.2+) and at rest (OCI-managed or customer-managed keys).

**Requirements**:
- API Gateway: TLS 1.2+ enabled by default — do NOT disable
- Secrets: Stored in OCI Vault, accessed via Resource Principal at runtime
- Custom domains: Use OCI Certificates Service with auto-renewal

**Why it is mandatory**: Unencrypted data violates every compliance framework (SOC2, ISO 27001, PCI-DSS).
**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

**7. Centralized Logging and Monitoring**: Tracing and logging MUST be enabled on Functions Applications and API Gateway Deployments.

**Requirements**:
- `trace_config.is_enabled = true` at Application level with APM domain OCID
- API Gateway: `access_log.is_enabled = true` and `execution_log.is_enabled = true`
- Alarms configured for: function invocation errors, API Gateway 5xx rate, function duration > 80% of timeout

**Verification**:
```bash
oci fn application get --application-id <OCID> --query 'data."trace-config"."is-enabled"'
# Expected: true
```

**Why it is mandatory**: Functions are ephemeral — without tracing and structured logging, debugging production issues is impossible.
**Failure if omitted**: Extended incident resolution time, inability to diagnose issues, SLA violations.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsexportingfunctionlogfiles.htm

---

**8. Tagging Strategy for Cost Allocation**: Apply tags to all serverless resources for cost attribution.

**Required tags**: `Environment`, `Project`, `Team`, `CostCenter`, `ManagedBy`

**Why it is mandatory**: Functions are billed per invocation and per GB-second. Without tags, cost attribution is impossible.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm

---

