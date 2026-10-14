---
name: refactoring-oci-java
description: Refactors OCI Functions Java code for readability with Extract Method, SOLID decomposition, DRY, and behavior-preserving safety (tests stay green). Use when asked to refactor, clean up, improve readability/legibilidade, decompose a god class, extract methods, or apply clean code / SOLID to existing Java.
---

# Refactoring OCI Java for Clean Code / SOLID

Procedural, behavior-preserving refactoring of existing Java. The standing checklist lives in the
instruction `.github/instructions/java-functions-clean-code.instructions.md` (auto-applied to
`src/main/java`); this skill is the step-by-step recipe with examples. Golden rule: **behavior stays
identical** — same outputs, status codes, log texts, side-effect order — and the existing test suite
stays green.

## Safe-Refactor Recipe

1. **Baseline green.** Establish the JVM (Corretto 21 — Java 25+ breaks Mockito) and run the suite
   BEFORE touching code, so you have a parity reference:
   ```bash
   export JAVA_HOME=$(/usr/libexec/java_home -v 21)
   mvn -f services/<func>/pom.xml test
   ```
2. **Map test coupling first.** Note what tests depend on: package-private test constructors, the
   `handler(...)` signature, package-private methods called directly. These MUST NOT change (or you
   relocate the test — step 5).
3. **Identify smells:** long method (>~40 lines), block-titling comments, deep nesting, duplicated
   logic, magic-string/status classification, a static utility holding multiple concerns, long
   parameter lists / local-variable sprawl.
4. **Extract in small steps**, preserving public/test signatures and exact exception types/messages.
   One smell at a time; recompile between steps.
5. **Run tests after each step** to prove parity. Relocate unit tests to the class that now owns the
   logic; add focused tests for newly extracted classes.

## Before → After (from this repo)

- **God class → thin dispatcher.** A 578-line `RestProxyFunction` doing routing + store-id resolution +
  mapping + marshalling + span boilerplate + error mapping + metrics became a ~230-line dispatcher that
  routes via `Route` and delegates to collaborators in `route/ transform/ web/ handler/ obs/`.
- **Long method → named steps.** `configure()`/`handler()` were split with Extract Method into
  `readProxyConfig`, `buildHttpClient`, `loadOAuthSecrets`, `beginRequest`, `dispatch`,
  `recordTelemetry`, `populateResponseMetadata` — each method reads as one intent.
- **Repeated span scaffolding → `TracedCall`.** The open-span / try / end-span(null) / catch /
  end-span(error) / rethrow block (5× copies) collapsed into `TracedCall.run(name, peer, attrs, callable)`.
- **Magic-string classification → `ErrorMapper`.** The `if message.startsWith("Falha na chamada HTTP:")`
  chain moved into a dedicated `web/ErrorMapper` that maps exceptions → HTTP responses.
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

## Exit Checklist

- [ ] Public method signatures and package-private test constructors unchanged (or tests relocated).
- [ ] Exact exception types/messages, log texts, status codes, and side-effect order preserved.
- [ ] Each long method now reads as a short sequence of named steps; no duplicated scaffolding.
- [ ] Business logic delegated out of the handler into the package taxonomy.
- [ ] Full suite green (`mvn test`) — proves identical behavior.
- [ ] No speculative abstraction / single-use indirection added.

## References

- Standing checklist: `.github/instructions/java-functions-clean-code.instructions.md`
- Test parity + JVM guard: `.github/instructions/java-functions-testing.instructions.md`, `.github/instructions/java-environment-validation.instructions.md`
- Package layout: `.github/instructions/java-functions-project-structure.instructions.md`
