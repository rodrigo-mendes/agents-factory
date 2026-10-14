## Integration Patterns

### OCI Functions ↔ API Gateway (fn-events)

**Official Library**: `com.fnproject.fn:fn-events:1.1.11`
**Compatibility**: FDK v1.1.x+, API Gateway

```xml
<!-- pom.xml dependency for fn-events -->
<dependency>
    <groupId>com.fnproject.fn</groupId>
    <artifactId>fn-events</artifactId>
    <version>${fdk.version}</version>
</dependency>
```

**Integration Pattern**:
```java
// Complete API Gateway function with typed request/response (FDK v1.1.x)
import com.fnproject.events.APIGatewayFunction;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.Headers;
import java.util.Optional;
import java.util.UUID;

public class GatewayHandler extends APIGatewayFunction<RequestDto, ResponseDto> {

    @Override
    public APIGatewayResponseEvent<ResponseDto> handler(
            APIGatewayRequestEvent<RequestDto> requestEvent) {

        // Access query parameters
        Optional<String> id = requestEvent.getQueryParameters().get("id");

        // Access typed body
        RequestDto body = requestEvent.getBody();

        // Access HTTP method
        String method = requestEvent.getMethod();

        // Build typed response with status code and headers
        ResponseDto response = new ResponseDto();
        response.setResult("processed");

        return new APIGatewayResponseEvent.Builder<ResponseDto>()
            .statusCode(200)
            .headers(Headers.emptyHeaders()
                .addHeader("X-Request-Id", UUID.randomUUID().toString()))
            .body(response)
            .build();
    }
}
```

**Source**: https://github.com/fnproject/fdk-java/blob/master/fn-events/README.md

---

### OCI Functions ↔ OCI Vault (Secrets)

**Official Library**: `com.oracle.oci.sdk:oci-java-sdk-secrets` (via BOM)
**Compatibility**: OCI SDK v3.0+, FDK v1.0.186+

**Integration Pattern**:
```java
// Retrieve secrets from OCI Vault using Resource Principal (OCI SDK v3.x)
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.secrets.SecretsClient;
import com.oracle.bmc.secrets.model.Base64SecretBundleContentDetails;
import com.oracle.bmc.secrets.requests.GetSecretBundleRequest;
import com.oracle.bmc.secrets.responses.GetSecretBundleResponse;
import java.util.Base64;

public class VaultSecretReader {
    private final SecretsClient secretsClient;

    public VaultSecretReader() {
        var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        this.secretsClient = SecretsClient.builder().build(provider);
    }

    public String getSecret(String secretId) {
        GetSecretBundleResponse response = secretsClient.getSecretBundle(
            GetSecretBundleRequest.builder()
                .secretId(secretId)
                .build());

        Base64SecretBundleContentDetails content =
            (Base64SecretBundleContentDetails) response.getSecretBundle()
                .getSecretBundleContent();

        return new String(Base64.getDecoder().decode(content.getContent()));
    }
}
```

**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm

---

### OCI Functions ↔ Object Storage

**Official Library**: `com.oracle.oci.sdk:oci-java-sdk-objectstorage` (via BOM)
**Compatibility**: OCI SDK v3.0+, FDK v1.0.186+

**Integration Pattern**:
```java
// Store data in Object Storage from a function (OCI SDK v3.x)
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

public class ObjectStorageWriter {
    private final ObjectStorageClient client;

    public ObjectStorageWriter(ObjectStorageClient client) {
        this.client = client;
    }

    public void putObject(String namespace, String bucketName,
                          String objectName, String data) {
        byte[] bytes = data.getBytes(StandardCharsets.UTF_8);

        client.putObject(
            PutObjectRequest.builder()
                .namespaceName(namespace)
                .bucketName(bucketName)
                .objectName(objectName)
                .contentLength((long) bytes.length)
                .putObjectBody(new ByteArrayInputStream(bytes))
                .build());
    }
}
```

**Source**: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/javasdk.htm

---

