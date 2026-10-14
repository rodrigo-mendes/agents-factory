---
name: provisioning-oci-iam
description: Provisions IAM resources (Dynamic Groups, Policies, Compartments) with Terraform OCI Provider v6.x+ following OCI Best Practices 2024. Use when setting up identity and access management for serverless workloads.
---

## Version Context

**Technology**: Terraform OCI Provider — IAM (`oci_identity_dynamic_group`, `oci_identity_policy`, `oci_identity_compartment`)
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Terraform Version**: >= 1.7
**Provider Version**: oracle/oci >= 6.0, < 9.0
**Provider Registry**: https://registry.terraform.io/providers/oracle/oci/latest/docs
**Release Date**: 2024–2026 (continuous releases)
**Support Status**: Active

**Key Constraints**:
- Dynamic Groups and Policies are **tenancy-level** resources — `compartment_id = tenancy_ocid`
- Policy names are **unique per-tenancy** and **immutable** (rename = destroy/recreate)
- IAM policy propagation takes **up to 60 seconds** — `depends_on` is mandatory for downstream resources
- OCI policies are **additive only** — there is no explicit deny
- Compartment delete is **async** and takes up to **90 minutes**
- Policy statements maximum: **50 per policy**, **50 policies per compartment**

**Deprecations**:
- None in OCI Provider v6.x+ for core IAM resources

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform OCI Provider v6.x+. Do NOT mix syntax from older provider versions. Validate all resource type names are case-correct (`fnfunc`, `ApiGateway`).

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
- **Provider Version Constraint** — Pin `>= 6.0, < 9.0` for IAM stability
- **Compartment-Scoped Dynamic Groups** — MUST use `ALL {}` with `resource.compartment.id`. Without scoping = tenancy-wide privilege escalation
- **Least-Privilege Policies** — Use minimum verb: `inspect` < `read` < `use` < `manage`. Never `manage all-resources` for workloads
- **Service Policies at Tenancy-Level** — `Allow service FaaS` goes to `tenancy_ocid`, not compartment. Case-sensitive: `FaaS`, `ApiGateway`
- **Compartment Hierarchy** — Set `enable_delete = true`. Delete takes up to 90 min (async)
- **Variable Validation for OCIDs** — Validate `ocid1.tenancy.*` and `ocid1.compartment.*` at plan-time
- **Explicit `depends_on`** — IAM propagation takes up to 60s. Downstream modules must wait
- **Tags on All IAM Resources** — Tenancy-level resources proliferate. Tags ensure traceability
- **Outputs for Inter-Module Dependencies** — Dynamic Group names/OCIDs for downstream modules

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Compartment-Scoped vs. Tenancy-Scoped Policies** — Service policies always tenancy-level. Workload policies compartment-level when possible
- **Single vs. Multiple Dynamic Groups** — 1 project/compartment = single DG. Shared compartment = multiple DGs or tag-based
- **Matching Rule Operators (ALL vs. ANY)** — ALL recommended (AND logic). ANY broadens blast radius
- **Policy Verb (Specific vs. Family)** — `fn-invocation` (specific) vs. `functions-family` (broad). Production = specific
- **Policy Conditions (where clauses)** — Network source, tag-based ABAC, request variables for fine-grained control

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Dynamic Group without compartment constraint** — `ANY {resource.type = 'fnfunc'}` matches ALL Functions tenancy-wide. CRITICAL
- **`manage all-resources` for workloads** — Compromised Function = full compartment control. CRITICAL
- **Hardcoded credentials in provider** — Source code, git history, CI/CD logs exposure. CRITICAL
- **Compartment OCID in policy statements** — Use names for readability/auditability
- **Special characters or duplicate policy names** — Names unique per-tenancy, not per-compartment
- **Missing `depends_on` for IAM → downstream** — IAM propagation takes up to 60s. Causes flaky CI/CD
- **Renaming Dynamic Groups** — `name` is immutable. Change = destroy/recreate = auth failure window

