# Worked Examples (from the reference PoC)

These examples are extracted from `workspace/poc-oci-serverless/` — a validated, deployed PoC
(Pattern 03 deployed 2026-05-14; Pattern 01 deployed subsequently). Cite paths when explaining
patterns to users.

---

## Pattern 03 — API Facade: end-to-end architecture

**Source**: `workspace/poc-oci-serverless/docs/patterns/03-api-facade/03-api-facade.md`
and `workspace/poc-oci-serverless/services/func-api-facade/`

**Architecture** (delivered, deployed):
```
Internet
  │ HTTPS/TLS 1.2+
  ▼
API Gateway (public subnet, NSG: 443 inbound)
  │ ORACLE_FUNCTIONS_BACKEND (VCN internal)
  ▼
func-api-facade (private subnet, Resource Principal)
  ├── Vault (secret retrieval via OCI SDK)
  └── Object Storage (PutObject via OCI SDK)
```

**IAM chain** proven in the PoC:
- Dynamic Group matching Functions in the compartment → `fn-invocation` policy for the gateway
- `Allow service FaaS to use virtual-network-family in compartment <name>` (enables function networking)
- `Allow dynamic-group fn-dg to read secret-bundles in compartment <name>` (Vault access)
- `Allow dynamic-group fn-dg to manage objects in compartment <name> where target.bucket.name = '<bucket>'`

**Cold-start pattern** (`ApiFacadeFunction.configure()`):
```java
// @FnConfiguration executes once per container — this is the cold-start initialization path
@Override @FnConfiguration
public void configure(RuntimeContext ctx) {
    super.configure(ctx);
    this.environment = ctx.getConfigurationByKey("ENVIRONMENT").orElse("dev");
    ObservabilityHelper.configure(ctx);   // Registers JUL→SLF4J bridge + OCI Monitoring client
    if (this.ociClient == null) {
        this.ociClient = loadOciClient();  // Initializes ResourcePrincipal SDK clients
    }
    // Log cold-start duration for APM baseline
    log.info("COLD_START completed in {}ms | env={}", elapsed, environment);
}
```
The pattern: expensive initialization (SDK client wiring, `ResourcePrincipalAuthenticationDetailsProvider`)
happens once in `configure()`, not in `handler()`. Warm invocations skip this path entirely.

---

## Pattern 01 — Request-Reply REST Proxy: multi-backend routing

**Source**: `workspace/poc-oci-serverless/services/func-rr-rest-proxy/` and
`workspace/poc-oci-serverless/docs/patterns/01-request-reply/reference/rest-proxy/`

**Architecture** (multiple routes, single Function Application):
```
API Gateway
  ├── POST /v1/proxy/store/create  ─► func-rr-rest-proxy ─► OAuth2 → RMS → transform → TargetServices
  ├── POST /v1/proxy/store/update  ─► func-rr-rest-proxy ─► OAuth2 → RMS → transform → TargetServices
  └── POST /v1/proxy/item/webhook  ─► func-rr-rest-proxy ─► signature check → forward
```

**Secret retrieval at runtime** (shown in `OciSecretService.java`):
```java
// Functions NEVER store OAuth2 client_secret in func.yaml config.
// Only the Vault secret OCID is stored in config; the value is fetched at runtime.
String secretOcid = ctx.getConfigurationByKey("OAUTH2_SECRET_OCID").orElseThrow();
// OciSecretService uses ResourcePrincipalAuthenticationDetailsProvider → Vault SDK
String clientSecret = ociSecretService.getSecretValue(secretOcid);
```

**Handler collaborator pattern** (thin dispatcher):
```java
// RestProxyFunction.java — handler() is a thin dispatcher; no business logic here
switch (Route.from(path)) {
    case STORE_CREATE -> responseEvent = storeHandler.handleCreate(req);
    case STORE_UPDATE -> responseEvent = storeHandler.handleUpdate(req);
    case ITEM_WEBHOOK -> responseEvent = webhookHandler.handle(req);
    default           -> responseEvent = responses.notFound(path);
}
```
Compare with the API Facade's inline `switch`: the REST Proxy extracts handlers as collaborators
wired in `configure()` — preferred when handlers have their own dependencies (HTTP clients, mappers).

---

## Function Application composition (from PoC Terraform structure)

The PoC uses one **Functions Application** hosting multiple functions, each as a separate
`oci_functions_function` resource pointing to its own OCIR image:

```
infra/environments/dev/
  apps.tf
    module "app_api_facade"  → modules/function-app  (image: func-api-facade:latest)
    module "app_rr_proxy"    → modules/function-app  (image: func-rr-rest-proxy:latest)

infra/modules/api-gateway/
  routes are configured via var.route_backends — one list, multiple function OCIDs
```

**Key constraint**: Each function has its own memory and timeout configuration. The API Facade uses
128 MB / 60 s; the REST Proxy uses 256 MB / 120 s (upstream HTTP calls with OAuth2 are slower).
Confirm sizing in `func.yaml` before provisioning.

---

## Observability architecture (both patterns)

Both functions emit the same three observability signals:
1. **Structured logs** → OCI Logging (JUL→SLF4J bridge + MDC with `opc-request-id`, `route`)
2. **OTel traces** → APM (`SERVER` span per request, `CLIENT` child spans per downstream call)
3. **Custom OCI Monitoring metrics** → per-route `invocation_count`, `duration_ms`, `error_count`

The custom metrics enable per-route alarms — the built-in OCI Functions metrics are per-function,
not per-route. This is the "Management Dashboards" pattern referenced in the Always-Do patterns of
`architecting-oci-serverless`.

> For dashboard provisioning, use `provisioning-custom-dashboard-oci-observability` (owner:
> `@oci-observability`). Widget shapes must come from the OCI Console `{JSON}` editor — see
> `designing-oci-observability` skill for the render-valid constraint.
