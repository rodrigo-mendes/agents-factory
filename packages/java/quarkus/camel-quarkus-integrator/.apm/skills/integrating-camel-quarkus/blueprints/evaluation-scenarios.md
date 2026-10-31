# Evaluation Scenarios: integrating-camel-quarkus

Five scenarios covering canonical, edge, misuse and anti-pattern cases. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-file-transform-http
query: "I need an integration that watches /input for XML files, transforms them with an XSLT stylesheet, and POSTs the result to an external API. Add a test."
must_pass:
  - "Runs the four-block interview (or confirms the answers already given) and posts a requirement summary for confirmation before generating"
  - "Loads structuring-camel-quarkus-projects first, then developing-camel-quarkus-core-v3-40"
  - "Loads the file-processing, data-transformation and http-clients blueprints, plus testing because a test was requested"
  - "Loads developing-camel-quarkus-file-v3-40, developing-camel-quarkus-xslt-v3-40, developing-camel-quarkus-http-v3-40, developing-camel-quarkus-junit-v3-40 and developing-quarkus-junit-v3-40"
  - "Joins the three specialties through direct: endpoints, one RouteBuilder per specialty"
  - "Ends with the checklist, including ./mvnw clean compile"
must_not:
  - "Loads the REST APIs blueprint, platform-http, rest, jaxb, log, bean or arc skills"
  - "Generates code before the user confirms the summary"
  - "Adds @ApplicationScoped to a RouteBuilder that injects nothing"
```

---

## Scenario 2: Edge Case

**Type**: Narrow request that must not over-load

```yaml
id: 2
name: edge-rest-only
query: "Expose POST /orders that accepts JSON and hands it to direct:process-order. Nothing else yet."
must_pass:
  - "Loads only the REST APIs blueprint"
  - "Loads developing-camel-quarkus-platform-http-v3-40 and developing-camel-quarkus-rest-v3-40 after the structure and core skills"
  - "Asks the Ask First questions of the REST blueprint that matter (contract-first or code-first, CORS origins) instead of assuming"
  - "Leaves the consumer of direct:process-order to the core routes specialty without loading its blueprint"
must_not:
  - "Loads the file-processing, http-clients, data-transformation or testing blueprints"
  - "Loads developing-quarkus-rest-v3-40 without the user choosing Jakarta REST resources"
  - "Loads all 13 skills"
```

---

## Scenario 3: Misuse

**Type**: Request outside the package scope

```yaml
id: 3
name: misuse-kafka-and-jdbc
query: "Consume orders from a Kafka topic, enrich them from a PostgreSQL table with JDBC, and publish to another topic."
must_pass:
  - "States that no installed skill covers Kafka or message brokers, or JDBC and databases"
  - "Asks whether to proceed with only the documented parts, or to research first with /researching-technical-frameworks"
  - "Loads no skill or blueprint for the out-of-scope parts"
  - "Does not name Kafka or JDBC extensions, annotations or options as verified"
must_not:
  - "Invents a skill name such as developing-camel-quarkus-kafka-v3-40"
  - "Writes from(\"kafka:...\") or JDBC route code as if documented"
  - "Says the skills will 'load the appropriate skills' for these areas"
```

---

## Scenario 4: Anti-pattern Trap

**Type**: User asks for patterns the skills forbid

```yaml
id: 4
name: trap-spring-resilience4j-junit5
query: "Build the API with a Spring @RestController, wrap the outbound call in camel-quarkus-resilience4j, and write the tests with camel-quarkus-junit5."
must_pass:
  - "Corrects @RestController: Spring annotations do not apply on Quarkus; offers the REST DSL (developing-camel-quarkus-rest-v3-40) or a Jakarta REST resource (developing-quarkus-rest-v3-40) and asks which"
  - "Corrects camel-quarkus-resilience4j: not in 3.40.x; uses camel-quarkus-microprofile-fault-tolerance per developing-camel-quarkus-http-v3-40"
  - "Corrects camel-quarkus-junit5: use camel-quarkus-junit and org.apache.camel.test.junit6 imports per developing-camel-quarkus-junit-v3-40"
  - "Explains each correction briefly and still proceeds with the corrected design after confirmation"
must_not:
  - "Generates any of the three requested forms"
  - "Calls startRouteDefinitions() or overrides isUseAdviceWith() in the tests"
```

---

## Scenario 5: Handoff and Unverified Relay

**Type**: Closed requirement and confidence tags

```yaml
id: 5
name: handoff-and-unverified-relay
query: "Requirement is closed: timer every 10 minutes calls an external API over HTTPS with OAuth2 client credentials, logs the result. Run it as a batch."
must_pass:
  - "Confirms the summary and that no Ask First decision remains open (asks the timer period, timezone, auth source if missing)"
  - "Offers delegation to the subagent camel-quarkus-integrator with the summary, skill list and blueprint list"
  - "Tells the user that timer and scheduling extension details are not covered by an installed skill and are unverified"
  - "Relays the medium-confidence tag on the OAuth2 options from developing-camel-quarkus-http-v3-40"
must_not:
  - "Delegates while questions are still open"
  - "States timer option names or OAuth2 defaults as verified"
```
