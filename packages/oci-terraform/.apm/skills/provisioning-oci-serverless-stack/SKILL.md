---
name: provisioning-oci-serverless-stack
description: Provisions a complete serverless API stack (OCI Functions + API Gateway + IAM) as an integrated Terraform module. Use when deploying a full serverless stack. For individual services, use provisioning-oci-functions, provisioning-oci-api-gateway, or provisioning-oci-iam instead.
---

## Version Context

**Technology**: Terraform OCI Provider — Functions + API Gateway + IAM
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Terraform Version**: >= 1.7
**Provider Version**: oracle/oci >= 6.0, < 9.0 (latest 8.12.0, 105M+ downloads)
**Provider Registry**: https://registry.terraform.io/providers/oracle/oci/latest
**Support Status**: Active (GA — all features production-ready)

**Key Resources Managed**:

| Service | Terraform Resources |
|---------|-------------------|
| OCI Functions | `oci_functions_application`, `oci_functions_function` |
| API Gateway | `oci_apigateway_gateway`, `oci_apigateway_deployment`, `oci_apigateway_certificate` |
| IAM | `oci_identity_dynamic_group`, `oci_identity_policy`, `oci_identity_compartment` |
| Networking | `oci_core_vcn`, `oci_core_subnet`, `oci_core_network_security_group` |

**Key Capabilities (Provider v6.x+)**:
- Provisioned Concurrency (`CONSTANT` strategy) for cold start elimination
- JWT Authentication on API Gateway deployments
- Resource Principal auth via Dynamic Groups
- Full NSG-based network security

**Service Limits**:

| Parameter | Default/Limit |
|-----------|--------------|
| Function memory | 128 – 2048 MB |
| Function timeout | 5 – 300 seconds |
| Concurrent executions per compartment | 60 (soft limit) |
| API Gateway requests/second per deployment | 500 (soft limit) |
| Dynamic group matching rules | 100 per dynamic group |

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform OCI Provider v6.x+ with Terraform >= 1.7. Credentials MUST NEVER be hardcoded — use Instance Principal (production) or config file (dev). State files MUST be encrypted with remote backend. IAM policies MUST follow least-privilege — never `manage all-resources in tenancy`.

> 📎 **Scope Clarification**: This is an **integration skill** that demonstrates the end-to-end provisioning of Functions + API Gateway + IAM as a single coherent stack. For **individual service provisioning**, use the dedicated skills:
> - Functions only → `provisioning-oci-functions`
> - API Gateway only → `provisioning-oci-api-gateway`
> - IAM only → `provisioning-oci-iam`
>
> Use THIS skill when provisioning a **complete serverless API stack from scratch**. Use the individual skills when modifying or extending an existing infrastructure.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Cross-service integration examples
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Terraform Configuration Block** — Version constraints for provider and Terraform. Encrypted remote backend for state
- **Provider Authentication** — Resource Principal/Instance Principal for production. Never hardcode credentials
- **Functions Application in Private Subnet** — NSG-controlled access. API Gateway in separate public subnet
- **API Gateway with JWT + Rate Limiting** — Deployment-level policies for all routes. Rate limit prevents cost explosion
- **Dynamic Groups with compartment scope** — `resource.compartment.id` matching for least-privilege
- **IAM Policies with `depends_on`** — 60s propagation delay. Gateway deployment must wait for policy creation

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **State Backend** — Local for solo dev, Remote (OCI Object Storage) for team collaboration
- **Provisioned Concurrency vs On-Demand** — Provisioned for <100ms latency SLAs, On-Demand for cost optimization

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Hardcoded credentials in provider** — CRITICAL: Full tenancy compromise via VCS/CI logs
- **Wildcard IAM policy (`manage all-resources`)** — Violates least-privilege. No explicit deny in OCI
- **Security group `0.0.0.0/0` on management ports** — Unrestricted access to SSH/RDP/admin interfaces
- **Unencrypted state file backend** — State contains OCIDs, connection strings, and sensitive config

