# Unverified and risks register, CFK 3.4.0

Back to [SKILL.md](../SKILL.md). Provenance: the official pages in the Source Bibliography below (read 2026-11-04). I1 to I4 were not resolved by the pages read: this skill does not resolve them, a human must verify. Descriptive facts cited to one versioned page are untagged; recommendations and prohibitions need 2 or more pages, and those resting on one page carry (medium confidence).

## Version-lifetime risk

- CFK 3.4.0 was released 2026-10-28 and end of standard support is 2028-10-28 (S1, S2, read 2026-11-04). Pages changed between 2026-10-27 and 2026-11-02; re-check S1 and S2 before relying on this skill.
- CFK 3.3.x covers CP 7.5 to 8.3 and 3.2.x covers 7.4 to 8.2, so CP 8.4 needs CFK 3.4.x (S2).
- CP 8.0 removed ZooKeeper (S10). CFK 3.4 still ships a `Zookeeper` CR (S11).
- The successor CFK release number and date are page not recorded.

## Unverified (U1..U13): 13 items

| ID | Item | Tag |
|---|---|---|
| U1 | CP 8.4 to Apache Kafka version mapping was not read. The statement "CP 8.4 bundles Kafka 4.4.x" is unverified; this skill does not state it | (unverified) |
| U2 | Production-shaped YAML and the Connect snippet are assemblies from several pages, not published examples | (unverified) |
| U3 | `KRaftMigrationJob` field list was not on the overview page | (unverified) |
| U4 | KRaft controller scaling and dynamic quorum procedure (page `co-configure-kraft-dynamic-quorum` not read) | (unverified) |
| U5 | Per-option tradeoffs of external access types are not described on the pages read | (unverified) |
| U6 | Operator scope (namespaced or cluster-wide) and its Helm values were not read | (unverified) |
| U7 | `confluent-kubernetes-examples` repository not read; the quick start uses its master branch, not pinned to 3.4.0 | (unverified) |
| U8 | Failure mode of ZooKeeper dependencies moved to CP 8.x is not documented | (unverified) |
| U9 | Performance effect of the lowered default heap is not documented | (unverified) |
| U10 | Rack awareness configuration page was not read | (unverified) |
| U11 | No official CFK test harness; `helm template` plus `kubectl apply --dry-run=server` and `kubectl explain kafka.spec` are not Confluent steps | (unverified) |
| U12 | ZooKeeper mode under CFK 3.4 limited to CP 7.6 to 7.9 is inferred from the compatibility table and the ZooKeeper quick start | (unverified) |
| U13 | Consequence of 1 or 2 brokers (topics cannot be fully replicated at the default factor) is inferred | (unverified) |

## Irresolvable (I1..I4): 4 items

| ID | Item | Tag | Note |
|---|---|---|---|
| I1 | Whether CFK 3.4 supports the community `cp-kafka` broker image (a no-license path) | (unverified) | Not mentioned on any CFK 3.4 page read. Verify with Confluent |
| I2 | Simple ACL behavior after license expiry | (unverified) | No official statement found. Test on a lab cluster |
| I3 | Default PodDisruptionBudgets and the field-level `Kafka` CR reference | (unverified) | API reference page does not render field docs. Use `kubectl explain kafka.spec` |
| I4 | CP upgrade rolling semantics (one broker at a time, under-replicated wait) and rollback or downgrade | (unverified) | Pages `co-upgrade-considerations` and `co-upgrade-example` not read. Back up CRs |

## Medium confidence (M1..M32): 32 items

