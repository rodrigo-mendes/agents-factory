---
name: refactoring-oci-java
description: Refactors OCI Functions Java code for readability with Extract Method, SOLID decomposition, DRY, and behavior-preserving safety (tests stay green). Use when asked to refactor, clean up, improve readability, decompose a god class, extract methods, or apply clean code / SOLID to existing Java.
---

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails) — ✅⚠️🚫 patterns
- [Safe-Refactor Recipe](#safe-refactor-recipe) — step-by-step workflow
- [Before / After Examples](#before--after-examples) — project patterns
- [Verification Loop](#verification-loop) — exit checklist and verification commands
- [Evaluation Scenarios](./blueprints/evaluation-scenarios.md) — canonical, edge, misuse test cases
- [Version Context](#version-context)
- [External Resources](#external-resources)

---

## Blueprints & Guardrails

### ✅ Always Do

- **Establish a green baseline before touching any code.** Run `mvn test` on Corretto 21 and confirm the suite passes. If it is red, fix the failing tests first — refactoring with a red baseline makes it impossible to distinguish regressions from pre-existing failures.
- **Map test coupling before extracting.** Identify which tests call `handler()`, use package-private constructors, or call package-private methods directly. These signatures must not change (or the test must be relocated to the new class).
- **Refactor one smell at a time.** Identify the single largest smell (long method, duplicated scaffolding, magic-string classification, mixed concerns). Extract it, recompile, run tests, then move to the next smell.
- **Run `mvn test` after every extraction step.** A green suite after each step is the proof of behavior preservation — not code review.
- **Preserve exact exception types, messages, log texts, status codes, and side-effect order.** The contract is the observable behavior, not the internal structure.

### ⚠️ Ask First

- **Scope of the refactoring.** Is this a single method extraction, a class decomposition, or a full package restructuring? Larger scope means more test relocation and higher risk — confirm before starting.
- **Test coverage adequacy.** If the class has <50% coverage, adding tests before refactoring reduces risk. Ask whether to add tests first or proceed with caution.
- **Speculative abstractions.** If a new collaborator class would only be used once, ask before creating it. Single-use indirection adds navigation cost without DRY benefit.
- **Relocating tests.** When logic moves to a new class, the unit test for that logic should move too. Confirm before modifying test files — especially if they are shared with other tests.

### 🚫 Never Do

**Never change behavior during a refactoring session.**
```java
// 🚫 WRONG: fixing a bug while refactoring ErrorMapper
// Original: returns 500 for all IOExceptions
public int mapToStatus(Exception e) {
    if (e instanceof IOException) return 503; // "fixing" while refactoring
    return 500;
}

// ✅ CORRECT: preserve existing behavior exactly, then open a separate task to fix
public int mapToStatus(Exception e) {
    if (e instanceof IOException) return 500; // same as original
    return 500;
}
```

**Never remove package-private test constructors or change handler signatures without relocating the dependent test.**
```java
// 🚫 WRONG: removing the test constructor during decomposition
public class OrderFunction {
    // removed: OrderFunction(OrderService svc) {}  ← test depended on this
}

// ✅ CORRECT: keep the constructor OR move the test to the new class that owns the logic
public class OrderFunction {
    OrderFunction(OrderService svc) { this.svc = svc; } // preserved
}
```

**Never start refactoring with a red test suite.**
```bash
# 🚫 WRONG: refactoring despite failing tests
mvn test  # 3 tests FAILED
# ... start extracting methods anyway

# ✅ CORRECT: fix or skip-with-reason first, then refactor
mvn test  # BUILD SUCCESS — 0 failures, 0 errors
# ... now safe to begin refactoring
```

**Never add speculative abstractions — extract to a new class only when there are two or more call sites.**
```java
// 🚫 WRONG: creating an interface for a single implementation "for future flexibility"
interface StoreResolver { ... }
class DefaultStoreResolver implements StoreResolver { ... }
// Only one call site exists

// ✅ CORRECT: extract a plain class; add the interface if/when a second implementation appears
class StoreResolver { ... }
```

---

## Safe-Refactor Recipe

1. **Baseline green.** Set the JVM to Corretto 21 and run the suite before touching code:
   ```bash
   export JAVA_HOME=$(/usr/libexec/java_home -v 21)
   mvn -f services/<func>/pom.xml test
   ```

2. **Map test coupling.** Note what tests depend on: package-private test constructors, the
   `handler(...)` signature, package-private methods called directly. These must not change
   (or relocate the test in step 5).

3. **Identify smells:** long method (>~40 lines), block-titling comments, deep nesting, duplicated
   logic, magic-string/status classification, a static utility holding multiple concerns, long
   parameter lists / local-variable sprawl.

4. **Extract in small steps**, preserving public/test signatures and exact exception types/messages.
   One smell at a time; recompile between steps.

5. **Run tests after each step** to prove parity. Relocate unit tests to the class that now owns the
   logic; add focused tests for newly extracted classes.

---

## Before / After Examples

These examples are drawn from the project's `RestProxyFunction` decomposition:

- **God class → thin dispatcher.** A 578-line `RestProxyFunction` doing routing + store-id resolution +
  mapping + marshalling + span boilerplate + error mapping + metrics became a ~230-line dispatcher that
  routes via `Route` and delegates to collaborators in `route/ transform/ web/ handler/ obs/`.
- **Long method → named steps.** `configure()`/`handler()` were split with Extract Method into
  `readProxyConfig`, `buildHttpClient`, `loadOAuthSecrets`, `beginRequest`, `dispatch`,
  `recordTelemetry`, `populateResponseMetadata` — each method reads as one intent.
- **Repeated span scaffolding → `TracedCall`.** The open-span / try / end-span(null) / catch /
  end-span(error) / rethrow block (5× copies) collapsed into `TracedCall.run(name, peer, attrs, callable)`.
- **Magic-string classification → `ErrorMapper`.** The `if message.startsWith(...)` chain moved into
  a dedicated `web/ErrorMapper` that maps exceptions → HTTP responses.
- **Response construction → `ResponseFactory`.** `ok/error/response` builders centralized in `web/`.
- **Duplicated retry loop → `HttpRetryExecutor`.** Identical send-with-retry in two clients extracted
  to one parameterized executor; each client injects a `ResponseHandler` to keep its exact success
  mapping and exception messages.
- **OAuth split out of client.** Token cache/refresh moved to `OAuth2TokenProvider`; `RmsClient`
  delegates `getAccessToken()`/`invalidateToken()` (tests unchanged).
- **Static multi-concern → facade.** `ObservabilityHelper` kept its static API but delegates to
  `LoggingBridge` + `MetricsPublisher` + `TracingSupport` — no call site or test changed.
- **Variable sprawl → records.** Correlated values grouped into private `record`s (`ProxyConfig`,
  `OAuthCredentials`, `RequestContext`).

---

## Verification Loop

Run the full test suite — it must pass unchanged, proving identical behavior after refactoring:

```bash
mvn test          # expected exit code 0; all tests green (no new failures/skips)
```

- [ ] Full suite green (`mvn test`) — proves identical behavior.
- [ ] Public method signatures and package-private test constructors unchanged (or tests relocated).
- [ ] Exact exception types/messages, log texts, status codes, and side-effect order preserved.
- [ ] Each long method now reads as a short sequence of named steps; no duplicated scaffolding.
- [ ] Business logic delegated out of the handler into the package taxonomy.
- [ ] No speculative abstraction / single-use indirection added.

---

## Version Context

**Java**: Corretto 21 (required — Java 25+ breaks Mockito byte-buddy mocking; do not upgrade JVM
without validating the full test suite)
**Mockito**: current stable compatible with Java 21 (`mockito-core` + `mockito-junit-jupiter`)
**OCI Functions FDK**: current stable (`com.fnproject.fn:api` + `runtime`) — FDK lifecycle
(`@FnConfiguration`, `handler`) must be preserved through any refactoring
**Maven**: 3.8+ (used to run `mvn test` and `mvn -f <path>/pom.xml test`)

**Key constraint:** `JAVA_HOME` must point to Corretto 21 before running tests. Verify:
```bash
java -version   # must show openjdk 21
```

---

## External Resources

- [Fowler Refactoring Catalog](https://refactoring.com/catalog/) — canonical patterns: Extract Method, Extract Class, Move Method, Replace Conditional with Polymorphism (verified 2026-07-26)
- [Mockito — Compatibility matrix](https://github.com/mockito/mockito/wiki/What%27s-new-in-Mockito-2#incompatible-changes) — Java version requirements and known limitations (verified 2026-07-26)
- [JUnit 5 — Migration guide from JUnit 4](https://junit.org/junit5/docs/current/user-guide/#migrating-from-junit4) — if tests use `@Rule` patterns that need updating (verified 2026-07-26)
- [OCI Functions FDK for Java](https://github.com/fnproject/fdk-java) — FDK lifecycle reference: `@FnConfiguration`, handler signatures, hot functions (verified 2026-07-26)
- [Standing clean-code rules](../../instructions/java-functions-clean-code.instructions.md) — auto-applied to `src/main/java` (verified 2026-07-26)
- [Testing rules](../../instructions/java-functions-testing.instructions.md) — test parity and JVM guard (verified 2026-07-26)
- [Project structure rules](../../instructions/java-functions-project-structure.instructions.md) — package taxonomy (verified 2026-07-26)
