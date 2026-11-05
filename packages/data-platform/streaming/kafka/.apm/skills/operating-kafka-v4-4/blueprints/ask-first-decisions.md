# Ask-first decisions, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). Ask the user before acting on any item below. Tags resolve in the [register](./unverified-and-risks.md). S-ids resolve in the [Source Bibliography](./unverified-and-risks.md#source-bibliography).

## Controller placement: combined vs dedicated

| Option | Topology | Optimizes | Sacrifices | Min nodes | Best when |
|---|---|---|---|---|---|
| Single combined | 1 node `broker,controller` | Simplicity | Any HA | 1 | Local dev; image default [S3] |
| Combined cluster | 3 nodes `broker,controller` | Fewer containers | Controller isolation | 3 | Dev and CI multi-node tests [S4][S6] |
| Dedicated (isolated) | 3 controllers + N brokers | Controller isolation | More nodes | 3 + 3 | Critical environments [S6]; official isolated example [S5] |

- Dedicated roles for critical environments, with combined mode avoided there, rest on one official page [S6] (medium confidence, M13).
- Failover is automatic while a majority of voters is alive [S6]. Losing the majority stops metadata changes.
- Docker Compose is single-host, so it gives no cross-host failover (medium confidence). A host failure takes down every container.
- Ask: "Is this environment critical (production) or dev/CI? Do you need multi-host HA at all?"

## Static vs dynamic quorum

- Static: `controller.quorum.voters`, used by the official Compose examples [S4][S5]. Deprecated as of KRaft version 1 [S6].
- Dynamic (KIP-853): `controller.quorum.bootstrap.servers` and `kraft.version >= 1`, formatted with `--standalone` or `--initial-controllers`. Lets you add and remove controllers with `kafka-metadata-quorum.sh` [S6]. The mode is chosen at format time [S6].
- Upgrading static to dynamic: the compatibility page and the KRaft page disagree (medium confidence). Human-verify before promising it to the user (register U4).
- Formatting a dynamic quorum from `apache/kafka` image environment variables is (unverified). The README documents `CLUSTER_ID` only [S3].
- Ask: "Will controllers be added or replaced without a full cluster rebuild? If yes, plan a dynamic quorum from day one."

## Cluster ID

- Generate the ID once with `kafka-storage.sh random-uuid` (Always Do). Formatting every KRaft node with that same ID rests on one official page [S6] (medium confidence, M24); the quickstart shows a one-node `format --standalone` only [S30].
- Ask: "Which cluster ID do all nodes share?"

## Authorizer

- `StandardAuthorizer` with `super.users` on every node rests on one official page [S9] (medium confidence, M14). The same page says to keep `allow.everyone.if.no.acl.found` at its default `false` in production and to use `true` only for dev, tests or phased rollouts (medium confidence, M14). With `true`, resources that have no ACLs are open to everyone.
- Alternative to `true`: keep `false` and grant specific ACLs with `kafka-acls.sh --add`.
- Ask: "Should ACL authorization be enabled on this cluster?"

## Controller quorum size

- An odd quorum of 3 or 5 (2N+1 controllers survive N failures) and checking it with `kafka-metadata-quorum.sh describe --status` rest on one official page [S6] (medium confidence, M16, M18).
- Ask: "Do you want 3 or 5 controllers?"

## Node identity

- Each node needs a unique `node.id`; `broker.id` is deprecated in 4.4 [S1]. The broker configs page [S7] was read 200000 of 201536 characters, so the claim stays below High (medium confidence, M17).
- Ask: "Which node ids are free?"

## SASL mechanism

- SASL/PLAIN must be used only with TLS so passwords are not sent in clear [S10] (medium confidence, M21). Alternative: `SASL_SSL` with SCRAM-SHA-512.
- SCRAM credentials in KRaft are stored in the metadata log; that suits production only where controllers are secured and the network is private [S10] (medium confidence, M23).
- Ask: "Which SASL mechanism do your clients support?"

## Client certificates

- `ssl.client.auth=required` for mTLS; `requested` is discouraged [S11] (medium confidence, M22).
- Ask: "Do all clients present certificates?"

## Controller port

- The controller listener must stay network-isolated from clients [S31] (medium confidence, M20). Publish only client listener ports, bound to `127.0.0.1` or the application network.
- Ask: "Which ports must leave the host?"

## File descriptors

- At least 100000 open files, `ulimits: nofile` in Compose [S16] (medium confidence, M19).
- Ask: "Can the host raise the nofile limit?"

## Image tag

- Only the existence of tag `4.4.0` is sourced [S2], one page. Avoiding floating tags such as `latest` is factory practice, not in the docs (medium confidence, M15).
- Ask: "Is pinning `apache/kafka:4.4.0` acceptable?"

## Native image

- `apache/kafka-native` is described as dev and test only [S2]. Ask before using it for anything beyond a laptop. Alternative: `apache/kafka:4.4.0`.
- SASL on the native image: the Docker page says 4.4.0 supports it, the 4.4-branch README says it does not (KAFKA-19584). Treated as (unverified), conflicting official sources. Human-verify. Default answer: use the JVM image for SASL.

## Topic auto-creation

- Default is `auto.create.topics.enable=true` [S7]. Setting it to `false` so topics get an explicit partition count and RF is factory practice, not in the docs (medium confidence).
- Ask: "Should topics be created only through explicit tooling (recommended)?"

## Certificate rotation

- Hot keystore reload without restart is not described on the 4.4 SSL page (unverified). Plan a rolling restart unless verified.
- Ask: "Is a rolling restart acceptable for certificate rotation?"

## Rolling upgrade order

- Controllers first is common practice, not stated on the 4.4 page (unverified). Between nodes check UnderReplicatedPartitions is 0 [S14].
- Ask: "Do you want controllers first, then brokers?"

## Multi-datacenter

| Option | Optimizes | Sacrifices |
|---|---|---|
| Local cluster per DC with MM2 (recommended) [S19] | Availability, latency | Asynchronous replication, RPO above 0 |
| Stretched cluster | Synchronous replication | Write latency, availability on link failure [S19] |

Ask: "Is cross-DC replication actually required, and what RPO is acceptable for asynchronous mirroring?"

## Delivery guarantee target

| Guarantee | Producer | Consumer |
|---|---|---|
| At-least-once (default) | `acks=all`, idempotence on | `enable.auto.commit=false`, commit after processing |
| Exactly-once | `transactional.id` set | `isolation.level=read_committed`, `enable.auto.commit=false` |

Source: [S15][S28][S29]. Ask: "Does any consumer write side effects outside Kafka? Exactly-once then needs application idempotency as well."

## Consumer group protocol

`group.protocol=consumer` (KIP-848, GA since 4.0) when all clients support it (medium confidence). Default is `classic` [S29]. Ask: "Do all consuming clients support the new consumer protocol?"

## Partition count

No official sizing formula was found (unverified). Ask: "What is the target throughput and consumer parallelism per topic?" See [capacity-sizing](./capacity-sizing.md).

## Share groups

Queue-like consumption, production-ready since 4.2. Dead-letter queues need `share.version` 2 (new in 4.4) [S1][S23]. With fewer than 3 brokers set `share.coordinator.state.topic.replication.factor` and `.min.isr` to 1 [S1]. Ask: "Do you need queue semantics instead of consumer groups?"
