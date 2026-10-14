---
name: provisioning-oci-events
description: Provisions and manages OCI Events Rules (event-driven automation) with Terraform OCI Provider v6.x+. Use when provisioning event-driven infrastructure for serverless architectures.
---

## Version Context

**Technology**: Terraform OCI Provider — Events Service (`oci_events_rule`)
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Terraform Version**: >= 1.7
**Provider Version**: oracle/oci >= 6.0, < 9.0
**Provider Registry**: https://registry.terraform.io/providers/oracle/oci/latest/docs
**Release Date**: 2024–2026 (continuous releases)
**Support Status**: Active

**Key Constraints**:
- Event Rules are **compartment-scoped with inheritance** — a rule captures events from its compartment AND all child compartments
- `condition` is a JSON string that MUST contain `eventType` — an empty condition `{}` captures ALL events (dangerous in production)
- Maximum **50 rules per compartment** and **10 actions per rule** (service limits)
- Events are **fire-and-forget** — no replay or reprocessing capability; lost events are unrecoverable
- IAM policy for `cloudevents` service principal must propagate (up to 60s) before rules can invoke Functions
- Three action types: `FAAS` (Function), `OSS` (Stream), `ONS` (Notification Topic)

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform OCI Provider v6.x+. Do NOT mix syntax from older provider versions. Always use `jsonencode()` for the `condition` field — never raw JSON strings. The service principal is `cloudevents` (not "events" or "Events").

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
- **Provider Version Constraint** — Lock OCI provider. Events integrate with Functions, Streaming, Notifications
- **Specific Condition with `jsonencode()`** — Empty condition captures ALL events → exponential costs and Function concurrency exhaustion
- **Type-Safe Action Targets via Terraform References** — Never hardcode OCIDs. Use resource references for dependency graph
- **Compartment-Scoped Rules** — Rules inherit hierarchically. Root compartment rules capture ALL tenancy events
- **Tags and Description** — Required for auditability and cost tracking

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Single Rules vs `for_each` Map** — Single for few event types; `for_each` for multiple similar rules
- **Staged Rollout (`is_enabled = false`) vs Immediate** — Staged for production; immediate for dev/test
- **Action Type Selection** — Functions (processing), Streaming (audit/retention), Notifications (alerting)

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Empty condition in production** — Captures ALL events. Function concurrency exhaustion, exponential cost, unrecoverable data loss
- **Hardcoded OCIDs in action targets** — Breaks portability, prevents clean destroy/recreate, bypasses dependency graph
- **Event Rule in root compartment** — Captures events from ALL compartments. Violates least-privilege
- **Multiple actions without idempotent consumers** — Events delivered at-least-once. Non-idempotent consumers cause duplicate processing

---

## Integration Patterns

For complete integration code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Summary of integrations**:
- **Events ↔ OCI Functions** — Serverless processing pipeline with IAM policies and event schema
- **Events ↔ OCI Streaming** — Audit trail and event retention with partitioning
- **Events ↔ Functions Lifecycle** — Observability: function create/update/delete events for monitoring
## Module Architecture

**Recommended module structure** for reusable Events provisioning:
```
modules/events/
├── main.tf          # oci_events_rule resources with dynamic blocks
├── variables.tf     # Input variables with validation
└── outputs.tf       # Rule IDs and state outputs
```

**Module main.tf** (complete, copy-paste ready):
```hcl
resource "oci_events_rule" "rules" {
  for_each = var.event_rules

  compartment_id = var.compartment_ocid
  display_name   = "${each.value.display_name}-${var.environment}"
  description    = each.value.description
  is_enabled     = each.value.is_enabled

  condition = jsonencode(each.value.condition)

  actions {
    dynamic "actions" {
      for_each = each.value.actions
      content {
        action_type = actions.value.action_type
        is_enabled  = actions.value.is_enabled
        description = actions.value.description
        function_id = actions.value.action_type == "FAAS" ? actions.value.target_id : null
        stream_id   = actions.value.action_type == "OSS" ? actions.value.target_id : null
        topic_id    = actions.value.action_type == "ONS" ? actions.value.target_id : null
      }
    }
  }

  defined_tags  = var.defined_tags
  freeform_tags = merge(var.tags, { "ManagedBy" = "terraform" })
}
```

