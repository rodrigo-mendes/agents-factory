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
**Source**: See [designing-oci-api-gateway](../designing-oci-api-gateway/SKILL.md) skill for complete API Gateway patterns.

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
**Source**: See [provisioning-oci-iam](../provisioning-oci-iam/SKILL.md) skill for complete IAM patterns.

---

### Functions ↔ Network (Private Subnet + NSG)

Functions require a private subnet with Service Gateway for OCIR access.

```hcl
# Wire network module into functions (OCI Provider v6.x+)
module "functions" {
  source = "./modules/functions"

  subnet_id = module.network.subnet_private_id
  nsg_ids   = [module.network.nsg_functions_id]
  # ...
}
```
**Dependency**: Private subnet must have Service Gateway in its route table for OCIR access. Without it, function image pulls fail with "SubnetNotAuthorized".
**Source**: See [designing-oci-networking](../designing-oci-networking/SKILL.md) skill for complete networking patterns.

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
**Source**: See [designing-oci-vault-security](../designing-oci-vault-security/SKILL.md) skill for complete Vault patterns.

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

