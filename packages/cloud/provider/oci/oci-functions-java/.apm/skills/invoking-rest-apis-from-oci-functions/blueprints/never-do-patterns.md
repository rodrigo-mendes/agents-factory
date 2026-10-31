### 🚫 Never Do

**Anti-Pattern**: Creating HTTP clients in the handler method

```java
// 🚫 WRONG: New HttpClient per invocation — wastes TLS handshake, no connection reuse
// OCI Functions Java 17 — hot function JVM persists between invocations
public String handleRequest(String input) throws Exception {
    HttpClient client = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(5))
        .build();  // NEW connection pool per invocation!

    HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create("https://api.example.com/data"))
        .build();
    return client.send(request, HttpResponse.BodyHandlers.ofString()).body();
}

// ✅ CORRECT: Create once in @FnConfiguration — reused across hot invocations
private HttpClient httpClient;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    this.httpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(5))
        .build();
}

public String handleRequest(String input) throws Exception {
    HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create("https://api.example.com/data"))
        .timeout(Duration.ofSeconds(10))
        .build();
    return httpClient.send(request, HttpResponse.BodyHandlers.ofString()).body();
}
```
**Why it is prohibited**: HTTP clients create connection pools, TLS sessions, and thread pools. In hot functions, creating a new client per invocation wastes ~50-200ms per call and can cause connection pool exhaustion under burst load.
**Actual impact**: 50-200ms overhead per invocation, connection exhaustion in burst scenarios.
**Source**: [Oracle Functions Samples](https://github.com/oracle-samples/oracle-functions-samples)

---

**Anti-Pattern**: Using API keys or config file authentication in OCI Functions

```java
// 🚫 WRONG: Config file auth — ~/.oci/config does NOT exist in Functions containers
// Hardcoded API keys are a severe security vulnerability
ConfigFileReader.ConfigFile configFile = ConfigFileReader.parseDefault();
AuthenticationDetailsProvider provider =
    new ConfigFileAuthenticationDetailsProvider(configFile);

// ✅ CORRECT: Always use Resource Principal in OCI Functions
// OCI SDK v3.x+ — injected automatically by the Functions runtime
ResourcePrincipalAuthenticationDetailsProvider provider =
    ResourcePrincipalAuthenticationDetailsProvider.builder().build();
```
**Why it is prohibited**: Functions containers have no `~/.oci/config` file. Embedding API keys in the container image exposes credentials to anyone who can pull the image from OCIR.
**Actual impact**: `FileNotFoundException` at runtime. If API key is embedded: credential leak, security incident.
**Source**: [Oracle Functions Samples — Resource Principal](https://github.com/oracle-samples/oracle-functions-samples/blob/master/samples/oci-objectstorage-put-object-java/src/main/java/com/example/fn/ObjectStoragePutObject.java)

---

**Anti-Pattern**: SDK read timeout exceeding function timeout

```java
// 🚫 WRONG: Default SDK read timeout (60s) with default function timeout (30s)
// OCI SDK v3.x+ — function killed before SDK timeout fires
ObjectStorageClient client = ObjectStorageClient.builder()
    .build(provider);
// Default readTimeoutMillis = 60000 (60s)
// Default function timeout = 30s → platform kills function first!

// ✅ CORRECT: Read timeout (15s) well within function budget (30s)
// OCI SDK v3.x+ — leaves room for error handling and logging
ClientConfiguration config = ClientConfiguration.builder()
    .connectionTimeoutMillis(5000)   // 5s
    .readTimeoutMillis(15000)        // 15s — within 30s function timeout
    .build();

ObjectStorageClient client = ObjectStorageClient.builder()
    .configuration(config)
    .build(provider);
```
**Why it is prohibited**: When SDK timeout (60s) exceeds function timeout (30s), the platform kills the function abruptly. No error logging, no cleanup, no graceful degradation. The caller gets "Function Invoke Timedout" (503) with zero diagnostic information.
**Actual impact**: Platform kill (502/503 to caller), no error context, impossible to debug.
**Source**: [OCI SDK ClientConfiguration](https://github.com/oracle/oci-java-sdk/blob/master/bmc-common/src/main/java/com/oracle/bmc/ClientConfiguration.java)

---

**Anti-Pattern**: Blindly retrying all BmcException errors

```java
// 🚫 WRONG: Retrying 404 and 400 errors — these are deterministic, won't change
// OCI SDK v3.x+ — wastes function execution time and compute cost
try {
    return ociClient.getObject(request);
} catch (BmcException e) {
    Thread.sleep(1000);
    return ociClient.getObject(request); // same error guaranteed
}

// ✅ CORRECT: Only retry transient errors (429, 5xx, timeouts)
try {
    return ociClient.getObject(request);
} catch (BmcException e) {
    if (e.getStatusCode() == 404) {
        return null; // Not found — not retryable
    }
    if (e.getStatusCode() == 401 || e.getStatusCode() == 403) {
        throw new SecurityException("IAM policy issue: " + e.getServiceCode(), e);
    }
    if (e.getStatusCode() == 429 || e.getStatusCode() >= 500) {
        throw e; // Let SDK RetryConfiguration handle transient errors
    }
    throw e;
}
```
**Why it is prohibited**: 4xx errors (400, 401, 403, 404) are deterministic — the same request will produce the same error. Retrying them wastes function execution time and compute cost without any chance of success.
**Actual impact**: Wasted compute cost, delayed failure, masked root cause (IAM misconfiguration appears as timeout).
**Source**: [OCI SDK DefaultRetryCondition](https://github.com/oracle/oci-java-sdk/blob/master/bmc-common/src/main/java/com/oracle/bmc/retrier/DefaultRetryCondition.java)

---

**Anti-Pattern**: Calling setEndpoint() on shared FunctionsInvokeClient in handler

```java
// 🚫 WRONG: Changing endpoint on shared client — NOT thread-safe in hot functions
// OCI SDK v3.x+ — concurrent invocations may send to wrong endpoint
private FunctionsInvokeClient invokeClient;

public String handleRequest(InvokeRequest input) {
    invokeClient.setEndpoint(input.getTargetEndpoint()); // race condition!
    return invokeClient.invokeFunction(request);
}

// ✅ CORRECT Option A: Single target — set endpoint once in @FnConfiguration
@FnConfiguration
public void configure(RuntimeContext ctx) {
    this.invokeClient = FunctionsInvokeClient.builder().build(provider);
    this.invokeClient.setEndpoint(
        ctx.getConfigurationByKey("TARGET_ENDPOINT").orElseThrow());
}

// ✅ CORRECT Option B: Multiple targets — one client per endpoint
private Map<String, FunctionsInvokeClient> clientsByEndpoint = new ConcurrentHashMap<>();

private FunctionsInvokeClient getClientForEndpoint(String endpoint) {
    return clientsByEndpoint.computeIfAbsent(endpoint, ep -> {
        FunctionsInvokeClient client = FunctionsInvokeClient.builder().build(provider);
        client.setEndpoint(ep);
        return client;
    });
}
```
**Why it is prohibited**: `setEndpoint()` mutates shared client state. In hot functions with concurrent invocations, requests can be routed to the wrong function endpoint — causing silent data corruption or invoking the wrong function.
**Actual impact**: Requests routed to wrong function. Silent data corruption. Wrong function invoked.
**Source**: [OCI SDK FunctionsInvokeClient](https://github.com/oracle/oci-java-sdk/blob/master/bmc-functions/src/main/java/com/oracle/bmc/functions/FunctionsInvokeClient.java)

---

**Anti-Pattern**: Logging sensitive data from API responses

```java
// 🚫 WRONG: Logging full response body — may contain PII, tokens, or secrets
// OCI Functions logs go to OCI Logging — accessible to log readers
HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
LOG.info("API Response: " + response.body()); // PII/secrets in logs!

// ✅ CORRECT: Log only status and non-sensitive metadata
HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
LOG.info("API Response: status=" + response.statusCode()
    + " content-length=" + response.headers().firstValue("content-length").orElse("unknown"));
```
**Why it is prohibited**: OCI Functions logs are sent to OCI Logging or stdout. Sensitive data in logs can be exposed to any user with log read access, violating GDPR, LGPD, and HIPAA compliance.
**Actual impact**: Credential leakage, PII exposure in logs, compliance violations, potential data breach.
**Source**: Security best practices

---

