---
paths:
  - "**/src/main/java/**/*.java"
---
You are an OCI Functions Observability specialist.
Ensure all function implementations include proper logging and diagnostic output that enables debugging of deployed functions without direct container access.

## Why Observability Is Critical in Serverless

OCI Functions have:
- **No SSH access** — cannot attach debugger or read local logs
- **No persistent filesystem** — logs disappear when container is recycled
- **Limited OCI Logging** — may not be configured, has latency, query is complex
- **The API response is often your ONLY diagnostic channel**

Without observability patterns, a single problem can take **5x longer to diagnose** (proven in production incidents).

## Mandatory Logging Patterns

### 1. Cold Start Marker

Log when the function initializes (cold start) vs reuses existing JVM (hot invocation):

```java
private static final Logger LOG = Logger.getLogger(MyFunction.class.getName());
private boolean coldStart = true;

@Override
@FnConfiguration
public void configure(RuntimeContext ctx) {
    super.configure(ctx);
    long start = System.currentTimeMillis();
    try {
        // initialization code...
    } catch (Exception e) {
        this.initError = e.getClass().getName() + ": " + e.getMessage();
        LOG.severe("INIT FAILED: " + initError);
    }
    long elapsed = System.currentTimeMillis() - start;
    LOG.info(String.format("COLD_START completed in %dms | memory=%sMB | timeout=%ss",
        elapsed,
        ctx.getConfigurationByKey("FN_MEMORY").orElse("?"),
        ctx.getConfigurationByKey("FN_TIMEOUT").orElse("?")));
}
```

### 2. Invocation Entry/Exit Logging

Log each invocation with timing and outcome:

```java
@Override
public APIGatewayResponseEvent<Response> handler(APIGatewayRequestEvent<Request> req) {
    long start = System.currentTimeMillis();
    String method = req.getMethod();
    String path = req.getPath();

    LOG.info(String.format("INVOKE %s %s | coldStart=%s", method, path, coldStart));
    coldStart = false; // subsequent calls are hot

    try {
        // business logic...
        long elapsed = System.currentTimeMillis() - start;
        LOG.info(String.format("COMPLETE %s %s | status=200 | elapsed=%dms", method, path, elapsed));
        return success(response);
    } catch (Exception e) {
        long elapsed = System.currentTimeMillis() - start;
        LOG.severe(String.format("FAILED %s %s | status=500 | elapsed=%dms | error=%s: %s",
            method, path, elapsed, e.getClass().getName(), e.getMessage()));
        return error(500, Response.error("Internal error", e.getMessage()));
    }
}
```

### 3. Downstream Call Timing

Log each external call with duration for timeout budget analysis:

```java
long callStart = System.currentTimeMillis();
HttpResponse<String> response = httpClient.send(request, BodyHandlers.ofString());
long callElapsed = System.currentTimeMillis() - callStart;
LOG.info(String.format("HTTP_CALL %s | status=%d | elapsed=%dms",
    request.uri().getHost(), response.statusCode(), callElapsed));
```

### 4. Initialization Subsystem Reporting

Log each subsystem init separately to identify which one fails:

```java
@Override
@FnConfiguration
public void configure(RuntimeContext ctx) {
    super.configure(ctx);
    try {
        LOG.info("INIT: Loading configuration...");
        loadConfig(ctx);

        LOG.info("INIT: Creating SDK client...");
        createSdkClient();

        LOG.info("INIT: Loading Vault secrets...");
        loadSecrets();

        LOG.info("INIT: Creating HTTP client...");
        createHttpClient();

        LOG.info("INIT: All subsystems ready");
    } catch (Exception e) {
        this.initError = e.getClass().getName() + ": " + e.getMessage();
        LOG.severe("INIT FAILED at subsystem: " + initError);
    }
}
```

## Response Metadata Pattern

Include diagnostic metadata in ALL responses (success and error):

```java
public class Response {
    private String status;      // "sucesso" | "erro"
    private String message;
    private Object data;
    private long elapsed_ms;    // Total handler time
    private boolean cold_start; // Was this a cold start invocation?
    private String version;     // Function version (from func.yaml or env)

    // Error-specific
    private String erro;
    private String detalhe;     // Full exception message — NEVER strip
}
```

This enables diagnosis from the API response alone:
- `elapsed_ms: 0` + error → init failure (didn't reach business logic)
- `elapsed_ms: 60000` + timeout → budget exceeded
- `elapsed_ms: 200` + success → healthy
- `cold_start: true` + `elapsed_ms: 3000` → normal cold start overhead

## Health/Diagnostic Endpoint Pattern

For functions with API Gateway integration, implement a diagnostic path:

```java
if ("/health".equals(path) || "/diag".equals(path)) {
    Map<String, Object> diag = new LinkedHashMap<>();
    diag.put("status", initError == null ? "healthy" : "degraded");
    diag.put("initError", initError);
    diag.put("version", version);
    diag.put("coldStart", coldStart);
    diag.put("uptime_ms", System.currentTimeMillis() - startupTime);
    diag.put("config_keys", List.of("KEY1", "KEY2")); // names only, not values
    return success(Response.ok(diag));
}
```

## Log Level Guidelines

| Level | When | Example |
|-------|------|---------|
| SEVERE | Init failure, uncaught exceptions, security events | "INIT FAILED: NoSuchElementException" |
| WARNING | Recoverable issues, degraded operations | "JAXB unavailable, XML disabled" |
| INFO | Invocation start/end, cold start, downstream calls | "INVOKE POST /store | coldStart=true" |
| FINE | Request/response bodies (only in dev) | "REQUEST: {store_id: 1001}" |

## ✅ Always Do
- Log COLD_START with initialization time in milliseconds
- Log INVOKE entry and COMPLETE/FAILED exit with elapsed time
- Include `elapsed_ms` in all API responses (success and error)
- Log downstream call timing (HTTP calls, SDK calls)
- Include full `e.getMessage()` in error responses and logs
- Log each initialization subsystem separately
- Include function version in responses

## 🚫 Never Do
- Log secret values, credentials, or tokens (even at FINE level)
- Use `System.out.println` — use `java.util.logging.Logger`
- Log request bodies in production that may contain PII
- Skip logging in catch blocks — `catch (Exception e) {}` is FORBIDDEN
- Strip or summarize exception messages — the detail IS the diagnostic
- Log at FINE level in production without conditional check
