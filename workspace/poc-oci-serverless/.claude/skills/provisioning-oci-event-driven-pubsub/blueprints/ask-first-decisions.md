# Ask First Decisions — OCI Event-Driven Pub/Sub Provisioning

Present these options to the user and wait for a decision before generating Terraform.

---

## Decision 1 — Stream Pool Type (PUBLIC vs PRIVATE)

**Ask**: "Will Service Connector Hub be the source for this stream, or will only in-VCN Kafka clients (Functions, microservices inside the VCN) read from it directly?"

| Option | Config | SCH as Source | In-VCN Kafka | When to Choose |
|--------|--------|--------------|--------------|----------------|
| **PUBLIC** (recommended when SCH is source) | No `private_endpoint_settings` block | YES | YES (via NAT or Service GW) | SCH + Functions fan-out (standard pub/sub pattern 02) |
| **PRIVATE** | `private_endpoint_settings { subnet_id, nsg_ids }` | NO — SCH outside VCN | YES | In-VCN-only consumers; SCH not used |

**This decision is immutable.** `private_endpoint_settings` cannot be changed after pool creation without `terraform apply -replace` (destroys pool + all streams inside it; data loss; new OCIDs). Make this decision before the first `terraform apply`.

**Reconciliation note for `provisioning-oci-streaming` skill**: The streaming skill's "Never Do" section flags public pools for sensitive data (correct for in-VCN-only Kafka access). This pub/sub skill overrides that guidance for the specific case where SCH is the source — PUBLIC is the only viable choice. Both skills are consistent: PRIVATE is correct for in-VCN clients; PUBLIC is required for SCH.

---

## Decision 2 — Cursor Strategy (LATEST vs TRIM_HORIZON)

**Ask**: "If the SCH connector is deactivated (maintenance, forced-replace, incident) and later reactivated, should it recover missed messages or start from the newest available?"

| Option | `cursor_kind` | Recovery Behavior | Risk | When to Choose |
|--------|--------------|------------------|------|----------------|
| `LATEST` | `"LATEST"` | Starts reading new messages; gap is permanent | Missed events during INACTIVE lost forever | Notifications, real-time alerts — no tolerance for duplicate processing |
| `TRIM_HORIZON` | `"TRIM_HORIZON"` | Replays from oldest retained message (up to 7 days of stream retention) | Reactivation replays ALL retained data; downstream must be fully idempotent | Audit, compliance, DB materialization — no tolerance for gaps |

**Operational implication**: Pool recreation (e.g., switching from PRIVATE to PUBLIC) requires SCH connector recreation (connector's source private-endpoint-settings becomes invalid). The new connector's cursor starts fresh regardless of kind — there is no cursor state transfer.

---

## Decision 3 — SCH Batch Tuning Values

**Ask**: "What is the approximate event volume per hour, and what is the maximum acceptable end-to-end event delivery latency?"

| Scenario | `batch_size_in_kbs` | `batch_time_in_sec` | Invocation Pattern |
|----------|--------------------|--------------------|-------------------|
| Low volume, latency-tolerant (default) | 128 | 60 | 1 invoke/poll-cycle or when batch full |
| Medium volume, balanced | 1000 | 60 | Multiple events per invoke |
| High volume, throughput-optimized | 5000 | 120 | Large batches, fewer cold starts |
| Low volume, latency-sensitive | 64 | 10 | Near-real-time delivery, more invocations |

**Note**: Lower `batch_time_in_sec` increases invocation frequency and cold-start risk if containers are not warm. Higher values accumulate more events per batch but delay delivery. For SCH→Functions with standard JVM consumers (no PC), lower batch frequency reduces cold-start exposure.

---

## Decision 4 — Provisioned Concurrency (Zero Cold Start)

**Ask**: "Is there a strict SLA requiring zero cold-start on SCH deliveries (e.g., compliance SLA where every message must be processed within N seconds of SCH poll)? Is there budget for always-on containers?"

| Option | Cold Start | Cost | Constraint |
|--------|-----------|------|-----------|
| **None** (default `provisioned_concurrency = 0`) | ~60 s on cold container | Pay-per-use only | Cold delivery completes with timeout=300s + memory=1024MB |
| **Provisioned concurrency** (`count = 10`, minimum) | ~0 s | 10 always-on 1024 MB containers per consumer function | Platform requires count to be multiple of 10; count=1 is REJECTED |

**PC cost example**: 2 consumer functions × 10 containers × 1024 MB = 20 always-on containers at 1024 MB billing rate. At ~$0.00001285/GB-s, this is ~$0.264/hour continuously.

**Important**: OCI Functions PC count must be a multiple of 10. `provisioned_concurrency = 1` is rejected by the OCI API with `400 InvalidParameter: Count must be a multiple of 10`. Minimum viable = 10 per function.

**Also important**: Removing `provisioned_concurrency_config` from HCL is a NO-OP (optional+computed attribute). To actually remove PC, use the CLI directly: `oci fn function update --function-id <OCID> --provisioned-concurrency '{"strategy":"NONE"}' --force`. Then `terraform apply` will see no diff.

---

## Decision 5 — Stream Retention Period

**Ask**: "How long should events be available for replay if a connector is deactivated, or for debugging? Note: retention is immutable after stream creation."

| Retention | Hours | When |
|-----------|-------|------|
| 24 h (default) | 24 | Dev/test, ephemeral event patterns |
| 7 days (max) | 168 | Audit, compliance, replay scenarios |
| Custom | 24–168 | Based on SLA and storage cost trade-off |

**Immutability**: `retention_in_hours` cannot be changed after stream creation. Changing it requires `terraform apply -replace` (destroy/recreate stream = data loss). The `prevent_destroy = true` lifecycle rule prevents accidental changes.