**Module variables.tf** (with validation guards):
```hcl
variable "compartment_ocid" {
  description = "OCID of the compartment where event rules will be created"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "event_rules" {
  description = "Map of event rules to create"
  type = map(object({
    display_name = string
    description  = string
    is_enabled   = optional(bool, true)
    condition = object({
      eventType = list(string)
      data      = optional(map(any), null)
    })
    actions = list(object({
      action_type = string
      is_enabled  = optional(bool, true)
      target_id   = string
      description = optional(string, "")
    }))
  }))

  validation {
    condition = alltrue([
      for rule in var.event_rules : alltrue([
        for action in rule.actions : contains(["FAAS", "OSS", "ONS"], action.action_type)
      ])
    ])
    error_message = "action_type must be one of: FAAS, OSS, ONS."
  }

  validation {
    condition = alltrue([
      for rule in var.event_rules : length(rule.actions) <= 10
    ])
    error_message = "Maximum 10 actions per rule (OCI service limit)."
  }

  validation {
    condition = alltrue([
      for rule in var.event_rules : length(rule.condition.eventType) > 0
    ])
    error_message = "condition.eventType must have at least one event type (never use empty condition)."
  }
}

variable "tags" {
  description = "Freeform tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "defined_tags" {
  description = "Defined tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

**Module outputs.tf**:
```hcl
output "rule_ids" {
  description = "Map of rule key to rule OCID"
  value       = { for k, v in oci_events_rule.rules : k => v.id }
}

output "rule_states" {
  description = "Map of rule key to lifecycle state"
  value       = { for k, v in oci_events_rule.rules : k => v.state }
}

output "rules" {
  description = "Full map of created rules"
  value       = oci_events_rule.rules
}
```

---

## Verification Loop

The agent MUST execute after each event rule code generation:

### 1. Terraform Validate
```bash
terraform validate
# Exit code: 0 (valid) | 1 (invalid configuration)
```
**Expected output**: `Success! The configuration is valid.`
**Exit code**: 0

### 2. Terraform Plan
```bash
terraform plan -target='module.events'
# Exit code: 0 (no changes) | 1 (error) | 2 (changes pending)
```
**Expected output**: Plan showing resources to add/change/destroy with no errors
**Exit code**: 0

### 3. Verify Event Rules Post-Apply
```bash
# List active rules in compartment
oci events rule list \
# Exit code: 0 (success) | 1 (auth/network error)
  --compartment-id $COMPARTMENT_OCID \
  --lifecycle-state ACTIVE \
  --output table
```
**Expected output**: Table listing created rules with ACTIVE state

### 4. Validate Rule Condition
```bash
# Parse and verify condition JSON
oci events rule get \
# Exit code: 0 (success) | 1 (auth/network error)
  --rule-id $RULE_OCID \
  --output json | jq '.data.condition | fromjson'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
```
**Expected output**: Valid JSON with `eventType` array

### 5. Test Event Delivery
```bash
# Trigger a test event (e.g., create object in monitored bucket)
oci os object put \
# Exit code: 0 (success) | 1 (auth/network error)
  --bucket-name $TEST_BUCKET \
  --name "test-event-$(date +%s).txt" \
  --file /dev/stdin <<< "test content"

# Verify rule matched the event
oci monitoring metric-data summarize-metrics-data \
  --compartment-id $COMPARTMENT_OCID \
  --namespace oci_events \
  --query-text "EventsMatched[1m].count()" \
  --output table
