---
name: testing-oci-functions-java
description: "Tests OCI Functions Java handlers with FDK v1.1.x testing framework (FnTestingRule, APIGatewayTestFeature, Mockito). Use when writing unit tests, mocking OCI SDK services, or validating fn-events functions."
---

## Version Context

**Technology**: Fn Java FDK Testing Framework
**Target Version**: v1.1.11 (testing-core, fn-events-testing)
**Runtime**: Java 17, JUnit 4.13+, Mockito 5.x
**Support Status**: Active
**Platform**: OCI Functions (Oracle Cloud Infrastructure)

**Key Modules**:
- `testing-core` — `FnTestingRule` (JUnit 4 Rule, class loader isolation)
- `fn-events-testing` — `APIGatewayTestFeature` (typed API Gateway testing)

**Critical Constraint**: `FnTestingRule` uses **separate class loaders per invocation**. Static state in the function class is NOT shared with the test class. Mock injection requires `addSharedClass()` on helper classes only.

⚠️ **Version Lock**: FDK testing uses JUnit 4 Rules (`@Rule`). JUnit 5 requires `junit-vintage-engine` adapter.

---

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory testing patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Strategy choices requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Testing anti-patterns with fixes
- **[OCI Service Mocking](./blueprints/oci-service-mocking.md)** — Complete mock examples per service
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Agent evaluation test scenarios
- **[Verification Loop](#verification-loop)** — Test execution commands
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

See external blueprint files for detailed patterns:
- [Always Do Patterns](./blueprints/always-do-patterns.md)
- [Ask First Decisions](./blueprints/ask-first-decisions.md)
- [Never Do Patterns](./blueprints/never-do-patterns.md)

---

## Integration Patterns

For complete mock setup examples per OCI service, see [OCI Service Mocking](./blueprints/oci-service-mocking.md).

**Summary of covered integrations**:
- **Object Storage** — mock getObject, putObject, listObjects
- **Vault / Secrets** — mock getSecretBundle with Base64 content
- **Streaming** — mock putMessages with per-entry error checking
- **Notifications (ONS)** — mock publishMessage
- **Queue** — mock putMessages/getMessages
- **Monitoring** — mock postMetricData

**Error Path Testing Pattern** (applies to all services):

```java
// Test BmcException handling
when(mockClient.getObject(any()))
    .thenThrow(new BmcException(404, "ObjectNotFound", "Not found", "opc-req-1"));
testing.givenEvent().withHeader("content-type", "application/json")
    .withBody("{\"action\":\"read\",\"objectName\":\"missing.json\"}").enqueue();
testing.thenRun(FileFunction.class, "handleRequest");
FnResult result = testing.getOnlyResult();
assertTrue(result.getBodyAsString().contains("404"));
```

---

## Verification Loop

### 1. Unit Tests
```bash
mvn clean test
```
**Expected**: `BUILD SUCCESS, Tests run: N, Failures: 0, Errors: 0` | **Exit code**: 0

### 2. Specific Test
```bash
mvn test -Dtest=OrderFunctionTest#testProcessOrder
```
**Expected**: `Tests run: 1, Failures: 0` | **Exit code**: 0

### 3. Integration (fn CLI)
```bash
fn start -d && fn deploy --app testapp --local && \
  echo '{"action":"hello"}' | fn invoke testapp my-function && fn stop
```
**Expected**: Function JSON response | **Exit code**: 0

### 4. Docker Build
```bash
docker build -t my-function:test . && docker run --rm my-function:test ls /function/app/
```
**Expected**: JAR files listed | **Exit code**: 0

**Troubleshooting**:
- `Resource Principal not available` → You're calling real SDK in test. Use mock.
- `ClassNotFoundException: MockOciClients` → Missing `addSharedClass()` in test setup.
- `null` POJO in handler → Missing `content-type: application/json` header.
- `BmcException caught by generic Exception handler` → Missing `addSharedClassPrefix("com.oracle.bmc.")` in test setup.

---

## Coverage Measurement

⚠️ **JaCoCo Limitation**: FnTestingRule executes function handlers in an isolated child classloader. JaCoCo's agent only instruments classes loaded by the main test classloader, so **function handler coverage will report 0%** even when all paths are tested.

**What works**:
- Model/POJO classes — tested directly from the main classloader → accurate coverage
- Utility/helper classes — tested directly → accurate coverage

**What doesn't work**:
- Function handler classes (loaded by FnTestingRule's child classloader) → reports 0%

**Recommendation**: Exclude function handler classes from JaCoCo enforcement. Rely on test pass/fail to verify handler coverage.

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.12</version>
    <executions>
        <execution>
            <goals><goal>prepare-agent</goal></goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals><goal>report</goal></goals>
        </execution>
    </executions>
    <configuration>
        <excludes>
            <!-- Exclude function handlers (unmeasurable due to FnTestingRule classloader) -->
            <exclude>com/mycompany/functions/**/*Function.class</exclude>
            <!-- Exclude OCI SDK client wrappers (require Resource Principal) -->
            <exclude>com/mycompany/functions/**/Oci*Client.class</exclude>
        </excludes>
    </configuration>
</plugin>
```

---

## Maven Dependencies

```xml
<properties>
    <fdk.version>1.1.11</fdk.version>
    <mockito.version>5.11.0</mockito.version>
</properties>

<!-- FDK Testing -->
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

<!-- fn-events-testing (FDK 1.1.x) -->
<dependency>
    <groupId>com.fnproject.fn</groupId>
    <artifactId>fn-events-testing</artifactId>
    <version>${fdk.version}</version>
    <scope>test</scope>
</dependency>

<!-- JUnit 4 + Mockito -->
<dependency>
    <groupId>junit</groupId>
    <artifactId>junit</artifactId>
    <version>4.13.2</version>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-core</artifactId>
    <version>${mockito.version}</version>
    <scope>test</scope>
</dependency>
```

---

## External Resources

- [Testing Functions (Official)](https://github.com/fnproject/fdk-java/blob/master/docs/TestingFunctions.md) — FnTestingRule guide
- [fn-events-testing](https://github.com/fnproject/fdk-java/tree/master/fn-events-testing) — APIGatewayTestFeature
- [API Gateway Test Example](https://github.com/fnproject/fdk-java/tree/master/examples/apigateway-event) — Complete working test
- [Data Binding](https://github.com/fnproject/fdk-java/blob/master/docs/DataBinding.md) — POJO serialization rules
- [Function Configuration](https://github.com/fnproject/fdk-java/blob/master/docs/FunctionConfiguration.md) — @FnConfiguration lifecycle
- [OCI Resource Principals](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm) — Auth in Functions
