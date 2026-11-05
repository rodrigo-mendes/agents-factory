# Capacity sizing, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). S-ids resolve in the [Source Bibliography](./unverified-and-risks.md#source-bibliography). No scale target was given for this skill, so sizing here is heuristics plus documented limits.

## Documented sizing inputs

| Resource | Guidance | Source |
|---|---|---|
| Controller memory and disk | About 5 GB of RAM and 5 GB of disk for the metadata log directory in a typical cluster | [S6] |
| Page cache | Kafka uses all free memory as page cache. Size it to buffer about 30 seconds of writes: write throughput x 30 | [S16] |
| Disks | Multiple drives; disk throughput is usually the bottleneck; XFS preferred over ext4; `noatime` is safe; RAID costs write throughput | [S16] |
| File descriptors | At least 100000 (medium confidence, M19) | [S16] |
| Memory map areas | Each partition needs at least 2; check `vm.max_map_count` (about 65535 default) | [S16] |
| Heap | Typical: `-Xmx6g -Xms6g` with G1 settings from the Java page | [S17] |
| Java | 17, 21, 25 fully supported; 25 recommended | [S17] |
| Flush | Keep defaults (application fsync disabled); durability comes from replication | [S16][S15] |

## Heuristics

- Disk per broker: ingress x retention x RF, divided by broker count, plus headroom (medium confidence, M10). Set `retention.bytes` as a guard [S27].
- Broker count: at least the replication factor (3) so RF 3 is placeable. Controllers: 3 or 5 [S6] (medium confidence, M16).
- Partition count: no official formula (unverified, U9). Use target throughput divided by measured per-partition throughput, and the maximum consumer parallelism you need. Partitions can never be reduced [S12].
- A Compose host shares CPU, memory and disks across all containers, so per-broker numbers do not add up to a real cluster (medium confidence, M12).

Worked example, labeled heuristic only: 20 MB/s ingress, 7 days retention, RF 3.
`20 MB/s x 604800 s x 3 = about 36 TB` across the cluster (medium confidence). Divide by broker count, then compare with the volume size.

## Reference scale (documented, not a target)

One LinkedIn cluster: 60 brokers, 50k partitions at RF 2, 800k messages/s in, 300 MB/s in, over 1 GB/s out, 90th-percentile GC pause about 21 ms [S17].

## Growth triggers

| Signal | Action | Source |
|---|---|---|
| RequestHandlerAvgIdlePercent or NetworkProcessorAvgIdlePercent below 0.3 | Raise `num.io.threads` or `num.network.threads`, then add brokers | [S14][S7] |
| Follower lag growing | Raise `num.replica.fetchers` (medium confidence), then add brokers | [S7] |
| Disk above your budget | Lower retention, expand volumes, or reassign partitions with a throttle | [S12] |
| Controller log directory near full | Expand the metadata disk; keep about 5 GB as the starting point | [S6] |

## Adding brokers

New brokers do not receive existing partitions automatically. Move partitions with the reassignment tool and a throttle, then verify [S12]:

```bash
kafka-reassign-partitions.sh --bootstrap-server kafka-1:19092 --reassignment-json-file plan.json --execute --throttle 50000000
kafka-reassign-partitions.sh --bootstrap-server kafka-1:19092 --reassignment-json-file plan.json --verify
# Expected: reassignment complete; --verify also removes the throttle
```

The throttle value is a placeholder. Third-party rebalancers (Cruise Control and similar) are not researched for 4.4 (unverified, U18).