---

## Integration Patterns

For complete integration code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Summary of integrations**:
- **Terraform ↔ OCI Functions** — Application + Function resources with OCIR image management
- **Terraform ↔ API Gateway** — Gateway + Deployment with route-to-function mapping
- **Terraform ↔ IAM** — Dynamic Groups + Policies with cross-resource dependencies
- **Terraform ↔ Networking** — VCN, subnets, gateways, NSGs for serverless topology

---

## Verification Loop

The agent MUST execute after each Terraform code generation:

### 1. Initialize & Upgrade Provider
```bash
terraform init -upgrade
# Exit code: 0 (success) | 1 (error)
```
**Expected output**: `Terraform has been successfully initialized!`
**Exit code**: 0

### 2. Validate Syntax
```bash
terraform validate
# Exit code: 0 (valid) | 1 (invalid configuration)
```
**Expected output**: `Success! The configuration is valid.`
**Exit code**: 0

### 3. Format Check
```bash
terraform fmt -recursive -check
# Exit code: 0 (formatted) | 3 (needs formatting)
```
**Expected output**: No output (all files formatted)
**Exit code**: 0

### 4. Plan
```bash
terraform plan -out=tfplan
# Exit code: 0 (no changes) | 1 (error) | 2 (changes pending)
```
**Expected output**: Plan with resources to create/modify/destroy
**Exit code**: 0

### 5. Security Scan
```bash
# tfsec for OCI-specific checks
tfsec . --format sarif
# Exit code: 0 (no issues) | 1 (issues found)

# Checkov for policy-as-code
checkov -d . --framework terraform
# Exit code: 0 (passed) | 1 (failed checks)
```
**Expected output**: No HIGH or CRITICAL severity findings

**Troubleshooting**:
- `Error: Invalid provider configuration` → Check `~/.oci/config` or environment variables
- `Error: 404-NotAuthorizedOrNotFound` → Verify compartment OCID and IAM policies
- `Error: 409-Conflict` → Resource already exists, import with `terraform import`
- Format failures → Run `terraform fmt -recursive` to auto-fix

---

## State Management

### Remote State (OCI Object Storage)

```hcl
# Pre-requisite: Create the state bucket (manually or in separate Terraform)
resource "oci_objectstorage_bucket" "terraform_state" {
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "terraform-state"
  access_type    = "NoPublicAccess"
  versioning     = "Enabled"

  freeform_tags = {
    "ManagedBy" = "manual"
    "Purpose"   = "terraform-state"
  }
}
```

**State Locking**: OCI Object Storage S3-compatible API does NOT support DynamoDB-style locking. Alternatives:
- Terraform Cloud/Enterprise for native state locking
- OCI Resource Manager (automatic locking)
- CI/CD pipeline serialization (convention-based)

---

## Production Considerations

### Scalability
- OCI Functions: Max 60 concurrent executions per compartment (soft limit — request increase via support ticket)
- API Gateway: Max 500 requests/second per deployment (soft limit)
- Dynamic Groups: Max 100 matching rules per dynamic group

### Cost Optimization
- Functions: Pay per invocation + execution time + memory
- API Gateway: Pay per API call + data transfer
- NAT Gateway: ~$0.028/hr flat fee + data transfer

### DR Strategy
- Functions: Deploy in multiple regions (identical code)
- API Gateway: OCI Traffic Management for DNS failover
- State: Versioning on Object Storage bucket + cross-region replication

---

## Quick Reference

**Essential Terraform commands**:
```bash
terraform init -upgrade          # Initialize and upgrade providers
terraform validate               # Validate configuration syntax
terraform fmt -recursive         # Format all .tf files
terraform plan -out=tfplan       # Generate execution plan
terraform apply tfplan           # Apply the saved plan
terraform import <resource> <id> # Import existing OCI resources
```

