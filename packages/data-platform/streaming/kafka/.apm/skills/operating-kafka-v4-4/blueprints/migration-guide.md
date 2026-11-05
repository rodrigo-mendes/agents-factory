# Migration guide 3.9 to 4.4, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). S-ids resolve in the [Source Bibliography](./unverified-and-risks.md#source-bibliography). For this skill the 3.9 upgrade page was read 100000 of 233388 characters (register L4); the same page was read in full for `operating-kafka-v3-9`.

## ZooKeeper pointer (the only ZooKeeper content in this skill)

ZooKeeper mode was removed in Kafka 4.0. To run or migrate a ZooKeeper-based cluster, use skill `operating-kafka-v3-9`. Migration to KRaft happens on the 3.9 bridge release before any 4.x upgrade [S1][S6][S22]. This skill does not carry ZooKeeper configuration.

## Compatibility matrix

| From | To 4.4.0 | Direct | Notes |
|---|---|---|---|
| 3.9.x KRaft | 4.4.0 | Yes (unverified, U2) | Rolling upgrade, then `kafka-features.sh upgrade --release-version 4.4`. The 4.4 procedure heading has no body; steps come from the 4.3 and 4.2 notes [S1] |
| 3.3.x to 3.8.x KRaft | 4.4.0 | Yes (servers 3.3.x+) | The notes say KRaft clusters older than 3.3.x should go to 3.9.x first; 3.9.x is recommended [S1] |
| Any ZooKeeper-mode cluster | 4.x | No | Migrate to KRaft on 3.9 first. Use `operating-kafka-v3-9` [S6][S1] |
| 4.0 to 4.3 | 4.4.0 | Yes | Same rolling pattern [S1] |
| Clients older than 2.1 | 4.x brokers | No | Clients and brokers need 2.1+; full compatibility from 3.x [S1][S32] |

## Rolling upgrade procedure

Pattern from the 4.3 and 4.2 notes [S1]; node order is (unverified), U11. Compose commands are representative.

```bash
# 1. Per node: edit the image tag to apache/kafka:4.4.0, then recreate that one service
docker compose up -d --no-deps controller-1
# 2. Verify the node rejoined
/opt/kafka/bin/kafka-metadata-quorum.sh --bootstrap-server kafka-1:19092 describe --status
# 3. Repeat for the remaining controllers and brokers; UnderReplicatedPartitions must be 0 between brokers [S14]
# 4. Finalize feature levels
/opt/kafka/bin/kafka-features.sh --bootstrap-server kafka-1:19092 upgrade --release-version 4.4
/opt/kafka/bin/kafka-features.sh --bootstrap-controller controller-1:9093 describe
```

- Before rolling, check the 4.4 JWKS requirement: a JWKS URL needs `sasl.oauthbearer.expected.audience` and `sasl.oauthbearer.expected.issuer` or the broker fails at startup [S1].
- Do not re-format storage directories with the 4.4 tool if an older broker may run on them (KIP-1170) [S1][S23].
- Controller unregistration (KIP-1312) needs metadata version `4.4-IV2` [S1].

## Rollback

- Trigger: a node fails to rejoin, or under-replicated or offline partitions persist after the roll.
- Before finalizing, revert the image tag on the upgraded nodes.
- Whether 4.4 supports metadata downgrade is (unverified), U2. The 4.3 notes say downgrade is not supported across releases that change metadata, and 4.4 adds `4.4-IV2` [S1].
- KIP-1170: storage formatted by the 4.4 tool cannot be used by an older broker [S1].
- If Streams applications use `group.instance.id` on the streams rebalance protocol, remove it before downgrading brokers below 4.4 [S1].

## Breaking changes reaching 4.4.0 from 3.9 [S1]

- ZooKeeper removed; Java 17 required for brokers, Connect and tools; MirrorMaker 1 removed; Log4j moved to Log4j2.
- Removed configs: `log.message.format.version`, `message.format.version`, `delegation.token.master.key`, `offsets.commit.required.acks`, `log.message.timestamp.difference.max.ms`.
- `alterConfigs` removed; use `incrementalAlterConfigs`.
- Changed defaults: `linger.ms` 0 to 5; topic `message.timestamp.after.max.ms` to 1 hour (the broker-page reading conflicts, medium confidence, U6); `num.recovery.threads.per.data.dir` 1 to 2; `remote.log.manager.thread.pool.size` 10 to 2.
- 4.1: `log.cleaner.enable` deprecated, ELR on by default for new clusters, `ConfigCommand --force` removed.
- 4.2: stricter LIST config validation; `cleanup.policy` may be empty (infinite retention).
- 4.3: dynamic controller configs and `group.coordinator.rebalance.protocols` deprecated.
- 4.4: JWKS audience and issuer requirement, KIP-1170, `broker.id` and `kafka-broker-api-versions.sh` deprecated, share-group dead-letter queues (`share.version` 2), protocol decoding allocation limits [S1][S23].

## Removed ZooKeeper-era configs [S20]

All `zookeeper.*`, `control.plane.listener.name`, `controlled.shutdown.max.retries`, and `inter.broker.protocol.version` (replaced by `metadata.version`). `advertised.listeners` is no longer dynamic.

## Static to dynamic quorum

Sources conflict on whether upgrading static to dynamic voters is supported: the compatibility page (4.0 matrix) says no (KAFKA-16538), the KRaft page documents a `kraft.version=1` upgrade via `--release-version 4.1` (medium confidence, U4). Human-verify before attempting it. Do not decide for the user.
