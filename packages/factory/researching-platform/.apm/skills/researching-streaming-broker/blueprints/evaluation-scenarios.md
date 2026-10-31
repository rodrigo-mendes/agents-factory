# Evaluation Scenarios — researching-streaming-broker

Cross-vendor coverage required: at least one Kafka scenario AND at least one non-Kafka scenario (RabbitMQ or Pulsar). This confirms the sibling is not biased toward Kafka.

---

## Scenario 1 — Kafka on Kubernetes (Strimzi)

**Input**:
```
/researching-streaming-broker Kafka 3.7 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Output cites the Strimzi operator (CNCF) as the official K8s operator for Kafka
- Includes KRaft mode configuration (Kafka 3.7 defaults to KRaft; ZooKeeper is deprecated for new deployments)
- Documents `min.insync.replicas` with the recommendation `replication.factor - 1` for RF=3
- Provides at least one Kafka-specific KPI with its exact JMX/Prometheus metric name (e.g., `kafka_consumer_group_lag`, `kafka_server_replicafetchermanager_minfetchrate`)
- References `blueprints/references/kafka-<version>.md` for pinned config values
- Includes the `## Kubernetes Deployment Blueprint` section (triggered by `deployment=kubernetes-operator`)

**must_not**:
- Recommend ZooKeeper as the default metadata store for Kafka 3.7 (KRaft is default)
- Include RabbitMQ terminology (queue, mirror, exchange) as Kafka concepts
- Reference `blueprints/references/rabbitmq-*.md` in a Kafka-only research

---

## Scenario 2 — RabbitMQ on VM (baseline)

**Input**:
```
/researching-streaming-broker RabbitMQ 3.13 deployment=vm depth=standard
```

**must_pass**:
- Uses RabbitMQ terminology: queue, exchange, binding, vhost, consumer, publisher (NOT partition, ISR, broker in the Kafka sense)
- Recommends Quorum Queues (Raft-based) for HA over the legacy Mirrored Queues (deprecated in 3.9+)
- Documents `prefetch-count` as the consumer flow control mechanism (equivalent to Kafka's max.poll.records)
- Includes RabbitMQ-specific KPIs: `rabbitmq_queue_messages_unacknowledged`, `rabbitmq_node_mem_alarm`, `rabbitmq_node_disk_free_alarm`
- Documents Management Plugin and Prometheus Plugin as the observability stack
- References `blueprints/references/rabbitmq-<version>.md`

**must_not**:
- Recommend Mirrored Queues (deprecated) for new production deployments in 3.13
- Use `min.insync.replicas` (Kafka term) as a RabbitMQ setting
- Reference Strimzi (Kafka operator) as RabbitMQ's K8s operator

---

## Scenario 3 — Apache Pulsar on Kubernetes

**Input**:
```
/researching-streaming-broker Apache Pulsar 3.2 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Uses Pulsar terminology: topic, subscription, ledger, bookie, broker (Pulsar-broker), tenant, namespace
- Documents the separation of compute (Pulsar brokers) from storage (BookKeeper bookies) — the key architectural differentiator
- Recommends the StreamNative Pulsar Operator or the Apache Pulsar Helm chart
- Documents subscription types (Exclusive, Shared, Failover, Key_Shared) and when to use each
- Includes Pulsar KPIs: `pulsar_subscription_back_log`, `pulsar_topics_count`, `bookkeeper_journal_add_entry_ms`
- References `blueprints/references/pulsar-<version>.md`

**must_not**:
- Describe Pulsar as "Kafka-compatible" without also noting the architectural differences (bookie separation)
- Recommend a single-node deployment for production
- Use Kafka-style consumer group semantics (Pulsar uses subscriptions with named types)

---

## Scenario 4 — Misuse: Client Library Research

**Input**:
```
/researching-streaming-broker kafka-python 2.0
```

**must_pass**:
- Detects that `kafka-python` is a client library, not a broker
- Redirects to `researching-technical-frameworks` for client SDK research
- Does NOT generate broker research for a library

---

## Scenario 5 — Delivery Guarantee Requirement

**Input**:
```
/researching-streaming-broker Kafka 3.7 (workload: financial transactions, exactly-once required)
```

**must_pass**:
- Configures producer with `enable.idempotence=true` AND `transactional.id`
- Configures consumer with `isolation.level=read_committed`
- Uses `sendOffsetsToTransaction()` pattern for atomic produce + offset commit
- Documents that exactly-once is limited to Kafka-to-Kafka pipelines (not Kafka-to-external-system without additional coordination)

**must_not**:
- Recommend `acks=all` alone as sufficient for exactly-once (it only ensures durability, not deduplication)
- Suggest that at-least-once + application-level dedup is equivalent to broker-supported exactly-once without noting the trade-offs
