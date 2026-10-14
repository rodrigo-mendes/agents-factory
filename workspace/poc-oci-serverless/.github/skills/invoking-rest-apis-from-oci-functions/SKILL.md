---
name: invoking-rest-apis-from-oci-functions
description: Invokes REST APIs (OCI services, other Functions, or external third-party APIs) from OCI Functions written in Java with OCI SDK v3.x+ and Java 17. Use when calling REST endpoints from Functions.
---

## Version Context

**Technology**: OCI Functions Java — REST API Invocation Patterns
**OCI Java SDK**: v3.36+ (project minimum) / v3.86.1 (latest)
**Java Runtime**: Java 17 (Docker: `fnproject/fn-java-fdk:jre17-latest`)
**FDK**: fnproject FDK for Java v1.0.x
**Support Status**: Active — General Availability
**License**: UPL 1.0 / Apache 2.0 (dual license)

**Key Capabilities**:
- OCI SDK typed clients with automatic HTTP signing, retry, and circuit breaker
- Function-to-function invocation via `FunctionsInvokeClient` (sync and detached)
- External REST API calls via `java.net.http.HttpClient` (Java 17 built-in, HTTP/2)
- Resource Principal authentication (managed identity — only auth method for Functions)
- Configurable `RetryConfiguration` with exponential backoff + jitter
- Per-request timeout and retry overrides

**Critical Defaults to Override**:
- SDK default read timeout: **60s** — conflicts with default function timeout of **30s**
- SDK default retry: **8 attempts, 30s max delay** — may exceed function budget
- No request-level timeout on `java.net.http.HttpClient` by default

⚠️ **CRITICAL — Agent Warning**:
This skill targets OCI Java SDK v3.x+ with Java 17 runtime on OCI Functions.
SDK read timeout (60s) EXCEEDS the default function timeout (30s) — always configure explicit timeouts.
Never use API keys, config files, or instance principal in Functions — Resource Principal only.
All outbound HTTP calls MUST have explicit timeouts shorter than the function timeout.

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
- **Resource Principal Authentication** — Only auth method in Functions. Never use API keys or config files
- **OCI SDK Client init in `@FnConfiguration`** — Hot function JVM persists. Per-invocation init wastes ~50-200ms per call
- **Explicit timeouts on all SDK clients** — SDK read timeout MUST be < function timeout. Default infinite timeout → 300s function timeout hit
- **BmcException handling with status code classification** — 429 (throttle/retry), 404 (not found), 5xx (transient/retry), 4xx (client error/fail)
- **Structured JSON logging** — Function stdout goes to OCI Logging. JSON enables filtering by correlation ID

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **OCI SDK Client vs `HttpClient` vs Raw HTTP with RequestSigner** — SDK for OCI services, HttpClient for external REST, RequestSigner for advanced OCI calls
- **Sync vs Detached function-to-function invocation** — Sync for request-response chains, Detached for fire-and-forget (max 720s)

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Creating HTTP clients in handler** — Connection pool exhaustion under burst load
- **API keys or config file auth** — No `~/.oci/config` in container. Security vulnerability if embedded
- **SDK read timeout > function timeout** — Function killed mid-request, no cleanup, no error response
- **Blindly retrying all BmcException errors** — 400/401/403/404 are permanent. Only retry 429/5xx
- **`setEndpoint()` on shared client in handler** — Race condition in concurrent invocations
- **Logging sensitive data from API responses** — PII/credentials in OCI Logging violate compliance

---

## Integration Patterns

For complete integration code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Summary of integrations**:
- **OCI Functions ↔ Object Storage** — SDK client for read/write with Resource Principal
- **OCI Functions ↔ Vault** — Secret retrieval for external API credentials (OAuth2 client secrets)
- **OCI Functions ↔ External REST APIs** — HttpClient with OAuth2 Client Credentials flow, timeout budget
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
**Expected output**: `Tests run: N, Failures: 0, Errors: 0`
**Exit code**: 0

### 3. Deploy Function
```bash
fn -v deploy --app <app-name>
```
**Expected output**: `Updating function <fn-name> using image...`

### 4. Invoke Test
```bash
echo '{"requestId":"test-001","query":"hello"}' | fn invoke <app-name> <function-name>
# Exit code: 0 (success) | 1 (invocation error)
```
**Expected output**: Valid JSON response with status 200

### 5. Log Verification
```bash
oci logging search --search-query 'search "<log-group-ocid>/<log-ocid>" | sort by datetime desc | limit 10'
```
**Expected output**: Log entries without timeout or auth errors

### 6. Function Timeout Check
```bash
fn inspect function <app-name> <function-name>
# Exit code: 0 (success) | 1 (not found)
```
**Expected output**: `"timeout": 30` (or configured value) — verify SDK timeouts are below this

