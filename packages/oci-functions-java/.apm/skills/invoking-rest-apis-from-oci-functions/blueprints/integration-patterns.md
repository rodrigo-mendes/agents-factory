## Integration Patterns

### OCI Functions ↔ OCI Object Storage

**Official Module**: `oci-java-sdk-objectstorage`
**Compatibility**: OCI SDK v3.x+, Java 17

```java
// ✅ Complete pattern: Read object from Object Storage in a Function
// OCI SDK v3.x+ with Resource Principal and function-appropriate timeouts
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.GetObjectRequest;
import com.oracle.bmc.objectstorage.responses.GetObjectResponse;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    this.objectStorageClient = ObjectStorageClient.builder()
        .configuration(ClientConfiguration.builder()
            .connectionTimeoutMillis(5000)
            .readTimeoutMillis(15000)
            .build())
        .build(provider);
}

public String handleRequest(String objectName) {
    GetObjectResponse response = objectStorageClient.getObject(
        GetObjectRequest.builder()
            .namespaceName("my-namespace")
            .bucketName("my-bucket")
            .objectName(objectName)
            .build());
    // response.getInputStream() contains the object content
    return "Retrieved: " + objectName;
}
```

**Required IAM Policy**:
```
allow dynamic-group <dg-name> to manage objects in compartment <compartment>
```

