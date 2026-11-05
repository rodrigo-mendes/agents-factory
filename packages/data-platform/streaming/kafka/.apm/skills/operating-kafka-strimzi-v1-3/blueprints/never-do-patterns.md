# Never-do patterns, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). Nine High items (two or more official documents read in full each); every alternative is High too. Single-source prohibitions are not here: see [ask-first-decisions](./ask-first-decisions.md#single-source-prohibitions-medium-confidence). Do not copy the older shared Kubernetes operator guide: it shows v1beta2, operator 0.40.0 and Kafka 3.7.0, all rejected or unsupported on 1.3.x.

## N1. ZooKeeper-based cluster on Strimzi 1.3.x

Sources: [upgrade sequence](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-sequence.adoc) ("Upgrades from ZooKeeper-based clusters are not supported"), [KRaft assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-kraft-mode.adoc), [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html).

- ❌ A `spec.zookeeper` section, or asking Strimzi 1.3.x to manage a ZooKeeper cluster. The operator cannot manage it.
- ✅ Use KRaft node pools: KRaft controllers as a node pool. For an existing ZooKeeper cluster, see the migration question in [ask-first-decisions](./ask-first-decisions.md#single-source-prohibitions-medium-confidence).

```yaml
apiVersion: kafka.strimzi.io/v1
kind: KafkaNodePool
metadata:
  name: controller
  labels:
    strimzi.io/cluster: my-cluster
spec:
  replicas: 3
  roles:
    - controller
```

## N2. Removed API versions

Sources: [1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0), [1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1), [official example](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/examples/kafka/kafka-persistent.yaml), [v1 conversion](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-api-conversion-v1.adoc).

```yaml
# ❌ removed in Strimzi 1.0.0
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
# ✅
apiVersion: kafka.strimzi.io/v1
kind: Kafka
```

Resources and CRDs from before 1.0.0 must be converted before upgrading.

## N3. Kafka 4.4.0 or any unsupported version

Sources: [downloads](https://strimzi.io/downloads/), [1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0), [1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1), [operator upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/proc-upgrade-cluster-operator.adoc).

```yaml
# ❌ 4.4.0 is not in the Strimzi 1.3.x list
spec:
  kafka:
    version: 4.4.0
# ✅ 1.3.1 (use 4.3.1 on 1.3.0)
spec:
  kafka:
    version: 4.3.2
```

## N4. Changing a controller pool

Sources: [KRaft assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-kraft-mode.adoc), [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html). Strimzi uses static KRaft quorums, so you cannot add, remove or rescale controller roles, rename a controller pool or change its storage type.

```bash
# ❌ kubectl scale kafkanodepool controller --replicas=5
# ✅ size controllers at creation (for example 3); add capacity in broker-only pools
kubectl scale kafkanodepool broker --replicas=4
```

## N5. Shrinking a PV or changing storage type

Sources: [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html) ("Decreasing the size of persistent volumes is not supported"), [API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html) (`KafkaNodePool.spec.storage` "Cannot be updated").

```yaml
# ❌ size: 50Gi when the volume was 100Gi
# ✅ plan jbod up front and grow only
storage:
  type: jbod
  volumes:
    - id: 0
      type: persistent-claim
      size: 200Gi
```

Moving data off a JBOD volume uses `KafkaRebalance` mode `remove-disks` (API reference). The JBOD reassignment procedure was not read (register L3).

## N6. Deleting pods to restart them

Sources: [rolling updates](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-rolling-updates.adoc), [manual roll](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-manual-rolling-update-pods.adoc). Deleting can conflict with Cluster Operator actions and bypasses its in-sync replica checks.

```bash
# ❌ kubectl delete pod my-cluster-broker-0
# ✅
kubectl annotate pod my-cluster-broker-0 strimzi.io/manual-rolling-update="true"
```

## N7. Scale-down with data still on the brokers

Sources: [scale-down checks](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-skipping-scale-down-checks.adoc), [scale-down](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-scaling-down-node-pools.adoc). Strimzi blocks this "to prevent possible data loss". The `strimzi.io/skip-broker-scaledown-check="true"` annotation "will likely cause a reconciliation failure" when topics remain.

```bash
# ❌ kubectl annotate kafka my-cluster strimzi.io/skip-broker-scaledown-check="true"
# ✅ run a remove-brokers KafkaRebalance (see always-do item 9), approve it, then scale
kubectl annotate kafkarebalance my-rebalance strimzi.io/rebalance="approve"
```

## N8. Assuming Helm upgrades CRDs

Sources: [Helm README](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/helm-charts/helm3/strimzi-kafka-operator/README.md), [upgrade assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/upgrading/assembly-upgrade-cluster-operator.adoc).

```bash
# ❌ helm upgrade alone leaves old CRD schemas
# ✅ apply the release CRDs first (file name unverified), then upgrade (a 1.3.1 chart is unconfirmed, unverified)
kubectl apply -f <strimzi-crds-from-the-release>
helm upgrade my-strimzi-cluster-operator oci://quay.io/strimzi-helm/strimzi-kafka-operator --version <chart-version>
```

## N9. Clear-text secrets in `custom` OAuth config

Sources: [OAuth migration](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-migration.adoc) ("Do not use sensitive values directly in the `config` section"), [OAuth server config](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-server-config.adoc).

- ❌ A client secret typed into `listenerConfig`. It leaks into the CR, etcd backups and GitOps repositories.
- ✅ Keep the secret in a Kubernetes `Secret` and read it through a Kafka configuration provider. The requirement is High; the exact placeholder syntax is (unverified), see [security-listeners-auth](./security-listeners-auth.md#oauth-20-with-custom).
