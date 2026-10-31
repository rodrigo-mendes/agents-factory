# Evaluation Scenarios — researching-kv-store

Cross-vendor coverage required: at least one Redis-as-primary-DB scenario AND at least one non-Redis scenario (TiKV, RocksDB, or LMDB).

---

## Scenario 1 — Redis as Primary Datastore on VM

**Input**:
```
/researching-kv-store Redis 7.2 deployment=vm depth=standard
```

**must_pass**:
- Confirms primary-datastore intent (contrasts with `researching-cache-store`)
- Recommends `appendonly yes` + `appendfsync everysec` (or `always` for zero-loss) — persistence mandatory
- Recommends `maxmemory-policy noeviction` (NOT allkeys-lru, which is for cache)
- HA: Sentinel (3 sentinels) or Cluster (6 nodes) — data must survive failover
- Data Modeling: namespaced keys, structure selection, secondary index patterns
- Backup with verified restore (RDB + AOF)
- References `blueprints/references/redis-7.2.md`

**must_not**:
- Recommend eviction policy for primary data
- Recommend disabling persistence
- Treat data loss as acceptable

---

## Scenario 2 — TiKV on Kubernetes

**Input**:
```
/researching-kv-store TiKV 7.5 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Uses TiKV terminology: Region, Raft group, Placement Driver (PD), RocksDB storage engine, coprocessor
- Documents distributed transactions (Percolator model) and strong consistency via Raft
- Recommends TiDB Operator for Kubernetes
- Documents PD as the metadata/scheduling component (required)
- Ordered-key range scan design (TiKV is an ordered KV)
- References `blueprints/references/tikv-7.5.md`

**must_not**:
- Use Redis config keys (`appendonly`, `maxmemory`) for TiKV
- Describe TiKV as single-node failover-pair (it's distributed Raft)
- Omit the Placement Driver dependency

---

## Scenario 3 — RocksDB (embedded)

**Input**:
```
/researching-kv-store RocksDB 9.0 deployment=bare-metal depth=standard
```

**must_pass**:
- Notes RocksDB is an embedded library, not a standalone server — HA/replication is the responsibility of the embedding application
- Documents LSM-tree tuning: compaction strategy (level vs universal), write amplification, block cache, bloom filters
- Documents WAL + memtable + SST levels
- Column family concept
- References `blueprints/references/rocksdb-9.0.md`

**must_not**:
- Recommend a "RocksDB cluster operator" (it's embedded, no server)
- Apply Redis Sentinel/Cluster concepts to RocksDB

---

## Scenario 4 — Misuse: Cache Intent

**Input**:
```
/researching-kv-store Redis 7.2 (workload: ephemeral API response cache, eviction is fine)
```

**must_pass**:
- Detects cache intent (eviction acceptable)
- Routes to `researching-cache-store` OR asks to confirm
- Does NOT recommend noeviction + mandatory persistence for a cache workload
