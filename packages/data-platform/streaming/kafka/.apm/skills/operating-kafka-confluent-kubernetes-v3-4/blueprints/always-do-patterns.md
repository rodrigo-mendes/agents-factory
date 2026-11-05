# Always-do patterns, CFK 3.4.0

Back to [SKILL.md](../SKILL.md). Each item rests on 2 or more versioned CFK 3.4 pages (S-ids are in the [bibliography](./unverified-and-risks.md#source-bibliography)). Commands are representative: adapt namespace and names.

## A1
Pin the CFK and CP pair to a supported row of the compatibility table (S1, S2). CFK 3.4.x supports CP 7.6 to 8.4, Kubernetes 1.29 to 1.37, OpenShift 4.15 to 4.22. A CP-only upgrade must stay in the range (S7).

```bash
helm list -n <namespace>
kubectl get kafka <kafka-name> -n <namespace> -o jsonpath='{.status.currentClusterVersion}'
```

## A2
Run KRaft for any CP 8.x deployment (S10, S7, S8). CP 8.0 removes ZooKeeper. From 7.6.x or earlier go to 7.9 on ZooKeeper, migrate in 7.9, then upgrade to 8.0. From 7.7.x or later migrate on the current version, then upgrade (S8). KRaftController example as published (S9):

```yaml
kind: KRaftController
metadata:
  name: kcontroller
  namespace: operator
spec:
  replicas: 3
  listeners:
    controller:
      authentication:
        type: plain
        jaasConfig:
          secretRef: kraft-secret
      tls:
        enabled: true
  configOverrides:
    server:
      - default.replication.factor=3
```

## A3
`KRaftController` `spec.replicas` must be odd and at least 3 (S9, S22). Changing the value rolls the cluster (S9). See A2 (`replicas: 3`).

## A4
The controller listener carries node-to-node traffic on port 9074. Authentication and TLS must match on both sides (S9, S16). Kafka side (S9):

```yaml
kind: Kafka
metadata:
  name: kafka
  annotations:
    platform.confluent.io/broker-id-offset: 10
spec:
  dependencies:
    kRaftController:
      clusterRef:
        name: kcontroller
        namespace: operator
      controllerListener:
        authentication:
          type: plain
          jaasConfig:
            secretRef: secret
        tls:
          enabled: true
```

## A5
"By default, CFK configures Kafka, KRaft, and MDS without authentication" (S16). The mechanism cannot be enabled or changed on existing listeners (S24). Server-side SASL/PLAIN skeleton (S16):

```yaml
kind: <Kafka or kRaftController>
spec:
  listeners:
    <listener type>:
      authentication:
        type: plain
        jaasConfig:
          secretRef:
```

Secret keys: `plain-users.json` and `plain-interbroker.txt` (server side), `plain.txt` (client side), `plain-jaas.conf` (pass-through). Secret files must use LF line endings (S16).

## A6
For simple ACLs set `type: simple` in the KRaftController CR as well as the Kafka CR (S19). For RBAC the KRaftController CR needs `authorization.type: rbac`, `superUsers` and `dependencies.mdsKafkaCluster` (S18).

```yaml
kind: KRaftController
spec:
  authorization:
    type: simple
    superUsers:
```

## A7
One- or two-broker setups are not supported for development, testing or production (S22). Do not set `replicas` below 3: CFK sets a default replication factor of 3 (S20).

```yaml
kind: Kafka
spec:
  replicas: 3
```

## A8
The storage page recommends `WaitForFirstConsumer` (S12). The multi-AZ page requires it so volumes land in the pod's zone (S26). The storage class of existing PVCs cannot be changed (S24).

```yaml
spec:
  storageClass:
    name: my-storage-class
```

## A9
The upgrade procedure blocks reconciliation (step 2) and enables it again at step 8, so one rolling restart applies the chart and the init container change (S6). 3.4.0 adds the two plugin commands (S1).

```bash
kubectl confluent block-reconcile --namespace <namespace>
# helm upgrade, init container change
kubectl confluent enable-reconcile --namespace <namespace>
```

## A10
Without the 3.4.0 init container, `cfkprober` is missing and the exec liveness probe fails open, reporting components live when they are not (S6, S7). The CP upgrade page checks that the init tag matches the CFK version (S8).

```bash
kubectl patch kafka <CR name> -n <namespace> --type merge -p '{"spec":{"image":{"init":"confluentinc/confluent-init-container:3.4.0"}}}'
```

## A11
3.4.0 default heap: brokers min(50% of `requests.memory`, 32Gi), controllers min(80%, 32Gi). "If you don't, the upgrade reduces the heap to the cap" (S1). The change triggers a one-time rolling restart (S7); the resources page has the same formulas (S21). In CFK 3.3 the default was 100% of the pod memory request (S1).

```yaml
spec:
  configOverrides:
    jvm:
      - "-Xms6G"
      - "-Xmx6G"
```

## A12
Leftover `message.format.version`, or `segment.bytes` below 1 MiB, prevent brokers from starting on 8.0 or later (S8). The overview lists the three settings to remove and the 1048576-byte minimum (S7).

```yaml
kind: KafkaTopic
spec:
  configs:
    segment.bytes: "1048576"
```

## A13
Both pages say the Centralized Connect License does not work with `confluentinc/cp-kafka-connect` (S25, S3). Use `cp-server-connect`. Assembly, not a published example (unverified):

```yaml
kind: Connect
spec:
  image:
    application: confluentinc/cp-server-connect:<cp-tag>
    init: confluentinc/confluent-init-container:3.4.0
```
