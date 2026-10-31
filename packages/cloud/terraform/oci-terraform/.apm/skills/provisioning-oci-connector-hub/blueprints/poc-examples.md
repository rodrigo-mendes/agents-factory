# Worked Examples — provisioning-oci-connector-hub

Source: `workspace/poc-oci-serverless/infra/modules/service-connector/`

---

## Worked example (from the reference PoC)

### Service Connector Hub (fan-out from Streaming to Functions) — `infra/modules/service-connector/main.tf`

The PoC deploys N Service Connectors (`for_each`) all reading from the **same stream** but each
maintaining its own cursor — real fan-out (every consumer receives every message). Each connector
targets a different OCI Function.

```hcl
# from infra/modules/service-connector/main.tf

locals {
  common_tags = merge(var.tags, {
    "Component" = "service-connector"
  })
}

resource "oci_sch_service_connector" "this" {
  for_each = var.connectors   # map: { "audit" = { display_name, function_id, ... }, ... }

  compartment_id = var.compartment_ocid
  display_name   = each.value.display_name
  state          = var.connector_state   # ACTIVE or INACTIVE

  source {
    kind      = "streaming"
    stream_id = var.stream_id   # same stream_id for all connectors → fan-out

    cursor {
      kind = var.cursor_kind   # TRIM_HORIZON or LATEST
    }
  }

  target {
    kind              = "functions"
    function_id       = each.value.function_id
    batch_size_in_kbs = coalesce(each.value.batch_size_in_kbs, var.default_batch_size_in_kbs)
    batch_time_in_sec = coalesce(each.value.batch_time_in_sec, var.default_batch_time_in_sec)
  }

  freeform_tags = local.common_tags

  # IAM MUST exist before activation — without the policy the connector enters FAILED
  # state and silently discards data (ErrorsAtSource metric will fire).
  depends_on = [var.iam_dependencies]
}
```

**Key patterns from this example:**
- `for_each = var.connectors` creates one connector per consumer — use a map with stable keys.
- `state = var.connector_state` allows deploying connectors in INACTIVE state first and activating after IAM is confirmed.
- `depends_on = [var.iam_dependencies]` enforces IAM creation before connector activation — critical pattern; omitting it causes silent data loss.
- `batch_size_in_kbs` and `batch_time_in_sec` are tuned per connector via `coalesce` with a module default.
- The same `stream_id` in all connectors is the fan-out mechanism — each connector holds an independent cursor.
