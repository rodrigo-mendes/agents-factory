# ZooKeeper ensemble operations, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). Kafka 3.9.2 bundles ZooKeeper 3.8.4 ([dependencies.gradle at tag 3.9.2](https://raw.githubusercontent.com/apache/kafka/3.9.2/gradle/dependencies.gradle)). Operating guidance comes from the [Kafka ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/) and the [ZooKeeper 3.8.4 Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html), both read in full 2026-11-04. Items rooted in one page only are tagged (medium confidence, M10).

## Triangulated rules (two pages)

- **Odd size, at least 3** (Admin Guide alone; the Kafka page names 5 or 7 as typical; medium confidence, M19). 3 servers tolerate 1 failure, 5 or 7 are typical and tolerate 2 and 3. Avoid oversized ensembles.
- **Dedicated transaction-log device.** `dataLogDir` on its own disk. A dedicated partition is not enough.
- **Do not expose ZooKeeper.** It expects a trusted environment, and clients do not use it in 3.9: tools connect with `--bootstrap-server` ([basic operations](https://kafka.apache.org/39/operations/basic-kafka-operations/)).

## Single-page settings (medium confidence, M10)

| Setting | Default | Recommended | Source |
|---|---|---|---|
| `autopurge.purgeInterval` | 0 (off) | 1 or higher. "A ZooKeeper server will not remove old snapshots and log files when using the default configuration" | Admin Guide |
| `autopurge.snapRetainCount` | 3 (minimum 3) | 3 or higher | Admin Guide |
| `4lw.commands.whitelist` | `srvr` | `srvr`. Add `mntr` or `ruok` only if needed | Admin Guide |
| `admin.serverPort` / AdminServer | 8080, enabled | Disable (`admin.enableServer=false`) or firewall | Admin Guide, [bundled zookeeper.properties](https://raw.githubusercontent.com/apache/kafka/3.9.2/config/zookeeper.properties) |
| `reconfigEnabled` | false | Keep. Membership changes are then rolling static-config changes (procedure unverified, U24) | Admin Guide |
| `maxClientCnxns` | bundled file sets 0 "since this is a non-production config" | Set a per-IP limit in production (value unverified, U31) | bundled file |
| Heap | n/a | "Be conservative - use a maximum heap size of 3GB for a 4GB machine". Never swap | Admin Guide |

The bundled `config/zookeeper.properties` is a single-server, non-production file (`dataDir=/tmp/zookeeper`) and does not set autopurge.

## Operations notes

- **Redundancy and segregation**: spread servers across racks, with redundant power and network. Run ZooKeeper isolated unless you know the other applications' I/O patterns. Virtualization can work but adds timing risk. Prefer system packages from Apache, not OS-packaged versions ([ZooKeeper page](https://kafka.apache.org/39/operations/zookeeper/)).
- **Heap at Kafka scale**: the Kafka team ran 3 to 5 GB depending on data set size. If snapshots reach several GB, raise `initLimit`.
- **Monitoring**: JMX and four-letter commands, with the Kafka page preferring four-letter commands where they overlap. A Prometheus provider exists: `metricsProvider.className=org.apache.zookeeper.metrics.prometheus.PrometheusMetricsProvider`, endpoint on `metricsProvider.httpPort` (default 7000).
- **Upgrading the ZooKeeper binaries**: upgrades from Kafka 2.4 or later require ZooKeeper 3.8.3 or higher first, and ZooKeeper binaries from Kafka 2.4 or later "can be updated directly" ([upgrade notes](https://kafka.apache.org/39/getting-started/upgrade/), single page, M10).
- **Disk full**: with autopurge off the data directory grows without bound. The manual purge tool and procedure are (unverified, U27). Prevent it with autopurge.
- **Backup**: the state is the snapshots and transaction logs under `dataDir` and `dataLogDir`. A documented backup and restore procedure was not found (unverified, U10).

## Verification

```bash
# Representative, adapt to your environment
docker exec zk-1 bash -c 'exec 3<>/dev/tcp/127.0.0.1/2181; echo srvr >&3; cat <&3'
# Expected: one "Mode: leader", the rest "Mode: follower". The /dev/tcp trick in the image is (unverified, U12)
docker exec zk-1 du -sh /var/lib/kafka/data/zookeeper
# Expected: size stable once autopurge runs
```

Compose layout: [deploy-compose-zookeeper](./deploy-compose-zookeeper.md). Security: [zookeeper-security](./zookeeper-security.md). Failure runbooks: [high-availability-dr](./high-availability-dr.md).
