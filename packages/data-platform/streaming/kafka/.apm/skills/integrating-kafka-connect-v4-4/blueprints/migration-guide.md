# Migration guide 3.9 to 4.4, Kafka Connect

Back to [SKILL.md](../SKILL.md). Sources: [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/) (page modified 2026-10-26), [4.4.0 announcement](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/) (2026-10-22), [compatibility](https://kafka.apache.org/44/getting-started/compatibility/), [Java version](https://kafka.apache.org/44/operations/java-version/). All read 2026-11-04. Broker upgrades are in `operating-kafka-v4-4`.

## Changes that affect Connect

| Release | Change |
|---|---|
| 4.0.0 | Brokers, Connect and tools require Java 17 |
| 4.0.0 | Clients including Connect must be on 2.1 or later before brokers upgrade. The 4.0.1 notes say "Clients (including Streams and Connect) must be on version 2.1 or higher before upgrading to 4.0" |
| 4.0.0 | ReplaceField `whitelist` and `blacklist` removed; use `include` and `exclude` (medium confidence, one page) |
| 4.0.0 | `SinkTask.onPartitionsRevoked` and `onPartitionsAssigned` removed; `SourceTask.commitRecord(SourceRecord)` removed (custom plugin code) |
| 4.0.0 | MirrorMaker 1 removed; use Connect-based MirrorMaker 2. Removed MM2 keys: `use.incremental.alter.configs`, `add.source.alias.to.metrics`, `config.properties.blacklist` (use `config.properties.exclude`), `topics.blacklist` (use `topics.exclude`), `groups.blacklist` (use `groups.exclude`). KIP-1074 changed internal-topic detection in ReplicationPolicy |
| 4.1.0, 4.3.x | No Connect items found in the notes |
| 4.2.0 | `AllowlistConnectorClientConfigOverridePolicy` added (KIP-1188). `Principal` policy deprecated, removed in 5.0.0. `Allowlist` becomes the default in 5.0.0 |
| 4.4.0 | `internal.topics.automatic.creation.enable` (default `true`) and `connect-internal-topics.sh` (KIP-1209) |
| 4.4.0 | KIP-909 is not supported in Connect: `bootstrap.resolve.timeout.ms` is forced to 0 |
| 4.4.0 | The `org.apache.kafka.automatic.config.providers` allowlist is applied to dynamic broker config validation. Effect on Connect workers is (unverified) |

Stale keys to search for in connector configs:

```bash
grep -rnE 'whitelist|blacklist' connectors/
# Expected: no output after migration
```

## Upgrade steps

The 4.4 docs contain no Connect-specific rolling-upgrade procedure, so every step below that is not a cited removal is inferred (unverified).

1. Confirm Java 17 or later on every worker host (upgrade notes, Java version page).
2. Replace removed keys: ReplaceField `whitelist` and `blacklist`, MM2 `*.blacklist`.
3. Rebuild custom plugins that use the removed `SinkTask` and `SourceTask` methods.
4. Roll workers one at a time to 4.4.0 (order and procedure unverified). The incremental cooperative protocol moves only the affected tasks. `scheduled.rebalance.max.delay.ms` (default 300000) gives a departed worker 5 minutes to return ([administration](https://kafka.apache.org/44/kafka-connect/administration/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/)). Watch the rebalance metrics in [observability](./observability.md).
5. After the roll, set `connector.client.config.override.policy=Allowlist` and optionally `internal.topics.automatic.creation.enable=false`.
6. To enable exactly-once sources on an existing cluster, do two more rolling restarts: `preparing`, then `enabled` ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/)).

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Java (worker) | 17 | 25 tested | Java 17, 21 and 25 are fully supported. The compatibility page table for 4.0.0 shows Java 17 yes, Java 11 no |
| Broker protocol seen by Connect clients | 2.1 | n/a | 0.x to 2.0 not compatible, 2.1 to 2.8 limited, 3.x fully compatible |
| `connect.protocol` | `eager` | `sessioned` | The configs page default is `sessioned`; the administration page says `compatible` is the default. Two official 4.4 pages conflict (medium confidence, register U3). Leave the key unset |
| Docker image | `apache/kafka:4.4.0` | n/a | No documented Connect usage of the image (unverified) |

## Edge

Kafka 4.4.0 was released 2026-10-22; 4.4.x patch notes may follow. No active Connect CVE was searched (unverified).
