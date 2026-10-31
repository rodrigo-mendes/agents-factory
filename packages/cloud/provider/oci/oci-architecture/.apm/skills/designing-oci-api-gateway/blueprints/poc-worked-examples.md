# Worked Examples (from the reference PoC)

These examples are extracted from `workspace/poc-oci-serverless/` — a validated, deployed PoC
(status: delivered 2026-05-14). Cite paths when explaining patterns to users.

---

## Pattern 03 — API Facade (`services/func-api-facade/`)

**Source**: `workspace/poc-oci-serverless/services/func-api-facade/src/main/java/com/example/functions/apifacade/ApiFacadeFunction.java`

The API Facade pattern uses a single OCI Function as a unified backend for multiple routes, each
handled by a `switch` on the extracted route path. The API Gateway routes all requests through one
`ORACLE_FUNCTIONS_BACKEND`:

```java
// ApiFacadeFunction.java (extract)
// Route dispatch — path extracted from the full API Gateway-forwarded URL
switch (path) {
    case "/hello":   responseEvent = handleHello(req);          break;
    case "/secret":  responseEvent = handleSecret(req);         break;
    case "/store":   responseEvent = handleStore(req);          break;
    case "/health":
    case "/diag":    responseEvent = handleHealth(isColdStart); break;
    default:         responseEvent = error(404, "Route not found: " + path);
}
```

**Key design decisions shown in this PoC**:
- `extractRoutePath()` strips the API Gateway path prefix (`/v1/facade/hello` → `/hello`).
- `opc-request-id` from the API Gateway request header is propagated via `MDC` for end-to-end
  correlation across API Gateway access logs and Function execution logs.
- `traceparent` W3C header is forwarded from the API Gateway to seed an OpenTelemetry span inside
  the Function (requires API Gateway passthrough header policy).
- Cold-start flag (`boolean coldStart`) is tracked per container instance — the first invocation
  is marked and OCI Monitoring receives a custom `cold_start` metric via `ObservabilityHelper`.

**API Gateway route mapping** for this facade (Terraform pattern):
```hcl
# Each route maps to the SAME function OCID — routing is done inside the function
route_backends = [
  { path = "/hello",  methods = ["GET"],  function_id = oci_functions_function.api_facade.id },
  { path = "/secret", methods = ["POST"], function_id = oci_functions_function.api_facade.id },
  { path = "/store",  methods = ["POST"], function_id = oci_functions_function.api_facade.id },
  { path = "/health", methods = ["GET"],  function_id = oci_functions_function.api_facade.id },
]
```

---

## Pattern 01 — Request-Reply REST Proxy (`services/func-rr-rest-proxy/`)

**Source**: `workspace/poc-oci-serverless/services/func-rr-rest-proxy/` and
`workspace/poc-oci-serverless/docs/patterns/01-request-reply/reference/rest-proxy/`

The REST Proxy pattern uses the Function as a protocol bridge: receives JSON from the API Gateway,
fetches data from an upstream REST API (Oracle RMS) with OAuth2, transforms the response to XML,
and forwards it to a downstream REST API (TargetServices).

```java
// RestProxyFunction.java (extract) — thin dispatcher delegates to domain handlers
// Path routing uses a Route enum; business logic in StoreProxyHandler / ItemWebhookHandler
switch (Route.from(path)) {
    case STORE_CREATE -> responseEvent = storeHandler.handleCreate(req);
    case STORE_UPDATE -> responseEvent = storeHandler.handleUpdate(req);
    case ITEM_WEBHOOK -> responseEvent = webhookHandler.handle(req);
    default           -> responseEvent = responses.notFound(path);
}
```

**OpenAPI contract** — the upstream RMS API spec (`docs/patterns/01-request-reply/reference/rest-proxy/openapi.yaml`)
describes the store endpoint consumed by the proxy:
```yaml
# openapi.yaml (extract) — Oracle RMS REST Services v25.1.403.0
paths:
  /services/private/Store/storeDetail:
    get:
      operationId: getStoreDetail
      parameters:
        - name: store
          in: query
          required: true
```

**API Gateway route design for REST Proxy**:
- One deployment, multiple routes: `POST /v1/proxy/store/create`, `POST /v1/proxy/store/update`,
  `POST /v1/proxy/item/webhook`.
- Authentication: `ANONYMOUS` on the webhook route (signature verified inside the Function);
  `JWT` on the store routes.
- The Function uses Vault (`OciSecretService`) to retrieve the OAuth2 `client_secret` at runtime —
  no credentials in `func.yaml` config.

**Collaborator pattern**: Unlike the API Facade's `switch`, the REST Proxy wires collaborators in
`@FnConfiguration` (cold-start) and delegates to typed handlers. This keeps `configure()` as an
initialization step and `handler()` as a thin dispatcher — the recommended pattern for Functions
with multiple route responsibilities.

---

## Observability integration (shared pattern, both services)

Both `func-api-facade` and `func-rr-rest-proxy` share the same observability approach:

1. **MDC correlation**: `opc-request-id`, `route`, `method`, `coldStart` set at request entry,
   cleared in `finally` to protect warm-container executions.
2. **OTel spans**: `SERVER` span created at entry with `traceparent` from the API Gateway
   passthrough header; `CLIENT` child spans wrap downstream SDK/HTTP calls
   (`Vault.GetSecret`, `ObjectStorage.PutObject`, `RmsClient.getStoreDetail`).
3. **OCI Monitoring custom metrics**: `invocation_count`, `duration_ms`, `error_count` posted
   via `ObservabilityHelper.postInvocation/postDuration/postError` — not relying on built-in
   Function metrics alone, allowing per-route alerting.

> The API Gateway must be configured with `execution_log_level = "INFO"` and
> `access_log.is_enabled = true` to correlate `opc-request-id` across gateway access logs and
> Function execution logs in the same OCI Logging search.
