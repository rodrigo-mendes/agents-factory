### 🚫 Never Do

**Anti-Pattern**: Hardcoded API keys for OCI authentication

```java
// 🚫 WRONG: API keys hardcoded — credential leak risk (ALL versions)
SimpleAuthenticationDetailsProvider provider = SimpleAuthenticationDetailsProvider.builder()
    .tenantId("ocid1.tenancy.oc1..aaa...")
    .userId("ocid1.user.oc1..aaa...")
    .fingerprint("ab:cd:ef:...")
    .privateKeyFilePath("/path/to/key.pem")
    .build();

// ✅ CORRECT: Resource Principal via Dynamic Group (FDK v1.0.186+ / OCI SDK v3.x)
ResourcePrincipalAuthenticationDetailsProvider provider =
    ResourcePrincipalAuthenticationDetailsProvider.builder().build();
```

**Why it is prohibited**: API keys in code are a security vulnerability. Leaked credentials = full account compromise. Functions are authenticated via Dynamic Groups + IAM Policies.
**Actual impact**: Security breach, credential rotation nightmare, violates OCI security best practices.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm

---

**Anti-Pattern**: Mutable shared state between invocations

```java
// 🚫 WRONG: State accumulates across hot function invocations (ALL versions)
public class BadHandler {
    private List<String> requestLog = new ArrayList<>(); // grows unbounded!

    public String handleRequest(String input) {
        requestLog.add(input); // accumulates across hot invocations
        return "Processed " + requestLog.size() + " requests";
    }
}

// ✅ CORRECT: Stateless handler, or immutable init-once state (FDK v1.0.186+)
public class GoodHandler {
    private final OciServiceClient client; // immutable, initialized once

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        this.client = new OciServiceClient(); // one-time init is OK
    }

    public String handleRequest(String input) {
        // Process input without accumulating state
        return client.process(input);
    }
}
```

**Why it is prohibited**: Hot functions reuse the same JVM. Mutable state accumulates between invocations, causing memory leaks and unpredictable behavior. The Fn runtime does not guarantee which instance serves which request.
**Actual impact**: Memory leak, incorrect results, OOM after prolonged use.
**Source**: https://github.com/fnproject/fdk-java/blob/master/docs/FunctionConfiguration.md

---

**Anti-Pattern**: Consuming InputEvent body twice

```java
// 🚫 WRONG: Body InputStream can only be consumed once (ALL versions)
public OutputEvent handleRequest(InputEvent event) {
    String body1 = event.consumeBody(is -> readAll(is));
    String body2 = event.consumeBody(is -> readAll(is)); // IllegalStateException!
    return OutputEvent.fromBytes(body2.getBytes(), 200, "text/plain");
}

// ✅ CORRECT: Use combined binding — body auto-parsed, headers via InputEvent (FDK v1.0.186+)
public OutputEvent handleRequest(String body, InputEvent event) {
    // body is already parsed by Jackson, headers available via event
    String header = event.getHeaders().get("X-My-Header").orElse("");
    return OutputEvent.fromBytes(body.getBytes(), 200, "text/plain");
}
```

**Why it is prohibited**: The body of `InputEvent` is an InputStream that can only be consumed once. A second attempt throws `IllegalStateException`.
**Actual impact**: Function crashes with `IllegalStateException` at runtime.
**Source**: https://github.com/fnproject/fdk-java/blob/master/docs/DataBinding.md

---

**Anti-Pattern**: Heavy initialization in handler method

```java
// 🚫 WRONG: Creating OCI client on EVERY invocation (ALL versions)
public class SlowHandler {
    public ApiResponse handleRequest(ApiRequest request) {
        // OCI SDK client creation involves network calls — costly per invocation
        var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        var client = ObjectStorageClient.builder().build(provider);
        return ApiResponse.ok("done");
    }
}

// ✅ CORRECT: Initialize once in @FnConfiguration (FDK v1.0.186+)
public class FastHandler {
    private ObjectStorageClient client;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        this.client = ObjectStorageClient.builder().build(provider);
    }

    public ApiResponse handleRequest(ApiRequest request) {
        // Reuse pre-initialized client — warm invocation ~5-50ms
        return ApiResponse.ok("done");
    }
}
```

**Why it is prohibited**: OCI SDK client creation involves network calls and is expensive. In hot functions, this is executed every invocation, wasting the warm container benefit.
**Actual impact**: 10-100x slower invocations, wasted compute, higher costs.
**Source**: https://github.com/fnproject/fdk-java/blob/master/docs/FunctionConfiguration.md

---

**Anti-Pattern**: Sharing function class with test ClassLoader

```java
// 🚫 WRONG: Breaks class loader isolation in FnTestingRule (ALL versions)
@Rule
public FnTestingRule testing = FnTestingRule.createDefault();

@Before
public void setup() {
    testing.addSharedClass(MyFunction.class); // breaks isolation!
}

// ✅ CORRECT: Share only helper/mock classes (FDK v1.0.186+)
@Before
public void setup() {
    testing.addSharedClass(MockServiceClient.class);
    testing.addSharedClassPrefix("com.eci.serverless.mocks.");
    testing.addSharedClassPrefix("com.oracle.bmc.");  // Required for BmcException catch
}
```

**Why it is prohibited**: FnTestingRule uses separate class loaders to simulate real Fn isolation. Sharing the function class breaks `@FnConfiguration` simulation and may cause unexpected static field initialization.
**Actual impact**: Tests pass locally but function fails in production. `@FnConfiguration` may not execute correctly.
**Source**: https://github.com/fnproject/fdk-java/blob/master/docs/TestingFunctions.md

---

**Anti-Pattern**: Blocking thread pool in function

```java
// 🚫 WRONG: Thread pools waste memory in 256MB container (ALL versions)
public class ParallelHandler {
    private ExecutorService pool = Executors.newFixedThreadPool(10);

    public String handleRequest(String input) {
        Future<String> f = pool.submit(() -> heavyWork(input));
        return f.get(25, TimeUnit.SECONDS);
    }
}

// ✅ CORRECT: Process sequentially — Fn handles 1 invocation per container (FDK v1.0.186+)
public class SequentialHandler {
    public String handleRequest(String input) {
        return heavyWork(input); // single thread, simple
    }
}
```

**Why it is prohibited**: OCI Functions process one invocation per container instance. Thread pools are wasted memory (256MB limit) and the Fn runtime does not guarantee pool lifecycle between invocations.
**Actual impact**: Memory pressure in 256MB containers, timeout complexity, resource waste.
**Source**: https://github.com/fnproject/fdk-java (Fn architecture: 1 invocation per container)

---