**Critical resource references**:
```hcl
# Function Application
oci_functions_application.app.id

# Function
oci_functions_function.handler.id

# API Gateway
oci_apigateway_gateway.this.id

# API Gateway Deployment endpoint
oci_apigateway_deployment.api.endpoint

# Dynamic Group
oci_identity_dynamic_group.functions.name
```

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
- [ ] End-to-end: deploy function, invoke via API Gateway, verify response
- [ ] Confirm IAM policies grant Functions access to required services
- [ ] Commit state and tag release
```

## External Resources

### Official Documentation
- [OCI Terraform Provider Registry](https://registry.terraform.io/providers/oracle/oci/latest) (verified 2026-07-26)
- [OCI Functions Documentation](https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm) (verified 2026-07-26)
- [OCI API Gateway Documentation](https://docs.oracle.com/en-us/iaas/Content/APIGateway/home.htm) (verified 2026-07-26)
- [OCI IAM Documentation](https://docs.oracle.com/en-us/iaas/Content/Identity/home.htm) (verified 2026-07-26)
- [OCI Terraform Examples (GitHub)](https://github.com/oracle/terraform-provider-oci/tree/master/examples) (verified 2026-07-26)

### Security
- [OCI IAM Common Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm) (verified 2026-07-26)
- [OCI Network Security Groups](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm) (verified 2026-07-26)
- [Terraform State Sensitive Data](https://developer.hashicorp.com/terraform/language/state/sensitive-data) (verified 2026-07-26)
- [OCI Tagging Overview](https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm) (verified 2026-07-26)

### Validation & Tools
- [tfsec — Terraform Security Scanner](https://github.com/aquasecurity/tfsec) (verified 2026-07-26)
- [Checkov — Policy-as-Code](https://www.checkov.io/) (verified 2026-07-26)
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) (verified 2026-07-26)

---

## Multi-Function Composition

### When to Use

Use multi-function mode when:
- A pattern requires more than one function in the same Application
- Different API routes must target different function backends
- Adding a new function to an existing deployment (incremental addition)

### Infrastructure Pattern

```hcl
# Multi-function: use var.functions list instead of singular function_name/function_image
functions = [
  {
    name                    = "api-handler"
    image                   = "gru.ocir.io/ns/repo/api-handler:0.0.5"
    memory_in_mbs           = 256
    timeout_in_seconds      = 60
    provisioned_concurrency = 0
    config                  = {}
  },
  {
    name                    = "func-api-facade"
    image                   = "gru.ocir.io/ns/repo/func-api-facade:0.0.1"
    memory_in_mbs           = 256
    timeout_in_seconds      = 60
    provisioned_concurrency = 0
    config                  = {}
  },
]

# Per-route function targeting via route_backends
route_backends = [
  { path = "/hello",  methods = ["GET", "POST"], function_id = "<from output>", auth_type = "AUTHENTICATION_ONLY" },
  { path = "/secret", methods = ["POST"],        function_id = "<from output>", auth_type = "AUTHENTICATION_ONLY" },
  { path = "/store",  methods = ["POST"],        function_id = "<from output>", auth_type = "AUTHENTICATION_ONLY" },
]
```

### Outputs

Multi-function mode produces map-based outputs:
- `function_ids` — Map of `{ function_name => ocid }` for all functions
- `function_endpoints` — Map of `{ function_name => invoke_endpoint }`

### Adding a New Function

To add a function to an existing environment:
1. Add a new `module "app_<name>"` block in `apps.tf` using `../../modules/function-app`
2. Add route entry in `route_backends` of the `module.api_gateway` block
3. Run `terraform plan` — should show only new resource additions

### ✅ Always Do (Multi-Function)
- Use one `function-app` module instance per function (isolated Applications)
- Set `function_id` per route in `route_backends` (never assume single backend)
- Verify `terraform plan` shows no destructive changes when adding functions

### 🚫 Never Do (Multi-Function)
- Share the same Application for unrelated functions (blast radius)
- Hardcode function OCIDs — always reference from module outputs
- Skip `depends_on = [module.iam]` for function-app modules
