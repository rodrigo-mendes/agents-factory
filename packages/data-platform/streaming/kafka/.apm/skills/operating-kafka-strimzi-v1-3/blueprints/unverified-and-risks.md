# Unverified and risks register, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). Provenance: the official pages in the Source Bibliography below (read 2026-11-04). Conflicts and gaps below are not resolved here; a human or a live 1.3.1 cluster must settle them.

## Version-lifetime risk

- Strimzi 1.3.1 was tagged 2026-11-04T10:24:25Z. Its versioned docs URL returned HTTP 404 on 2026-11-04 (I1), and strimzi.io/downloads still lists 1.3.0 as latest. Evidence is the 1.3.0 docs plus the 1.3.1 release notes.
- 1.3.1 is a patch release: it adds Kafka 4.3.2, fixes concurrency bugs and updates dependencies. 1.3.1-specific defaults are inferred from 1.3.0 docs (U9).
- Kafka 4.4.0 was released 2026-10-22 (https://kafka.apache.org/community/downloads/, read 2026-11-04). It is not in the Strimzi 1.3.0 supported list (High: https://strimzi.io/downloads/, read 2026-11-04). No page read states when a Strimzi release adds Kafka 4.4.
- No per-release support or end-of-life policy was found (I2). Re-check strimzi.io before relying on this skill after the next Strimzi release.
- Deprecated in 1.3.0: PKCS12 certificates. Early Access: internal cluster security and cert-manager integration. Deprecated listener type: `ingress`.

## Unverified (U1..U13): 13 items

| ID | Item | Tag |
|---|---|---|
| U1 | Helm chart 1.3.1 existence and `--version 1.3.1` usage (only 1.3.0 is in the classic index) | (unverified) |
| U2 | Whether 1.3.x ignores or rejects the older `strimzi.io/node-pools` and `strimzi.io/kraft` annotations | (unverified) |
| U3 | The hardened overlay and the KafkaUser / listener YAML shapes as combinations (assembled from documented fields) | (unverified) |
| U4 | The Connect and connector YAML (field names `bootstrapServers`, `tls`, `certificateAndKey`, `state` values) | (unverified) |
| U5 | OAuth `listenerConfig` JAAS string and the `${secrets:...}` placeholder syntax | (unverified) |
| U6 | kubectl verification commands (grep patterns, columns, `--dry-run=server`, under-replicated check, label selector, Kubernetes version wording) | (unverified) |
| U7 | Exact CRD file names to apply for 1.3.1 before `helm upgrade` | (unverified) |
| U8 | `metadataVersion` for Kafka 4.3.2 (the official example shows 4.3-IV0 for 4.3.1) | (unverified) |
| U9 | 1.3.1 defaults inferred from 1.3.0 docs (for example the Connect default Kafka version) | (unverified) |
| U10 | No Strimzi-native topic-data backup and no Velero or snapshot guidance in the pages read (absence of evidence) | (unverified) |
| U11 | Storage `class` field name and PDB template placement on a `KafkaNodePool` | (unverified) |
| U12 | Contents of example files other than `kafka-persistent.yaml`; no documented mocking framework for custom resources | (unverified) |
| U13 | Reading of "storage reduction is only possible with several disks per broker" as meaning removal of a JBOD volume after its data has moved (inferred, not stated) | (unverified) |

## Irresolvable (I1..I4): 4 items

| ID | Item | Tag |
|---|---|---|
| I1 | 1.3.1 versioned docs are not published (404 on 2026-11-04). Follow-up: https://strimzi.io/docs/operators/1.3.1/deploying.html | (unverified) |
| I2 | No per-release support or end-of-life policy found by search or on the pages read. Treat the latest release as supported | (unverified) |
| I3 | `UseBackgroundPodDeletion` default: the 1.3.0 release notes say beta and enabled, the feature-gate reference says disabled. Set the gate explicitly | (unverified) |
| I4 | Pod naming: some pages use `<cluster>-kafka-<index>`, others `<cluster>-<pool>-<id>`. Discover names on the live cluster | (unverified) |

## Medium confidence (M1..M22): 22 items

| ID | Claim | Tag |
|---|---|---|
| M1 | Set CPU and memory requests and limits; Strimzi sets none by default; heap and GC options in `jvmOptions` | (medium confidence) |
| M2 | One namespace per Kafka cluster and per Connect cluster | (medium confidence) |
| M3 | `auto.create.topics.enable: false` when topics come from `KafkaTopic` | (medium confidence) |
| M4 | Block storage only (and tiered storage statement, one page) | (medium confidence) |
| M5 | `strimzi.io/use-connector-resources: "true"` before creating connectors | (medium confidence) |
| M6 | `sha512sum` on every Connect build artifact | (medium confidence) |
| M7 | Set `spec.version` on KafkaConnect and KafkaMirrorMaker2 | (medium confidence) |
| M8 | Connect hardening: disallowed login modules and override policy `None` | (medium confidence) |
| M9 | `maintenanceTimeWindows` for certificate renewals | (medium confidence) |
| M10 | `networkPolicyPeers` to restrict listeners | (medium confidence) |
| M11 | `replica.selector.class` set by the user (class name from Kafka, not the Strimzi page) | (medium confidence) |
| M12 | Kafka Exporter for consumer-lag metrics | (medium confidence) |
| M13 | Quote `metadataVersion` as a string | (medium confidence) |
| M14 | Keep `min.insync.replicas` in `spec.kafka.config` (operator falls back to 1) | (medium confidence) |
| M15 | `RackAwareGoal` rebalance after moving nodes between pools | (medium confidence) |
| M16 | KafkaTopic replica change: Cruise Control page and topic page conflict | (medium confidence) |
| M17 | Single-source procedure details: reconciliation interval (2 minutes) and `strimzi.io/pause-reconciliation`, node IDs 0 to 999 and next/remove annotations, Cruise Control topics and goals, KafkaTopic rules, user secrets, recovery details, YAML install steps, example file names | (medium confidence) |
| M18 | CHANGELOG-only facts (read partly, main branch): health-check port rename, removed resource-state metrics, no OPA authorizer, Access Operator 0.2.0, restricted Pod Security default, dropped Kafka 4.0 and 4.1 | (medium confidence) |
| M19 | `tlsroute` (Gateway API) maturity and the `ingress` deprecation reason | (medium confidence) |
| M20 | Finalizer handling for `KafkaTopic` (`STRIMZI_USE_FINALIZERS=false`) | (medium confidence) |
| M21 | Seven single-source prohibitions (ingress, Strimzi-created ConfigMaps, `metadataVersion` downgrade, Connect internal topic RF, MM2 ACL sync with User Operator, PKCS12 keystores, encrypted private keys) | (medium confidence) |
| M22 | ZooKeeper support removed in Strimzi 0.46 (the release number; the KRaft-only claim itself is High), and the advice to migrate to KRaft on Strimzi 0.45.x first | (medium confidence) |

## Coverage limits (L1..L7): 7 items

| ID | Limit |
|---|---|
| L1 | `deploying.html` was read in full (733340 chars) but its converted text ends at section 18.3.4; later sections came from the AsciiDoc modules at tag 1.3.0 |
| L2 | CHANGELOG read 100000 of 106760 characters, main branch rather than the tag |
| L3 | Not read: downgrade modules, JBOD reassignment (section 23), partition reassignment tool (section 24), tracing, tuning, uninstall |
| L4 | Of the official examples only `kafka-persistent.yaml` was read |
| L5 | The listener authentication page looked cut in the SCRAM section; SCRAM details cross-checked with the client authentication page |
| L6 | Every page was read through WebFetch, a summarizing tool, not verbatim text |
| L7 | The GitHub releases API page was read 100000 of 155790 characters (timestamps only) |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Version Context and Ask First (Helm 1.3.1, 1.3.1 defaults, end-of-life) | U1, U9, I2 |
| (unverified, I3), (unverified, I4) | SKILL.md Ask First (`UseBackgroundPodDeletion` default, pod names) | I3, I4 |
| (unverified) | SKILL.md Quick Reference (`kubectl apply --dry-run=server`), hardened-overlay.md | U6 |
| (medium confidence) | SKILL.md Version Context, Quick Reference, Ask First (ZooKeeper release number, reconciliation, node IDs, tlsroute, practices) | M22, M17, M19, M1..M4 |
| (medium confidence) | ask-first-decisions.md (recommendations, prohibitions, tlsroute) | M1..M15, M19, M21 |
| (unverified) | ask-first-decisions.md (Helm chart 1.3.1, 1.3.1 Connect default) | U1, U9 |
| (unverified) | always-do-patterns.md, never-do-patterns.md (commands, CRD file name, metadataVersion, OAuth placeholder) | U5, U6, U7, U8 |
| (unverified) | deploy-install-and-cr.md | U1, U2, U3, U6, U8, U11 |
| (medium confidence) | deploy-install-and-cr.md, storage-and-scaling.md | M3, M4, M11, M15, M17, M18 |
| (unverified), (medium confidence) | security-listeners-auth.md | U3, U5, M9, M10 |
| (unverified), (medium confidence) | connect-topics-users.md | U4, M5..M8, M16, M17, M20 |
| (unverified), (medium confidence) | observability.md | U6, U12, M1, M12, M17, M18 |
| (unverified), (medium confidence) | recovery-and-dr.md, rolling-updates-and-upgrades.md | U10, M17, M18, M21, M22 |
| (unverified), (medium confidence) | evaluation-scenarios.md | U3, U9, M22 |
| (unverified) | rolling-updates-and-upgrades.md (sed and jsonpath commands) | U6 |
| (unverified) | storage-and-scaling.md (JBOD reading of the storage-reduction sentence) | U13 |

## Source Bibliography

All pages read 2026-11-04 with WebFetch. Docs and the 1.3.0 tag date 2026-10-12; 1.3.1 tag date 2026-11-04. Navigation-only GitHub tree listings are not cited.

- S1 https://strimzi.io/downloads/ ; S2 https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0 ; S3 https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.1 ; S4 https://api.github.com/repos/strimzi/strimzi-kafka-operator/releases?per_page=8 ; S5 https://github.com/strimzi/strimzi-kafka-operator/releases
- S6 https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/main/CHANGELOG.md (partly read)
- S7 https://strimzi.io/docs/operators/1.3.0/deploying.html ; S8 https://strimzi.io/docs/operators/1.3.0/configuring.html ; S9 https://strimzi.io/docs/operators/1.3.1/deploying.html (HTTP 404) ; S10 https://strimzi.io/charts/index.yaml
- S11 https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/helm-charts/helm3/strimzi-kafka-operator/README.md ; S12 https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/examples/kafka/kafka-persistent.yaml
- AsciiDoc base `https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/`, then:
- S13 assemblies/upgrading/assembly-upgrade.adoc ; S14 assemblies/upgrading/assembly-upgrade-cluster-operator.adoc ; S15 modules/upgrading/proc-upgrade-cluster-operator.adoc ; S16 modules/upgrading/proc-upgrade-kafka-kraft.adoc ; S17 modules/upgrading/con-upgrade-sequence.adoc ; S18 modules/upgrading/con-upgrade-paths.adoc ; S19 modules/upgrading/con-api-conversion-v1.adoc ; S20 modules/upgrading/con-upgrade-cluster.adoc
- S21 assemblies/cruise-control/assembly-cruise-control-concepts.adoc ; S22 modules/cruise-control/proc-configuring-deploying-cruise-control.adoc ; S23 modules/cruise-control/proc-generating-optimization-proposals.adoc ; S24 modules/cruise-control/proc-approving-optimization-proposal.adoc ; S25 modules/cruise-control/proc-automating-rebalances.adoc
- S26 assemblies/deploying/assembly-rolling-updates.adoc ; S27 modules/managing/proc-manual-rolling-update-pods.adoc ; S28 assemblies/deploying/assembly-cluster-recovery-volume.adoc ; S29 modules/managing/con-cluster-recovery-scenarios.adoc ; S30 modules/managing/proc-cluster-recovery-volume.adoc
- S31 assemblies/metrics/assembly-metrics.adoc ; S32 modules/metrics/con_metrics-prometheus-options.adoc ; S33 modules/metrics/proc-strimzi-metrics-reporter-kafka-deploy-options.adoc ; S34 modules/metrics/proc-jmx-exporter-metrics-kafka-deploy-options.adoc ; S35 modules/metrics/proc-kafka-exporter-deploy.adoc
- S36 modules/security/con-securing-kafka-authentication.adoc ; S37 modules/security/con-securing-kafka-authorization.adoc ; S38 modules/security/con-securing-client-authentication.adoc ; S39 modules/security/con-securing-client-acls.adoc ; S40 modules/security/con-certificate-renewal.adoc ; S41 modules/security/proc-restricting-access-to-listeners-using-network-policies.adoc
- S42 modules/operators/proc-configuring-kafka-topic.adoc ; S43 modules/operators/con-topic-replication.adoc ; S44 modules/operators/con-application-topic-handling.adoc ; S50 modules/operators/ref-operator-cluster-feature-gates.adoc ; S59 modules/operators/proc-configuring-kafka-user.adoc
- S45 modules/configuring/con-skipping-scale-down-checks.adoc ; S46 modules/configuring/con-maintenance-time-window-definition.adoc ; S47 modules/configuring/proc-distributing-brokers-across-zones.adoc ; S48 modules/configuring/con-node-pools-racks.adoc ; S49 modules/configuring/proc-scaling-down-node-pools.adoc ; S51 modules/configuring/con-common-configuration.adoc ; S52 modules/configuring/con-config-kafka-connect-build.adoc ; S53 modules/configuring/proc-disable-pod-disruption-budget-generation.adoc ; S58 modules/configuring/proc-managing-node-pools-ids.adoc
- S54 modules/oauth/con-oauth-migration.adoc ; S55 modules/oauth/con-oauth-server-config.adoc ; S56 modules/drain-cleaner/proc-drain-cleaner-using.adoc ; S57 assemblies/deploying/assembly-kraft-mode.adoc
- Supported Kafka versions of Strimzi 1.3.0 (4.2.0, 4.2.1, 4.2.2, 4.3.0, 4.3.1 on Kubernetes 1.32-1.37 tested; 4.4.0 not listed): High, https://strimzi.io/downloads/ (S1), read 2026-11-04. Kafka 4.4.0 release date (2026-10-22): https://kafka.apache.org/community/downloads/, read 2026-11-04.
