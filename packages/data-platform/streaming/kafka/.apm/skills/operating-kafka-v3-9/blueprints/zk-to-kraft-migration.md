# ZooKeeper to KRaft migration, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). Every step comes from the "ZooKeeper to KRaft Migration" section of the [3.9 KRaft page](https://kafka.apache.org/39/operations/kraft/) (read in full 2026-11-04, last modified 2026-10-23). The procedure rests on that one page (medium confidence, M11). Compose mechanics are inferred (unverified, U29). Last bridge release: 3.9 ([4.4 KRaft page](https://kafka.apache.org/44/operations/kraft/)). After migration, continue with `operating-kafka-v4-4`.

## Phases

Initial (ZooKeeper brokers + ZooKeeper controller) -> initial metadata load -> hybrid (mixed brokers, KRaft controller) -> dual-write (all brokers KRaft, controller still writes to ZooKeeper) -> finalized. Dual-write is not active-active: the KRaft controller is authoritative. Rollback is possible until finalization; once finalized you cannot return to ZooKeeper mode.

## Prerequisites

1. All brokers on 3.9.x. The page says "upgraded to software version 3.9.1". Use 3.9.2, which carries the fixes KAFKA-19480 and KAFKA-19988 (release notes). That 3.9.2 meets the 3.9.1 text is inferred (medium confidence, U3).
2. `inter.broker.protocol.version=3.9` on all brokers.
3. Do not change `metadata.version` during the migration.
4. Repair broken log directories first. A ZooKeeper broker with several log dirs shuts down on any directory failure (KAFKA-16431).
5. Features not fully implemented in KRaft block the migration. In 3.9 these are partial JBOD (KAFKA-16061) and some dynamic configs on a standalone controller.
6. With an AlterConfigPolicy, consider `alter.config.policy.kraft.compatibility.enable=true` (KIP-1252) (medium confidence, M6).
7. If the ZooKeeper Security Migration Tool ran earlier, the migration can stall (KAFKA-19480). Workaround: delete the `/migration` znode. 3.9.2 fixes the null-value hang.
8. Monitoring: TRACE for `org.apache.kafka.metadata.migration` on controllers, DEBUG on controllers and ZooKeeper brokers. Watch `ZkMigrationState`, `MigratingZkBrokerCount`, `ZkWriteBehindLag` ([observability](./observability.md)).

## Step 1: retrieve the cluster ID

From ZooKeeper `/cluster/id` or a broker's `meta.properties`. Handling of IDs with a leading dash (KAFKA-19988 doc fix) is (unverified, U25).

```bash
docker exec zk-1 /opt/kafka/bin/zookeeper-shell.sh localhost:2181 get /cluster/id
```

## Step 2: provision migration-enabled controllers

Each controller sets `process.roles=controller`, a `node.id` that collides with no broker id, `controller.quorum.bootstrap.servers`, `controller.listener.names`, `zookeeper.metadata.migration.enable=true`, `zookeeper.connect`, `inter.broker.listener.name`. Format with `--standalone` using the existing cluster ID, then start. To add controllers to the dynamic quorum use `--no-initial-controllers` and `kafka-metadata-quorum.sh add-controller`. Whether to build 3 controllers before or after the metadata load is not stated (unverified, U26, human-verify).

```properties
process.roles=controller
node.id=3000
controller.quorum.bootstrap.servers=controller-1:9093
controller.listener.names=CONTROLLER
listeners=CONTROLLER://:9093
listener.security.protocol.map=CONTROLLER:PLAINTEXT,INTERNAL:PLAINTEXT
inter.broker.listener.name=INTERNAL
zookeeper.metadata.migration.enable=true
zookeeper.connect=zk-1:2181,zk-2:2181,zk-3:2181
```

```yaml
# Representative, adapt to your environment. Compose mechanics are (unverified, U29)
controller-1:
  image: apache/kafka:3.9.2
  command: ["bash", "-c", "/opt/kafka/bin/kafka-storage.sh format --standalone -t \"$$ZK_CLUSTER_ID\" -c /mnt/ctl/controller.properties --ignore-formatted && exec /opt/kafka/bin/kafka-server-start.sh /mnt/ctl/controller.properties"]
  environment: { ZK_CLUSTER_ID: "<value from /cluster/id>" }
  volumes: ["controller-1-data:/var/lib/kafka/data", "./config/controller-1.properties:/mnt/ctl/controller.properties:ro"]
```

