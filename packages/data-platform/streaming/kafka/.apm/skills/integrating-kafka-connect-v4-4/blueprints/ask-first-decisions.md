# Ask-first decisions, Kafka Connect 4.4.0

Back to [SKILL.md](../SKILL.md). Each section gives options, tradeoff and the question to ask. Single-page and inferred items are tagged here and stay out of Always Do. All pages read 2026-11-04.

## Standalone or distributed

Source: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Standalone | One process, connector files on the command line, offsets in `offset.storage.file.filename` | No fault tolerance | Local dev, single-host agents |
| Distributed | Balancing, scaling, fault tolerance, REST-only management | Needs 3 internal topics, group membership, REST security | Any shared or production use |

Ask: "Does the workload need fault tolerance or exactly-once source delivery? If yes, distributed." The statement that standalone cannot give exactly-once rests on one page (medium confidence).

## Error tolerance and DLQ

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/). Full detail in [error-handling-dlq](./error-handling-dlq.md).

Ask: "Are skipped records acceptable, and who drains the DLQ?" Never pick `errors.tolerance=all` without a DLQ silently.

## Exactly-once source connectors

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/), [connector development guide](https://kafka.apache.org/44/kafka-connect/connector-development-guide/).

- Worker: `exactly.once.source.support` is `disabled` (default), `enabled` or `preparing`. New cluster: `enabled` on every worker. Existing cluster: two rolling restarts, first `preparing`, then `enabled`.
- Connector: `exactly.once.support` is `requested` (default) or `required`. With `required`, preflight validation fails if the connector cannot provide it. `transaction.boundary` is `poll` (default), `interval` (with `transaction.boundary.interval.ms`) or `connector`. `offsets.storage.topic` gives the connector its own offsets topic.
- `offset.flush.timeout.ms` has no effect on exactly-once source connectors.
- Secured cluster ACLs: worker needs Write and Describe on TransactionalId `connect-cluster-${groupId}`. Source tasks need Write and Describe on TransactionalId `${groupId}-${connector}-${taskId}` and Describe on the offsets topic.
- Downstream readers see only committed data with `isolation.level=read_committed`. For sinks set the worker property `consumer.isolation.level=read_committed`, or `consumer.override.isolation.level` if the policy allows it.
- The connector design decides whether exactly-once is possible.

```properties
# every distributed worker, Kafka Connect 4.4.0
exactly.once.source.support=enabled
```

Ask: "Does the source connector declare exactly-once support, and is this a new or an existing cluster (one rolling restart or two)?"

## Internal topic auto-creation (new in 4.4.0)

Sources: [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [4.4.0 announcement](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/). `internal.topics.automatic.creation.enable` (default `true`) covers the offset, config and status topics and connector-specific `offsets.storage.topic` topics. With `false`, a missing internal topic makes the worker fail at startup.

The topics must exist before workers start either way. Ask: "Who creates the internal topics: IaC (then set `false` and create them first) or the 4.4 auto-creation setting?"

## REST authentication

Source: [security model](https://kafka.apache.org/44/security/security-model-connect/) only (medium confidence). Options: a reverse proxy (mTLS, OIDC, basic auth), or `rest.extension.classes` with `BasicAuthSecurityRestExtension` (JAAS HTTP basic auth). The reference `PropertyFileLoginModule` is not intended for production because it stores credentials in cleartext (medium confidence). Authentication identifies the caller; there is no per-connector authorization. The full class names are (unverified).

Ask: "Which identity system fronts the platform? Prefer a proxy if one exists." The proxy is an option here only; the Never Do alternative is trusted network and HTTPS.

## Converters

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/) for semantics (medium confidence), [sample worker file](https://raw.githubusercontent.com/apache/kafka/4.4/config/connect-distributed.properties). The converter sets the format of keys and values in Kafka and is independent of the connector. The sample uses `org.apache.kafka.connect.json.JsonConverter` with `schemas.enable=true`. Setting both `key.converter.schemas.enable` and `value.converter.schemas.enable` to `false` gives schemaless JSON. A connector may override the worker converters. `header.converter` defaults to `SimpleHeaderConverter` ([configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/)). Avro or Protobuf need a vendor Schema Registry converter: out of scope.

Ask: "Which format do consumers expect, and does a schema registry exist?"

## Internal topic shape and replication

All three topics are replicated ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/)). Shape claims (medium confidence, M14, user guide only): config topic one partition, offset topic many partitions, status topic several partitions, all compacted. Factor claims (medium confidence, M15, configs only): `config.storage.replication.factor`, `offset.storage.replication.factor` and `status.storage.replication.factor` default to 3; -1 means the broker default. The 4.4 defaults are 25 offset partitions and 5 status partitions.

```properties
config.storage.replication.factor=3
offset.storage.replication.factor=3
status.storage.replication.factor=3
offset.storage.partitions=25
status.storage.partitions=5
```

Ask: "Do you accept this topic shape, or does IaC provision the topics?"

## Connect cluster group.id

Source: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/) only (medium confidence, M16). `group.id` names the Connect cluster and must not conflict with consumer group IDs.

