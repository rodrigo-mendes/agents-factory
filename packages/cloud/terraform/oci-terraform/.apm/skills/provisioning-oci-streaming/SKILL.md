---
name: provisioning-oci-streaming
description: Provisions OCI Streaming resources (Stream Pools, Streams, Connect Harness) with Terraform OCI Provider v6.x+. Use when provisioning event streaming infrastructure for serverless architectures.
---

## Version Context

**Technology**: Terraform OCI Provider — Streaming (`oci_streaming_stream_pool`, `oci_streaming_stream`, `oci_streaming_connect_harness`)
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Terraform Version**: >= 1.7
**Provider Version**: oracle/oci >= 6.0, < 9.0
**Provider Registry**: https://registry.terraform.io/providers/oracle/oci/latest/docs
**Release Date**: GA, continuous releases (current stable, latest 8.13.0)
**Support Status**: Active

**Key Constraints**:
- Stream Pool `private_endpoint_settings` (subnet, NSGs) are **immutable** — changes force destroy/recreate of pool + all streams
- `nsg_ids` in private endpoint settings do **NOT support in-place update** — forces pool recreation
- Stream `partitions` are **immutable** — changing forces destroy/recreate with **data loss**
- Stream `retention_in_hours` is **read-only after creation** — cannot be altered
- `compartment_id` and `stream_pool_id` are **mutually exclusive** in `oci_streaming_stream`
- Billing is per **partition-hour** + data transfer — partitions directly impact cost
- Hierarchical model: **Stream Pool** → contains 1..N **Streams**

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform OCI Provider v6.x+. Many Streaming attributes are immutable after creation — misconfiguration requires destroy/recreate with potential data loss. Always validate partitions, retention, and network settings before `terraform apply`.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Cross-service integration examples
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases
- **[Module Architecture](#module-architecture)** — Terraform module composition
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Provider Version Constraint** — Streaming resources contain data in transit. Untested upgrades could trigger pool recreation
- **Private Stream Pool with Custom Encryption** — Public pool exposes Kafka endpoint. Customer-managed KMS key for compliance
- **Stream within Pool** — `stream_pool_id` inherits network/encryption. Never use `compartment_id` directly on stream
- **Partition sizing** — IMMUTABLE after creation. Size for peak throughput (1MB/s write, 2MB/s read per partition)
- **Retention period and tags** — 24h default (max 168h). Tags required for cost tracking

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Public vs Private Stream Pool** — Private for production (VCN-only access). Public only for dev/test
- **Oracle-Managed vs Customer-Managed Key (KMS)** — Customer-managed for PCI-DSS/SOC2. Oracle-managed for non-sensitive data
- **Partition Count** — IMMUTABLE. Size based on peak throughput needs. Over-provision slightly

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Stream with both `compartment_id` and `stream_pool_id`** — Mutually exclusive. Pool provides network/encryption context
- **Public Stream Pool with sensitive data** — Kafka endpoint exposed to internet. No network-level access control
- **Auto-create topics in production** — Uncontrolled stream creation bypasses naming/partitioning/tagging standards
- **Modifying partitions on existing Stream** — IMMUTABLE. Forces destroy/recreate with data loss
- **Mutating NSG on Private Stream Pool** — Forces pool recreation, destroying all streams and in-flight messages

---

## Integration Patterns

For complete integration code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Summary of integrations**:
- **Streaming ↔ OCI Functions** — Detached mode destination for async processing
- **Streaming ↔ Service Connector Hub** — Managed pipeline from source to stream
- **Streaming ↔ IAM** — Dynamic Group policies for stream read/write access
- **Streaming ↔ Network** — NSG rules for Kafka protocol (TCP 9092/9093)
- **Streaming ↔ OCI Events** — Event Rule action targeting stream for audit trail

---

## Module Architecture

### Multiple Streams via `for_each`

```hcl
# Create multiple streams from a map variable (OCI Provider v6.x+)
variable "streams" {
  type = map(object({
    partitions         = number
    retention_in_hours = number
  }))
  default = {
    "events" = {
      partitions         = 5
      retention_in_hours = 48
    }
    "audit" = {
      partitions         = 3
      retention_in_hours = 168
    }
    "notifications" = {
      partitions         = 1
      retention_in_hours = 24
    }
  }
}

resource "oci_streaming_stream" "this" {
  for_each = var.streams

  name               = "stream-${each.key}-${var.project_name}-${var.environment}"
  partitions         = each.value.partitions
  retention_in_hours = each.value.retention_in_hours
  stream_pool_id     = oci_streaming_stream_pool.this.id
  freeform_tags      = var.tags
}
```

### Module Outputs

```hcl
output "stream_pool_id" {
  description = "OCID of the Stream Pool"
  value       = oci_streaming_stream_pool.this.id
}

output "stream_pool_endpoint" {
  description = "FQDN of the Stream Pool messages endpoint"
  value       = oci_streaming_stream_pool.this.endpoint_fqdn
}

output "kafka_bootstrap_servers" {
  description = "Kafka bootstrap servers for Kafka-compatible clients"
  value       = oci_streaming_stream_pool.this.kafka_settings[0].bootstrap_servers
}

output "stream_ids" {
  description = "Map of stream names to OCIDs"
  value       = { for k, v in oci_streaming_stream.this : k => v.id }
}

output "stream_messages_endpoints" {
  description = "Map of stream names to messages endpoints"
  value       = { for k, v in oci_streaming_stream.this : k => v.messages_endpoint }
}
```

---

## Verification Loop

The agent MUST execute after each Terraform code generation:

### 1. Validate Configuration
```bash
terraform validate
# Exit code: 0 (valid) | 1 (invalid configuration)
```
**Expected output**: `Success! The configuration is valid.`
**Exit code**: 0

### 2. Plan Review
```bash
terraform plan -out=plan.tfplan
# Exit code: 0 (no changes) | 1 (error) | 2 (changes pending)
```
**Expected output**: Resources to be created/modified — verify NO unexpected destroy/recreate of streams or pools.
**Exit code**: 0
**Critical check**: Look for `# forces replacement` on any stream or stream pool — this means data loss.

### 3. Verify Stream Pool
```bash
oci streaming admin stream-pool list \
# Exit code: 0 (success) | 1 (auth/network error)
  --compartment-id $COMPARTMENT_OCID \
  --query 'data[*].{"name":"name","state":"lifecycle-state","is-private":"is-private","endpoint":"endpoint-fqdn"}' \
  --output table
```
**Expected output**: Pool in `ACTIVE` state with correct private/public setting.

### 4. Verify Streams
```bash
oci streaming admin stream list \
# Exit code: 0 (success) | 1 (auth/network error)
  --compartment-id $COMPARTMENT_OCID \
  --query 'data[*].{"name":"name","partitions":"partitions","retention":"retention-in-hours","state":"lifecycle-state"}' \
  --output table
```
**Expected output**: All streams in `ACTIVE` state with correct partitions and retention.

### 5. Produce/Consume Test Message
```bash
# Produce test message (base64 encoded)
oci streaming stream message put \
# Exit code: 0 (success) | 1 (auth/network error)
  --stream-id $STREAM_OCID \
  --messages '[{"key":"dGVzdA==","value":"aGVsbG8gd29ybGQ="}]'
# Expected: {"entries": [{"offset": 0, "partition": "0", ...}]}

# Create cursor and consume
CURSOR=$(oci streaming stream cursor create-cursor \
# Exit code: 0 (success) | 1 (auth/network error)
  --stream-id $STREAM_OCID \
  --partition "0" \
  --type TRIM_HORIZON \
  --query 'data.value' --raw-output)

oci streaming stream message get \
# Exit code: 0 (success) | 1 (auth/network error)
  --stream-id $STREAM_OCID \
  --cursor "$CURSOR" \
  --query 'data[*].{"key":"key","value":"value","offset":"offset","partition":"partition"}'
```
**Expected output**: Message retrieved with correct key/value.

### 6. Terraform State Verification
```bash
terraform state list | grep streaming
# Exit code: 0 (success) | 1 (error)
terraform state show module.streaming.oci_streaming_stream_pool.this
# Exit code: 0 (success) | 1 (not found)
```
**Expected output**: All streaming resources tracked in state.

### Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| "StreamPool in FAILED state" | Private endpoint with invalid subnet or missing Service Gateway | Verify subnet routes to Oracle Services; verify NSG allows 9092 |
| "Cannot update partitions" | Immutable attribute modification | Create new stream with desired partitions, migrate consumers, decommission old |
| "Cannot update retention_in_hours" | Read-only after creation | Create new stream with desired retention, migrate consumers |
| "ConflictException: stream_pool_id and compartment_id" | Both specified in `oci_streaming_stream` | Use only `stream_pool_id` (recommended) OR `compartment_id` |
| "Kafka connection refused" (private pool) | Client outside VCN or NSG blocking | Verify client is in same VCN; NSG allows 9092 from source |
| "SASL authentication failed" | Username format incorrect | Format: `<tenancy_ocid>/<user_ocid>/<stream_pool_ocid>` |
| "TopicAuthorizationException" | Missing IAM policy | Add: `Allow dynamic-group X to use stream-push in compartment Y` |
| "KMS key DISABLED" | KMS key disabled/deleted | Re-enable key in Vault; if deleted, pool is irrecoverable |
| "Terraform plan perpetual diff on kafka_settings" | `bootstrap_servers` is computed | Use `ignore_changes = [kafka_settings[0].bootstrap_servers]` |
| "NSG change forces recreation" | `nsg_ids` in private_endpoint_settings is immutable | Modify rules WITHIN the NSG instead of changing NSG association |

---

## Quick Reference

### Resource Reference

| Resource | Purpose | Key Immutable Args |
|----------|---------|-------------------|
| `oci_streaming_stream_pool` | Pool grouping streams (network, encryption, Kafka settings) | `private_endpoint_settings`, `nsg_ids` |
| `oci_streaming_stream` | Individual topic (partitions, retention) | `partitions`, `retention_in_hours` |
| `oci_streaming_connect_harness` | Kafka Connect integration | — |

### Service Limits

| Resource | Limit | Scope |
|----------|-------|-------|
| Stream Pools per compartment | 10 | Compartment |
| Streams per Stream Pool | 50 | Stream Pool |
| Streams per tenancy per region | 500 | Tenancy/Region |
| Partitions per stream | 50 | Stream |
| Total partitions per tenancy/region | 500 | Tenancy/Region |
| Retention period | 24–168 hours | Stream |
| Message size | 1 MB | Per message |
| Write throughput per partition | 1 MB/s | Partition |
| Read throughput per partition | 2 MB/s | Per consumer group |

### Terraform Import

```bash
# Import existing Stream Pool
terraform import module.streaming.oci_streaming_stream_pool.this "<stream_pool_ocid>"

# Import existing Stream
terraform import 'module.streaming.oci_streaming_stream.this["events"]' "<stream_ocid>"

# Import existing Connect Harness
terraform import module.streaming.oci_streaming_connect_harness.this "<connect_harness_ocid>"
```

### Kafka Client Configuration

> 📎 **Application-level configuration**: For Kafka client properties (bootstrap servers, SASL/PLAIN authentication), refer to the [OCI Streaming Kafka Compatibility documentation](https://docs.oracle.com/en-us/iaas/Content/Streaming/Tasks/kafkacompatibility.htm). For Java-based producers/consumers within OCI Functions, use skill `publishing-events-from-oci-functions`.

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
- [ ] Validate partition count (immutable after creation)
- [ ] Verify private endpoint connectivity if stream pool is private
- [ ] Commit state and tag release
```

## External Resources

### Official Documentation
- [OCI Streaming Overview](https://docs.oracle.com/en-us/iaas/Content/Streaming/home.htm) (verified 2026-07-26)
- [OCI Streaming Concepts](https://docs.oracle.com/en-us/iaas/Content/Streaming/Concepts/streamingoverview.htm) (verified 2026-07-26)
- [OCI Streaming Security](https://docs.oracle.com/en-us/iaas/Content/Streaming/Concepts/streamingsecurity.htm) (verified 2026-07-26)
- [OCI Streaming Kafka Compatibility](https://docs.oracle.com/en-us/iaas/Content/Streaming/Tasks/kafkacompatibility.htm) (verified 2026-07-26)

### Terraform Provider
- [oci_streaming_stream_pool](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream_pool) (verified 2026-07-26)
- [oci_streaming_stream](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream) (verified 2026-07-26)
- [oci_streaming_connect_harness](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_connect_harness) (verified 2026-07-26)
- [OCI Provider GitHub](https://github.com/oracle/terraform-provider-oci) (verified 2026-07-26)
- [OCI Streaming Terraform Examples](https://github.com/oracle/terraform-provider-oci/tree/master/examples/streaming) (verified 2026-07-26)

### Tagging & Cost
- [OCI Tagging Overview](https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm) (verified 2026-07-26)

### Terraform Core
- [Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules) (verified 2026-07-26)
- [Lifecycle Meta-Arguments](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle) (verified 2026-07-26)
