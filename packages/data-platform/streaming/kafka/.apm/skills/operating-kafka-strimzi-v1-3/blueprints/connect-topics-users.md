# Connect, topics, users, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). Everything here is single-source or assembled, so it stays out of Always Do and Never Do. Connect REST API scope belongs to skill `integrating-kafka-connect-v4-4` (link only). Doc base: `https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/`.

## KafkaTopic (medium confidence)

Sources: [topic procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/proc-configuring-kafka-topic.adoc), [topic replication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/con-topic-replication.adoc), [topic handling](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/con-application-topic-handling.adoc), [API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html). Single-source procedure details, register M17.

```yaml
apiVersion: kafka.strimzi.io/v1
kind: KafkaTopic
metadata:
  name: my-topic
  labels:
    strimzi.io/cluster: my-cluster
spec:
  partitions: 10
  replicas: 3
  config:
    min.insync.replicas: 2
```

- Configuration flows one way, from `KafkaTopic` to Kafka; changes made outside the resource are reverted (medium confidence).
- Partitions can grow but not shrink (`PartitionDecreaseException`) (medium confidence).
- Deleting a topic needs `delete.topic.enable: true`, which is the default (medium confidence).
- Absent `partitions` and `replicas` fall back to the broker's `num.partitions` and `default.replication.factor` (medium confidence).
- Changing `spec.replicas` on an existing topic: one page says it needs Cruise Control, another says the replica count cannot be changed. The pages conflict (medium confidence, M16). Treat it as needing Cruise Control and ask the user.
- Running without finalizers uses the Topic Operator env var `STRIMZI_USE_FINALIZERS=false`; do not strip finalizers by hand (medium confidence, M20).

## User secrets (medium confidence)

Source: [client authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-client-authentication.adoc) (register M17).

- A `tls` user gets a secret named after the `KafkaUser` with `ca.crt`, `user.crt`, `user.key`, `user.p12` and `user.password`.
- A `scram-sha-512` user gets `password` and `sasl.jaas.config`.
- Force renewal by annotating the secret with `strimzi.io/force-renew: "true"`.
- User certificates are signed by the clients CA; clients must rotate keystores before expiry ([certificate renewal](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-certificate-renewal.adoc)).

## KafkaConnect and KafkaConnector

The YAML below was assembled from the deploying guide (sections 7.3 and 11.7) and the Connect build page; it is (unverified) as a whole (U4). Field names marked in comments were not confirmed.

```yaml
apiVersion: kafka.strimzi.io/v1
kind: KafkaConnect
metadata:
  name: my-connect-cluster
  annotations:
    strimzi.io/use-connector-resources: "true"
spec:
  version: 4.3.1                 # set explicitly (medium confidence, M7)
  replicas: 3
  bootstrapServers: my-cluster-kafka-bootstrap:9093   # service name unverified
  groupId: my-connect-cluster
  configStorageTopic: my-connect-cluster-configs
  offsetStorageTopic: my-connect-cluster-offsets
  statusStorageTopic: my-connect-cluster-status
  tls:
    trustedCertificates:
      - secretName: my-cluster-cluster-ca-cert        # secret key field unverified
        pattern: "*.crt"
  authentication:
    type: tls
    certificateAndKey:                                # field names unverified
      secretName: my-connect-user
      certificate: user.crt
      key: user.key
  config:
    connector.client.config.override.policy: None     # (medium confidence, M8)
  build:
    output:
      type: docker
      image: <registry>/my-connect:1.0.0
      pushSecret: my-registry-credentials
    plugins:
      - name: my-plugin
        artifacts:
          - type: tgz
            url: <artifact-url>
            sha512sum: <sha512>                       # (medium confidence, M6)
---
apiVersion: kafka.strimzi.io/v1
kind: KafkaConnector
metadata:
  name: my-source-connector
  labels:
    strimzi.io/cluster: my-connect-cluster   # same namespace as KafkaConnect
spec:
  class: <connector-class>
  tasksMax: 2
  state: running                             # other values unverified beyond "stop or pause with state"
```

Single-source facts (medium confidence, M5, M6, M17):

- `replicas`, `groupId` and the three storage topics are required in the v1 API ([API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html), [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- "If you enable `KafkaConnector` resources before creating them, you delete all connectors" (M5).
- A wrong plugin URL or checksum fails the build and leaves Connect unchanged ([Connect build](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-config-kafka-connect-build.adoc)).
- Restart a connector with the `strimzi.io/restart` annotation (options `includeTasks`, `onlyFailed`), a task with `strimzi.io/restart-task`, and manage offsets with `strimzi.io/connector-offsets` (`list`, `alter` or `reset`).
- Buildah is the only image builder in 1.3.x ([1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0)).
- Do not change Connect internal topic replication factors after creation (see [ask-first-decisions](./ask-first-decisions.md#single-source-prohibitions-medium-confidence)).
