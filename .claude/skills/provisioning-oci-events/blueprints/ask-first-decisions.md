### ⚠️ Ask First

**Decision Point**: Event Rule creation strategy — single rules vs. `for_each` map

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| Single resource blocks | Readability, explicit control | DRY principle | ≤3 rules with different conditions/actions |
| `for_each` with map variable | Scalability, maintainability | Debuggability, simplicity | >3 rules or multi-environment deployment |
| Module with dynamic blocks | Reusability across projects | Learning curve | Team-shared infrastructure, standardized patterns |

**Agent Behavior**:
"Before creating event rules, ask:
'How many event rules do you need? Are they sharing similar conditions/actions, or are they unique? Will this be reused across multiple environments or projects?'"

**Decision Factors**:
- Number of rules in the compartment (max 50)
- Whether rules share action types and targets
- Multi-environment deployment needs (dev/staging/prod)
- Team familiarity with Terraform `for_each` and dynamic blocks

**`for_each` example** (when chosen):
```hcl
# ⚠️ Use when >3 rules with varying event types but similar action structure
variable "event_rules" {
  type = map(object({
    display_name = string
    description  = string
    event_types  = list(string)
    action_type  = string
    target_id    = string
    is_enabled   = optional(bool, true)
  }))
}

resource "oci_events_rule" "rules" {
  for_each = var.event_rules

  compartment_id = var.compartment_ocid
  display_name   = "${each.value.display_name}-${var.environment}"
  description    = each.value.description
  is_enabled     = each.value.is_enabled

  condition = jsonencode({
    eventType = each.value.event_types
  })

  actions {
    actions {
      action_type = each.value.action_type
      is_enabled  = true
      function_id = each.value.action_type == "FAAS" ? each.value.target_id : null
      stream_id   = each.value.action_type == "OSS" ? each.value.target_id : null
      topic_id    = each.value.action_type == "ONS" ? each.value.target_id : null
      description = "Action for ${each.key}"
    }
  }

  freeform_tags = var.tags
}
```
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/events_rule

---

**Decision Point**: Staged rollout with `is_enabled = false` vs. immediate activation

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| Create enabled (`is_enabled = true`) | Immediate activation, simplicity | Safety on misconfigured conditions | Dev/staging environments |
| Create disabled + manual enable | Safety, condition validation | Deployment speed, automation | Production, first-time rule creation |
| Create disabled + lifecycle `ignore_changes` | Operational control post-creation | Terraform state consistency | Rules managed operationally after creation |

**Agent Behavior**:
"Before setting `is_enabled`, ask:
'Is this a production environment? Do you want to validate the condition before activating the rule? Events are fire-and-forget — lost events during misconfiguration cannot be reprocessed.'"

**Decision Factors**:
- Environment sensitivity (dev vs. prod)
- Event recoverability (fire-and-forget = no replay)
- Operational model (Terraform-managed vs. Console/CLI-managed)

**Staged rollout example** (when chosen):
```hcl
# ⚠️ Create disabled in prod for condition validation before activation
resource "oci_events_rule" "production_rule" {
  compartment_id = var.compartment_ocid
  display_name   = "rule-production-${var.project_name}-${var.environment}"
  description    = "Production event rule - staged deployment"

  # Disabled in prod, enabled in dev/staging
  is_enabled = var.environment == "prod" ? var.rule_enabled : true

  condition = jsonencode({
    eventType = var.event_types
    data = {
      compartmentId = [var.compartment_ocid]
    }
  })

  actions {
    actions {
      action_type = "FAAS"
      is_enabled  = true
      function_id = var.function_id
      description = "Process events"
    }
  }

  freeform_tags = var.tags

  lifecycle {
    # Operational control: enable/disable via Console/CLI after creation
    ignore_changes = [is_enabled]
  }
}
```
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/events_rule

---

**Decision Point**: Condition filtering granularity — eventType only vs. resource attributes

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| `eventType` only | Simplicity, broad capture | Precision, potential noise | Monitoring/audit of all events of a type |
| `eventType` + `data.additionalDetails` | Precision, reduced noise | Complexity, service-specific knowledge | Filtering by bucket, namespace, or resource attributes |
| `eventType` + `data.compartmentId` | Compartment isolation | Flexibility | Multi-tenant compartment with mixed workloads |

**Agent Behavior**:
"Before defining the condition, ask:
'Do you need to filter events by specific resource attributes (e.g., bucket name, namespace)? Or should the rule capture all events of this type in the compartment?'"

**Resource attribute filter example** (when chosen):
```hcl
# ⚠️ Filter by specific bucket — use when multiple buckets exist in compartment
condition = jsonencode({
  eventType = [
    "com.oraclecloud.objectstorage.createobject",
    "com.oraclecloud.objectstorage.deleteobject"
  ]
  data = {
    additionalDetails = {
      bucketName = [var.bucket_name]       # Values are ALWAYS arrays
      namespace  = [var.os_namespace]       # Even for single values
    }
  }
})
```
**Key Constraint**: Fields inside `data.additionalDetails` vary by service — consult the specific event documentation. Values are ALWAYS arrays (lists) even for a single value.
**Source**: https://docs.oracle.com/iaas/Content/Events/Concepts/filterevents.htm | https://docs.oracle.com/iaas/Content/Events/Reference/eventsproducers.htm

---

