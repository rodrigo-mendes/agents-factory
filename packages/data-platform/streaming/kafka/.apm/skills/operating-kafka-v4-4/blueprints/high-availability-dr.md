# High availability, failover and DR, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). S-ids resolve in the [Source Bibliography](./unverified-and-risks.md#source-bibliography). Commands are representative: adapt to your environment. Paths under `/opt/kafka` are inferred (medium confidence, U3). One Compose host cannot survive a host failure (medium confidence, M12).

## Topology

KRaft dedicated quorum (3 controllers) plus 3 or more brokers. Partition replication uses RF 3 with `min.insync.replicas=2`. Brokers are observers of the metadata log. Clients bootstrap through `advertised.listeners`.

## Failover behavior

- Controller: a new active controller is elected automatically while a majority of voters is alive [S6].
- Partition leader: the controller elects from the ISR first, then from unfenced ELR members, then the last known leader if it is unfenced [S18]. Followers stay in the ISR within `replica.lag.time.max.ms` (30000) [S7].
- ELR is on by default for new clusters since 4.1; with ELR on, the cluster-level `min.insync.replicas` is used [S18][S1].
- Typical failover duration: (unverified), U9. No official figure was found.
- Client reconnection: clients refresh metadata and move to the new leader. The producer retries within `delivery.timeout.ms` (120000) [S28].
- Controlled shutdown (`controlled.shutdown.enable=true`) moves leadership away gracefully and succeeds only if every partition on the broker has another live replica [S12].
- Preferred leaders return via `auto.leader.rebalance.enable=true`, or `kafka-leader-election.sh --election-type preferred --all-topic-partitions` [S12].
- Rack awareness: `broker.rack` spreads replicas over min(#racks, RF) racks [S12]. On one Compose host it is cosmetic.

Durability: "With this ISR model and f+1 replicas, a Kafka topic can tolerate f failures without losing committed messages" [S15].

## Split-brain mitigation

- Risk: losing the controller majority. Restoring a controller disk early can elect a leader missing committed data.
- Mitigation: majority quorum (2N+1) [S6] (medium confidence, M16). Do not format or start a replacement controller until a majority has all committed data [S16] (medium confidence, M25: one official page). Auto-formatting was removed for this reason [S6].

```bash
/opt/kafka/bin/kafka-metadata-quorum.sh --bootstrap-server kafka-1:19092 describe --status
/opt/kafka/bin/kafka-metadata-quorum.sh --bootstrap-server kafka-1:19092 describe --replication
```

## Controller membership (dynamic quorum) [S6]

- Add: `kafka-metadata-quorum.sh --command-config controller.properties --bootstrap-server ... add-controller`.
- Remove: `remove-controller --controller-id <id> --controller-directory-id <dir-id>`, optionally with `--unregister`.
- Unregister an already removed controller: `kafka-cluster.sh unregister-controller --id <id>`, new in 4.4, needs metadata version `4.4-IV2` [S1][S23].
- A new controller joining formats with `--no-initial-controllers`.
- Whether a static quorum can be upgraded to dynamic is in conflict (medium confidence, U4): human-verify.

## Multi-DC and DR

- One cluster per DC mirrored by MM2; a stretched cluster is discouraged [S19][S13].
- Patterns: active/passive (`A->B`) and active/active (`A->B`, `B->A`). Define both flows in one config file to avoid loops. `DefaultReplicationPolicy` renames remote topics to `{source}.{topic}` [S13].
- Exactly-once MM2 (dedicated mode): `{cluster}.exactly.once.source.support = enabled` plus `dedicated.mode.enable.internal.rest = true`; consumers set `isolation.level = read_committed`. Use `tasks.max` of at least 2 [S13].

## Backup and restore

No native snapshot or backup tool for partition data in the 4.4 pages read (unverified, U8). Documented resilience: replication inside a cluster [S15] and MM2 to a second cluster, which copies topics, configs, consumer group offsets and ACLs [S13].

```bash
cat > mm2.properties <<'EOF'
clusters = primary, backup
primary.bootstrap.servers = kafka-1:19092
backup.bootstrap.servers = dr-kafka-1:19092
primary->backup.enabled = true
primary->backup.topics = .*
tasks.max = 2
EOF
bin/connect-mirror-maker.sh mm2.properties
# Expected: topics appear on backup as primary.<topic>; watch replication-latency-ms
```

Restore: consumers move to the backup cluster; group offsets are translated by MirrorCheckpointConnector [S13]. Replay a group from a point in time on the same cluster, with consumers inactive first [S12]:

```bash
bin/kafka-consumer-groups.sh --bootstrap-server kafka-1:19092 --reset-offsets --group my-group \
  --topic orders --to-datetime 2026-11-04T10:00:00.000 --execute
bin/kafka-consumer-groups.sh --bootstrap-server kafka-1:19092 --describe --group my-group
# Expected: CURRENT-OFFSET at the reset point; LAG decreasing after restart
```

- PITR is not native. Replay works only within retention, using `--to-datetime` or `--by-duration` [S12]; granularity is the record timestamp.
- RTO and RPO figures: (unverified), U9. MM2 is asynchronous, so RPO is roughly `replication-latency-ms` (medium confidence, inference, M11) [S13].
- Metadata inspection (not a backup): `kafka-metadata-shell.sh --snapshot <checkpoint>` and `kafka-dump-log.sh --cluster-metadata-decoder --files <file>` [S6].

## Runbook: broker crash or container stop

- Detect: `docker compose ps`; `kafka-topics.sh --bootstrap-server kafka-2:19092 --describe --under-replicated-partitions` lists partitions whose Isr misses the dead node.
- Respond: confirm `UnderMinIsrPartitionCount` is 0 [S14]. If not, acks=all producers to those partitions fail.
- Recover: `docker compose up -d kafka-1`, then `kafka-leader-election.sh --bootstrap-server kafka-2:19092 --election-type preferred --all-topic-partitions` [S12].

## Runbook: controller quorum loss

- Detect: `describe --status` fails or shows no LeaderId; the sum of `ActiveControllerCount` is 0 [S6][S14].
- Respond: restart the existing controllers with their volumes intact. Do not reformat.
- Recover: `docker compose up -d controller-1 controller-2 controller-3`. Replace a controller disk only once a majority has all committed data [S16] (medium confidence, M25). A new controller formats with `--cluster-id <ID> --no-initial-controllers`, then `add-controller` [S6].
