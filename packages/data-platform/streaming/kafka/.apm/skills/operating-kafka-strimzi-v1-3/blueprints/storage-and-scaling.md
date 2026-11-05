# Storage and scaling, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). Doc base: `https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/`. Commands are representative; pod names conflict between docs (register I4).

## Storage rules

Sources: [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), [API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html), [official example](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/examples/kafka/kafka-persistent.yaml).

- Types: `ephemeral` (not suitable for topics with replication factor 1), `persistent-claim` (one PV), `jbod` (several PVs).
- The storage type cannot change after deploy; `KafkaNodePool.spec.storage` "Cannot be updated". Volume size can grow; shrinking a PV is not supported (see [never-do N5](./never-do-patterns.md#n5-shrinking-a-pv-or-changing-storage-type)). The guide also says: "storage reduction is only possible with several disks per broker". Reading this as removal of a JBOD volume after its data has moved is inferred (unverified, U13).
- JBOD volume IDs cannot change, but volumes can be added or removed.
- The KRaft metadata log goes on the lowest-ID volume unless a volume sets `kraftMetadata: shared`.
- `deleteClaim` defaults to `false`. With no storage class the cluster default is used.
- Block storage only (medium confidence, M4). Tiered storage is supported (the guide says production-ready in Kafka since 3.9.0; medium confidence, one page).
- Moving data off a JBOD volume uses `KafkaRebalance` mode `remove-disks` (API reference). The JBOD reassignment procedure was not read (register L3).

```yaml
storage:
  type: jbod
  volumes:
    - id: 0
      type: persistent-claim
      size: 100Gi
      kraftMetadata: shared
```

## Which pools scale

Sources: [KRaft assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-kraft-mode.adoc), [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html).

- Only broker-only pools scale. Controller pools are fixed at creation (static quorum): no add, remove, rescale, rename or storage-type change.
- Scaling a cluster with external listeners may roll all brokers.

## Cruise Control

Sources: [deploy Cruise Control](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-configuring-deploying-cruise-control.adoc), [concepts](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/cruise-control/assembly-cruise-control-concepts.adoc), [optimization proposals](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-generating-optimization-proposals.adoc).

- Enable with `cruiseControl: {}` on the `Kafka` resource. Run one Cruise Control per Kafka cluster (medium confidence, M17).
- It creates `strimzi.cruisecontrol.metrics`, `strimzi.cruisecontrol.partitionmetricsamples` and `strimzi.cruisecontrol.modeltrainingsamples`; do not delete or change them. `default.goals` must include all `hard.goals` (medium confidence, M17).
- `KafkaRebalance` modes: `full`, `add-brokers`, `remove-brokers`, `remove-disks`. `remove-brokers` needs a `brokers` list.
- Insufficient-CPU errors report percentages based on the `KafkaNodePool` CPU limit (medium confidence, M17).

## Manual rebalance flow

Sources: [optimization proposals](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-generating-optimization-proposals.adoc), [approval](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-approving-optimization-proposal.adoc). States: `PendingProposal`, `ProposalReady`, then approve, `Rebalancing`, `Ready`.

```bash
kubectl apply -f my-rebalance.yaml
kubectl get kafkarebalance -o wide -w -n kafka          # wait for ProposalReady
kubectl describe kafkarebalance my-rebalance             # review the optimization result
kubectl annotate kafkarebalance my-rebalance strimzi.io/rebalance="approve"
# later reuse of a proposal: strimzi.io/rebalance="refresh"
```

## Scale-up flow

Sources: [optimization proposals](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-generating-optimization-proposals.adoc), [auto-rebalance](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-automating-rebalances.adoc).

1. `kubectl scale kafkanodepool broker --replicas=4`.
2. Rebalance in `add-brokers` mode, or let auto-rebalance do it.
3. Auto-rebalance runs only when `spec.replicas` of an existing pool changes, not when pools are created or deleted. On Kafka 4.3 or later, brokers being removed are cordoned with `cordoned.log.dirs`.

## Scale-down flow

Sources: [scale-down](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-scaling-down-node-pools.adoc), [scale-down checks](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-skipping-scale-down-checks.adoc), [optimization proposals](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-generating-optimization-proposals.adoc).

1. Create a `KafkaRebalance` with `mode: remove-brokers` and `brokers: [<ids>]`.
2. Wait for `ProposalReady`, approve, wait for `Ready`.
3. Confirm the nodes hold no partition replicas.
4. Lower `KafkaNodePool.spec.replicas`.

Never skip the check with `strimzi.io/skip-broker-scaledown-check` (see [never-do N7](./never-do-patterns.md#n7-scale-down-with-data-still-on-the-brokers)).

## Rack awareness and node pools

Sources: [zones](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-distributing-brokers-across-zones.adoc), [node pool racks](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-node-pools-racks.adoc). After moving nodes between pools in a rack-aware cluster run a `RackAwareGoal` rebalance (medium confidence, M15). Closest-replica fetching needs `replica.selector.class` set by you (medium confidence, M11).

## Disruption budgets

Sources: [API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html), [PDB generation](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-disable-pod-disruption-budget-generation.adoc).

- Strimzi generates one PDB per component (Kafka, Connect, MM2, Bridge) over all node-pool pods; `maxUnavailable` defaults to 1.
- `STRIMZI_POD_DISRUPTION_BUDGET_GENERATION=false` lets you supply your own PDBs. A hand-written PDB next to the generated one would duplicate it.
- `maxUnavailable: 0` blocks automatic eviction and is meant for Drain Cleaner or manual rolls.
