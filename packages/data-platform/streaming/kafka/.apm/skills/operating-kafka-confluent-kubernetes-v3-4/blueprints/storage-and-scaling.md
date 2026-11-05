# Storage, sizing, scaling, CFK 3.4.0

Back to [SKILL.md](../SKILL.md). S-ids are in the [bibliography](./unverified-and-risks.md#source-bibliography). Facts below rest on one versioned page each unless two are cited; recommendations and prohibitions that rest on one page carry (medium confidence).

## Storage (S12)

- Block storage only, one PV per broker. No object or network file storage for Kafka.
- EBS CSI driver on AWS with Kubernetes 1.23 or later.
- PVCs are `ReadWriteOnce` by default and the access mode is fixed once created.
- Tiered Storage buckets must exist first and are not cleaned up when the cluster is deleted.
- Explicit StorageClass with `WaitForFirstConsumer`: [always-do A8](./always-do-patterns.md#a8).
- `reclaimPolicy: Retain` (the page says required for production) and `allowVolumeExpansion: true`; avoid the default StorageClass in production; `Delete` reclaim means `kubectl delete kafka` deletes data (S12) (medium confidence).
- Give all brokers the same disk size; do not grow one broker's disk alone (S20) (medium confidence).

## Sizing (S22)

| Component | Production | Minimum |
|---|---|---|
| Kafka brokers | 24 CPU, 64 GB, 12 TB | 4 CPU, 16 GB, 1 TB |
| KRaft controllers | 5 pods, 5 CPU, 4 GB, 64 GB SSD | 3 pods, 3 CPU |
| Connect | 2 workers, 12 CPU, 24 GB | not listed |
| Schema Registry | 2 pods, 2 CPU, 4 GB | not listed |
| Control Center | 4 CPU, 8 GB, 200 GB | not listed |

The page also lists "Default resources" (limits 500m CPU and 512Mi, requests 100m and 256Mi) "on Confluent Platform pods". Whether these are operator defaults is unclear (medium confidence). The CFK init container is fixed at limits 500m/1Gi and requests 100m/512Mi (S21).

## CPU, memory, heap (S21, S1)

Heap default in 3.4.0: brokers min(50% of `requests.memory`, 32Gi), controllers min(80%, 32Gi). Pin `-Xms`/`-Xmx` in `spec.configOverrides.jvm` before upgrading: [always-do A11](./always-do-patterns.md#a11). Heap policy options: [ask-first C8](./ask-first-decisions.md#heap-sizing-policy-c8).

## Scaling (S20)

- Scale up: `kubectl scale kafka <name> --replicas=N`. New brokers get the next ID, and DNS must resolve them.
- Scale down needs a `KafkaRestClass`, `spec.dependencies.kafkaRest` and `spec.services.kafkaRest`, and disabled webhooks. It removes the highest IDs first and is not supported on multi-AZ or multi-rack clusters. Disable with `platform.confluent.io/enable-shrink=false`.
- Self-Balancing is on by default and automates shrink. Trigger choice: [ask-first C6](./ask-first-decisions.md#self-balancing-trigger-c6) (medium confidence). Self-Balancing is an Enterprise feature (medium confidence, M32): see [licensing](./licensing.md).
- Do not edit the shrink annotations or resize ZooKeeper with `kubectl scale` (medium confidence). ZooKeeper replica count is set only at first deploy.
- ksqlDB, Connect and REST Proxy scale horizontally. Schema Registry "does not support scaling in this context" (medium confidence).
- KRaft controller scaling and dynamic quorum procedure: not on the page read (unverified, U4).

## Availability (S26, S27)

- Use topology spread constraints and `oneReplicaPerNode: true`; both rest on one page each (medium confidence). Changing `oneReplicaPerNode` on a running cluster rolls the cluster.
- A PV cannot move across AZs. If an AZ fails, its pods stay Pending (S26).
- Rack awareness uses AZs as racks; the configuration page was not read (unverified, U10).
- PodDisruptionBudget defaults created by CFK are not covered on any page read (unverified, I3).
