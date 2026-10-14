### 🚫 Never Do

**Anti-Pattern**: Stream with both `compartment_id` and `stream_pool_id`

```hcl
# 🚫 WRONG: compartment_id and stream_pool_id are mutually exclusive (OCI Provider v6.x+)
resource "oci_streaming_stream" "bad" {
  name               = "my-stream"
  partitions         = 1
  compartment_id     = var.compartment_ocid     # ⚠️ CONFLICT
  stream_pool_id     = var.stream_pool_ocid     # ⚠️ CONFLICT
  retention_in_hours = 24
}

# ✅ CORRECT: Use stream_pool_id to inherit network/encryption from pool
resource "oci_streaming_stream" "good" {
  name               = "my-stream"
  partitions         = 1
  stream_pool_id     = oci_streaming_stream_pool.this.id
  retention_in_hours = 24
}
```
**Why it is prohibited**: `compartment_id` and `stream_pool_id` are mutually exclusive parameters. Specifying both causes an apply error that blocks the entire Terraform pipeline.
**Actual impact**: `terraform apply` fails with `ConflictException`, blocking deployment.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream

---

**Anti-Pattern**: Public Stream Pool with sensitive data

```hcl
# 🚫 WRONG: Public pool exposes Kafka endpoint to internet (OCI Provider v6.x+)
resource "oci_streaming_stream_pool" "bad" {
  compartment_id = var.compartment_ocid
  name           = "sp-production"
  # No private_endpoint_settings = PUBLIC on the internet
  # No custom_encryption_key = Oracle-managed key

  kafka_settings {
    auto_create_topics_enable = true  # Any producer creates topics!
  }
}

# ✅ CORRECT: Private pool with KMS and governed topic creation
resource "oci_streaming_stream_pool" "good" {
  compartment_id = var.compartment_ocid
  name           = "sp-production"

  private_endpoint_settings {
    subnet_id = var.subnet_private_id
    nsg_ids   = [var.nsg_streaming_id]
  }

  custom_encryption_key {
    kms_key_id = var.kms_key_ocid
  }

  kafka_settings {
    auto_create_topics_enable = false
    log_retention_hours       = 168
    num_partitions            = 5
  }

  freeform_tags = var.tags
}
```
**Why it is prohibited**: Public endpoint exposes Kafka protocol to the internet. Any client with SASL credentials can connect, produce, and consume. Combined with `auto_create_topics_enable = true`, any producer can create ungoverned topics.
**Actual impact**: Data exposure; unauthorized access; ungoverned topic proliferation; cost overrun.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Streaming/Concepts/streamingoverview.htm

---

**Anti-Pattern**: Auto-create topics enabled in production

```hcl
# 🚫 WRONG: Allows any producer to create topics with default settings (OCI Provider v6.x+)
kafka_settings {
  auto_create_topics_enable = true  # NEVER in production
}

# ✅ CORRECT: Disable auto-create; manage all streams via Terraform
kafka_settings {
  auto_create_topics_enable = false
  log_retention_hours       = 24
  num_partitions            = 1
}
```
**Why it is prohibited**: Auto-create bypasses Terraform governance. Producers sending messages to non-existent topics silently create them with default partitions/retention, violating naming conventions and generating untracked costs.
**Actual impact**: Ungoverned topics; naming chaos; cost overrun; no Terraform state tracking for auto-created topics.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream_pool

---

**Anti-Pattern**: Modifying partitions on an existing Stream

```hcl
# 🚫 WRONG: Changing partitions forces destroy/recreate — DATA LOSS (OCI Provider v6.x+)
# Before: partitions = 3
# After:  partitions = 5 → DESTROY + RECREATE!
resource "oci_streaming_stream" "bad" {
  name       = "critical-events"
  partitions = 5  # Changed from 3 → 5 = ALL MESSAGES LOST
  # ...
}

# ✅ CORRECT: Create a new stream, migrate consumers, decommission old one
resource "oci_streaming_stream" "events_v2" {
  name               = "stream-events-v2-${var.environment}"
  partitions         = 5
  stream_pool_id     = oci_streaming_stream_pool.this.id
  retention_in_hours = 24
  freeform_tags      = var.tags
}

# Keep old stream protected until consumers migrate
resource "oci_streaming_stream" "events_v1" {
  name               = "stream-events-v1-${var.environment}"
  partitions         = 3
  stream_pool_id     = oci_streaming_stream_pool.this.id
  retention_in_hours = 24
  freeform_tags      = var.tags

  lifecycle {
    prevent_destroy = true  # Protect during migration
  }
}
```
**Why it is prohibited**: `partitions` is immutable. Terraform plans destroy/recreate when the value changes. All unconsumed messages in the stream are permanently lost.
**Actual impact**: Complete data loss of all in-flight messages; consumer offset reset; potential downstream processing gaps.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream

---

**Anti-Pattern**: Mutating NSG association on Private Stream Pool

```hcl
# 🚫 WRONG: Changing nsg_ids forces destroy/recreate of entire pool (OCI Provider v6.x+)
private_endpoint_settings {
  subnet_id = var.subnet_id
  nsg_ids   = [var.new_nsg_id]  # Changed! → ENTIRE POOL + ALL STREAMS DESTROYED
}

# ✅ CORRECT: Modify rules WITHIN the existing NSG (rules are mutable)
resource "oci_core_network_security_group_security_rule" "streaming_ingress" {
  network_security_group_id = var.nsg_streaming_id  # Same NSG — no pool recreation
  direction                 = "INGRESS"
  protocol                  = "6"  # TCP
  source                    = var.new_source_nsg_id
  source_type               = "NETWORK_SECURITY_GROUP"
  description               = "Allow Kafka from new source"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 9092
      max = 9092
    }
  }
}
```
**Why it is prohibited**: `nsg_ids` in `private_endpoint_settings` does not support in-place updates. Changing the NSG association forces destroy/recreate of the Stream Pool and ALL Streams within it.
**Actual impact**: Complete pool and stream destruction; data loss across all streams in the pool.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream_pool

---

