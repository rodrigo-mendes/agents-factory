# Wide-Column Data Modeling

For `DATASTORE_TYPE=wide-column`. Platforms: Apache Cassandra, ScyllaDB, HBase.

---

## Query-First Design Process

Wide-column databases (CQL/HQL) do NOT support arbitrary WHERE clauses. Every table is designed for ONE specific query pattern.

```
Step 1: List all queries the application will run
Step 2: For each query, create one table
Step 3: Tables can duplicate data — this is intentional and correct
Step 4: Choose partition key → clustering columns for each table
```

---

## Partition Key Design

The partition key determines which node holds the data. Design rules:

| Rule | Rationale |
|---|---|
| High cardinality (millions+ distinct values) | Data distributed evenly across nodes |
| Avoid monotonically increasing keys (time, sequential ID) as sole partition key | All writes go to the same token — hot partition |
| Avoid low-cardinality keys (country, status with 5 values) | Too few partitions — uneven distribution |
| Partition size < 100MB | Large partitions slow reads; Cassandra recommends < 100MB |
| Bucket if needed | Composite: (user_id, bucket_id) where bucket_id = date or hash % N |

### Hot Partition Detection

```bash
# Cassandra — check partition sizes
nodetool tablehistograms keyspace.table | grep "Partition Size"

# ScyllaDB — REST API
curl http://localhost:10000/column_family/metrics/estimated_sstable_count/keyspace/table

# Alert threshold: any partition > 100MB
```

---

## Clustering Columns

Clustering columns define the sort order of rows WITHIN a partition:

```cql
-- Table for: "Get the last 10 messages for a conversation"
CREATE TABLE messages_by_conversation (
    conversation_id UUID,          -- partition key: routes to node
    sent_at         TIMEUUID,      -- clustering: sorted DESC within partition
    message_id      UUID,
    sender_id       UUID,
    body            TEXT,
    PRIMARY KEY (conversation_id, sent_at)
) WITH CLUSTERING ORDER BY (sent_at DESC);

-- This table answers EXACTLY this query efficiently:
SELECT * FROM messages_by_conversation WHERE conversation_id = ? LIMIT 10;

-- It does NOT efficiently answer:
-- "Get all messages from sender_id X" → requires a separate table
```

---

## Data Duplication is Intentional

Wide-column modeling requires storing the same data in multiple tables to serve different query patterns:

```
Table 1: messages_by_conversation  (for "show conversation history")
Table 2: messages_by_sender        (for "show all messages from a user")
Table 3: unread_messages_by_user   (for "show unread count per user")

All three tables may contain overlapping data. This is correct — it avoids ALLOW FILTERING.
Trade-off: writes must update all three tables; use batch for atomicity within a partition.
```

---

## TTL Strategy

Wide-column databases excel at automatic expiration:

```cql
-- Set TTL at write time (preferred — per-record TTL)
INSERT INTO sensor_readings (sensor_id, time, value)
VALUES (?, ?, ?) USING TTL 604800;  -- 7 days in seconds

-- Set default TTL at table level
CREATE TABLE sensor_readings (...)
WITH default_time_to_live = 604800;  -- 7 days

-- After TTL expires, rows become tombstones → deleted on compaction
-- High tombstone density degrades read performance → tune gc_grace_seconds
```

---

## Compaction Strategy Selection

| Strategy | Best For | Trade-off |
|---|---|---|
| STCS (Size-Tiered) | Write-heavy; no deletes/TTL | Poor for reads; worst for tombstone cleanup |
| LCS (Leveled) | Read-heavy; many random reads | Higher write amplification; predictable read performance |
| TWCS (Time-Window) | Time-series data with TTL; append-only | Low write amplification; bad for updates |
| ICS (Incremental — ScyllaDB) | General purpose; default in ScyllaDB | Balanced; fewer compaction peaks |

---

## Schema Evolution in Wide-Column

```
Safe changes (online, non-breaking):
  + Add column: always safe — old rows return null for new column
  + Add table: always safe
  + Change column comment: no-op

Risky changes (require careful planning):
  - Remove column: old clients may still write to it; mark deprecated first
  - Change column type: NOT supported in place — add new column + migrate + drop old
  - Change primary key: NOT supported — must create new table + migrate data
  - Change clustering order: NOT supported — new table required

Pattern for changing primary key:
  1. Create new table with desired schema
  2. Dual-write to both tables
  3. Backfill old data to new table
  4. Switch reads to new table
  5. Remove old table
```
