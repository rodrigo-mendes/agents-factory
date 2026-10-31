### ✅ Always Do

**1. API Gateway as Single Entry Point**: All external API traffic MUST pass through OCI API Gateway. Never expose OCI Functions or backend services directly to the internet.

**Required configuration**:
- Gateway with `endpoint_type = PUBLIC` in a public subnet with Internet Gateway
- Functions Application in a private subnet with no public IP
- Deployment with rate limiting, authentication, and logging enabled
- Health check route (`/health`) with `STOCK_RESPONSE_BACKEND` and `ANONYMOUS` authorization
- Business routes with `ORACLE_FUNCTIONS_BACKEND` pointing to function OCIDs

**Why it is mandatory**: Functions without a gateway have no rate limiting, WAF, or centralized auth — exposing them to DDoS, abuse, and cost explosion (unlimited invocations at ~$0.20/million).
**Failure if omitted**: Unprotected Functions are vulnerable to cost attacks and unauthorized access. A single bot can trigger thousands of invocations per second.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayoverview.htm

> 📎 **Implementation**: For Terraform provisioning of Gateway + Deployment + Routes, use the skill `provisioning-oci-api-gateway`.

---

**2. IAM Policies for Gateway-to-Function Invocation**: Three IAM configurations are MANDATORY for the gateway to invoke Functions. Missing any one causes 502 Bad Gateway errors on all routes.

**Required IAM resources**:
- **Dynamic Group** for API Gateways matching `resource.type = 'ApiGateway'` scoped to the compartment (note: `ApiGateway` is PascalCase — case-sensitive in OCI)
- **Policy 1**: `Allow dynamic-group <gw-group> to use fn-invocation in compartment <name>` — gateway invokes Functions
- **Policy 2**: `Allow service FaaS to use virtual-network-family in compartment <name>` — FaaS service uses VCN
- **Policy 3**: `Allow service FaaS to read repos in tenancy` — FaaS service reads container images from OCIR

**Why it is mandatory**: Without `fn-invocation` policy, every API call returns 502. Without `virtual-network-family`, Functions cannot attach to VCN subnets. Without `read repos`, Functions cannot pull container images.
**Failure if omitted**: 502 Bad Gateway on all ORACLE_FUNCTIONS_BACKEND routes — the single most common setup issue.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingoraclefunctionsbackend.htm

> 📎 **Implementation**: For Terraform provisioning of Dynamic Groups and Policies, use the skill `provisioning-oci-iam`.

---

**3. Restrictive Network Security Groups (NSGs)**: Gateway in public subnet MUST have NSG allowing ONLY port 443 inbound. Functions subnet MUST only accept traffic from the gateway subnet.

**Required network rules**:
- **API Gateway NSG — Ingress**: TCP 443 from `0.0.0.0/0` (HTTPS only)
- **API Gateway NSG — Egress**: TCP to private Functions subnet CIDR only
- **Functions NSG — Ingress**: TCP from API Gateway subnet CIDR only (or inter-NSG reference)
- **Functions NSG — Egress**: TCP 443 to Service CIDR (OCI services via Service Gateway) + optionally TCP 443 to `0.0.0.0/0` (external APIs via NAT Gateway)

**Why it is mandatory**: Open ports beyond 443 expand attack surface. Functions accepting traffic from any source bypass gateway protections.
**Failure if omitted**: Functions reachable from unexpected sources, bypassing auth, rate limiting, and WAF.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm

> 📎 **Implementation**: For Terraform provisioning of NSGs and security rules, use the skill `provisioning-oci-networking`.

---

**4. CORS with Explicit Origins**: For browser-consumed APIs, CORS MUST list allowed origins explicitly. NEVER use wildcard `*` with `is_allow_credentials_enabled = true`.

**Required CORS configuration**:
- `allowed_origins`: List specific origins (e.g., `["https://app.example.com", "https://staging.example.com"]`)
- `allowed_methods`: Explicit HTTP methods (e.g., `["GET", "POST", "PUT", "DELETE", "OPTIONS"]`)
- `allowed_headers`: Required headers (e.g., `["Content-Type", "Authorization", "X-Request-Id"]`)
- `is_allow_credentials_enabled`: Only `true` when origins are explicit (NEVER with wildcard)
- `max_age_in_seconds`: Cache preflight responses (e.g., `3600`)

**🚫 PROHIBITED**: `allowed_origins = ["*"]` with `is_allow_credentials_enabled = true` — violates the CORS specification and enables CSRF from any domain.

**Why it is mandatory**: Wildcard origins with credentials enabled allows cross-site request forgery (CSRF) from any domain.
**Failure if omitted**: CSRF attacks, credential theft, session hijacking via malicious origins.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingcors.htm

---

**5. Logging Enabled on All Deployments**: Access logs and execution logs MUST be enabled on every deployment.

**Required logging configuration**:
- **Access log**: `is_enabled = true` — always, for audit trail of every request
- **Execution log**: `is_enabled = true` with log level:
  - Production: `ERROR` (reduces volume/cost)
  - Dev/Staging: `INFO` (full debugging)

**Why it is mandatory**: Without logs, incident diagnosis is blind, compliance audit trails are missing, and security attacks go undetected.
**Failure if omitted**: Slow MTTR, compliance violations, inability to detect and respond to security incidents.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaymanaginglogs.htm

---

**6. TLS 1.2+ with Certificate Management**: Default gateway hostnames include auto-managed TLS. Custom domains MUST use OCI Certificates Service with auto-renewal enabled.

**Requirements**:
- Default hostnames: TLS is auto-managed by OCI — do NOT disable
- Custom domains: Use `ca_bundles` with `CERTIFICATE_AUTHORITY` type for mTLS
- For B2B/financial APIs: Enable mutual TLS (mTLS) with client certificate validation

**Why it is mandatory**: Data in transit must be encrypted. Expired certificates cause outages. mTLS is required for B2B/financial APIs.
**Failure if omitted**: Data exposure in transit, certificate expiration outages, compliance failures (PCI-DSS, SOC2).
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingcustomdomains.htm

---

