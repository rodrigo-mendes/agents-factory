# Evaluation Scenarios — researching-coordination-service

Cross-vendor coverage required: at least one etcd scenario AND at least one non-etcd scenario (ZooKeeper or Consul).

---

## Scenario 1 — etcd on Kubernetes

**Input**:
```
/researching-coordination-service etcd 3.5 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Recommends odd-numbered cluster (3 or 5 nodes) with explicit warning against even numbers
- Documents `--quota-backend-bytes` (default 2GB in 3.5) with sizing guidance
- Documents auto-compaction (`--auto-compaction-mode`, `--auto-compaction-retention`) as mandatory
- Includes defragmentation procedure as separate step from compaction
- Documents mTLS between cluster members (`--peer-cert-file`, `--peer-key-file`)
- KPIs: `etcd_server_has_leader`, `etcd_disk_backend_commit_duration_seconds`, `etcd_server_quota_backend_bytes`
- Warns: "etcd is NOT for large values (>1.5MB per key) or high-throughput application data"

**must_not**:
- Recommend even-numbered cluster (2, 4)
- Suggest etcd as a general-purpose datastore
- Omit auto-compaction guidance

---

## Scenario 2 — Apache ZooKeeper on VM (baseline)

**Input**:
```
/researching-coordination-service Apache ZooKeeper 3.9 deployment=vm depth=standard
```

**must_pass**:
- Uses ZooKeeper terminology: ensemble, znode, session, watch, ZAB protocol, epoch
- Documents observer nodes for read scaling without affecting quorum
- Recommends JVM tuning (heap 1-2GB; G1GC; low-pause GC settings) to avoid session expirations from GC pauses
- Documents `tickTime`, `initLimit`, `syncLimit` as core timing parameters
- KPIs: `zk_avg_latency`, `zk_outstanding_requests`, `zk_znode_count`, `zk_watch_count`
- Documents `snapCount` and log purging for disk management

**must_not**:
- Use etcd terminology (leases, revisions) for ZooKeeper
- Recommend Raft (etcd uses Raft; ZooKeeper uses ZAB)
- Omit JVM GC pause discussion (critical for ZK stability)

---

## Scenario 3 — HashiCorp Consul on VM (service discovery focus)

**Input**:
```
/researching-coordination-service HashiCorp Consul 1.18 deployment=vm depth=standard
```

**must_pass**:
- Uses Consul terminology: server, client, agent, datacenter, gossip pool (LAN + WAN), service definition, health check, ACL token
- Documents server nodes (3 or 5) using Raft; client agents on every host (agent = local proxy for services)
- Documents ACL tokens as the auth model (bootstrap + per-service tokens)
- Multi-datacenter federation via WAN gossip pool
- KPIs: `consul_raft_leader_lastContact`, `consul_serf_events`, `consul_catalog_service_query_tags`
- Documents Consul KV, Service Discovery, Connect (service mesh) — noting each is a separate concern

**must_not**:
- Describe Consul as etcd-compatible
- Confuse server/agent architecture with etcd's peer-only model
- Omit ACL bootstrap discussion (auth is critical)

---

## Scenario 4 — Misuse: High Throughput

**Input**:
```
/researching-coordination-service etcd 3.5 (workload: 100k writes/sec application events)
```

**must_pass**:
- Rejects the workload as inappropriate for etcd (etcd targets ~1000 ops/sec for coordination)
- Recommends `researching-streaming-broker` (Kafka) for event streams
- Recommends `researching-kv-store` if key-value application data is needed
- Does NOT try to tune etcd for the wrong workload

---

## Scenario 5 — Distributed Lock Correctness

**Input**:
```
/researching-coordination-service etcd 3.5 (need distributed lock for job scheduler leader)
```

**must_pass**:
- Recommends etcd Election API (not raw put-if-not-exists) — handles session/lease lifecycle
- Includes fencing token pattern with monotonic revision number
- Warns about long GC pauses in client → false lock expiry → need to validate fencing token at write site
