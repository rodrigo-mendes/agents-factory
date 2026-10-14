### ✅ Always Do

**Function Entry Point Declaration**: Every OCI Function MUST declare its entry point in `func.yaml` with the `cmd` field pointing to `ClassName::methodName`.

```yaml
# ✅ CORRECT: func.yaml with explicit entry point (FDK v1.0.186+)
schema_version: 20180708
name: api-handler
version: 0.0.1
runtime: java
build_image: fnproject/fn-java-fdk-build:jdk17-latest
run_image: fnproject/fn-java-fdk:jre17-latest
cmd: com.eci.serverless.handler.ApiHandler::handleRequest
memory: 256
timeout: 30
```

**Why it is mandatory**: The Fn runtime uses `cmd` to locate and invoke the function. Without it, the container starts but cannot route events.
**Failure if omitted**: Function deployment fails or invocations return 502.
**Source**: https://github.com/fnproject/fdk-java

---

**@FnConfiguration for One-Time Initialization**: Use `@FnConfiguration` to initialize OCI SDK clients, database connections, and expensive resources ONCE per container lifecycle (FDK v1.0.x+).

```java
// ✅ CORRECT: Heavy resources initialized once in @FnConfiguration (FDK v1.0.186+)
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.objectstorage.ObjectStorageClient;

public class ApiHandler {
    private ObjectStorageClient storageClient;
    private String namespace;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        // Called ONCE per container lifecycle (cold start only)
        var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        this.storageClient = ObjectStorageClient.builder().build(provider);
        this.namespace = ctx.getConfigurationByKey("OCI_NAMESPACE").orElseThrow();
    }

    public ApiResponse handleRequest(ApiRequest request) {
        // Called for EACH invocation — reuses pre-initialized client
        return processRequest(request, storageClient, namespace);
    }
}
```

**Why it is mandatory**: OCI SDK client creation involves network calls and is expensive. In hot functions, initializing per-invocation wastes the warm container benefit (10-100x slower).
**Failure if omitted**: Cold-start latency on every invocation, wasted compute, higher costs.
**Source**: https://github.com/fnproject/fdk-java/blob/master/docs/FunctionConfiguration.md

---

**Resource Principal Authentication**: OCI Functions MUST use `ResourcePrincipalAuthenticationDetailsProvider` for accessing OCI services. Dynamic Groups + IAM Policies grant permissions automatically.

```java
// ✅ CORRECT: Resource Principal for OCI SDK authentication (FDK v1.0.186+ / OCI SDK v3.x)
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.secrets.SecretsClient;

public class OciServiceClient {
    private final ObjectStorageClient objectStorageClient;
    private final SecretsClient secretsClient;

    public OciServiceClient() {
        // Resource Principal — authenticated via Dynamic Group + IAM Policy
        var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        this.objectStorageClient = ObjectStorageClient.builder().build(provider);
        this.secretsClient = SecretsClient.builder().build(provider);
    }
}
```

**Why it is mandatory**: API keys in code are a security vulnerability. Leaked credentials = full account compromise. Resource Principal is the only supported auth method for OCI Functions.
**Failure if omitted**: Security breach, credential rotation nightmare, violates OCI security best practices.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm

---

**JSON Data Binding with Jackson**: Use `@JsonIgnoreProperties(ignoreUnknown = true)` on all input POJOs for forward-compatibility. The FDK uses Jackson for automatic serialization when content-type is `application/json`.

```java
// ✅ CORRECT: Forward-compatible POJO with Jackson (FDK v1.0.186+)
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class ApiRequest {
    private String action;
    private String resourceId;
    private String bucketName;
    private String objectName;
    private String data;

    public String getAction() { return action; }
    public void setAction(String action) { this.action = action; }
    public String getResourceId() { return resourceId; }
    public void setResourceId(String resourceId) { this.resourceId = resourceId; }
    public String getBucketName() { return bucketName; }
    public void setBucketName(String bucketName) { this.bucketName = bucketName; }
    public String getObjectName() { return objectName; }
    public void setObjectName(String objectName) { this.objectName = objectName; }
    public String getData() { return data; }
    public void setData(String data) { this.data = data; }
}
```

**Why it is mandatory**: Without `ignoreUnknown = true`, new fields added to API payloads cause `UnrecognizedPropertyException` at runtime.
**Failure if omitted**: Function breaks when upstream adds new fields to request payload.
**Source**: https://github.com/fnproject/fdk-java/blob/master/docs/DataBinding.md

---

**Multi-Stage Docker Build**: Separate build (JDK + Maven) from runtime (JRE) to minimize image size and attack surface.

```dockerfile
# ✅ CORRECT: Multi-stage Docker build (FDK v1.0.186+ / JDK 17)
FROM fnproject/fn-java-fdk-build:jdk17-latest as build-stage
WORKDIR /function
ENV MAVEN_OPTS="-Dmaven.repo.local=/usr/share/maven/ref/repository"

ADD pom.xml /function/pom.xml
RUN ["mvn", "package", "dependency:copy-dependencies", "-DincludeScope=runtime", \
     "-DskipTests=true", "-Dmdep.prependGroupId=true", "-DoutputDirectory=target"]

ADD src /function/src
RUN ["mvn", "package", "-DskipTests=true"]

FROM fnproject/fn-java-fdk:jre17-latest
WORKDIR /function
COPY --from=build-stage /function/target/*.jar /function/app/
CMD ["com.eci.serverless.handler.ApiHandler::handleRequest"]
```

**Why it is mandatory**: Single-stage builds include JDK, Maven, and build artifacts in the runtime image — increasing size, cold start time, and attack surface.
**Failure if omitted**: Larger images, slower cold starts, unnecessary tools in production container.
**Source**: https://github.com/fnproject/fdk-java

---

**FnTestingRule for Unit Tests**: Use the official `FnTestingRule` (JUnit 4 Rule) to emulate the Fn runtime locally with class loader isolation between invocations.

```java
// ✅ CORRECT: FnTestingRule with hot function simulation (FDK v1.0.186+)
import com.fnproject.fn.testing.FnTestingRule;
import com.fnproject.fn.testing.FnResult;
import org.junit.Rule;
import org.junit.Test;
import static org.junit.Assert.*;

public class ApiHandlerTest {
    @Rule
    public final FnTestingRule testing = FnTestingRule.createDefault();

    @Test
    public void testHelloAction() {
        testing.setConfig("OCI_REGION", "us-ashburn-1");

        testing.givenEvent()
            .withBody("{\"action\": \"hello\"}")
            .enqueue();

        testing.thenRun(ApiHandler.class, "handleRequest");

        FnResult result = testing.getOnlyResult();
        assertNotNull(result);
        assertTrue(result.getBodyAsString().contains("\"status\":200"));
    }

    @Test
    public void testHotFunctionBehavior() {
        // Multiple events simulate hot function — same JVM, multiple invocations
        testing.givenEvent().withBody("{\"action\": \"hello\"}").enqueue();
        testing.givenEvent().withBody("{\"action\": \"hello\"}").enqueue();
        testing.givenEvent().withBody("{\"action\": \"hello\"}").enqueue();

        testing.thenRun(ApiHandler.class, "handleRequest");

        assertEquals(3, testing.getResults().size());
    }
}
```

**Why it is mandatory**: FnTestingRule simulates class loader isolation and `@FnConfiguration` lifecycle. Raw JUnit tests miss container-specific behavior.
**Failure if omitted**: Tests pass locally but function fails in production due to class loading or configuration differences.
**Source**: https://github.com/fnproject/fdk-java/blob/master/docs/TestingFunctions.md

---

