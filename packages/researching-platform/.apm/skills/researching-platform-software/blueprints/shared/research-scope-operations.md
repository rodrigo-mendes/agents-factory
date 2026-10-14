# Research Scope — Operations Reference

Full section content for `researching-platform-software` skill. Sections §1–§12 apply to all platforms. Sections §K8s, §API, §DM are conditional.

---

## §1 — Platform Fundamentals

Research the internal architecture of `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}`:

- **Core architectural model**: single-node, broker cluster, replica set, ring, shard topology — how data is stored and routed internally
- **Data model**: record format (BSON / Avro / Parquet / row-page / SSTable / byte-array), wire protocol (binary/text, custom/standard), serialization format
- **Storage engine**: which storage engine is the default in `{{TARGET_VERSION}}`, whether it is pluggable, and what changed from the previous version
- **Concurrency model**: threading model, async I/O, lock granularity (table/row/document/partition), MVCC or append-only log
- **Persistence guarantee**: durability level (fsync behavior, WAL/journal usage, checkpoint interval), what is lost on crash without fsync
- **Network topology**: client connection points, intra-cluster communication ports, TLS support per protocol

Format:
```
Component: [name]
Role: [what it does]
Default in {{TARGET_VERSION}}: [value or behavior]
Changed from previous version: [yes/no — if yes, describe]
Source: [URL] (DATE)
```

---

## §2 — Installation & Bootstrapping

Research installation methods for all `DEPLOYMENT_MODEL` values:

### Package Manager (bare-metal / VM)

- Official OS packages: deb (apt), rpm (yum/dnf), tar.gz
- Exact repository URL for `{{TARGET_VERSION}}`
- Version pinning command to prevent auto-upgrade
- Post-install steps: user/group creation, directory layout, systemd unit file

### Container (Docker Compose)

- Official Docker image name and tag pattern for `{{TARGET_VERSION}}` (never use `latest`)
- Minimum `docker-compose.yml` for a development/staging single-node setup
- Volume mounts for data persistence
- Environment variables for initial configuration
- Health check definition

### Kubernetes Operator

- Official operator name, maintainer organization, and version compatible with `{{TARGET_VERSION}}`
- Helm chart repository URL and exact chart version
- Minimal Custom Resource (CR) to bootstrap a functional cluster
- Required PersistentVolumeClaim configuration
- Namespace and RBAC setup
- See full guidance in [deployment-guides/kubernetes-operator-guide.md](./deployment-guides/kubernetes-operator-guide.md)

### Verification (all models)

```bash
# Representative — adapt to your environment
# Health check command
[command that returns cluster/node status]
# Expected output indicating healthy state: [output]

# Version verification
[command that prints version string]
# Expected: {{TARGET_VERSION}} or compatible patch
```

---

## §3 — Configuration Reference (Top-20 Parameters)

Identify the 20 most operationally critical parameters for `{{WORKLOAD_PROFILE}}`:

For each parameter document:

| Field | Description |
|---|---|
| Parameter | Exact config key name as it appears in config file / CLI / CR |
| Scope | Where it applies: broker / instance / topic / index / connection / cluster |
| Default | Default value in `{{TARGET_VERSION}}` — cite source |
| Recommended | Value for `{{WORKLOAD_PROFILE}}` + rationale |
| Unit | Bytes / milliseconds / integer / boolean / percentage |
| Deployment note | If value differs by `DEPLOYMENT_MODEL`, note each |
| Source | Official docs URL with section name (DATE) |

Category-specific parameter guidance: see `blueprints/category-templates/`.

---

## §4 — Cluster Topology & High Availability

Research all supported HA topologies for `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}`:

For each topology:
- **Name**: official name from docs
- **Minimum nodes**: absolute minimum for quorum (always odd for consensus-based)
- **Recommended production minimum**: (typically 3 or 5 nodes)
- **Replication mode**: synchronous / asynchronous / semi-synchronous
- **Leader/primary election**: algorithm (Raft, Paxos, ZAB, configurable, external), trigger condition, duration
- **Automatic failover**: yes/no — if yes, what triggers it and how long it takes
- **Manual intervention required when**: split-brain, quorum lost, epoch conflict
- **Read scaling**: can replicas/followers serve reads, and at what consistency level
- **Cross-datacenter/zone support**: multi-AZ / multi-region topology options

