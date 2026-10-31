# Never Do Patterns — OCI Event-Driven Pub/Sub Provisioning

Each anti-pattern shows what NOT to do and the correct alternative.

---

## Anti-Pattern 1 — Private Stream Pool When SCH Is the Source

**Risk Level**: CRITICAL
**Impact**: SCH is Oracle-managed and runs outside the customer VCN. A pool with `private_endpoint_settings` has only a private IP address inside the VCN (e.g., 10.0.1.131:443). SCH cannot reach it. Result: `ErrorsAtSource` increments every ~5-min poll cycle, `MessagesFromSource = 0`, consumers never invoked. The connector shows ACTIVE in the console (lifecycle state is not FAILED — it's ACTIVE but reading 0 messages with errors counted in metrics).

```hcl
# ❌ WRONG: private pool + SCH as source = SCH cannot read (ErrorsAtSource)
resource "oci_streaming_stream_pool" "this" {
  compartment_id = var.compartment_ocid
  name           = "sp-events-dev"

  private_endpoint_settings {        # ← Blocks SCH access
    subnet_id = var.subnet_private_id
    nsg_ids   = [var.nsg_streaming_id]
  }

  kafka_settings { auto_create_topics_enable = false }
}

# ✅ CORRECT: public pool → SCH reaches Oracle-managed endpoint
resource "oci_streaming_stream_pool" "this" {
  compartment_id = var.compartment_ocid
  name           = "sp-events-dev"

  # NO private_endpoint_settings = PUBLIC endpoint
  # SCH (Oracle-managed) can reach cell-1.streaming.<region>.oci.oraclecloud.com
  # In-VCN Functions reach it via NAT Gateway

  kafka_settings { auto_create_topics_enable = false }
  freeform_tags = var.tags
}
```

**Reconciliation with `provisioning-oci-streaming` skill**: That skill's Never Do section correctly prohibits public pools for "sensitive data" (security concern for in-VCN Kafka clients). This prohibition applies when Kafka clients inside the VCN are the sole consumers. When SCH is the source, PUBLIC is the ONLY correct choice — the security model shifts from network-level (private endpoint) to IAM + TLS.

**Evidence**: `docs/handoff/event-pubsub/diagnosis-report-sch-source.md` (private pool analysis), `deploy-report.md` cycles 9-10 (public pool fix → fan-out GREEN).

---

## Anti-Pattern 2 — Removing private_endpoint_settings as a Plain terraform apply

**Risk Level**: HIGH
**Impact**: `private_endpoint_settings` on `oci_streaming_stream_pool` is an optional+computed attribute. Removing it from HCL does NOT trigger a diff in `terraform plan`. The provider interprets the absent block as "leave as-is" (not "set to null"). A plain `terraform apply` is a silent no-op while the pool remains private and SCH continues to fail.

```hcl
# ❌ WRONG: remove block from HCL and run plain terraform apply
# Before:
resource "oci_streaming_stream_pool" "this" {
  private_endpoint_settings { subnet_id = ... nsg_ids = [...] }
}
# After (HCL edited, block removed):
resource "oci_streaming_stream_pool" "this" {
  # (no private_endpoint_settings block)
}
# terraform plan → "No changes." ← SILENT NO-OP, pool still private

# ✅ CORRECT: force-replace the pool
# terraform apply -replace='module.streaming.oci_streaming_stream_pool.this'
# → Plan shows: pool DESTROYED + RECREATED (public), stream DESTROYED + RECREATED
# → Review plan: also updates SCH source configs + producer app config (new stream OCID)
# → Accept data-loss (buffered events in old pool/stream are gone)
# → All references to stream_id must be re-pointed (SCH sources, producer config)
```

**Same trap applies to `provisioned_concurrency_config`** on `oci_functions_function` — removing it from HCL is a no-op. Use `oci fn function update --provisioned-concurrency '{"strategy":"NONE"}' --force` via CLI to clear it without resource replacement.

**Evidence**: `docs/handoff/event-pubsub/deploy-report.md` cycle 9 (no-op trap confirmed by plan review), cycle 7 (PC no-op confirmed, fixed via CLI).

---

## Anti-Pattern 3 — SCH Connector Without All Four IAM Verbs

**Risk Level**: CRITICAL
**Impact**: Missing any of the four required IAM verbs causes silent failure:
- Missing `STREAM_READ`/`STREAM_CONSUME` → `ErrorsAtSource`, stream never read
- Missing `fn-function` → fast auth reject, zero function logs, `ErrorsAtTarget` (looks like cold start but isn't)
- Missing `fn-invocation` → auth reject after function resolved

```hcl
# ❌ WRONG: only fn-invocation (common mistake — misses fn-function)
resource "oci_identity_policy" "streaming" {
  statements = [
    "Allow dynamic-group dg-functions to use stream-push in compartment X",
    "Allow any-user to {STREAM_READ, STREAM_CONSUME} in compartment X where ...",
    # Missing: fn-function
    "Allow any-user to use fn-invocation in compartment X where ...",
  ]
}
# → ErrorsAtTarget every poll cycle, zero consumer function logs (fast auth reject)

# ✅ CORRECT: all four verbs
resource "oci_identity_policy" "streaming" {
  statements = [
    "Allow dynamic-group dg-functions to use stream-push in compartment ${var.compartment_name}",
    "Allow any-user to {STREAM_READ, STREAM_CONSUME} in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",
    "Allow any-user to use fn-function   in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",
    "Allow any-user to use fn-invocation in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",
  ]
}
```

**Evidence**: `docs/handoff/event-pubsub/diagnosis-report-sch-auth.md` (fn-function missing → zero logs, fast reject), `infra/modules/iam/main.tf` lines 92-93 (final correct state).

---

## Anti-Pattern 4 — Setting provisioned_concurrency = 1 (Rejected by Platform)

**Risk Level**: MEDIUM
**Impact**: OCI Functions API rejects any `provisioned_concurrency_config` with count not a multiple of 10. `count = 1` returns `400 InvalidParameter: Count must be a multiple of 10`. The function update fails; Terraform plan shows an in-place update but apply errors. This also means "1 warm container" is not achievable — minimum viable PC = 10 containers.

```hcl
# ❌ WRONG: count = 1 (rejected by OCI API)
provisioned_concurrency_config {
  strategy = "CONSTANT"
  count    = 1   # → 400 InvalidParameter: Count must be a multiple of 10
}

# ✅ CORRECT if PC is needed: minimum = 10
provisioned_concurrency_config {
  strategy = "CONSTANT"
  count    = 10  # 10 always-warm containers per function; costs 10× compared to 0
}
# Or: do not use PC at all (count=0 is the default, pay-per-use works with timeout=300s+memory=1024MB)
```

**Evidence**: `docs/handoff/event-pubsub/deploy-report.md` cycle 6 (PC count=1 rejected, minimum 10 applied).

---

## Anti-Pattern 5 — Missing prevent_destroy on Stream

**Risk Level**: HIGH
**Impact**: Stream `partitions` and `retention_in_hours` are immutable. Any future change to these attributes in the Terraform config generates a plan that silently destroys the stream and all its buffered messages. Without `prevent_destroy = true`, a Terraform plan review is the only safeguard — and it is easy to miss.

```hcl
# ❌ WRONG: no lifecycle protection on stream
resource "oci_streaming_stream" "event_stream" {
  name               = "event-stream"
  partitions         = 3
  retention_in_hours = 168
  stream_pool_id     = oci_streaming_stream_pool.this.id
  # No lifecycle block → future partition change silently plans a destroy
}

# ✅ CORRECT: prevent_destroy blocks accidental data loss
resource "oci_streaming_stream" "event_stream" {
  name               = "event-stream"
  partitions         = 3
  retention_in_hours = 168
  stream_pool_id     = oci_streaming_stream_pool.this.id
  freeform_tags      = var.tags

  lifecycle {
    prevent_destroy = true  # Force explicit acknowledgment if stream must be destroyed
    ignore_changes  = [kafka_settings]  # Avoids perpetual diff on computed bootstrap_servers
  }
}
```
