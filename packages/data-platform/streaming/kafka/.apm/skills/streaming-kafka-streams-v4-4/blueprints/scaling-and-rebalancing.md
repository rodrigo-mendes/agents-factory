# Scaling, standbys and rebalancing, Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). All pages read 2026-11-04. Representative commands: adapt to your environment.

## Parallelism

Sources: [architecture](https://kafka.apache.org/44/streams/architecture/), [running apps](https://kafka.apache.org/44/streams/developer-guide/running-app/), [KafkaStreams javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/streams/KafkaStreams.html).

- The number of input partitions is the upper limit; extra instances stay idle as hot spares.
- Threads share no state. Add or remove them at runtime with `addStreamThread()` and `removeStreamThread()` (only in RUNNING or REBALANCING).

## Restoration, standbys and warmups

Sources: [running apps](https://kafka.apache.org/44/streams/developer-guide/running-app/), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [rebalance protocol](https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/).

- A migrated task is fully restored before processing resumes.
- Standbys and warmup replicas (classic protocol) cut restore time. Active tasks go only to instances within `acceptable.recovery.lag` (default 10000).
- Provision n+1 instances for n standbys.
- Warmup tasks are not implemented under the streams protocol.
- Under `group.protocol=streams` the client `num.standby.replicas` is ignored; set the group config `streams.num.standby.replicas` on the broker (medium confidence, M14, one page).

## Rebalance protocols

Decision table and requirements: [ask-first-decisions](./ask-first-decisions.md#rebalance-protocol-classic-or-streams). Source: [rebalance protocol](https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/).

Migration from classic to streams, offline only:

```text
1. Stop all instances.
2. Wait for the session timeout (or force a leave).
3. Set group.protocol=streams.
4. Start all instances. Only committed offsets carry over.
```

Do not migrate on 4.2.0 (KAFKA-20254, fixed in 4.2.1). Topology changes under the streams protocol need a new group. Custom `TaskAssignor` implementations must be thread safe ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)).

## Static membership (4.4, streams protocol)

`group.instance.id` needs 4.4 brokers; older brokers reject it with `INVALID_REQUEST`, fatal to the client. Remove it before you downgrade brokers below 4.4 ([rebalance protocol](https://kafka.apache.org/44/streams/developer-guide/streams-rebalance-protocol/), [upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)).

## Resetting an application

Sources: [reset tool](https://kafka.apache.org/44/streams/developer-guide/app-reset-tool/), [groups tool](https://kafka.apache.org/44/streams/developer-guide/kafka-streams-group-sh/).

```bash
# Classic protocol. Representative: instances stopped
bin/kafka-streams-application-reset.sh --bootstrap-server localhost:9092 --application-id orders-agg --input-topics orders --dry-run
# Expected: planned offset resets and internal topics to delete; no changes made (--dry-run)

# Streams protocol
bin/kafka-streams-groups.sh --bootstrap-server localhost:9092 --describe --group orders-agg --offsets
# Expected: group listed with committed offsets per input partition
```

`KafkaStreams#cleanUp()` deletes local state and may run only before `start()` or after `close()`. The `--all-input-topics --to-earliest` flags with `--reset-offsets` are (unverified, U9): the page names `--all-input-topics` only for `--delete-offsets`.

## Memory

Sources: [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/), [StreamsConfig.java](https://raw.githubusercontent.com/apache/kafka/4.4/streams/src/main/java/org/apache/kafka/streams/StreamsConfig.java), [memory management](https://kafka.apache.org/44/streams/developer-guide/memory-mgmt/).

- The record cache is `statestore.cache.max.bytes` (default 10485760), split across threads.
- `cache.max.bytes.buffering` is deprecated since 3.4 but still defined in 4.4. The memory-management page still names the old key; that page is stale here. Use `statestore.cache.max.bytes` (the config page and the code agree).
- RocksDB uses off-heap memory. Bounding it is (medium confidence, M9), see [ask-first-decisions](./ask-first-decisions.md#single-source-items-medium-confidence).
- RocksDB library: 9.7.3 since 4.0; the bundled version in 4.4 is (unverified, U11).

## Shutdown

Close `KafkaStreams` in a shutdown hook, with a timeout below the shutdown grace period of the platform that runs the app ([memory management](https://kafka.apache.org/44/streams/developer-guide/memory-mgmt/)). The `CloseOptions.GroupMembershipOperation.DEFAULT` is the 4.4 default (KIP-1284), and `org.apache.kafka.streams.CloseOptions` replaced `KafkaStreams$CloseOptions` in 4.2 ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)).
