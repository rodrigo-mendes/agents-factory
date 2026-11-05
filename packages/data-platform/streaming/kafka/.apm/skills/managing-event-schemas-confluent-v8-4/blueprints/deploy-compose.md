# Deploy with Docker Compose, Confluent Schema Registry 8.4.0

Back to [SKILL.md](../SKILL.md). Both Compose files below are this skill's assembly and are (unverified) as tested wholes (U14): nobody ran them. Individual lines trace to official pages. Kubernetes deployment is out of scope: use `operating-kafka-confluent-kubernetes-v3-4`.

## Environment variable naming rule

Docker image variables use the prefix `SCHEMA_REGISTRY_`, uppercase, `.` becomes `_`, `_` becomes `__`, `-` becomes `___`. Source: [Docker config reference](https://docs.confluent.io/platform/8.4/installation/docker/config-reference.html). Whether this yields a working variable for `schema.registry.group.id` is (unverified), U4.

## 1. Local development stack (single broker, KRaft combined mode)

The Schema Registry block and the broker KRaft keys are quoted from the official [cp-all-in-one community Compose, branch 8.4.0-post](https://github.com/confluentinc/cp-all-in-one/blob/8.4.0-post/cp-all-in-one-community/docker-compose.yml). The file is trimmed: the official file sets more `KAFKA_*` keys (for example replication factors) that were not captured. (unverified) as a whole.

```yaml
services:
  broker:
    image: confluentinc/cp-kafka:8.4.0
    hostname: broker
    container_name: broker
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: 'broker,controller'
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@broker:29093'
      KAFKA_LISTENERS: 'PLAINTEXT://broker:29092,CONTROLLER://broker:29093,PLAINTEXT_HOST://0.0.0.0:9092'
      KAFKA_ADVERTISED_LISTENERS: 'PLAINTEXT://broker:29092,PLAINTEXT_HOST://localhost:9092'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: 'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT'
      KAFKA_CONTROLLER_LISTENER_NAMES: 'CONTROLLER'
      KAFKA_INTER_BROKER_LISTENER_NAME: 'PLAINTEXT'
      KAFKA_LOG_DIRS: '/tmp/kraft-combined-logs'
      CLUSTER_ID: 'MkU3OEVBNTcwNTJENDM2Qk'

  schema-registry:
    image: confluentinc/cp-schema-registry:8.4.0
    hostname: schema-registry
    container_name: schema-registry
    depends_on:
      - broker
    ports:
      - "8081:8081"
    environment:
      SCHEMA_REGISTRY_HOST_NAME: schema-registry
      SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: 'broker:29092'
      SCHEMA_REGISTRY_LISTENERS: http://0.0.0.0:8081
```

With one broker, `_schemas` gets replication factor 1 because the effective RF is the lesser of the setting and the live broker count. Development only.

Verification (representative):

```bash
docker compose up -d
curl -s http://localhost:8081/subjects      # Expected: [] on a fresh registry
kafka-topics --bootstrap-server localhost:9092 --describe --topic _schemas
# Expected: PartitionCount: 1, cleanup.policy=compact
```

The official Compose confirms KRaft combined mode (no ZooKeeper service). Whether Schema Registry runs against ZooKeeper-mode brokers is moot: it has used Kafka-based election only since 7.0.0.

## 2. Hardened node (HTTPS, Basic auth, SASL_SSL to Kafka)

Variable names come from the naming rule applied to property names in the [config reference](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html) and the [security page](https://docs.confluent.io/platform/8.4/schema-registry/security/index.html). (unverified) as a whole, U14. That the image accepts `SCHEMA_REGISTRY_OPTS` for the JAAS file is (unverified), U5: the security page documents it for `schema-registry-start`. The `kafkastore` SASL JAAS config key was not captured (unverified), U6, so SASL credentials are not wired here.

```yaml
  schema-registry-1:
    image: confluentinc/cp-schema-registry:8.4.0
    environment:
      SCHEMA_REGISTRY_HOST_NAME: schema-registry-1
      SCHEMA_REGISTRY_LISTENERS: https://0.0.0.0:8081
      SCHEMA_REGISTRY_SSL_KEYSTORE_LOCATION: /etc/schema-registry/secrets/sr.keystore.jks
      SCHEMA_REGISTRY_SSL_KEYSTORE_PASSWORD: ${SR_KEYSTORE_PASSWORD}
      SCHEMA_REGISTRY_SSL_KEY_PASSWORD: ${SR_KEY_PASSWORD}
      SCHEMA_REGISTRY_INTER_INSTANCE_PROTOCOL: https
      SCHEMA_REGISTRY_AUTHENTICATION_METHOD: BASIC
      SCHEMA_REGISTRY_AUTHENTICATION_ROLES: admin,developer,user
      SCHEMA_REGISTRY_AUTHENTICATION_REALM: SchemaRegistry-Props
      SCHEMA_REGISTRY_OPTS: -Djava.security.auth.login.config=/etc/schema-registry/jaas_config.conf
      SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: SASL_SSL://broker-1:9093,SASL_SSL://broker-2:9093,SASL_SSL://broker-3:9093
      SCHEMA_REGISTRY_KAFKASTORE_SECURITY_PROTOCOL: SASL_SSL
      SCHEMA_REGISTRY_KAFKASTORE_SASL_MECHANISM: SCRAM-SHA-512
      SCHEMA_REGISTRY_KAFKASTORE_SSL_TRUSTSTORE_LOCATION: /etc/schema-registry/secrets/kafka.truststore.jks
      SCHEMA_REGISTRY_KAFKASTORE_SSL_TRUSTSTORE_PASSWORD: ${KAFKA_TRUSTSTORE_PASSWORD}
      SCHEMA_REGISTRY_SCHEMA_COMPATIBILITY_LEVEL: backward_transitive
      SCHEMA_REGISTRY_SCHEMA_REGISTRY_GROUP_ID: schema-registry-prod
```

Defaults for context (config reference): `kafkastore.security.protocol` is `PLAINTEXT`, `kafkastore.sasl.mechanism` is `GSSAPI`, `ssl.client.authentication` is `NONE`.

JAAS file shape (security page):

```
SchemaRegistry-Props {
  org.eclipse.jetty.security.jaas.spi.PropertyFileLoginModule required
  file="/etc/schema-registry/password-file"
  debug="false";
};
```

Basic auth without HTTPS sends credentials in plain text (medium confidence, M3). Keep passwords in secrets, never in the file.

## Health check

No official health-check endpoint was found for 8.4.0 (unverified, I1). Community Compose files probe `GET /subjects`; that is not official and is not used as evidence. With authentication on, such a probe needs credentials.

## Pin the image

Use `confluentinc/cp-schema-registry:8.4.0`, not `latest` (medium confidence, M10). The license of the `cp-schema-registry` image is not documented on the pages read (unverified, I2).
