# Always Do Patterns — OCI Event-Driven Pub/Sub Provisioning

Mandatory Terraform patterns for the Streaming + SCH + Functions pub/sub stack. Auto-execute without waiting for user confirmation.

---

## Pattern 1 — IAM Before SCH Activation (depends_on)

**Why**: A Service Connector Hub connector without IAM policies enters FAILED state immediately on activation and **silently drops all data** — no retry, no buffer. This applies to both source (STREAM_READ/STREAM_CONSUME) and target (fn-function/fn-invocation) verbs. The IAM policy must be created and active before the connector is activated. `depends_on` enforces this ordering.

```hcl
# iam/main.tf — streaming policy created first
resource "oci_identity_policy" "streaming" {
  compartment_id = var.compartment_ocid
  name           = "policy-streaming-${var.environment}"
  description    = "Producer stream-push; SCH reads stream and invokes consumer functions"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use stream-push in compartment ${var.compartment_name}",
    "Allow any-user to {STREAM_READ, STREAM_CONSUME} in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",
    "Allow any-user to use fn-function   in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",
    "Allow any-user to use fn-invocation in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",
  ]
  freeform_tags = var.tags
}

# service-connector/main.tf — connector depends on IAM (injected via var.iam_dependencies)
resource "oci_sch_service_connector" "this" {
  for_each = var.connectors
  # ...
  depends_on = [var.iam_dependencies]  # var.iam_dependencies = [module.iam.streaming_policy_id]
}
```

---

## Pattern 2 — PUBLIC Stream Pool (No private_endpoint_settings)

**Why**: SCH is Oracle-managed and runs outside the customer VCN. A pool with `private_endpoint_settings` exposes only a private IP (in-VCN). SCH cannot reach it → `ErrorsAtSource` on every poll, `MessagesFromSource = 0`, consumers never fire.

```hcl
# streaming/main.tf — PUBLIC pool (no private_endpoint_settings block)
resource "oci_streaming_stream_pool" "this" {
  compartment_id = var.compartment_ocid
  name           = "sp-${var.project_name}-${var.environment}"

  # NO private_endpoint_settings block = PUBLIC pool
  # SCH (Oracle-managed, outside VCN) can reach the public messages endpoint.
  # In-VCN clients (Functions) reach the pool via NAT GW or Service GW.

  kafka_settings {
    auto_create_topics_enable = false
    log_retention_hours       = var.retention_hours
    num_partitions            = var.default_partitions
  }

  freeform_tags = var.tags
}
```

**When PRIVATE is correct**: Only when SCH is NOT the source and all consumers are warm in-VCN Kafka clients (Functions, microservices). Choosing PRIVATE with SCH as the intended source is a critical design error — immutable at pool creation.

---

## Pattern 3 — prevent_destroy on Stream

**Why**: Stream `partitions` and `retention_in_hours` are immutable. An accidental `terraform plan` change to either attribute shows `forces replacement` — destroying all buffered messages. `prevent_destroy = true` forces users to explicitly acknowledge the data-loss risk before proceeding.

```hcl
resource "oci_streaming_stream" "event_stream" {
  name               = var.stream_name
  partitions         = var.partitions
  retention_in_hours = var.retention_hours
  stream_pool_id     = oci_streaming_stream_pool.this.id
  freeform_tags      = var.tags

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [kafka_settings]  # bootstrap_servers is computed — ignore perpetual diff
  }
}
```

---

## Pattern 4 — for_each on SCH Connectors

**Why**: Fan-out requires N separate connectors for N consumers. `for_each` on a `var.connectors` map enables adding a consumer by extending the map without changing the module structure. Each connector gets its own cursor state in OCI Streaming.

```hcl
# service-connector/variables.tf
variable "connectors" {
  description = "Map of connector name to configuration. One connector per consumer (fan-out)."
  type = map(object({
    display_name      = string
    function_id       = string
    batch_size_in_kbs = optional(number)
    batch_time_in_sec = optional(number)
  }))
}

# service-connector/main.tf
resource "oci_sch_service_connector" "this" {
  for_each = var.connectors

  compartment_id = var.compartment_ocid
  display_name   = each.value.display_name
  state          = var.connector_state

  source {
    kind      = "streaming"
    stream_id = var.stream_id
    cursor { kind = var.cursor_kind }
  }

  target {
    kind              = "functions"
    function_id       = each.value.function_id
    batch_size_in_kbs = coalesce(each.value.batch_size_in_kbs, var.default_batch_size_in_kbs)
    batch_time_in_sec = coalesce(each.value.batch_time_in_sec, var.default_batch_time_in_sec)
  }

  freeform_tags = local.common_tags
  depends_on    = [var.iam_dependencies]
}
```

**Calling the module** (environments/dev/apps.tf):
```hcl
module "service_connector" {
  source          = "../../modules/service-connector"
  compartment_ocid = var.compartment_ocid
  stream_id       = module.streaming.stream_id
  cursor_kind     = "TRIM_HORIZON"
  connector_state = "ACTIVE"
  iam_dependencies = [module.iam.streaming_policy_id]

  connectors = {
    notify = {
      display_name = "sch-event-notify-dev"
      function_id  = module.app_evt_consumer_notify.function_id
    }
    audit = {
      display_name = "sch-event-audit-dev"
      function_id  = module.app_evt_consumer_audit.function_id
    }
  }
}
```

---

## Pattern 5 — Consumer Function Memory >= 1024 MB + Timeout = 300 s

**Why**: SCH invokes Functions synchronously. Standard JVM images (OTel + Jersey3 + OCI SDK) require ~60 s of platform provisioning + JVM pre-main before application code runs. At 256 MB (~0.17 vCPU) and timeout 60 s, the SCH sync deadline expires during cold-provisioning → abort → ErrorsAtTarget loop. 1024 MB raises CPU to ~0.67 vCPU (faster class-load); timeout 300 s gives the cold-provision time to complete.

```hcl
# In environments/dev/apps.tf — consumer function-app module calls
module "app_evt_consumer_notify" {
  source           = "../../modules/function-app"
  # ...
  memory_in_mbs    = 1024   # Minimum for SCH sync cold-start to complete
  timeout_in_seconds = 300  # Maximum; gives platform provisioning time to finish
  # provisioned_concurrency = 0  # Default; raise only if zero cold-start is budgeted (min=10)
}
```

Note: the producer function (invoked via API Gateway, which buffers cold-start) can remain at 256 MB if latency is tolerable. Only SCH-targeted consumer functions need the elevated settings.

---

## Pattern 6 — Batch Tuning on SCH Functions Target

**Why**: Default SCH batch parameters are not tuned for Functions cold-start economics. Under-tuned `batch_time_in_sec` causes one invocation per message (cold-start storm cost overrun). Over-tuned causes unacceptable delivery latency. Tune based on event volume and latency SLA.

```hcl
# For low-to-medium event volume (standard pub/sub)
target {
  kind              = "functions"
  function_id       = each.value.function_id
  batch_size_in_kbs = 128   # Accumulate up to 128 KB per batch
  batch_time_in_sec = 60    # Invoke every 60 s if batch not full (one poll cycle)
}

# For high-volume events (reduce per-invocation overhead)
target {
  kind              = "functions"
  function_id       = each.value.function_id
  batch_size_in_kbs = 5000  # Large batch reduces invocation count
  batch_time_in_sec = 120   # Accept higher latency for throughput
}
```
