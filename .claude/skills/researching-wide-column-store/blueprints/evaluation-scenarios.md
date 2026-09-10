# Evaluation Scenarios — researching-wide-column-store

Cross-vendor coverage required: at least one Cassandra scenario AND at least one ScyllaDB or HBase scenario.

---

## Scenario 1 — Cassandra on Kubernetes (K8ssandra)

**Input**:
```
/researching-wide-column-store Apache Cassandra 5.0 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Recommends K8ssandra Operator
- Documents RF=3 + LOCAL_QUORUM as production baseline
- Query-first data modeling: partition key cardinality, clustering columns, one-table-per-query
- Compaction strategy selection (STCS/LCS/TWCS) based on workload
- Tombstone / gc_grace_seconds discussion; TTL over DELETE
- Repair automation (Reaper)
- References `blueprints/references/cassandra-5.0.md`

**must_not**:
- Recommend entity-first modeling
- Recommend ALLOW FILTERING for production queries
- Use even RF without noting quorum math

---

## Scenario 2 — ScyllaDB on VM

**Input**:
```
/researching-wide-column-store ScyllaDB 6.0 deployment=vm depth=standard
```

**must_pass**:
- Notes ScyllaDB is Cassandra-compatible (CQL) but C++ / shard-per-core architecture (different tuning)
- Documents ScyllaDB-specific: shard-aware drivers, seastar framework, `--smp`, `--memory` flags
- Recommends Scylla Operator for K8s (if mentioned)
- Notes ScyllaDB's Incremental Compaction Strategy (ICS) as default
- References `blueprints/references/scylladb-6.0.md`

**must_not**:
- Copy Cassandra JVM tuning (Scylla is not JVM-based)
- Assume identical compaction defaults to Cassandra

---

## Scenario 3 — HBase (HDFS-backed)

**Input**:
```
/researching-wide-column-store Apache HBase 2.5 deployment=vm depth=standard
```

**must_pass**:
- Uses HBase terminology: HMaster, RegionServer, Region, column family, HFile, WAL, HDFS, ZooKeeper
- Documents HBase's dependency on HDFS (storage) and ZooKeeper (coordination) — architectural difference from Cassandra's peer model
- Documents region splitting and RegionServer distribution
- References `blueprints/references/hbase-2.5.md`

**must_not**:
- Describe HBase as peer-to-peer (it has HMaster + RegionServers)
- Use Cassandra's token-ring model for HBase
- Omit the HDFS + ZooKeeper dependencies

---

## Scenario 4 — Hot Partition Prevention

**Input**:
```
/researching-wide-column-store Apache Cassandra 5.0 (workload: time-series events by day)
```

**must_pass**:
- Warns that using date alone as partition key sends all of today's writes to one partition (hot partition)
- Recommends a composite key (e.g., (source_id, day) or (day, bucket)) to distribute writes
- Recommends TWCS compaction for time-series with TTL
