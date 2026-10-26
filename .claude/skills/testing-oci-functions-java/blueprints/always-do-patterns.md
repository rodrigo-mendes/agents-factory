# ✅ Always Do — Testing Patterns

## FnTestingRule Setup (Every Test Class)

```java
import com.fnproject.fn.testing.FnTestingRule;
import com.fnproject.fn.testing.FnResult;
import org.junit.Rule;
import org.junit.Test;
import static org.junit.Assert.*;

public class OrderFunctionTest {
    @Rule
    public final FnTestingRule testing = FnTestingRule.createDefault();

    @Test
    public void testProcessOrder() {
        testing.setConfig("BUCKET_NAME", "test-bucket");
        testing.givenEvent()
            .withHeader("content-type", "application/json")  // REQUIRED for POJO binding
            .withBody("{\"action\":\"create\",\"productId\":\"P001\"}")
            .enqueue();
        testing.thenRun(OrderFunction.class, "handleRequest");

        FnResult result = testing.getOnlyResult();
        assertTrue(result.getBodyAsString().contains("\"status\":\"created\""));
    }
}
```

## Hot Function Simulation (Detect State Leaks)

```java
@Test
public void testNoStateLeakage() {
    testing.givenEvent().withBody("{\"id\":\"1\"}").enqueue();
    testing.givenEvent().withBody("{\"id\":\"2\"}").enqueue();
    testing.givenEvent().withBody("{\"id\":\"3\"}").enqueue();
    testing.thenRun(MyFunction.class, "handleRequest");

    List<FnResult> results = testing.getResults();
    assertEquals(3, results.size());
    // Verify each invocation is independent
}
```

## APIGatewayTestFeature for fn-events Functions

```java
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.events.testing.APIGatewayTestFeature;
import static org.mockito.Mockito.*;

public class OrderApiFunctionTest {
    @Rule
    public FnTestingRule fn = FnTestingRule.createDefault();
    private final APIGatewayTestFeature apiGw = APIGatewayTestFeature.createDefault(fn);

    @Test
    public void testPost() {
        @SuppressWarnings("unchecked")
        APIGatewayRequestEvent<OrderRequest> event = mock(APIGatewayRequestEvent.class);
        when(event.getBody()).thenReturn(new OrderRequest("P001", 3));
        when(event.getMethod()).thenReturn("POST");
        when(event.getQueryParameters()).thenReturn(new QueryParametersImpl(Map.of()));

        apiGw.givenEvent(event).enqueue();
        fn.thenRun(OrderApiFunction.class, "handler");

        APIGatewayResponseEvent<OrderResponse> resp = apiGw.getResult(OrderResponse.class);
        assertEquals(Integer.valueOf(201), resp.getStatus());
    }
}
```

## OCI SDK Mock Injection via addSharedClass

```java
// 1. Mock holder (in src/test — NOT the function class)
public class MockOciClients {
    public static ObjectStorageClient objectStorageClient;
    public static SecretsClient secretsClient;
    public static String namespace = "test-namespace";
}

// 2. Test setup
@Before
public void setup() {
    testing.addSharedClass(MockOciClients.class);
    testing.addSharedClassPrefix("com.eci.functions.mocks.");
    testing.addSharedClassPrefix("com.oracle.bmc.");  // Required for BmcException catch
    MockOciClients.objectStorageClient = mock(ObjectStorageClient.class);
}

// 3. Function detects mock via Class.forName in @FnConfiguration
@FnConfiguration
public void configure(RuntimeContext ctx) {
    try {
        Class<?> mock = Class.forName("com.eci.functions.mocks.MockOciClients");
        this.client = (ObjectStorageClient) mock.getField("objectStorageClient").get(null);
    } catch (ClassNotFoundException e) {
        // Production — Resource Principal
        this.client = ObjectStorageClient.builder()
            .build(ResourcePrincipalAuthenticationDetailsProvider.builder().build());
    }
}
```

## OCI SDK Classloader Sharing (BmcException)

When your function catches `BmcException`, you **MUST** share the OCI SDK classes across the FnTestingRule classloader boundary. Without this, exceptions thrown from mocked services are loaded by a different classloader and won't match the `catch (BmcException e)` block in the function — they fall through to `catch (Exception e)` instead.

```java
// MANDATORY when testing BmcException error paths
testing.addSharedClassPrefix("com.oracle.bmc.");
```

**Impact of omitting**: All BmcException tests silently pass through to the generic exception handler, returning 500 instead of the expected error classification (503 for timeout/429/5xx, or the actual status code for client errors).

---

## content-type Header for JSON POJOs

Always set `content-type: application/json` when testing POJO handlers. Without it, FDK passes raw String/bytes instead of deserializing.

```java
testing.givenEvent()
    .withHeader("content-type", "application/json")  // MANDATORY
    .withBody("{\"key\":\"value\"}")
    .enqueue();
```

---

## Complete Test Setup Checklist

Copy-paste this setup block for functions that use interface abstraction + OCI SDK error handling:

```java
@Rule
public final FnTestingRule testing = FnTestingRule.createDefault();

private MyService mockService;

@Before
public void setUp() {
    // 1. Configuration
    testing.setConfig("ENVIRONMENT", "test");

    // 2. Share mock holder class
    testing.addSharedClass(MockServiceHolder.class);

    // 3. Share interface package (for interface cast across classloaders)
    testing.addSharedClassPrefix("com.mycompany.functions.myfunction.service.");

    // 4. Share OCI SDK (for BmcException catch to work)
    testing.addSharedClassPrefix("com.oracle.bmc.");

    // 5. Create and inject mock
    mockService = mock(MyService.class);
    MockServiceHolder.service = mockService;
}
```

**Key rules**:
- `addSharedClass()` — share the static holder class itself
- `addSharedClassPrefix("<interface-package>.")` — share the service interface so mock can be cast
- `addSharedClassPrefix("com.oracle.bmc.")` — share OCI SDK so BmcException identity matches across classloaders
- Never share the function class — this breaks `@FnConfiguration` isolation
