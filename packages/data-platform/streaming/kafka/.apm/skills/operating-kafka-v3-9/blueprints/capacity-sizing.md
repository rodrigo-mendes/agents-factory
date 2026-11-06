# Capacity sizing and defaults, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-04: [hardware](https://kafka.apache.org/39/operations/hardware-and-os/), [Java](https://kafka.apache.org/39/operations/java-version/), [KRaft](https://kafka.apache.org/39/operations/kraft/), [ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/), [Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html), [broker configs](https://kafka.apache.org/39/configuration/broker-configs/). Sizing numbers are single-page (medium confidence, M10). Scale in the research request was not specified, so these are heuristics.

## Sizing heuristics

- **Page cache**: write throughput times 30 (seconds of data to keep cached). Reference hardware on the page: dual quad-core Xeon with 24 GB.
- **Disk**: use several drives. A disk-sizing formula (ingress x retention x RF) is not on the pages read (unverified, U31).
- **KRaft controllers**: about 5 GB of memory and 5 GB of metadata disk is sufficient for a typical cluster.
- **ZooKeeper heap**: the Kafka team ran 3 to 5 GB depending on data set size. Admin Guide: at most 3 GB on a 4 GB machine, and never swap.
- **Reference scale** (LinkedIn, Java page): 60 brokers, 50k partitions at RF 2, 800k messages per second in, 300 MB/s in and over 1 GB/s out, 90th-percentile GC pause about 21 ms.
- **Partition count formula**: no official formula found (medium confidence, M8).
- **File descriptors**: at least 100000. `vm.max_map_count` matters because each segment uses 2 map areas.

## Defaults reference (3.9.2, broker configs page unless noted)

| Parameter | Default | Recommended |
|---|---|---|
| `zookeeper.connect` | null | all ensemble members, `zk-1:2181,zk-2:2181,zk-3:2181` (example, medium confidence, M10) |
| `zookeeper.session.timeout.ms` | 18000 | keep |
| `zookeeper.set.acl` | false | true once ZooKeeper auth is enabled (order in [zookeeper-security](./zookeeper-security.md)) (medium confidence, M13) |
| `zookeeper.ssl.client.enable` | false | true with a TLS ZooKeeper port (medium confidence, M13) |
| `zookeeper.clientCnxnSocket` | null | `org.apache.zookeeper.ClientCnxnSocketNetty` for TLS (medium confidence, M13) |
| `zookeeper.ssl.endpoint.identification.algorithm` | HTTPS | keep |
| `zookeeper.metadata.migration.enable` | false | true only during migration (medium confidence, M11) |
| `broker.id` | -1 (auto) | explicit and unique, at most `reserved.broker.max.id` (medium confidence, M11) |
| `reserved.broker.max.id` | 1000 | keep. Migration needs `broker.id` at most this value (medium confidence, M11) |
| `process.roles` | empty (ZooKeeper mode) | `broker` or `controller` on KRaft |
| `node.id` | -1 | unique, no collision with broker ids during migration (medium confidence, M11) |
| `controller.quorum.bootstrap.servers` / `controller.quorum.voters` | empty | dynamic quorum / static quorum |
| `listeners` | `PLAINTEXT://:9092` | named listeners (INTERNAL, EXTERNAL) (medium confidence, M11) |
| `inter.broker.protocol.version` | 3.9-IV0 | pin during upgrades, 3.9 before migration |
| `log.dirs` | null (falls back to `log.dir`) | dedicated disks (medium confidence, M10) |
| `default.replication.factor` | 1 | 3 |
| `min.insync.replicas` | 1 | 2 |
| `offsets.topic.replication.factor` | 3 | 3 |
| `transaction.state.log.replication.factor` / `.min.isr` | 3 / 2 | keep on 3 or more brokers (medium confidence, M11) |
| `auto.create.topics.enable` | true | false is an example value (medium confidence, M12) |
| `unclean.leader.election.enable` | false | false |
| `replica.lag.time.max.ms` | 30000 | keep |
| `log.retention.hours` / `retention.ms` | 168 / 604800000 | per workload |
| `ssl.client.auth` | none | `required` for mTLS (medium confidence, M13) |
| `sasl.enabled.mechanisms` | GSSAPI | SCRAM-SHA-512 (medium confidence, M13) |
| `ssl.enabled.protocols` | read as `TLSv1.2` | set `TLSv1.2,TLSv1.3` explicitly (medium confidence, U7) |
| `alter.config.policy.kraft.compatibility.enable` | false | see [ask-first](./ask-first-decisions.md) (medium confidence, M6) |
| `autopurge.purgeInterval` (ZooKeeper) | 0 | 1 or higher (Admin Guide, medium confidence, M10) |
| `admin.serverPort` (ZooKeeper) | 8080, enabled | disable or firewall (Admin Guide, medium confidence, M10) |

All defaults apply to 3.9.2. Tuning behind these numbers: [performance-tuning](./performance-tuning.md).
