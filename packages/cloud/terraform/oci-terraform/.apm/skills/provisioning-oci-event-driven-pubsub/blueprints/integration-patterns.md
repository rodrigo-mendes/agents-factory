# Integration Patterns — OCI Event-Driven Pub/Sub Provisioning

Complete Terraform composition examples for the pub/sub stack.

---

## Pattern 1 — Full Stack Module Composition (dev)

The pattern as delivered in `infra/environments/dev/apps.tf`. Calls streaming + service-connector + function-app modules in dependency order.

```hcl
# ─── Streaming ────────────────────────────────────────────────────────────────
module "streaming" {
  source           = "../../modules/streaming"
  compartment_ocid = var.compartment_ocid
  project_name     = var.project_name
  environment      = var.environment

  # PUBLIC pool — required for SCH source (see provisioning-oci-streaming Ask First)
  # No private_endpoint_settings = public messages endpoint reachable by SCH
  partitions         = 3
  retention_hours    = 168  # 7 days — IMMUTABLE after creation

  stream_name = "event-stream"
  tags        = local.common_tags
}

# ─── Consumer Functions ───────────────────────────────────────────────────────
module "app_evt_consumer_notify" {
  source           = "../../modules/function-app"
  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_private_id
  nsg_ids          = [module.network.nsg_functions_id]

  application_name   = "app-evt-consumer-notify-${var.environment}"
  function_name      = "func-evt-consumer-notify"
  function_image     = var.evt_consumer_notify_image
  memory_in_mbs      = 1024   # Required: SCH sync cold-start ceiling fix
  timeout_in_seconds = 300    # Required: allow cold-provision to complete

  function_config = {
    NOTIFY_TARGET_URL  = var.notify_target_url
    APM_DOMAIN_URL     = var.apm_domain_url
    APM_DATA_KEY       = var.apm_data_key
    SERVICE_NAME       = "func-evt-consumer-notify"
    COMPARTMENT_OCID   = var.compartment_ocid
  }
}

module "app_evt_consumer_audit" {
  source           = "../../modules/function-app"
  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_private_id
  nsg_ids          = [module.network.nsg_functions_id]

  application_name   = "app-evt-consumer-audit-${var.environment}"
  function_name      = "func-evt-consumer-audit"
  function_image     = var.evt_consumer_audit_image
  memory_in_mbs      = 1024
  timeout_in_seconds = 300

  function_config = {
    APM_DOMAIN_URL  = var.apm_domain_url
    APM_DATA_KEY    = var.apm_data_key
    SERVICE_NAME    = "func-evt-consumer-audit"
    COMPARTMENT_OCID = var.compartment_ocid
  }
}

# ─── Service Connector Hub (fan-out) ──────────────────────────────────────────
module "service_connector" {
  source           = "../../modules/service-connector"
  compartment_ocid = var.compartment_ocid
  stream_id        = module.streaming.stream_id
  cursor_kind      = "TRIM_HORIZON"  # Replay on reactivation; consumers must be idempotent
  connector_state  = "ACTIVE"

  # IAM must exist before connectors activate (depends_on injected via this var)
  iam_dependencies = [module.iam.streaming_policy_id]

  # One entry per consumer = one independent SCH cursor per consumer = true fan-out
  connectors = {
    notify = {
      display_name      = "sch-event-notify-${var.environment}"
      function_id       = module.app_evt_consumer_notify.function_id
      batch_size_in_kbs = 128
      batch_time_in_sec = 60
    }
    audit = {
      display_name      = "sch-event-audit-${var.environment}"
      function_id       = module.app_evt_consumer_audit.function_id
      batch_size_in_kbs = 128
      batch_time_in_sec = 60
    }
  }

  tags = local.common_tags
}
```

---

## Pattern 2 — IAM Module Streaming Policy (all four verbs)

```hcl
# infra/modules/iam/main.tf (streaming policy section)
resource "oci_identity_policy" "streaming" {
  compartment_id = var.compartment_ocid
  name           = "policy-streaming-${var.environment}"
  description    = "Producer stream-push; SCH reads stream and invokes consumer functions"

  statements = [
    # Producer Functions DG publishes to stream
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use stream-push in compartment ${var.compartment_name}",

    # SCH reads from stream (source stage)
    "Allow any-user to {STREAM_READ, STREAM_CONSUME} in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",

    # SCH invokes Functions target — BOTH verbs required (fn-function = resolve; fn-invocation = invoke)
    # Missing fn-function → fast auth reject, zero function logs, ErrorsAtTarget (NOT cold-start)
    "Allow any-user to use fn-function   in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",
    "Allow any-user to use fn-invocation in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",
  ]

  freeform_tags = var.tags
}

# Output for use in service-connector module's depends_on
output "streaming_policy_id" {
  description = "OCID of the streaming IAM policy (pass to SCH module as iam_dependencies)"
  value       = oci_identity_policy.streaming.id
}
```

---

## Pattern 3 — Switching from PRIVATE to PUBLIC Pool (Force Replace)

When the pool was initially created as PRIVATE and SCH is being added as a source:

```bash
# Step 1: Remove private_endpoint_settings from streaming/main.tf
# (plain apply is a no-op for optional+computed attribute — must force-replace)

# Step 2: Force-replace pool (cascades to stream via dependency)
terraform apply \
  -replace='module.streaming.oci_streaming_stream_pool.this' \
  -replace='module.streaming.oci_streaming_stream.event_stream' \
  <existing pin -var args>
# Plan must show: pool REPLACED, stream REPLACED, SCH sources UPDATED (new stream_id), producer app config UPDATED
# DO NOT apply if anything else is destroyed (functions, gateway, network)

# Step 3: SCH connectors may also need replace (if their source config had private endpoint)
terraform apply \
  -replace='module.service_connector.oci_sch_service_connector.this["notify"]' \
  -replace='module.service_connector.oci_sch_service_connector.this["audit"]' \
  <pins>
# Plan: both connectors DESTROYED + RECREATED with new public stream_id

# Step 4: Verify public endpoint
oci streaming admin stream-pool get \
  --stream-pool-id <NEW_POOL_OCID> \
  --query 'data.{"endpoint":"endpoint-fqdn","private-ep":"private-endpoint-settings"}'
# Expected: private-ep = null; endpoint contains "cell-1.streaming..."
```

**Data-loss warning**: Pool and stream recreation destroys all buffered messages. For a POC this is acceptable. For production, drain all consumers before recreating.

---

## Pattern 4 — Adding a Third Consumer (Extending for_each)

```hcl
# environments/dev/apps.tf — add third consumer function app
module "app_evt_consumer_db" {
  source             = "../../modules/function-app"
  # ...same pattern as notify/audit...
  memory_in_mbs      = 1024
  timeout_in_seconds = 300
}

# service-connector module call — add third entry to connectors map
module "service_connector" {
  # ...
  connectors = {
    notify = { ... }
    audit  = { ... }
    db = {                                            # ← New consumer
      display_name = "sch-event-db-${var.environment}"
      function_id  = module.app_evt_consumer_db.function_id
    }
  }
}
# terraform plan → 1 resource added (new oci_sch_service_connector.this["db"])
# Existing connectors untouched (for_each keys are stable)
```