`controller.properties` also needs `log.dirs` or `metadata.log.dir` on the volume. The command override is explained in [deploy-compose-zookeeper](./deploy-compose-zookeeper.md#why-the-command-is-overridden).

## Step 3: enable migration on the ZooKeeper brokers

On every broker set: `broker.id` (non-negative, at most `reserved.broker.max.id`), `controller.quorum.bootstrap.servers`, `controller.listener.names`, the controller listener in `listener.security.protocol.map`, `zookeeper.metadata.migration.enable=true`, `inter.broker.protocol.version=3.9`. Rolling-restart. Migration starts once the last ZooKeeper broker restarts, and the active controller logs "Completed migration of metadata from Zookeeper to KRaft" at INFO. The cluster is now in dual-write.

## Step 4: move brokers to KRaft

Per broker: replace `broker.id` with `node.id` (same value), add `process.roles=broker`, remove `zookeeper.connect` and other ZooKeeper settings, remove `control.plane.listener.name` if set, do not set the IBP, and switch `AclAuthorizer` to `org.apache.kafka.metadata.authorizer.StandardAuthorizer`. Rolling-restart.

## Step 5: finalize (irreversible)

Remove `zookeeper.metadata.migration.enable` and the ZooKeeper client settings from each controller, restart them one at a time. Then ZooKeeper can be decommissioned and reverting is no longer possible. Run in dual-write with all brokers on KRaft and validate topics, ACLs, consumer offsets and client traffic before this step (single page, medium confidence, M11).

## Rollback by last completed step

| Last completed step | Revert actions |
|---|---|
| Preparing | Nothing to undo |
| Provisioned controller quorum | Deprovision the quorum |
| Brokers in migration mode | 1. Deprovision the quorum. 2. With `zookeeper-shell.sh`, compare `/controller_epoch` with `kraft_controller_epoch` in `/migration`; raise `/controller_epoch` above it if needed (KAFKA-20488). 3. `delete /controller`. 4. Get and delete `/migration`. Do 2-4 quickly after deprovisioning. 5. On brokers, remove the migration, controller-listener and bootstrap settings, change `node.id` back to `broker.id`, rolling-restart |
| Brokers moved to KRaft | 1. On brokers restore `broker.id` and `zookeeper.connect`, remove `process.roles`, roll, keeping `zookeeper.metadata.migration.enable=true`. 2. Deprovision the quorum. 3. Same epoch, `/controller` and `/migration` steps. 4. Remove migration settings and roll again |
| Finalized | Not possible |

## Stalls

A migration that does not start shows no "Completed migration" log line, `ZkMigrationState` stuck at PRE_MIGRATION (2) and `MigratingZkBrokerCount` below the broker count. Check that every broker restarted with the migration settings, then check for a stale `/migration` znode.

## Getting to 3.9.2 first

Single page: [upgrade notes](https://kafka.apache.org/39/getting-started/upgrade/) (section titled "Upgrading to 3.9.1"; steps treated as valid for 3.9.2, medium confidence, U3).

| From | To 3.9.2 | Notes |
|---|---|---|
| 0.8.x to 3.8.x, ZooKeeper mode | Rolling | Pin IBP to the current version, roll binaries, set IBP 3.9, roll again. No downgrade after the IBP bump. Do not start reassignments during the upgrade |
| 3.x, KRaft | Rolling | Roll nodes, then `bin/kafka-features.sh --bootstrap-server kafka-1:19092 upgrade --metadata 3.9`. Order of controllers and brokers: (unverified, U19) |
| 3.9.x ZooKeeper | 4.x | Not possible. Migrate first |
| 3.9.x KRaft | 4.4.0 | See `operating-kafka-v4-4` |

Rollback trigger: errors before the IBP bump or the metadata bump; downgrade is possible only before those steps.
