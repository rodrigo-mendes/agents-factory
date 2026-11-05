# Evaluation scenarios, managing-event-schemas-confluent-v8-4

Back to [SKILL.md](../SKILL.md). Nine scenarios: canonical (2), edge (2), rejection (4 misuse cases), trap (1). Each `query` is a user request. `expected_behavior` is what a correct answer does.

## Scenario 1: canonical, local development stack

```json
{
  "skills": ["managing-event-schemas-confluent-v8-4"],
  "query": "Give me a docker compose with Kafka and Confluent Schema Registry 8.4 for local development.",
  "expected_behavior": [
    "Uses confluentinc/cp-kafka:8.4.0 in KRaft combined mode and confluentinc/cp-schema-registry:8.4.0, with SCHEMA_REGISTRY_HOST_NAME and SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS set",
    "Says the Compose file is this skill's assembly and (unverified) as a tested whole",
    "Notes that _schemas gets replication factor 1 with one broker, for development only",
    "Verifies with GET /subjects and a describe of _schemas (1 partition, cleanup.policy=compact)",
    "Does not claim an official health-check endpoint exists (unverified)"
  ]
}
```

## Scenario 2: canonical, Protobuf compatibility

```json
{
  "skills": ["managing-event-schemas-confluent-v8-4"],
  "query": "Which compatibility level should the orders-value Protobuf subject use and how do I set it?",
  "expected_behavior": [
    "Recommends BACKWARD_TRANSITIVE for Protobuf with the reason that adding message types is not forward compatible",
    "Gives PUT /config/orders-value with Content-Type application/vnd.schemaregistry.v1+json",
    "Says the implicit default is non-transitive BACKWARD and asks how many versions must stay readable",
    "Recommends normalize.schemas=true"
  ]
}
```

## Scenario 3: edge, default subject name strategy

```json
{
  "skills": ["managing-event-schemas-confluent-v8-4"],
  "query": "What is the default value.subject.name.strategy in 8.4.0?",
  "expected_behavior": [
    "Reports both facts: the docs name TopicNameStrategy, the 8.4.0 source defaults to AssociatedNameStrategy with TopicNameStrategy fallback (unverified)",
    "Does not pick a winner, says behavior is the same unless topic-subject associations exist",
    "Advises setting the strategy explicitly and asks whether associations exist"
  ]
}
```

## Scenario 4: edge, release 8.4.0 of 2026-10-27

```json
{
  "skills": ["managing-event-schemas-confluent-v8-4"],
  "query": "Roll Schema Registry 8.4.0 into production this week.",
  "expected_behavior": [
    "States 8.4.0 was released 2026-10-27, research date 2026-11-04, and that unreleased 8.4.1 build tags already exist on GitHub",
    "Tells the user to check for an 8.4.1 release before shipping and asks whether to ship now or wait",
    "Checks that every client uses kafka-schema-registry-client 6.2 or later, and upgrades brokers before Schema Registry (medium confidence)",
    "Does not claim CVE status for 8.4.0 (unverified)"
  ]
}
```

## Scenario 5: rejection, Apicurio

```json
{
  "skills": ["managing-event-schemas-confluent-v8-4"],
  "query": "Set up Apicurio Registry with PostgreSQL storage for our Kafka cluster.",
  "expected_behavior": [
    "Declines: this skill covers Confluent Schema Registry 8.4.0 only",
    "Points to the skill managing-event-schemas-apicurio-v3-3",
    "Does not mix Apicurio settings into the answer"
  ]
}
```

## Scenario 6: rejection, Kubernetes deployment

```json
{
  "skills": ["managing-event-schemas-confluent-v8-4"],
  "query": "Deploy Confluent Schema Registry on Kubernetes with an operator and a Helm chart.",
  "expected_behavior": [
    "Declines Kubernetes operator content: it is out of scope for this skill",
    "Points to the skill operating-kafka-confluent-kubernetes-v3-4",
    "May still give the node-level settings that apply anywhere: Kafka-based election, host.name, group ID, _schemas rules"
  ]
}
```

## Scenario 7: rejection, RBAC without an Enterprise license

```json
{
  "skills": ["managing-event-schemas-confluent-v8-4"],
  "query": "Turn on RBAC for Schema Registry. We only run the Community edition, so just assume it works.",
  "expected_behavior": [
    "Refuses to assume it works: the security page says the Schema Registry security plugins require a Confluent Enterprise license, and the license page says a license is required for RBAC through the Security Plugins (medium confidence)",
    "Asks whether the user holds an Enterprise license",
    "Without one, offers HTTPS plus Basic auth or mTLS, with authorization at network and Kafka-ACL level",
    "Gives no legal advice"
  ]
}
```

## Scenario 8: rejection, competing SaaS on the Community License

```json
{
  "skills": ["managing-event-schemas-confluent-v8-4"],
  "query": "We want to host Schema Registry as a paid managed service for other companies. Is the Community License fine with that?",
  "expected_behavior": [
    "Quotes the Excluded Purpose: making available any software-as-a-service, platform-as-a-service, infrastructure-as-a-service or other similar online service that competes with Confluent products or services that provide the Software (medium confidence)",
    "Says running it for your own workloads is within the grant and a competing hosted offering is the Excluded Purpose, as an inference",
    "States this is not legal advice and tells the user to read the license text and ask a lawyer",
    "Does not state a license for the cp-schema-registry Docker image (unverified)"
  ]
}
```

## Scenario 9: anti-pattern trap, hard delete

```json
{
  "skills": ["managing-event-schemas-confluent-v8-4"],
  "query": "Clean up orders-value: DELETE /subjects/orders-value?permanent=true. Our topic still has data using version 3.",
  "expected_behavior": [
    "Warns that a hard delete removes all metadata including schema IDs, which are not reusable, so the data in the topic could no longer be deserialized",
    "Gives the sequence: soft delete the version first, hard delete a numbered version only when no topic holds its ID",
    "Notes that versions/latest with permanent=true gives only a soft delete",
    "Notes the deletion APIs are primarily intended for development"
  ]
}
```
