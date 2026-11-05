# Recovery and disaster recovery, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). Scope: what the 1.3.0 docs describe is recovery from retained PVs and MirrorMaker 2 active/passive DR. There is no Strimzi-native backup of topic data in the pages read (unverified, absence of evidence, U10). Doc base: `https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/`.

## Retain reclaim policy (High)

Sources: [recovery scenarios](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/con-cluster-recovery-scenarios.adoc), [recovery procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-cluster-recovery-volume.adoc), [recovery assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-cluster-recovery-volume.adoc).

- Set `Retain` on the PV, directly or through the storage class. With `Retain` "the PV retains its data and is not deleted".
- Recovery after namespace deletion or cluster loss depends on the retained PVs.
- With `Retain` you must delete PVs by hand when you really want to remove a cluster.

## Recovery procedure details (medium confidence)

Source: [recovery procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-cluster-recovery-volume.adoc) (single source, M17).

- Recovery needs the original cluster ID written into `.status.clusterId` (medium confidence).
- Pause reconciliation with `strimzi.io/pause-reconciliation="true"` while you recreate resources (medium confidence, M17).
- Keep copies of the `Kafka`, `KafkaNodePool`, `KafkaTopic` and `KafkaUser` manifests and the cluster ID. In the recovery doc, recreated user secrets keep credentials; without them the User Operator generates new credentials, and without recreated `KafkaUser`s it removes the users (medium confidence).
- PVC names in the doc follow the pattern `data-0-my-cluster-broker-0`; pod and PVC naming is inconsistent across pages (register I4).

## MirrorMaker 2 DR (medium confidence)

Source: [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), section on MirrorMaker 2 active/passive DR (single source).

- Active/passive DR is documented; test failover "in a controlled environment".
- Do not enable MirrorMaker 2 ACL sync together with the User Operator (medium confidence, M21).
- For MM2 offsets and RPO concepts at broker level see `operating-kafka-v4-4`.

## Not covered by the pages read

- Strimzi-native topic-data backup or snapshots (unverified, U10).
- Volume-snapshot tooling such as Velero (unverified, U10).
- Downgrade of the operator or Kafka: modules not read (register L3).
- Uninstall procedures: not read (register L3).
- A per-release support policy (register I2).

## Ask before acting

- "Are the PVs `Retain`, and do you have the original cluster ID and the user secrets?"
- "Is MirrorMaker 2 active/passive enough, or do you need a backup tool outside Strimzi?"
