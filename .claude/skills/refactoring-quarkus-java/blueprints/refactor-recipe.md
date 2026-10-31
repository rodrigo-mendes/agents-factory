# Safe-refactor recipe

Back to [SKILL.md](../SKILL.md). The method is team practice (register U1, no page read; the Quarkus-specific rule is `quarkus-clean-code`, package `quarkus-core`); the Quarkus checks in steps 2, 5 and 6 are Quarkus 3.40 facts with their sources. Package layout: [taxonomy](./package-taxonomy.md).

## Steps

1. **Baseline green.** Run the full suite and require exit code 0 ([patterns](./always-do-patterns.md#green-baseline)).
2. **Map test coupling and deployed names.** Note bean types named by `@InjectMock`, resource classes named by `@TestHTTPEndpoint`, constructors used by tests, and the CDI names used by configuration such as `quarkus.lambda.handler` ([AWS Lambda guide](https://quarkus.io/guides/aws-lambda)).
3. **Identify smells** with the table below. Write the list; do not fix yet.
4. **Extract one smell** in a small step. Keep public signatures, package-private test hooks, exception types and messages.
5. **Check the Quarkus contract of what moved.** Scope on every injected collaborator, markers that moved with a bean, resource signature kind, constraint annotations on the parameter ([patterns](./always-do-patterns.md)).
6. **Run the suite.** Green means parity. Where a quick look at removed beans is useful, ArC lists them in dev mode (unverified, U4).
7. **Relocate tests** to the class that now owns the logic; add a focused test for each new collaborator. Ask before editing shared test files.
8. **Repeat from step 3** for the next smell, then stop (see [stop rule](#stop-rule)).

## Smells and triggers

| Smell or trigger | Extraction |
|---|---|
| Method longer than about 40 lines | Extract private methods with intent-revealing names |
| A comment that titles a block (`// 1. validate body`) | The comment becomes the method name |
| More than 2 nesting levels | Guard clauses and early returns |
| Try/catch or logging scaffolding repeated around calls | One helper (for example a `TracedCall.run(name, callable)` wrapper) |
| `if`/`switch` chain classifying exceptions or magic strings | A dedicated `ErrorMapper` in `web/` |
| Response or DTO construction repeated with small variations | A factory method in `web/` or `transform/` |
| Same send-with-retry or call-with-wrap logic in two places | Shared, parameterized executor (see DRY below) |
| Long parameter list or local-variable sprawl | A private `record` ([below](#records-as-value-holders)) |
| Static utility holding several concerns | Facade ([below](#facade-over-statics)) |

## DRY with exception parity

Extract duplicated logic when it appears in two or more places. When collapsing it, keep the exact exception types and messages: downstream error mapping and tests depend on them.

```java
// before: two clients each wrap failures with their own message
// after: one executor, each caller injects its own failure message
<T> T call(Supplier<T> action, Function<RuntimeException, RuntimeException> onFailure) {
    try { return action.get(); }
    catch (RuntimeException e) { throw onFailure.apply(e); }
}
// caller A keeps: e -> new IllegalStateException("queue send failed: " + e.getMessage())
// caller B keeps: e -> new IllegalStateException("table read failed: " + e.getMessage())
```

Log lines inside the helper must keep their text and level; a log moved into a shared method keeps one distinct text per caller.

## Records as value holders

Group correlated values (configuration read from `@ConfigProperty`, per-request context, credentials) into a small private `record` instead of long parameter lists. Records need a Java level that supports them; the Quarkus 3.40 minimum is not recorded (unverified, U3), so confirm the build JDK first.

```java
private record SendContext(String queueUrl, String correlationId, int attempt) { }
```

## Facade over statics

When a static utility accumulates concerns, keep its public static API and delegate internally to focused collaborators. Call sites and tests stay unchanged. Static helpers are not CDI beans; if a collaborator needs injection, it is a bean and the facade receives it from the caller or a producer.

## Naming and constants

Names reveal intent (`resolveOrder`, `enqueueConfirmation`), not mechanics. Replace magic numbers and strings with named constants (`MAX_BODY_BYTES`, `ORDER_PATH`). Constant values stay identical.

## Stop rule

Stop when each method reads as a short sequence of named steps, no scaffolding is duplicated, and the entry class only orchestrates. Do not extract single-use indirection, and do not add an interface without a second implementation or a real test seam.