```properties
group.id=connect-cluster-orders
```

Ask: "Which group.id does each Connect cluster use?"

## Plugin layout

Source: [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/) only (medium confidence, M17). For class-loading isolation, place each plugin and its dependencies in its own direct child directory of `plugin.path`. Paths may be JAR or ZIP archives, uber-jars or directories; each child directory is scanned recursively.

```text
/opt/connect-plugins/            <- plugin.path=/opt/connect-plugins
├── my-jdbc-connector/           <- one plugin plus its dependency JARs
└── my-custom-smt/
```

Ask: "Where are plugins installed?"

## Plugin discovery mode

Source: [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/). `only_scan` (reflection, compatible with all plugins), `hybrid_warn` (default), `hybrid_fail` (startup fails on plugins without manifests), `service_load` (fastest startup).

Ask: "Do all installed plugins ship ServiceLoader manifests before choosing `service_load`?"

## SMT and predicate chains

Source: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/). Built-in SMTs in 4.4: Cast, DropHeaders, ExtractField, Filter, Flatten, HeaderFrom, HoistField, InsertField, InsertHeader, MaskField, RegexRouter, ReplaceField, SetSchemaMetadata, TimestampConverter, TimestampRouter, ValueToKey. Built-in predicates: TopicNameMatches (`pattern`), HasHeaderKey (`name`), RecordIsTombstone. A transform may set `predicate` and `negate`. The fully qualified class names used below are (unverified), because the page lists SMTs by short name.

```json
{
  "transforms": "dropFoo",
  "transforms.dropFoo.type": "org.apache.kafka.connect.transforms.Filter",
  "transforms.dropFoo.predicate": "isFoo",
  "predicates": "isFoo",
  "predicates.isFoo.type": "org.apache.kafka.connect.transforms.predicates.TopicNameMatches",
  "predicates.isFoo.pattern": "foo"
}
```

Ask: "Is this simple per-record logic (SMT), or does it need joins or aggregation (Kafka Streams, out of scope)?" ReplaceField `whitelist` and `blacklist` were removed in 4.0.0; use `include` and `exclude` (medium confidence, one page: [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/)).

## Plugin path variables

`plugin.path` must not use config provider variables ([configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/), one page, medium confidence). Use a literal path such as `plugin.path=/opt/connect-plugins`.

## Secured cluster client settings

Source: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/) only (medium confidence). Only `bootstrap.servers` is inherited without a prefix from the worker config. Set security settings unprefixed (worker clients), with `producer.` (source tasks) and with `consumer.` (sink tasks). The SASL mechanism and JAAS settings belong to `operating-kafka-v4-4`.

Ask: "Which security protocol do the brokers use?"

## Open conflicts and gaps

- `connect.protocol` default: the configs page says `sessioned`, the administration page says `compatible` (medium confidence). Leave the key unset. See register item U3.
- Running Connect from `apache/kafka:4.4.0` is not documented (unverified). See [deploy-compose](./deploy-compose.md).
- No Connect rolling-upgrade procedure exists in the 4.4 docs (unverified). See [migration-guide](./migration-guide.md).
