### ✅ Always Do

**Provider Version Constraint**: Lock the OCI provider to a tested range to prevent breaking changes in event-critical resources.

```hcl
# ✅ CORRECT: Constrained provider version for Events stability (OCI Provider v6.x+)
terraform {
  required_version = ">= 1.7"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0, < 9.0"
    }
  }
}
```
**Why it is mandatory**: Events rules integrate with Functions, Streaming, and Notifications. An untested provider upgrade could silently change action type behavior or condition schema.
**Failure if omitted**: Uncontrolled provider upgrades may introduce breaking changes to `oci_events_rule` resources.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs

---

**Specific Condition with jsonencode()**: Event Rules MUST use `jsonencode()` for the `condition` field and MUST specify at least one `eventType`. This prevents accidental catch-all rules that generate massive invocation volumes.

```hcl
# ✅ CORRECT: Event Rule with specific condition using jsonencode() (OCI Provider v6.x+)
resource "oci_events_rule" "object_upload_trigger" {
  compartment_id = var.compartment_ocid
  display_name   = "rule-object-upload-${var.project_name}-${var.environment}"
  description    = "Triggers function on Object Storage object creation"
  is_enabled     = var.is_enabled

  # Condition JSON — ALWAYS use jsonencode(), ALWAYS specify eventType
  condition = jsonencode({
    eventType = ["com.oraclecloud.objectstorage.createobject"]
    data = {
      additionalDetails = {
        bucketName = [var.source_bucket_name]
      }
    }
  })

  actions {
    actions {
      action_type = "FAAS"
      is_enabled  = true
      function_id = var.function_id
      description = "Invoke processing function on object upload"
    }
  }

  freeform_tags = var.tags
}
```
**Why it is mandatory**: An empty condition `{}` captures ALL events in the compartment and children, generating thousands of invocations per minute and exhausting Function concurrency limits, Stream throughput, and causing exponential costs.
**Failure if omitted**: Unfiltered event flood, unrecoverable lost events, and potential service disruption.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/events_rule | https://docs.oracle.com/iaas/Content/Events/Concepts/filterevents.htm

---

**Type-Safe Action Targets via Terraform References**: Action targets (`function_id`, `stream_id`, `topic_id`) MUST use Terraform resource references or variables — never hardcoded OCIDs. The correct target field must match the `action_type`.

```hcl
# ✅ CORRECT: Fan-out pattern with multiple type-safe actions (OCI Provider v6.x+)
# Note: The nested actions block structure is MANDATORY — actions{} wraps inner actions{} blocks
resource "oci_events_rule" "audit_event_fanout" {
  compartment_id = var.compartment_ocid
  display_name   = "rule-audit-fanout-${var.project_name}-${var.environment}"
  description    = "Fan-out audit events to Function, Stream, and Notification"
  is_enabled     = true

  condition = jsonencode({
    eventType = [
      "com.oraclecloud.identitycontrolplane.createpolicy",
      "com.oraclecloud.identitycontrolplane.deletepolicy",
      "com.oraclecloud.identitycontrolplane.updatepolicy"
    ]
  })

  actions {
    # Action 1: FAAS — requires function_id (Terraform reference)
    actions {
      action_type = "FAAS"
      is_enabled  = true
      function_id = oci_functions_function.compliance_check.id
      description = "Run compliance check on IAM policy change"
    }

    # Action 2: OSS — requires stream_id (Terraform reference)
    actions {
      action_type = "OSS"
      is_enabled  = true
      stream_id   = oci_streaming_stream.audit.id
      description = "Stream IAM audit events for retention"
    }

    # Action 3: ONS — requires topic_id (variable reference)
    actions {
      action_type = "ONS"
      is_enabled  = true
      topic_id    = var.security_notification_topic_id
      description = "Alert security team on IAM policy changes"
    }
  }

  freeform_tags = var.tags
}
```
**Why it is mandatory**: Hardcoded OCIDs break portability between environments, prevent clean destroy/recreate, and bypass Terraform's dependency graph (causing race conditions). The nested `actions` block structure is required by the provider — inner `actions` blocks cannot be at top level.
**Failure if omitted**: Deployment failures across environments, silent delivery failures due to missing targets, and race conditions on create.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/events_rule

---

**depends_on for IAM Policy Propagation**: Event Rules with `FAAS` action type MUST depend on the IAM policy that grants the `cloudevents` service principal permission to invoke Functions. Without this, invocations fail silently.

```hcl
# ✅ CORRECT: IAM policy for Events service + depends_on (OCI Provider v6.x+)
# Service principal is 'cloudevents' — NOT 'events' or 'Events'
resource "oci_identity_policy" "events_invoke_functions" {
  compartment_id = var.tenancy_ocid
  name           = "policy-events-invoke-functions-${var.project_name}-${var.environment}"
  description    = "Permite Events Service invocar Functions"

  statements = [
    "Allow service cloudevents to use fn-invocation in compartment ${var.compartment_name}",
    "Allow service cloudevents to use virtual-network-family in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}

# Event Rule MUST depend on policy propagation (up to 60s delay)
resource "oci_events_rule" "trigger_function" {
  compartment_id = var.compartment_ocid
  display_name   = "rule-trigger-fn-${var.project_name}-${var.environment}"
  description    = "Event rule that triggers function"
  is_enabled     = true

  condition = jsonencode({
    eventType = ["com.oraclecloud.objectstorage.createobject"]
  })

  actions {
    actions {
      action_type = "FAAS"
      is_enabled  = true
      function_id = var.function_id
      description = "Invoke function on object creation"
    }
  }

  # MANDATORY: Wait for IAM policy to propagate
  depends_on = [oci_identity_policy.events_invoke_functions]

  freeform_tags = var.tags
}
```
**Why it is mandatory**: IAM policy propagation takes up to 60 seconds. Without `depends_on`, the rule is created before the policy is active, causing silent invocation failures — no error in Events logs, only visible in Function metrics.
**Failure if omitted**: Function invocations silently fail with no error logs in the Events service.
**Source**: https://docs.oracle.com/iaas/Content/Events/Reference/eventsiam.htm

---

**Wildcard for Event Type Families**: Use `*` wildcard at the END of `eventType` paths to capture entire event families without listing each type individually.

```hcl
# ✅ CORRECT: Wildcard captures entire database event family (OCI Provider v6.x+)
resource "oci_events_rule" "database_all_events" {
  compartment_id = var.compartment_ocid
  display_name   = "rule-database-all-${var.project_name}-${var.environment}"
  description    = "Capture all database service events"
  is_enabled     = true

  # Wildcard ONLY at the END of the path — mid-path wildcards are NOT supported
  condition = jsonencode({
    eventType = ["com.oraclecloud.databaseservice.*"]
  })

  actions {
    actions {
      action_type = "OSS"
      is_enabled  = true
      stream_id   = var.database_events_stream_id
      description = "Stream all database events for monitoring"
    }
  }

  freeform_tags = var.tags
}
```
**Why it is mandatory**: Listing individual event types is error-prone and misses new events added by OCI. Wildcard ensures comprehensive capture for monitoring and auditing use cases.
**Failure if omitted**: Missing event types in condition leads to blind spots in monitoring and compliance.
**Source**: https://docs.oracle.com/iaas/Content/Events/Concepts/filterevents.htm

---

