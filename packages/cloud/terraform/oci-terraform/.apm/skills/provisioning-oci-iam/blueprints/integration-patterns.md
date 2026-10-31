## Integration Patterns

### Terraform IAM ↔ OCI Functions

**Purpose**: Dynamic Group + Policy enables Functions to authenticate as Resource Principals for service-to-service access.

```hcl
# Dynamic Group identifies Functions in the target compartment (OCI Provider v6.x+)
resource "oci_identity_dynamic_group" "functions" {
  compartment_id = var.tenancy_ocid
  name           = "dg-functions-${var.project_name}-${var.environment}"
  matching_rule  = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"
}

# Policy grants Functions access to OCI services
resource "oci_identity_policy" "functions_services" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-services-${var.project_name}-${var.environment}"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read secret-bundles in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to manage objects in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use log-content in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use stream-push in compartment ${var.compartment_name}",
  ]
}

# Service policy: FaaS accesses VCN and OCIR (tenancy-level)
resource "oci_identity_policy" "faas_network" {
  compartment_id = var.tenancy_ocid
  name           = "policy-faas-network-${var.project_name}-${var.environment}"
  statements = [
    "Allow service FaaS to use virtual-network-family in compartment ${var.compartment_name}",
    "Allow service FaaS to read repos in tenancy",
  ]
}
```

**Common Issues**:
- **Issue**: `fnfunc` resource type is lowercase — using `FnFunc` or `FNFUNC` silently matches nothing
  **Solution**: Always use `fnfunc` (lowercase)
- **Issue**: Policy propagation delay causes Function deploy failure
  **Solution**: Add `depends_on = [module.iam]` to Functions module
- **Issue**: Matching rule evaluated at invocation time, not deployment time
  **Solution**: Verify Dynamic Group membership via OCI Console after deployment

**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingpolicies.htm

---

### Terraform IAM ↔ OCI API Gateway

**Purpose**: Dynamic Group + Policy enables API Gateway to invoke Functions.

```hcl
# API Gateway Dynamic Group — 'ApiGateway' is PascalCase (OCI Provider v6.x+)
resource "oci_identity_dynamic_group" "api_gateway" {
  compartment_id = var.tenancy_ocid
  name           = "dg-apigw-${var.project_name}-${var.environment}"
  matching_rule  = "ALL {resource.type = 'ApiGateway', resource.compartment.id = '${var.compartment_ocid}'}"
}

resource "oci_identity_policy" "apigw_invoke" {
  compartment_id = var.compartment_ocid
  name           = "policy-apigw-invoke-${var.project_name}-${var.environment}"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.api_gateway.name} to use fn-invocation in compartment ${var.compartment_name}",
  ]
}
```

**Common Issues**:
- **Issue**: `ApiGateway` is PascalCase — `apigateway` or `API_GATEWAY` silently matches nothing
  **Solution**: Always use `ApiGateway` exactly
- **Issue**: Without `fn-invocation` policy, API Gateway returns 502 Bad Gateway
  **Solution**: Create the policy and ensure `depends_on` is set
- **Issue**: `fn-invocation` is a specific resource type (not `functions-family`)
  **Solution**: Use `fn-invocation` for invocation only; add more statements for other operations

**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatingpolicies.htm

---

### Terraform IAM ↔ OCI Vault (Secrets)

**Purpose**: Dynamic Group + Policy enables Functions to read secrets at runtime.

```hcl
# Functions Vault policy (OCI Provider v6.x+)
resource "oci_identity_policy" "functions_vault" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-vault-${var.project_name}-${var.environment}"
  statements = [
    # read secret-bundles = actual secret CONTENT (not just metadata)
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read secret-bundles in compartment ${var.compartment_name}",
    # use keys = encrypt/decrypt with Vault keys (if needed)
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use keys in compartment ${var.compartment_name}",
  ]
}
```

**Common Issues**:
- **Issue**: `read secrets` ≠ `read secret-bundles`. `secrets` = metadata only; `secret-bundles` = actual content
  **Solution**: Always use `secret-bundles` for reading secret values
- **Impact**: Using `read secrets` leads to "permission denied" at runtime when Function tries to read secret content

**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

### Terraform IAM ↔ OCI Object Storage

**Purpose**: Dynamic Group + Policy enables Functions to read/write objects.

```hcl
# Functions Object Storage policy (OCI Provider v6.x+)
resource "oci_identity_policy" "functions_objectstorage" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-objectstorage-${var.project_name}-${var.environment}"
  statements = [
    # manage objects = CRUD on objects in buckets
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to manage objects in compartment ${var.compartment_name}",
    # read buckets = list and get bucket metadata (needed to find objects)
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read buckets in compartment ${var.compartment_name}",
  ]
}
```

**Common Issues**:
- **Issue**: `manage objects` does NOT include `manage buckets` (create/delete buckets are separate)
  **Solution**: Add `manage buckets` only if Functions need to create/delete buckets themselves

**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/objectstoragepolicyreference.htm

---

### Terraform IAM ↔ OCI Networking (VCN)

**Purpose**: Service policy enables FaaS to place Functions in VCN subnets.

```hcl
# FaaS service needs VCN access to deploy Functions in private subnets (OCI Provider v6.x+)
# This is a SERVICE policy (not Dynamic Group) — tenancy-level only
resource "oci_identity_policy" "faas_network" {
  compartment_id = var.tenancy_ocid
  name           = "policy-faas-network-${var.project_name}-${var.environment}"
  statements = [
    "Allow service FaaS to use virtual-network-family in compartment ${var.compartment_name}",
  ]
}
```

**Common Issues**:
- **Issue**: This is a SERVICE policy (`Allow service FaaS`), not a Dynamic Group policy
  **Solution**: Always place at `tenancy_ocid` level, not compartment level
- **Issue**: Without this policy, Function Application creation fails
  **Solution**: Create this policy before any Function deployment; only needs to be created once per compartment

**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingpolicies.htm

---

### Terraform IAM ↔ OCI Logging

**Purpose**: Dynamic Group + Policy enables Functions to write execution logs.

```hcl
# Functions Logging policy (OCI Provider v6.x+)
resource "oci_identity_policy" "functions_logging" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-logging-${var.project_name}-${var.environment}"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use log-content in compartment ${var.compartment_name}",
  ]
}
```

**Common Issues**:
- **Issue**: `use log-content` allows writing to Log Groups; `read log-content` only allows reading
  **Solution**: Functions typically need `use` for writing execution logs

**Source**: https://docs.oracle.com/en-us/iaas/Content/Logging/Task/managinglogs.htm
