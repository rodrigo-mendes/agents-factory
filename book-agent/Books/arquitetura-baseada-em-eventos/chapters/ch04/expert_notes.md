## Expert Review — Delivery Guarantees and Idempotency
Reviewer profile: Senior practitioner, 10+ years, cloud-native microservices and corporate distributed systems
Date: 2026-09-01

---

### At-Most-Once, At-Least-Once, and Exactly-Once Semantics

> **Expert Note:** The prose correctly frames Kafka's exactly-once semantics (EOS) as broker-internal, but understates two production-critical constraints that architects routinely discover too late. First, enabling EOS requires `enable.idempotence=true` plus transactional producers (`transactional.id`) and carries a measurable throughput cost — Confluent benchmarks consistently show 5–15% reduction in write throughput at high load, because each batch requires a two-phase protocol with the broker's transaction coordinator. Second, Kafka EOS is invalidated the moment an external side effect is introduced — but the invalidation is silent. There is no exception, no warning, and no transaction rollback of the external system. Teams that enable EOS on their Kafka clients and then call an HTTP endpoint inside the same handler believe they are protected; they are not. The correct mental model is: EOS = atomic Kafka-offset-commit + atomic Kafka-topic-write, nothing more.

**Integration level:** inline callout
**Priority:** high

---

### Consumer Idempotency and Deduplication Keys

> **Expert Note:** The prose correctly warns that dedup key retention cannot grow without bound, but does not provide the formula for the minimum safe retention window — which is where teams silently introduce data loss. The minimum retention must be: `max_redelivery_window = message_visibility_timeout x max_receive_count`. For SQS with a 12-hour visibility timeout and a max receive count of 10, that is 120 hours minimum. In Kafka, the equivalent is the `retention.ms` of the retry topic multiplied by the maximum consumer restart lag. Teams commonly set a flat 24-hour TTL by intuition. If a Kafka broker lag event holds a message in a retry topic for 36 hours before it is redelivered, the dedup store entry has already expired and the handler reprocesses it as new — a silent, intermittent duplicate with no stack trace.

**Integration level:** inline callout
**Priority:** high

---

### Consumer Idempotency and Deduplication Keys

> **Expert Note:** The dedup store is a stateful dependency and must be designed to the same availability and consistency tier as the primary business database. In practice, teams commonly reach for a shared Redis instance because it is fast, then deploy it without persistence (`appendonly no`) or with a single node. When Redis becomes unavailable — a rolling restart during patching, a sentinel failover — the consumer falls back to processing every message as if it were new. The dedup store silently stops protecting. The minimum production posture is Redis with AOF persistence enabled and a replicated Sentinel or Cluster setup. If the dedup check and the business write are unified in the same relational transaction (as the prose recommends), this concern disappears — which is the strongest argument for the unified-transaction approach over a separate cache.

**Integration level:** collapsed block
**Priority:** medium

---

### Message Ordering and Partitioning

> **Expert Note:** Version-aware idempotency using a monotonically increasing per-entity version number is sound when a single producer owns the entity lifecycle. It breaks down in common multi-producer patterns — for example, when multiple services can independently emit events for the same aggregate (an order updated by both the fulfillment service and the payments service). Coordinating a global sequence counter across producers creates coupling and a distributed coordination problem. The industry-standard solution is to push version enforcement to the database via optimistic locking: the consumer performs a `WHERE current_version = N - 1` conditional update and treats zero-rows-affected as a duplicate or stale event, retrying or discarding accordingly. This is how Axon Framework and EventStoreDB implement sequence enforcement at the aggregate boundary without requiring cross-producer coordination.

**Integration level:** collapsed block
**Priority:** medium

---

### Message Ordering and Partitioning

> **Expert Note:** The partition hotspot problem is understated in discussions of partition key selection, and it is acute in multi-tenant SaaS systems. If the partition key is the tenant ID and a single tenant accounts for 40% of traffic volume (a common enterprise contract pattern), that tenant's events concentrate on one or a few partitions. Consumer group parallelism is bounded by partition count, so hot partitions create a processing bottleneck that no amount of horizontal consumer scaling can resolve without a partition count increase — which requires a Kafka topic rebuild or a repartition stream. Design the partition key at the granularity where order matters (aggregate ID, not tenant ID), and use a separate fan-out mechanism if per-tenant isolation is a requirement.

**Integration level:** collapsed block
**Priority:** medium

---

### The Transactional Outbox Pattern and the Dual-Write Problem

> **Expert Note:** CDC via Debezium is the correct high-throughput choice, but it requires database-level permissions that corporate DBAs frequently restrict and that PaaS offerings (Amazon RDS, Azure Database for PostgreSQL Flexible Server) expose only under specific configurations. Specifically: MySQL binlog access requires the `REPLICATION SLAVE` and `REPLICATION CLIENT` grants, and `binlog_format=ROW` must be set at the server level. PostgreSQL logical replication requires the `REPLICATION` role and a replication slot, and RDS imposes a hard limit of 20 replication slots that counts against all consumers. Teams routinely discover this constraint during UAT or production cutover, not during design. The fallback to polling is always available, but the architectural decision should be made with full knowledge of the permission requirements in the target environment — not deferred to deployment day.

**Integration level:** inline callout
**Priority:** high

---

### The Transactional Outbox Pattern and the Dual-Write Problem

> **Expert Note:** The prose describes the outbox relay as "marking each row as sent," but the two common implementations — soft-delete via a status column versus hard-delete after publish — have meaningfully different operational profiles. Status-column soft-delete preserves the audit trail and allows replay by resetting the status, but the outbox table grows indefinitely and requires a periodic purge job. Hard-delete keeps the table small and fast but makes post-mortem investigation harder because the evidence is gone. A practical middle path used by teams running high-volume outbox patterns is to hard-delete from the outbox table and append to a separate, compacted `outbox_archive` table or object storage sink (S3/GCS) for audit and replay purposes.

**Integration level:** collapsed block
**Priority:** low

---

### Dead-Letter Queues and Retry Policies

> **Expert Note:** The prose correctly distinguishes transient from permanent failures, but omits a production-critical failure mode that sits between the two: the infrastructure-level redelivery that occurs before any application-level retry policy fires. In SQS, if the `VisibilityTimeout` is shorter than the processing time for a message, the broker makes the message visible again while the first consumer is still processing it — causing concurrent dual delivery to two different consumer instances. Neither instance sees an application-level error; both process successfully and both ack. The result is a duplicate that bypasses the dedup store if both reads happen before either write commits. The safe rule is: set `VisibilityTimeout` to at least 6x the P99 processing latency, and monitor the `ApproximateNumberOfMessagesNotVisible` CloudWatch metric to detect concurrent delivery events. In Kafka, the analogous failure is a session timeout causing partition rebalance mid-processing, which re-delivers from the last committed offset.

**Integration level:** inline callout
**Priority:** high

---

## Summary
- Total notes: 8
- High priority (inline callout): 4
- Medium priority (collapsed block): 3
- Low priority (file only): 1

**Top 3 notes to integrate:**

1. [The Transactional Outbox Pattern and the Dual-Write Problem] CDC/Debezium requires database-level replication permissions that are frequently restricted in corporate and PaaS environments — a deployment blocker teams discover too late.
2. [Consumer Idempotency and Deduplication Keys] Dedup key retention window must be calculated from the broker's maximum redelivery window, not set arbitrarily — an arbitrary 24-hour TTL produces silent, intermittent duplicates.
3. [Dead-Letter Queues and Retry Policies] SQS VisibilityTimeout shorter than P99 processing latency causes concurrent dual delivery that bypasses application-level retry logic and the dedup store.
