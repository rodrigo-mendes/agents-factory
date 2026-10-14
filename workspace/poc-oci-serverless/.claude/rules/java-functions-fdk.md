---
paths:
  - "**/src/main/java/**/*.java"
---
You are an OCI Functions FDK Lifecycle specialist for FDK v1.1.x.
Ensure all function implementations follow the correct FDK lifecycle patterns for cold start optimization and hot function reuse.

For complete code patterns and implementation examples, load the skill: `.claude/skills/developing-oci-functions-java/SKILL.md`
For fn-events typed abstractions, load: `.claude/skills/implementing-oci-functions-events/SKILL.md`

## When to Load These Skills

Load `developing-oci-functions-java` when the user request involves:
- Creating a new function handler (any pattern)
- Setting up `@FnConfiguration` initialization
- Understanding hot function model and cold start optimization
- Accessing configuration via `RuntimeContext`

Load `implementing-oci-functions-events` when the user also needs:
- `APIGatewayFunction<Req, Res>` — typed API Gateway backend
- `ConnectorHubFunction<T>` — Service Connector Hub event handler
- `NotificationFunction<T>` — OCI Notifications subscriber

## Function Entry Point Decision Matrix

| Pattern | Entry Point | When to Use | func.yaml cmd |
|---------|------------|-------------|---------------|
| A: Direct POJO | `::handleRequest` | Simple JSON APIs, no HTTP header access needed | `ClassName::handleRequest` |
| B: InputEvent/OutputEvent | `::handleRequest` | HTTP header access, binary payloads, custom content types | `ClassName::handleRequest` |
| C: APIGatewayFunction | `::handler` | API Gateway backend with typed HTTP request/response | `ClassName::handler` |
| D: ConnectorHubFunction | `::handler` | Service Connector Hub target (batch processing, void return) | `ClassName::handler` |
| E: NotificationFunction | `::handler` | OCI Notifications subscriber (single event, void return) | `ClassName::handler` |

**CRITICAL**: Using `::handleRequest` with fn-events classes causes SILENT routing failure.

## @FnConfiguration Rules (MANDATORY)

Initialize ALL expensive resources once per JVM lifecycle in `@FnConfiguration`:

### What to Initialize in @FnConfiguration

| Object | Initialize? | Reason |
|--------|------------|--------|
| OCI SDK clients | ✅ Yes | Thread-safe, reuse connection pool |
| HttpClient | ✅ Yes | Reuse TLS sessions + connection pool |
| ObjectMapper | ✅ Yes | Immutable once configured |
| DateTimeFormatter | ✅ Yes (static final) | Immutable |
| Configuration values | ✅ Yes | Read once from RuntimeContext |
| OCI Vault secrets | ✅ Yes | API call once, cache value |
| Object Storage namespace | ✅ Yes | `getNamespace()` call once |

### What NOT to Cache in Instance Fields

| Object | Cache? | Reason |
|--------|--------|--------|
| Request-scoped data | ❌ No | Data corruption across invocations |
| InputStream | ❌ No | Must close per invocation |
| Mutable counters/state | ❌ No | Thread safety issues unless synchronized |

## Hot Function Model

- JVM persists between invocations — `@FnConfiguration` runs ONCE per cold start
- Instance fields survive across invocations — treat as effectively final after init
- SDK clients are thread-safe — safe for concurrent hot invocations
- Cold start cost: ~500-2000ms (JVM + SDK init). Hot invocations: near-zero overhead

## RuntimeContext Configuration Access

- Required config: `ctx.getConfigurationByKey("KEY").orElseThrow()` — fail fast on cold start
- Optional config: `ctx.getConfigurationByKey("KEY").orElse("default")` — with sensible default
- Precedence: Function config (func.yaml) > Application config > Defaults

## ✅ Always Do
- Initialize ALL SDK clients in `@FnConfiguration`
- Cache ObjectMapper, HttpClient, DateTimeFormatter as instance fields
- Use `RuntimeContext.getConfigurationByKey()` for configuration access
- Use `::handler` for fn-events abstract classes in func.yaml cmd
- Fail fast in `@FnConfiguration` if required config is missing

## @FnConfiguration Override Rules (CRITICAL)

When extending an `fn-events` abstract class (e.g., `APIGatewayFunction`), the child MUST follow these rules:

### Rule 1: Method Name MUST Be `configure`

```java
// ✅ CORRECT — overrides parent's @FnConfiguration method
@Override
@FnConfiguration
public void configure(RuntimeContext ctx) {
    super.configure(ctx);
    // child initialization here
}
```

