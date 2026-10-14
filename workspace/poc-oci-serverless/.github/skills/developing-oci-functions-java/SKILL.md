---
name: developing-oci-functions-java
description: Develops, tests, and deploys serverless Java functions with OCI Functions Java FDK (Fn Project) v1.0.x/1.1.x. Use when building Java functions for OCI serverless architectures.
---

## Version Context

**Technology**: Fn Java FDK (Function Development Kit for Java)
**Target Version**: v1.0.186 (project baseline) / v1.1.11 (latest)
**Release Date**: 2024-ongoing (v1.1.11 released ~2025)
**Support Status**: Active
**Runtime**: Java 11+ (Java 17 recommended for OCI)
**Platform**: OCI Functions (Oracle Cloud Infrastructure)

**Breaking Changes in v1.1.x**:
- `fn-events` module added (new typed API Gateway support via `APIGatewayFunction`)
- `fn-events-testing` module added for API Gateway test simulation
- Docker base images updated to newer JDK versions

**Deprecations**:
- None significant between 1.0.x → 1.1.x (additive release)

⚠️ **CRITICAL — Agent Warning**:
This skill targets Fn Java FDK v1.0.186+ / v1.1.11. Hot function model means JVM persists between invocations — `@FnConfiguration` runs ONCE, handler runs per-event. Never assume fresh state per invocation. Always use Resource Principal for OCI authentication — never API keys.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Cross-service integration examples
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Function Entry Point in `func.yaml`** — `cmd: ClassName::methodName`. Without it, container starts but can't route events → 502
- **OCI SDK Client init in `@FnConfiguration`** — Hot function JVM persists. Per-invocation init is 10-100x slower
- **Resource Principal Authentication** — Only auth method. Dynamic Groups + IAM Policies grant permissions automatically
- **InputEvent for raw access, POJO for typed** — InputEvent for headers/context, POJO for automatic JSON deserialization
- **Structured JSON logging to stderr** — stdout consumed by FDK. Use stderr for application logs

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Handler method signature style** — `void`, `String`, `OutputEvent`, or typed POJO return
- **State initialization strategy** — `@FnConfiguration` (static init) vs lazy init (first invocation)
- **fn-events vs raw handler for API Gateway** — fn-events for typed request/response, raw for custom protocols

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Hardcoded API keys** — Security vulnerability. Resource Principal is the only supported method
- **Mutable shared state between invocations** — Hot function reuse means state leaks between requests
- **Consuming InputEvent body twice** — InputStream is single-read. Second read returns empty
- **Heavy initialization in handler** — Wastes warm container benefit. Use `@FnConfiguration`
- **Sharing function class with test ClassLoader** — FnTestingRule uses isolated ClassLoader. Static state not shared
- **Blocking thread pool in function** — Single-threaded model. Blocking causes timeout with no error

---

## Integration Patterns

For complete integration code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Summary of integrations**:
- **OCI Functions ↔ API Gateway (fn-events)** — Typed request/response mapping with APIGatewayFunction
- **OCI Functions ↔ Vault** — Secret retrieval during init for external service credentials
- **OCI Functions ↔ Object Storage** — Read/write files with SDK client initialized in `@FnConfiguration`
## Verification Loop

The agent MUST execute after each code generation:

### 1. Build & Compile
```bash
mvn clean package -DskipTests
# Exit code: 0 (success) | 1 (compilation/test failure)
```
**Expected output**: `BUILD SUCCESS`, `target/*.jar` created
**Exit code**: 0

### 2. Unit Tests
```bash
mvn clean test
# Exit code: 0 (all tests passed) | 1 (test failure)
```
**Expected output**: `BUILD SUCCESS`, `Tests run: N, Failures: 0, Errors: 0`
**Exit code**: 0

### 3. Docker Build
```bash
docker build -t my-function:latest .
# Exit code: 0 (success) | 1 (build error)
```
**Expected output**: `Successfully built <image-id>`
**Exit code**: 0

### 4. Local Invocation (Fn CLI)
```bash
fn start &
fn deploy --app myapp --local
# Exit code: 0 (success) | 1 (build/push/create error)
echo '{"action":"hello"}' | fn invoke myapp my-function
# Exit code: 0 (success) | 1 (invocation error)
```
**Expected output**: JSON response from function
**Exit code**: 0

### 5. Deploy to OCI
```bash
fn deploy --app <app-name>
# Exit code: 0 (success) | 1 (build/push/create error)
```
**Expected output**: `Deploying my-function to app: <app-name>` followed by image push confirmation
**Exit code**: 0