Failure mode for each topology:
```
Topology: [name]
Failure: [scenario — e.g., "primary node crash"]
Detection: [monitoring signal or command]
Recovery: [automatic / manual steps]
Data risk: [zero / potential data loss — under what condition]
Source: [URL] (DATE)
```

---

## §5 — Storage & Persistence

- **Data directory layout**: recommended filesystem layout, separate mounts for WAL vs data vs logs
- **WAL / Journal / Oplog**: format, retention configuration, impact on disk usage, truncation rules
- **Storage engine options**: default engine in `{{TARGET_VERSION}}`, pluggable engines, and when to use each
- **Checkpoint / Compaction**: how often, what triggers it, performance impact during checkpoint
- **Durability settings**: fsync behavior, write-ahead log sync mode, crash recovery guarantee
- **Disk I/O requirements**: sequential vs random I/O profile, recommended disk type (NVMe/SSD/HDD), IOPS requirements for `{{SCALE_TARGET}}`
- **Memory requirements**: how much data is cached in memory, cache eviction policy, memory-mapped files

---

## §6 — Security Hardening

Research security controls available in `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}`:

### Authentication
- Available mechanisms: password / certificate / SASL / LDAP / Kerberos / API key / mTLS
- Default auth state in `{{TARGET_VERSION}}` (enabled or disabled — this is often a critical anti-pattern)
- Steps to enable and test auth

### Authorization
- RBAC / ACL support: granularity (database / collection / topic / index / cluster)
- Principle of least privilege: minimum roles needed for application reads/writes
- Admin role isolation: separate admin credentials from application credentials

### Encryption in Transit
- TLS support: client-server, intra-cluster
- Minimum TLS version supported in `{{TARGET_VERSION}}`
- Certificate rotation: hot-rotation supported or requires restart
- Cipher suite recommendations from official docs

### Encryption at Rest
- Native at-rest encryption: supported in `{{TARGET_VERSION}}` (yes/no) — if yes, key management
- If not native: recommended OS-level encryption (LUKS/dm-crypt)
- Encrypted backups

### Network Security
- Ports used: list all with purpose
- Binding address default (0.0.0.0 is an anti-pattern — must be restricted)
- Firewall rules required for: client access, intra-cluster replication, monitoring, backup

---

## §7 — Backup, Restore & PITR

Research official backup tooling and procedures for `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}`:

### Backup Types
| Type | Tool | Granularity | Impact on Platform | Use Case |
|---|---|---|---|---|
| Logical | [official CLI tool] | [table/collection/topic] | [CPU/IO impact] | [schema migration, cross-version] |
| Physical | [official tool or filesystem snapshot] | [file-level] | [requires consistent state] | [fast restore, same version] |
| Continuous / PITR | [WAL archiving tool] | [transaction/checkpoint] | [continuous overhead] | [RPO < minutes] |

### Backup Verification
- Restore drill: how to verify a backup is restorable without impacting production
- Checksum validation: official command to verify backup integrity
- Frequency recommendation: based on `{{SCALE_TARGET}}` and recovery objectives

### Kubernetes Backup
- Operator-integrated backup: which operators support scheduled backups natively
- Velero compatibility: for PVC-level snapshots
- See [deployment-guides/kubernetes-operator-guide.md](./deployment-guides/kubernetes-operator-guide.md)

---

## §8 — Upgrade & Migration

Research the upgrade path to `{{TARGET_VERSION}}`:

### Compatibility Matrix
- Wire protocol compatibility between versions (for rolling upgrade safety)
- Data format compatibility (on-disk format changes requiring migration)
- Client driver compatibility matrix
- Operator/Helm chart version required for `{{TARGET_VERSION}}`

### Rolling Upgrade Steps
1. Upgrade one non-primary/follower node at a time
2. Verify it rejoins the cluster and syncs
3. Repeat until all replicas are upgraded
4. Upgrade the primary/leader last (trigger controlled failover first if needed)
5. Verify cluster health after all nodes upgraded

### Breaking Changes Research
- Identify all breaking changes from the N-1 stable to `{{TARGET_VERSION}}` via official release notes
- Deprecated configs that will fail in `{{TARGET_VERSION}}`
- API endpoints removed or changed
- Default values changed that could silently affect behavior

---

## §9 — Observability & KPIs

Research official monitoring integration for `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}`:

### Metrics
- Official metrics endpoint: protocol (Prometheus/JMX/HTTP/SNMP) and port
- Official Prometheus exporter: name, version, and whether it ships with the platform or is separate
- Required metric labels for multi-instance monitoring

