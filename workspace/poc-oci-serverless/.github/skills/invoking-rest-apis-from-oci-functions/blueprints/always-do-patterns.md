### ✅ Always Do

## Contents
1. Resource Principal Authentication
2. OCI SDK Client Initialization in @FnConfiguration
3. ClientConfiguration with Timeouts Within Function Budget
4. BmcException Error Handling with Status Code Discrimination
5. External REST API Calls with java.net.http.HttpClient and Explicit Timeout
6. Function-to-Function Invocation via FunctionsInvokeClient

---

**Resource Principal Authentication**: OCI Functions run with Resource Principal — a managed identity provided automatically by the platform. This is the only authentication method available and recommended. Never use API keys, config files, or instance principal.

```java
// ✅ CORRECT: Resource Principal — only auth method for OCI Functions
// OCI SDK v3.x+ — auto-provided via environment variables by the Functions runtime
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;

final ResourcePrincipalAuthenticationDetailsProvider provider =
    ResourcePrincipalAuthenticationDetailsProvider.builder().build();

// All OCI SDK clients accept this provider
ObjectStorageClient osClient = ObjectStorageClient.builder().build(provider);
SecretsClient secretsClient = SecretsClient.builder().build(provider);
FunctionsInvokeClient fnClient = FunctionsInvokeClient.builder().build(provider);
```
**Why it is mandatory**: Functions containers have no `~/.oci/config` and no instance metadata endpoint. Resource Principal tokens are injected via `OCI_RESOURCE_PRINCIPAL_RPST` and `OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM` environment variables.
**Failure if omitted**: `FileNotFoundException` on config file, or security vulnerability if API key is embedded in container image.
**Source**: [Oracle Functions Samples — Object Storage Put](https://github.com/oracle-samples/oracle-functions-samples/blob/master/samples/oci-objectstorage-put-object-java/src/main/java/com/example/fn/ObjectStoragePutObject.java)

---

**OCI SDK Client Initialization in @FnConfiguration**: HTTP clients, OCI SDK clients, and connection pools MUST be initialized in the `@FnConfiguration` method, not in the handler. In hot functions, the JVM persists between invocations — initializing in the handler wastes resources and prevents connection reuse.

```java
// ✅ CORRECT: Initialize all clients once during cold start
// OCI SDK v3.x+ / Java 17 — clients reused across hot invocations
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.objectstorage.ObjectStorageClient;

import java.net.http.HttpClient;
import java.time.Duration;

public class MyFunction {
    private ObjectStorageClient objectStorageClient;
    private HttpClient httpClient;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();

        // OCI SDK client — reused across invocations
        this.objectStorageClient = ObjectStorageClient.builder().build(provider);

        // External HTTP client — connection pool reused in hot function
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .version(HttpClient.Version.HTTP_1_1)
            .build();
    }

    public String handleRequest(String input) {
        // Use pre-initialized clients here
        return "OK";
    }
}
```
**Why it is mandatory**: Creating clients per invocation causes ~50-200ms overhead for TLS handshake and pool creation. In hot functions, this accumulates and can exhaust connections under burst load.
**Failure if omitted**: Connection pool exhaustion, degraded latency, wasted cold-start budget on every invocation.
**Source**: [Oracle Functions Samples](https://github.com/oracle-samples/oracle-functions-samples)

---

**ClientConfiguration with Timeouts Within Function Budget**: The OCI SDK default read timeout is **60s**, but the default function timeout is **30s**. The SDK timeout MUST be configured below the function timeout to allow graceful error handling before the platform kills the function.

```java
// ✅ CORRECT: Timeouts configured within function budget (30s default)
// OCI SDK v3.x+ — ClientConfiguration + RetryConfiguration
import com.oracle.bmc.ClientConfiguration;
import com.oracle.bmc.retrier.RetryConfiguration;
import com.oracle.bmc.waiter.MaxAttemptsTerminationStrategy;
import com.oracle.bmc.waiter.ExponentialBackoffDelayStrategyWithJitter;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();

    // Function-appropriate retry: 3 attempts, max 5s between retries
    RetryConfiguration retryConfig = RetryConfiguration.builder()
        .terminationStrategy(new MaxAttemptsTerminationStrategy(3))
        .delayStrategy(new ExponentialBackoffDelayStrategyWithJitter(5000))
        .retryCondition(e -> e.getStatusCode() == 429
            || e.getStatusCode() >= 500
            || e.isTimeout())
        .build();

    ClientConfiguration clientConfig = ClientConfiguration.builder()
        .connectionTimeoutMillis(5000)   // 5s (default: 10s)
        .readTimeoutMillis(15000)        // 15s (default: 60s) — within 30s function budget
        .retryConfiguration(retryConfig)
        .build();

    this.objectStorageClient = ObjectStorageClient.builder()
        .configuration(clientConfig)
        .build(provider);
}
```
**Why it is mandatory**: If SDK read timeout (60s) exceeds function timeout (30s), the platform kills the function mid-request. The caller receives 503 "Function Invoke Timedout" with no error context. No logging, no cleanup, no graceful degradation.
**Failure if omitted**: Platform kill (502/503 to caller), silent failure, no diagnostic logs.
**Source**: [OCI SDK ClientConfiguration](https://github.com/oracle/oci-java-sdk/blob/master/bmc-common/src/main/java/com/oracle/bmc/ClientConfiguration.java)

---

**BmcException Error Handling with Status Code Discrimination**: Every OCI SDK call can throw `BmcException`. Error handling MUST distinguish retryable errors (429, 5xx) from fatal errors (400, 401, 403, 404). Always log `opcRequestId` for Oracle Support troubleshooting.

```java
// ✅ CORRECT: Discriminate error types in OCI SDK v3.x+ calls
import com.oracle.bmc.model.BmcException;

public String callOciService(String resourceId) {
    try {
        return doOciCall(resourceId);
    } catch (BmcException e) {
        if (e.isTimeout()) {
            LOG.warning("OCI call timed out | opc-request-id=" + e.getOpcRequestId());
            throw new RuntimeException("Service timeout", e);
        }
        if (e.isClientSide()) {
            LOG.severe("Client-side error: " + e.getMessage());
            throw new RuntimeException("Network error", e);
        }
        switch (e.getStatusCode()) {
            case 400:
                throw new IllegalArgumentException("Invalid request: " + e.getServiceCode(), e);
            case 401: case 403:
                LOG.severe("Auth error " + e.getStatusCode() + ": " + e.getServiceCode()
                    + " | opc-request-id=" + e.getOpcRequestId());
                throw new SecurityException("Unauthorized: " + e.getServiceCode(), e);
            case 404:
                LOG.warning("Resource not found: " + resourceId);
                return null;
            case 429:
                LOG.warning("Rate limited | opc-request-id=" + e.getOpcRequestId());
                throw new RuntimeException("Rate limited", e);
            default:
                LOG.severe("OCI error " + e.getStatusCode() + "/" + e.getServiceCode()
                    + " | opc-request-id=" + e.getOpcRequestId());
                throw new RuntimeException("OCI service error", e);
        }
    }
}
```
**Why it is mandatory**: Retrying 404 or 400 errors is pointless and wastes function execution time. Auth errors (401/403) indicate IAM policy misconfiguration — retrying won't fix them. Only 429 and 5xx are transient and retryable.
**Failure if omitted**: Wasted compute cost, delayed failure response, silent misdiagnosis of IAM policy issues.
**Source**: [OCI SDK BmcException](https://github.com/oracle/oci-java-sdk/blob/master/bmc-common/src/main/java/com/oracle/bmc/model/BmcException.java)

---

**External REST API Calls with java.net.http.HttpClient and Explicit Timeout**: For non-OCI REST APIs, use the `java.net.http.HttpClient` built-in to Java 17. Always set a request-level timeout shorter than the function timeout to allow graceful error handling.

```java
// ✅ CORRECT: External REST call with timeout — Java 17 HttpClient
// Timeout (10s) leaves room for error handling within 30s function budget
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public String callExternalApi(String payload) throws Exception {
    HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create(apiBaseUrl + "/api/v1/data"))
        .header("Content-Type", "application/json")
        .header("Authorization", "Bearer " + apiKey)
        .timeout(Duration.ofSeconds(10))  // MUST be < function timeout
        .POST(HttpRequest.BodyPublishers.ofString(payload))
        .build();

    try {
        HttpResponse<String> response = httpClient.send(
            request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() >= 200 && response.statusCode() < 300) {
            return response.body();
        }
        throw new RuntimeException("API error: HTTP " + response.statusCode());
    } catch (java.net.http.HttpTimeoutException e) {
        LOG.warning("External API timeout: " + e.getMessage());
        return "{\"error\": \"upstream_timeout\"}";  // graceful degradation
    }
}
```
**Why it is mandatory**: External APIs have unpredictable latency. Without an explicit timeout, the function blocks until platform kill (30s default), returning 503 with no diagnostic context.
**Failure if omitted**: Platform kills function, 503 to caller, no error logging, no graceful fallback.
**Source**: [Java 17 HttpClient API](https://docs.oracle.com/en/java/javase/17/docs/api/java.net.http/java/net/http/HttpClient.html)

---

**Function-to-Function Invocation via FunctionsInvokeClient**: For composing functions, use `FunctionsInvokeClient` with the target function's invoke endpoint. Set the endpoint once in `@FnConfiguration` (obtained from `FunctionsManagementClient` or configuration).

```java
// ✅ CORRECT: Function-to-function invocation — OCI SDK v3.x+
import com.oracle.bmc.functions.FunctionsInvokeClient;
import com.oracle.bmc.functions.FunctionsManagementClient;
import com.oracle.bmc.functions.requests.InvokeFunctionRequest;
import com.oracle.bmc.functions.requests.GetFunctionRequest;
import com.oracle.bmc.functions.responses.InvokeFunctionResponse;
import com.oracle.bmc.util.StreamUtils;
import java.nio.charset.StandardCharsets;

public class FunctionChainer {
    private FunctionsInvokeClient invokeClient;
    private String targetFunctionId;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        this.invokeClient = FunctionsInvokeClient.builder().build(provider);
        this.targetFunctionId = ctx.getConfigurationByKey("TARGET_FUNCTION_ID").orElseThrow();

        // Get invoke endpoint once during cold start
        FunctionsManagementClient mgmtClient = FunctionsManagementClient.builder().build(provider);
        String invokeEndpoint = mgmtClient.getFunction(
            GetFunctionRequest.builder().functionId(targetFunctionId).build()
        ).getFunction().getInvokeEndpoint();
        this.invokeClient.setEndpoint(invokeEndpoint);
        mgmtClient.close();
    }

    public String handleRequest(String payload) {
        InvokeFunctionRequest request = InvokeFunctionRequest.builder()
            .functionId(targetFunctionId)
            .invokeFunctionBody(
                StreamUtils.createByteArrayInputStream(
                    payload.getBytes(StandardCharsets.UTF_8)))
            .build();

        InvokeFunctionResponse response = invokeClient.invokeFunction(request);
        return StreamUtils.toString(response.getInputStream(), StandardCharsets.UTF_8);
    }
}
```
**Why it is mandatory**: Direct HTTP calls to function endpoints require OCI request signing. The SDK client handles signing, retry, and error handling automatically.
**Failure if omitted**: Unsigned requests are rejected (401). Manual signing is complex and error-prone.
**Source**: [OCI SDK InvokeFunctionExample](https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/InvokeFunctionExample.java)

---

