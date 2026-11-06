# Always-do patterns, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). Every item is a High claim: at least two separate official documents read in full (research date 2026-11-04). Commands are representative: adapt names. Pod names follow two patterns in the docs (register I4); discover real names first with `kubectl get pods -l strimzi.io/cluster=<name>` (unverified).

## 1. Kubernetes 1.32 or newer

Sources: [1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0), [1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1), [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), [Helm README](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/helm-charts/helm3/strimzi-kafka-operator/README.md), [downloads](https://strimzi.io/downloads/).

```bash
kubectl version   # server version must be 1.32 or newer (command wording: unverified)
```

## 2. `kafka.strimzi.io/v1` on every resource

Sources: [1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0), [1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1), [official example](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/examples/kafka/kafka-persistent.yaml).

```yaml
apiVersion: kafka.strimzi.io/v1
kind: Kafka
```

## 3. A Kafka version the operator supports

Sources: [downloads](https://strimzi.io/downloads/), [1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0), [1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1), [operator upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/proc-upgrade-cluster-operator.adoc), [upgrade paths](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-paths.adoc). An unsupported version makes the operator return an error until `spec.kafka.version` is fixed.

```yaml
# Strimzi 1.3.0 official example values
spec:
  kafka:
    version: 4.3.1
    metadataVersion: 4.3-IV0
```

On 1.3.1 the list adds 4.3.2. The `metadataVersion` for 4.3.2 is not recorded (unverified).

## 4. Node pool labelled with the cluster name

Sources: [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), [KRaft assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-kraft-mode.adoc), [official example](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/examples/kafka/kafka-persistent.yaml). A cluster needs one `Kafka` and at least one `KafkaNodePool`.

```yaml
metadata:
  labels:
    strimzi.io/cluster: my-cluster   # must equal the Kafka resource name
```

## 5. Dedicated controller and broker pools in production

Sources: same three as item 4. Dual-role nodes suit development or testing. The full official example is in [deploy-install-and-cr](./deploy-install-and-cr.md#kafka-cluster-official-example).

## 6. RF 3 and min ISR 2 before disruptive operations

Sources: [cluster upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-cluster.adoc), [manual roll](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-manual-rolling-update-pods.adoc), [topic replication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/con-topic-replication.adoc), [official example](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/examples/kafka/kafka-persistent.yaml).

```yaml
config:
  default.replication.factor: 3
  min.insync.replicas: 2
```

## 7. Upgrade order

Sources: [upgrade sequence](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-sequence.adoc), [Kafka upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/proc-upgrade-kafka-kraft.adoc), [upgrade assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/upgrading/assembly-upgrade.adoc), [v1 conversion](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-api-conversion-v1.adoc). Order: check Kubernetes, confirm KRaft, convert to the v1 API if coming from before 1.0.0, upgrade the Cluster Operator, change `spec.kafka.version` (keep `metadataVersion`), change `metadataVersion` last. Steps: [rolling-updates-and-upgrades](./rolling-updates-and-upgrades.md).

## 8. CRDs are not updated by `helm upgrade`

Sources: [Helm README](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/helm-charts/helm3/strimzi-kafka-operator/README.md), [upgrade assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/upgrading/assembly-upgrade-cluster-operator.adoc). `helm upgrade` does not update CRDs; apply the release CRDs yourself, from the release downloads or the chart's `crd` subdirectory. Whether to apply them before or after `helm upgrade`, and the exact CRD file name for 1.3.1, are not stated by a cited page (unverified, U7).

## 9. Remove-brokers rebalance before scale-down

Sources: [scale-down](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-scaling-down-node-pools.adoc), [scale-down checks](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-skipping-scale-down-checks.adoc), [optimization proposals](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-generating-optimization-proposals.adoc), [auto-rebalance](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-automating-rebalances.adoc). Full flow: [storage-and-scaling](./storage-and-scaling.md#scale-down-flow).

```yaml
apiVersion: kafka.strimzi.io/v1
kind: KafkaRebalance
metadata:
  name: my-rebalance
  labels:
    strimzi.io/cluster: my-cluster
spec:
  mode: remove-brokers
  brokers: [3]
```

## 10. Manual restart by annotation

Sources: [rolling updates](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-rolling-updates.adoc), [manual roll](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-manual-rolling-update-pods.adoc), [cluster upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-cluster.adoc). Annotate individual Pods, not the `StrimziPodSet`.

```bash
kubectl annotate pod my-cluster-broker-0 strimzi.io/manual-rolling-update="true"   # pod name: see register I4
```

## 11. Drain Cleaner

Sources: [cluster upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-cluster.adoc), [Drain Cleaner](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/drain-cleaner/proc-drain-cleaner-using.adoc). It annotates evicted pods so the Cluster Operator rolls them. With anti-affinity keep a spare worker node. The manual alternative is `maxUnavailable: 0` plus the annotation.

## 12. Retain reclaim policy

Sources: [recovery scenarios](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/con-cluster-recovery-scenarios.adoc), [recovery procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-cluster-recovery-volume.adoc). With `Retain`, "the PV retains its data and is not deleted". You must then delete PVs by hand when you remove a cluster for good. See [recovery-and-dr](./recovery-and-dr.md).

## 13. Authenticate every client listener

Sources: [listener authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-kafka-authentication.adoc), [client authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-client-authentication.adoc), [KafkaUser procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/proc-configuring-kafka-user.adoc). Without `authentication` the listener accepts all connections. See [security-listeners-auth](./security-listeners-auth.md).

## 14. Authorization `simple` for KafkaUser ACLs

Sources: [KafkaUser procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/proc-configuring-kafka-user.adoc), [authorization](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-kafka-authorization.adoc), [client ACLs](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-client-acls.adoc).

```yaml
spec:
  kafka:
    authorization:
      type: simple
```

## 15. OAuth through `custom`

Sources: [OAuth migration](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-migration.adoc), [OAuth server config](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-server-config.adoc). The `oauth` and `keycloak` types are deprecated. Skeleton in [security-listeners-auth](./security-listeners-auth.md#oauth-20-with-custom).

## 16. Rack awareness by zone

Sources: [zones](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-distributing-brokers-across-zones.adoc), [common config](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-common-configuration.adoc), [API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html). Strimzi then sets `broker.rack`. Meant for one location, not across regions.

```yaml
spec:
  kafka:
    rack:
      type: topology-label
      topologyKey: topology.kubernetes.io/zone
```

## 17. Metrics on 9404

Sources: [Metrics Reporter](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/metrics/proc-strimzi-metrics-reporter-kafka-deploy-options.adoc), [JMX exporter](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/metrics/proc-jmx-exporter-metrics-kafka-deploy-options.adoc), [listener authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-kafka-authentication.adoc) (port 9404 is reserved). Details: [observability](./observability.md).

```yaml
spec:
  kafka:
    metricsConfig:
      type: strimziMetricsReporter   # or jmxPrometheusExporter (ConfigMap-backed)
```
