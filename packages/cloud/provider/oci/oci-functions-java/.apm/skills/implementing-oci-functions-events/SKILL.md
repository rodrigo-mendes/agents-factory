---
name: implementing-oci-functions-events
description: Implements event-driven OCI Functions with typed abstractions (API Gateway, Service Connector Hub, Notifications) using fn-events v1.1.x. Use when building event-driven function handlers.
---

## Version Context

**Technology**: Fn Java FDK — fn-events module
**Target Version**: v1.1.11 (fn-events requires FDK 1.1.x+)
**Release Date**: 2025 (v1.1.11 latest stable)
**Support Status**: Active
**Runtime**: Java 11+ (Java 17 recommended)
**Platform**: OCI Functions (Oracle Cloud Infrastructure)

**Breaking Changes from FDK 1.0.x → 1.1.x**:
- fn-events module introduced — not available in 1.0.x
- Entry point changes from `handleRequest` to `handler` when using abstract classes
- `func.yaml` `cmd` must reference `::handler` (not `::handleRequest`)
- Return type changes to `APIGatewayResponseEvent<T>` for API Gateway functions
- Handler becomes `void` for ConnectorHub and Notification functions

**Deprecations**:
- Raw manual parsing of API Gateway JSON envelope → use `APIGatewayFunction<Req, Res>`
- Manual base64 decoding of Streaming values → use `StreamingData<T>` auto-decode

⚠️ **CRITICAL — Agent Warning**:
This skill targets fn-events v1.1.x. The module does NOT exist in FDK 1.0.x.
If the project uses FDK 1.0.186, upgrading to 1.1.11 is required before using fn-events.
Do not mix raw `handleRequest` patterns with fn-events abstract classes in the same function.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Cross-service integration examples
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 5 scenarios: typed API Gateway handler, FDK 1.0.x upgrade, batch partial failure, func.yaml mismatch, raw parsing misuse
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Add fn-events Maven dependency** — Without it, `APIGatewayFunction`, `ConnectorHubFunction` etc. are not on classpath → `ClassNotFoundException`
- **Extend typed abstract class** — `APIGatewayFunction<Req, Res>`, `ConnectorHubFunction<T>`, `NotificationFunction`. Override `handler()` not `handleRequest`
- **APIGatewayFunction for API Gateway backends** — Type-safe HTTP request/response with query params, headers, status code control
- **ConnectorHubFunction for Service Connector Hub** — Processes batches from Streaming/Logging/Monitoring sources
- **NotificationFunction for ONS triggers** — Typed `NotificationInput` with subject, message, topic
- **func.yaml `cmd` points to correct class** — Entry point must match the extending class, not inner handler

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Event source type selection** — API Gateway, Connector Hub, or Notifications determines which abstract class to extend
- **ConnectorHubFunction data type** — Generic type `<T>` must match the source event schema
- **Error handling strategy for batch functions** — Fail-fast vs partial processing for ConnectorHub batches
- **API Gateway error response strategy** — HTTP status codes and error body format

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Raw `handleRequest` for API Gateway** — Loses type safety, manual JSON envelope parsing is brittle
- **Manual base64 decode for Streaming events** — ConnectorHubFunction handles decoding automatically
- **Ignoring batch semantics in ConnectorHubFunction** — Single item failure shouldn't drop entire batch
- **Returning values from void handlers** — FDK ignores return value, causes silent data loss
- **Mixing fn-events with raw FDK handlers** — ClassLoader conflicts and undefined routing behavior
- **Non-JSON Queue messages** — fn-events expects JSON deserialization. Binary/text causes parse failures

---

## Integration Patterns

For complete integration code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Summary of integrations**:
- **fn-events ↔ API Gateway** — APIGatewayFunction with deployment route configuration
- **fn-events ↔ Service Connector Hub** — ConnectorHubFunction for Streaming/Logging/Monitoring sources
- **fn-events ↔ Notifications** — NotificationFunction for ONS topic subscriptions
- **fn-events ↔ Service Connector Hub (Monitoring)** — Custom metrics source processing

