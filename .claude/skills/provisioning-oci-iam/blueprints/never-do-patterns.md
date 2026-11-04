### 🚫 Never Do

**Anti-Pattern**: Dynamic Group with `ANY{}` without compartment constraint

```hcl
# 🚫 WRONG: Matches ALL Functions in the ENTIRE TENANCY (OCI Provider v6.x+)
# Any Function in any compartment receives these permissions
resource "oci_identity_dynamic_group" "functions" {
  compartment_id = var.tenancy_ocid
  name           = "dg-all-functions"
  matching_rule  = "ANY {resource.type = 'fnfunc'}"  # NO compartment constraint!
}

# ✅ CORRECT: Scope to specific compartment
resource "oci_identity_dynamic_group" "functions" {
  compartment_id = var.tenancy_ocid
  name           = "dg-functions-${var.project_name}-${var.environment}"
  matching_rule  = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"
}
```
**Why it is prohibited**: Cross-compartment privilege escalation. A compromised Function in any compartment inherits all permissions granted to this Dynamic Group.
**Actual impact**: Full tenancy-wide access for any resource of the matching type.
**Severity**: CRITICAL
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm

---

**Anti-Pattern**: `manage all-resources` for workload Dynamic Groups

```hcl
# 🚫 WRONG: Functions with manage all-resources = full admin (OCI Provider v6.x+)
resource "oci_identity_policy" "functions_admin" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-admin"
  statements = [
    "Allow dynamic-group dg-functions to manage all-resources in compartment ${var.compartment_name}",
  ]
}

# ✅ CORRECT: Granular permissions with minimum verb
resource "oci_identity_policy" "functions_services" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-services-${var.project_name}-${var.environment}"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read secret-bundles in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to manage objects in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use log-content in compartment ${var.compartment_name}",
  ]
}
```
**Why it is prohibited**: If the Function is compromised (code injection, supply-chain attack), the attacker has full CRUD on all resources in the compartment — can delete VCN, create users, exfiltrate all data.
**Actual impact**: Full compartment compromise from a single Function vulnerability.
**Severity**: CRITICAL
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policies.htm

---

**Anti-Pattern**: Hardcoded credentials in provider configuration

```hcl
# 🚫 WRONG: Credentials exposed in code, git history, and logs (OCI Provider v6.x+)
provider "oci" {
  tenancy_ocid = "ocid1.tenancy.oc1..aaa..."
  user_ocid    = "ocid1.user.oc1..bbb..."
  fingerprint  = "aa:bb:cc:dd:ee:ff"
  private_key  = "<PEM private key pasted here>"
  region       = "sa-saopaulo-1"
}

# ✅ CORRECT: Credentials via ~/.oci/config or env vars (development)
provider "oci" {
  region = var.region
}

# ✅ CORRECT: Instance Principal (OCI Compute/Containers)
provider "oci" {
  auth   = "InstancePrincipal"
  region = var.region
}

# ✅ CORRECT: Resource Principal (Resource Manager stacks)
provider "oci" {
  auth   = "ResourcePrincipal"
  region = var.region
}
```
**Why it is prohibited**: Credentials exposed in source code, git history, and CI/CD logs. Compromises the entire OCI tenancy.
**Actual impact**: Full tenancy compromise — attacker gains complete control of all OCI resources.
**Severity**: CRITICAL
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs#authentication

---

**Anti-Pattern**: Policy referencing compartment by OCID in statements instead of name

```hcl
# 🚫 WRONG: OCIDs in policy statements are error-prone and unreadable (OCI Provider v6.x+)
resource "oci_identity_policy" "bad_policy" {
  compartment_id = var.tenancy_ocid
  name           = "policy-bad-reference"
  statements = [
    "Allow dynamic-group dg-functions to read secret-bundles in compartment id ocid1.compartment.oc1..aaaaaa",
  ]
}

# ✅ CORRECT: Use compartment name (human-readable, auditable)
resource "oci_identity_policy" "good_policy" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-services-${var.project_name}-${var.environment}"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read secret-bundles in compartment ${var.compartment_name}",
  ]
}
```
**Why it is prohibited**: Policy statements with OCIDs are unreadable in audit logs and error-prone. Oracle recommends `compartment <name>` for legibility and auditability.
**Actual impact**: Audit readability degradation, maintenance burden, error-prone copy-paste.
**Severity**: MEDIUM
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policysyntax.htm

---

**Anti-Pattern**: Policy name with special characters or duplicate names

```hcl
# 🚫 WRONG: Spaces, special chars, or duplicate names (OCI Provider v6.x+)
resource "oci_identity_policy" "bad" {
  name = "My Policy (prod) #1"  # Invalid characters!
}

resource "oci_identity_policy" "duplicate" {
  name = "policy-functions"  # Collides if already exists in tenancy!
}

# ✅ CORRECT: Descriptive, unique, no special chars — include project + env
resource "oci_identity_policy" "functions_services" {
  name = "policy-functions-services-${var.project_name}-${var.environment}"
  # Result: "policy-functions-services-myapp-prod"
}
```
**Why it is prohibited**: Policy names must be unique across the ENTIRE tenancy (not just per-compartment). Invalid characters cause creation failure. Duplicate names cause Terraform apply errors.
**Actual impact**: Terraform apply failure, name collision across teams.
**Severity**: HIGH
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_policy

---

**Anti-Pattern**: Missing `depends_on` for IAM → downstream resources

```hcl
# 🚫 WRONG: Race condition — Function may deploy before policy propagates (OCI Provider v6.x+)
module "app_my_function" {
  source    = "../../modules/function-app"
  subnet_id = module.network.subnet_private_id
  # No depends_on = [module.iam] — policy may not be active yet
}

# ✅ CORRECT: Explicit dependency ensures policy propagation
module "app_my_function" {
  source    = "../../modules/function-app"
  subnet_id = module.network.subnet_private_id
  depends_on = [module.iam]  # Waits for IAM policy propagation (~60s)
}
```
**Why it is prohibited**: IAM policies take up to 60 seconds to propagate. Without `depends_on`, Terraform creates resources in parallel — Functions and API Gateway deploy before authorization is active.
**Actual impact**: Intermittent deployment failures, 502 Bad Gateway, "permission denied" errors that self-resolve on retry (flaky CI/CD).
**Severity**: HIGH
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm

---

**Anti-Pattern**: Renaming a Dynamic Group (forces destroy/recreate)

```hcl
# 🚫 WRONG: Changing name destroys and recreates the Dynamic Group (OCI Provider v6.x+)
# All policies referencing the old name by name BREAK during transition
resource "oci_identity_dynamic_group" "functions" {
  name = "dg-new-name"  # Changed from "dg-old-name" — DESTROY/RECREATE
}

# ✅ CORRECT: Plan name carefully using consistent naming convention
# Once created, never change the name
resource "oci_identity_dynamic_group" "functions" {
  name = "dg-functions-${var.project_name}-${var.environment}"
  # This name is permanent. Changes force destroy/recreate.
}
```
**Why it is prohibited**: Dynamic Group `name` is immutable in the OCI API. Terraform will destroy and recreate the resource. All policies referencing the old name by name break during the transition window.
**Actual impact**: Temporary authorization failures for all resources in the Dynamic Group during recreate.
**Severity**: HIGH
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_dynamic_group