| ID | Claim | Source |
|---|---|---|
| M1 | Upgrade CFK first, then CP | S7 |
| M2 | CP-on-KRaft order controllers, brokers, metadata, others, Control Center; 7.9.0 to 7.9.2 exception | S8 |
| M3 | Raise the metadata version with `kafka-features ... upgrade --metadata` after a health check | S8 |
| M4 | StorageClass `Retain` and `allowVolumeExpansion`; no default class; `Delete` reclaim deletes data | S12 |
| M5 | Equal disk sizes; shrink limits; do not edit shrink annotations; do not resize ZooKeeper by scale | S20 |
| M6 | `oneReplicaPerNode: true` | S27 |
| M7 | `topologySpreadConstraints` across zones | S26 |
| M8 | JMX off by default since 3.2.1; pair JMX authentication with TLS | S23 |
| M9 | Enable TLS at first deploy | S24 |
| M10 | Unique TLS secret per component; example JKS script not for production | S15 |
| M11 | `helm upgrade --dry-run` before the real upgrade | S6 |
| M12 | `rbac: false` needs the `customresourcedefinitions` ClusterRole rule | S7 |
| M13 | `AclAuthorizer` is the ZooKeeper-only class; KRaft uses the default or `StandardAuthorizer` | S19 |
| M14 | TLS auto-generated versus user-provided tradeoffs | S15 |
| M15 | Install method and CRD management tradeoffs | S5, S6 |
| M16 | License delivery options and license cautions | S3 |
| M17 | Self-Balancing trigger options | S20 |
| M18 | Connect plugin delivery options | S25 |
| M19 | Heap sizing policy options | S21 |
| M20 | Monitoring stack options | S23 |
| M21 | Do not set both `zookeeper` and `kRaftController` dependencies | S9 |
| M22 | Do not use `kafka-features --release-version` | S8 |
| M23 | Licensing inferences: developer license fit, Self-Balancing default, Schema Registry ACL plugin | S4, S19, S20, S22 |
| M24 | License expiry wording conflict (stops functioning versus starts with errors) | S4 |
| M25 | Helm 3 required versus Helm 3.x or 4.x | S2, S6 |
| M26 | Sizing "Default resources" row may or may not be operator defaults | S22 |
| M27 | Helm `--version` equals the image tag `0.2038.1` (inferred from a placeholder) | S2, S6 |
| M28 | Image tag table column names inferred from the row | S2 |
| M29 | Schema Registry "does not support scaling in this context" | S20 |
| M30 | Gateway CR settings, SNI host check, log4j1 and jetty9 annotations, dynamic certificate rotation | S7, S6, S15 |
| M31 | License statements cited to a single page (Developer, Enterprise features, Community, Apache 2.0, multi-tenancy, Cloud license, Platinum support, expiry behavior) | S2, S3, S4 |
| M32 | License statements read on the Confluent Platform license page (medium confidence; same license facts wherever they are repeated in the skill) | S4 |

## Coverage limits (L1..L6): 6 items

| ID | Limit |
|---|---|
| L1 | Every page was read through WebFetch, which returns a summarized page, not verbatim text |
| L2 | License page S4 is 162,890 characters, read in two parts; the second part was navigation only |
| L3 | API reference S11: CR list complete, field-level `KafkaSpec` docs not rendered; the `.md` rendering is a stub |
| L4 | RBAC page S18 was summarized; its YAML was not reproduced by the tool |
| L5 | Found but not read: dynamic quorum, upgrade example, upgrade considerations, deploy CP steps, rack awareness, custom values, operator scope pages |
| L6 | Kafka and KRaftController manifests from S11 had indentation rebuilt by the tool and are field evidence only |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md Ask First | M1, M2, M13, M14, M15, M16, M17, M18, M19, M20 |
| (medium confidence, M32) | SKILL.md Ask First and Quick Reference (Enterprise RBAC, 30-day trial) | M31, M32 |
| (unverified) | SKILL.md Ask First, Version Context | I1, I2, I4, U1, U5, U12 |
| (medium confidence) | ask-first-decisions.md | M1 to M22, M31, M32 |
| (unverified) | ask-first-decisions.md | I1, I2, I3, I4, U5 |
| (unverified) | always-do-patterns.md, A13 snippet | U2 |
| (unverified) | never-do-patterns.md, N1 N3 N4 impact | U8, U9, U13 |
| (unverified) | deploy-install-and-cr.md | I1, I3, U2, U6, U7 |
| (medium confidence) | deploy-install-and-cr.md | M4, M15, M21 |
| (medium confidence), (medium confidence, M32), (medium confidence, inferred) | licensing.md | M16, M23, M24, M31, M32 |
| (medium confidence, M32) | observability.md, security-rbac-tls.md, storage-and-scaling.md (Enterprise features) | M31, M32 |
| (unverified) | licensing.md | I1, I2 |
| (medium confidence) | security-rbac-tls.md | M9, M10, M12, M13, M14, M30 |
| (unverified) | security-rbac-tls.md | I2, U5 |
| (medium confidence) | storage-and-scaling.md | M4, M5, M6, M7, M17, M26, M29 |
| (unverified) | storage-and-scaling.md | I3, U4, U10 |
| (medium confidence) | upgrades-and-zk-migration.md | M1, M2, M3, M11, M12, M22, M25, M27, M28, M30 |
| (unverified) | upgrades-and-zk-migration.md | I4, U3, U12 |
| (medium confidence) | observability.md | M8, M20 |
| (unverified) | observability.md | U11 |
| (medium confidence), (unverified) | evaluation-scenarios.md | M24, M31, M32, I1, I2, I4, U3, U12 |

