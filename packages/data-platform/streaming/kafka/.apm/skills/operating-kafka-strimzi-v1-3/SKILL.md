---
name: operating-kafka-strimzi-v1-3
description: "Operates Kafka on Kubernetes with Strimzi 1.3.x (KRaft, v1 API): install, node pools, security, upgrades. Use when deploying Strimzi 1.3. Not for ZooKeeper (operating-kafka-v3-9). Kafka 4.4.0 unsupported: see operating-kafka-v4-4 (Compose) or operating-kafka-confluent-kubernetes-v3-4."
---

# Operating Kafka with Strimzi 1.3.x (Kubernetes, KRaft)

> Version lock: every claim applies to **Strimzi 1.3.x** (evidence from the 1.3.0 versioned docs plus the 1.3.1 release notes). Research date **2026-11-04**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.
> Provenance: the cited official pages, listed in the [Source Bibliography](./blueprints/unverified-and-risks.md#source-bibliography).
> **Kafka 4.4.0 is not supported by this Strimzi line.** Strimzi 1.3.0 supports Kafka 4.2.0, 4.2.1, 4.2.2, 4.3.0, 4.3.1 on Kubernetes 1.32-1.37 (tested); Kafka 4.4.0 is not listed (https://strimzi.io/downloads/, read 2026-11-04). For 4.4 broker facts on Compose see `operating-kafka-v4-4`; for Confluent Platform on Kubernetes see `operating-kafka-confluent-kubernetes-v3-4`.

## Version Context

| Item | Value | Source (fetched 2026-11-04) |
|---|---|---|
| Strimzi | 1.3.1 was tagged 2026-11-04T10:24:25Z. It has **no versioned docs yet** (the 1.3.1 docs URL returns 404). Docs evidence is 1.3.0 (published 2026-10-12) | https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1 and https://strimzi.io/docs/operators/1.3.0/deploying.html |
| Supported Kafka | 1.3.0: 4.2.0, 4.2.1, 4.2.2, 4.3.0, 4.3.1. 1.3.1 adds 4.3.2. **Not 4.4.0** | https://strimzi.io/downloads/ and https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1 |
| Kubernetes | 1.32 or newer (downloads page lists 1.32 to 1.37 as tested) | https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0 and https://strimzi.io/downloads/ |
| Cluster mode | KRaft only. ZooKeeper support removed in Strimzi 0.46 (medium confidence, M22) | https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-kraft-mode.adoc |
| CRD API | `kafka.strimzi.io/v1` only (v1beta2, v1beta1, v1alpha1 removed in 1.0.0) | https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1 |
| Kafka brokers 4.4 | See skill `operating-kafka-v4-4` for broker facts. Its 4.4-only items do not apply to a Strimzi 1.3.x cluster | https://strimzi.io/downloads/ (read 2026-11-04) |

**Version-lifetime risk** (as of 2026-11-04; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- 1.3.1 was released on 2026-11-04, so 1.3.1-specific defaults are inferred from 1.3.0 docs (unverified).
- No per-release support or end-of-life policy was found (unverified). Treat only the latest release as supported.

## Scope

In scope: the Strimzi Cluster Operator, `Kafka`, `KafkaNodePool`, `KafkaTopic`, `KafkaUser`, `KafkaConnect`, `KafkaConnector`, `KafkaRebalance`, Cruise Control, Drain Cleaner, metrics, upgrades and recovery. Out of scope: broker-level tuning (use `operating-kafka-v4-4`, with the version caveat above), ZooKeeper mode (Strimzi 1.3.x does not support it; for ZooKeeper broker facts use `operating-kafka-v3-9`, Compose only; `operating-kafka-confluent-kubernetes-v3-4` states ZooKeeper mode only on Confluent Platform 7.6 to 7.9, unverified there), Confluent for Kubernetes (use `operating-kafka-confluent-kubernetes-v3-4`), Connect REST API internals, schema registries.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Ask-first decisions](./blueprints/ask-first-decisions.md)
- [Install, Kafka CR, node pools, KRaft](./blueprints/deploy-install-and-cr.md)
- [Hardened production overlay (assembled, unverified)](./blueprints/hardened-overlay.md)
- [Security, listeners, authentication](./blueprints/security-listeners-auth.md)
- [Storage and scaling](./blueprints/storage-and-scaling.md)
- [Rolling updates and upgrades](./blueprints/rolling-updates-and-upgrades.md)
- [Connect, topics, users](./blueprints/connect-topics-users.md)
- [Observability](./blueprints/observability.md)
- [Recovery and DR](./blueprints/recovery-and-dr.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

Code and checks for each item are in [always-do-patterns](./blueprints/always-do-patterns.md).

- **Run Strimzi 1.3.x only on Kubernetes 1.32 or newer** ([1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0), [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- **Write every Strimzi resource with `apiVersion: kafka.strimzi.io/v1`** ([1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1), [official example](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/examples/kafka/kafka-persistent.yaml)).
- **Set `spec.kafka.version` to a Kafka version the installed operator supports** ([downloads](https://strimzi.io/downloads/), [1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1)).
- **Label at least one `KafkaNodePool` with `strimzi.io/cluster: <kafka-name>` for every `Kafka`** ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), [KRaft assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-kraft-mode.adoc)).
- **Use dedicated controller and broker node pools in production** ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), [KRaft assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-kraft-mode.adoc)).
- **Give highly available topics replication factor 3 and `min.insync.replicas: 2` before rolls, upgrades or drains** ([manual roll](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-manual-rolling-update-pods.adoc), [topic replication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/con-topic-replication.adoc)).
- **Upgrade in this order: Kubernetes, Cluster Operator, `spec.kafka.version`, then `metadataVersion` last** ([upgrade sequence](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-sequence.adoc), [Kafka upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/proc-upgrade-kafka-kraft.adoc)).
- **`helm upgrade` does not update CRDs: apply the release CRDs yourself when you upgrade the operator with Helm; the order relative to `helm upgrade` is (unverified, U7)** ([Helm README](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/helm-charts/helm3/strimzi-kafka-operator/README.md), [upgrade assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/upgrading/assembly-upgrade-cluster-operator.adoc)).
- **Move partitions off brokers with a `KafkaRebalance` in `remove-brokers` mode before lowering `KafkaNodePool.spec.replicas`** ([scale-down](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-scaling-down-node-pools.adoc), [scale-down checks](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-skipping-scale-down-checks.adoc)).
- **Trigger a manual restart by annotating the Pod with `strimzi.io/manual-rolling-update="true"`** ([rolling updates](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-rolling-updates.adoc), [manual roll](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-manual-rolling-update-pods.adoc)).
- **Use the Strimzi Drain Cleaner to move Kafka pods off nodes during Kubernetes drains** ([cluster upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-cluster.adoc), [Drain Cleaner](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/drain-cleaner/proc-drain-cleaner-using.adoc)).
- **Use PV reclaim policy `Retain` for Kafka volumes you may need to recover** ([recovery scenarios](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/con-cluster-recovery-scenarios.adoc), [recovery procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-cluster-recovery-volume.adoc)).
- **Configure `authentication` on every client listener that must not be open** ([listener authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-kafka-authentication.adoc), [client authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-client-authentication.adoc)).
- **Enable `spec.kafka.authorization` with `type: simple` when `KafkaUser` resources use `authorization.type: simple`** ([KafkaUser procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/proc-configuring-kafka-user.adoc), [authorization](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-kafka-authorization.adoc)).
- **Configure OAuth 2.0 listeners with `authentication.type: custom`** ([OAuth migration](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-migration.adoc), [OAuth server config](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-server-config.adoc)).
- **For multi-zone clusters set `spec.kafka.rack` with `type: topology-label` and `topologyKey: topology.kubernetes.io/zone`** ([zones](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-distributing-brokers-across-zones.adoc), [common config](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-common-configuration.adoc)).
- **Expose Kafka metrics through `spec.kafka.metricsConfig` on port 9404** ([Strimzi Metrics Reporter](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/metrics/proc-strimzi-metrics-reporter-kafka-deploy-options.adoc), [JMX exporter](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/metrics/proc-jmx-exporter-metrics-kafka-deploy-options.adoc)).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Operator install method | YAML files, Helm OCI chart, or OLM. Upgrades must use the same method. A 1.3.1 Helm chart is not confirmed (unverified) | "Which install method does the cluster already use or allow?" |
| Watched namespaces | One, a list, or all (`STRIMZI_NAMESPACE="*"`); all needs cluster-wide RBAC | "How many teams or namespaces host Kafka clusters?" |
| Storage layout | `persistent-claim`, `jbod` or `ephemeral`; the type cannot change after deploy | "Which storage class, per-broker size, and is JBOD needed?" |
| Client authentication | mTLS, `tls-external`, SCRAM-SHA-512 or OAuth via `custom` | "Which identity system do the clients already use?" |
| External exposure | `loadbalancer`, `nodeport`, `route`, `tlsroute` (maturity: medium confidence) or deprecated `ingress` | "How do clients outside Kubernetes reach the cluster?" |
| Rebalancing | Manual approval, `rebalance-auto-approval`, or `spec.cruiseControl.autoRebalance` | "Must a human review data movement in production?" |
| Certificate authority | Strimzi CAs (default), own CA, or cert-manager (Early Access, not for production) | "Must a corporate PKI or cert-manager issue certificates?" |
| Single-source practices | Resource limits, namespace per cluster, `auto.create.topics.enable: false`, block storage (medium confidence) | "Do you want these recommendations applied?" |
| Existing ZooKeeper cluster | Strimzi 1.3.x is KRaft only; migrate to KRaft on Strimzi 0.45.x first (medium confidence, M22) | "Is the existing cluster still on ZooKeeper?" |
| Single-source prohibitions | `ingress` listener, edited Strimzi ConfigMaps, raising `metadataVersion`, Connect internal topic RF, MM2 ACL sync, PKCS12, encrypted keys (medium confidence, M21; list in [ask-first-decisions](./blueprints/ask-first-decisions.md#single-source-prohibitions-medium-confidence)) | "Do you want these prohibitions enforced?" |
| `UseBackgroundPodDeletion` | Docs conflict on the default (unverified, I3) | "Set the gate explicitly in `STRIMZI_FEATURE_GATES`?" |
| Pod names in commands | Docs use two naming patterns (unverified, I4) | "Can you run `kubectl get pods` so I use the real names?" |

Details: [ask-first-decisions](./blueprints/ask-first-decisions.md).

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Run or upgrade a ZooKeeper-based cluster with Strimzi 1.3.x ([upgrade sequence](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/con-upgrade-sequence.adoc), [KRaft assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-kraft-mode.adoc)) | Use KRaft node pools |
| Use `kafka.strimzi.io/v1beta2`, v1beta1 or v1alpha1 ([1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0), [1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1)) | Use `kafka.strimzi.io/v1` ([official example](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/examples/kafka/kafka-persistent.yaml)) |
| Set `spec.kafka.version: 4.4.0` or any unsupported version ([downloads](https://strimzi.io/downloads/), [1.3.1 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1)) | Use 4.3.2 on 1.3.1 (4.3.1 on 1.3.0) |
| Scale, rename or change the storage type of a controller pool ([KRaft assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-kraft-mode.adoc), [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)) | Size controllers at creation; scale broker-only pools |
| Shrink a PV or switch storage type after creation ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), [API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html)) | Plan JBOD up front; grow volumes only |
| Delete Kafka pods to restart them ([rolling updates](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/deploying/assembly-rolling-updates.adoc), [manual roll](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-manual-rolling-update-pods.adoc)) | Annotate the Pod with `strimzi.io/manual-rolling-update="true"` |
| Lower broker pool replicas while brokers hold partition replicas ([scale-down checks](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-skipping-scale-down-checks.adoc), [scale-down](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-scaling-down-node-pools.adoc)) | Run a `remove-brokers` `KafkaRebalance`, then scale |
| Assume `helm upgrade` upgrades the CRDs ([Helm README](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/helm-charts/helm3/strimzi-kafka-operator/README.md), [upgrade assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/upgrading/assembly-upgrade-cluster-operator.adoc)) | Apply the release CRDs yourself (order relative to `helm upgrade` is unverified, U7) |
| Put client secrets in clear text in `custom` OAuth `config` ([OAuth migration](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-migration.adoc), [OAuth server config](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-server-config.adoc)) | Keep secrets in a Kubernetes `Secret` read through a configuration provider |

Also rejected: `v1beta2` manifests, operator pins other than 1.3.x and Kafka versions outside the supported list ([1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0), [downloads](https://strimzi.io/downloads/)).

Details: [never-do-patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Minimum Kubernetes | 1.32 | https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0 |
| Kafka versions, 1.3.1 | 4.2.0 to 4.3.2 | https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1 |
| Kafka metrics port | 9404 | https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/metrics/proc-jmx-exporter-metrics-kafka-deploy-options.adoc |
| PDB `maxUnavailable` default | 1 | https://strimzi.io/docs/operators/1.3.0/configuring.html |
| `deleteClaim` default | false | https://strimzi.io/docs/operators/1.3.0/configuring.html |
| CA validity / renewal | 365 days / 30 days | https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-certificate-renewal.adoc |
| Reconciliation interval | 2 minutes (default) (medium confidence, M17) | https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-manual-rolling-update-pods.adoc |
| Node ID range | 0 to 999 (medium confidence) | https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/proc-managing-node-pools-ids.adoc |
| Pause reconciliation | `strimzi.io/pause-reconciliation="true"` (medium confidence, M17) | https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-cluster-recovery-volume.adoc |
| Check a CR before applying | `kubectl apply --dry-run=server -f <file>` (unverified) | page not recorded |

## External Resources

All fetched 2026-11-04.

- [Strimzi 1.3.0 deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)
- [Strimzi 1.3.0 API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html)
- [1.3.1 release notes (2026-11-04)](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1)
- [Strimzi downloads](https://strimzi.io/downloads/)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
