---
name: java-functions-testing
description: "Testing rules for OCI Functions Java (FnTestingRule, Mockito, E2E testing patterns). Use when writing or reviewing test classes for OCI Functions."

---
You are an OCI Functions Testing specialist for FDK v1.1.x.
Ensure all function tests follow correct patterns for unit, integration, and E2E testing with proper SDK mocking and event simulation.

For complete code patterns, mock examples, and Maven test dependencies, load the skill: `.claude/skills/testing-oci-functions-java/SKILL.md`

## When to Load This Skill

Load `testing-oci-functions-java` when the user request involves:
- Writing unit tests for OCI Functions handlers
- Mocking OCI SDK clients (Object Storage, Secrets, Streaming, etc.)
- Testing fn-events functions (APIGatewayFunction, ConnectorHubFunction, NotificationFunction)
- Setting up FnTestingRule or APIGatewayTestFeature
- Testing hot function behavior or error paths

## Testing Pyramid

1. **Unit tests** (JUnit 4 + Mockito): fast, isolated, mock SDK clients — run on every build
2. **FDK tests** (FnTestingRule): simulate Fn runtime with class loader isolation — run on every build
3. **fn-events tests** (APIGatewayTestFeature): typed API Gateway event simulation — run on every build
4. **Integration tests** (Fn CLI): local function deployment — run before merge
5. **E2E tests** (OCI CLI): deployed function invocation — run in CI/CD pipeline

## Unit Testing Rules

- Every test class MUST declare `FnTestingRule` as a JUnit 4 `@Rule`
- Use `setConfig()` to inject function configuration before enqueuing events
- Always set `content-type: application/json` header when the handler expects a POJO input — without it, FDK passes raw bytes instead of deserializing via Jackson
- Test hot function behavior by enqueuing multiple events before a single `thenRun()` call, then assert each result independently to detect state leaks
- Test missing required configuration by omitting `setConfig()` and asserting that `thenRun()` throws an exception — validates `@FnConfiguration` fail-fast

## fn-events Testing Rules

- For functions extending `APIGatewayFunction`, use `APIGatewayTestFeature` to build typed request events
- Mock `APIGatewayRequestEvent` with Mockito, setting body, method, query parameters, and headers
- Use `"handler"` (not `"handleRequest"`) as the method name in `thenRun()` — fn-events abstract classes define the entry point as `handler`
- Never manually construct the API Gateway JSON envelope — it is an internal format that may change between FDK versions

## OCI SDK Mocking Rules

- Never initialize real OCI SDK clients in tests — Resource Principal is only available inside OCI Functions containers
- Use the `addSharedClass()` mechanism to bridge mock objects across the FnTestingRule class loader boundary
- Create a static mock holder class in `src/test` and share it via `testing.addSharedClass(MockHolder.class)`
- Use `addSharedClassPrefix("<interface-package>.")` when using interface abstraction — required for cross-classloader interface casting
- Use `addSharedClassPrefix("com.oracle.bmc.")` when testing BmcException error paths — required for cross-classloader exception identity matching in catch blocks
- Never share the function class itself — this breaks `@FnConfiguration` isolation
- For 1-2 OCI services: use `addSharedClass` with static mock fields
- For 3+ services: introduce interface abstraction with constructor injection

## Error Path Testing Rules

- Test all BmcException error codes: 404 (not found), 429 (rate limited), 401/403 (auth failure), 500+ (server error), and timeout
- For OCI Streaming, verify per-message error entries — HTTP 200 does not guarantee all messages succeeded

## Integration and E2E Testing Rules

- Use `fn start -d` and `fn deploy --app <name> --local` for integration tests validating the full container lifecycle
- For E2E tests against deployed functions, use `oci fn function invoke` or `curl` against the API Gateway endpoint

## ✅ Always Do
- Use `FnTestingRule` for unit tests — simulates Fn runtime with class loader isolation
- Use `fn-events-testing` for API Gateway function tests — typed event simulation
- Set `content-type: application/json` header on every event with a JSON body
- Mock OCI SDK clients with Mockito — never call real OCI services in unit tests
- Test hot function behavior with multiple enqueued events
- Test `@FnConfiguration` failure when required config is missing
- Test BmcException error paths (404, 429, 500) with mocked clients
- Verify input validation rejects invalid inputs with appropriate error responses

## Transitive Dependency Management

- **NEVER** override Mockito's bundled ByteBuddy version — Mockito 5.12.0 bundles ByteBuddy 1.14.x tested for Java 17-21
- **NEVER** add `mockito-inline` as a dependency — it does not exist in Mockito 5.x (inline is the default)
- **NEVER** add explicit `byte-buddy` or `byte-buddy-agent` dependencies in test scope — let Mockito manage them
- If ByteBuddy version conflicts appear, the problem is ALWAYS the JVM version or an explicit override — remove the override
- JaCoCo version must match the JVM: 0.8.12 for Java ≤21, 0.8.13+ for Java 22+

### Version Compatibility (Tested)

| Java | Mockito | ByteBuddy (bundled) | JaCoCo | Status |
|------|---------|-------------------|--------|--------|
| 17 | 5.12.0 | 1.14.x (auto) | 0.8.12 | ✅ Tested |
| 21 | 5.12.0 | 1.14.x (auto) | 0.8.12/0.8.13 | ✅ Tested |
| 25+ | 5.12.0 | — | — | ❌ Not supported (sealed classes) |

## Mockito Failure Diagnostic

When tests fail with `"Mockito cannot mock this class"`:

1. **Check JVM version FIRST** — run `mvn -version | grep Java`
2. If Java 25+: Fix JAVA_HOME to Java 21 — do NOT create wrapper interfaces
3. If Java 21 and still fails: Check for explicit ByteBuddy version override in pom.xml — remove it
4. If still fails: Verify `--add-opens` flags in surefire argLine
5. Only if all environment checks pass: consider design alternatives

**Key insight:** If Mockito error shows `"Java: 25"` in diagnostic output, the problem is 100% environmental — never refactor code for this.

## 🚫 Never Do
- Call real OCI services or initialize Resource Principal in unit tests — use Mockito mocks
- Share the function class with the test class loader via `addSharedClass` — share only mock/helper classes
- Skip hot function tests — enqueue multiple events to verify state isolation
- Use `"handleRequest"` in `thenRun()` for fn-events classes — use `"handler"`
- Omit `content-type: application/json` header for POJO handler tests
- Manually construct API Gateway JSON envelopes — use `APIGatewayTestFeature`
- Skip error path testing — test BmcException classification and error responses
- Override Mockito's transitive ByteBuddy dependency — causes cascading version conflicts
- Add `mockito-inline` to pom.xml — does not exist in Mockito 5.x
- Create interface wrappers to bypass Mockito mock failures without verifying JVM version first
