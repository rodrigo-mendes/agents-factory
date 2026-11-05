# Ask-first decisions, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). Ask the user before choosing. Tags follow the [register](./unverified-and-risks.md). All sources read 2026-11-04.

## Metadata mode: ZooKeeper, KRaft dedicated, KRaft combined

| Option | Topology | Sacrifices | Best when |
|---|---|---|---|
| ZooKeeper mode | 3 or 5 ZooKeeper servers + N brokers | Deprecated since 3.5, removed in 4.0, extra ensemble to run | Existing clusters awaiting migration ([ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/)) |
| KRaft dedicated | 3 or 5 controllers + N brokers | Controller sizing (about 5 GB RAM and disk) | New 3.9 clusters, migration target ([KRaft](https://kafka.apache.org/39/operations/kraft/)) |
| KRaft combined | 3 nodes with `broker,controller` | Isolation. "Not recommended in critical deployment environments" (medium confidence, M3) | Dev and CI |

Ask: "Is this new or existing? If new, why not KRaft or 4.x directly? If existing, when is the migration?" Failover is automatic in both modes while a majority lives ([design](https://kafka.apache.org/39/design/design/)).

## ZooKeeper-mode broker from the stock image

The `apache/kafka` image runs a storage format step at startup. The 3.9 `StorageTool` rejects configs without `process.roles`, so the default `CMD` cannot start a ZooKeeper-mode broker (medium confidence, U1, inferred from source, not run). The documented-image pages never mention ZooKeeper mode. The workaround is a `command` override ([deploy-compose-zookeeper](./deploy-compose-zookeeper.md)). Ask: "Do you accept an override that no official example shows?"

## Migration timing and finalize

- The whole procedure rests on one official page, the 3.9 KRaft page (medium confidence, M11). Treat the [runbook](./zk-to-kraft-migration.md) as that page's steps, not as a triangulated procedure.
- Finalize removes the ability to return to ZooKeeper (same page). Ask: "Which checks prove dual-write is healthy, and who approves finalize?"
- How to build a 3-controller quorum during migration is not stated (unverified, U26, human-verify). Ask which quorum layout the user wants and say the page shows a `--standalone` first controller only.
- Which patch: the page says brokers on "3.9.1"; 3.9.2 contains two migration fixes (KAFKA-19480, KAFKA-19988), but 3.9.2 meeting the text is inferred (medium confidence, U3). Recommendation: confirm it on a test cluster or ask the Apache community before relying on it (medium confidence).

## Support window and lifecycle

The 12-month critical-fix statement has no stated start date. Counted from 3.9.0 (2024-11-06) it ended 2025-11-06, yet 3.9.2 shipped 2026-02-21 (unverified, U4, human-verify). 3.9.x is archived on the downloads page (medium confidence, M2). No official end-of-life table (unverified, U15, human-verify). Ask: "Can you accept an archived line until the migration is done?"

## Static or dynamic KRaft quorum

Static uses `controller.quorum.voters`. Dynamic uses `controller.quorum.bootstrap.servers` and `kraft.version >= 1`, chosen at format time. Converting static to dynamic "is not yet supported" in 3.9 ([KRaft](https://kafka.apache.org/39/operations/kraft/)). The image wrapper formats with `--cluster-id` and `-c` only, so dynamic formatting through the image is (unverified, U5). Ask: "Will controllers be added or replaced without a rebuild?"

## ZooKeeper ensemble size

3 tolerates 1 failure, 5 tolerates 2, 7 tolerates 3. More servers add read capacity and cost write traffic ([ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/), [Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html)). Ask: "How many simultaneous failures, including maintenance, must you survive?"

## Cluster ID

Generate the ID once with `kafka-storage.sh random-uuid` (Always Do). Formatting every KRaft node with that same ID rests on one official page ([KRaft](https://kafka.apache.org/39/operations/kraft/), medium confidence, M14); the quickstart shows a one-node format only. For the migration use the existing ZooKeeper cluster ID. Ask: "Which cluster ID do all nodes share?"

## Rolling restart pacing

Restart one broker at a time (Always Do). Waiting for the ISR to rejoin before the next restart is stated by the running-cluster security page ([running cluster](https://kafka.apache.org/39/security/incorporating-security-features-in-a-running-cluster/), medium confidence, M15). Check with `kafka-topics.sh --describe --under-replicated-partitions`. Ask: "How will you confirm the ISR is back between restarts?"

## Other decisions

| Decision | Options | Ask |
|---|---|---|
| Topic auto-creation | `auto.create.topics.enable=false` appears in the production example as a value, not as a rule (medium confidence, M12). Default is `true` | "Should topics be created only through tooling?" |
| Delivery guarantee | At-least-once (defaults) vs exactly-once (`transactional.id`, `isolation.level=read_committed`) ([producer](https://kafka.apache.org/39/configuration/producer-configs/), [consumer](https://kafka.apache.org/39/configuration/consumer-configs/), [design](https://kafka.apache.org/39/design/design/)) | "Can consumers tolerate duplicates?" |
| Retention | Time (`retention.ms`, 7 days), size (`retention.bytes`, -1), compaction ([topic configs](https://kafka.apache.org/39/configuration/topic-level-configs/)) | "What is the replay window?" |
| Multi-datacenter | MM2 per DC (preferred) vs stretched (discouraged) | "What RPO is acceptable for asynchronous mirroring?" |
| KRaft rolling-upgrade order | Controllers vs brokers first is not stated on the 3.9 upgrade page (unverified, U19) | "Which node order do you want?" |
| Certificate rotation | Dynamic keystore update is not described on the 3.9 SSL page (unverified, U14). Plan a rolling restart | "Is a rolling restart acceptable?" |
| AlterConfigPolicy | `alter.config.policy.kraft.compatibility.enable=true` (KIP-1252, default `false`) when you use a policy and migrate (medium confidence, M6) | "Do you use an AlterConfigPolicy?" |
| Image tag | Pin `apache/kafka:3.9.2` rather than a floating tag. Pinning is factory practice (medium confidence, M9) | "Pin the tag?" |
| Compose host scope | Compose is single-host, so no failover across hosts. Use for dev, CI and staging (medium confidence, M5) | "Is multi-host HA needed?" |

## Single-page guidance kept out of Always Do and Never Do

Each item below rests on one official page, so it is a recommendation to confirm, tagged (medium confidence, M13) unless noted.

- **SASL/PLAIN** should be used only with TLS as transport ([SASL](https://kafka.apache.org/39/security/authentication-using-sasl/)). Prefer SCRAM-SHA-512 over SASL_SSL.
- **SCRAM credentials stored in ZooKeeper** suit production only where ZooKeeper is secure and on a private network ([SASL](https://kafka.apache.org/39/security/authentication-using-sasl/), medium confidence, M4).
- **Default OAUTHBEARER** (unsecured JWT) is only suitable for non-production ([SASL](https://kafka.apache.org/39/security/authentication-using-sasl/)). Production needs custom callback handlers.
- **`ssl.client.auth=requested`** "provides a false sense of security" ([SSL](https://kafka.apache.org/39/security/encryption-and-authentication-using-ssl/)). Use `required` for mTLS.
- **Authorizer class**: `kafka.security.authorizer.AclAuthorizer` in ZooKeeper mode, `org.apache.kafka.metadata.authorizer.StandardAuthorizer` in KRaft, plus `super.users`. With no matching ACL only super users get access. Default of `allow.everyone.if.no.acl.found` is not shown (unverified, U8) ([ACLs](https://kafka.apache.org/39/security/authorization-and-acls/)).
- **Securing ZooKeeper in the wrong order** can leave inconsistent znode ACLs: follow the 5-step order in [zookeeper-security](./zookeeper-security.md) ([ZooKeeper auth](https://kafka.apache.org/39/security/zookeeper-authentication/)).
- **Finalizing a migration before validation** is irreversible ([KRaft](https://kafka.apache.org/39/operations/kraft/), M11). Validate topics, ACLs, offsets and client traffic in dual-write first.
- **ZooKeeper autopurge, heap and AdminServer**: single-page settings in [zookeeper-ensemble](./zookeeper-ensemble.md) (medium confidence, M10).
- **Remote JMX** has authentication off by default ([monitoring](https://kafka.apache.org/39/operations/monitoring/)); the image launch script also defaults it off. Do not publish it. Secure flag set: (medium confidence, U23).
- **Image default `CLUSTER_ID`**: unset means the image uses a hard-coded ID, read from branch-head scripts (medium confidence, U13). Always set your own.
