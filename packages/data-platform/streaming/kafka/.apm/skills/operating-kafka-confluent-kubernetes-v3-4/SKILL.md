---
name: operating-kafka-confluent-kubernetes-v3-4
description: "Operates Confluent for Kubernetes 3.4.0 (Confluent Platform 7.6-8.4): Helm, KRaft CRs, TLS, RBAC, storage, upgrades, licensing. Use when deploying CFK or Confluent Platform 8.4 on Kubernetes. Not for Strimzi (operating-kafka-strimzi-v1-3) or schemas (managing-event-schemas-confluent-v8-4)."
---

# Operating Kafka with Confluent for Kubernetes 3.4.0

> Version lock: every claim applies to **CFK 3.4.0** (Confluent Platform 7.6.x to 8.4.x) only. Research date **2026-11-04**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.
> Provenance: the cited official pages, listed in the [Source Bibliography](./blueprints/unverified-and-risks.md#source-bibliography).

## Version Context

| Item | Value | Source (fetched 2026-11-04) |
|---|---|---|
| Confluent for Kubernetes | 3.4.0, released 2026-10-28, active, end of standard support 2028-10-28 | https://docs.confluent.io/operator/3.4/co-supported-environments.html and https://docs.confluent.io/operator/3.4/release-notes.html |
| Confluent Platform | 7.6.x to 8.4.x (Control Center 2.4 to 2.7) | https://docs.confluent.io/operator/3.4/co-supported-environments.html |
| Kubernetes | 1.29 to 1.37 (OpenShift 4.15 to 4.22) | https://docs.confluent.io/operator/3.4/co-supported-environments.html |
| Operator image | `confluentinc/confluent-operator:0.2038.1`, init container `confluent-init-container:3.4.0` | https://docs.confluent.io/operator/3.4/release-notes.html |
| ZooKeeper | Removed in Confluent Platform 8.0. KRaft required on 8.x | https://docs.confluent.io/operator/3.4/co-migrate-kraft-overview.html |
| Kafka 4.4 / CP 8.4 | CFK 3.4.0 supports CP up to 8.4.x and deploys Confluent Platform images (`confluentinc/cp-server`), not Apache Kafka images. Which Apache Kafka version CP 8.4 bundles was not read: do not state 4.4.x (unverified, U1) | https://docs.confluent.io/operator/3.4/co-supported-environments.html and https://docs.confluent.io/operator/3.4/co-custom-registry.html |
| Cluster mode under CFK 3.4 | ZooKeeper mode only on CP 7.6 to 7.9 (unverified) | inference from the two compatibility and quick start pages |

**Version-lifetime risk** (as of 2026-11-04; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- CFK 3.4.0 was released 2026-10-28; the pages were read on 2026-11-04. Pages changed between 2026-10-27 and 2026-11-02 and may change again. Re-check the release notes and the supported-environments page before relying on this skill.
- CFK 3.3.x supports CP 7.5 to 8.3 only, so CP 8.4 needs CFK 3.4.x ([supported environments](https://docs.confluent.io/operator/3.4/co-supported-environments.html)).

## Scope

In scope: CFK operator install, `KRaftController` and `Kafka` CRs, listeners, TLS, authentication, authorization, storage, scaling, upgrades, monitoring, licensing. Out of scope: Strimzi (use `operating-kafka-strimzi-v1-3`), generic broker tuning (use `operating-kafka-v4-4`), Schema Registry internals (use `managing-event-schemas-confluent-v8-4`), Kafka Streams.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Ask-first decisions](./blueprints/ask-first-decisions.md)
- [Install, KRaftController and Kafka CRs](./blueprints/deploy-install-and-cr.md)
- [Licensing](./blueprints/licensing.md)
- [Security: RBAC, authentication, TLS](./blueprints/security-rbac-tls.md)
- [Storage and scaling](./blueprints/storage-and-scaling.md)
- [Upgrades and ZooKeeper migration](./blueprints/upgrades-and-zk-migration.md)
- [Observability](./blueprints/observability.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

Code for each item is in [always-do-patterns](./blueprints/always-do-patterns.md).

- **Pin the CFK and Confluent Platform pair to a supported row of the 3.4 compatibility table** ([supported environments](https://docs.confluent.io/operator/3.4/co-supported-environments.html), [release notes](https://docs.confluent.io/operator/3.4/release-notes.html)). See [A1](./blueprints/always-do-patterns.md#a1).
- **Run KRaft (`KRaftController` plus `Kafka`) for any Confluent Platform 8.x deployment** ([migrate overview](https://docs.confluent.io/operator/3.4/co-migrate-kraft-overview.html), [upgrade overview](https://docs.confluent.io/operator/3.4/co-upgrade-overview.html), [upgrade CP](https://docs.confluent.io/operator/3.4/co-upgrade-cp.html)). See [A2](./blueprints/always-do-patterns.md#a2).
- **Set `KRaftController` `spec.replicas` to an odd number of at least 3** ([configure KRaft](https://docs.confluent.io/operator/3.4/co-configure-kraft.html), [sizing](https://docs.confluent.io/operator/3.4/co-plan-sizing.html)). See [A3](./blueprints/always-do-patterns.md#a3).
- **Use the same controller listener authentication and TLS on the KRaftController and in `Kafka.spec.dependencies.kRaftController.controllerListener`** ([configure KRaft](https://docs.confluent.io/operator/3.4/co-configure-kraft.html), [authenticate](https://docs.confluent.io/operator/3.4/co-authenticate-kafka.html)). See [A4](./blueprints/always-do-patterns.md#a4).
- **Configure listener authentication in the first deploy, because CFK deploys without authentication by default** ([authenticate](https://docs.confluent.io/operator/3.4/co-authenticate-kafka.html), [plan availability](https://docs.confluent.io/operator/3.4/co-plan-availability.html)). See [A5](./blueprints/always-do-patterns.md#a5).
- **Set `authorization.type` in both the Kafka CR and the KRaftController CR** ([simple ACLs](https://docs.confluent.io/operator/3.4/co-simple-acls.html), [RBAC](https://docs.confluent.io/operator/3.4/co-rbac.html)). See [A6](./blueprints/always-do-patterns.md#a6).
- **Deploy at least 3 Kafka brokers** ([sizing](https://docs.confluent.io/operator/3.4/co-plan-sizing.html), [scale cluster](https://docs.confluent.io/operator/3.4/co-scale-cluster.html)). See [A7](./blueprints/always-do-patterns.md#a7).
- **Set an explicit StorageClass with `volumeBindingMode: WaitForFirstConsumer` before the first deploy** ([storage](https://docs.confluent.io/operator/3.4/co-storage.html), [multi-AZ](https://docs.confluent.io/operator/3.4/co-multi-az.html), [plan availability](https://docs.confluent.io/operator/3.4/co-plan-availability.html)). See [A8](./blueprints/always-do-patterns.md#a8).
- **Block reconciliation before a CFK upgrade** ([upgrade CFK](https://docs.confluent.io/operator/3.4/co-upgrade-cfk.html), [release notes](https://docs.confluent.io/operator/3.4/release-notes.html)). See [A9](./blueprints/always-do-patterns.md#a9).
- **Set `spec.image.init` to `confluentinc/confluent-init-container:3.4.0` in every component CR** ([upgrade CFK](https://docs.confluent.io/operator/3.4/co-upgrade-cfk.html), [upgrade overview](https://docs.confluent.io/operator/3.4/co-upgrade-overview.html), [upgrade CP](https://docs.confluent.io/operator/3.4/co-upgrade-cp.html)). See [A10](./blueprints/always-do-patterns.md#a10).
- **Check broker and controller heap before upgrading to CFK 3.4.0** ([release notes](https://docs.confluent.io/operator/3.4/release-notes.html), [upgrade overview](https://docs.confluent.io/operator/3.4/co-upgrade-overview.html), [resources](https://docs.confluent.io/operator/3.4/co-resources.html)). See [A11](./blueprints/always-do-patterns.md#a11).
- **Pin heap in `spec.configOverrides.jvm` when it exceeds the new 3.4.0 cap** ([release notes](https://docs.confluent.io/operator/3.4/release-notes.html), [upgrade overview](https://docs.confluent.io/operator/3.4/co-upgrade-overview.html), [resources](https://docs.confluent.io/operator/3.4/co-resources.html)). See [A11](./blueprints/always-do-patterns.md#a11).
- **Remove `message.format.version`, `message.downconversion.enable` and `message.timestamp.difference.max.ms` before moving `cp-server` to 8.0 or later** ([upgrade overview](https://docs.confluent.io/operator/3.4/co-upgrade-overview.html), [upgrade CP](https://docs.confluent.io/operator/3.4/co-upgrade-cp.html)). See [A12](./blueprints/always-do-patterns.md#a12).
- **Use the `confluentinc/cp-server-connect` image for Connect when you use the Centralized Connect License** ([configure Connect](https://docs.confluent.io/operator/3.4/co-configure-connect.html), [CFK license](https://docs.confluent.io/operator/3.4/co-license.html)). See [A13](./blueprints/always-do-patterns.md#a13).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Authorization model | RBAC (needs MDS, identity provider, Enterprise (medium confidence, M32)) vs simple ACLs vs none. ACL behavior after license expiry is not documented (unverified) | "Do you hold a Confluent Enterprise subscription, and which identity provider do you run?" |
| TLS certificates | CFK auto-generated vs user-provided. Cannot switch after deploy | "Do clients connect from outside the Kubernetes cluster?" |
| External access type | `loadBalancer`, `nodePort`, `route`, static port or host routing. Fixed after deploy. Per-option tradeoffs not documented (unverified) | "Which ingress does the platform offer?" |
| Install method | Helm repo vs download bundle vs OpenShift OperatorHub (medium confidence) | "Is the cluster air-gapped or OpenShift?" |
| License delivery | Global vs per-component secret vs Vault path (medium confidence) | "Does one subscription cover all components?" |
| Community broker image | Whether CFK can run `cp-kafka` is not documented (unverified) | "Do you need a no-license path? Then verify with Confluent first" |
| Self-Balancing trigger | `EMPTY_BROKER` (default) vs `ANY_UNEVEN_LOAD` (medium confidence) | "Can the cluster tolerate background partition movement?" |
| Heap policy | 3.4 default cap vs pinned `-Xms`/`-Xmx` vs percentage (medium confidence) | "Which heap size does the current cluster run?" |
| Connect plugins | `build.type: onDemand` vs custom image (medium confidence) | "May pods download plugins from the internet at startup?" |
| Monitoring stack | Control Center bundled vs own Prometheus vs JMX (medium confidence) | "Which monitoring stack do you already run?" |
| CP and CFK upgrade order | CFK first, then CP; KRaft order controllers, brokers, metadata version (medium confidence). Rolling and rollback semantics are not documented (unverified) | "Is a maintenance window available, and are CR backups taken?" |
| CFK or Strimzi | Strimzi 1.3.0 supports Kafka 4.2.0 to 4.3.1 and does not list 4.4.0 (https://strimzi.io/downloads/, read 2026-11-04). Strimzi is out of scope here | "Are you committed to Confluent Platform images and a subscription?" |

Details: [ask-first-decisions](./blueprints/ask-first-decisions.md).

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Upgrade a ZooKeeper-based deployment to Confluent Platform 8.x ([migrate overview](https://docs.confluent.io/operator/3.4/co-migrate-kraft-overview.html), [upgrade overview](https://docs.confluent.io/operator/3.4/co-upgrade-overview.html), [upgrade CP](https://docs.confluent.io/operator/3.4/co-upgrade-cp.html)) | Go to 7.9 on ZooKeeper, migrate to KRaft, then upgrade to 8.x |
| Upgrade CFK to 3.4.0 and leave the old init container image ([upgrade CFK](https://docs.confluent.io/operator/3.4/co-upgrade-cfk.html), [upgrade overview](https://docs.confluent.io/operator/3.4/co-upgrade-overview.html)) | Set `spec.image.init` to `confluent-init-container:3.4.0` |
| Upgrade to CFK 3.4.0 without checking broker and controller heap ([release notes](https://docs.confluent.io/operator/3.4/release-notes.html), [upgrade overview](https://docs.confluent.io/operator/3.4/co-upgrade-overview.html), [resources](https://docs.confluent.io/operator/3.4/co-resources.html)) | Pin `-Xms` and `-Xmx` in `spec.configOverrides.jvm` first |
| Run a one- or two-broker Kafka cluster under CFK ([sizing](https://docs.confluent.io/operator/3.4/co-plan-sizing.html), [scale cluster](https://docs.confluent.io/operator/3.4/co-scale-cluster.html)) | `spec.replicas: 3` or more |
| Keep deprecated pre-8.0 configurations when moving to CP 8.x ([upgrade overview](https://docs.confluent.io/operator/3.4/co-upgrade-overview.html), [upgrade CP](https://docs.confluent.io/operator/3.4/co-upgrade-cp.html)) | Remove them; raise `segment.bytes` to at least 1048576 |
| Plan to add authentication to an existing Kafka or KRaft listener later ([authenticate](https://docs.confluent.io/operator/3.4/co-authenticate-kafka.html), [plan availability](https://docs.confluent.io/operator/3.4/co-plan-availability.html)) | Set authentication and TLS in the first deploy |

Details: [never-do-patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| API group and version | `platform.confluent.io/v1beta1` | https://docs.confluent.io/operator/3.4/co-api.html |
| Broker and controller image | `confluentinc/cp-server` (Confluent Server) | https://docs.confluent.io/operator/3.4/co-custom-registry.html |
| Controller listener port | 9074 | https://docs.confluent.io/operator/3.4/co-configure-kraft.html |
| Heap default (3.4.0) | brokers min(50% of `requests.memory`, 32Gi); controllers min(80%, 32Gi) | https://docs.confluent.io/operator/3.4/release-notes.html |
| `manageCRDs` | `true` (`false` on OpenShift); CRD downgrade blocked | https://docs.confluent.io/operator/3.4/co-upgrade-cfk.html |
| Minimum broker | 4 CPU, 16 GB, 1 TB; KRaft minimum 3 pods | https://docs.confluent.io/operator/3.4/co-plan-sizing.html |
| JMX / Jolokia / exporter ports | 7203 / 7777 / 7778; JMX off by default since 3.2.1 | https://docs.confluent.io/operator/3.4/co-monitor-cp.html |
| Trial without a key | 30 days (medium confidence, M32) | https://docs.confluent.io/operator/3.4/co-license.html |

## External Resources

All fetched 2026-11-04.

- [CFK 3.4 documentation](https://docs.confluent.io/operator/3.4/)
- [CFK 3.4 release notes (2026-10-28)](https://docs.confluent.io/operator/3.4/release-notes.html)
- [Supported environments (updated 2026-11-02)](https://docs.confluent.io/operator/3.4/co-supported-environments.html)
- [Confluent Platform licenses (CP 8.4)](https://docs.confluent.io/platform/current/installation/license.html)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
