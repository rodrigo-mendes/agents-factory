# Evaluation Scenarios: refactoring-quarkus-java

Six scenarios: canonical, edge, misuse rejection, anti-pattern trap, reviewer use at I7, out-of-scope routing. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical path](#scenario-1-canonical-path)
- [Scenario 2: Edge case](#scenario-2-edge-case)
- [Scenario 3: Misuse rejection](#scenario-3-misuse-rejection)
- [Scenario 4: Anti-pattern trap](#scenario-4-anti-pattern-trap)
- [Scenario 5: Reviewer at I7](#scenario-5-reviewer-at-i7)
- [Scenario 6: Out of scope](#scenario-6-out-of-scope)

---

## Scenario 1: Canonical path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-fat-resource-with-aws-client
skills: ["refactoring-quarkus-java"]
query: "My Quarkus 3.40 OrderResource.create is 90 lines: it validates, maps, sends to SQS and builds error responses. Refactor it for readability."
must_pass:
  - "Establishes a green baseline (runs the suite) and maps test coupling before editing"
  - "Refactors one smell at a time and reruns the tests after each step"
  - "Leaves the resource thin: same blocking signature, @Valid on the parameter, same status codes"
  - "Extracts a flow, a mapper and a client wrapper; every injected new class gets a scope such as @ApplicationScoped"
  - "Keeps the log texts, exception types and side-effect order of the original"
  - "Keeps the handler or resource class at the package root; uses web/, handler/, client/, transform/, obs/ neutrally"
must_not:
  - "Changes a status code, log text or the order of map-then-send"
  - "Adds an interface with one implementation"
  - "Presents the AWS client wrapper code as taken from an official page (it is illustrative)"
```

---

## Scenario 2: Edge case

**Type**: Unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-identifier-only-bean-moved-to-new-module
skills: ["refactoring-quarkus-java"]
query: "I want to move OrderMapper, which has only @Identifier(\"orderMapper\") and is called by name from a Camel route, into a new orders-core Maven module. Will it still work, and can I use a record for the route context?"
must_pass:
  - "States that beans in another module are discovered only with beans.xml, META-INF/jandex.idx or quarkus.index-dependency.* and shows the properties"
  - "States that removal of an @Identifier-only bean is unverified and keeps or adds @Unremovable"
  - "Treats the module split as an Ask First decision"
  - "Notes that the Quarkus 3.40 minimum Java is not recorded (unverified) and asks which JDK the build uses before using records"
must_not:
  - "Asserts that ArC does or does not remove an @Identifier-only bean"
  - "Claims the Quarkus 3.40 minimum Java version"
```

---

## Scenario 3: Misuse rejection

**Type**: Request the skill must refuse to fold into a refactor

```yaml
id: 3
name: misuse-fix-behaviour-while-refactoring
skills: ["refactoring-quarkus-java"]
query: "While refactoring my exception mapper I noticed IllegalStateException returns 500 but should probably be 409, and a log line is misleading. Change them as part of this cleanup."
must_pass:
  - "Refuses to change status codes or log texts during the refactor"
  - "Preserves 500 and the existing log text, finishes the refactor with a green suite"
  - "Proposes a separate task for the 409 change and the log text"
  - "Explains that mixing behaviour fixes with refactoring makes regressions impossible to bisect"
must_not:
  - "Changes the status code or log text 'while in there'"
```

---

## Scenario 4: Anti-pattern trap

**Type**: Tempting edits that break Quarkus contracts

```yaml
id: 4
name: trap-scope-validation-and-handler-rename
skills: ["refactoring-quarkus-java"]
query: "Clean up my Lambda project: make Clock a @Singleton for speed, move @Valid from the resource into OrderService.create, and rename OrderEventsHandler to OrderEventProcessor."
must_pass:
  - "Declines the scope change in a refactor as team practice (separate task); mentions that @InjectMock works only on normal-scoped beans and a @Singleton needs @MockitoConfig(convertScopes = true), tagged (medium confidence, L1)"
  - "Declines moving @Valid: parameter violations return 400, service-method violations give 5xx unless ConstraintViolationException is mapped"
  - "On the rename: changes class name, CDI name and quarkus.lambda.handler together, or recommends not renaming deployed configuration during a refactor"
  - "Cites the Quarkus 3.40 pages for each claim"
must_not:
  - "Applies the three edits without comment"
  - "Renames the class but leaves quarkus.lambda.handler at the old CDI name"
```

---

## Scenario 5: Reviewer at I7

**Type**: Review a finished diff

```yaml
id: 5
name: reviewer-checklist-with-adr-check
skills: ["refactoring-quarkus-java"]
query: "Review this refactor diff: OrderResource now returns Uni<OrderDto>, a new class CreateOrderFlow has no scope annotation, and the PR replaces the X-Ray client wrapper with an OpenTelemetry one."
must_pass:
  - "Starts with the process items: checks the diff against the project's ADRs before reading the code"
  - "Flags the Uni return type as a thread-model flip (high severity)"
  - "Flags the missing scope on an injected class (high severity)"
  - "Flags the tracing replacement as a non-refactor (scope of change) and as a possible ADR contradiction"
  - "Reports in the verdict format: verdict, findings with severity low|moderate|high, ADR check, tests"
must_not:
  - "Approves without an ADR check"
  - "Uses the bare word medium for a severity"
```

---

## Scenario 6: Out of scope

**Type**: Routing to the correct neighbour

```yaml
id: 6
name: out-of-scope-oci-and-quarkus-4
skills: ["refactoring-quarkus-java"]
query: "Refactor my OCI Function (FnConfiguration, fn-events) and also apply the Quarkus 4 Jackson 3 changes while you are at it."
must_pass:
  - "States OCI Functions code is out of scope for this skill"
  - "States that Quarkus 4 behaviour is out of scope for this skill (Quarkus 3.40 statements only)"
  - "Does not apply Quarkus 4 patterns or OCI/FDK facts"
must_not:
  - "Mixes OCI/FDK facts into the Quarkus refactor"
  - "Asserts Quarkus 4 behaviour as fact"
```
