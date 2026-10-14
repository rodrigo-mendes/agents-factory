### 🚫 Never Do

**Anti-Pattern**: Empty condition in production

```hcl
# 🚫 WRONG: Empty condition captures ALL events in compartment + children
# This generates thousands of invocations per minute in active compartments
resource "oci_events_rule" "catch_all" {
  compartment_id = var.compartment_ocid
  display_name   = "rule-catch-all"
  is_enabled     = true
  condition      = "{}"  # DANGEROUS: captures EVERY event

  actions {
    actions {
      action_type = "FAAS"
      is_enabled  = true
      function_id = var.function_id
    }
  }
}

# ✅ CORRECT: Always specify at least eventType (OCI Provider v6.x+)
resource "oci_events_rule" "specific_events" {
  compartment_id = var.compartment_ocid
  display_name   = "rule-specific-events"
  is_enabled     = true
  condition = jsonencode({
    eventType = ["com.oraclecloud.objectstorage.createobject"]
  })

  actions {
    actions {
      action_type = "FAAS"
      is_enabled  = true
      function_id = var.function_id
      description = "Process object creation events"
    }
  }
}
```
**Why it is prohibited**: Empty condition captures all events in the compartment and all child compartments, exhausting Function concurrency limits, Stream throughput, and generating exponential costs. Events are fire-and-forget — lost events during the flood are unrecoverable.
**Actual impact**: Function concurrency exhaustion, Stream throttling, exponential cost, unrecoverable data loss.
**Source**: https://docs.oracle.com/iaas/Content/Events/Concepts/filterevents.htm

---

**Anti-Pattern**: Hardcoded OCIDs in action targets

```hcl
# 🚫 WRONG: Hardcoded OCID breaks portability and Terraform dependency graph
actions {
  actions {
    action_type = "FAAS"
    is_enabled  = true
    function_id = "ocid1.fnfunc.oc1.sa-saopaulo-1.aaaaaaaaexample"
  }
}

# ✅ CORRECT: Use Terraform resource reference or variable (OCI Provider v6.x+)
actions {
  actions {
    action_type = "FAAS"
    is_enabled  = true
    function_id = oci_functions_function.processor.id
    # Alternative: function_id = var.function_id
    description = "Process events via function"
  }
}
```
**Why it is prohibited**: Hardcoded OCIDs break portability across environments (dev/staging/prod), prevent clean destroy/recreate cycles, and bypass Terraform's dependency graph causing race conditions during creation.
**Actual impact**: Deployment failures across environments, silent delivery failures when target resource doesn't exist, and untraceable state drift.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/events_rule

---

**Anti-Pattern**: Event Rule in root compartment without explicit need

```hcl
# 🚫 WRONG: Rule in root compartment captures events from ENTIRE tenancy
# Violates least-privilege and exposes information from other workloads
resource "oci_events_rule" "tenancy_wide" {
  compartment_id = var.tenancy_ocid  # ROOT — captures everything!
  display_name   = "rule-all-events"
  is_enabled     = true
  condition      = jsonencode({ eventType = ["com.oraclecloud.objectstorage.*"] })

  actions {
    actions {
      action_type = "OSS"
      is_enabled  = true
      stream_id   = var.stream_id
    }
  }
}

# ✅ CORRECT: Rule scoped to workload compartment (OCI Provider v6.x+)
resource "oci_events_rule" "workload_scoped" {
  compartment_id = var.compartment_ocid  # Specific workload compartment
  display_name   = "rule-workload-events-${var.environment}"
  is_enabled     = true
  condition      = jsonencode({ eventType = ["com.oraclecloud.objectstorage.*"] })

  actions {
    actions {
      action_type = "OSS"
      is_enabled  = true
      stream_id   = var.stream_id
      description = "Stream object storage events"
    }
  }
}
```
**Why it is prohibited**: Rules inherit hierarchically — a rule in the root compartment captures events from ALL compartments in the tenancy. This generates massive event volume, violates least-privilege, and may expose sensitive information from other workloads.
**Actual impact**: Tenancy-wide event capture, cross-workload information leakage, compliance violations, and uncontrolled costs.
**Source**: https://docs.oracle.com/iaas/Content/Events/Concepts/eventsoverview.htm

---

**Anti-Pattern**: Missing `description` on actions

```hcl
# 🚫 WRONG: Actions without descriptions are unidentifiable in Console and logs
actions {
  actions {
    action_type = "FAAS"
    is_enabled  = true
    function_id = var.function_id
    # No description — impossible to troubleshoot in OCI Console
  }
}

# ✅ CORRECT: Always include descriptive action descriptions (OCI Provider v6.x+)
actions {
  actions {
    action_type = "FAAS"
    is_enabled  = true
    function_id = var.function_id
    description = "Invoke file processor function on object upload"
  }
}
```
**Why it is prohibited**: Actions without descriptions are indistinguishable in the OCI Console and lifecycle messages. When a rule has multiple actions and one fails, the missing description makes troubleshooting significantly harder.
**Actual impact**: Increased mean-time-to-resolution (MTTR) during incident response.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/events_rule

---

