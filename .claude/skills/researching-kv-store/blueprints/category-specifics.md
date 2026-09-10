# Key-Value Store — Neutral Category Specifics

Patterns for persistent key-value stores used as a primary datastore. Vendor-specific config keys and commands live in `references/<vendor>-<version>.md`.

---

## Cache vs Primary-Datastore Distinction

This sibling covers KV stores as a **primary datastore** — data must survive restart and must not be silently evicted. If the platform is deployed as an ephemeral cache, use `researching-cache-store` instead.

| Dimension | Cache (`researching-cache-store`) | Primary KV (this sibling) |
|---|---|---|
| Data loss on eviction | Acceptable | Unacceptable |
| Persistence | Optional | Mandatory |
| Eviction policy | LRU/LFU | no-eviction |
| Backup rigor | Low | High (RDBMS-level) |

---

## Storage Engine Model (Neutral)

| Concept | What to research per engine |
|---|---|
| Storage structure | LSM-tree (RocksDB, TiKV) vs B+tree (LMDB) vs in-memory+persistence (Redis) |
| Durability mechanism | WAL / AOF / snapshot / memory-mapped file |
| Compaction | LSM compaction strategy + tuning (RocksDB, TiKV) |
| Write amplification | Inherent to LSM; tune compaction to balance |
| Read path | Bloom filters, block cache, memtable → SST levels |

---

## Durability Modes (Neutral)

| Mode | Data loss window (RPO) | Performance | Use When |
|---|---|---|---|
| Sync every write (fsync-always) | Zero | Slowest | Financial / cannot lose any write |
| Sync periodically (e.g., every 1s) | ~1 second | Balanced | Most primary-datastore workloads |
| OS-buffered (no explicit fsync) | Until OS flushes (seconds+) | Fastest | Only when data is reconstructible |
| Snapshot-only | Since last snapshot | Fast writes, coarse recovery | Point-in-time acceptable; combine with WAL |

Most engines combine a WAL (fine-grained durability) with periodic snapshots (fast recovery). Document the exact combination and its RPO.

---

## HA Topologies (Neutral)

1. **Failover pair** — primary + replica; automatic failover (via sentinel/orchestrator); data fits in one node
2. **Sharded cluster** — data distributed across nodes by key hash / range; each shard replicated; horizontal scale
3. **Distributed consensus (TiKV)** — Raft groups per data range; strong consistency; horizontal scale
4. **Single node + backup** — dev/test only

---

## Key Design (Neutral)

Detailed guidance in [data-modeling.md](./data-modeling.md). Neutral summary:

- Namespace keys hierarchically (`entity:id:attribute`)
- Avoid generic keys; encode entity type + identity
- Keep keys short (memory overhead per key)
- Choose the right value structure (string/hash/list/set/sorted-set for Redis; opaque bytes for RocksDB/LMDB)
- Set TTL only where expiration is a business requirement — never as an eviction crutch for a primary datastore

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Memory / storage usage | Capacity | approaching limit |
| Persistence lag (WAL fsync, snapshot age) | Durability health | last snapshot / fsync too old |
| Replication offset lag | Replica health | growing |
| Command latency p99 | Query health | > single-digit ms |
| Compaction pending / stalls (LSM) | Write health | stalls indicate compaction can't keep up |
| Connected clients | Pool pressure | approaching limit |
| Keyspace size | Growth | trend |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Eviction enabled on primary datastore | Silent data loss | no-eviction; scale storage/memory |
| Persistence off on primary datastore | Total loss on restart | Enable WAL/AOF/snapshot |
| Storing huge values (>1MB) | Memory fragmentation; slow ops | Split or store blob in object storage + reference |
| Key explosion (per-request keys, no TTL) | Unbounded memory growth | Aggregate; bound key cardinality |
| Full keyspace scan in production | Blocks single-threaded engines | Cursor-based scan |
| No auth on network-accessible port | Full data exposure | Auth + restricted bind |

---

## §Data Modeling

Full guidance: [data-modeling.md](./data-modeling.md). Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Ecosystem Adjacencies (neutral; names in reference cards)

- Client libraries per language
- Sharding proxy / router
- Backup tooling
- Monitoring exporters (Prometheus per vendor)