**Source**: [Oracle Functions Samples — Object Storage](https://github.com/oracle-samples/oracle-functions-samples/blob/master/samples/oci-objectstorage-put-object-java/src/main/java/com/example/fn/ObjectStoragePutObject.java)

---

### OCI Functions ↔ OCI Vault (Secrets)

**Official Module**: `oci-java-sdk-secrets`
**Compatibility**: OCI SDK v3.x+, Java 17

```java
// ✅ Complete pattern: Retrieve API key from OCI Vault at cold start
// OCI SDK v3.x+ — secret fetched once, cached for hot invocations
import com.oracle.bmc.secrets.SecretsClient;
import com.oracle.bmc.secrets.requests.GetSecretBundleRequest;
import com.oracle.bmc.secrets.model.Base64SecretBundleContentDetails;
import java.util.Base64;

private String apiKey;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    SecretsClient secretsClient = SecretsClient.builder().build(provider);

    String secretId = ctx.getConfigurationByKey("API_KEY_SECRET_ID").orElseThrow();
    var response = secretsClient.getSecretBundle(
        GetSecretBundleRequest.builder().secretId(secretId).build());
    Base64SecretBundleContentDetails content =
        (Base64SecretBundleContentDetails) response.getSecretBundle().getSecretBundleContent();
    this.apiKey = new String(
        Base64.getDecoder().decode(content.getContent()), StandardCharsets.UTF_8);

    secretsClient.close(); // Close after fetching — not needed for hot invocations
}
```

**Required IAM Policy**:
```
allow dynamic-group <dg-name> to read secret-bundles in compartment <compartment>
```

**Source**: [OCI Vault Security Skill](../../skills/designing-oci-vault-security/SKILL.md)

---

### OCI Functions ↔ External REST APIs

**Library**: `java.net.http.HttpClient` (Java 17 built-in — no external dependency)
**Compatibility**: Java 11+, recommended Java 17

```java
// ✅ Complete pattern: POST to external API with auth from Vault
// Java 17 HttpClient — zero external dependencies
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

private HttpClient httpClient;
private String apiBaseUrl;
private String apiKey;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    this.httpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(5))
        .version(HttpClient.Version.HTTP_1_1)
        .build();
    this.apiBaseUrl = ctx.getConfigurationByKey("API_BASE_URL").orElseThrow();
    // apiKey loaded from OCI Vault (see Vault integration above)
}

public String handleRequest(String input) throws Exception {
    HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create(apiBaseUrl + "/api/v1/data"))
        .header("Content-Type", "application/json")
        .header("Authorization", "Bearer " + apiKey)
        .header("Accept", "application/json")
        .timeout(Duration.ofSeconds(10))
        .POST(HttpRequest.BodyPublishers.ofString(input))
        .build();

    HttpResponse<String> response = httpClient.send(
        request, HttpResponse.BodyHandlers.ofString());

    LOG.info("External API: status=" + response.statusCode());

    if (response.statusCode() >= 200 && response.statusCode() < 300) {
        return response.body();
    } else if (response.statusCode() == 429) {
        throw new RuntimeException("External API rate limited");
    } else {
        throw new RuntimeException("External API error: HTTP " + response.statusCode());
    }
}
```

**Network Requirements**:
```
# If function is in a VCN subnet:
# 1. NAT Gateway — required for outbound internet access
# 2. Route rule directing 0.0.0.0/0 to NAT Gateway
# If function is NOT in a VCN (default):
# - Can access internet directly via public endpoints
```

**Source**: [Java 17 HttpClient API](https://docs.oracle.com/en/java/javase/17/docs/api/java.net.http/java/net/http/HttpClient.html)

---

## Worked Example (from the reference PoC)

### HttpRetryExecutor — reusable send-with-retry engine
// from services/func-evt-consumer-notify/src/main/java/com/brx/functions/event/consumer/notify/client/http/HttpRetryExecutor.java

```java
public class HttpRetryExecutor {
    private static final int MAX_RETRIES = 2;
    private final HttpClient httpClient;
    private final String serviceName;

    public interface ResponseHandler<T> {
        T onSuccess(HttpResponse<String> response) throws IOException;
        IOException onFailure(HttpResponse<String> response);
    }

    public <T> T execute(HttpRequest request, ResponseHandler<T> handler)
            throws IOException, InterruptedException {
        for (int attempt = 0; attempt <= MAX_RETRIES; attempt++) {
            try {
                HttpResponse<String> response = httpClient.send(request,
                        HttpResponse.BodyHandlers.ofString());
                int status = response.statusCode();

                if (status >= 200 && status < 300) return handler.onSuccess(response);

                if (status >= 500 && attempt < MAX_RETRIES) {
                    // exponential backoff: 2^attempt * 1000ms
                    Thread.sleep((long) Math.pow(2, attempt) * 1000);
                    continue;
                }
                throw handler.onFailure(response);
            } catch (HttpTimeoutException e) {
                if (attempt < MAX_RETRIES) {
                    Thread.sleep((long) Math.pow(2, attempt) * 1000);
                } else {
                    throw new HttpTimeoutException(serviceName + " timeout after " + MAX_RETRIES + " retries");
                }
            }
        }
        throw new IOException(serviceName + " request failed after retries");
    }
}
```

Key design decisions:
- 3 total sends (initial + 2 retries); exponential backoff 1s, 2s
- 5xx and timeout are retried; 4xx is not (client error, retry won't help)
- `ResponseHandler` interface keeps success mapping and error message in the calling client
- `serviceName` field for contextual log messages

### TracedCall — collapses start/end span boilerplate into one place
// from services/func-evt-consumer-notify/src/main/java/com/brx/functions/event/consumer/notify/obs/TracedCall.java

```java
public final class TracedCall {
    public static <T> T run(String spanName, String peerService,
                            Map<String, String> attributes, Callable<T> call) throws Exception {
        Span span = ObservabilityHelper.startChildSpan(spanName);
        span.setAttribute("peer.service", peerService);
        attributes.forEach(span::setAttribute);
        try {
            T result = call.call();
            ObservabilityHelper.endSpan(span, (Throwable) null);
            return result;
        } catch (Exception e) {
            ObservabilityHelper.endSpan(span, e);
            throw e; // always re-throw unchanged
        }
    }
}
```

Usage pattern: `TracedCall.run("POST /notify", "notification-service", Map.of("eventId", id), () -> notifyClient.send(payload));`

### OciServiceClient — Vault + Object Storage initialization in configure()
// from services/func-api-facade/src/main/java/com/brx/functions/apifacade/service/OciServiceClient.java

```java
// Both clients initialized once with ResourcePrincipal + retry config
AbstractAuthenticationDetailsProvider provider =
        ResourcePrincipalAuthenticationDetailsProvider.builder().build();

RetryConfiguration retryConfig = RetryConfiguration.builder()
        .terminationStrategy(new MaxAttemptsTerminationStrategy(3))
        .delayStrategy(new ExponentialBackoffDelayStrategyWithJitter(5000))
        .build();

ClientConfiguration clientConfig = ClientConfiguration.builder()
        .connectionTimeoutMillis(5000)
        .readTimeoutMillis(15000)
        .retryConfiguration(retryConfig)
        .build();

this.objectStorageClient = ObjectStorageClient.builder()
        .configuration(clientConfig).build(provider);
this.secretsClient = SecretsClient.builder()
        .configuration(clientConfig).build(provider);

// Vault secret retrieval
public String getSecret(String secretId) {
    GetSecretBundleResponse response = secretsClient.getSecretBundle(
            GetSecretBundleRequest.builder().secretId(secretId).build());
    Base64SecretBundleContentDetails content =
            (Base64SecretBundleContentDetails) response.getSecretBundle().getSecretBundleContent();
    return new String(Base64.getDecoder().decode(content.getContent()), StandardCharsets.UTF_8);
}
```