**Troubleshooting**:
- `ClassNotFoundException` at runtime → Docker build missing dependency JARs; check `dependency:copy-dependencies` step
- `BmcException` 401/403 → Dynamic Group policy misconfiguration; verify IAM policies
- OOM / timeout → Increase `memory` or `timeout` in `func.yaml`
- `IllegalStateException` on body read → InputEvent body consumed twice; use combined binding

---

## Quick Reference

**Most used commands**:
```bash
# Initialize new function
fn init --runtime java --trigger http my-function

# Build locally
mvn clean package -DskipTests

# Run tests
mvn clean test

# Build Docker image
docker build -t my-function:latest .

# Deploy to OCI
fn deploy --app <app-name>
```

**Essential patterns**:
```java
// One-time init pattern (FDK v1.0.186+)
@FnConfiguration
public void configure(RuntimeContext ctx) {
    var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    this.client = ObjectStorageClient.builder().build(provider);
}

// Stateless handler pattern
public ApiResponse handleRequest(ApiRequest request) {
    return processRequest(request, client);
}
```

**Maven dependencies**:
```xml
<properties>
    <fdk.version>1.0.186</fdk.version>
    <oci.sdk.version>3.36.0</oci.sdk.version>
</properties>

<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-bom</artifactId>
            <version>${oci.sdk.version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <!-- Fn FDK Core -->
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>api</artifactId>
        <version>${fdk.version}</version>
    </dependency>
    <!-- OCI SDK (via BOM) -->
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-common</artifactId>
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-objectstorage</artifactId>
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-secrets</artifactId>
    </dependency>
    <!-- Testing -->
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>testing-core</artifactId>
        <version>${fdk.version}</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>testing-junit4</artifactId>
        <version>${fdk.version}</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>junit</groupId>
        <artifactId>junit</artifactId>
        <version>4.13.2</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

**Performance baseline**:
| Metric | Value |
|--------|-------|
| Cold Start | ~3-8 seconds (JVM + class loading + @FnConfiguration) |
| Warm Invocation | ~5-50ms (hot function reuse) |
| Memory | 128MB-2048MB (default 256MB) |
| Timeout | 30-300 seconds |
| Max Payload | 6MB request/response body |
| Concurrency | 1 invocation per instance (scale out) |

**Security hardening checklist**:
- [ ] Resource Principal (never API keys)
- [ ] Dynamic Group with specific `matching_rule` (not `ALL {true}`)
- [ ] IAM Policy least-privilege
- [ ] Secrets in OCI Vault (not in config vars for sensitive data)
- [ ] Private subnet for function network access
- [ ] Docker image scan before OCIR push
- [ ] `@JsonIgnoreProperties(ignoreUnknown = true)` on all input POJOs
- [ ] Input validation in handler (null checks, bounds)

---

## External Resources

### Official Documentation
- [FDK Java GitHub Repository](https://github.com/fnproject/fdk-java) — Primary source (v1.1.11)
- [Function Configuration Guide](https://github.com/fnproject/fdk-java/blob/master/docs/FunctionConfiguration.md)
- [Data Binding Guide](https://github.com/fnproject/fdk-java/blob/master/docs/DataBinding.md)
- [Testing Functions Guide](https://github.com/fnproject/fdk-java/blob/master/docs/TestingFunctions.md)
- [fn-events Module](https://github.com/fnproject/fdk-java/blob/master/fn-events/README.md)
- [Fn Project Docs](https://github.com/fnproject/docs)

### OCI Integration
- [OCI Functions Concepts](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsconcepts.htm)
- [Accessing OCI Resources from Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm)
- [OCI SDK for Java](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/javasdk.htm)

### Examples
- [API Gateway Function Example](https://github.com/fnproject/fdk-java/tree/master/examples/apigateway-event)
- [Connector Hub (Monitoring)](https://github.com/fnproject/fdk-java/tree/master/examples/connectorhub-monitoring)
- [Connector Hub (Streaming)](https://github.com/fnproject/fdk-java/tree/master/examples/connectorhub-streaming)
- [OCI Notifications Example](https://github.com/fnproject/fdk-java/tree/master/examples/notifications)

### API References
- [RuntimeContext API](https://github.com/fnproject/fdk-java/blob/master/api/src/main/java/com/fnproject/fn/api/RuntimeContext.java)
- [InputEvent Interface](https://github.com/fnproject/fdk-java/blob/master/api/src/main/java/com/fnproject/fn/api/InputEvent.java)
- [OutputEvent Interface](https://github.com/fnproject/fdk-java/blob/master/api/src/main/java/com/fnproject/fn/api/OutputEvent.java)
- [FDK Docker Images](https://hub.docker.com/r/fnproject/fn-java-fdk)
- [FDK Releases](https://github.com/fnproject/fdk-java/releases)
