# Evaluation Scenarios: developing-quarkus-rest-v3-40

Five scenarios, covering the four required types. The `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-rest-resource-calls-camel-route
query: "In a Camel Quarkus 3.40 app, add POST /api/orders with Quarkus REST and JSON, validate the body, and hand it to the Camel route direct:processOrder."
must_pass:
  - "Uses quarkus-rest and quarkus-rest-jackson plus quarkus-hibernate-validator, without versions"
  - "Injects ProducerTemplate into the resource and calls requestBody(\"direct:processOrder\", ...) from a blocking (plain return type) method"
  - "Uses @Valid on the body and states invalid input returns 400"
  - "Says the ProducerTemplate-in-resource pattern is shown on the camel-quarkus-examples main branch (medium confidence) and that no official source shows Quarkus REST and platform-http together"
  - "Leaves the RouteBuilder without @ApplicationScoped since nothing is injected"
must_not:
  - "States @ApplicationScoped is mandatory on a RouteBuilder"
  - "Returns Uni from the endpoint while calling requestBody inside it"
  - "Adds quarkus-resteasy* artifacts"
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
  - "Assert which of the two handlers wins on a shared path"
  - "Assert that per-client timeouts inherit the global values"
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
  - "Present tools.jackson.* packages as valid on 3.40"
  - "Fabricate a Camel Quarkus build on Quarkus 4"
  - "Write Camel REST DSL routes from this skill"
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
  - "Recommend origins=* in production"
  - "Claim @PermitAll overrides quarkus.http.auth.permission policies"
```
