# Install, KRaftController and Kafka CRs, CFK 3.4.0

Back to [SKILL.md](../SKILL.md). Commands are representative: adapt to your environment. S-ids are in the [bibliography](./unverified-and-risks.md#source-bibliography).

## Install the operator (S5)

```bash
kubectl create namespace confluent
helm repo add confluentinc https://packages.confluent.io/helm
helm repo update
helm upgrade --install confluent-operator \
  confluentinc/confluent-for-kubernetes \
  --namespace confluent
kubectl get pods -n confluent        # Expected: confluent-operator  1/1  Running
```

- CRDs are managed by the operator at startup: `manageCRDs` is `true` by default (`false` on OpenShift). CRDs only move up, are never deleted, and a downgrade is blocked (S1, S6).
- Install methods (Helm repo, bundle, OperatorHub) and tradeoffs: see [ask-first](./ask-first-decisions.md#install-method-and-crd-management-c4) (medium confidence).
- Namespaced versus cluster-wide operator scope and the Helm values for it were not read (unverified).

## Custom resources (S11)

API group `platform.confluent.io/v1beta1`; the 3.4 API reference lists 28 kinds, including `Kafka`, `KRaftController`, `Zookeeper`, `KRaftMigrationJob`, `Connect`, `Connector`, `SchemaRegistry`, `Schema`, `ControlCenter`, `KsqlDB`, `KafkaRestProxy`, `KafkaRestClass`, `KafkaTopic`, `ConfluentRolebinding`, `ClusterLink`, `Gateway`, `USMAgent` and the Flink kinds. The API reference page does not render field-level `KafkaSpec` docs (L3).

Brokers and KRaft controllers run `confluentinc/cp-server` (Confluent Server) (S11, S8, S28). Other images: Connect `cp-server-connect`, Schema Registry `cp-schema-registry`, ksqlDB `cp-ksqldb-server`, REST Proxy `cp-kafka-rest`, ZooKeeper `cp-zookeeper`, Control Center `cp-enterprise-control-center-next-gen`, Replicator `cp-enterprise-replicator` (S15, S25, S8, S28). Whether CFK accepts the community `cp-kafka` image is not documented (unverified, I1).

## KRaftController and Kafka CRs

Official examples for both CRs are in [always-do A2 and A4](./always-do-patterns.md#a2). Rules from the KRaft page (S9):
- `replicas` odd, at least 3; changing it rolls the cluster.
- `default.replication.factor=3` under `configOverrides.server` is required.
- Isolated mode only for ZooKeeper migration (S10); combined nodes are not supported there.
- Do not set both `zookeeper` and `kRaftController` in `Kafka.spec.dependencies` (medium confidence, see [ask-first](./ask-first-decisions.md#single-source-cautions-not-never-do-candidates)).

## Production-shaped cluster (assembly)

(unverified) Every field comes from a cited page, but the combination was not found as one example. Field placement of `oneReplicaPerNode`, `podTemplate` and `spec.tls.secretRef` is taken from page prose, because the Kafka field reference was not rendered (I3). Check with `kubectl explain kafka.spec` against the installed CRDs.

```yaml
# CFK 3.4.0, CP 8.x. Sources: S9, S11, S12, S15, S16, S19, S21, S26, S27
apiVersion: platform.confluent.io/v1beta1
kind: KRaftController
metadata:
  name: kraftcontroller
  namespace: confluent
spec:
  replicas: 3
  image:
    application: confluentinc/cp-server:<cp-8.x-tag>
    init: confluentinc/confluent-init-container:3.4.0
  dataVolumeCapacity: 64Gi            # sizing table: 64 GB SSD minimum (S22)
  storageClass:
    name: <waitforfirstconsumer-retain-class>
  oneReplicaPerNode: true
  authorization:
    type: simple
    superUsers:
      - User:kafka
  listeners:
    controller:
      authentication:
        type: plain
        jaasConfig:
          secretRef: kraft-secret
      tls:
        enabled: true
  tls:
    secretRef: kraft-tls
  configOverrides:
    server:
      - default.replication.factor=3
---
apiVersion: platform.confluent.io/v1beta1
kind: Kafka
metadata:
  name: kafka
  namespace: confluent
spec:
  replicas: 3
  image:
    application: confluentinc/cp-server:<cp-8.x-tag>
    init: confluentinc/confluent-init-container:3.4.0
  dataVolumeCapacity: 1Ti             # minimum per broker (S22)
  storageClass:
    name: <waitforfirstconsumer-retain-class>
  oneReplicaPerNode: true
  podTemplate:
    resources:
      requests:
        cpu: "4"
        memory: 16Gi                  # minimum broker (S22)
  authorization:
    type: simple
    superUsers:
      - User:kafka
  tls:
    secretRef: kafka-tls
  listeners:
    internal:
      authentication:
        type: plain
        jaasConfig:
          secretRef: credential
      tls:
        enabled: true
  dependencies:
    kRaftController:
      clusterRef:
        name: kraftcontroller
        namespace: confluent
      controllerListener:
        authentication:
          type: plain
          jaasConfig:
            secretRef: credential
        tls:
          enabled: true
```

## Quick start and teardown

The KRaft quick start applies `confluent-platform-c3++.yaml` from `confluentinc/confluent-kubernetes-examples` on the master branch. That repository was not read and a master-branch file is not pinned to 3.4.0 (unverified, U7). Teardown order from the quick start (S13): applications, platform CRs, operator (`helm uninstall confluent-operator`), namespace. Deleting a `Kafka` CR with reclaim policy `Delete` deletes the data (S12) (medium confidence).

## Verification

```bash
kubectl get pods -n <namespace>                       # confluent-operator 1/1 Running (S5)
kubectl get kraftcontroller -n <namespace>            # STATUS RUNNING (S8)
kubectl get kafka -n <namespace>                      # STATUS RUNNING (S8)
kubectl get pod kafka-0 -n <namespace> -o jsonpath='{.spec.containers[*].image}'
kubectl explain kafka.spec                            # field placement check (unverified as a documented step)
```

## Connect, Schema Registry, Control Center pointers

- Connect: distributed mode only; `spec.mountedSecrets` mount at `/mnt/secrets/<secret-name>`; declarative `Connector` CR since CFK 2.1.0 (S25). Connect and Schema Registry use no persistent volumes (S12).
- Schema Registry internals are out of scope: use `managing-event-schemas-confluent-v8-4`.
- Control Center: `cp-enterprise-control-center-next-gen` with Prometheus and Alertmanager images on the Control Center release tag (S8). Deleting the `ControlCenter` CR deletes its PVCs (S23).
- ZooKeeper (CP 7.6 to 7.9 only): the `Zookeeper` CR exists (S11); set the replica count only at first deploy (S20).
