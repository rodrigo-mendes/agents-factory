# Migration guide to Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). Sources: [Streams upgrade guide 4.4](https://kafka.apache.org/44/streams/upgrade-guide/) (read in full, 113801 of 113801 characters, 2 reads), [4.4.0 announcement](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/), [4.0.0 announcement](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/), [config page](https://kafka.apache.org/44/streams/developer-guide/config-streams/). Read 2026-11-04. Broker upgrade steps: `operating-kafka-v4-4`.

## Breaking and behavior changes

| Release | Change | Source |
|---|---|---|
| 4.4 | Processors sharing a `StoreBuilder` are grouped into one subtopology (KAFKA-20464). Task IDs change; state is restored from the changelog on first startup | upgrade guide |
| 4.4 | Async bootstrap DNS (KIP-909) unsupported; `bootstrap.resolve.timeout.ms` forced to 0 | upgrade guide |
| 4.4 | `application.server` validated; bad values throw `ConfigException` (KIP-1245) | upgrade guide, announcement |
| 4.4 | `StreamPartitioner#partitions` gains a headers-aware default; the old method is deprecated for 5.0. Header-sensitive windowed key serializers may change partition and break co-partitioning with existing data | upgrade guide, announcement |
| 4.4 | `CloseOptions.GroupMembershipOperation.DEFAULT` is the default (KIP-1284) | upgrade guide, announcement |
| 4.4 | `ValueJoinerWithKey` GlobalKTable join overloads deprecated; new overloads with `ValueJoinerWithStreamAndMappedKey` (KIP-1340) | upgrade guide, announcement |
| 4.4 | Custom `TaskAssignor` implementations must be thread safe | upgrade guide |
| 4.3 | Changelog offsets stored in the state store (KIP-1035). Downgrade to 4.2.x requires deleting `state.dir` | upgrade guide, memory management |
| 4.3 | 4.3.0 has a native memory leak (KAFKA-20616); use 4.3.1 if you stop there | upgrade guide |
| 4.3 | `kafka-streams-scala` deprecated, removal in 5.0 (KIP-1244) | upgrade guide, DSL page |
| 4.3 | `processing.exception.handler.global.enabled` deprecated for removal in 5.0; the config page recommends enabling it now | upgrade guide, config page |
| 4.2 | `errors.dead.letter.queue.topic.name` added; `Response`, `handleError`, `handleSerializationError` replace the deprecated handler API (KIP-1034) | upgrade guide |
| 4.2 | `org.apache.kafka.streams.CloseOptions` replaces `KafkaStreams$CloseOptions` (KIP-1153) | upgrade guide |
| 4.0 | EOS v1 removed; every API deprecated up to 3.5 removed (old Processor API, `through`, transformers, `branch`; the upgrade guide is read as including `setUncaughtExceptionHandler(Thread...)` (unverified, U2)) | upgrade guide |
| 4.0 | `default.deserialization.exception.handler` and `default.production.exception.handler` deprecated (KIP-1056) | upgrade guide, config page |
| 4.0 | Production handler is called on `TimeoutException` and can return `RETRY` (KIP-1065) | upgrade guide, 4.0 announcement |
| 4.0 | RocksDB 7.9.2 to 9.7.3 with API removals | upgrade guide, monitoring page |
| 4.0 | Clients and Streams require Java 11 or later | 4.0 announcement |

## Upgrade steps

1. From 3.4 or earlier: two rolling bounces. In the first, set `upgrade.from` to the old version ("2.4" to "3.4"); in the second, remove it (upgrade guide, config page).
2. From 3.5 to 4.3: a single rolling bounce with the new jar. This is inferred from the guide requiring `upgrade.from` only below 3.4 (unverified, U6).
3. Offline alternative: stop all instances, replace the jar, restart. The guide says this works from versions as old as 0.11.0.x.
4. After upgrading to 4.4, expect state restoration on first startup if any processors share a `StoreBuilder` (KAFKA-20464).
5. With the streams protocol, remove `group.instance.id` before downgrading brokers below 4.4.

```bash
# Representative. Adapt to your environment
# Step 1 (from 3.4 or earlier only): upgrade.from=3.4 in the app config, rolling bounce
# Step 2: remove upgrade.from, rolling bounce again
# Expected: every instance back in RUNNING (client metric state, MBean kafka.streams:type=stream-metrics)
```

## Replacing removed APIs

See [never-do-patterns](./never-do-patterns.md#apis-removed-in-40-risk-high). Compare `Topology.describe()` before and after replacing `transformValues()` with `processValues()` when merge-repartition-topics optimization is on (KAFKA-19668).

## Compatibility

| Dependency | Version | Source |
|---|---|---|
| Kafka brokers | The upgrade guide matrix lists Streams 2.6 to 4.4 against brokers 2.4.x to 4.4.x; EOS v2 needs brokers 2.5+ | upgrade guide |
| Brokers for `group.protocol=streams` | 4.2 to 4.4; static membership needs 4.4 | rebalance protocol page |
| Java | 17, 21, 25 fully supported; 11 for a subset including streams | https://kafka.apache.org/44/operations/java-version/ |
| `kafka-streams-test-utils` | Same version as `kafka-streams` (4.4.0) | testing page |
| Bundled RocksDB | 9.7.3 since 4.0; version in 4.4 (unverified, U11) | upgrade guide |

## Downgrade notes

4.3 or later stores changelog offsets in the state stores; downgrading to 4.2.x requires deleting `state.dir` (upgrade guide).
