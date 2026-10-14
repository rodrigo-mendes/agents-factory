# Evaluation Scenarios: developing-camel-quarkus-bean-v3-40

Four scenarios, one per type. The `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-named-bean-called-from-route
query: "Write a Camel Quarkus 3.40 route that calls a Java bean named orderService to validate the body, and make it work in native mode."
must_pass:
  - "Adds camel-quarkus-bean without a version"
  - "Gives the bean a name (@Named or @Identifier) and @RegisterForReflection, and a bean-defining scope such as @ApplicationScoped (medium confidence)"
  - "Selects the target method with method=, .bean(name, method) or @Handler (any of the three is accepted)"
  - "Uses a plain RouteBuilder without @ApplicationScoped, since nothing is injected"
must_not:
  - "States @ApplicationScoped is mandatory on a RouteBuilder"
  - "Put @ApplicationScoped on a route class that has no @Inject or @ConfigProperty"
  - "Omit @RegisterForReflection on a bean referenced by name"
```

---

## Scenario 2: Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-identifier-only-bean-removal
query: "I named my bean only with @Identifier and nothing injects it. Will Quarkus remove it? And until when is Camel Quarkus 3.40 supported?"
must_pass:
  - "States the removal of an @Identifier-only bean is unverified (the Quarkus CDI reference does not say) and recommends @Identifier plus @Unremovable, or @Named"
  - "States the Camel Quarkus-specific support end date is not published and only the Quarkus 3.40 LTS date (2027-09-30) is known"
  - "Notes that @Named beans and @Unremovable beans are unremovable per the Quarkus CDI reference"
must_not:
  - "Assert that @Identifier-only beans are or are not removed"
  - "Assert a Camel Quarkus end-of-support date"
```

---

## Scenario 3: Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-bean-consumer-and-quarkus-4
query: "Use from(\"bean:myBean\") to start a route, and make it work on Quarkus 4.0 Beta1."
must_pass:
  - "States the Bean component is producer-only and offers .to(\"bean:myBean\") from another endpoint or @Consume on a bean method"
  - "Declines to apply 3.40.x guidance to Quarkus 4 and notes no Camel Quarkus build on it is known as of 2026-10-14 (medium confidence, absence of evidence)"
  - "States the skill covers Camel Quarkus 3.40.x bean binding only"
must_not:
  - "Present bean: as a consumer endpoint"
  - "Fabricate a Camel Quarkus 4 BOM or artifact"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Request with a Never Do violation embedded

```yaml
id: 4
name: trap-singleton-state-and-missing-reflection
query: "Add a bean class with a private List field that collects items across calls, reference it as bean:acc from a route, and ship it as a native image. Keep it simple, no extra annotations."
must_pass:
  - "Warns that the default scope=Singleton shares one instance, so a mutable field is unsafe"
  - "Adds @RegisterForReflection because the 3.40.0 processor registers only @Handler classes, not classes referenced by name"
  - "Adds a bean-defining scope so the bean can be found (medium confidence)"
must_not:
  - "Keep the mutable list in a singleton-scoped bean without a warning"
  - "Skip reflection registration for native mode"
```
