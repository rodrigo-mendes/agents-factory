# Document Store — Neutral Category Specifics

Patterns for document databases. Vendor-specific config keys, query language, and index types live in `references/<vendor>-<version>.md`.

---

## Document Model (Neutral)

| Neutral concept | What to research per engine |
|---|---|
| Document | Serialization format (BSON/JSON), size limit, nesting depth |
| Collection / bucket | Container of documents; schema flexibility; validation options |
| Index types | Single-field, compound, multikey/array, text, geo, wildcard, partial |
| Replica / quorum | Replica-set / cluster model; write concern; read concern |
| Sharding | Shard key selection; chunk/vbucket distribution; balancer |
| Consistency | Tunable read/write concern; causal consistency; transactions scope |

---

## Durability & Consistency (Neutral)

Every document DB exposes tunable durability and read consistency. Research per engine:

- **Write durability level** — acknowledge on primary only vs majority of replicas vs journal-flushed
- **Read consistency level** — read from primary (latest) vs secondary (may lag) vs majority-committed vs linearizable
- **Causal consistency** — read-your-writes / monotonic-reads guarantees within a session
- **Transaction scope** — single-document atomicity (always) vs multi-document transactions (cost + limits)

Rule: match the durability/consistency level to each access pattern's requirement (see [data-modeling.md](./data-modeling.md)).

---

## HA Topologies (Neutral)

1. **Replica set / replica group** — one primary + N secondaries; automatic failover on primary loss; minimum 3 members (odd for election quorum)
2. **Sharded cluster** — data partitioned by shard key across multiple replica sets; router tier + config metadata
3. **Standalone** — dev/test only; no HA

For sharded clusters, document: shard key choice, chunk/balancer behavior, cross-shard query cost, and the router/config-server topology.

---

## Sharding Key Selection (Neutral)

The shard key is the most consequential decision in a sharded document DB:

| Property | Requirement |
|---|---|
| Cardinality | High — many distinct values for even distribution |
| Frequency | No single value dominates (avoids hot shard) |
| Monotonicity | Avoid monotonically increasing keys (all writes hit the newest shard) |
| Query alignment | Common queries should include the shard key (avoid scatter-gather) |

Compound or hashed shard keys mitigate monotonic-key hot spots.

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Operations per second (by type) | Throughput baseline | anomaly |
| Replication lag | Secondary health | > threshold |
| Connections | Pool pressure | approaching limit |
| Cache usage (working set) | Memory effectiveness | working set > RAM → page faults |
| Page faults / disk reads | Memory pressure | rising |
| Replication oplog/window | Recovery window | shrinking below safe threshold |
| Query targeting (scanned vs returned) | Index effectiveness | high scan:return ratio |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Standalone in production | No HA | 3+ member replica set |
| Unbounded array in a document | Hits size limit; slow rewrites | Reference or bucket pattern |
| No schema validation | Invalid data silently stored | Collection-level JSON Schema validation |
| Missing shard key in queries (sharded) | Scatter-gather to all shards | Include shard key in common queries |
| Multi-document transactions in hot path | Latency; defeats document model | Redesign for single-document atomicity |
| Default auth off | Full data exposure | Enable auth + least-privilege roles |
| Monotonic shard key | Hot shard on newest range | Hashed or compound shard key |

---

## §Data Modeling

Full guidance: [data-modeling.md](./data-modeling.md). Core principle: **embed data accessed together; reference data accessed independently or that grows unboundedly.** Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Ecosystem Adjacencies (neutral; names in reference cards)

- Query router / connection proxy (mongos, Couchbase SDK gateway)
- GUI client (Compass, Couchbase Web Console, RavenDB Studio)
- Backup tooling (Percona Backup for MongoDB, mongodump, cbbackupmgr)
- Change data capture (change streams, Debezium)
- Monitoring exporters (Prometheus per vendor)
