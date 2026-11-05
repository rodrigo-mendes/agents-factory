# Never-do patterns, CFK 3.4.0

Back to [SKILL.md](../SKILL.md). Each item rests on 2 or more versioned CFK 3.4 pages (S-ids in the [bibliography](./unverified-and-risks.md#source-bibliography)). The correct alternative is High confidence too.

## N1 Upgrade a ZooKeeper-based deployment to CP 8.x
Why: CP 8.0 removes ZooKeeper; migrate to KRaft first (S10, S7, S8). Impact: the brokers have no supported metadata quorum on 8.x; the exact failure mode is not documented (unverified).

```yaml
# Wrong (illustrative): ZooKeeper dependency kept while moving cp-server to 8.x
kind: Kafka
spec:
  image:
    application: confluentinc/cp-server:8.3.0
  dependencies:
    zookeeper:
      endpoint: zookeeper.confluent.svc.cluster.local:2181
```

Correct, in order:
1. From CP 7.6.x or earlier, upgrade to 7.9 on ZooKeeper.
2. Migrate to KRaft with `KRaftMigrationJob` (isolated controllers only; rollback possible until finalize).
3. Upgrade the KRaft deployment to 8.x: controllers, brokers, metadata version, other components.

## N2 Upgrade CFK to 3.4.0 without updating the init container image
Why: `cfkprober` is missing, so the exec liveness probe fails open (S6, S7). Impact: Kubernetes reports dead components as live and does not restart them.

```yaml
# Wrong: old tag left after a CFK 3.4.0 upgrade
spec:
  image:
    init: confluentinc/confluent-init-container:3.3.0
# Correct
spec:
  image:
    init: confluentinc/confluent-init-container:3.4.0
```

## N3 Upgrade to CFK 3.4.0 without checking heap
Why: the upgrade lowers any default heap above the cap and rolls the cluster once (S1, S7, S21). Impact: a smaller heap and an unplanned restart; the performance effect is not documented (unverified).

```yaml
# Wrong: no jvm override; relied on the CFK 3.3 default (100% of requests.memory)
kind: Kafka
spec:
  podTemplate:
    resources:
      requests:
        memory: 64Gi
# Correct
kind: Kafka
spec:
  configOverrides:
    jvm:
      - "-Xms6G"
      - "-Xmx6G"
```

## N4 Run a one- or two-broker Kafka cluster
Why: not supported for development, testing or production (S22). CFK sets a default replication factor of 3 (S20). Impact: an unsupported topology; topics at the default replication factor cannot be fully replicated (inference, unverified).

```yaml
# Wrong
kind: Kafka
spec:
  replicas: 1
# Correct
kind: Kafka
spec:
  replicas: 3
```

## N5 Leave pre-8.0 deprecated configurations when moving to CP 8.x
Why: they prevent brokers from starting (S7, S8).

```yaml
# Wrong
kind: Kafka
spec:
  configOverrides:
    server:
      - message.format.version=3.0
      - log.segment.bytes=524288
# Correct
kind: Kafka
spec:
  configOverrides:
    server:
      - log.segment.bytes=1048576
```

## N6 Plan to add authentication to an existing listener later
Why: CFK deploys listeners without authentication (S16) and cannot enable or change the mechanism on existing listeners (S24).

```yaml
# Wrong: no authentication "for now"
kind: Kafka
spec:
  listeners:
    internal: {}
# Correct (listener block shape from the API reference example, S11)
kind: Kafka
spec:
  listeners:
    internal:
      authentication:
        type: plain
        jaasConfig:
          secretRef: credential-example
      tls:
        enabled: true
```
