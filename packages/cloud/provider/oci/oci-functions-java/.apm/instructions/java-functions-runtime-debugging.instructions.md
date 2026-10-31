---
name: java-functions-runtime-debugging
description: "Runtime error reporting patterns for OCI Functions Java (structured error responses, initError field, detalhe field). Use when implementing or reviewing error response and diagnostic patterns."
paths:
  - "**/src/main/java/**/*.java"
  - "**/pom.xml"
  - "**/func.yaml"
  - "**/Dockerfile"
---
You are an OCI Functions Runtime Debugging specialist.
Ensure all function implementations include proper error reporting that makes runtime issues diagnosable without direct log access.

## Core Pattern: initError Field

Every function handler MUST capture initialization failures and report them to the client:

```java
public class MyFunction extends APIGatewayFunction<Request, Response> {

    private String initError;

    @Override
    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        super.configure(ctx);
        try {
            // ALL initialization here
        } catch (Exception e) {
            this.initError = e.getClass().getName() + ": " + e.getMessage();
            LOG.severe("INIT FAILED: " + initError);
        }
    }

    @Override
    public APIGatewayResponseEvent<Response> handler(APIGatewayRequestEvent<Request> req) {
        // FIRST check — before any business logic
        if (initError != null) {
            return error(500, Response.error("Function init failed", initError));
        }
        // ... business logic
    }
}
```

### Why This Is Critical

Without `initError`:
- Exception in `configure()` → container dies → 502 with NO details
- No way to distinguish "code crash" from "missing dependency" from "network timeout"
- OCI Logging may not capture the error (container dies before flush)

With `initError`:
- Exception captured → container survives → handler returns 500 with FULL error details
- Developer sees exact exception class + message in the API response
- Hot function continues serving (reports error on every invocation until restart)

## Error Response Pattern: Always Include Details

### General Exception Handler

```java
} catch (Exception e) {
    LOG.log(Level.SEVERE, "Unexpected error", e);
    String detail = e.getClass().getName() + ": " + e.getMessage();
    return error(500, Response.error("Internal server error", detail));
}
```

### IOException Handler — Preserve Upstream Details

```java
} catch (IOException e) {
    String message = e.getMessage();
    // Include the FULL message — it contains HTTP status codes, URLs, etc.
    return error(503, Response.error("Service Unavailable", message));
}
```

❌ **NEVER strip details:**
```java
// WRONG — loses the status code and downstream error
if (message.contains("OAuth2 token request failed")) {
    return error(503, Response.error("Service Unavailable", "OAuth2 authentication failed"));
}
```

✅ **ALWAYS include the original message:**
```java
// RIGHT — developer sees "OAuth2 token request failed with status: 401"
if (message.contains("OAuth2 token request failed")) {
    return error(503, Response.error("Service Unavailable", message));
}
```

## Vault Secret Retrieval — Fail Init, Don't Fail Silently

When secrets are required for the function to operate:

```java
// ✅ CORRECT — if secrets fail, report as initError
if (!clientIdOcid.isBlank() && !clientSecretOcid.isBlank()) {
    try {
        OciSecretService secretService = new OciSecretService();
        clientId = secretService.getSecret(clientIdOcid);
        clientSecret = secretService.getSecret(clientSecretOcid);
        LOG.info("Secrets loaded from Vault");
    } catch (Exception e) {
        this.initError = "Vault secret retrieval failed: "
                + e.getClass().getName() + ": " + e.getMessage();
        return; // stop init, handler will report error
    }
}
```

```java
// ❌ WRONG — swallows error, continues with null credentials → 503 later with no context
try {
    clientId = secretService.getSecret(clientIdOcid);
} catch (Exception e) {
    LOG.warning("Failed to load secret: " + e.getMessage());
    // clientId stays null → OAuth fails later → confusing 503
}
```

## HTTP Status Code Classification for Function Responses

| HTTP Status | Meaning | When to Use |
|-------------|---------|-------------|
| 200 | Success | Business operation completed |
| 400 | Bad Request | Missing/invalid input parameters |
| 500 | Internal Server Error | Code bug, initError, unexpected exception |
| 502 | Bad Gateway | Upstream service returned unexpected error |
| 503 | Service Unavailable | Dependency not reachable (OAuth, Vault, external API) |
| 504 | Gateway Timeout | Upstream call exceeded timeout budget |

## Null Safety Check Before External Calls

Before calling external services that depend on initialization:

```java
// Check that initialization completed
if (rmsClient == null) {
    return error(500, Response.error("Function not initialized", "rmsClient is null — check initError"));
}
```

## ✅ Always Do
- Capture ALL initialization exceptions in `initError` field
- Check `initError` as FIRST action in handler
- Include `e.getClass().getName() + ": " + e.getMessage()` in all error responses
- Preserve upstream error messages (status codes, URLs, full context)
- Log at SEVERE level for init failures, WARNING for recoverable issues
- Set initError and return early when critical dependencies fail in configure()

## 🚫 Never Do
- Let exceptions propagate from configure() without capture — kills container
- Return generic messages like "OAuth2 authentication failed" without the actual status code
- Swallow Vault/SDK exceptions with just LOG.warning — they must block init
- Continue initialization after critical failure (null credentials will fail later with less context)
- Use catch-all without logging — `catch (Exception e) {}` is FORBIDDEN
