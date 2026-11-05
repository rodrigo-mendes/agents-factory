# High availability, failover, DR and runbooks, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). Sources are 3.9 pages read 2026-11-04: [design](https://kafka.apache.org/39/design/design/), [ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/), [KRaft](https://kafka.apache.org/39/operations/kraft/), [datacenters](https://kafka.apache.org/39/operations/datacenters/), [geo-replication](https://kafka.apache.org/39/operations/geo-replication-cross-cluster-data-mirroring/), [basic operations](https://kafka.apache.org/39/operations/basic-kafka-operations/), [hardware](https://kafka.apache.org/39/operations/hardware-and-os/). Compose runs on one host, so there is no failover across hosts (medium confidence, M5).

## Topology

ZooKeeper mode: 3 ZooKeeper servers (quorum 2) + 3 brokers, one of which is the active controller. RF 3, min ISR 2.

```text
        clients (bootstrap: kafka-1..3)
  +----------+----------+----------+
  | kafka-1  | kafka-2  | kafka-3  |  leaders spread; one broker = active controller
  +----+-----+----+-----+----+-----+
       | zookeeper.connect (sessions, watches, metadata)
  +----+-----+----+-----+----+-----+
  |  zk-1    |  zk-2    |  zk-3    |  quorum 2888, election 3888
  +----------+----------+----------+
```

KRaft on 3.9: 3 controllers (quorum 2) + 3 brokers. Quorum sizes: ZooKeeper 3, 5 or 7 tolerate 1, 2 or 3 failures. KRaft controllers 3 or 5 (2N+1; one official page, medium confidence, M16).

## Failover behavior

- **Broker failure (ZooKeeper mode)**: the ZooKeeper session expires and its ephemeral node is deleted. The controller notices through a watch, marks the broker offline, and leaders move to ISR members ([design](https://kafka.apache.org/39/design/design/)).
- **Controller broker failure**: another broker is elected controller.
- **ZooKeeper server failure**: the ensemble continues while a majority is up.
- **Follower lag**: a follower leaves the ISR after `replica.lag.time.max.ms` (30000).
- **Failover duration** is bounded by `zookeeper.session.timeout.ms` (18000) for liveness detection (inferred, unverified, U30). Typical end-to-end durations are (unverified, U11).
- **Client reconnection**: clients refresh metadata. Producer retries are bounded by `delivery.timeout.ms` (120000).
- **Manual intervention needed** when the ZooKeeper quorum is lost, when all ISR replicas of a partition are lost (only unclean election would recover them, with data loss), or when a KRaft controller must be replaced.

## Split-brain

Majority quorum in ZooKeeper (odd size) or the controller quorum prevents it. With a minority, metadata changes stop (inferred, unverified, U30). Do not stretch one cluster across datacenters.

## DR with MirrorMaker 2

No native backup tool was found in the pages read (unverified, U10). Durability comes from replication: a failed node recovers from its replicas ([hardware](https://kafka.apache.org/39/operations/hardware-and-os/)). MM2 to a second cluster also replicates consumer groups including offsets. Exactly-once for dedicated MirrorMaker clusters is supported from 3.5.0 through `exactly.once.source.support`. Moving consumers between clusters is not described step by step (unverified, U10). See [always-do](./always-do-patterns.md#14-mirrormaker-2-for-dr) for the config.

- **Restore a broker after disk loss**: replace it with the same `broker.id` and an empty `log.dirs`, and it re-replicates from peers (inferred, unverified, U30). Reverse MM2 flow to restore a rebuilt primary is also inferred (unverified, U30).
- **PITR** is not a broker feature (medium confidence, M8). Consumers can reset offsets within retention (`kafka-consumer-groups.sh --reset-offsets`).
- **RTO and RPO**: (unverified, U11). MM2 is asynchronous, so RPO equals replication lag (inferred, unverified, U30).

```bash
# Restore verification, representative
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:19092 --describe --under-replicated-partitions
# Expected: no output
/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server kafka-1:19092 --describe --group my-group
# Expected: lag consistent with the source
```

## Runbooks

**ZooKeeper quorum lost.** Detection: fewer than 2 servers answer `srvr`, no "Mode: leader", broker `SessionState` Disconnected ([monitoring](https://kafka.apache.org/39/operations/monitoring/)). Response: restore the ZooKeeper servers, do not change broker config. Metadata changes cannot proceed without ZooKeeper (inferred, unverified, U30). Recovery: restart failed servers with intact `dataDir`; if snapshots are large, raise `initLimit`. Prevention: 5 servers, dedicated `dataLogDir`, autopurge, no swap.

**ZooKeeper disk full.** Trigger: `autopurge.purgeInterval=0`, the default. Response: free space (manual purge procedure (unverified, U27)). Prevention: `autopurge.purgeInterval=1`.

**Broker session expiry.** Trigger: a GC pause or network loss longer than 18000 ms, or a crash. Detection: `SessionState=Expired`, `IsrShrinksPerSec > 0`, `UnderReplicatedPartitions > 0`. Response: check GC logs and heap, restart with the same `broker.id` and data, then wait until `--under-replicated-partitions` is empty. Prevention: G1 settings and adequate heap ([performance-tuning](./performance-tuning.md)).

**Under-min-ISR partitions (producers with acks=all fail).** Detection: `UnderMinIsrPartitionCount > 0`. The flag `kafka-topics.sh --describe --under-min-isr-partitions` is (unverified, U12). Response: bring failed replicas back. Do not lower `min.insync.replicas` or enable unclean election. RF 3 with min ISR 2 tolerates one replica down. Use `broker.rack` for rack awareness.

**Disk full on a broker.** Detection: `df -h` on the data volume. Response: lower `retention.ms` or `retention.bytes` on large topics with `kafka-configs.sh`, or add disk. Recovery: move partitions with `kafka-reassign-partitions.sh --generate/--execute/--verify --throttle`. A ZooKeeper broker with several log dirs shuts down on any dir failure (KAFKA-16431).

**Replacing a failed KRaft controller (KRaft on 3.9).** Detection: `kafka-metadata-quorum.sh --bootstrap-server kafka-1:19092 describe --replication`. Do not format and start the new controller until a majority of controllers has all committed data (check Lag, LogEndOffset, LastCaughtUpTimestamp) (medium confidence, M17). Then `kafka-storage.sh format` (use `--ignore-formatted` only when just the metadata log dir was lost in combined mode) and start.

**Migration stalls or revert fails after the controller epoch advanced.** See [zk-to-kraft-migration](./zk-to-kraft-migration.md).
