# Evaluation scenarios, managing-event-schemas-apicurio-v3-3

Back to [SKILL.md](../SKILL.md). Eight scenarios: canonical, edge, rejection (four misuse cases), trap. Each `query` is a user request. `expected_behavior` is what a correct answer does.

## Scenario 1: canonical, production registry on PostgreSQL

```json
{
  "skills": ["managing-event-schemas-apicurio-v3-3"],
  "query": "Set up Apicurio Registry 3.3 for our shared staging environment with PostgreSQL and a login.",
  "expected_behavior": [
    "Sets APICURIO_STORAGE_KIND=sql and APICURIO_STORAGE_SQL_KIND=postgresql, not the default H2",
    "Pins apicurio/apicurio-registry:3.3.4 and passes the datasource credentials through _FILE secrets",
    "Enables OIDC (QUARKUS_OIDC_TENANT_ENABLED=true) and role-based authorization",
    "Sets a COMPATIBILITY rule explicitly and asks which level fits topic retention",
    "Notes that the assembled Compose file is (unverified) as a tested whole"
  ]
}
```

## Scenario 2: canonical, KafkaSQL journal topic

```json
{
  "skills": ["managing-event-schemas-apicurio-v3-3"],
  "query": "We want KafkaSQL storage. Create the journal topic.",
  "expected_behavior": [
    "Creates the topic with cleanup.policy=delete, retention.ms=-1 and retention.bytes=-1, never compact",
    "Uses replication factor 3 and verifies the settings with kafka-configs.sh --describe",
    "Does not claim a required partition count and reports that official pages show 1 and 3 (unverified)",
    "Does not set a fixed consumer group ID"
  ]
}
```

## Scenario 3: edge, which side upgrades first

```json
{
  "skills": ["managing-event-schemas-apicurio-v3-3"],
  "query": "With BACKWARD_TRANSITIVE, do we upgrade consumers or producers first?",
  "expected_behavior": [
    "Says the 3.3.x pages do not state the upgrade order per mode (unverified) and does not assert one",
    "States only what the mode checks: transitive modes check every prior version",
    "Mentions that BACKWARD_TRANSITIVE as a production level rests on a single official page (medium confidence) and asks about retention and consumer lag"
  ]
}
```

## Scenario 4: rejection, Confluent Schema Registry

```json
{
  "skills": ["managing-event-schemas-apicurio-v3-3"],
  "query": "Configure Confluent Schema Registry with Avro compatibility for our Kafka cluster.",
  "expected_behavior": [
    "Declines: this skill covers Apicurio Registry 3.3.x only",
    "Points to the skill managing-event-schemas-confluent-v8-4",
    "May mention that Apicurio offers a Confluent-compatible API at /apis/ccompat/v7 with documented gaps, if the user wants to keep Confluent clients on Apicurio"
  ]
}
```

## Scenario 5: rejection, downgrade

```json
{
  "skills": ["managing-event-schemas-apicurio-v3-3"],
  "query": "3.3.4 broke something. Roll the image back to 3.3.3 on the same PostgreSQL database.",
  "expected_behavior": [
    "States that migrations are forward-only (medium confidence) and asks about a backup, instead of rolling the image back in place",
    "Gives the documented recovery: stop the registry, restore the pre-upgrade backup, deploy the previous version",
    "Asks whether a restorable pre-upgrade backup exists",
    "Notes that the patch notes of 3.3.4 list bug fixes while the support policy says patches carry none (unverified)"
  ]
}
```

## Scenario 6: rejection, official sample compose in production

```json
{
  "skills": ["managing-event-schemas-apicurio-v3-3"],
  "query": "Use the official docker-compose sample from the Apicurio repo as our production deployment, it is the quickest.",
  "expected_behavior": [
    "Refuses: the samples at tag 3.3.4 use latest-snapshot and CORS * and are development only",
    "Replaces latest-snapshot with apicurio/apicurio-registry:3.3.4, sets explicit CORS origins, uses _FILE secrets, keeps deletion endpoints at their default false",
    "Switches storage from in-memory H2 to PostgreSQL or KafkaSQL and enables OIDC with roles",
    "Offers the hardened Compose in deploy-compose.md and says it is (unverified) as a tested whole"
  ]
}
```

## Scenario 7: rejection, Kubernetes operator

```json
{
  "skills": ["managing-event-schemas-apicurio-v3-3"],
  "query": "Deploy Apicurio Registry 3.3 on Kubernetes with an operator.",
  "expected_behavior": [
    "Declines: Kubernetes operator content is out of scope for this skill",
    "Points to operating-kafka-strimzi-v1-3 and operating-kafka-confluent-kubernetes-v3-4 for the Kafka side and says they do not cover running a registry",
    "Offers the Docker Compose scope of this skill, or asks the user to consult the official operator pages (not read for this skill)"
  ]
}
```

## Scenario 8: anti-pattern trap, Avro field without a default

```json
{
  "skills": ["managing-event-schemas-apicurio-v3-3"],
  "query": "Add a required string field discountCode to our orders-value Avro schema and register it. The rule is BACKWARD.",
  "expected_behavior": [
    "Warns that adding a field without a default is not backward compatible and the registry will reject the version",
    "Proposes {\"name\":\"discountCode\",\"type\":[\"null\",\"string\"],\"default\":null}",
    "Suggests a dry run or a CI registration gate and does not switch the rule to NONE to force it through"
  ]
}
```
