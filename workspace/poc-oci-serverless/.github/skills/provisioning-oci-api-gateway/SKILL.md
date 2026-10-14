---
name: provisioning-oci-api-gateway
description: Provisions and configures OCI API Gateway resources (Gateway, Deployment, Routes, Policies) with Terraform OCI Provider v6.x+. Use when provisioning API Gateway for serverless architectures.
---

## Version Context

**Technology**: Terraform OCI Provider — API Gateway (`oci_apigateway_gateway`, `oci_apigateway_deployment`)
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Terraform Version**: >= 1.7
**Provider Version**: oracle/oci >= 6.0, < 9.0
**Provider Registry**: https://registry.terraform.io/providers/oracle/oci/latest/docs
**Release Date**: 2024–2026 (continuous releases)
**Support Status**: Active

**Key Constraints**:
- Gateway requires a **subnet** — PUBLIC endpoint needs public subnet with Internet Gateway; PRIVATE endpoint needs private subnet
- Deployment `specification` is the core configuration block — all routes, policies, and backends are nested within it
- IAM Dynamic Group + Policy is **required** for API Gateway to invoke Functions (`use fn-invocation`) — without it, all calls return **502 Bad Gateway**
- Rate limiting is **deployment-level** (not per-route) — applies to all routes in the deployment
- Maximum **100 routes per deployment**, **100 deployments per gateway**, **10 MB** request/response body
- Function backend timeout maximum is **300 seconds**

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform OCI Provider v6.x+. Do NOT mix syntax from older provider versions. Always validate that IAM policies exist and have propagated (up to 60s) before creating API Gateway Deployments with Functions backends.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Cross-service integration examples
- **[Module Architecture](#module-architecture)** — Terraform module composition
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Provider Version Constraint** — Lock OCI provider to tested range to prevent breaking changes on public-facing endpoints
- **Gateway with NSG and Tags** — NSG restricts traffic to HTTPS/443 only. Tags required for cost tracking and compliance
- **Deployment with JWT, CORS, Rate Limiting** — Cross-cutting concerns at deployment level. Rate limiting prevents DDoS/cost explosion
- **Variable Validation with OCID Regex** — Catch misconfiguration at plan-time before apply
- **IAM `depends_on`** — Gateway Deployments must depend on IAM policies (60s propagation delay causes 502 errors)

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **PUBLIC vs PRIVATE Gateway** — Public for external consumers, Private for internal/VCN-only access
- **Authentication Strategy** — JWT (IdP integration), Custom Authorizer Function, or Token-based
- **Backend Type Selection** — OCI Functions, HTTP passthrough, or Stock Response

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Hardcoded Credentials in Provider** — CRITICAL: Full tenancy compromise. Use Resource Principal or config file
- **API Gateway Without Rate Limiting** — CRITICAL: DDoS causes unbounded Function invocations and cost explosion
- **Functions Exposed Without API Gateway** — CRITICAL: No auth, rate limiting, CORS, or logging
- **SSL Verification Disabled on JWKS** — CRITICAL: Enables MITM and complete authentication bypass

---

## Integration Patterns

For complete integration code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Summary of integrations**:
- **API Gateway ↔ OCI Functions** — Function backend configuration with IAM dependency management
- **API Gateway ↔ VCN (Network)** — Subnet placement, NSG rules for HTTPS ingress
- **API Gateway ↔ OCI Logging & Monitoring** — Access logs, execution logs, custom metrics

---
## Module Architecture

### Recommended Module Composition

```
terraform/oci-serverless/
├── main.tf              # Module composition (root)
├── variables.tf         # Input variables with validation
├── outputs.tf           # Stack outputs
├── versions.tf          # Provider constraints
├── modules/
│   ├── api-gateway/     # Gateway + Deployment
│   ├── functions/       # Application + Function
│   ├── iam/             # Dynamic Groups + Policies
│   ├── network/         # VCN + Subnets + Gateways + NSGs
│   └── observability/   # Logging + Monitoring Alarms
```

### Root Module Dependency Flow

```hcl
# Dependencies: network → iam → functions → api_gateway → observability
module "network" {
  source = "./modules/network"
}

module "iam" {
  source = "./modules/iam"
}

module "app_api_handler" {
  source     = "./modules/function-app"
  subnet_id  = module.network.subnet_private_id
  depends_on = [module.iam]
}

module "api_gateway" {
  source      = "./modules/api-gateway"
  subnet_id   = module.network.subnet_public_id
  function_id = module.functions.function_id
  depends_on  = [module.iam]
}

module "observability" {
  source            = "./modules/observability"
  api_deployment_id = module.api_gateway.deployment_id
}
```

### Module Outputs

```hcl
# modules/api-gateway/outputs.tf
output "gateway_id" {
  value = oci_apigateway_gateway.this.id
}
output "deployment_id" {
  value = oci_apigateway_deployment.this.id
}
output "deployment_endpoint" {
  value       = oci_apigateway_deployment.this.endpoint
  description = "Public API endpoint URL"
}
```

---

## Verification Loop

The agent MUST execute after each code generation:

### 1. Init & Provider Lock
```bash
terraform init -upgrade
# Exit code: 0 (success) | 1 (error)
```
**Expected output**: `Terraform has been successfully initialized!` with `oracle/oci v6.x` (or higher within constraint)
**Exit code**: 0

### 2. Format Check
```bash
terraform fmt -recursive -check=true
# Exit code: 0 (formatted) | 3 (needs formatting)
```
**Expected output**: Exit 0 (no formatting issues)
**Exit code**: 0

### 3. Validate Configuration
```bash
terraform validate
# Exit code: 0 (valid) | 1 (invalid configuration)
```
**Expected output**: `Success! The configuration is valid.`
**Exit code**: 0

### 4. Plan with Review
```bash
terraform plan -var-file="terraform.tfvars" -out=tfplan
# Exit code: 0 (no changes) | 1 (error) | 2 (changes pending)
terraform show tfplan | head -50
```
**Expected output**: Plan showing `oci_apigateway_gateway` and `oci_apigateway_deployment` resources
**Exit code**: 0

### 5. Verify Deployment (post-apply)
```bash
terraform output api_gateway_endpoint
# Exit code: 0 (success) | 1 (error)
curl -s "$(terraform output -raw api_gateway_endpoint)/health" | jq .
# Exit code: 0 (success) | 1 (error)
```
**Expected output**: `{"status":"healthy","environment":"<env>"}`
**Status code**: 200

### 6. Security Scan (recommended)
```bash
tfsec . --format sarif
# Exit code: 0 (no issues) | 1 (issues found)
checkov -d . --framework terraform --quiet
# Exit code: 0 (passed) | 1 (failed checks)
```
**Expected output**: No CRITICAL or HIGH findings related to credentials, encryption, or network exposure

**Troubleshooting**:
- **502 Bad Gateway on Function routes** → IAM policy `use fn-invocation` missing or not propagated (wait 60s)
- **Gateway stuck in CREATING** → Check subnet/NSG configuration; verify Internet Gateway exists for PUBLIC endpoint
- **Rate limit errors during testing** → Wait for rate window reset; increase rate limit for testing

---

## Quick Reference

**Most used commands**:
```bash
terraform init -upgrade                            # Init with latest provider within constraint
terraform fmt -recursive                           # Format all .tf files
terraform validate                                 # Validate configuration
terraform plan -var-file="terraform.tfvars"         # Preview changes
terraform apply -var-file="terraform.tfvars"        # Apply changes
terraform state list | grep apigateway             # List API Gateway resources in state
terraform import module.api_gateway.oci_apigateway_gateway.this <ocid>  # Import existing gateway
```

**Essential patterns**:
```hcl
# Gateway endpoint (from output)
oci_apigateway_deployment.this.endpoint

# Function backend route
backend {
  type        = "ORACLE_FUNCTIONS_BACKEND"
  function_id = var.function_id
}

# Stock response (health check)
backend {
  type   = "STOCK_RESPONSE_BACKEND"
  status = 200
  body   = jsonencode({ status = "healthy" })
}

# Rate limiting
rate_limiting {
  rate_in_requests_per_second = 100
  rate_key                    = "CLIENT_IP"
}
```

**Scalability limits**:
| Resource | Limit |
|----------|-------|
| Gateways per compartment | 50 (requestable increase) |
| Deployments per gateway | 100 |
| Routes per deployment | 100 |
| Rate limit max | 10,000 req/s |
| Request/Response body | 10 MB |
| Function timeout | 300s |

---

## Deployment Workflow

```
Provisioning Progress:
- [ ] terraform init -upgrade
- [ ] terraform fmt -recursive -check (exit 0)
- [ ] terraform validate (exit 0)
- [ ] terraform plan -out=tfplan (review)
- [ ] terraform apply tfplan
- [ ] Verify resources via OCI CLI
- [ ] Validate JWT/CORS/rate-limiting policies on deployment routes
- [ ] Test endpoint invocation (curl with expected status codes)
- [ ] Commit state and tag release
```

## External Resources

### Official Documentation
- [OCI API Gateway — Service Overview](https://docs.oracle.com/en-us/iaas/Content/APIGateway/home.htm)
- [oci_apigateway_gateway — Terraform Registry](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apigateway_gateway)
- [oci_apigateway_deployment — Terraform Registry](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apigateway_deployment)
- [API Gateway Authentication](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingauthentication.htm)
- [API Gateway Rate Limiting & Policies](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingpolicies.htm)

### Security
- [OCI IAM Policies for API Gateway](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatingpolicies.htm)
- [OCI Network Security Groups](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm)
- [Terraform State Sensitive Data](https://developer.hashicorp.com/terraform/language/state/sensitive-data)
- [OCI WAF](https://docs.oracle.com/en-us/iaas/Content/WAF/Concepts/overview.htm)

### Integration & Examples
- [Functions + API Gateway Integration](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsintegratingwithAPIgateway.htm)
- [API Gateway Response Caching](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayresponsecaching.htm)
- [Terraform OCI Provider — GitHub Examples](https://github.com/oracle/terraform-provider-oci/tree/master/examples/api_gateway)
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)

### Related Skills
- [provisioning-oci-iam](../provisioning-oci-iam/SKILL.md) — Dynamic Groups and Policies for API Gateway → Functions
- [designing-oci-networking](../designing-oci-networking/SKILL.md) — VCN, Subnets, NSGs, Gateways
- [architecting-oci-serverless](../architecting-oci-serverless/SKILL.md) — Functions Application and Function resources
- [designing-oci-vault-security](../designing-oci-vault-security/SKILL.md) — Secrets management with OCI Vault

---

## Multi-Backend Routing

### When to Use

`var.route_backends` is the **only** routing mechanism. Each route maps to a specific function backend:
- Different routes can target different function backends
- Routes have per-route auth_type configuration (e.g., some ANONYMOUS, some AUTHENTICATION_ONLY)
- Multiple functions share the same API Gateway deployment

### Variable Pattern

```hcl
variable "route_backends" {
  type = list(object({
    path        = string
    methods     = list(string)
    function_id = string
    auth_type   = optional(string, "AUTHENTICATION_ONLY")  # or "ANONYMOUS"
  }))
  # Required — no default
}
```

### Example: Multi-Function Routing

```hcl
route_backends = [
  # Routes for api-handler function
  { path = "/hello",  methods = ["GET", "POST"], function_id = module.app_api_handler.function_id },
  
  # Routes for func-api-facade function
  { path = "/secret", methods = ["POST"], function_id = module.app_api_facade.function_id },
  { path = "/store",  methods = ["POST"], function_id = module.app_api_facade.function_id },
]
```

### Auth Type per Route

| auth_type | Behavior |
|-----------|----------|
| `AUTHENTICATION_ONLY` | Requires valid JWT (default) |
| `ANONYMOUS` | No authentication required (use for health checks, public endpoints) |

### ✅ Always Do
- Set explicit `auth_type` for each route (don't rely on defaults for security-sensitive routes)
- Use module output references for `function_id` (never hardcode OCIDs)
- Verify all function_ids reference functions in the same compartment

### 🚫 Never Do
- Use ANONYMOUS auth_type for routes that handle sensitive data
- Reference function_ids from a different Terraform state without data source
