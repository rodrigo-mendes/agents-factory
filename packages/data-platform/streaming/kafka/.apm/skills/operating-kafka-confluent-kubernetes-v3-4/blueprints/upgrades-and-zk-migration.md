# Upgrades and ZooKeeper-to-KRaft migration, CFK 3.4.0

Back to [SKILL.md](../SKILL.md). S-ids are in the [bibliography](./unverified-and-risks.md#source-bibliography). CFK 3.4.0 was released 2026-10-28; its upgrade pages changed between 2026-10-27 and 2026-11-02, so re-read them before an upgrade. Commands are representative.

## Compatibility matrix (S2)

| CFK | Confluent Platform | Control Center | Kubernetes (OpenShift) | Released | End of standard support |
|---|---|---|---|---|---|
| 3.4.x | 7.6 to 8.4 | 2.4 to 2.7 | 1.29 to 1.37 (4.15 to 4.22) | 2026-10-28 | 2028-10-28 |
| 3.3.x | 7.5 to 8.3 | 2.4 to 2.6 | 1.28 to 1.36 (4.15 to 4.22) | 2026-06-23 | 2028-06-23 |
| 3.2.x | 7.4 to 8.2 | 2.4 to 2.6 | 1.27 to 1.35 (4.14 to 4.21) | 2026-03-11 | 2028-03-11 |

The page says not to treat the image tag table as the source of truth for compatibility. Other prerequisites: CNCF-conformant Kubernetes, kubectl, Helm (the compatibility page says "Helm 3 is required", the upgrade page accepts "Helm 3.x or 4.x"; conflict, medium confidence), x86 or ARM64. Image tag table: CFK 3.4.0, image tag `0.2038.1`, app version `3.4.0`, chart `v0.2038.1`; column names inferred from the row (medium confidence).

## Changes from CFK 3.3 to 3.4.0 (S1)

"There are no breaking changes in this release." Still act on:
- Heap default cap: [always-do A11](./always-do-patterns.md#a11), [never-do N3](./never-do-patterns.md#n3-upgrade-to-cfk-340-without-checking-heap).
- `cfkprober` exec liveness probe, so the init container must be 3.4.0: [A10](./always-do-patterns.md#a10), [N2](./never-do-patterns.md#n2-upgrade-cfk-to-340-without-updating-the-init-container-image).
- Operator-managed CRDs with a ValidatingAdmissionPolicy blocking downgrades (S6).
- Gateway CR security settings moved; manual CFK RBAC needs the `customresourcedefinitions` rule (S7) (medium confidence).
- Other additions: `KafkaTopic` replication factor change (needs CP 8.4 or later), drift protection for Day-2 CRs, a password encoder secret on the KRaftController for migration (S1).

## Upgrade CFK (S6)

1. `kubectl config current-context`, `helm version`, `helm list -n <namespace>`.
2. CP 7.x only: add `platform.confluent.io/use-log4j1=true` and, for basic auth web components, `platform.confluent.io/use-old-jetty9=true` during a CFK 2.x to 3.x upgrade (medium confidence).
3. `kubectl confluent block-reconcile --namespace <namespace>` ([A9](./always-do-patterns.md#a9)).
4. `helm repo add confluentinc https://packages.confluent.io/helm`, then `helm repo update`.
5. `helm pull confluentinc/confluent-for-kubernetes --version <cfk_image_tag> --untar`. For 3.4.0 the image tag is `0.2038.1` (S2); that it is the Helm `--version` is inferred from the placeholder (medium confidence).
6. CRDs: automatic with `manageCRDs: true`; otherwise `kubectl apply --server-side=true -f confluent-for-kubernetes/crds/`.
7. `helm upgrade --install confluent-operator confluentinc/confluent-for-kubernetes --values <file> -n <namespace> --dry-run`, then again without `--dry-run` (medium confidence for the dry-run step).
8. Set `spec.image.init: confluentinc/confluent-init-container:3.4.0` on each CR ([A10](./always-do-patterns.md#a10)).
9. `kubectl confluent enable-reconcile --namespace <namespace>`. Expect one rolling restart. Pods may briefly show `Error` or `CrashLoopBackOff` and recover; wait for `STATUS: RUNNING`.

## Upgrade Confluent Platform on KRaft (S8)

Order: KRaft controllers (`image.application: confluentinc/cp-server:<tag>`, then `kubectl rollout status statefulset/kraftcontroller`), brokers (same for `statefulset/kafka`), metadata version, other components, then Control Center (`cp-enterprise-control-center-next-gen:<c3-tag>` plus Prometheus and Alertmanager images on the Control Center release tag).

- This order is one page (medium confidence). Exception from 7.7.3 or 7.8.x to 7.9.0 to 7.9.2: brokers before controllers, or brokers can crash-loop (medium confidence).
- Raise the metadata version after a health check: `kafka-features --bootstrap-server kafka:9071 upgrade --metadata <x.y>` (for example `4.3` for CP 8.3) (medium confidence).
- Do not use `--release-version` on CFK-managed clusters (medium confidence).
- Control Center (Legacy) is unsupported on 8.x: move to Control Center (S7, S8).
- Before 8.0, remove deprecated configs: [A12](./always-do-patterns.md#a12), [N5](./never-do-patterns.md#n5-leave-pre-80-deprecated-configurations-when-moving-to-cp-8x).
- Order when upgrading both: CFK first, then CP (S7) (medium confidence).
- Whether brokers roll one at a time or wait for under-replicated partitions, and any rollback or downgrade path, are not documented (unverified, I4). Check under-replicated partitions between steps and back up CRs with `kubectl get ... -o yaml`.

## ZooKeeper to KRaft migration (S10)

- Prerequisites: CP 7.6 minimum (7.6.1 or later recommended for production); CFK 2.9.2 or later in 2.9.x, or 2.10.x or later; CFK-based deployments only; isolated mode only (no combined nodes); no existing KRaftController; upgrade and migration are not done at the same time.
- Phases: SETUP, MIGRATE, DUAL-WRITE, MoveToKRaftControllerOnly (finalize annotation), COMPLETE.
- Rollback is possible during SETUP, MIGRATE and DUAL-WRITE, not after finalization. The ZooKeeper cluster is not deleted automatically.
- The `KRaftMigrationJob` field list was not on the overview page (unverified, U3).
- Path to CP 8.x: [always-do A2](./always-do-patterns.md#a2).
- Under CFK 3.4 ZooKeeper mode is limited to CP 7.6 to 7.9, because the ZooKeeper quick start applies to "Confluent Platform 7.9 and earlier" (S14) and CFK 3.4 starts at CP 7.6 (unverified, U12: inference).
- Examples page `co-upgrade-example` was found by search and not read (L5).