---

## Integration Patterns

For complete integration patterns with code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Available integrations**:
- **IAM ↔ OCI Functions** — Dynamic Group (`fnfunc` lowercase) + Resource Principal. `depends_on` required for policy propagation
- **IAM ↔ OCI API Gateway** — Dynamic Group (`ApiGateway` PascalCase) + `fn-invocation` policy
- **IAM ↔ OCI Vault** — `read secret-bundles` (not `read secrets`) for actual secret content
- **IAM ↔ Object Storage** — `manage objects` ≠ `manage buckets` (separate permissions)
- **IAM ↔ Networking** — SERVICE policy (`Allow service FaaS`) at tenancy-level only
- **IAM ↔ Logging** — `use log-content` for writing; `read log-content` for reading only

---

## Module Architecture

### IAM Module Layout
```
modules/iam/
├── main.tf          # Dynamic Groups + Policies
├── variables.tf     # Input variables (tenancy_ocid, compartment_ocid, etc.)
└── outputs.tf       # Dynamic Group IDs and names for downstream modules
```

### Extended IAM Module (Production)
```
modules/iam/
├── main.tf              # Core Dynamic Groups + Policies
├── compartments.tf      # Compartment hierarchy (optional)
├── network_sources.tf   # Network Sources for policy conditions
├── tags.tf              # Tag Namespaces and Defined Tags
├── variables.tf         # Input variables
├── outputs.tf           # Outputs for downstream modules
└── README.md            # Documentation
```

### Module Composition in Root
```hcl
# Root main.tf — IAM precedes all workload modules (OCI Provider v6.x+)
module "iam" {
  source           = "./modules/iam"
  tenancy_ocid     = var.tenancy_ocid
  compartment_ocid = var.compartment_ocid
  compartment_name = var.compartment_name
  environment      = var.environment
  project_name     = var.project_name
  tags             = local.tags
}

module "network" {
  source           = "./modules/network"
  compartment_ocid = var.compartment_ocid
}

module "app_api_handler" {
  source    = "./modules/function-app"
  subnet_id = module.network.subnet_private_id
  depends_on = [module.iam]  # CRITICAL: wait for policy propagation
}

module "api_gateway" {
  source      = "./modules/api-gateway"
  function_id = module.functions.function_id
  depends_on  = [module.iam]  # CRITICAL: fn-invocation policy needed
}
```

---

## State Management

### IAM State Isolation Strategy
```
terraform-state-bucket/
├── iam/shared/terraform.tfstate        # Shared IAM (tenancy-level policies)
├── serverless/dev/terraform.tfstate     # Dev workload
├── serverless/staging/terraform.tfstate
└── serverless/prod/terraform.tfstate
```
**Key decision**: Tenancy-level IAM (service policies, admin groups) should be in a SEPARATE state file from workload resources. This prevents accidental destroy of platform IAM during workload teardown.

### Lifecycle Rules for IAM Resources
```hcl
# Prevent accidental deletion of production IAM (OCI Provider v6.x+)
resource "oci_identity_policy" "critical" {
  # ...
  lifecycle {
    prevent_destroy = true
  }
}

resource "oci_identity_compartment" "prod" {
  # ...
  enable_delete = false  # Extra safety for production compartment
  lifecycle {
    prevent_destroy = true
  }
}
```

### Import Strategy for Existing IAM Resources
```bash
# Import existing compartment
terraform import oci_identity_compartment.project <compartment-ocid>

# Import existing dynamic group
terraform import oci_identity_dynamic_group.functions <dynamic-group-ocid>

# Import existing policy
terraform import oci_identity_policy.faas_network <policy-ocid>

# Post-import: verify state matches config
terraform plan
```

---

## Verification Loop

The agent MUST execute after each IAM code generation:

