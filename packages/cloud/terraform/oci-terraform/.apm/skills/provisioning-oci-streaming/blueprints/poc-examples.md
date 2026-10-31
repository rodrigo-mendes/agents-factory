# Worked Examples — provisioning-oci-streaming

Source: `workspace/poc-oci-serverless/infra/modules/streaming/`

---

## Worked example (from the reference PoC)

### Stream Pool (PUBLIC) + Stream with data protection — `infra/modules/streaming/main.tf`

The PoC uses a **public** stream pool deliberately — the OCI Service Connector Hub managed service
runs outside the VCN and cannot reach a pool with a private endpoint. The trade-off (public endpoint
vs. VCN isolation) is compensated by IAM least-privilege, CMEK, and OCI Audit.

```hcl
# from infra/modules/streaming/main.tf

locals {
  common_tags = merge(var.tags, { "Component" = "streaming" })
}

resource "oci_streaming_stream_pool" "this" {
  compartment_id = var.compartment_ocid
  name           = "sp-${var.project_name}-${var.environment}"

  # PUBLIC pool — no private_endpoint_settings block.
  # IMMUTABLE: adding/removing private_endpoint_settings forces destroy/recreate
  # of the pool AND all streams (message loss).

  kafka_settings {
    auto_create_topics_enable = false   # Never allow ad-hoc topic creation
  }

  # CMEK optional — empty = Oracle-managed key; non-empty = customer key
  dynamic "custom_encryption_key" {
    for_each = var.kms_key_id != "" ? [1] : []
    content {
      kms_key_id = var.kms_key_id
    }
  }

  freeform_tags = local.common_tags
}

resource "oci_streaming_stream" "event_stream" {
  name               = var.stream_name
  partitions         = var.partitions          # IMMUTABLE after creation
  retention_in_hours = var.retention_in_hours  # Read-only after creation (up to 168h / 7d)
  stream_pool_id     = oci_streaming_stream_pool.this.id

  freeform_tags = local.common_tags

  lifecycle {
    prevent_destroy = true   # Protects buffered messages and SCH cursors from accidental destroy
  }
}
```

**Key patterns from this example:**
- `auto_create_topics_enable = false` — mandatory; ad-hoc topic creation bypasses naming/partition/tag controls.
- `partitions` and `retention_in_hours` are **immutable** after creation — changing either forces `terraform apply -replace` with message loss.
- `prevent_destroy = true` on the stream (not the pool) — prevents accidental `terraform destroy` from wiping buffered messages. The pool does NOT have `prevent_destroy` because a `-replace` of the pool (for public↔private endpoint migration) is a legitimate operation.
- CMEK wiring in environment: `kms_key_id = var.streaming_use_cmek ? module.vault.key_id : ""`.
