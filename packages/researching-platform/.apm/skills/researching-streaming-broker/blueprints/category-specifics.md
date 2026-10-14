# Streaming & Messaging — Neutral Category Specifics

Patterns and decisions that apply to every streaming/messaging broker regardless of vendor. Vendor-specific parameter names, exact commands, and CR fields live in `references/<vendor>-<version>.md`.

---

## Broker Roles & Terminology (Neutral Vocabulary)

Every broker in this family exposes the same conceptual model, even if the vocabulary differs:

| Neutral concept | What it means | Ask the reference card for |
|---|---|---|
| Producer | Publishes records/messages | The client library name and config for durability level |
| Consumer | Subscribes and processes records/messages | Delivery guarantee configuration; acknowledgment mode |
| Topic / queue / stream | The named channel producers write to and consumers read from | The exact naming rules, character limits, deletion behavior |
| Partition / shard / segment | The unit of parallelism within a topic | Whether the broker allows repartitioning without downtime |
| Consumer group / subscription | Coordination mechanism so each record is processed by one consumer of a group | The group offset storage location and TTL |
| Replica | Copy of the data for HA | The replication mode (sync/async/quorum) and consistency level |
| Retention policy | When records are removed from the broker | Time-based / size-based / compacted / never |

---

## Delivery Guarantee Selection

The broker's supported guarantees are documented in its reference card. The choice depends on the application's tolerance:

| Guarantee | Producer behavior | Consumer behavior | When acceptable |
|---|---|---|---|
| At-most-once | Fire-and-forget; no ack wait | Commit offset before processing | Metrics, telemetry — data loss on failure is OK |
| At-least-once | Wait for broker ack (durable); retry on failure | Commit offset after processing | Most business events — idempotent consumers required to avoid duplicates |
| Exactly-once | Broker-supported transactional producer + consumer idempotency key | Transactional offset commit | Financial ledgers, inventory — requires broker + client library support |

**Rule**: state the target guarantee explicitly for every producer/consumer pattern. If the broker cannot support the required guarantee natively (e.g., exactly-once), document the application-level workaround (dedup key + idempotent write).

---

## Ordering Guarantees

| Scope | Where ordering holds | Where it does NOT |
|---|---|---|
| Single-partition/queue ordering | Within one partition (or one queue in a queue-per-consumer model) | Across partitions of the same topic |
| Global ordering | Only with a single partition — sacrifices parallelism | Anything above 1 partition |
| Session ordering | Records with the same session key routed to same partition | Between different session keys |

**Design implication**: choose the partition key based on the entity whose event order matters (user_id, order_id, tenant_id). Never partition by timestamp — collapses parallelism to one partition per time window.

---

## HA Topology Neutral Model

Every broker offers some form of the following topologies; the reference card names the vendor-specific implementation:

1. **Single-node** — dev/test only; no HA
2. **Primary-replica (leader-follower)** — one writer, N read replicas; failover requires promotion
3. **Quorum-based (consensus)** — N-node cluster with majority-quorum writes; automatic leader election
4. **Sharded / partitioned cluster** — data distributed across nodes; each shard has its own quorum
5. **Geo-replication (federation / mirror-maker / built-in)** — cross-datacenter async replication for DR

For each topology chosen, the research MUST document:
- Minimum node count (odd numbers for quorum: 3, 5, 7)
- Automatic vs manual failover trigger
- Data loss scenarios and their probability
- Split-brain risk and mitigation
- Backup interaction (can you backup during failover?)

---

## Backpressure & Flow Control

All brokers face the pattern: producer produces faster than consumer consumes. Neutral handling:

- **Broker-side buffering** — accumulates messages until retention limit or memory alarm
- **Consumer-side pull vs broker-side push** — pull-based (Kafka, Pulsar consumer) is naturally back-pressured; push-based (RabbitMQ classic mode) requires `prefetch-count` limit
- **Overflow policy** — block producers / reject with error / drop messages — the reference card names the exact config

---

## Dead Letter Handling

Neutral pattern for messages that repeatedly fail processing:

1. Consumer detects processing failure (exception, timeout, poison pill)
2. After N retries (config parameter, per-message TTL, or delivery-count check), route the message to a **dead-letter queue/topic/DLQ**
3. Operator alerts on DLQ growth > threshold
4. Investigation & reprocessing tooling documented in the reference card

---

## Neutral KPIs (all brokers)

Every broker should expose (or via exporter):

| Neutral metric | Purpose | Reference card provides |
|---|---|---|
| Producer publish rate | Ingest rate | Exact metric name + exporter |
| Consumer processing rate | Drain rate | Exact metric name + exporter |
| Consumer lag / backlog | Health of consumer keeping up | Metric name; lag calculation |
| Under-replicated partition/queue count | Replication health | Exact metric name; alert threshold |
| Leader election / re-election count | Cluster stability signal | Metric name |
| Disk usage per broker | Retention / capacity signal | Metric name |
| In-flight request count | Broker load signal | Metric name |
| Consumer group / subscription count | Discovery / cardinality health | Metric name |

Alert thresholds are workload-specific — see the sibling's evaluation-scenarios for guidance.

---

## Universal Anti-Patterns (all brokers)

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Strong producer ack setting with quorum = 1 | Illusion of durability — single node loss = data loss | Pair strong ack with quorum size that survives one node failure |
| Auto-commit consumer offsets before processing | Message skipped on consumer crash → data loss | Commit offset after successful processing (manual commit) |
| Unbounded consumer lag without alerting | Consumer falls behind silently; backlog grows | Alert on lag > threshold; add consumers or scale processing |
| Message payload without schema versioning | Consumer breaks on producer schema change | Use a schema registry or embed version field in payload |
| No dead-letter queue for poison pills | Bad message blocks the entire partition/queue | Route to DLQ after N retries; monitor DLQ growth |
| Cross-DC replication without an SLA | Async replication lag hidden until DR event | Measure replication lag; alert; test failover regularly |
| Publishing without idempotency key when using at-least-once | Duplicate records processed multiple times | Producer sets a message-level idempotency key; consumer deduplicates |

---

## Ecosystem Adjacencies

Neutral list of concerns often paired with a streaming broker; the reference card names the specific tools per vendor:

- **Schema registry** (evolving message contracts)
- **Connector framework** (source/sink integrations to databases, cloud storage)
- **Stream processing engine** (in-broker windowed aggregations, joins)
- **Mirror / geo-replicator** (cross-DC async replication)
- **Management UI** (topic/queue browsing, consumer lag monitoring)
- **Client libraries per language** (with version compatibility matrix per broker version)
