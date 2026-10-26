---
name: provisioning-oci-iam
description: Provisions IAM resources (Dynamic Groups, Policies, Compartments) with Terraform OCI Provider v6.x+. Use when setting up identity and access management for serverless workloads.
---

## Version Context

**Technology**: Terraform OCI Provider — IAM (`oci_identity_dynamic_group`, `oci_identity_policy`, `oci_identity_compartment`)
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Terraform Version**: >= 1.7
**Provider Version**: oracle/oci >= 6.0, < 9.0
**Provider Registry**: https://registry.terraform.io/providers/oracle/oci/latest/docs
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
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Cross-service integration examples with HCL
- **[Module Architecture](./blueprints/module-architecture.md)** — Module layout, composition, state isolation, agent confidence tiers
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge case, and misuse test cases
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
  | jq '.data[] | select(.name | startswith("dg-")) | {name, "matching-rule"}'

# Verify Policies
oci iam policy list --compartment-id $COMPARTMENT_OCID --all \
  | jq '.data[] | select(.name | startswith("policy-")) | {name, statements}'

# Test Function invocation (validates API Gateway → Functions policy)
curl -s "https://<gateway-hostname>/v1/health" | jq .
# Expected: {"status":"healthy"}
```

### 5. Security Audit
```bash
# Check for overly permissive policies
oci iam policy list --compartment-id $TENANCY_OCID --all \
  | jq '.data[].statements[]' | grep -i "manage all-resources"
  # Expected: no output (exit 1)

# Check Dynamic Groups for broad matching rules
oci iam dynamic-group list --compartment-id $TENANCY_OCID --all \
  | jq '.data[] | select(."matching-rule" | test("ANY")) | .name'
  # Expected: no output (exit 1)
```

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
- [OCI IAM Documentation](https://docs.oracle.com/en-us/iaas/Content/Identity/home.htm) (verified 2026-07-26)
- [OCI Policy Reference — All Verbs and Resource Types](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/policyreference.htm) (verified 2026-07-26)
- [OCI Common Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm) (verified 2026-07-26)
- [Dynamic Groups — Managing and Matching Rules](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm) (verified 2026-07-26)
- [Policy Advanced Features — Conditions](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policyadvancedfeatures.htm) (verified 2026-07-26)
- [Policy Syntax Reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policysyntax.htm) (verified 2026-07-26)

### Terraform Provider
- [OCI Provider Registry](https://registry.terraform.io/providers/oracle/oci/latest/docs) (verified 2026-07-26)
- [oci_identity_dynamic_group Resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_dynamic_group) (verified 2026-07-26)
- [oci_identity_policy Resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_policy) (verified 2026-07-26)
- [oci_identity_compartment Resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_compartment) (verified 2026-07-26)
- [OCI Provider Authentication](https://registry.terraform.io/providers/oracle/oci/latest/docs#authentication) (verified 2026-07-26)

### Data Sources
- [oci_identity_dynamic_groups](https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/identity_dynamic_groups) (verified 2026-07-26)
- [oci_identity_policies](https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/identity_policies) (verified 2026-07-26)
- [oci_identity_compartments](https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/identity_compartments) (verified 2026-07-26)

### Service-Specific IAM Guides
- [Functions Required Policies](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingpolicies.htm) (verified 2026-07-26)
- [API Gateway Required Policies](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatingpolicies.htm) (verified 2026-07-26)
- [Object Storage Policy Reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/objectstoragepolicyreference.htm) (verified 2026-07-26)
- [Vault/KMS IAM Overview](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm) (verified 2026-07-26)
- [Logging IAM](https://docs.oracle.com/en-us/iaas/Content/Logging/Task/managinglogs.htm) (verified 2026-07-26)

### Examples & Source Code
- [OCI Identity Terraform Examples](https://github.com/oracle/terraform-provider-oci/tree/master/examples/identity) (verified 2026-07-26)
- [OCI Provider GitHub](https://github.com/oracle/terraform-provider-oci) (verified 2026-07-26)
