## Integration Patterns

### Functions ↔ API Gateway

API Gateway uses `ORACLE_FUNCTIONS_BACKEND` to invoke functions. Requires IAM policy allowing gateway to invoke the function.

```hcl
# API Gateway route with Function backend (OCI Provider v6.x+)
resource "oci_apigateway_deployment" "api" {
  # ...
  specification {
    routes {
      path    = "/api/v1/{path*}"
      methods = ["GET", "POST", "PUT", "DELETE"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = oci_functions_function.api_handler.id
      }
    }
  }
}
```
**Dependency**: API Gateway needs IAM policy: `Allow dynamic-group <apigw-dg> to use functions-family in compartment <name>`
**Source**: See [designing-oci-api-gateway](../../designing-oci-api-gateway/SKILL.md) skill for complete API Gateway patterns.

---

### Functions ↔ IAM (Dynamic Groups + Policies)

Functions authenticate to OCI services via Resource Principal — no credentials needed. Dynamic Groups and Policies grant access.

```hcl
# Dynamic Group for Functions (OCI Provider v6.x+)
resource "oci_identity_dynamic_group" "functions" {
  compartment_id = var.tenancy_ocid
  name           = "dg-functions-${var.project_name}-${var.environment}"
  description    = "Dynamic group for OCI Functions"
  matching_rule  = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"
}

# Policy: Functions access Vault secrets and Object Storage
resource "oci_identity_policy" "functions" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-${var.project_name}-${var.environment}"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read secret-bundles in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to manage objects in compartment ${var.compartment_name} where target.bucket.name = '${var.bucket_name}'",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use log-content in compartment ${var.compartment_name}",
  ]
}
```
**Source**: See [provisioning-oci-iam](../../provisioning-oci-iam/SKILL.md) skill for complete IAM patterns.

---

### Functions ↔ Network (Private Subnet + NSG)

Functions require a private subnet with Service Gateway for OCIR access.

```hcl
# Wire network module into function-app (OCI Provider v6.x+)
module "app_my_function" {
  source = "../../modules/function-app"

  subnet_id = module.network.subnet_private_id
  nsg_ids   = [module.network.nsg_functions_id]
  # ...
}
```
**Dependency**: Private subnet must have Service Gateway in its route table for OCIR access. Without it, function image pulls fail with "SubnetNotAuthorized".
**Source**: See [designing-oci-networking](../../designing-oci-networking/SKILL.md) skill for complete networking patterns.

---

### Functions ↔ Vault (Secrets at Runtime)

Terraform passes only the Vault secret OCID via `config` — never the secret value. Function code reads the secret at runtime using Resource Principal.

```hcl
# Pass secret OCIDs only — never secret values (OCI Provider v6.x+)
resource "oci_functions_function" "this" {
  # ...
  config = {
    "DB_SECRET_OCID"  = oci_vault_secret.db_password.id   # OCID only
    "API_SECRET_OCID" = oci_vault_secret.api_key.id        # OCID only
  }
}

# Java function reads secret at runtime:
# SecretsClient client = SecretsClient.builder()
#   .build(ResourcePrincipalAuthenticationDetailsProvider.builder().build());
# GetSecretBundleResponse response = client.getSecretBundle(
#   GetSecretBundleRequest.builder().secretId(secretOcid).build());
```
**Source**: See [designing-oci-vault-security](../../designing-oci-vault-security/SKILL.md) skill for complete Vault patterns.

---

### Functions ↔ Observability (APM + Logging)

Tracing and logging are critical for debugging ephemeral functions. Configure at the Application level to propagate to all functions.

```hcl
# APM tracing and JSON logging (OCI Provider v6.x+)
resource "oci_functions_application" "this" {
  # ...
  trace_config {
    domain_id  = var.apm_domain_id  # OCID of APM Domain — isolates per environment
    is_enabled = true
  }

  # Structured logging for parsing
  logging {
    line_format = "JSON"  # JSON or PLAIN
  }
}
```
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsexportingfunctionlogfiles.htm

---

### Multiple Functions per Application (for_each)

Create multiple functions from a variable map — all share the same Application (VCN, NSGs, config).

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

---

### CI/CD Integration (Image Tag via Variable)

Pipeline generates `terraform.tfvars` with image tag and digest from the build stage.

```hcl
# terraform.tfvars — generated by CI/CD pipeline
function_image        = "gru.ocir.io/namespace/repo:v1.2.3-abc123"
function_image_digest = "sha256:ca0eeb6fb05351dfc8759c20733c91def84cb8007aa89a5bf606bc8b315b9fc7"

# Pipeline steps:
# 1. docker build + docker push → OCIR
# 2. Extract digest: docker inspect --format='{{index .RepoDigests 0}}' image
# 3. terraform apply -var="function_image=..." -var="function_image_digest=..."
```

---

### Invoke Function for Testing/Warm-up

Health check invocation immediately after deploy to verify function is reachable and warm.

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

### Module Interface Reference

#### Variables (inputs)

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

#### Outputs

| Output | Description |
|--------|-------------|
| `application_id` | OCID of the Functions Application |
| `function_id` | OCID of the Function |
| `function_invoke_endpoint` | HTTPS invoke URL (sensitive) |
| `function_state` | Current state (ACTIVE, INACTIVE, etc.) |
| `application_state` | Application lifecycle state |

---

### Multi-Function Application Decision

Use `var.functions` (list mode) instead of `function_name`/`function_image` (singular) when deploying multiple functions that share the same VCN, NSGs, and application config.

| Criteria | Same Application | New Application |
|----------|-----------------|-----------------|
| Shared VCN/Subnet | Yes | Redundant |
| Shared NSGs | Yes | Separate |
| Shared config (ENVIRONMENT, etc.) | Yes | Duplicated |
| Independent scaling | Per-function memory/timeout | Per-function |
| Isolation requirement | Not isolated | Fully isolated |
| Different teams/lifecycle | Coupled deploys | Independent |

**Rule of thumb**: Same Application unless there is a strong isolation requirement.

```hcl
variable "functions" {
  type = list(object({
    name                    = string
    image                   = string
    memory_in_mbs           = optional(number, 256)
    timeout_in_seconds      = optional(number, 30)
    provisioned_concurrency = optional(number, 0)
    config                  = optional(map(string), {})
  }))
  default = []
}
```

**Naming convention**:
- Application: `{application_name}-{environment}` (e.g., `app-integration-patterns-dev`)
- Function: `{function_name}-{environment}` (e.g., `func-api-facade-dev`)
