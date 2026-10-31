# Evaluation Scenarios: developing-quarkus-rest-v3-40

Five scenarios, covering the four required types. The `skill-evaluator` agent runs these.

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case](#scenario-2-edge-case)
- [Scenario 3: Misuse Rejection](#scenario-3-misuse-rejection)
- [Scenario 4: Anti-Pattern Trap](#scenario-4-anti-pattern-trap)
- [Scenario 5: Medium-Confidence Handling](#scenario-5-medium-confidence-handling)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-rest-resource-validation-thread-model
query: "In a Quarkus 3.40 app, add POST /api/orders with Quarkus REST and JSON that validates the body and returns 201 with the created order. The service call uses blocking JDBC."
must_pass:
  - "Uses quarkus-rest and quarkus-rest-jackson plus quarkus-hibernate-validator, without versions"
  - "Uses @Valid on the body parameter and states a constraint failure on an endpoint parameter returns 400 with a violations report"
  - "Uses a plain (blocking) return type so the JDBC call runs on a worker thread, and explains that a Uni/Multi signature would run on the IO thread"
  - "Returns RestResponse<T> rather than a raw Response (type inferred at build time, relevant for native mode) and asks whether native mode is a target"
  - "Does not bring in Camel, ProducerTemplate or REST DSL; points Camel content to developing-camel-quarkus-rest-v3-40"
must_not:
  - "Returns Uni from the endpoint while calling blocking code inside it"
  - "Adds quarkus-resteasy* artifacts"
  - "Hardcodes artifact versions that the Quarkus BOM manages"
```

---

## Scenario 2: Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-shared-path-and-client-timeouts
query: "I have a Quarkus REST resource at /orders and a Camel REST DSL route also at /orders. What happens? And do my REST clients inherit the 15000/30000 ms timeouts if I set none?"
must_pass:
  - "States the shared-path behaviour is irresolvable (no 3.40 page states it) and recommends disjoint path prefixes"
  - "States that whether quarkus.rest.path affects platform-http routes is unverified"
  - "States the global defaults are 15000 ms connect and 30000 ms read, but that per-client inheritance is unverified, and recommends explicit per-client timeouts"
must_not:
  - "Asserts which of the two handlers wins on a shared path"
  - "Asserts that per-client timeouts inherit the global values"
```

---

## Scenario 3: Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-quarkus-4-jackson-3-and-rest-dsl
query: "Give me the Quarkus 4 Jackson 3 setup with JsonMapperBuilderCustomizer for my 3.40 app, and write the Camel REST DSL routes too."
must_pass:
  - "Declines to apply Quarkus 4 details to 3.40, noting they come from a migration wiki (medium confidence) and Quarkus 4.0.0.Beta1 was published 2026-10-01"
  - "Points to ObjectMapperCustomizer for 3.40"
  - "Refers the Camel REST DSL part to the sibling skill developing-camel-quarkus-rest-v3-40"
must_not:
  - "Presents tools.jackson.* packages as valid on 3.40"
  - "Fabricates a Camel Quarkus build on Quarkus 4"
  - "Writes Camel REST DSL routes from this skill"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Request with a Never Do violation embedded

```yaml
id: 4
name: trap-trust-all-and-blocking-uni
query: "My REST client fails TLS against the partner API. Just set quarkus.tls.partner.trust-all=true, and make my Uni endpoint call the client synchronously so it stays simple."
must_pass:
  - "Refuses trust-all for production, citing the guides, and offers a named bucket with trust-store.pem.certs and tls-configuration-name"
  - "Warns that a blocking call inside a Uni endpoint runs on the IO thread and proposes a blocking signature"
  - "Keeps the client under a configKey with a mandatory base URL"
must_not:
  - "Sets trust-all or disables hostname verification without a production warning"
  - "Keeps the blocking call in the Uni endpoint"
```

---

## Scenario 5: Medium-Confidence Handling

**Type**: Edge case on tagged claims

```yaml
id: 5
name: edge-cors-and-permitall
query: "Set CORS to * for my production API and mark the public resource @PermitAll while /* requires authentication."
must_pass:
  - "Tags the CORS and @PermitAll guidance as medium confidence (single source) and recommends an explicit origin list"
  - "Explains HTTP permissions run before annotations, so @PermitAll cannot override them, and suggests a permit policy on the public prefix"
  - "Notes that whether annotation checks run before body deserialization is unverified"
must_not:
  - "Recommends origins=* in production"
  - "Claims @PermitAll overrides quarkus.http.auth.permission policies"
```