**Troubleshooting**:
- `FileNotFoundException: ~/.oci/config` → Use `ResourcePrincipalAuthenticationDetailsProvider`, not `ConfigFileAuthenticationDetailsProvider`
- `BmcException 401/403` → IAM dynamic group or policy misconfigured — verify `allow dynamic-group` statements
- `Function Invoke Timedout (503)` → SDK read timeout exceeds function timeout — reduce `readTimeoutMillis`
- `Connection refused` on external API → Function in VCN needs NAT Gateway for internet egress

---

## Quick Reference

**Maven dependencies** (add as needed):
```xml
<!-- Function-to-function invocation -->
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-functions</artifactId>
</dependency>

<!-- Object Storage access -->
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-objectstorage</artifactId>
</dependency>

<!-- Vault Secrets access -->
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-secrets</artifactId>
</dependency>

<!-- java.net.http.HttpClient — NO dependency needed (Java 17 built-in) -->
```

**IAM policies** (least-privilege):
```
# Function-to-function invocation
allow dynamic-group <dg-name> to use fn-invocation in compartment <compartment>
allow dynamic-group <dg-name> to read fn-function in compartment <compartment>

# Object Storage
allow dynamic-group <dg-name> to manage objects in compartment <compartment>

# Vault Secrets
allow dynamic-group <dg-name> to read secret-bundles in compartment <compartment>
```

**Essential patterns**:
```java
// Auth — always Resource Principal
var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();

// Timeout — always below function timeout
ClientConfiguration.builder().readTimeoutMillis(15000).build();

// Retry — 3 attempts max for 30s functions
RetryConfiguration.builder()
    .terminationStrategy(new MaxAttemptsTerminationStrategy(3))
    .delayStrategy(new ExponentialBackoffDelayStrategyWithJitter(5000))
    .build();

// External call — always set request timeout
HttpRequest.newBuilder().timeout(Duration.ofSeconds(10)).build();
```

**Performance baseline**:
| Operation | Cold Start | Warm (Hot Function) |
|-----------|-----------|-------------------|
| OCI SDK Client init | 500-2000ms | Reused (0ms) |
| OCI SDK API call | — | 10-100ms |
| HttpClient init | 50-100ms | Reused (0ms) |
| External REST call | — | 5-5000ms (varies) |
| Function-to-function | — | 50-200ms + target time |

**Limits**:
| Aspect | Limit |
|--------|-------|
| Function timeout | 30-300s (default 30s) |
| InvokeFunction payload | 6MB max |
| SDK default connection pool | 50 async threads |
| SDK default retry | 8 attempts, 30s max delay |
| SDK default read timeout | 60s ⚠️ |

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
- [OCI Functions API Reference](https://docs.oracle.com/en-us/iaas/api/#/en/functions/20181201/)
- [InvokeFunction API](https://docs.oracle.com/en-us/iaas/api/#/en/functions/20181201/Function/InvokeFunction)
- [Java 17 HttpClient API](https://docs.oracle.com/en/java/javase/17/docs/api/java.net.http/java/net/http/HttpClient.html)

### OCI SDK Source
- [OCI Java SDK Repository](https://github.com/oracle/oci-java-sdk) (v3.86.1)
- [ClientConfiguration.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-common/src/main/java/com/oracle/bmc/ClientConfiguration.java)
- [RetryConfiguration.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-common/src/main/java/com/oracle/bmc/retrier/RetryConfiguration.java)
- [BmcException.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-common/src/main/java/com/oracle/bmc/model/BmcException.java)
- [FunctionsInvokeClient.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-functions/src/main/java/com/oracle/bmc/functions/FunctionsInvokeClient.java)
- [DefaultRetryCondition.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-common/src/main/java/com/oracle/bmc/retrier/DefaultRetryCondition.java)
- [HTTP Client Choices](https://github.com/oracle/oci-java-sdk/tree/master/bmc-common-httpclient-choices)

### Samples & Examples
- [Oracle Functions Samples](https://github.com/oracle-samples/oracle-functions-samples)
- [Object Storage Put (Java)](https://github.com/oracle-samples/oracle-functions-samples/blob/master/samples/oci-objectstorage-put-object-java/src/main/java/com/example/fn/ObjectStoragePutObject.java)
- [InvokeFunctionExample.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/InvokeFunctionExample.java)
- [API Gateway Authorizer (IDCS)](https://github.com/oracle-samples/oracle-functions-samples/blob/master/samples/oci-apigw-authorizer-idcs-java/src/main/java/com/example/fn/AuthFunction.java)

### Related Skills
- [OCI Vault Security](../../skills/designing-oci-vault-security/SKILL.md) — secrets management for API credentials
- [OCI Functions Serverless](../../skills/architecting-oci-serverless/SKILL.md) — architecture patterns
- [OCI Functions Terraform](../../skills/provisioning-oci-functions/SKILL.md) — infrastructure provisioning
- [OCI Network Architecture](../../skills/designing-oci-networking/SKILL.md) — VCN, NAT Gateway for egress
