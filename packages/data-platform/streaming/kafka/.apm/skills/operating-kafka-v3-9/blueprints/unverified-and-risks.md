# Unverified and risks register, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). Provenance: the official pages in the Source Bibliography below (research date 2026-11-04). Items U4, U15 and U26 are gaps or ambiguities that this skill does not resolve: a human must verify them. The U ids are not contiguous: the range is U1..U31, the ids U16, U17, U18, U20 and U21 are unused, and the header counts the 26 rows.

## Version-lifetime risk

- Kafka 3.9.2 was released 2026-02-21 (https://kafka.apache.org/community/downloads/, read 2026-11-04).
- 3.9 is the last ZooKeeper line and the last bridge release [S40]. ZooKeeper mode is deprecated since 3.5 and removed in 4.0 [S6][S41].
- The downloads page lists 3.9.x under Archived Releases and lists only 4.4.0, 4.3.2 and 4.2.2 as supported (medium confidence, M2). Expect no further 3.9.x patches (medium confidence, M2).
- The 3.9 ZooKeeper page promises critical bug fixes and security fixes for the last ZooKeeper-capable 3.x release for 12 months after its release [S6]. The start date is not stated (unverified, U4).
- Support policy: the Apache wiki says rolling upgrades are tested from the last 3 releases, bugfix releases are attempted for the last 3, and a release ships every 4 months (medium confidence, M1, [S43]). No official per-version end-of-life table exists (unverified, U15).
- Successor: Kafka 4.4.0, released 2026-10-22 (skill `operating-kafka-v4-4`). Re-check the downloads page before relying on 3.9.x for security fixes.

## Unverified (U1..U31): 26 items (26 rows; ids U16-U18 and U20-U21 are unused)

| ID | Item | Tag | Note |
|---|---|---|---|
| U1 | The `apache/kafka:3.9.2` default CMD cannot start a ZooKeeper-mode broker, and `command: kafka-server-start.sh <props>` works. Inferred from source [S30][S31][S32][S33], not run. Side effect: the KAFKA_ env mapping does not run with the override | (medium confidence) | Test before relying on it |
| U2 | Named volumes at `/var/lib/kafka/data` writable by `appuser`, ZooKeeper data under that path | (unverified) | Test |
| U3 | 3.9.2 satisfies the migration text "3.9.1", and the "Upgrading to 3.9.1" steps apply to 3.9.2 | (medium confidence) | Section title only names 3.9.1 |
| U4 | Start date of the "12 months after its release" ZooKeeper fix window | (unverified) | Human-verify. Wording is ambiguous, no dated table. From 3.9.0 (2024-11-06) it ended 2025-11-06, yet 3.9.2 shipped 2026-02-21 |
| U5 | Dynamic-quorum formatting through the image's default startup. The wrapper passes only `--cluster-id` and `-c` [S31] | (unverified) | Manual format needed |
| U6 | ZooKeeper SASL quorum auth keys (`quorum.auth.*`) | (unverified) | Not in the chunks read |
| U7 | `ssl.enabled.protocols` default: the config page read `TLSv1.2`, the SSL page example lists `TLSv1.2,TLSv1.1,TLSv1` | (medium confidence) | Set `TLSv1.2,TLSv1.3` explicitly |
| U8 | Default of `allow.everyone.if.no.acl.found` not shown on the ACL or broker config pages | (unverified) | No matching ACL means only super users have access [S10] |
| U9 | KRaft SCRAM bootstrap on 3.9 (`kafka-storage --add-scram`, `kafka-configs --bootstrap-server`) not on the 3.9 SASL page | (unverified) | Page covers ZooKeeper-mode SCRAM |
| U10 | Native Kafka backup tool (absence), ZooKeeper backup and restore procedure, consumer failover steps between clusters | (unverified) | Absence of evidence |
| U11 | Failover durations, RTO and RPO numbers, alert durations and thresholds beyond the value 0, ZooKeeper normal ranges | (unverified) | Set from your own baseline |
| U12 | Healthcheck and diagnostic commands inside the image: `zookeeper-shell.sh ls /`, bash `/dev/tcp` with `srvr`, `zookeeper-shell.sh getAcl`, `kafka-topics.sh --under-min-isr-partitions` | (unverified) | Inferred commands |
| U13 | Docker scripts and Dockerfile were read from branch `3.9` head, not tag `3.9.2` (dependencies.gradle and zookeeper.properties were read from tag 3.9.2). Covers `/opt/kafka`, volumes, `appuser`, base image, JMX defaults, default `CLUSTER_ID`, `configure` script messages | (medium confidence) | Re-check against the tag |
| U14 | Dynamic keystore and certificate rotation on 3.9 (research id U7b) | (unverified) | Plan a rolling restart |
| U15 | Official per-version end-of-life table | (unverified) | Human-verify. None on kafka.apache.org |
| U19 | Controller versus broker order in a KRaft rolling upgrade on 3.9 | (unverified) | Not stated on the upgrade page |
| U22 | `zookeeper.set.acl` with mTLS only: the authentication page sample sets it, the encryption page says to set it only with SASL | (medium confidence) | Follow the authentication page for mTLS |
| U23 | Exact secure JMX flag set (JDK standard, not on the Kafka page) | (medium confidence) | Image also needs `jmxremote.rmi.port` in `KAFKA_JMX_OPTS` [S28] |
| U24 | Procedure for changing ZooKeeper ensemble membership (`reconfigEnabled` is false by default) | (unverified) | |
| U25 | Handling of ZooKeeper cluster IDs with a leading dash (KAFKA-19988 doc fix) | (unverified) | |
| U26 | Building a 3-controller quorum for the migration (before or after the metadata load) | (unverified) | Human-verify. The page shows a `--standalone` first controller and generic add-controller only |
| U27 | ZooKeeper manual purge tool and procedure | (unverified) | |
| U28 | The whole ZooKeeper-ensemble Compose layout in [deploy-compose-zookeeper](./deploy-compose-zookeeper.md) | (unverified) | Assembled from official keys, not run |
| U29 | Compose mechanics of the migration controller service (command, `--ignore-formatted`, `log.dirs`) | (unverified) | `--ignore-formatted` exists [S32][S13]; idempotent restart use is inferred |
| U30 | Inferred operational statements: failover bounded by session timeout, minority quorum stops metadata changes, broker disk-loss re-replication, reverse MM2 flow restore, MM2 RPO equals lag, AtMinIsr alert meaning, ZooKeeper quorum loss blocks metadata changes | (unverified) | From majority-quorum semantics |
| U31 | Tuning values with no official threshold: session timeout tuning, `zookeeper.ssl.protocol`, `num.replica.fetchers`, `maxClientCnxns` value, `linger.ms` and `batch.size` numbers, disk-sizing formula | (unverified) | Measure |

## Irresolvable (I1..): 0 items

No separate irresolvable class is kept. Facts that cannot be resolved from documentation are listed once above as U-ids (U4, U15, U26) with a human-verify note.

## Medium confidence (M1..M17): 17 items

| ID | Claim | Tag |
|---|---|---|
| M1 | Support policy from the Apache wiki Time Based Release Plan [S43], last edited 2024-07-09 | (medium confidence) |
| M2 | 12-month critical-fix statement and 3.9.x listed as Archived; downloads page partly read | (medium confidence) |
| M3 | Combined mode "not recommended in critical deployment environments", one official page [S1] | (medium confidence) |
| M4 | ZooKeeper-mode SCRAM storage is suitable for production only where ZooKeeper is secure and private, one page [S9] | (medium confidence) |
| M5 | Docker Compose is single-host, so dev, CI or staging only; per-device bind mounts are needed for a dedicated `dataLogDir` (inference) | (medium confidence) |
| M6 | When to set `alter.config.policy.kraft.compatibility.enable=true` (KIP-1252) | (medium confidence) |
| M7 | `KAFKA_HEAP_OPTS` and `KAFKA_JVM_PERFORMANCE_OPTS` are read by the Kafka start scripts | (medium confidence) |
| M8 | Absence claims: no official broker Prometheus exporter, no native at-rest encryption, PITR not a broker feature, no official partition-count formula | (medium confidence) |
| M9 | Pinning the image tag is factory practice, not a docs statement | (medium confidence) |
| M10 | Single-page ZooKeeper Admin Guide, hardware page and upgrade-page guidance kept out of Always Do (autopurge, 4lw, AdminServer, heap, file descriptors, disk sizing numbers, other sizing numbers, ZooKeeper binary upgrade). The dedicated `dataLogDir` device is not in this list: it is an Always Do item because the ZooKeeper page and the Admin Guide both state it | (medium confidence) |
| M11 | The ZooKeeper-to-KRaft migration procedure and finalize guidance rest on one official page, the 3.9 KRaft page. The `inter.broker.protocol.version=3.9` prerequisite is excluded: it is an Always Do item because the KRaft page and the upgrade notes both state it | (medium confidence) |
| M12 | `auto.create.topics.enable=false` appears in the production example only as a value, not as a rule | (medium confidence) |
| M13 | Single-page security guidance: SASL/PLAIN needs TLS, default OAUTHBEARER, `ssl.client.auth=requested`, authorizer class, ZooKeeper ACL step order, sasl mechanism choice | (medium confidence) |
| M14 | Format every KRaft node with the same cluster ID: the multi-node rule is on one official page (KRaft [S1]); the quickstart [S38] shows a one-node format only | (medium confidence) |
| M15 | Wait for the ISR to rejoin before restarting the next broker: stated by one official page (running cluster [S20]); the upgrade notes [S5] only say to roll one broker at a time | (medium confidence) |
| M16 | Odd KRaft controller quorum of 3 or 5 (2N+1 survives N failures): one versioned page (KRaft [S1]) | (medium confidence) |
| M17 | Do not format or start a replacement KRaft controller until a majority of controllers has all committed data: one official page (KRaft [S1]) | (medium confidence) |

## Coverage limits (L1..L4): 4 items

| ID | Limit |
|---|---|
| L1 | Downloads page (F1, F4) read 100000 of 152730 characters. The 3.9.x and supported-releases entries were inside the part read |
| L2 | The 4.4 KRaft page and the 4.0.0 announcement were read in full by the orchestrator on 2026-11-04; the skill author used only their bridge-release and ZooKeeper sentences |
| L3 | Every page was read through WebFetch, which returns a summarized page, not verbatim text. For pages under 100000 characters the sizes are estimates, one untruncated call each |
| L4 | The tiered storage page was not read, and the operations index was read as navigation only |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md lifecycle warning, Version Context, Ask First (support window) | M2, U15 |
| (unverified) | SKILL.md lifecycle warning, Ask First (support window, start date) | U4 |
| (medium confidence) | SKILL.md Version Context and Ask First (image, ZooKeeper-mode command override) | U1 |
| (unverified) | SKILL.md Ask First (Compose layout, quorum type, 3-controller quorum) | U28, U5, U26 |
| (medium confidence) | SKILL.md Ask First (migration procedure, patch, combined mode, auto-create, cluster ID, rolling restart pacing) | M11, U3, M3, M12, M14, M15 |
| (medium confidence) | always-do-patterns.md (paths, Compose single-host, cluster ID, rolling restart pacing) | U13, M5, M14, M15 |
| (unverified) | always-do-patterns.md (ZooKeeper health command) | U12 |
| (medium confidence), (unverified) | ask-first-decisions.md | U1, U3, U4, U5, U7, U8, U13, U14, U15, U19, U23, U26, M2, M3, M4, M5, M6, M9, M10, M11, M12, M13, M14, M15 |
| (medium confidence), (unverified) | deploy-compose-zookeeper.md | U1, U2, U12, U13, U23, U28, M5, M7, M10 |
| (medium confidence), (unverified) | zookeeper-ensemble.md | M10, U10, U12, U24, U27, U31 |
| (medium confidence), (unverified) | zookeeper-security.md | M4, M8, M13, U6, U7, U8, U9, U13, U14, U22 |
| (medium confidence), (unverified) | zk-to-kraft-migration.md | M6, M11, U3, U19, U25, U26, U29 |
| (unverified) | high-availability-dr.md, observability.md | U10, U11, U12, U27, U30 |
| (medium confidence) | high-availability-dr.md, observability.md | M5, M8, M16, M17 |
| (medium confidence), (unverified) | performance-tuning.md, capacity-sizing.md | M6, M7, M8, M10, M11, M12, M13, U7, U31 |
| (medium confidence), (unverified) | evaluation-scenarios.md | U1, U3, U4, U5, U15, U26, U28, M11 |

## Source Bibliography

All pages read 2026-11-04. S27 and S42 are not cited.

| ID | Title | URL |
|---|---|---|
| S1 | KRaft (incl. ZooKeeper to KRaft Migration), AK 3.9.X | https://kafka.apache.org/39/operations/kraft/ |
| S2 | Docker, AK 3.9.X | https://kafka.apache.org/39/getting-started/docker/ |
| S3 | Docker examples README, branch 3.9 | https://raw.githubusercontent.com/apache/kafka/3.9/docker/examples/README.md |
| S4 | Compose example cluster/isolated/plaintext, branch 3.9 | https://raw.githubusercontent.com/apache/kafka/3.9/docker/examples/docker-compose-files/cluster/isolated/plaintext/docker-compose.yml |
| S5 | Upgrading, AK 3.9.X | https://kafka.apache.org/39/getting-started/upgrade/ |
| S6 | ZooKeeper, AK 3.9.X Operations | https://kafka.apache.org/39/operations/zookeeper/ |
| S7 | ZooKeeper Authentication, AK 3.9.X | https://kafka.apache.org/39/security/zookeeper-authentication/ |
| S8 | ZooKeeper Encryption, AK 3.9.X | https://kafka.apache.org/39/security/zookeeper-encryption/ |
| S9 | Authentication using SASL, AK 3.9.X | https://kafka.apache.org/39/security/authentication-using-sasl/ |
| S10 | Authorization and ACLs, AK 3.9.X | https://kafka.apache.org/39/security/authorization-and-acls/ |
| S11 | Broker Configs, AK 3.9.X | https://kafka.apache.org/39/configuration/broker-configs/ |
| S12 | Design, AK 3.9.X | https://kafka.apache.org/39/design/design/ |
| S13 | Hardware and OS, AK 3.9.X | https://kafka.apache.org/39/operations/hardware-and-os/ |
| S14 | Java Version, AK 3.9.X | https://kafka.apache.org/39/operations/java-version/ |
| S15 | Topic-Level Configs, AK 3.9.X | https://kafka.apache.org/39/configuration/topic-level-configs/ |
| S16 | Producer Configs, AK 3.9.X | https://kafka.apache.org/39/configuration/producer-configs/ |
| S17 | Consumer Configs, AK 3.9.X | https://kafka.apache.org/39/configuration/consumer-configs/ |
| S18 | Encryption and Authentication using SSL, AK 3.9.X | https://kafka.apache.org/39/security/encryption-and-authentication-using-ssl/ |
| S19 | Listener Configuration, AK 3.9.X | https://kafka.apache.org/39/security/listener-configuration/ |
| S20 | Incorporating Security Features in a Running Cluster, AK 3.9.X | https://kafka.apache.org/39/security/incorporating-security-features-in-a-running-cluster/ |
| S21 | Monitoring, AK 3.9.X | https://kafka.apache.org/39/operations/monitoring/ |
| S22 | Datacenters, AK 3.9.X | https://kafka.apache.org/39/operations/datacenters/ |
| S23 | Geo-Replication, AK 3.9.X | https://kafka.apache.org/39/operations/geo-replication-cross-cluster-data-mirroring/ |
| S24 | Basic Kafka Operations, AK 3.9.X | https://kafka.apache.org/39/operations/basic-kafka-operations/ |
| S25 | Apache Kafka Downloads (partly read) | https://kafka.apache.org/community/downloads/ |
| S26 | Kafka 3.9.2 Release Notes | https://archive.apache.org/dist/kafka/3.9.2/RELEASE_NOTES.html |
| S28 | Docker image `configure` script, branch 3.9 | https://raw.githubusercontent.com/apache/kafka/3.9/docker/resources/common-scripts/configure |
| S29 | Docker image `configureDefaults` script, branch 3.9 | https://raw.githubusercontent.com/apache/kafka/3.9/docker/resources/common-scripts/configureDefaults |
| S30 | Docker image JVM `launch` script, branch 3.9 | https://raw.githubusercontent.com/apache/kafka/3.9/docker/jvm/launch |
| S31 | KafkaDockerWrapper.scala, branch 3.9 | https://raw.githubusercontent.com/apache/kafka/3.9/core/src/main/scala/kafka/docker/KafkaDockerWrapper.scala |
| S32 | StorageTool.scala, branch 3.9 | https://raw.githubusercontent.com/apache/kafka/3.9/core/src/main/scala/kafka/tools/StorageTool.scala |
| S33 | Docker JVM image Dockerfile, branch 3.9 | https://raw.githubusercontent.com/apache/kafka/3.9/docker/jvm/Dockerfile |
| S34 | Docker Hub tag apache/kafka:3.9.2 (registry API) | https://hub.docker.com/v2/repositories/apache/kafka/tags/3.9.2 |
| S35 | gradle/dependencies.gradle, tag 3.9.2 | https://raw.githubusercontent.com/apache/kafka/3.9.2/gradle/dependencies.gradle |
| S36 | config/zookeeper.properties, tag 3.9.2 | https://raw.githubusercontent.com/apache/kafka/3.9.2/config/zookeeper.properties |
| S37 | ZooKeeper 3.8.4 Administrator's Guide | https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html |
| S38 | Quick Start, AK 3.9.X | https://kafka.apache.org/39/getting-started/quickstart/ |
| S39 | Kafka Configuration (production server config example), AK 3.9.X | https://kafka.apache.org/39/operations/kafka-configuration/ |
| S40 | KRaft, AK 4.4.X (read in full 2026-11-04) | https://kafka.apache.org/44/operations/kraft/ |
| S41 | Apache Kafka 4.0.0 Release Announcement (2025-03-18, read in full 2026-11-04) | https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/ |
| S43 | Time Based Release Plan (Apache Kafka wiki, official Apache wiki, last edited 2024-07-09, read 2026-11-04) | https://cwiki.apache.org/confluence/display/KAFKA/Time+Based+Release+Plan |