### 1. Validate Configuration
```bash
cd terraform/oci-serverless
terraform init -upgrade
# Exit code: 0 (success) | 1 (error)
terraform validate
# Exit code: 0 (valid) | 1 (invalid configuration)
```
**Expected output**: `Success! The configuration is valid.`
**Exit code**: 0

### 2. Format Check
```bash
terraform fmt -recursive -check=true
# Exit code: 0 (formatted) | 3 (needs formatting)
```
**Expected output**: (no output — clean exit)
**Exit code**: 0

### 3. Plan IAM Resources
```bash
terraform plan -var-file="terraform.tfvars" -target=module.iam
# Exit code: 0 (no changes) | 1 (error) | 2 (changes pending)
```
**Expected output**: Shows creation of `oci_identity_dynamic_group` and `oci_identity_policy` resources.
**Exit code**: 0

### 4. Post-Apply Verification
```bash
# Verify Dynamic Groups
oci iam dynamic-group list --compartment-id $TENANCY_OCID --all \
# Exit code: 0 (success) | 1 (auth/network error)
  | jq '.data[] | select(.name | startswith("dg-")) | {name, "matching-rule"}'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)

# Verify Policies
oci iam policy list --compartment-id $COMPARTMENT_OCID --all \
# Exit code: 0 (success) | 1 (auth/network error)
  | jq '.data[] | select(.name | startswith("policy-")) | {name, statements}'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)

# Test Function invocation (validates API Gateway → Functions policy)
curl -s "https://<gateway-hostname>/v1/health" | jq .
# Exit code: 0 (success) | 1 (connection error) | 22 (HTTP error with -f)
# Expected: {"status":"healthy"}
```

### 5. Security Audit
```bash
# Check for overly permissive policies
oci iam policy list --compartment-id $TENANCY_OCID --all \
# Exit code: 0 (success) | 1 (auth/network error)
  | jq '.data[].statements[]' | grep -i "manage all-resources"
  # Exit code: 0 (match found) | 1 (no match)

# Check Dynamic Groups for broad matching rules
oci iam dynamic-group list --compartment-id $TENANCY_OCID --all \
# Exit code: 0 (success) | 1 (auth/network error)
  | jq '.data[] | select(."matching-rule" | test("ANY")) | .name'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
```
**Expected output**: Both commands should return empty results (no overly permissive patterns).

**Troubleshooting**:
- `Error: compartment_id is required` → Ensure `tenancy_ocid` is set for Dynamic Groups, `compartment_ocid` for workload policies
- `Error: Policy name already exists` → Policy names are unique per-tenancy; add project/environment suffix
- `Error 404 — Dynamic group not found` → IAM propagation delay; wait 60s and retry
- `502 Bad Gateway from API Gateway` → Missing `fn-invocation` policy or propagation delay

---

## Quick Reference

### OCI Policy Verb Hierarchy
| Verb | Permissions | Use Case |
|------|------------|----------|
| `inspect` | List resources, get metadata only | Monitoring, inventory |
| `read` | inspect + get resource content | Reading secrets, objects, configs |
| `use` | read + act on existing resources | Invoke functions, write logs, use VCN |
| `manage` | use + create/delete resources | Admin operations, full CRUD |

### Common Resource Types (Serverless)
| Resource Type | Service | Typical Verb |
|---------------|---------|-------------|
| `fn-invocation` | Functions | `use` |
| `fn-app` | Functions | `read` |
| `fn-function` | Functions | `read` |
| `secret-bundles` | Vault | `read` |
| `keys` | Vault/KMS | `use` |
| `objects` | Object Storage | `manage` |
| `buckets` | Object Storage | `read` |
| `log-content` | Logging | `use` |
| `stream-push` | Streaming | `use` |
| `virtual-network-family` | VCN | `use` |
| `repos` | OCIR | `read` |

### Resource Type Case-Sensitivity
| Resource Type | Correct Case | Wrong |
|---------------|-------------|-------|
| Functions | `fnfunc` | `FnFunc`, `FNFUNC` |
| API Gateway | `ApiGateway` | `apigateway`, `API_GATEWAY` |
| Compute | `instance` | `Instance` |