```
**Expected output**: Non-zero event count matching the triggered event

### 6. Terraform State Verification
```bash
# Confirm state consistency
terraform state list | grep "oci_events_rule"
# Exit code: 0 (success) | 1 (error)
terraform plan -target='module.events' -detailed-exitcode
# Exit code: 0 (no changes) | 1 (error) | 2 (changes pending)
```
**Expected output**: Exit code 0 (no changes) confirming state matches infrastructure

**Troubleshooting**:
- **Rule ACTIVE but events not triggering actions**: Check IAM policy for `cloudevents` service principal — invocations fail silently without it
- **Plan shows condition changes but content is same**: Use `jsonencode()` consistently — provider normalizes JSON key ordering
- **Action state is FAILED**: Verify target resource OCID exists and is ACTIVE via `oci events rule get --rule-id $RULE_OCID`
- **Destroy fails**: Rule may be in CREATING/UPDATING state — wait and retry (20-minute timeout)
- **Permission denied on create/update**: Add policy `Allow group <group> to manage cloudevents-rules in compartment <name>`

---

## Quick Reference

**Service Limits**:
| Limit | Value | Scope |
|-------|-------|-------|
| Rules per compartment | 50 | Compartment |
| Actions per rule | 10 | Per rule |
| Condition JSON size | 4 KB | Per rule |
| Event delivery latency | < 1 minute (typical) | Regional |
| Event retention/replay | None | Service |

**Action Type → Target Field Mapping**:
| action_type | Required Field | Target Resource |
|-------------|---------------|-----------------|
| `FAAS` | `function_id` | OCI Function |
| `OSS` | `stream_id` | OCI Stream |
| `ONS` | `topic_id` | Notification Topic |

**Common Event Types**:
| Service | Event Type |
|---------|-----------|
| Object Storage | `com.oraclecloud.objectstorage.createobject` |
| Object Storage | `com.oraclecloud.objectstorage.deleteobject` |
| Functions | `com.oraclecloud.functions.function.invoke` |
| IAM | `com.oraclecloud.identitycontrolplane.createpolicy` |
| IAM | `com.oraclecloud.identitycontrolplane.deletepolicy` |
| Networking | `com.oraclecloud.virtualnetwork.changenetworksecuritygroupsecurityrules` |
| API Gateway | `com.oraclecloud.apigateway.createdeployment` |
| Vault | `com.oraclecloud.kms.schedulekeydeletion` |

**Terraform Import**:
```bash
# Import existing rule by OCID
terraform import 'module.events.oci_events_rule.rules["my_rule"]' <rule_ocid>

# Import block (Terraform >= 1.5)
import {
  to = module.events.oci_events_rule.rules["my_rule"]
  id = "ocid1.eventrule.oc1.sa-saopaulo-1.aaaaaaaexample"
}
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
- [ ] Validate event rule condition specificity (avoid overly broad filters)
- [ ] Confirm action targets are reachable (Functions, Streaming, Notifications)
- [ ] Commit state and tag release
```

## External Resources

### Official Documentation
- [OCI Events Service Overview](https://docs.oracle.com/iaas/Content/Events/Concepts/eventsoverview.htm)
- [Matching Events with Filters](https://docs.oracle.com/iaas/Content/Events/Concepts/filterevents.htm)
- [Services that Produce Events](https://docs.oracle.com/iaas/Content/Events/Reference/eventsproducers.htm)
- [Events Service Required IAM Policies](https://docs.oracle.com/iaas/Content/Events/Reference/eventsiam.htm)
- [OCI Events API Reference](https://docs.oracle.com/iaas/api/#/en/events/latest/Rule)
- [OCI Events Service Limits](https://docs.oracle.com/iaas/Content/General/Concepts/servicelimits.htm#events)

### Terraform Provider
- [oci_events_rule Resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/events_rule)
- [oci_events_rule Data Source](https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/events_rule)
- [oci_events_rules Data Source (List)](https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/events_rules)
- [Terraform Provider OCI Examples — Events](https://github.com/oracle/terraform-provider-oci/tree/master/examples/events)

### Related Skills
- [OCI IAM Terraform](../provisioning-oci-iam/SKILL.md) — IAM policies and Dynamic Groups required for Events
- [OCI Functions Serverless](../architecting-oci-serverless/SKILL.md) — Function targets for FAAS actions
- [OCI Serverless Stack](../provisioning-oci-serverless-stack/SKILL.md) — End-to-end serverless architecture
