# Evaluation Scenarios — researching-rdbms

Cross-vendor coverage required: at least one PostgreSQL scenario AND at least one MySQL/MariaDB scenario.

---

## Scenario 1 — PostgreSQL on Kubernetes (CloudNativePG)

**Input**:
```
/researching-rdbms PostgreSQL 16 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Recommends CloudNativePG (CNCF) as an official operator
- Documents `shared_buffers` (25-30% RAM bare-metal; cgroup-aware in container), `work_mem`, `max_connections`, `synchronous_commit`
- Recommends PgBouncer for connection pooling
- Documents streaming replication + Patroni-style automatic failover (CNPG handles this natively)
- Backup via Barman / pgBackRest with WAL archiving + PITR
- Includes `## Data Modeling` (normal forms, index types GIN/GiST/BRIN, partitioning)
- References `blueprints/references/postgresql-16.md`

**must_not**:
- Use MySQL config keys (`innodb_buffer_pool_size`) for PostgreSQL
- Omit autovacuum tuning
- Recommend single-instance for production

---

## Scenario 2 — MySQL on VM

**Input**:
```
/researching-rdbms MySQL 8.4 deployment=vm depth=standard
```

**must_pass**:
- Uses MySQL/InnoDB terminology: `innodb_buffer_pool_size`, `innodb_flush_log_at_trx_commit`, binary log, undo log, clustered index
- Recommends Group Replication or Orchestrator for HA (not Patroni, which is PostgreSQL)
- Recommends ProxySQL for connection pooling / routing
- Backup via Percona XtraBackup (physical) + mysqldump/mydumper (logical) + binlog for PITR
- Documents gh-ost / pt-online-schema-change for online DDL
- References `blueprints/references/mysql-8.4.md`

**must_not**:
- Use PostgreSQL config keys (`shared_buffers`, `autovacuum`) for MySQL
- Recommend pg_repack (PostgreSQL tool) for MySQL
- Reference CloudNativePG (PostgreSQL operator) for MySQL

---

## Scenario 3 — CockroachDB (NewSQL, distributed)

**Input**:
```
/researching-rdbms CockroachDB 24.1 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Documents distributed consensus (Raft) — all nodes accept writes; no single primary
- Minimum 3 nodes for production; replication factor 3
- Documents range-based sharding (automatic) and rebalancing
- Notes PostgreSQL wire-protocol compatibility but different operational model
- References `blueprints/references/cockroachdb-24.1.md`

**must_not**:
- Describe CockroachDB as primary-standby (it's multi-active)
- Apply single-node PostgreSQL tuning as-is

---

## Scenario 4 — Extension Boundary (pgvector / TimescaleDB)

**Input**:
```
/researching-rdbms PostgreSQL 16 (primary use: vector similarity for RAG)
```

**must_pass**:
- Notes that pgvector is the extension for vector search, but if vector similarity is the PRIMARY use case, `researching-vector-store` covers it in depth
- Still covers base PostgreSQL operations (this sibling remains relevant for the RDBMS layer)
- Routes or cross-references appropriately

---

## Scenario 5 — Replication Mode Trade-off

**Input**:
```
/researching-rdbms PostgreSQL 16 (workload: financial ledger, zero data loss required)
```

**must_pass**:
- Recommends synchronous replication (`synchronous_commit = on` + `synchronous_standby_names`)
- Documents the latency cost of waiting for standby ack
- Recommends at least 2 standbys so one standby failure doesn't block all writes (quorum-based sync)
