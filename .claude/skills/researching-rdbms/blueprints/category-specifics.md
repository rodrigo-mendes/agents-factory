# RDBMS — Neutral Category Specifics

Patterns for relational / NewSQL databases. Vendor-specific config keys, tools, and SQL dialect quirks live in `references/<vendor>-<version>.md`.

---

## Storage & Concurrency Model (Neutral)

| Concept | What to research per engine |
|---|---|
| Concurrency control | MVCC (PostgreSQL, CockroachDB) vs undo-log MVCC (MySQL InnoDB) — how readers/writers avoid blocking |
| Isolation levels | Which levels the engine supports; the default; anomalies possible at each |
| Storage layout | Heap (PostgreSQL) vs clustered index (MySQL InnoDB) — impacts primary-key choice |
| WAL / redo log | Durability mechanism; sync mode; sizing; archiving for PITR |
| Dead tuple / undo cleanup | Vacuum (PG) vs purge (MySQL) — bloat management |
| Checkpoints | How dirty pages are flushed; tuning for write bursts |

---

## Isolation Level Decision (Neutral)

| Level | Prevents | Still allows | Cost |
|---|---|---|---|
| Read Uncommitted | — | dirty reads | lowest |
| Read Committed | dirty reads | non-repeatable reads, phantoms | low (common default) |
| Repeatable Read | + non-repeatable reads | phantoms (engine-dependent) | medium |
| Serializable | + phantoms, write skew | — | highest (may abort on conflict) |

Document the engine's default and the anomalies the application must tolerate or defend against (idempotency, retries on serialization failure).

---

## HA & Replication (Neutral Topologies)

1. **Primary + async standby** — lowest latency; standby may lag; failover risks losing the lag window
2. **Primary + sync standby** — zero data loss on failover; write latency includes standby ack
3. **Primary + multiple standbys (read scaling)** — reads distributed to standbys; watch replication lag for read-your-writes
4. **Multi-primary / distributed consensus (NewSQL)** — all nodes accept writes via Raft/Paxos; horizontal scale; higher write latency
5. **Orchestrated cluster** — external orchestrator (Patroni/Orchestrator) manages leader election + automatic failover

For each: document minimum node count, failover trigger, split-brain fencing, and read-consistency implications.

---

## Connection Pooling (Neutral)

Every RDBMS has a per-connection memory + CPU cost. At scale:

- **Client-side pool** — application maintains a bounded connection pool
- **External pooler** — a dedicated process multiplexes many client connections onto few DB connections
- **Pool modes** — session (1:1 for the session), transaction (release after each txn — most efficient), statement (release after each statement)

Sizing: `db_max_connections ≈ RAM / per_connection_overhead`; pooler pool size distributed across app servers.

---

## Indexing (Neutral Principles)

Detailed guidance in [data-modeling.md](./data-modeling.md). Neutral summary:

- Index only columns used in WHERE / JOIN / ORDER BY with high selectivity
- Every index adds write amplification — one extra I/O per write per index
- Composite index column order: equality columns first, then range, then sort
- Covering indexes enable index-only scans (no heap fetch)
- Partial / filtered / expression indexes reduce index size for specific patterns

---

## Partitioning (Neutral)

Partition a table when it exceeds the engine's practical single-table size or when bulk-delete of old data is needed:

| Strategy | Use Case |
|---|---|
| Range | Time-series / monotonic key (monthly partitions) |
| List | Fixed discrete values (country, status) |
| Hash | Even distribution with no natural partition key |

Rule: include the partition key in queries for partition pruning; avoid low-cardinality skewed keys (hot partitions).

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Active connections / max | Connection pressure | approaching max |
| Query latency p99 | Query health | > SLA |
| Transactions per second | Throughput baseline | anomaly |
| Cache/buffer hit ratio | Memory effectiveness | < ~0.99 for OLTP |
| Replication lag | Standby health | > threshold (seconds) |
| Checkpoint / flush time | Write-burst handling | long stalls |
| Dead tuples / bloat (PG) or history list length (MySQL) | Cleanup health | growing unbounded |
| Deadlocks per interval | Concurrency contention | spike |
| Long-running / idle-in-transaction queries | Lock holders | > threshold duration |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| SELECT N+1 | O(n) round trips | JOIN or batched WHERE id IN (...) |
| Over-indexing | Write amplification; bloat | Index only high-selectivity WHERE/JOIN/ORDER BY columns |
| No connection pooling | Connection exhaustion | PgBouncer / ProxySQL / built-in pooler |
| Missing vacuum/purge tuning | Bloat → seq scans | Tune for hot tables |
| Unbounded transaction / idle-in-transaction | Holds locks; blocks vacuum | Bound transaction scope; timeout idle txns |
| Single node in production | No HA | Primary + standby with failover |
| DDL on huge table without online tool | Long lock; outage | pg_repack / gh-ost / pt-osc |
| Backup without restore test | Unrecoverable on disaster | Verified restore drill |

---

## Ecosystem Adjacencies (neutral; names in reference cards)

- Connection pooler (PgBouncer, ProxySQL)
- HA orchestrator (Patroni, Orchestrator, built-in)
- Backup tooling (pgBackRest, Barman, Percona XtraBackup, mysqldump)
- Online schema migration (pg_repack, gh-ost, pt-online-schema-change)
- Monitoring exporters (postgres_exporter, mysqld_exporter)
- Logical replication / CDC (Debezium, native logical replication)
