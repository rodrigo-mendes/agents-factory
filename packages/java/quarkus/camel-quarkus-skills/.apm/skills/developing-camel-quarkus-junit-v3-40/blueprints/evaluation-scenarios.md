# Evaluation Scenarios: developing-camel-quarkus-junit-v3-40

Five scenarios covering the four types. The `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-route-test-with-advice
query: "Write a Camel Quarkus 3.40 test for my route 'orders' that replaces the ERP endpoint toErp with a mock and asserts one message arrives."
must_pass:
  - "Adds camel-quarkus-junit at test scope without a version"
  - "Uses @QuarkusTest and extends org.apache.camel.quarkus.test.CamelQuarkusTestSupport"
  - "Uses adviceRoute(\"orders\", ...) or advice in doBeforeEach/@BeforeEach with weaveById(\"toErp\")"
  - "Asserts with getMockEndpoint and assertIsSatisfied"
  - "Does not call startRouteDefinitions()"
must_not:
  - "Uses camel-quarkus-junit5 or org.apache.camel.test.junit5"
  - "Uses a wildcard weave pattern"
  - "States @ApplicationScoped is mandatory on a RouteBuilder"
```

---

## Scenario 2: Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-unverified-and-conflicting-items
query: "The guide overrides createCamelContext() in tests. Should I? Also, will camel-quarkus-junit5 be removed, and does NotifyBuilder work with the shared context?"
must_pass:
  - "States the guide/source conflict on createCamelContext() (3.40.0 source declares only camelContextSupplier and bindToRegistry) and does not assert the override compiles"
  - "States the removal date of the camel-quarkus-junit5 stub is unverified and recommends camel-quarkus-junit"
  - "States NotifyBuilder behavior against the shared context is unverified and offers MockEndpoint"
must_not:
  - "Invent a removal version for the junit5 stub"
  - "Assert a Camel Quarkus-specific end-of-support date"
```

---

## Scenario 3: Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-generic-quarkus-and-quarkus-4
query: "Explain Quarkus test profiles in depth for plain REST resources, and make my Camel tests work on Quarkus 4.0 Beta."
must_pass:
  - "Points generic Quarkus testing to the sibling skill developing-quarkus-junit-v3-40"
  - "Declines to apply 3.40.x guidance to Quarkus 4 and notes no Camel Quarkus build on it is known as of 2026-10-14 (medium confidence, absence of evidence)"
  - "States the skill covers camel-quarkus-junit 3.40.x test support only"
must_not:
  - "Fabricate a Camel Quarkus 4 BOM or artifact"
  - "Restate generic Quarkus testing content as if it were Camel-specific"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Request with a Never Do violation embedded

```yaml
id: 4
name: trap-legacy-idioms-and-context-restart
query: "Port this 3.15 test as-is: it uses camel-quarkus-junit5, org.apache.camel.test.junit5 imports, isUseAdviceWith() returning true, startRouteDefinitions() after adviceWith, and context.stop()/start() to reset state. Also add @Inject ProducerTemplate to the IT that extends CamelQuarkusTestSupport."
must_pass:
  - "Replaces the artifact with camel-quarkus-junit and imports with org.apache.camel.test.junit6"
  - "Removes isUseAdviceWith() and startRouteDefinitions(), advising in doBeforeEach or adviceRoute"
  - "Removes context.stop()/start() and does not return a new CamelContext; may offer @TestProfile for a clean context (medium confidence, M12)"
  - "Refuses @Inject and CamelQuarkusTestSupport in @QuarkusIntegrationTest and proposes a plain @QuarkusTest base using REST Assured or files"
must_not:
  - "Keep any of the legacy idioms"
  - "Return a new CamelContext from a test"
```

---

## Scenario 5: Edge Case (ask-first choice)

**Type**: Decision the skill must put to the user

```yaml
id: 5
name: edge-native-reuse-decision
query: "I want the same route tests to run in JVM and native mode. Which base class should I use?"
must_pass:
  - "Notes CamelQuarkusTestSupport is JVM mode only"
  - "Asks whether the test must also run against the packaged artifact and proposes a plain @QuarkusTest base reused by a @QuarkusIntegrationTest subclass, tagged medium confidence for the example style"
  - "Mentions integration tests use the prod profile and ignore src/test/resources/application.properties, tagged medium confidence"
must_not:
  - "Claim CamelQuarkusTestSupport works in native mode"
```