---

## Verification Loop

The agent MUST execute after each code generation:

### 1. Build
```bash
mvn clean package -DskipTests
# Exit code: 0 (success) | 1 (compilation/test failure)
```
**Expected output**: `BUILD SUCCESS`
**Exit code**: 0

### 2. Unit Tests
```bash
mvn clean test
# Exit code: 0 (all tests passed) | 1 (test failure)
```
**Expected output**: `Tests run: N, Failures: 0, Errors: 0, Skipped: 0`
**Exit code**: 0

### 3. Verify func.yaml Entry Point
```bash
grep "cmd:" func.yaml
# Exit code: 0 (match found) | 1 (no match)
```
**Expected output**: `cmd: com.example.Function::handler` (must end with `::handler`)
**Exit code**: 0

### 4. Build Docker Image
```bash
docker build -t my-event-function:latest .
# Exit code: 0 (success) | 1 (build error)
```
**Expected output**: `Successfully built <image-id>`
**Exit code**: 0

### 5. Deploy to OCI
```bash
fn deploy --app <app-name>
# Exit code: 0 (success) | 1 (build/push/create error)
```
**Expected output**: `Updating function using image <region>.ocir.io/<namespace>/<repo>:<tag>`

### 6. Local Smoke Test (API Gateway functions only)
```bash
fn start &
fn deploy --app myapp --local
# Exit code: 0 (success) | 1 (build/push/create error)
curl -X POST http://localhost:8080/t/myapp/my-function \
# Exit code: 0 (success) | 1 (connection error) | 22 (HTTP error with -f)
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'
```
**Expected output**: JSON response with `statusCode` and `body`

**Troubleshooting**:
- `ClassNotFoundException: com.fnproject.events.*` → Add fn-events dependency to `pom.xml`
- `func.yaml cmd points to ::handleRequest` → Change to `::handler`
- `JsonParseException` on Queue messages → Ensure messages are valid JSON
- `IllegalArgumentException` on Streaming data → Do NOT manually base64 decode (auto-decoded)
- Compile error on handler return type → `ConnectorHubFunction`/`NotificationFunction` handlers must be `void`

---

## Quick Reference

**Essential patterns**:

```java
// API Gateway — typed request/response
public class Fn extends APIGatewayFunction<Req, Res> {
    @Override
    public APIGatewayResponseEvent<Res> handler(APIGatewayRequestEvent<Req> e) {
        return new APIGatewayResponseEvent.Builder<Res>()
            .statusCode(200).body(new Res()).build();
    }
}

// Connector Hub — void batch handler
public class Fn extends ConnectorHubFunction<LoggingData> {
    @Override
    public void handler(ConnectorHubBatch<LoggingData> batch) {
        for (LoggingData log : batch.getBatch()) { process(log); }
    }
}

// Notifications — void single message handler
public class Fn extends NotificationFunction<Payload> {
    @Override
    public void handler(NotificationMessage<Payload> msg) {
        process(msg.getBody());
    }
}
```

**Most used imports**:
```java
// Core abstractions (fn-events v1.1.x)
import com.fnproject.events.APIGatewayFunction;
import com.fnproject.events.ConnectorHubFunction;
import com.fnproject.events.NotificationFunction;

// Input types
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.input.ConnectorHubBatch;
import com.fnproject.events.input.NotificationMessage;
import com.fnproject.events.input.sch.MetricData;
import com.fnproject.events.input.sch.LoggingData;
import com.fnproject.events.input.sch.StreamingData;

// Output types
import com.fnproject.events.output.APIGatewayResponseEvent;

// Test features (fn-events-testing v1.1.x)
import com.fnproject.events.testing.APIGatewayTestFeature;
import com.fnproject.events.testing.ConnectorHubTestFeature;
import com.fnproject.events.testing.NotificationTestFeature;
```

**Compatibility Matrix**:

