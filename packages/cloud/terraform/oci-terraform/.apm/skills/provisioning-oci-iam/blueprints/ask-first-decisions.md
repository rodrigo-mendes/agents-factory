### ⚠️ Ask First

**Decision Point**: Compartment-Scoped vs. Tenancy-Scoped Policies

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| **Compartment-scoped** | Blast radius isolation, least-privilege | Complexity (more policy resources), cross-compartment requires explicit grants | Multi-team tenancy, production workloads |
| **Tenancy-scoped** | Simplicity, cross-compartment access out of the box | Security (overly broad permissions), large blast radius | Admin operations, platform services, single-team tenancy |

**Agent Behavior**:
"Before implementing policies, ask the user:
'Is this a multi-team tenancy? Do policies need to access resources across multiple compartments, or are all resources in a single compartment?'"

**Decision Factors**:
- Number of teams sharing the tenancy
- Whether resources span multiple compartments
- Compliance requirements (SOC2, PCI-DSS often mandate compartment isolation)

**Rule**: Service policies (`Allow service FaaS`) ALWAYS go to tenancy-level. Dynamic Group workload policies go to compartment-level when possible.

**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policies.htm

---

**Decision Point**: Single Dynamic Group vs. Multiple Granular Dynamic Groups

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| **Single DG per resource type** | Simplicity, fewer tenancy-level resources | Isolation if compartment has multiple projects | 1 project per compartment |
| **Multiple DGs per project+env** | Isolation between projects in shared compartment | Name management (unique per-tenancy), resource count | Multiple projects in same compartment |
| **Tag-based matching rules** | Fine-grained governance in multi-project compartments | Complexity (requires Defined Tags), setup overhead | Enterprise governance requirements |

**Agent Behavior**:
"Before creating Dynamic Groups, ask the user:
'Are there multiple projects in the same compartment that need isolated permissions? Or is it one project per compartment?'"

**Decision Factors**:
- Number of projects per compartment
- Whether teams share compartments
- Governance maturity (Defined Tags available?)

**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm

---

**Decision Point**: Matching Rule Operators — ALL vs. ANY

**Available Options**:
| Option | Semantics | Choose When |
|--------|-----------|-------------|
| **ALL {conditions}** | AND logic — resource must satisfy ALL conditions | Precise scoping (type + compartment) — **RECOMMENDED** |
| **ANY {conditions}** | OR logic — resource satisfies ANY condition | Multiple types in same group (evaluate carefully!) |
| **Combined** `ANY {ALL{...}, ALL{...}}` | Multiple independent AND sets | Multiple independent criteria |

```hcl
# ALL: Functions in specific compartment (RECOMMENDED — OCI Provider v6.x+)
matching_rule = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"

# ANY: Functions OR API Gateway (CAUTION — evaluate blast radius)
matching_rule = "ANY {resource.type = 'fnfunc', resource.type = 'ApiGateway'}"

# Combined: Functions in compartment A OR compartment B
matching_rule = "ANY {ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.comp_a_ocid}'}, ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.comp_b_ocid}'}}"
```

**Agent Behavior**:
"Before using ANY{} in matching rules, ask the user:
'Do you need resources of multiple types in the same Dynamic Group, or should they be separated for isolation? ANY{} broadens the blast radius.'"

**Decision Factors**:
- Whether different resource types need the same permissions
- Blast radius tolerance
- Number of Dynamic Groups vs. tenancy limits (200 default)

**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm

---

**Decision Point**: Policy Verb — Specific Resource Types vs. Family

**Available Options**:
| Option | Scope | Risk | Choose When |
|--------|-------|------|-------------|
| **Specific** (`use fn-invocation`) | Minimum necessary | More policies, more maintenance | Production, compliance-driven environments |
| **Family** (`use functions-family`) | All resources in service family | Over-permission if not all are needed | Development, rapid prototyping |
| **All** (`manage all-resources`) | Everything in compartment | **NEVER for workloads** | Compartment-admin groups only |

```hcl
# SPECIFIC (recommended for workloads — OCI Provider v6.x+)
"Allow dynamic-group dg-apigw to use fn-invocation in compartment myapp"

# FAMILY (acceptable when multiple operations needed)
"Allow dynamic-group dg-functions to use object-family in compartment myapp"

# ALL-RESOURCES (admin groups only — NEVER for Dynamic Groups)
"Allow group administrators to manage all-resources in compartment myapp"
```

**Agent Behavior**:
"Before writing policy statements, ask the user:
'Does the Function need only specific operations (e.g., read secrets, write objects) or full family access? What is the minimum set of operations required?'"

**Decision Factors**:
- Number of distinct operations needed per service
- Environment (dev allows broader; prod demands granular)
- Compliance posture

**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/policyreference.htm

---

**Decision Point**: Policy Conditions (where clauses)

**Available Options**:
| Option | Controls | Choose When |
|--------|----------|-------------|
| **No conditions** | Unconditional access | Simple environments, single-project compartments |
| **Network Source** | IP/VCN restriction | Console access from corporate network only |
| **Tag-based (ABAC)** | Attribute-based access control | Multi-tenant, fine-grained per-resource |
| **Request variables** | Request-time context | Target-specific restrictions (specific function, operation) |

```hcl
# Condition: Network Source (restrict to corporate VPN — OCI Provider v6.x+)
"Allow group developers to manage all-resources in compartment dev where request.networkSource.name='corporate-vpn'"

# Condition: Tag-based access control
"Allow dynamic-group dg-functions to read objects in compartment shared where target.resource.tag.project.name='myapp'"

# Condition: Request variable (specific Function only)
"Allow dynamic-group dg-apigw to use fn-invocation in compartment myapp where target.function.id = '${function_ocid}'"
```

**Agent Behavior**:
"Before adding policy conditions, ask the user:
'Do you need to restrict access beyond compartment scoping? For example: IP-based restrictions, tag-based filtering, or target-specific constraints?'"

**Decision Factors**:
- Whether compartment-level scoping is sufficient
- Multi-tenancy or shared compartment requirements
- Compliance requirements (network restrictions, ABAC)

**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policyadvancedfeatures.htm