### Critical KPIs (research ≥ 8 for the `{{PLATFORM_CATEGORY}}`)

Platform-category-specific KPIs to research:

**streaming-messaging**: consumer_lag, producer_rate, consumer_rate, under_replicated_partitions, leader_election_rate, request_latency_p99, disk_usage_per_topic, network_io_bytes

**datastore/rdbms**: connections_active, query_latency_p99, transactions_per_second, cache_hit_ratio, replication_lag_seconds, checkpoint_write_time, dead_tuples, table_bloat

**datastore/document**: opcounters_insert/query/update/delete, replication_lag, connections, page_faults, wired_tiger_cache_usage, oplog_window

**cache-coordination**: hit_ratio, evicted_keys, memory_usage_ratio, connected_clients, replication_offset, keyspace_hits_misses

**search-analytics**: indexing_rate, search_latency_p99, cluster_status, shard_count, segment_memory, GC_pause_time, pending_tasks

**api-management**: request_rate, latency_p99, error_rate_5xx, upstream_latency, active_connections, plugin_execution_time

### Alerting Thresholds
For each critical KPI, research the recommended alert threshold from official docs or recognized operational guides.

---

## §10 — Capacity Planning

Research sizing heuristics for `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}`:

- **Memory**: formula or rule-of-thumb for RAM per unit of workload (e.g., "2× working set size", "heap = 50% of RAM up to 26GB for Elasticsearch")
- **CPU**: cores per broker/node for `{{SCALE_TARGET}}`
- **Disk**: storage formula (replication factor × data size × retention), recommended IOPS
- **Network**: bandwidth calculation per partition/shard/node, inter-node replication overhead
- **Connection limits**: max clients per node, connection pool sizing at client side
- **JVM tuning** (if applicable): heap size, GC algorithm recommended in `{{TARGET_VERSION}}`

---

## §11 — Failure Modes & Runbooks

Research the most common operational failures for `{{PLATFORM_SOFTWARE}}`:

### Required Scenarios (≥ 3 of the following)
1. **Node/broker crash** — unexpected process death or node unavailability
2. **Disk full** — data directory fills up, writes blocked
3. **Network partition** — cluster split into two disconnected halves
4. **Replication lag** — replica falls behind primary beyond acceptable threshold
5. **Memory exhaustion / OOM kill** — process killed by OS OOM killer
6. **Certificate expiry** — TLS cert expires causing connection refusals
7. **Clock drift** — nodes with divergent system clocks causing consensus issues
8. **Poison pill / corrupt message** — a message or record that prevents consumer progress

For each scenario document:
- Trigger conditions
- Detection command (exact, reproducible)
- Blast radius (what is affected)
- Immediate response
- Recovery procedure
- Prevention (config or architectural change)

---

## §12 — Ecosystem & Adjacent Tools

Research companion projects officially recommended by the `{{PLATFORM_SOFTWARE}}` project or its maintainers:

For each tool:
```
Tool: [name]
Role: [what operational gap it fills]
Compatibility: [version range compatible with {{TARGET_VERSION}}]
Install: [official install command or URL]
Official status: [first-party / official-partner / community-recommended]
Source: [URL] (DATE)
```

Category-specific ecosystem tools to research by `{{PLATFORM_CATEGORY}}`:

- **streaming-messaging/Kafka**: Schema Registry, Kafka Connect, MirrorMaker 2, Kafka UI, AKHQ, Cruise Control
- **streaming-messaging/RabbitMQ**: Management Plugin, Shovel/Federation, Prometheus Plugin, Event Exchange
- **datastore/rdbms/PostgreSQL**: pgBouncer, PgBouncer-RR, Patroni, pg_repack, pgBackRest, Barman, pg_stat_statements
- **datastore/document/MongoDB**: mongos, Compass, Ops Manager, Percona Backup for MongoDB (pbm), mongodump/mongorestore
- **cache-coordination/Redis**: Sentinel, Redis Cluster (built-in), RedisInsight, redis-benchmark, keydb (fork)
- **search-analytics/Elasticsearch**: Kibana, Logstash, Beats, ILM, Curator, Elastic APM
- **api-management/Kong**: decK, Kong Manager, Kong Konnect, Insomnia, Plugin Hub, Kong Ingress Controller
- **api-management/APISIX**: APISIX Dashboard, apisix-ingress-controller, etcd (required dependency)
