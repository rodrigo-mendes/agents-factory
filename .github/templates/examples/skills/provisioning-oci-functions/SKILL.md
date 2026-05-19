---
name: provisioning-oci-functions
description: Provisions OCI Functions resources (Application, Function, Invoke, PBF) with Terraform OCI Provider v6.x+. Use when provisioning Functions infrastructure for serverless architectures.
---

## Version Context

**Technology**: Terraform OCI Provider — Functions (`oci_functions_application`, `oci_functions_function`, `oci_functions_invoke_function`)
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Target Service**: OCI Functions (FaaS based on Fn Project)
**Terraform Version**: >= 1.7
**Provider Version**: oracle/oci >= 6.0, < 9.0
**Provider Registry**: https://registry.terraform.io/providers/oracle/oci/latest/docs
**Release Date**: 2024–2026 (continuous releases, latest 8.13.0)
**Support Status**: Active

**Key Constraints**:
- Hierarchical model: **Application** → 1..N **Functions**. Application defines network, shape, tracing; Function defines image, memory, timeout
- `shape` (GENERIC_X86, GENERIC_ARM, GENERIC_X86_ARM) is **Application-level and immutable** — changing forces destroy/recreate
- `subnet_ids` on Application is **immutable** — cannot change without destroy/recreate
- `image` and `image_digest` **MUST be updated together** — updating one without the other causes inconsistent deploys
- `memory_in_mbs` determines CPU proportionally: 128MB = 1/8 vCPU, 256MB = 1/4, 512MB = 1/2, 1024MB = 1, 2048MB = 1 vCPU (max)
- Application destroy has a **known 5-minute delay** — pipelines must account for this
- Config size (keys + values) limited to **4 KB** total