```java
// ❌ WRONG — FDK treats this as a SEPARATE @FnConfiguration method
// Both parent.configure() AND child.config() will be called!
@FnConfiguration
public void config(RuntimeContext ctx) {
    // This does NOT override — it's an additional init method
}
```

### Rule 2: Always Call `super.configure(ctx)` First

The parent class initializes framework internals (event parsing, response builders). Skipping `super.configure()` breaks the fn-events abstraction.

### Rule 3: Wrap Init Body in try-catch for Resilience

In production deployments, initialization failures should be captured and reported to the client (not silently kill the container):

```java
private String initError;

@Override
@FnConfiguration
public void configure(RuntimeContext ctx) {
    super.configure(ctx);
    try {
        // all initialization here
    } catch (Exception e) {
        this.initError = e.getClass().getName() + ": " + e.getMessage();
        LOG.severe("INIT FAILED: " + initError);
    }
}
```

Then in handler:
```java
if (initError != null) {
    return error(500, Response.error("Function init failed", initError));
}
```

### Why This Matters

- If child uses a different name (e.g., `config()`), FDK calls BOTH `parent.configure()` and `child.config()` — causing double initialization, potential NPEs, and unpredictable behavior
- Without try-catch, any exception in `configure()` crashes the container with zero logs → generic 502 to caller

## Non-Fatal Optional Initialization (Degraded Mode)

Not all initialization subsystems are equally critical. Some failures should degrade the function (reduce capabilities) rather than block it entirely.

### Pattern: initWarnings for Non-Fatal Subsystems

```java
private String initError;                    // Fatal — function cannot operate
private final List<String> initWarnings = new ArrayList<>();  // Non-fatal — degraded mode

@Override
@FnConfiguration
public void configure(RuntimeContext ctx) {
    super.configure(ctx);
    try {
        // Critical subsystems — failure is fatal
        this.objectMapper = new ObjectMapper();
        this.httpClient = HttpClient.newBuilder().build();
        loadCredentials(ctx); // If this fails, nothing works

        // Optional subsystem — failure degrades but doesn't block
        try {
            this.jaxbContext = JAXBContext.newInstance(MyModel.class);
        } catch (Exception e) {
            initWarnings.add("JAXB unavailable: " + e.getMessage() + " — XML disabled");
            LOG.warning("JAXB init failed (non-fatal): " + e.getMessage());
        }

    } catch (Exception e) {
        this.initError = e.getClass().getName() + ": " + e.getMessage();
        LOG.severe("INIT FAILED: " + initError);
    }
}
```

### When to Use initWarnings vs initError

| Subsystem | If Fails | Use |
|-----------|----------|-----|
| SDK client (auth) | Function cannot call OCI services | `initError` (fatal) |
| Credentials (Vault) | Cannot authenticate to anything | `initError` (fatal) |
| Required config keys | Function has no context to operate | `initError` (fatal) |
| JAXB/XML processing | Can't do XML, but JSON still works | `initWarnings` (degraded) |
| Optional metric client | Can't emit metrics, but business works | `initWarnings` (degraded) |
| Cache pre-warming | Slower first call, but still works | `initWarnings` (degraded) |

### Reporting Degraded Mode in Response

```java
if (initError != null) {
    return error(500, Response.error("Function init failed", initError));
}
// Optional: inform caller about degraded capabilities
if (!initWarnings.isEmpty() && path.equals("/health")) {
    return success(Response.degraded(initWarnings));
}
```

## Dockerfile CMD for Docker/Terraform Deployment (MANDATORY)

When deploying via Docker image (Terraform `oci_functions_function`), the Dockerfile MUST include a CMD instruction:

```dockerfile
CMD ["com.example.MyFunction::handler"]
```

> **CRITICAL:** `func.yaml` `cmd` field is ONLY used by `fn` CLI. Docker deployments ignore it. Without CMD, the FDK base image does not know which class/method to invoke → container starts and immediately dies → 502.

## 🚫 Never Do
- Initialize SDK clients inside handler method — eliminates hot function benefit (500-2000ms per call)
- Create new HttpClient instances per invocation — TLS handshake + pool creation overhead
- Use `Thread.sleep()` for retry delays — wastes execution time and cost
- Use mutable shared state without thread safety — data corruption in hot JVM
- Store request-scoped data in instance fields — leaks between invocations
- Use `::handleRequest` with fn-events abstract classes — silent routing failure
- Name `@FnConfiguration` method anything other than `configure` when extending fn-events classes — causes double init
- Omit CMD from Dockerfile when deploying via Docker/Terraform — causes 502 with no logs
