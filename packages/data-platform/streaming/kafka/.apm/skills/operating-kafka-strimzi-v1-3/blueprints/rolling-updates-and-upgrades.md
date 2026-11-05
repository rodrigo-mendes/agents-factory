# Rolling updates and upgrades, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). Doc base: `https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/`. Downgrade modules were not read (register L3). Commands are representative.

## Manual rolling update

Sources: [rolling updates](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-rolling-updates.adoc), [manual roll](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-manual-rolling-update-pods.adoc), [cluster upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-cluster.adoc).

- Going through the Cluster Operator avoids conflicts with its own operations and respects in-sync replica rules. Annotate Pods directly, not the `StrimziPodSet`.
- For availability the topics need RF 3 or more and `min.insync.replicas` one less than RF.
- Reconciliation runs every two minutes by default (medium confidence, M17).

```bash
kubectl annotate pod <cluster>-<pool>-<id> strimzi.io/manual-rolling-update="true"
# list real pod names first: kubectl get pods -l strimzi.io/cluster=<name>   (unverified, I4)
```

## Kubernetes node drains

Sources: [cluster upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-cluster.adoc), [Drain Cleaner](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/drain-cleaner/proc-drain-cleaner-using.adoc).

- Recommended: Drain Cleaner, which annotates evicted pods so the Cluster Operator rolls them.
- Manual alternative: `maxUnavailable: 0` on the PDB plus the manual-rolling-update annotation.
- With anti-affinity keep a spare worker node.

## Upgrade sequence

Sources: [upgrade sequence](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-sequence.adoc), [upgrade paths](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-paths.adoc), [v1 conversion](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-api-conversion-v1.adoc).

1. Check Kubernetes is 1.32 or newer.
2. Confirm the cluster is KRaft. Upgrades from ZooKeeper-based clusters are not supported.
3. Coming from before 1.0.0, convert custom resources and CRDs to the `v1` API first.
4. Upgrade the Cluster Operator.
5. Change `spec.kafka.version`, then `metadataVersion` last.

Incremental (one minor) and multi-version upgrades are both supported. Temporary errors in multi-version upgrades "can typically be resolved during the upgrade". Test the path in a controlled environment. Previous operator for a direct upgrade: 1.3.0 (per the 1.3.1 notes), 1.2.0 (per the 1.3.0 notes).

## Operator upgrade, YAML method

Sources: [operator upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/proc-upgrade-cluster-operator.adoc), [upgrade assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/upgrading/assembly-upgrade-cluster-operator.adoc).

1. Record changes you made to the old installation files; the upgrade overwrites them.
2. Update custom resources to options the target version supports; review `STRIMZI_FEATURE_GATES`.
3. Set the namespace in the new files: `sed -i 's/namespace: .*/namespace: my-cluster-operator-namespace/' install/cluster-operator/*RoleBinding*.yaml` (unverified, U6).
4. Carry over env vars in `060-Deployment-strimzi-cluster-operator.yaml`: `STRIMZI_NAMESPACE`, and `STRIMZI_ENTITY_OPERATOR_WATCHED_NAMESPACE_ENABLED=true` if needed.
5. Recreate the RoleBindings or ClusterRoleBindings for the watched namespaces.
6. `kubectl replace -f install/cluster-operator`, then wait for the rolling updates.
7. If an unsupported-Kafka-version error appears, set `spec.kafka.version` to a supported one.
8. Verify the image tag (Strimzi version, then Kafka version): `kubectl get pods <broker-pod> -o jsonpath='{.spec.containers[0].image}'` (unverified, U6).

Helm: `helm upgrade`, then apply the new CRDs by hand. OLM: change the subscription channel and prefer version-specific channels. Same method as the first install.

## Kafka upgrade (KRaft)

Source: [Kafka upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/proc-upgrade-kafka-kraft.adoc), with [upgrade sequence](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-sequence.adoc).

1. `kubectl edit kafka <name>`. Check that any configured `metadataVersion` is supported by the target Kafka version.
2. Change `spec.kafka.version`; keep `metadataVersion` unchanged. If `spec.kafka.image` is set, change it too.
3. Wait for the rolling update.
4. Update `KafkaConnect.spec.version` and `KafkaMirrorMaker2.spec.version`; rebuild custom images on the new base image.
5. Set `spec.kafka.metadataVersion` to the new value. If unset, Strimzi moves it to the default for the new version.
6. Check the `Kafka` status and upgrade clients. The Kafka metrics `BrokerTopicMetrics` produce/fetch `MessageConversionsPerSec` show `0` when clients use the latest format.

Raising `metadataVersion` can make a downgrade impossible (medium confidence, M21).

## Compatibility matrix

Sources: [downloads](https://strimzi.io/downloads/), [1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0), [1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1).

| Dependency | Min | Max | Note |
|---|---|---|---|
| Kubernetes | 1.32 | 1.37 tested | 1.30 and 1.31 dropped |
| Kafka on 1.3.0 | 4.2.0 | 4.3.1 | |
| Kafka on 1.3.1 | 4.2.0 | 4.3.2 | |
| Kafka 4.4.0 | not supported | not supported | Not in the 1.3.0 supported list (https://strimzi.io/downloads/, read 2026-11-04) |
| CRD API | v1 | v1 | |
| HTTP Bridge (bundled) | 1.2.0 | n/a | per release notes |
| Kafka Exporter | 1.10.0 | n/a | per 1.3.0 notes |

## Changes to know when arriving at 1.3.x

Sources: [1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0), [1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1), [feature gates](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/ref-operator-cluster-feature-gates.adoc).

- Kaniko is removed; Buildah is the only Connect image builder (`UseConnectBuildWithBuildah` is GA and cannot be disabled).
- PKCS12 certificates are deprecated; `STRIMZI_PKCS12_KEYSTORE_GENERATION` will default to `false` in a future release.
- 1.3.1 adds Kafka 4.3.2 and fixes concurrency issues after the Vert.x removal. No 1.3.1 change touches the CRD API or these procedures.
- `UseBackgroundPodDeletion` is beta; its default is disputed (register I3). Set it explicitly.
- CHANGELOG-only items (health-check port rename in 1.1.0, removed resource-state metrics in 1.2.0, no bundled OPA authorizer, Access Operator 0.2.0 incompatible with 1.0.0 or later) are (medium confidence, M18).