**Key Advances (2024–2026)**:
- **Provisioned Concurrency**: CONSTANT strategy to eliminate cold starts
- **Detached Mode**: Async invocation with success/failure destinations (Streaming, Queue, Notifications)
- **Pre-Built Functions (PBF)**: Ready-made functions via `source_details.pbf_listing_id`
- **Image Signature Verification**: `image_policy_config` with KMS keys for supply chain security
- **ARM/Multi-Architecture**: Shapes `GENERIC_X86`, `GENERIC_ARM`, `GENERIC_X86_ARM`

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform OCI Provider v6.x+. Do NOT mix syntax from older provider versions. Always use private subnets for Functions Applications. Never store secrets in `config` — use OCI Vault with Resource Principal.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Cross-service integration examples
- **[Module Interface](#module-interface)** — Variables and outputs reference
- **[Advanced Patterns](#advanced-patterns)** — for_each, CI/CD, warm-up invocation
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Provider Version Constraint** — Lock OCI provider to tested range. Functions depend on networking, IAM, and OCIR
- **Application in Private Subnet with NSGs** — Zero internet ingress. Cannot change subnet without destroy/recreate
- **Function with Image, Memory, Timeout, Config** — `image` + `image_digest` must update atomically. Explicit timeout prevents runaway costs
- **OCIR Image URI Format** — Region-specific format: `<region-key>.ocir.io/<namespace>/<repo>:<tag>`. Wrong format → 502
- **IAM `depends_on`** — Function invocations fail with 502 until IAM policies propagate (~60s)

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Provisioned Concurrency vs On-Demand** — Provisioned eliminates cold starts but costs more. Needed for <100ms latency SLAs
- **Synchronous vs Detached Mode (Async)** — Detached for fire-and-forget (max 720s). Sync for request-response (max 300s)
- **Processor Architecture** — GENERIC_X86 (default), GENERIC_ARM (20% cheaper), GENERIC_X86_ARM (flexible)

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Credentials in Function Config** — CRITICAL: Plaintext in state file. Use OCI Vault secrets
- **Application in Public Subnet** — HIGH: Direct internet traffic bypasses API Gateway protections
- **Updating `image` without `image_digest`** — Non-deterministic behavior: old image may keep running
- **Hardcoded OCIDs** — Breaks portability across environments. Use Terraform references

---

## Integration Patterns

For complete integration code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Summary of integrations**:
- **Functions ↔ API Gateway** — Route configuration with Function backend type and IAM dependencies
- **Functions ↔ IAM** — Dynamic Groups matching application OCID + least-privilege policies
- **Functions ↔ Network** — Private subnet, NSG rules for API Gateway ingress only
- **Functions ↔ Vault** — Secret retrieval at runtime via config keys (not Terraform state)
- **Functions ↔ Observability** — APM tracing domain + OCI Logging integration
## Advanced Patterns

### Multiple Functions per Application (for_each)

```hcl
# Create multiple functions from a map (OCI Provider v6.x+)
variable "functions" {
  type = map(object({
    image              = string
    memory_in_mbs      = number
    timeout_in_seconds = number
    config             = map(string)
  }))
}

resource "oci_functions_function" "this" {
  for_each = var.functions

  application_id     = oci_functions_application.this.id
  display_name       = each.key
  image              = each.value.image
  memory_in_mbs      = each.value.memory_in_mbs
  timeout_in_seconds = each.value.timeout_in_seconds
  config             = each.value.config

  trace_config {
    is_enabled = var.enable_tracing
  }

  freeform_tags = var.tags
}
```

### CI/CD Integration (Image Tag via Variable)

```hcl
# terraform.tfvars — generated by CI/CD pipeline
function_image        = "gru.ocir.io/namespace/repo:v1.2.3-abc123"
function_image_digest = "sha256:ca0eeb6fb05351dfc8759c20733c91def84cb8007aa89a5bf606bc8b315b9fc7"

# Pipeline steps:
# 1. docker build + docker push → OCIR
# 2. Extract digest: docker inspect --format='{{index .RepoDigests 0}}' image
# 3. terraform apply -var="function_image=..." -var="function_image_digest=..."
```

### Invoke Function for Testing/Warm-up

```hcl
# Health check invocation after deploy (OCI Provider v6.x+)
resource "oci_functions_invoke_function" "healthcheck" {
  function_id          = oci_functions_function.api_handler.id
  invoke_function_body = jsonencode({ action = "healthcheck" })
  fn_intent            = "httprequest"
  fn_invoke_type       = "sync"

  depends_on = [oci_functions_function.api_handler]
}
```

---

## Module Interface Reference

### Variables (inputs)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `compartment_ocid` | string | — | OCID of the compartment |
| `subnet_id` | string | — | OCID of the private subnet |
| `nsg_ids` | list(string) | `[]` | NSG IDs for the Application |
| `application_name` | string | — | Application display name |
| `function_name` | string | — | Function display name |
| `function_image` | string | — | Full OCIR image URI |
| `function_image_digest` | string | `null` | SHA256 digest of the image |
| `function_memory_in_mbs` | number | `256` | Memory: 128, 256, 512, 1024, 2048 |
| `function_timeout_in_seconds` | number | `30` | Timeout: 5–300 seconds |
| `function_config` | map(string) | `{}` | Env vars passed to function |
| `function_shape` | string | `GENERIC_ARM` | Processor architecture |
| `provisioned_concurrency` | number | `0` | Pre-warmed instances (0–40) |
| `enable_tracing` | bool | `true` | Enable APM tracing |
| `apm_domain_id` | string | `null` | APM Domain OCID |

### Outputs

| Output | Description |
|--------|-------------|
| `application_id` | OCID of the Functions Application |
| `function_id` | OCID of the Function |
| `function_invoke_endpoint` | HTTPS invoke URL (sensitive) |
| `function_state` | Current state (ACTIVE, INACTIVE, etc.) |
| `application_state` | Application lifecycle state |

---

## Service Limits & Quotas

| Resource | Limit | Scope |
|----------|-------|-------|
| Applications per compartment | 10 (default) | Compartment |
| Functions per application | 20 (default) | Application |
| Concurrent executions | 60 (default) | Compartment |
| Provisioned concurrency per function | 40 | Function |
| Total provisioned concurrency per region | 400 | Region |
| Memory per function | 128–2048 MB | Function |
| Timeout per function | 5–300 seconds | Function |
| Config size (keys + values) | 4 KB | Application/Function |
| NSGs per application | 5 | Application |
| Image size | 6 GB | Function |

---

## Verification Loop

The agent MUST execute after each code generation:

### 1. Validate Terraform Configuration
```bash
terraform validate
# Exit code: 0 (valid) | 1 (invalid configuration)
```
**Expected output**: `Success! The configuration is valid.`
**Exit code**: 0

### 2. Plan
```bash
terraform plan -out=plan.tfplan
# Exit code: 0 (no changes) | 1 (error) | 2 (changes pending)
```
**Expected output**: Plan showing resources to create/modify
**Exit code**: 0

### 3. Verify Application Created
```bash
oci fn application list \
# Exit code: 0 (success) | 1 (auth/network error)
  --compartment-id $COMPARTMENT_OCID \
  --query 'data[*].{"name":"display-name","shape":"shape","state":"lifecycle-state","subnets":"subnet-ids"}' \
  --output table
```
**Expected output**: Table with application in ACTIVE state

### 4. Verify Function Created
```bash
oci fn function list \
# Exit code: 0 (success) | 1 (auth/network error)
  --application-id $APP_OCID \
  --query 'data[*].{"name":"display-name","memory":"memory-in-mbs","timeout":"timeout-in-seconds","state":"lifecycle-state","image":"image"}' \
  --output table
```
**Expected output**: Table with function in ACTIVE state

### 5. Invoke Function (Health Check)
```bash
oci fn function invoke \
# Exit code: 0 (success) | 1 (auth/network error)
  --function-id $FUNCTION_OCID \
  --body '{"action": "healthcheck"}' \
  --file -
```
**Expected output**: Response JSON from function

### 6. Verify Terraform State
```bash
terraform state list | grep "module.functions"
# Exit code: 0 (success) | 1 (error)
terraform state show module.functions.oci_functions_function.this
# Exit code: 0 (success) | 1 (not found)
```
**Expected output**: Resources listed with correct attributes

**Troubleshooting**:
- **502 on invocation** → Verify OCIR image URI, test `docker pull` locally, check function logs
- **Cold start > 10s (Java)** → Enable `provisioned_concurrency_config` with count >= 1, or use GraalVM native image
- **"NotAuthenticated"** → Verify Dynamic Group matching rule, wait up to 5 min for IAM propagation
- **"SubnetNotAuthorized"** → Verify Service Gateway in private subnet route table for OCIR access
- **Application destroy timeout** → Increase `timeouts { delete = "10m" }`, known OCI delay ~5 min
- **Config perpetual diff** → Normalize config keys, use `ignore_changes = [config]` temporarily
- **"FunctionConfigTooLarge"** → Move data to Object Storage or Vault, pass only OCIDs via config

---

## Quick Reference

**Most used commands**:
```bash
# List applications
oci fn application list --compartment-id $COMPARTMENT_OCID --output table

# List functions in application
oci fn function list --application-id $APP_OCID --output table

# Invoke function
oci fn function invoke --function-id $FUNCTION_OCID --body '{}' --file -

# Check provisioned concurrency
oci fn function get --function-id $FUNCTION_OCID --query 'data."provisioned-concurrency-config"'

# List Pre-Built Functions
oci fn pbf-listing list --all --output table
```

**Essential patterns**:
```hcl
# Terraform import existing resources
terraform import module.functions.oci_functions_application.this "<application_ocid>"
terraform import module.functions.oci_functions_function.this "<function_ocid>"

# Import with for_each key
terraform import 'module.functions.oci_functions_function.handlers["api-handler"]' "<function_ocid>"
```

---

## Data Sources Reference

| Data Source | Purpose | Key Arguments |
|-------------|---------|---------------|
| `oci_functions_application` | Get single application by ID | `application_id` |
| `oci_functions_applications` | List applications in compartment | `compartment_id`, `display_name`, `state` |
| `oci_functions_function` | Get single function by ID | `function_id` |
| `oci_functions_functions` | List functions in application | `application_id`, `display_name`, `state` |
| `oci_functions_pbf_listing` | Get Pre-Built Function listing | `pbf_listing_id` |
| `oci_functions_pbf_listings` | List available PBFs | `name`, `trigger` |
| `oci_functions_pbf_listing_version` | Get PBF version details | `pbf_listing_version_id` |
| `oci_functions_pbf_listing_versions` | List PBF versions | `pbf_listing_id`, `state` |

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
- [ ] Verify image+digest atomic update (function invoke succeeds)
- [ ] Confirm application subnet and NSG assignments
- [ ] Commit state and tag release
```

## External Resources

### Official Documentation
- [OCI Functions Documentation](https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm)
- [OCI Functions Concepts](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsconcepts.htm)
- [OCI Functions Networking](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringnetworking.htm)

### Terraform Registry
- [oci_functions_application](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_application)
- [oci_functions_function](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_function)
- [oci_functions_invoke_function](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_invoke_function)
- [PBF Data Sources](https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/functions_pbf_listings)

### Security
- [Functions Security (Resource Principal)](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingpolicies.htm)
- [Image Signature Verification](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingimagesignatureverification.htm)

### Performance
- [Provisioned Concurrency](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingprovisionedconcurrency.htm)
- [Functions Pricing](https://www.oracle.com/cloud/price-list/#functions)

### Logging & Tracing
- [Functions Logging](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsexportingfunctionlogfiles.htm)

### Source Code & Examples
- [OCI Terraform Provider GitHub](https://github.com/oracle/terraform-provider-oci)
- [OCI Functions Terraform Examples](https://github.com/oracle/terraform-provider-oci/tree/master/examples/functions)
- [OCI Provider Changelog](https://github.com/oracle/terraform-provider-oci/blob/master/CHANGELOG.md)
- [OCIR Registry Docs](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryoverview.htm)
