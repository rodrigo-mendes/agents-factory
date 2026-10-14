# Evaluation Scenarios: developing-quarkus-arc-v3-40

Five scenarios covering the four types plus one recommendation check. The `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-camel-route-calls-cdi-bean-by-name
query: "In a Camel Quarkus 3.40 app, write a route that calls a CDI bean named orderMapper by name, and make sure Quarkus does not remove the bean."
must_pass:
  - "Gives the bean a bean-defining scope such as @ApplicationScoped"
  - "Qualifies the bean with @Identifier (or notes @Named as the alternative) and uses .bean(name, method) or bean:name"
  - "Adds @Unremovable, explaining that removal of an @Identifier-only bean is unverified in the docs"
  - "Leaves the RouteBuilder unscoped because it injects nothing"
must_not:
  - "States @ApplicationScoped is mandatory on a RouteBuilder"
  - "Put @ApplicationScoped on a route class that has no @Inject or @ConfigProperty"
  - "Assert that ArC does or does not remove an @Identifier-only bean"
```

---

## Scenario 2: Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-identifier-removal-and-support-dates
query: "My bean has only @Identifier and nothing injects it. Will ArC remove it? Also, until when is Camel Quarkus 3.40 supported, and which Java does Quarkus 3.40 need?"
must_pass:
  - "States removal of an @Identifier-only bean is unverified and recommends @Unremovable"
  - "States the Camel Quarkus-specific support end date is not published, and only the Quarkus 3.40 LTS date (2027-09-30) is known"
  - "States the minimum Java for 3.40 was not recorded (unverified)"
  - "Notes that @Named beans, @Unremovable beans and unremovable-types are unremovable per the CDI reference"
must_not:
  - "Assert a Camel Quarkus end-of-support date"
  - "Assert a minimum Java version as documented"
```

---

## Scenario 3: Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-portable-extension-and-quarkus-4
query: "Write a CDI portable extension observing AfterBeanDiscovery, add a @ConversationScoped bean, and make it run on Quarkus 4.0 Beta1."
must_pass:
  - "States CDI portable extensions are not supported and @ConversationScoped is not available in ArC (CDI Lite)"
  - "Points to Quarkus extension build items as the replacement"
  - "Declines to apply 3.40.x guidance to Quarkus 4 and notes no Camel Quarkus build on it is known as of 2026-10-14 (medium confidence, absence of evidence)"
must_not:
  - "Provide a working portable extension for ArC"
  - "Fabricate a Quarkus 4 or Camel Quarkus 4 dependency"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Request with a Never Do violation embedded

```yaml
id: 4
name: trap-injectmock-on-singleton-and-field-access
query: "Mark my Clock service @Singleton, mock it in the test with @InjectMock, and read its public counter field directly from another bean. Keep it simple."
must_pass:
  - "Warns that only normal-scoped beans can be mocked and @InjectMock does not work on @Singleton or @Dependent"
  - "Offers @ApplicationScoped (or @MockitoConfig(convertScopes = true) as an advanced option) and asks which the user prefers"
  - "Warns that fields of a normal-scoped bean must not be read through the client proxy and suggests a getter"
  - "Mentions quarkus-junit-mockito is required"
must_not:
  - "Keep @InjectMock on a @Singleton bean without a warning"
  - "Read the field of an @ApplicationScoped bean directly"
```

---

## Scenario 5: Recommendation Check

**Type**: A recommendation that must not be presented as a hard failure

```yaml
id: 5
name: named-versus-identifier-recommendation
query: "Is using @Inject @Named(\"primary\") forbidden in Quarkus 3.40? A teammate says it breaks the build."
must_pass:
  - "States the Quarkus CDI reference recommends @Identifier instead of @Named, as a recommendation"
  - "Gives the documented reason: a @Named-only bean also gets @Default and can be ambiguous"
  - "Mentions the exception: an external language such as Qute that needs the bean name"
must_not:
  - "Claim @Named is forbidden or always fails the build"
```
