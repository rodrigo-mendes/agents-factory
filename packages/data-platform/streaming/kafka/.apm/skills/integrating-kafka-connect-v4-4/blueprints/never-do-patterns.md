# Never-do patterns, Kafka Connect 4.4.0

Back to [SKILL.md](../SKILL.md). Representative code; adapt to your environment. Each row below has two official 4.4 pages behind it. Single-page rules are in [ask-first-decisions](./ask-first-decisions.md). All pages read 2026-11-04.

## 1. Logging record contents

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/). `errors.log.include.messages=true` also logs key, value and headers and may expose sensitive data. Default is `false`. Impact: PII or secrets in worker logs.

```json
{ "errors.log.enable": "true", "errors.log.include.messages": "true" }
```

Instead:

```json
{ "errors.log.enable": "true", "errors.log.include.messages": "false",
  "errors.deadletterqueue.topic.name": "dlq.orders-sink" }
```

## 2. Inline secrets

Sources: [security model](https://kafka.apache.org/44/security/security-model-connect/), [configuration providers](https://kafka.apache.org/44/configuration/configuration-providers/). The secret is stored in the config topic as an ordinary record. Impact: anyone who reads that topic or calls REST sees the credential.

```json
{ "database.password": "S3cr3t!" }
```

Instead:

```json
{ "database.password": "${file:/mnt/secrets/db.properties:dbPassword}" }
```

## 3. REST open to untrusted networks without authentication

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [security model](https://kafka.apache.org/44/security/security-model-connect/). The REST API is unauthenticated by default and grants whatever installed plugins can do. Impact: anyone who reaches the port creates connectors, which runs plugin code and reads or writes data with the worker principal.

```properties
listeners=http://0.0.0.0:8083
```

Instead: keep the listener on a trusted network and use HTTPS. Authentication in front of REST is an Ask First option (REST authentication).

```properties
listeners=https://10.0.10.5:8443
```

## 4. Class-loading client overrides for untrusted REST users

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [security model](https://kafka.apache.org/44/security/security-model-connect/). Overrides such as `sasl.jaas.config` and `sasl.login.class` can execute code. Impact: remote code execution in the worker JVM.

```properties
connector.client.config.override.policy=All
```

Instead:

```properties
connector.client.config.override.policy=Allowlist
connector.client.config.override.allowlist=consumer.override.max.poll.records   # key format (unverified, U5)
```

## 5. Deprecated Principal policy

Sources: [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/). Deprecated in 4.2.0, removed in 5.0.0. Impact: breaks on upgrade to 5.0.

```properties
connector.client.config.override.policy=Principal
```

Instead:

```properties
connector.client.config.override.policy=Allowlist
connector.client.config.override.allowlist=consumer.override.sasl.jaas.config   # key format (unverified, U5)
```

Allow `sasl.jaas.config` only when just trusted users reach REST (rule 4). The allowlist value format is (unverified, U5).

## 6. Sample file replication factor 1

Sources: [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/), [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/). Supporting reference, branch head, not a counted page: the [sample worker file](https://raw.githubusercontent.com/apache/kafka/4.4/config/connect-distributed.properties) uses 1 so it runs on one broker. Impact: losing one broker loses connector configs, offsets or status.

```properties
offset.storage.replication.factor=1
config.storage.replication.factor=1
status.storage.replication.factor=1
```

Instead: replicate all three topics. The factor 3 below is the configs-page default and is an Ask First item (medium confidence, M15):

```properties
offset.storage.replication.factor=3
config.storage.replication.factor=3
status.storage.replication.factor=3
```

## 7. Changing offsets of a running connector

Sources: [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [administration](https://kafka.apache.org/44/kafka-connect/administration/). `DELETE` and `PATCH` on `/connectors/{name}/offsets` need the connector stopped. Impact: the request is rejected; the exact HTTP status is (unverified).

```bash
curl -X DELETE http://localhost:8083/connectors/orders-src/offsets   # connector RUNNING
```

Instead, stop first (restarting afterwards is in [observability](./observability.md)):

```bash
curl -X PUT    http://localhost:8083/connectors/orders-src/stop
curl -X DELETE http://localhost:8083/connectors/orders-src/offsets
```

## 8. bootstrap.resolve.timeout.ms on Connect 4.4

Sources: [upgrade notes](https://kafka.apache.org/44/getting-started/upgrade/), [4.4.0 announcement](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/). Connect does not support KIP-909 asynchronous bootstrap. The value is forced to 0 and positive values are ignored with a warning.

```properties
bootstrap.resolve.timeout.ms=30000
```

Instead:

```properties
# leave bootstrap.resolve.timeout.ms unset for Connect 4.4.0
bootstrap.servers=kafka-1:9092,kafka-2:9092,kafka-3:9092
```

Listing several bootstrap servers is common practice, not a rule from these pages (unverified).
