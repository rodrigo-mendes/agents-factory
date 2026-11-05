# Deploy a Connect worker with Docker Compose, Kafka Connect 4.4.0

Back to [SKILL.md](../SKILL.md). Representative code; adapt to your environment. The Compose file and the container entrypoint are inferred (unverified, register U1). The 4.4 docs and the 4.4 Docker examples README ([Docker page](https://kafka.apache.org/44/getting-started/docker/), [examples README](https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/README.md)) contain no Connect Compose example and no Connect usage of the image. A wrong path fails visibly at container start. A human must verify before use.

## What is and is not known

- Tag `apache/kafka:4.4.0` exists ([Docker page](https://kafka.apache.org/44/getting-started/docker/)).
- The Docker page says `apache/kafka-native` is "not recommended for production use" ([Docker page](https://kafka.apache.org/44/getting-started/docker/)). Whether it contains the Connect scripts is (unverified).
- The `/opt/kafka` path appears only in a troubleshooting note of the examples README. Using it for the Connect scripts is (unverified).
- The image maps `KAFKA_*` environment variables to broker properties. Do not rely on that mapping for Connect (unverified).
- Check the path before use (visible failure if wrong):

```bash
docker run --rm --entrypoint ls apache/kafka:4.4.0 /opt/kafka/bin
# Expected: connect-distributed.sh among the scripts (unverified)
```

## Worker file

Keys come from the [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/) and [sample worker file](https://raw.githubusercontent.com/apache/kafka/4.4/config/connect-distributed.properties). Values are choices.

```properties
# Kafka Connect 4.4.0 distributed worker. Representative, adapt to your environment
bootstrap.servers=kafka-1:9093,kafka-2:9093,kafka-3:9093
group.id=connect-cluster-orders
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=true
value.converter.schemas.enable=true

config.storage.topic=connect-orders-configs
offset.storage.topic=connect-orders-offsets
status.storage.topic=connect-orders-status
config.storage.replication.factor=3
offset.storage.replication.factor=3
status.storage.replication.factor=3
internal.topics.automatic.creation.enable=false

listeners=http://0.0.0.0:8083
rest.advertised.host.name=connect-1
plugin.path=/opt/connect-plugins
plugin.discovery=hybrid_warn

connector.client.config.override.policy=Allowlist
connector.client.config.override.allowlist=consumer.override.max.poll.records   # key format (unverified, U5)

config.providers=file
config.providers.file.class=org.apache.kafka.common.config.provider.FileConfigProvider
config.providers.file.param.allowed.paths=/mnt/secrets   # (medium confidence, M11)
```

The plain-HTTP `listeners` line is an exception to the Always Do rule "Use an HTTPS REST listener": it suits only a trusted network behind a TLS proxy (unverified, inferred for a Compose dev or CI setup). Otherwise use an HTTPS listener (see [security](./security.md)). The allowlist value format is (unverified, U5). On a secured cluster repeat the client security settings with `producer.` and `consumer.` prefixes (medium confidence); `security.protocol` defaults to `PLAINTEXT`. Create the internal topics before the first start ([always-do-patterns](./always-do-patterns.md)).

## Compose file (unverified)

```yaml
# Representative. Kafka Connect 4.4.0. Entrypoint and paths are inferred (unverified).
services:
  connect-1:
    image: apache/kafka:4.4.0
    hostname: connect-1
    entrypoint: ["/opt/kafka/bin/connect-distributed.sh"]
    command: ["/mnt/connect/connect-distributed.properties"]
    ports:
      - "127.0.0.1:8083:8083"          # host-local only; remote access through an authenticating TLS proxy
    volumes:
      - ./connect-distributed.properties:/mnt/connect/connect-distributed.properties:ro
      - ./plugins:/opt/connect-plugins:ro   # one child directory per plugin
      - ./secrets:/mnt/secrets:ro            # read by FileConfigProvider
    restart: unless-stopped
```

Binding the published port to `127.0.0.1` is an inferred hardening step (unverified). For a multi-worker cluster, give every worker the same `group.id` and topics and its own `rest.advertised.host.name` (unverified, U20).

## First connector

FileStreamSink ships in `libs/connect-file-4.4.0.jar` ([quick start](https://kafka.apache.org/44/getting-started/quickstart/)). The alias `FileStreamSink` is accepted by `connector.class` ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/)). The `file` key is (unverified).

```bash
curl -s -X POST -H 'Content-Type: application/json' http://localhost:8083/connectors -d '{
  "name": "orders-file-sink",
  "config": {
    "connector.class": "FileStreamSink",
    "tasks.max": "1",
    "topics": "orders",
    "file": "/tmp/orders.out",
    "errors.tolerance": "all",
    "errors.deadletterqueue.topic.name": "dlq.orders-file-sink",
    "errors.deadletterqueue.context.headers.enable": "true"
  },
  "initial_state": "RUNNING"
}'
```

`initial_state` takes `STOPPED`, `PAUSED` or `RUNNING`, default `RUNNING` ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/)). Check status and operate in [observability](./observability.md). Whether deleting a connector removes its stored offsets is (unverified).
