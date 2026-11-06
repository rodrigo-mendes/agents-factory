# Never-do patterns, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). Every row rests on at least two versioned official pages and has a High-confidence alternative, except the descriptive list of removed or deprecated APIs, which cites the upgrade notes only. All sources read 2026-11-04. Single-page warnings (native image, `allow.everyone.if.no.acl.found=true`, SASL/PLAIN without TLS, combined controller mode, publishing the controller port, stretching one cluster across datacenters) are not here: see [ask-first-decisions](./ask-first-decisions.md).

## Official Compose examples used unchanged (risk: high)

Why: the 4.4 examples set replication factors and min ISR to 1 and `KAFKA_LOG_DIRS` to `/tmp/kraft-combined-logs`, with no volume. The README says the SSL example is not for production, and that example sets `ssl.endpoint.identification.algorithm` to an empty string (hostname verification off) and reuses one credential set across brokers. Sources for the example contents (branch head, supporting): [examples README](https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/README.md), [isolated example](https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/docker-compose-files/cluster/isolated/plaintext/docker-compose.yml), [combined example](https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/docker-compose-files/cluster/combined/plaintext/docker-compose.yml). Sources for the RF 1 and min ISR 1 risk: [design](https://kafka.apache.org/44/design/design/), [topic configs](https://kafka.apache.org/44/configuration/topic-configs/).

```yaml
# 🚫 WRONG
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
KAFKA_LOG_DIRS: '/tmp/kraft-combined-logs'
KAFKA_SSL_ENDPOINT_IDENTIFICATION_ALGORITHM: ''
# ✅ CORRECT
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3   # a persistent volume backs KAFKA_LOG_DIRS; SSL endpoint identification stays at default https
```

Alternative: RF 3, min ISR 2 and a persistent volume (medium confidence, M1). The assembled layout is in [deploy-compose](./deploy-compose.md), which is not itself a High claim (path, medium confidence, M1; image details, U3).

Detection: `grep -nE "REPLICATION_FACTOR: 1|MIN_ISR: 1|/tmp/|ENDPOINT_IDENTIFICATION_ALGORITHM: ''" docker-compose*.yml`. See [deploy-compose](./deploy-compose.md).

## Strong acks with min.insync.replicas=1 (risk: critical)

Why: with `acks=all` the write is acknowledged by the current in-sync replicas. If the ISR shrinks to the leader and `min.insync.replicas` is the default 1, one more failure loses acknowledged data ([design](https://kafka.apache.org/44/design/design/), [topic configs](https://kafka.apache.org/44/configuration/topic-configs/)).

```bash
# 🚫 WRONG: min.insync.replicas left at default 1
kafka-topics.sh --create --topic orders --replication-factor 3 --partitions 6 --bootstrap-server kafka-1:19092
# ✅ CORRECT
kafka-topics.sh --create --topic orders --replication-factor 3 --partitions 6 --config min.insync.replicas=2 --bootstrap-server kafka-1:19092
```

Detection: `kafka-configs.sh --bootstrap-server kafka-1:19092 --entity-type topics --entity-name orders --describe | grep min.insync`.

## Unclean leader election (risk: high)

Why: Kafka by default waits for a consistent replica; enabling unclean election can elect a replica missing committed data ([design](https://kafka.apache.org/44/design/design/), [topic configs](https://kafka.apache.org/44/configuration/topic-configs/)). Alternative: `unclean.leader.election.enable=false` (default). Detection: `kafka-configs.sh --bootstrap-server kafka-1:19092 --entity-type brokers --entity-default --describe --all | grep unclean`.

## Adding partitions to keyed topics without a plan (risk: moderate)

Why: adding partitions changes `hash(key) % partitions` and breaks per-key ordering; consumers with `auto.offset.reset=latest` can skip records; partitions can never be reduced ([operations](https://kafka.apache.org/44/operations/basic-kafka-operations/), [consumer configs](https://kafka.apache.org/44/configuration/consumer-configs/)). Alternative: size partitions up front; if you must expand, use `auto.offset.reset=by_duration:PT5S` (consumer protocol) or `PT6M` (classic).

## ZooKeeper settings on 4.4

Why: 4.0 and later run entirely without ZooKeeper, so ZooKeeper configs such as `zookeeper.connect` do not apply ([KRaft vs ZooKeeper](https://kafka.apache.org/44/getting-started/zk2kraft/), [4.0.0 announcement](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/)). Alternative: KRaft settings. For a ZooKeeper cluster use skill `operating-kafka-v3-9`. The removed-config list is in [migration-guide](./migration-guide.md).

## Removed or deprecated APIs and configs

- `alterConfigs` is removed; use `incrementalAlterConfigs` ([upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/)).
- `broker.id` is deprecated; use `node.id` (same page).
- `kafka-broker-api-versions.sh` is deprecated; use `kafka-cluster.sh api-versions` (same page).
- Removed configs: `log.message.format.version`, `message.format.version`, `delegation.token.master.key`, `offsets.commit.required.acks`, `log.message.timestamp.difference.max.ms` (same page). Alternative: delete them from the config.

## Older broker on a directory formatted by the 4.4 tool

Why: since KIP-1170 a broker must be the same version as, or newer than, the `kafka-storage` tool that formatted the directory ([upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [4.4.0 announcement](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/)). Alternative: run a broker equal to or newer than the formatting tool.
