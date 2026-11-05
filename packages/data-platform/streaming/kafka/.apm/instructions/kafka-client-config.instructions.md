---
name: kafka-client-config
description: "Kafka config review checks: producer durability, listener security, authorizer/ACL, Connect errors and secrets, image pinning. Use when editing broker, producer, consumer, Kafka Streams or Connect properties and Connect JSON configs."
applyTo: "**/*kafka*.properties,**/server.properties,**/broker.properties,**/controller.properties,**/zookeeper.properties,**/producer.properties,**/consumer.properties,**/streams.properties,**/connect-*.json,**/connect.json,**/connector-*.json,**/connect-*.properties,**/connect.properties"
---

# Kafka configuration checks

Technical facts live in the skills; this rule only states what to check and where to look.
Skills are under `.claude/skills/`. Tags `(unverified)` / `(medium confidence)` in a skill apply here too.
Path-scoped rules load only when a matching file is read. The file patterns cover the standard Kafka file names
(`server`, `broker`, `controller`, `zookeeper`, `producer`, `consumer`, `streams`, `connect-*` and `connect` properties,
`connect-*`, `connect` and `connector-*` JSON). A Kafka Streams application that keeps its settings in `application.properties` or in code
is not matched: open the Streams skill directly for those.
This rule does not cover Kubernetes YAML custom resources, Compose files or Java code, or registry
config files that do not match these names.

## Pick the skill first

- The file has `zookeeper.connect` (ZooKeeper mode): read `operating-kafka-v3-9`. Otherwise read `operating-kafka-v4-4`.
  Do not mix settings between the two; each skill is locked to its own version.
- Connect worker or connector config (files named `connect-*`, `connect` or `connector-*`): read `integrating-kafka-connect-v4-4`.
- Kafka Streams application properties: read `streaming-kafka-streams-v4-4`.
- Schema registry client or server settings: `managing-event-schemas-apicurio-v3-3` or
  `managing-event-schemas-confluent-v8-4`. Ask which registry is in use if the file does not show it.
- Kubernetes configs (Strimzi or Confluent for Kubernetes): read `operating-kafka-strimzi-v1-3` or
  `operating-kafka-confluent-kubernetes-v3-4`, then follow their own checks. This rule does not cover the YAML CRs.

## Always

- Producer durability: check `acks` and idempotence against the Always Do tier of `operating-kafka-v4-4`
  (or `operating-kafka-v3-9` for ZooKeeper-line files). Flag any override that weakens them.
- Replication factor and `min.insync.replicas` of durable topics and internal topics: compare with the
  same Always Do tier; compare Connect internal topics with `integrating-kafka-connect-v4-4`.
- Listeners that leave the host must use an encrypted protocol: check against the Always Do tier of the
  broker skill. A PLAINTEXT listener off-host is a finding.
- Authorizer and ACL defaults: check against the Always Do and Never Do tiers of `operating-kafka-v4-4`
  (authorizer, deny-by-default setting). `operating-kafka-v3-9` has no deny-by-default authorizer item in its Always Do tier:
  for ZooKeeper-line files report that check as unverified and read its ZooKeeper security blueprint instead.
- Connect REST exposure and client override policy: check against the Always Do tier of
  `integrating-kafka-connect-v4-4`.
- Connect secrets: every secret is a config-provider placeholder (`integrating-kafka-connect-v4-4`).
- Connect error handling: confirm the error tolerance choice is deliberate and that bad records go to a
  dead letter queue when tolerance is not strict (`integrating-kafka-connect-v4-4`, error handling blueprint).
- Streams: processing guarantee value, exception handler keys and explicit naming are checked against the
  Always Do and Never Do tiers of `streaming-kafka-streams-v4-4`.
- Image tags in any config snippet or comment are pinned exactly as the matching skill shows them
  (broker skills, Apicurio skill, Confluent registry skill).
- Quote the skill and the tag (`(unverified)` / `(medium confidence)`) when reporting a finding.

## Ask first

- Anything the loaded skill lists in its Ask First table: controller placement, quorum type, native image,
  topic auto-creation, error tolerance and DLQ ownership, exactly-once sources, REST authentication,
  plugin discovery mode, rebalance protocol, compatibility level, auto-registration, license-gated features.
- Any setting a skill marks `(unverified)` or `(medium confidence)`: ask before asserting it as correct.
- Moving a ZooKeeper-mode config toward 4.x: the migration path is in `operating-kafka-v3-9`; ask before editing.
- Kafka version versus operator support when a Strimzi or Confluent for Kubernetes config references it:
  check the operator skill's supported versions before proposing a change.
- Registry choice (Apicurio or Confluent) and license-gated features: ask whether the Enterprise license exists.

## Never

- Copy the official example defaults (single replica, temp-directory logs, `latest` or snapshot tags,
  wildcard CORS) into a persistent or shared environment. Each broker, Connect and Apicurio skill names the replacement.
- Inline a secret in a connector config or properties file: use the config provider route.
- Turn on message logging for Connect errors in production: the skill names the safe setting.
- Open the Connect REST port to untrusted networks without authentication.
- Add ZooKeeper settings to a 4.x file or KRaft-only settings to a ZooKeeper-mode file without reading the
  other skill first.
- Use settings the skills list as removed or deprecated for 4.4 (Streams processing guarantee values,
  deprecated override policies, `default.*` handler keys): the skills name the replacements.
- Write Debezium, MySQL, observability or benchmark settings from memory: no skill in this package covers
  them, so flag it to the user.

## Verify

Re-read the matching skill's Always Do and Never Do tiers after editing and list each check as pass, fail
or unverified. Run no cluster command on the user's behalf; propose it with the skill's verification command.
