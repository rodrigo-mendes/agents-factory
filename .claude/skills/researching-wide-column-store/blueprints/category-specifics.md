# Wide-Column Store — Neutral Category Specifics

Patterns for wide-column databases. Vendor-specific config keys, CQL/HQL dialect, and compaction names live in `references/<vendor>-<version>.md`.

---

## Ring / Distribution Model (Neutral)

| Concept | What to research per engine |
|---|---|
| Partitioning | Consistent hashing (Cassandra/Scylla token ring) vs region splits (HBase) |
| Replication | Replication factor per keyspace/DC; replica placement strategy |
| Consistency level | Tunable per operation (ONE / QUORUM / LOCAL_QUORUM / ALL) |
| Node roles | Peer-to-peer (Cassandra/Scylla — no master) vs master-region-server (HBase) |
| Repair | Anti-entropy repair to reconcile replicas |
| Compaction | Strategy selection based on workload |

---

## Consistency Level (Neutral)

Wide-column stores offer tunable consistency per read and per write:

| Level | Meaning | Trade-off |
|---|---|---|
| ONE | One replica responds | Fast; may read stale/lose write on node loss |
| QUORUM | Majority of replicas | Balanced; strong consistency when R+W > RF |
| LOCAL_QUORUM | Majority within local DC | Multi-DC: avoids cross-DC latency |
| ALL | All replicas | Strongest; fails if any replica down |

**Strong consistency rule**: `read_CL + write_CL > replication_factor` guarantees read-after-write (e.g., QUORUM read + QUORUM write with RF=3).

---

## Compaction Strategy Selection (Neutral)

| Strategy | Best For | Trade-off |
|---|---|---|
| Size-Tiered (STCS) | Write-heavy, few deletes | Poor read amplification; slow tombstone cleanup |
| Leveled (LCS) | Read-heavy, many updates | Higher write amplification; predictable reads |
| Time-Window (TWCS) | Time-series with TTL, append-only | Efficient TTL expiry; bad for updates |

Choose based on the read/write/TTL profile from `WORKLOAD_PROFILE`.

---

## Tombstones & Deletes (Neutral)

Wide-column stores mark deletes as tombstones (not immediate removal):

- Tombstones persist until `gc_grace_seconds` (default often 10 days) to prevent deleted data resurrection
- High-volume deletes create tombstone floods → read queries scan tombstones → latency degradation
- **Prefer TTL over explicit DELETE** — TTL expiry is more compaction-friendly
- Run repair before `gc_grace_seconds` expires to avoid resurrecting deleted data

---

## HA & Multi-DC (Neutral)

- Peer-to-peer engines (Cassandra/Scylla): no single point of failure; any node handles any request (coordinator)
- Replication factor per datacenter via topology-aware strategy
- Local-quorum reads/writes avoid cross-DC latency while maintaining consistency
- Hinted handoff: coordinator stores writes for temporarily-down replicas (bounded window)

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Read/write latency p99 (coordinator + replica) | Query health | > SLA |
| Pending compactions | Compaction keeping up | growing backlog |
| Tombstone scanned per read | Delete-pattern health | high count → tombstone flood |
| Partition size (max) | Hot/large partition detection | > recommended max (e.g., 100MB) |
| Dropped mutations | Overload signal | non-zero |
| Repair status/age | Consistency health | overdue repair |
| Hinted handoff pending | Replica availability | growing |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Low-cardinality partition key | Hot partition; one node overloaded | High-cardinality key; bucket suffix |
| Unbounded partition | Slow reads; imbalance | Time-bucket partition key; TTL |
| Tombstone flood (high delete rate) | Read latency degradation | TTL instead of DELETE; tune gc_grace |
| ALLOW FILTERING | Full-partition/cluster scan | New table per query pattern |
| Entity-first modeling | Queries need scans | Query-first: one table per query |
| Secondary index on high-cardinality column | Distributed fan-out | Materialized view or dedicated table |

---

## §Data Modeling

Full guidance: [data-modeling.md](./data-modeling.md). Core principle: **query-first — one table per access pattern, data duplication is intentional.** Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Ecosystem Adjacencies (neutral; names in reference cards)

- Repair automation (Reaper for Cassandra)
- Backup tooling (Medusa, nodetool snapshot, cbbackup)
- Driver libraries per language
- Monitoring exporters (Prometheus per vendor)
- Migration tooling