| Dependency | Min Version | Max Version | Notes |
|------------|-------------|-------------|-------|
| fn-events | 1.1.0 | 1.1.11 | First introduced in 1.1.x |
| fn-events-testing | 1.1.0 | 1.1.11 | Must match fn-events version |
| FDK api | 1.1.0 | 1.1.11 | Must match fn-events version |
| Java | 11 | 21 | JDK 17 recommended |
| Jackson | 2.13 | 2.17+ | JSON serialization |

---

## Development Workflow

```
Function Development Progress:
- [ ] Create func.yaml with cmd entry point
- [ ] Implement @FnConfiguration (cold start init)
- [ ] Implement handler method
- [ ] mvn clean test (exit 0)
- [ ] mvn clean package (exit 0)
- [ ] docker build (exit 0)
- [ ] fn deploy --app <app-name> (exit 0)
- [ ] fn invoke and verify response
```

## External Resources

### Official Documentation
- [fn-events README](https://github.com/fnproject/fdk-java/blob/master/fn-events/README.md) — Module overview and usage (verified 2026-07-26)
- [FDK Java Repository](https://github.com/fnproject/fdk-java) — Source code (v1.1.11) (verified 2026-07-26)
- [FDK Testing Documentation](https://github.com/fnproject/fdk-java/blob/master/docs/TestingFunctions.md) — Testing guide (verified 2026-07-26)

### Examples
- [API Gateway Function Example](https://github.com/fnproject/fdk-java/tree/master/examples/apigateway-event) (verified 2026-07-26)
- [Connector Hub — Monitoring](https://github.com/fnproject/fdk-java/tree/master/examples/connectorhub-monitoring) (verified 2026-07-26)
- [Connector Hub — Logging](https://github.com/fnproject/fdk-java/tree/master/examples/connectorhub-logging) (verified 2026-07-26)
- [Connector Hub — Streaming](https://github.com/fnproject/fdk-java/tree/master/examples/connectorhub-streaming) (verified 2026-07-26)
- [Connector Hub — Queue](https://github.com/fnproject/fdk-java/tree/master/examples/connectorhub-queue) (verified 2026-07-26)
- [Notifications](https://github.com/fnproject/fdk-java/tree/master/examples/notifications) (verified 2026-07-26)

### OCI Service Documentation
- [API Gateway + Functions Backend](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingfunctionsbackend.htm) (verified 2026-07-26)
- [Service Connector Hub Overview](https://docs.oracle.com/en-us/iaas/Content/connector-hub/overview.htm) (verified 2026-07-26)
- [SCH Batch Settings](https://docs.oracle.com/en-us/iaas/Content/connector-hub/overview.htm#batch-settings) (verified 2026-07-26)
- [SCH Monitoring Source](https://docs.oracle.com/en-us/iaas/Content/connector-hub/create-service-connector-monitoring-source.htm) (verified 2026-07-26)
- [SCH Logging Source](https://docs.oracle.com/en-us/iaas/Content/connector-hub/create-service-connector-logging-source.htm) (verified 2026-07-26)
- [SCH Streaming Source](https://docs.oracle.com/en-us/iaas/Content/connector-hub/create-service-connector-streaming-source.htm) (verified 2026-07-26)
- [SCH Queue Source](https://docs.oracle.com/en-us/iaas/Content/connector-hub/create-service-connector-queue-source.htm) (verified 2026-07-26)
- [OCI Notifications Overview](https://docs.oracle.com/en-us/iaas/Content/Notification/Concepts/notificationoverview.htm) (verified 2026-07-26)
- [Notification Function Subscription](https://docs.oracle.com/en-us/iaas/Content/Notification/Tasks/create-subscription-function.htm) (verified 2026-07-26)

### Security
- [SCH Retry Policy](https://docs.oracle.com/en-us/iaas/Content/connector-hub/overview.htm#deactivate) (verified 2026-07-26)
- [SCH Default IAM Policies](https://docs.oracle.com/en-us/iaas/Content/connector-hub/overview.htm#Authenti__default-policies) (verified 2026-07-26)
