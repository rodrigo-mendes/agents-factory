# Ask First Decisions — OCI Event-Driven Pub/Sub Architecture

Present these options to the user, explain trade-offs, and wait for a decision before producing architecture diagrams or delegating implementation.

---

## Decision 1 — Consumer Variant

**Ask**: "When the consumer receives an event, where does the data go — an external REST API, a database, or another event bus/stream?"

| Option | Variant | Java Project | Target | When to Use |
|--------|---------|-------------|--------|-------------|
| REST Consumer | 02a | `func-event-consumer-rest` | External HTTP/REST API | Notify partner systems, trigger ERP actions, webhook delivery |
| Database Consumer | 02b | `func-event-consumer-ords` / `func-event-consumer-jdbc` | ORDS or JDBC (Autonomous DB) | Materialize events, audit log, projections, read models |
| Event Chain | 02c | `func-event-consumer-chain` | Another stream, Queue, or ONS | Pipeline composition, fan-out between domains, event transformation |
| Custom | N/A | New project | Any | Multiple targets or non-standard integration |

**Implications by variant**:

| Concern | 02a REST | 02b DB | 02c Chain |
|---------|----------|--------|-----------|
| IAM extras | `read secret-bundles` (API key in Vault) | `read secret-bundles` (DB password in Vault) | `use stream-push` or `use ons-topics` |
| Network | NAT GW (external HTTP) | Service GW (ORDS) or private DB endpoint | Service GW (Streaming) |
| Idempotency | `Set<event_id>` check before HTTP call | Unique constraint on `event_id` column | Pass `event_id` downstream |
| Error handling | Retry on 5xx; skip on 4xx; log failures | Catch duplicate key; log and skip | Retry on publish failure |

**Pattern docs**: [02a](docs/patterns/02-event-driven/02a-event-driven-rest-consumer.md), [02b](docs/patterns/02-event-driven/02b-event-driven-database-consumer.md), [02c](docs/patterns/02-event-driven/02c-event-driven-event-chain.md)

---

## Decision 2 — Stream Pool Type (PUBLIC vs PRIVATE)

**Ask**: "Is the Service Connector Hub the only consumer reading the stream, or will in-VCN Kafka clients (functions, microservices) also read from it directly?"

| Option | Config | SCH as Source | In-VCN Kafka Client | When to Choose |
|--------|--------|--------------|---------------------|----------------|
| **PUBLIC** (recommended for SCH) | No `private_endpoint_settings` | YES — SCH reaches Oracle-managed endpoint | YES — via NAT or Service GW | Any architecture where SCH sources the stream |
| **PRIVATE** | `private_endpoint_settings { subnet_id, nsg_ids }` | NO — SCH is outside VCN, cannot reach private IP | YES — in-VCN functions reach private endpoint | Only when SCH is NOT used; consumers are warm in-VCN Kafka clients |

**Critical constraint**: This decision is **immutable** — `private_endpoint_settings` cannot be changed after pool creation without destroy/recreate (data loss, OCID rotation). All consumers of the stream OCID (producer config, SCH source configs, IAM) must be re-pointed after recreation.

**If the use case is "SCH + in-VCN Kafka clients simultaneously"**: Use a PUBLIC pool. In-VCN functions can reach the public messages endpoint via NAT Gateway; the security model shifts from network-level (private endpoint) to IAM + TLS.

---

## Decision 3 — SCH Cold-Start Mitigation

**Ask**: "What is the maximum tolerable cold-start latency, and is there budget for always-warm containers?"

| Option | Cold Start | Cost | Complexity | When to Choose |
|--------|-----------|------|-----------|----------------|
| **timeout=300s + memory=1024MB** | ~60 s (first delivery on cold container) | Lowest — pay-per-use | Zero extra | Default for most use cases; cold delivery completes (not aborted) |
| **Provisioned Concurrency** | ~0 s (always warm) | High — minimum 10 containers (not 1; platform constraint) per function | Low | SLA requires zero cold-start penalty; budget approved for always-on cost |
| **GraalVM native image** | ~2-5 s | Moderate — build pipeline cost | High — native compilation | Cold start must be < 10 s; willing to invest in build-time AOT |
| **Async decouple** | N/A — SCH no longer invokes Function directly | Variable | High — architecture change | Cold-start problem cannot be solved with runtime config; decouples sync deadline |

**Provisioned Concurrency caveat**: OCI Functions requires PC count to be a multiple of 10. `count = 1` is REJECTED with `400 InvalidParameter: Count must be a multiple of 10`. Minimum viable PC = 10 containers per function. For 2 consumer functions = 20 always-on 1024 MB containers.

**Evidence**: `docs/handoff/event-pubsub/deploy-report.md` cycles 3b-6 (memory+timeout tried and confirmed insufficient at 256 MB; 1024 MB + 300 s unblocked at cycle 10); `diagnosis-report.md` (55 s platform pre-main gap, not reducible by memory alone at the scale of the SCH deadline).

---

## Decision 4 — Cursor Strategy (LATEST vs TRIM_HORIZON)

**Ask**: "If the SCH connector goes INACTIVE and is later reactivated, should it process missed messages or start fresh?"

| Option | `cursor_kind` | Behavior | Risk | When to Choose |
|--------|--------------|----------|------|----------------|
| `LATEST` | `LATEST` | Reads only new messages after activation | Missed messages during INACTIVE are permanently lost | Alerting, notifications — historical data not needed; duplicates are disruptive |
| `TRIM_HORIZON` | `TRIM_HORIZON` | Reads from oldest retained message (up to 7 days) | Reactivation replays ALL retained data — downstream must be fully idempotent | Audit, compliance, data materialization — no tolerance for gaps |

**Operational implication**: With `TRIM_HORIZON`, any SCH deactivation/reactivation cycle (maintenance, forced-replace, pool recreation) replays up to 7 days of events. All consumers must handle replay correctly — idempotency by event_id is mandatory.

---

## Decision 5 — Fan-Out Topology (Scale of Consumers)

**Ask**: "How many independent consumers will read from this stream, and do they all need the same data?"

| Option | Pattern | When |
|--------|---------|------|
| **N SCH connectors** (parallel fan-out) | 1 stream → N `oci_sch_service_connector` → N functions | 2-5 consumers, all receive same data, different actions (notify + audit + DB) |
| **Stream hub** (fan-out via intermediate stream) | 1 SCH → enrichment function → N output streams → N SCH → N consumers | 5+ consumers OR different subsets of data per consumer OR different retention needs |
| **In-VCN Kafka consumer group** | Functions or VMs directly consume stream via Kafka protocol | Warm, long-lived consumers; sub-second latency needed; SCH overhead unwanted |

**Note on parallel SCH connectors**: Each connector independently advances its cursor. 3 connectors = 3x the OCI Streaming read throughput cost (billed per read operation). For a small number of consumers this is negligible.
