# Data Modeling Principles — Cross-Type Reference

Universal principles that apply regardless of `DATASTORE_TYPE`. Use as the foundation before applying the type-specific modeling file.

---

## Principle 1: Access-Pattern-First

**Never start from the entity model.** Start from the list of operations the application will run.

```
For each access pattern, document:
  1. Operation type: Read / Write / Read-Write
  2. Frequency: requests/second at peak
  3. Latency SLA: p50/p99 target in milliseconds
  4. Filter/key fields: which fields are used to locate the data
  5. Result shape: single record / list / aggregate / count
  6. Consistency requirement: strong / eventual / monotonic-read / read-your-writes
```

The schema must satisfy the high-frequency, low-latency patterns first. Low-frequency patterns can tolerate slower queries or separate query paths.

---

## Principle 2: Read/Write Ratio Drives Indexing

```
Read-heavy (> 80% reads): bias toward more indexes and denormalization for query performance
Write-heavy (> 50% writes): bias toward fewer indexes; each index adds write overhead
Mixed: identify the 20% of query patterns that drive 80% of the load; optimize those
```

Every index has a cost: **write amplification** — every write must update each index. Document the write amplification factor for each index added.

---

## Principle 3: Consistency vs Availability Trade-off (CAP / PACELC)

```
Strong consistency (CP): every read returns the latest committed write — required for financial, inventory, booking
Eventual consistency (AP): reads may return stale data — acceptable for analytics, social feeds, telemetry
Read-your-writes: a client always sees its own writes — session stores, user profile
Monotonic read: a client never sees older data than it previously read — newsfeed, leaderboard
```

Match the consistency requirement of each access pattern to the consistency guarantee of the chosen datastore and configuration. If the platform cannot provide the required consistency level, flag it.

---

## Principle 4: Data Shape vs Query Shape

Choose whether to optimize for:
- **Write shape** (normalize): store data in its natural entity form — easier to update, harder to query
- **Read shape** (denormalize): store data pre-joined for the query — faster to read, harder to update

The decision depends on the read/write ratio and the flexibility required in query patterns. Datastores without powerful join capabilities (NoSQL, wide-column) force read-shape design.

---

## Principle 5: Schema Evolution Discipline

Every schema change must be classified before execution:

| Change | Backward Compatible | Forward Compatible | Online? |
|---|---|---|---|
| Add nullable field / new column | ✅ (old code ignores) | ❌ (old code won't send) | Usually yes |
| Remove field | ❌ (old code may depend) | ✅ | Risky — two-phase: deprecate first |
| Rename field | ❌ | ❌ | No — requires alias period |
| Change type (e.g., int → bigint) | Depends | Depends | Risky — data migration required |
| Add required field | ❌ | ❌ | No — existing records invalid |
| Add index | ✅ | ✅ | Yes (build in background) |
| Remove index | ✅ | ✅ | Yes |

**Expand-Contract pattern** for safe non-compatible changes:
1. Expand: add the new field alongside the old field
2. Migrate: backfill new field; update code to write both; then read from new
3. Contract: remove the old field when no code reads it

---

## Principle 6: Avoid Premature Optimization

```
Do not add indexes speculatively — add them when a slow query exists and EXPLAIN confirms a missing index
Do not partition until table size warrants it (RDBMS: > 100M rows; columnar: > 1TB)
Do not denormalize until JOIN cost is proven to be the bottleneck by profiling
Do not add read replicas until the primary is CPU/IO-bound on reads
```

---

## Principle 7: Document the Model

Every schema must be accompanied by:
- Entity-Relationship Diagram (ERD) or equivalent (RDBMS, document, graph)
- Access pattern table (from Principle 1)
- Index inventory with write amplification estimate
- Schema versioning / migration log

---

## Anti-Patterns (Cross-Type)

| Anti-Pattern | Type | Consequence | Correct Alternative |
|---|---|---|---|
| Modeling the entity, not the query | All types | Schema doesn't match access patterns; queries are slow | Start from the access pattern list |
| Adding indexes for all columns | All types | Write amplification; storage overhead | Index only high-selectivity columns in WHERE/JOIN/ORDER BY |
| Ignoring data growth | All types | Performance degrades as data grows | Estimate growth over 12 months; design for that volume |
| Mutable records in append-only stores | Streaming, wide-column | Updates are expensive or semantically wrong | Use immutable events + materialized read model |
| Using one datastore for all access patterns | All types | Forcing every pattern into one model degrades at least some | Polyglot persistence: primary store + read replica + cache |