## Source Bibliography

All pages read 2026-11-04 with WebFetch. S29 and S30 are landing pages with no facts used and are not cited. Base URL `https://docs.confluent.io/operator/3.4/` is written as `~/`.

| ID | Title | URL |
|---|---|---|
| S1 | Release Notes (release 2026-10-28) | ~/release-notes.html |
| S2 | Supported Environments (updated 2026-11-02) | ~/co-supported-environments.html |
| S3 | Manage Licenses (updated 2026-10-28) | ~/co-license.html |
| S4 | Manage Confluent Platform Licenses (CP 8.4, updated 2026-10-29) | https://docs.confluent.io/platform/current/installation/license.html |
| S5 | Deploy CFK | ~/co-deploy-operator.html |
| S6 | Upgrade CFK | ~/co-upgrade-cfk.html |
| S7 | Upgrade overview | ~/co-upgrade-overview.md |
| S8 | Upgrade Confluent Platform | ~/co-upgrade-cp.md |
| S9 | Configure KRaft (updated 2026-10-27) | ~/co-configure-kraft.html |
| S10 | Migrate ZooKeeper to KRaft overview | ~/co-migrate-kraft-overview.html |
| S11 | API reference | ~/co-api.html |
| S12 | Configure Storage | ~/co-storage.md |
| S13 | Quick Start with KRaft | ~/co-quickstart-kraft.md |
| S14 | Quick Start landing | ~/co-quickstart.md |
| S15 | Network Encryption | ~/co-network-encryption.md |
| S16 | Authentication for Kafka, KRaft, MDS | ~/co-authenticate-kafka.md |
| S17 | Configure Authorization overview | ~/co-authorize-overview.md |
| S18 | Configure RBAC | ~/co-rbac.md |
| S19 | Configure Simple ACLs | ~/co-simple-acls.md |
| S20 | Scale clusters and balance data | ~/co-scale-cluster.md |
| S21 | Configure CPU and Memory | ~/co-resources.md |
| S22 | Plan Capacity and Sizing | ~/co-plan-sizing.md |
| S23 | Monitor Confluent Platform | ~/co-monitor-cp.md |
| S24 | Plan availability, settings fixed after deploy | ~/co-plan-availability.md |
| S25 | Configure Kafka Connect | ~/co-configure-connect.md |
| S26 | Multiple Availability Zones | ~/co-multi-az.md |
| S27 | Schedule workloads | ~/co-schedule-workloads.md |
| S28 | Use custom image registries | ~/co-custom-registry.md |
| S31 | Strimzi downloads: Strimzi 1.3.0 supports Kafka 4.2.0, 4.2.1, 4.2.2, 4.3.0, 4.3.1 on Kubernetes 1.32-1.37 (tested), 4.4.0 not listed (read 2026-11-04) | https://strimzi.io/downloads/ |
