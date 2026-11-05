# Always-do patterns, Kafka Connect 4.4.0

Back to [SKILL.md](../SKILL.md). All code is representative: adapt names, hosts and paths to your environment. Caveats and options live in [ask-first-decisions](./ask-first-decisions.md). All pages read 2026-11-04.

## Distributed mode for fault tolerance

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [overview](https://kafka.apache.org/44/kafka-connect/overview/). Standalone mode does all work in one process and lacks fault tolerance.

```bash
bin/connect-distributed.sh config/connect-distributed.properties
```

## Internal topics exist before workers start

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/) for replication. Who creates them (IaC or the 4.4 auto-creation setting) is an Ask First item. All three topics are replicated. Auto-created topics get the broker default partitions and replication factor. Partitions, compaction, replication factor, `group.id` and plugin layout are Ask First items with code: [ask-first-decisions](./ask-first-decisions.md).

The 4.4.0 tool `connect-internal-topics.sh` creates them from the worker file (KIP-1209). The docs name the tool without syntax, so this syntax comes from the KIP page only (medium confidence):

```bash
bin/connect-internal-topics.sh create --worker-config config/connect-distributed.properties
```

## REST on trusted networks only

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [security model](https://kafka.apache.org/44/security/security-model-connect/). By default anyone who reaches the API can start and stop connectors. Whoever has REST access is as powerful as a cluster administrator. Details: [security](./security.md).

```properties
# bind to a management interface, not 0.0.0.0, unless a proxy fronts it
listeners=https://10.0.10.5:8443
```

## HTTPS REST listener

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [security model](https://kafka.apache.org/44/security/security-model-connect/). By default the listener reuses the worker `ssl.*` settings. With the `listeners.https.` prefix, only the prefixed options are used.

```properties
listeners=https://0.0.0.0:8443
listeners.https.ssl.keystore.location=/mnt/secrets/rest.keystore.p12
listeners.https.ssl.keystore.password=${file:/mnt/secrets/rest.properties:keystorePassword}
```

Whether a ConfigProvider reference resolves inside worker-level `listeners.https.*` settings is (unverified).

## Allowlist override policy

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [security model](https://kafka.apache.org/44/security/security-model-connect/), [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/). The 4.4 default is `All`. `Allowlist` becomes the default in 5.0.0. Allowed keys go in `connector.client.config.override.allowlist`.

```properties
connector.client.config.override.policy=Allowlist
connector.client.config.override.allowlist=consumer.override.max.poll.records,producer.override.linger.ms   # key format (unverified, U5)
```

The value format of the allowlist (full prefixed key or bare key) is (unverified, U5).

## Secrets through a ConfigProvider

Sources: [configuration providers](https://kafka.apache.org/44/configuration/configuration-providers/), [security model](https://kafka.apache.org/44/security/security-model-connect/). An inlined secret is stored in the config topic as an ordinary record.

```properties
# worker file
config.providers=file
config.providers.file.class=org.apache.kafka.common.config.provider.FileConfigProvider
```

```json
{ "database.password": "${file:/mnt/secrets/db.properties:dbPassword}" }
```

Anyone who can call REST and knows a valid template can usually read the resolved value, so this does not replace trusted-network REST. Restricting file paths with `allowed.paths` is described on one page only (medium confidence); see [security](./security.md).

## Test discovery modes before service_load

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/). `plugin.discovery` defaults to `hybrid_warn`. `service_load` is the fastest, but a plugin with no ServiceLoader manifest may not load. Check WARN logs under `hybrid_warn`, or run `hybrid_fail` in a test environment. `connect-plugin-path.sh list` and `sync-manifests --dry-run` inspect and fix manifests; the guide warns that syncing changes artifacts and does not suit code-signed environments.

```bash
bin/connect-plugin-path.sh list --worker-config config/connect-distributed.properties
```

## Java 17 or later

Sources: [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [Java version](https://kafka.apache.org/44/operations/java-version/), [quick start](https://kafka.apache.org/44/getting-started/quickstart/). Brokers, Connect and tools need Java 17 since 4.0.0. Java 17, 21 and 25 are fully supported in 4.4.

```bash
java -version
# Expected: major version 17, 21 or 25
```
