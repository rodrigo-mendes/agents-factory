# Coordination Service — Neutral Category Specifics

Patterns for distributed coordination services. Vendor-specific config keys in `references/<vendor>-<version>.md`.

---

## Purpose of a Coordination Store

Distributed coordination stores solve four canonical problems:

1. **Distributed configuration** — a single source of truth for cluster-wide config, watched by clients for changes
2. **Service discovery** — services register their endpoints; clients discover current instances
3. **Leader election** — one node in a cluster claims exclusive leadership; automatic failover on loss
4. **Distributed locking** — bounded exclusive access to a resource across a cluster, with automatic release on holder crash

If the use case is high-throughput data storage or message passing, a coordination service is the WRONG tool — route to `researching-kv-store` or `researching-streaming-broker`.

---

## Consensus Algorithm Model (Vendor-Neutral)

Every coordination service uses a consensus algorithm to ensure agreement across nodes:

| Property | Requirement |
|---|---|
| Quorum size | Must be odd — majority (N/2 + 1) required for writes |
| Node roles | Leader (accepts writes) + Followers (replicate + serve reads) + optional Observers (non-voting, for read scaling) |
| Write path | Client → Leader → Replicate to majority → Commit → Ack |
| Read consistency options | Linearizable (through leader) vs Serializable (from local follower — may be stale) |
| Failover trigger | Leader unreachable for `heartbeat_timeout` → new leader election |
| Election duration | Typically hundreds of milliseconds to a few seconds |

---

## Cluster Sizing Guidelines

| Cluster Size | Tolerated Failures | Use Case |
|---|---|---|
| 1 node | 0 (no HA) | Dev/test only |
| 3 nodes | 1 | Standard production HA |
| 5 nodes | 2 | Higher HA; larger clusters, geo-multi-DC |
| 7 nodes | 3 | Rare; very large multi-tenant clusters — write latency increases |

**Do not go beyond 7 voting nodes** — consensus latency grows with cluster size. For read scaling beyond what voting nodes provide, use observer/learner nodes (non-voting).

---

## Read Consistency Trade-off

| Consistency | Latency | Freshness | When to Use |
|---|---|---|---|
| Linearizable | Higher — round-trip to leader | Latest committed value | Leader election, critical config reads |
| Serializable / local | Lower — read from local follower | May be stale by heartbeat_interval | Service discovery, non-critical reads |

Every read call should explicitly choose the consistency level. Defaults differ per vendor.

---

## Distributed Locking Pattern

Neutral pattern (vendor-specific mechanism named in reference cards):

```
Lock acquisition:
  1. Create ephemeral key/lease with TTL
  2. Set key value = holder identity
  3. If key already exists → wait or fail (based on client policy)
  4. On success → holder proceeds

Lock renewal:
  - Holder periodically extends TTL (< half the TTL interval)
  - On failure to renew → key auto-expires → other client acquires

Lock release:
  - Explicit delete of key OR
  - Holder crash → TTL expires → auto-release

Fencing:
  - Include a monotonically-increasing fencing token with each lock
  - Downstream storage validates token — old holders (whose lock has been released) cannot corrupt state
```

---

## Service Discovery Pattern

```
Service registration:
  - Service instance writes: /services/<service-name>/<instance-id> = <endpoint>
  - Uses lease/session with TTL — auto-removed if instance crashes

Service resolution:
  - Client reads: /services/<service-name>/* (prefix range read)
  - Optionally watches for changes to react to instance up/down events

Health check integration:
  - Instances renew lease periodically only if healthy
  - Unhealthy instances stop renewing → auto-removed from discovery
```

---

## Compaction / Defragmentation

Coordination stores retain MVCC history that must be compacted:

- **Auto-compaction**: schedule (periodic or revision-based) with configurable retention window
- **Manual compaction**: on-demand for one-time cleanup
- **Defragmentation**: after compaction, actual disk space is reclaimed only after defrag — some vendors require this as separate step

**Alert**: coordination store size approaching quota is a critical operational signal — writes will fail once quota is hit.

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Has leader (boolean per node) | Cluster availability | 0 (no leader) |
| Backend commit duration p99 | Disk write speed | > 25ms (Raft consensus needs fast fsync) |
| Number of leader changes | Cluster stability | Sustained > 0 per hour indicates instability |
| Store size / quota | Storage headroom | > 0.8 approaching limit |
| Slow apply count | Replication health | Sustained non-zero |
| Watcher count | Client subscription load | Trending up unexpectedly |
| Proposal failure rate | Consensus health | Non-zero |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Even-numbered cluster (2, 4, 6 nodes) | No majority possible on split; single failure blocks writes | Always odd: 3, 5, 7 |
| Coordination store as message queue | MVCC history explodes; consensus latency spikes | Use `researching-streaming-broker` |
| Storing large blobs | Bloats snapshot; slows leader election | Store reference; blob in object storage |
| Skipping auto-compaction | Store size grows until quota hit; writes fail | Enable auto-compaction from day one |
| Cross-DC quorum without latency planning | High write latency; failed elections during transient partitions | Use one DC for voting members + observers in other DCs |
| No TLS between coordination nodes | Cluster traffic interceptable; malicious node can join | Enable mTLS between all cluster members |
| Ignoring certificate expiry | Cluster split-brain when certs expire | Automate rotation; alert 30+ days before expiry |

---

## Ecosystem Adjacencies

Neutral list (vendor names in reference cards):

- Client libraries per language (with retry, watch, session management)
- Backup/restore tooling
- Migration tooling (etcd-dump, ZooKeeper-migrator, consul snapshot)
- Web UI (etcd-manager, ZooNavigator, Consul UI)
- Metrics exporters (Prometheus per vendor)
