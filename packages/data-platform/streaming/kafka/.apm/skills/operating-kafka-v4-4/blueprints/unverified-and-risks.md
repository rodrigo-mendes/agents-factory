# Unverified and risks register, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). Provenance: the official pages in the Source Bibliography below (research date 2026-11-04). Items U1, U4 and U13 are conflicts or gaps that this skill does not resolve: a human must verify them.

## Version-lifetime risk

- Kafka 4.4.0 was released 2026-10-22 (https://kafka.apache.org/community/downloads/, read 2026-11-04).
- Deprecated in 4.4 for removal in 5.0: `broker.id` (use `node.id`) and `kafka-broker-api-versions.sh` (use `kafka-cluster.sh api-versions`) [S1].
- Support policy: the Apache wiki says rolling upgrades are tested from the last 3 releases, bugfix releases are attempted for the last 3 releases, and a release ships every 4 months (medium confidence, M9). No official per-version end-of-life table exists (unverified, U13).
- No successor to 4.4.0 (released 2026-10-22) is recorded in the pages read on 2026-11-04. Re-check the downloads page for any release after 4.4.0 before relying on this skill.

## Unverified (U1..U20): 20 items

| ID | Item | Tag | Note |
|---|---|---|---|
| U1 | Native image SASL support in 4.4.0: the Docker page says supported, the 4.4-branch examples README says not supported (KAFKA-19584) | (unverified) | Two official sources conflict. Human-verify. Use the JVM image for SASL |
| U2 | Body of "Upgrading Servers to 4.4.0" is empty. Steps are inferred from the 4.3 and 4.2 notes. Whether 4.4 supports metadata downgrade is unknown. The 3.9.x to 4.4.0 direct-upgrade row follows the same inference | (unverified) | See migration guide |
| U3 | `apache/kafka` image: data path ownership and UID, bundled JRE version, heap environment variable names, `/opt/kafka` bin path | (unverified) | `/opt/kafka` is inferred from the README (medium confidence); the rest is unverified |
| U4 | The compatibility page (4.0 matrix) says upgrading static to dynamic voters is not supported (KAFKA-16538). The KRaft page documents `kraft.version=1` upgrade via `--release-version 4.1` | (medium confidence) | Human-verify. The KRaft page is newer and more specific, but the conflict is not resolved here |
| U5 | Dynamic quorum formatting through the Docker image environment variables | (unverified) | README documents `CLUSTER_ID` only |
| U6 | Broker config page reading returned `message.timestamp.after.max.ms` default 9223372036854775807. Topic page and upgrade notes say 1 hour at topic level | (medium confidence) | The broker-page value is possibly a summarizer artifact. 1 hour is used |
| U7 | Hot keystore reload without restart | (unverified) | Plan a rolling restart |
| U8 | No native at-rest encryption and no native backup tool for partition data in the 4.4 pages read | (unverified) | Absence of evidence |
| U9 | Typical failover duration, RTO and RPO numbers, alert thresholds beyond the value 0, and an official partition-count formula | (unverified) | Set thresholds from your own baseline |
| U10 | KIP-1291 Linux I/O metric names | (unverified) | Named in the 4.4.0 announcement only |
| U11 | Rolling upgrade node order (controllers first) | (unverified) | Common practice, not in the 4.4 page |
| U12 | `auto.create.topics.enable=false` recommendation | (medium confidence) | Factory practice, not stated in the docs |
| U13 | Official per-version end-of-life table | (unverified) | None exists on kafka.apache.org. Human-verify. Wiki policy only (M9) |
| U14 | `super.users` and `log.cleaner.*` defaults not captured from the broker config page | (unverified) | `super.users` usage is taken from the ACL page |
| U15 | SSL page example shows `ssl.enabled.protocols` as `TLSv1.2,TLSv1.1,TLSv1`, the config page default is `TLSv1.2,TLSv1.3` | (medium confidence) | Config page value used |
| U16 | A JMX-to-Prometheus bridge for 4.4: the monitoring page names no exporter, so any bridge and its 4.4 compatibility are third-party | (unverified) | Not official, not researched |
| U17 | Exact broker startup and refusal messages: OAUTHBEARER JWKS without audience and issuer, and an older broker on a KIP-1170 directory | (unverified) | Read the container logs |
| U18 | Cruise Control and similar third-party rebalancers on 4.4 | (unverified) | Not official, not researched |
| U19 | Pacing of rolling restarts outside upgrades (for example one node at a time, waiting for the ISR) | (unverified) | Not researched for 4.4 |
| U20 | Formatting each controller of a static `controller.quorum.voters` quorum with `--cluster-id <ID> --config <file>` and no `--standalone` | (unverified) | The pages read show `--standalone`, `--initial-controllers` and the plain broker form only |

## Irresolvable (I1..): 0 items

No separate irresolvable class is kept. Facts that cannot be resolved from documentation are listed once above as U-ids (U1, U4, U13) with a human-verify note.

## Medium confidence (M1..M29): 29 items

| ID | Claim | Tag |
|---|---|---|
| M1 | Log directory path `/var/lib/kafka/data` is a factory choice, not an official path | (medium confidence) |
| M2 | Exact remote JMX flags are standard JDK flags. The page names only `KAFKA_JMX_OPTS` | (medium confidence) |
| M3 | `replica.fetch.max.bytes` at least `message.max.bytes` | (medium confidence) |
| M4 | Raise `num.replica.fetchers` when follower lag grows | (medium confidence) |
| M5 | Producer `linger.ms` 5 to 100 and larger `batch.size` for throughput | (medium confidence) |
| M6 | `group.protocol=consumer` when all clients support it | (medium confidence) |
| M7 | Alert when UnderReplicatedPartitions is above 0 for a sustained period | (medium confidence) |
| M8 | Normal value 0 for OfflinePartitionsCount and FencedBrokerCount | (medium confidence) |
| M9 | Support policy from the Apache wiki Time Based Release Plan, last edited 2024-07-09 | (medium confidence) |
| M10 | Disk sizing heuristic: ingress x retention x RF | (medium confidence) |
| M11 | MM2 RPO is roughly `replication-latency-ms` (inference) | (medium confidence) |
| M12 | Docker Compose is single-host, so dev, CI or staging only (inference from [S2] and Compose scope) | (medium confidence) |
| M13 | Dedicated `controller` and `broker` roles in critical environments, combined mode avoided there: one official page (KRaft [S6]) | (medium confidence) |
| M14 | Enable `StandardAuthorizer` with `super.users`, keep `allow.everyone.if.no.acl.found` at `false` and use `true` only for dev or tests: one official page (ACLs [S9]) | (medium confidence) |
| M15 | Pin the image tag `apache/kafka:4.4.0` and avoid floating tags such as `latest`: the avoid-floating advice is factory practice, not in the docs. Only the existence of tag 4.4.0 is sourced, one page [S2] | (medium confidence) |
| M16 | Odd controller quorum of 3 or 5 (2N+1 survives N failures): one versioned page (KRaft [S6]); the other source is a release-branch example file, which does not count | (medium confidence) |
| M17 | Unique `node.id` per node: upgrade notes [S1] state the `broker.id` deprecation; the broker configs page [S7] was read 200000 of 201536 characters (L1) | (medium confidence) |
| M18 | `kafka-metadata-quorum.sh describe --status` as the quorum health check: one official page (KRaft [S6]) | (medium confidence) |
| M19 | File descriptors at least 100000 (`ulimits: nofile`): one official page (hardware and OS [S16]) | (medium confidence) |
| M20 | Controller listener network-isolated and controller port not published: one official page (listener configuration [S31]); the example file is a release-branch file | (medium confidence) |
| M21 | `SASL_SSL` on SASL-authenticated listeners that leave the host, SASL/PLAIN only with TLS, with SCRAM-SHA-512 over `SASL_SSL` as the alternative: one official page (SASL [S10]) | (medium confidence) |
| M22 | `ssl.client.auth=requested` is discouraged: one official page (SSL [S11]) | (medium confidence) |
| M23 | SCRAM credentials in the KRaft metadata log suit production only where controllers are secured and private: one official page (SASL [S10]) | (medium confidence) |
| M24 | Format every KRaft node with the same cluster ID: the multi-node rule is on one official page (KRaft [S6]); the quickstart [S30] shows a one-node `format --standalone` only | (medium confidence) |
| M25 | Do not format or start a replacement controller until a majority has all committed data: one official page (Hardware and OS [S16]) | (medium confidence) |
| M26 | In Compose give each broker its own certificate: one release-branch file (examples README [S3]), not a versioned page | (medium confidence) |
| M27 | Docker 20.10.4 or later: one release-branch file (examples README [S3]), not a versioned page | (medium confidence) |
| M28 | Publish only client listener ports bound to `127.0.0.1` or the application network: derived from release-branch example files [S4][S5], not a versioned page | (medium confidence) |
| M29 | One cluster per datacenter mirrored with MM2 rather than a stretched cluster: the discouragement is on one official page (datacenters [S19]); the geo-replication page [S13] supports only the MM2 option | (medium confidence) |

## Coverage limits (L1..L6): 6 items

| ID | Limit |
|---|---|
| L1 | Broker configs page read 200000 of 201536 characters |
| L2 | Monitoring page read 100000 of 157611 characters; Connect and Streams sections unread |
| L3 | Downloads page (S33) read 100000 of 152730 characters |
| L4 | 3.9 upgrade page read 100000 of 233388 characters for this skill (the same page was read in full for `operating-kafka-v3-9`) |
| L5 | Security landing page read as navigation only |
| L6 | Every page was read through WebFetch, which returns a summarized page, not verbatim text |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md Ask First, auto-create topics | U12 |
| (medium confidence) | SKILL.md Ask First, controller placement | M12, M13 |
| (medium confidence) | SKILL.md Ask First, authorizer | M14 |
| (medium confidence) | SKILL.md Ask First, image tag | M15 |
| (medium confidence) | SKILL.md Ask First, quorum size, node identity, cluster ID, SASL mechanism (incl. SASL_SSL), client certificates, controller port, file descriptors | M16, M17, M18, M19, M20, M21, M22, M23, M24 |
| (medium confidence) | SKILL.md Ask First, multi-datacenter | M29 |
| (medium confidence) | SKILL.md Never Do, persistent volume alternative | M1 |
| (medium confidence), (unverified) | SKILL.md Ask First, static vs dynamic quorum | U4, U5 |
| (unverified) | SKILL.md Ask First, native image SASL | U1 |
| (medium confidence) | SKILL.md Version Context, support policy | M9 |
| (unverified) | SKILL.md Ask First, native SASL, quorum format, certificate reload, upgrade order | U1, U5, U7, U11 |
| (unverified) | SKILL.md Version Context, end-of-life table | U13 |
| (medium confidence) | ask-first-decisions.md | U4, U12, M6, M12, M13, M14, M15, M16, M17, M18, M19, M20, M21, M22, M23, M24, M29 |
| (unverified) | ask-first-decisions.md | U1, U5, U7, U11, U9, U19 |
| (medium confidence) | always-do-patterns.md, high-availability-dr.md, never-do-patterns.md | U3, U4, L2, M1, M2, M11, M12, M13, M14, M15, M16, M17, M18, M19, M21, M24, M25 |
| (unverified) | always-do-patterns.md | U2, U20 |
| (medium confidence), (unverified) | evaluation-scenarios.md | M12, M14, M20, U1, U4 |
| (medium confidence) | deploy-compose.md, paths, single-host scope, file descriptors, auto topic creation, Docker version | M1, M12, M19, U12, M27, M28 |
| (unverified) | deploy-compose.md, image details, native image SASL | U1, U3, U5 |
| (medium confidence) | tls-and-security.md | M2, L2, U15, M14, M19, M20, M21, M22, M23, M26, M28 |
| (unverified) | tls-and-security.md | U7, U8, U14 |
| (medium confidence) | observability.md | M2, M7, M8, M11 |
| (unverified) | observability.md | U9, U10, U16, U17 |
| (unverified) | high-availability-dr.md | U8, U9 |
| (medium confidence) | performance-tuning.md, capacity-sizing.md | M3, M4, M5, M6, M10, M12, M16, M19, U6 |
| (unverified) | performance-tuning.md, capacity-sizing.md | U3, U9, U18 |
| (unverified) | migration-guide.md | U2, U11 |
| (medium confidence) | migration-guide.md | U4, U6 |

## Source Bibliography

All pages read 2026-11-04. S8 and S21 are navigation pages and are not cited.

| ID | Title | URL |
|---|---|---|
| S1 | Upgrading, AK 4.4.X | https://kafka.apache.org/44/getting-started/upgrade/ |
| S2 | Docker, AK 4.4.X | https://kafka.apache.org/44/getting-started/docker/ |
| S3 | Docker examples README, branch 4.4 | https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/README.md |
| S4 | Compose example cluster/combined/plaintext, branch 4.4 | https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/docker-compose-files/cluster/combined/plaintext/docker-compose.yml |
| S5 | Compose example cluster/isolated/plaintext, branch 4.4 | https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/docker-compose-files/cluster/isolated/plaintext/docker-compose.yml |
| S6 | KRaft, AK 4.4.X Operations | https://kafka.apache.org/44/operations/kraft/ |
| S7 | Broker Configs, AK 4.4.X | https://kafka.apache.org/44/configuration/broker-configs/ |
| S9 | Authorization and ACLs | https://kafka.apache.org/44/security/authorization-and-acls/ |
| S10 | Authentication using SASL | https://kafka.apache.org/44/security/authentication-using-sasl/ |
| S11 | Encryption and Authentication using SSL | https://kafka.apache.org/44/security/encryption-and-authentication-using-ssl/ |
| S12 | Basic Kafka Operations | https://kafka.apache.org/44/operations/basic-kafka-operations/ |
| S13 | Geo-Replication (Cross-Cluster Data Mirroring) | https://kafka.apache.org/44/operations/geo-replication-cross-cluster-data-mirroring/ |
| S14 | Monitoring | https://kafka.apache.org/44/operations/monitoring/ |
| S15 | Design | https://kafka.apache.org/44/design/design/ |
| S16 | Hardware and OS | https://kafka.apache.org/44/operations/hardware-and-os/ |
| S17 | Java Version | https://kafka.apache.org/44/operations/java-version/ |
| S18 | Eligible Leader Replicas | https://kafka.apache.org/44/operations/eligible-leader-replicas/ |
| S19 | Datacenters | https://kafka.apache.org/44/operations/datacenters/ |
| S20 | KRaft vs ZooKeeper | https://kafka.apache.org/44/getting-started/zk2kraft/ |
| S22 | Apache Kafka 4.0.0 Release Announcement (2025-03-18) | https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/ |
| S23 | Apache Kafka 4.4.0 Release Announcement (2026-10-22) | https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/ |
| S24 | KRaft, AK 3.9.X Operations | https://kafka.apache.org/39/operations/kraft/ |
| S25 | Upgrading, AK 3.9.X (partly read) | https://kafka.apache.org/39/getting-started/upgrade/ |
| S26 | Time Based Release Plan (Apache Kafka wiki) | https://cwiki.apache.org/confluence/display/KAFKA/Time+Based+Release+Plan |
| S27 | Topic Configs | https://kafka.apache.org/44/configuration/topic-configs/ |
| S28 | Producer Configs | https://kafka.apache.org/44/configuration/producer-configs/ |
| S29 | Consumer and Share Consumer Configs | https://kafka.apache.org/44/configuration/consumer-configs/ |
| S30 | Quick Start | https://kafka.apache.org/44/getting-started/quickstart/ |
| S31 | Listener Configuration | https://kafka.apache.org/44/security/listener-configuration/ |
| S32 | Compatibility | https://kafka.apache.org/44/getting-started/compatibility/ |
| S33 | Downloads page | https://kafka.apache.org/community/downloads/ |
