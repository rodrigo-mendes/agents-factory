# Install, Kafka CR, KafkaNodePool, KRaft, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). Evidence is the 1.3.0 docs; 1.3.1 has no versioned docs (register I1). Do not reuse the older shared operator guide (v1beta2, 0.40.0). Commands are representative.

## KRaft facts

Sources: [KRaft assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-kraft-mode.adoc), [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html).

- A cluster is one `Kafka` plus at least one `KafkaNodePool`. Strimzi 1.3.x is KRaft only.
- Node pool settings (resources, JVM options, templates) take precedence over the `Kafka` resource and are not merged with `Kafka.spec.kafka.template`.
- For broker-level settings see skill `operating-kafka-v4-4`; its 4.4-only facts do not apply here: Kafka 4.4.0 is not in the Strimzi 1.3.0 supported list (https://strimzi.io/downloads/, read 2026-11-04).

## Step 1. Install the Cluster Operator

Option A, YAML files (steps from the [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), single source, medium confidence):

```bash
kubectl create namespace my-cluster-operator-namespace
sed -i 's/namespace: .*/namespace: my-cluster-operator-namespace/' install/cluster-operator/*RoleBinding*.yaml
kubectl create -f install/cluster-operator -n my-cluster-operator-namespace
kubectl get deployments -n my-cluster-operator-namespace
# Expected: strimzi-cluster-operator with AVAILABLE 1
```

Release artifacts come from the GitHub releases ([downloads](https://strimzi.io/downloads/)). On macOS use `sed -i ''`. Optional roles: `kubectl create -f install/strimzi-admin`.

Option B, Helm OCI ([Helm README](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/helm-charts/helm3/strimzi-kafka-operator/README.md) names the chart and the values `watchNamespaces`, `watchAnyNamespace`, `featureGates`, `resources`). The flags below are assembled (unverified):

```bash
helm install my-strimzi-cluster-operator oci://quay.io/strimzi-helm/strimzi-kafka-operator \
  --namespace strimzi-system --create-namespace --version 1.3.0 --set watchNamespaces="{kafka}"
```

Chart 1.3.0 is in the classic index ([index](https://strimzi.io/charts/index.yaml)); a 1.3.1 chart is not confirmed (unverified, U1). Restricted Pod Security Standard is the default for operator YAML and Helm (CHANGELOG, partly read, medium confidence).

## Kafka cluster official example

Source: [kafka-persistent.yaml at tag 1.3.0](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/examples/kafka/kafka-persistent.yaml). The `broker` pool is identical to `controller` except `name: broker` and `roles: [broker]` (the file defines both).

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
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 100Gi
        kraftMetadata: shared
---
apiVersion: kafka.strimzi.io/v1
kind: Kafka
metadata:
  name: my-cluster
spec:
  kafka:
    version: 4.3.1
    metadataVersion: 4.3-IV0
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
  entityOperator:
    topicOperator: {}
    userOperator: {}
```

The official example has no `strimzi.io/node-pools` or `strimzi.io/kraft` annotations. Whether 1.3.x ignores or rejects them is (unverified, U2). The `plain` listener has no authentication: production needs [security-listeners-auth](./security-listeners-auth.md).

## Hardened production overlay (assembled, unverified)

Moved to [hardened-overlay](./hardened-overlay.md).

## Node IDs (medium confidence)

Source: [node pool IDs](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-managing-node-pools-ids.adoc) (single source). Node IDs run 0 to 999 unless `reserved.broker.max.id` is raised.

```bash
kubectl annotate kafkanodepool broker strimzi.io/next-node-ids="[0,1,2,10-20,30]"
kubectl annotate kafkanodepool broker strimzi.io/remove-node-ids="[3]"
```

## Verify

All commands below are assembled checks (unverified, U6):

```bash
kubectl get kafka my-cluster -n kafka -o yaml            # status conditions
kubectl get kafkanodepool -n kafka                       # pools and replicas
kubectl get pods -n kafka                                # broker, controller and entity-operator pods Running
kubectl apply --dry-run=server -f kafka-persistent.yaml  # validate against the installed 1.3.x CRDs
```
