# Security and internal topics, Kafka Streams 4.4.0

Back to [SKILL.md](../SKILL.md). All pages read 2026-11-04. Broker-side TLS, SASL and ACL setup belongs to `operating-kafka-v4-4`.

## Authentication

Sources: [security](https://kafka.apache.org/44/streams/developer-guide/security/), [security model](https://kafka.apache.org/44/security/security-model-streams/).

- The app authenticates as one principal, with the same `ssl.*` and `sasl.*` client configs as producers and consumers.
- Streams is a client library, not a service.

```properties
# Representative. Adapt to your environment
security.protocol=SASL_SSL
ssl.truststore.location=/etc/streams/truststore.jks
```

## ACLs

Source: [security](https://kafka.apache.org/44/streams/developer-guide/security/).

- Grant prefixed ACLs on the `application.id`, which prefixes internal topics and the consumer group.
- Under the streams protocol the ACL table lists `STREAMS_GROUP_HEARTBEAT` (Group Read, Topic Describe, and Cluster or Topic Create when auto-creating internal topics) and `STREAMS_GROUP_DESCRIBE`.
- To avoid granting Create, pre-create internal topics with the right partition count and cleanup policy.
- ACLs on EOS transactional IDs are not on these pages (unverified, U5).

## Local state

Source: [security model](https://kafka.apache.org/44/security/security-model-streams/). Kafka does not encrypt local state stores or changelogs on disk; they are only as safe as the host filesystem. The `allow.os.group.write.access` config (KIP-1230, 4.2) exists ([upgrade guide](https://kafka.apache.org/44/streams/upgrade-guide/)); its default is (unverified, U12).

## Internal topics

Source: [manage topics](https://kafka.apache.org/44/streams/developer-guide/manage-topics/).

| Topic kind | Cleanup | Retention |
|---|---|---|
| Repartition | `delete` | Infinite |
| Key-value changelog | `compact` | Not applicable |
| Windowed changelog | `delete,compact` | 24 h plus window retention |

All use `CreateTime`. The naming pattern `<application.id>-<operatorName>-<suffix>` "is not guaranteed for future releases". Input and output topics are created ahead of time (medium confidence, M5). Internal topic replication factor: (medium confidence, M1). A distinct `state.dir` per instance on one host: (medium confidence, M2). The page may end abruptly (medium confidence, U13).