### IAM Resource Limits
| Resource | Limit per Tenancy | Notes |
|----------|-------------------|-------|
| Compartments | 100 (default) | Requestable increase |
| Dynamic Groups | 200 (default) | Requestable increase |
| Policies per Compartment | 50 | Hard limit per compartment |
| Statements per Policy | 50 | Combine related statements |
| Policy Name Length | 100 chars | Must be unique in tenancy |
| Compartment Nesting | 6 levels | Maximum depth |

### Policy Propagation Timing
| Operation | Propagation Time |
|-----------|-----------------|
| Create policy | ~10s (up to 60s) |
| Update statements | 10–60s |
| Delete policy | 10–60s |

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Creating Dynamic Groups with compartment-scoped matching rules
- Creating least-privilege policies for Functions/API Gateway
- Adding service policies (FaaS, API Gateway) at tenancy level
- Variable validation for OCIDs
- Adding freeform_tags to all IAM resources
- Setting depends_on for downstream modules
- Terraform validate and fmt

### Medium Confidence (Validate with user)
- Compartment hierarchy structure
- Policy verb choice (use vs. manage for specific operations)
- Multiple Dynamic Groups vs. single broad DG
- Cross-compartment policy requirements
- Tag-based access control strategy

### Low Confidence (Must ask user)
- Identity Domain configuration and federation
- MFA enforcement policies
- Network Source restrictions
- Cross-tenancy access patterns
- Compliance-specific requirements (SOC2, HIPAA, PCI-DSS)

### Emergency Stop
- **HALT** if `manage all-resources in tenancy` found in workload policies
- **HALT** if Dynamic Group uses `ANY{}` without compartment constraint
- **HALT** if credentials found in provider configuration
- **HALT** if policy names have no environment/project qualifier (collision risk)
- **HALT** if `enable_delete = true` on production compartments without `prevent_destroy` lifecycle

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
- [ ] Verify IAM policy propagation (wait 60s, test with OCI CLI)
- [ ] Confirm dynamic group matching rules target correct resource types
- [ ] Commit state and tag release
```

## External Resources

### Official Documentation
- [OCI IAM Documentation](https://docs.oracle.com/en-us/iaas/Content/Identity/home.htm)
- [OCI Policy Reference — All Verbs and Resource Types](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/policyreference.htm)
- [OCI Common Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm)
- [Dynamic Groups — Managing and Matching Rules](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm)
- [Policy Advanced Features — Conditions](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policyadvancedfeatures.htm)
- [Policy Syntax Reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policysyntax.htm)

### Terraform Provider
- [OCI Provider Registry](https://registry.terraform.io/providers/oracle/oci/latest/docs)
- [oci_identity_dynamic_group Resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_dynamic_group)
- [oci_identity_policy Resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_policy)
- [oci_identity_compartment Resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_compartment)
- [OCI Provider Authentication](https://registry.terraform.io/providers/oracle/oci/latest/docs#authentication)

### Data Sources
- [oci_identity_dynamic_groups](https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/identity_dynamic_groups) — List dynamic groups
- [oci_identity_policies](https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/identity_policies) — List policies
- [oci_identity_compartments](https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/identity_compartments) — List compartments

### Service-Specific IAM Guides
- [Functions Required Policies](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingpolicies.htm)
- [API Gateway Required Policies](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatingpolicies.htm)
- [Object Storage Policy Reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/objectstoragepolicyreference.htm)
- [Vault/KMS IAM Overview](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm)
- [Logging IAM](https://docs.oracle.com/en-us/iaas/Content/Logging/Task/managinglogs.htm)

### Examples & Source Code
- [OCI Identity Terraform Examples](https://github.com/oracle/terraform-provider-oci/tree/master/examples/identity)
- [OCI Provider GitHub](https://github.com/oracle/terraform-provider-oci)
