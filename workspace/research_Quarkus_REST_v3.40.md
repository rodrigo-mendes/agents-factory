# Research: Quarkus REST (quarkus-rest, quarkus-rest-jackson, quarkus-rest-client) — Quarkus 3.40.x LTS

> Version lock: every claim targets **Quarkus 3.40.x** (3.40.1 as used by Camel Quarkus 3.40.x). Patterns from Quarkus 3.15 or earlier, and from Quarkus 4.0 Beta, are NOT valid for this version unless stated.
> Research date: 2026-10-14. All pages accessed 2026-10-14. Versioned pages (`/version/3.40/`) are preferred; unversioned/`latest`/main-branch evidence is capped at Medium.
> Workflow note: this run is a forked batch from an orchestrator. The plan-approval step (EnterPlanMode/ExitPlanMode) was skipped because no user was available in the fork; the user approved the batch scheme in the parent session. Section-investigators were NOT spawned (orchestrator constraint); all pages were fetched directly by this agent.

---

## Metadata

```yaml
Full_Name: Quarkus REST (Jakarta REST server, successor of RESTEasy Reactive) + Quarkus REST Client + quarkus-rest-jackson
Target_Version: Quarkus 3.40.x (3.40.1)
Release_Date: 2026-09-30 (Quarkus 3.40 LTS)            # https://quarkus.io/releases (family facts, High)
Support_Status: LTS, community-maintained until 2027-09-30   # https://quarkus.io/releases (family facts, High)
Primary_Docs: https://quarkus.io/version/3.40/guides/rest
Secondary_Docs:
  - https://quarkus.io/version/3.40/guides/rest-client
  - https://quarkus.io/version/3.40/guides/rest-json
Official_Repo: https://github.com/quarkusio/quarkus
Research_Date: 2026-10-14
Domain_Complexity: Complex   # HTTP server + client, threading model, security, TLS, Camel integration
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 4
Unverified_Count: 6
Irresolvable_Count: 2
Research_Quality_Score: 89%   # (74 claims - 6 unverified - 2 irresolvable) / 74
```

---

## Executive Summary

Quarkus REST (`io.quarkus:quarkus-rest`) is the Quarkus Jakarta REST implementation "rebuilt on Vert.x, fully reactive, and tightly integrated with build-time processing"; the 3.40 guide names it as the successor of RESTEasy Reactive (High, https://quarkus.io/version/3.40/guides/rest). JSON comes from `quarkus-rest-jackson` or `quarkus-rest-jsonb`; XML from `quarkus-rest-jaxb` (High, same page). The matching client is `quarkus-rest-client` / `quarkus-rest-client-jackson`; the 3.40 guide states "the `quarkus-resteasy-client` extension may not be used with Quarkus REST, use `quarkus-rest-client` instead" (High, https://quarkus.io/version/3.40/guides/rest). Quarkus 3.40 is an LTS released 2026-09-30, community-maintained until 2027-09-30 (High, https://quarkus.io/releases, from family facts); Camel Quarkus 3.40.x runs on Quarkus 3.40.1 (High, https://camel.apache.org/camel-quarkus/latest/, from family facts).

The three critical patterns for 3.40 are: (1) **the method signature picks the thread**. `Uni`/`Multi`/`CompletionStage`/`Publisher` return types run on the IO thread; anything else is blocking. Use `@Blocking`, `@NonBlocking` or `@RunOnVirtualThread` (blocking-signature endpoints only) to override (High, https://quarkus.io/version/3.40/guides/rest + https://quarkus.io/version/3.40/guides/virtual-threads). (2) **REST client configuration is mandatory and named**. The base URL is "mandatory"; timeouts default to 15000 ms connect / 30000 ms read; TLS goes through `quarkus.rest-client."key".tls-configuration-name` pointing to a named `quarkus.tls.<name>` bucket, because client extensions ignore the default bucket except `trust-all` (High, https://quarkus.io/version/3.40/guides/rest-client + https://quarkus.io/version/3.40/guides/tls-registry-reference). (3) **Errors and security are explicit**. Quarkus REST "does not log [exceptions] by default (for security reasons)"; `@ServerExceptionMapper` inside a resource class applies only to that class; CORS is off by default (`quarkus.http.cors.enabled=false`) and `origins=*` in prod is called a severe risk (High, rest guide + https://quarkus.io/version/3.40/guides/security-cors).

Domain tier: **Complex**. The extension covers a reactive server, a client, a security layer (annotations plus HTTP permissions plus proactive auth), TLS and the Camel bridge. On the Camel question: the Camel Quarkus example `quarkus-rest-json` (main branch, pom pins Quarkus platform 3.40.1) injects `ProducerTemplate` into a Jakarta REST `@Path` resource and calls `requestBody("direct:processOrder", ...)`. That makes it an officially published Camel pattern, at Medium confidence (main-branch evidence). Quarkus 4.0.0.Beta1 (2026-10-01) moves to Java 21 and Jackson 3 (`ObjectMapperCustomizer` renamed `JsonMapperBuilderCustomizer`). None of that applies to 3.40 (High, https://quarkus.io/blog/quarkus-4-0-0-beta1-released/; Medium, https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0).

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)
> Every default/number carries its source URL inline. "UNVERIFIED" = not confirmed by an official page in this run.

### ✅ Mandatory Patterns

**M1. Use the Quarkus REST artifacts (not RESTEasy Classic / resteasy-client) — 3.40**
> Confidence: 🟢 High | [✓✓ Triangulated | https://quarkus.io/version/3.40/guides/rest (2026-10-14) + https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/quarkus-rest-json/pom.xml (main, 2026-10-14)]
- Why: The 3.40 rest guide names `quarkus-rest`, `quarkus-rest-jackson`, `quarkus-rest-jsonb` and `quarkus-rest-jaxb`, and says `quarkus-resteasy-client` "may not be used with Quarkus REST". The Camel Quarkus example pom (Quarkus platform 3.40.1) uses `quarkus-rest` + `quarkus-rest-jackson`.
- Code:
  ```xml
  <!-- Quarkus 3.40.x — versions come from the Quarkus/Camel Quarkus BOM -->
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest</artifactId></dependency>
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest-jackson</artifactId></dependency>
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest-client-jackson</artifactId></dependency>
  ```
- Source: https://quarkus.io/version/3.40/guides/rest , https://quarkus.io/version/3.40/guides/rest-client (2026-10-14)

**M2. Choose the thread model deliberately (signature, @Blocking, @NonBlocking, @RunOnVirtualThread) — 3.40**
> Confidence: 🟢 High | [✓✓ Triangulated | https://quarkus.io/version/3.40/guides/rest (2026-10-14) + https://quarkus.io/version/3.40/guides/virtual-threads (2026-10-14)]
- Why: "the thread Quarkus REST will run endpoint methods on depends on the signature of the method". `Uni`, `Multi`, `CompletionStage`, `Publisher` and Kotlin `suspend` are "considered non-blocking, and will be run on the IO thread by default". `@Blocking`/`@NonBlocking` apply at method, class or `Application` level, and `@Transactional` methods count as blocking (rest guide). `@RunOnVirtualThread` "can only be used on endpoints annotated with @Blocking or considered blocking because of their signature", and it requires Java 21+ (virtual-threads guide).
- Code:
  ```java
  // Quarkus 3.40.x
  @Path("/orders")
  public class OrderResource {
      @GET @Path("/{id}")                    // plain return type -> worker thread (blocking)
      public Order get(@RestPath String id) { return repo.find(id); }

      @GET @Path("/async/{id}")              // Uni -> IO (event-loop) thread: never block here
      public Uni<Order> getAsync(@RestPath String id) { return reactiveRepo.find(id); }

      @GET @Path("/vt/{id}") @RunOnVirtualThread   // blocking signature only; Java 21+
      public Order getVt(@RestPath String id) { return repo.find(id); }
  }
  ```
- Source: https://quarkus.io/version/3.40/guides/rest , https://quarkus.io/version/3.40/guides/virtual-threads (2026-10-14)

**M3. Configure each REST client with a configKey, a mandatory URL, explicit timeouts and a named TLS bucket — 3.40**
> Confidence: 🟢 High | [✓✓ Triangulated | https://quarkus.io/version/3.40/guides/rest-client (2026-10-14) + https://quarkus.io/version/3.40/guides/tls-registry-reference (2026-10-14)]
- Why: "Setting the base URL of the client is **mandatory**". Global defaults are `quarkus.rest-client.connect-timeout` = 15000 ms and `read-timeout` = 30000 ms, plus `connection-pool-size` = 50 and `http2` = false (rest-client guide config reference). `tls-configuration-name` selects `quarkus.tls.<name>.*`, and "an error will be thrown" if the name is missing (rest-client guide). Client extensions ignore the default `quarkus.tls.*` bucket except `trust-all`. TLS defaults to TLSv1.3 (tls-registry-reference).
- Code:
  ```java
  // Quarkus 3.40.x
  @RegisterRestClient(configKey = "partner-api")
  @Path("/v1/accounts")
  public interface PartnerApi {
      @GET @Path("/{id}") Account get(@RestPath String id);
  }
  @Path("/accounts") public class AccountResource {
      @RestClient PartnerApi partner;   // injected with @RestClient, not plain @Inject
      @GET @Path("/{id}") public Account get(@RestPath String id) { return partner.get(id); }
  }
  ```
  ```properties
  # Quarkus 3.40.x — defaults from https://quarkus.io/version/3.40/guides/rest-client
  quarkus.rest-client.partner-api.url=https://partner.example.com
  quarkus.rest-client.partner-api.connect-timeout=5000     # global default 15000
  quarkus.rest-client.partner-api.read-timeout=10000       # global default 30000
  quarkus.rest-client.partner-api.tls-configuration-name=partner
  quarkus.tls.partner.trust-store.pem.certs=certs/partner-ca.pem
  ```
- Note: per-client `connect-timeout`/`read-timeout` list no default in the config reference. The assumption that they inherit the global value is **UNVERIFIED (U1)**.
- Source: https://quarkus.io/version/3.40/guides/rest-client , https://quarkus.io/version/3.40/guides/tls-registry-reference (2026-10-14)

**M4. Map exceptions explicitly and log them yourself — 3.40**
> Confidence: 🟡 Medium (single source: rest guide, partly read)
- Why: "When an exception occurs, Quarkus REST does not log it by default (for security reasons)". An `@ServerExceptionMapper` method in a resource class "will only be called if the exception is thrown in the same class". Put global mappers outside endpoint classes. Jakarta `ExceptionMapper` also works.
- Code:
  ```java
  // Quarkus 3.40.x — global mapper (outside any resource class)
  public class GlobalMappers {
      private static final Logger LOG = Logger.getLogger(GlobalMappers.class);
      @ServerExceptionMapper
      public RestResponse<ErrorBody> map(OrderNotFoundException e) {
          LOG.debugf(e, "order not found");
          return RestResponse.status(Response.Status.NOT_FOUND, new ErrorBody(e.getMessage()));
      }
  }
  ```
- Source: https://quarkus.io/version/3.40/guides/rest (2026-10-14)

**M5. Validate request input with Hibernate Validator (400 for parameters) — 3.40**
> Confidence: 🟢 High | [✓✓ Triangulated | https://quarkus.io/version/3.40/guides/validation (2026-10-14) + camel-quarkus-examples quarkus-rest-json OrderResource (main)]
- Why: With `quarkus-hibernate-validator`, constraint failures on REST endpoint parameters return a bad request with a validation report (`status: 400`, a `violations` array). Return-value and service-method violations produce `5xx` unless you map `ConstraintViolationException`. The Camel example uses `@Valid @NotNull Order order` on a `@POST` resource.
- Code:
  ```java
  // Quarkus 3.40.x
  @POST
  public Response create(@Valid @NotNull Order order) { ... }   // invalid -> 400 + violations report
  ```
- Source: https://quarkus.io/version/3.40/guides/validation (2026-10-14)

**M6. Enable CORS explicitly with an explicit origin list — 3.40**
> Confidence: 🟡 Medium (single source)
- Why: `quarkus.http.cors.enabled` default `false`. If `quarkus.http.cors.origins` is unset, only same-origin requests are allowed. "Allowing unrestricted origins with `quarkus.http.cors.origins=*` in production environments poses severe security risks." The rest guide confirms "Quarkus includes a CORS filter at the HTTP layer level".
- Code:
  ```properties
  # Quarkus 3.40.x — https://quarkus.io/version/3.40/guides/security-cors
  quarkus.http.cors.enabled=true
  quarkus.http.cors.origins=https://app.example.com
  %dev.quarkus.http.cors.origins=/.*/
  ```
- Source: https://quarkus.io/version/3.40/guides/security-cors (2026-10-14)

**M7. Secure endpoints with annotations plus a deny-by-default switch — 3.40**
> Confidence: 🟡 Medium (single source per property)
- Why: `@RolesAllowed`, `@PermitAll`, `@DenyAll` apply to REST methods. `quarkus.security.jaxrs.deny-unannotated-endpoints` defaults to `false` (https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference). `quarkus.http.auth.permission.*` checks run before annotation checks, so "`@PermitAll` cannot override HTTP-level security configurations" (same page). Proactive authentication "is enabled in Quarkus by default". With it off, reading `SecurityIdentity` on the IO thread fails with `BlockingOperationNotAllowedException` (https://quarkus.io/version/3.40/guides/security-proactive-authentication).
- Code:
  ```properties
  # Quarkus 3.40.x
  quarkus.security.jaxrs.deny-unannotated-endpoints=true   # default false
  ```
- Source: the two pages above (2026-10-14)

### ⚠️ Conditional Patterns

**C1. Endpoint threading: worker vs IO thread vs virtual thread**
> Confidence: 🟢 High (rest + virtual-threads guides 3.40)
- Options: A) blocking signature (worker); B) `Uni`/`Multi` (IO thread); C) `@RunOnVirtualThread` (Java 21+).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A Worker | Simplicity, blocking libs (JDBC, ProducerTemplate) | Worker pool size limits | Most Camel-bridging endpoints |
  | B Uni/Multi | Throughput, no thread per request | Must never block; complex code | Fully reactive stack |
  | C Virtual thread | Blocking style at high concurrency | Pinning risk (synchronized on Java 21–23); CPU-bound monopolization | I/O-bound work only (virtual-threads guide) |

- Agent: "Ask the user which runtime Java version they use and whether the downstream calls are blocking (JDBC, Camel ProducerTemplate) before choosing B or C."
- Source: https://quarkus.io/version/3.40/guides/rest , https://quarkus.io/version/3.40/guides/virtual-threads (2026-10-14)

**C2. Expose HTTP via Quarkus REST resource + ProducerTemplate vs Camel REST DSL (platform-http)**
> Confidence: 🟡 Medium (main-branch example + 3.40.x platform-http reference)
- Options: A) Jakarta REST resource that injects `ProducerTemplate` (camel-quarkus-examples `quarkus-rest-json`); B) Camel REST DSL with `camel-quarkus-rest` on platform-http (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html); C) both in one app.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A Quarkus REST + ProducerTemplate | Full Quarkus REST features (validation, security annotations, OpenAPI from Jakarta annotations, typed responses) | Two layers (resource + route) | Rich API contract; Camel used only for integration logic |
  | B REST DSL | Everything in Camel routes | Quarkus REST features (filters, `@ServerExceptionMapper`) don't apply | Pure integration endpoints |
  | C Both | Migration flexibility | Path overlap behaviour undocumented (**IRRESOLVABLE I1**); platform-http docs warn about router changes when RESTEasy is present | Avoid unless paths are disjoint |

- Agent: "Ask whether endpoints need Quarkus REST features; if both stacks are present, require disjoint path prefixes."
- Source: https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/quarkus-rest-json/src/main/java/org/acme/rest/json/quarkus/OrderResource.java (main, 2026-10-14); https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html (2026-10-14)

**C3. REST client return style: blocking vs Uni vs CompletionStage**
> Confidence: 🟢 High (rest-client 3.40)
- Options: blocking return type; `Uni` (each subscription re-sends the request, so `onFailure().retry().atMost(n)` works); `CompletionStage` (retrying needs a new call).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Blocking | Simplicity | Must not run on the event loop | Called from a blocking endpoint/route |
  | Uni | Retry/composition | Reactive style | Called from a `Uni` endpoint |
  | CompletionStage | JDK standard | Manual retries | Interop |

- Agent: "Ask from which thread the client is called."
- Source: https://quarkus.io/version/3.40/guides/rest-client (2026-10-14)

**C4. JSON customization: ObjectMapperCustomizer vs own ObjectMapper vs per-method**
> Confidence: 🟢 High (rest-json + rest guide 3.40)
- Options: A) CDI bean `io.quarkus.jackson.ObjectMapperCustomizer` ("the simplest (and suggested) approach"); B) your own `ObjectMapper` producer (then you must apply all customizers yourself); C) `@CustomSerialization`/`@CustomDeserialization` or `@JsonView` per method.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | Keeps Quarkus defaults | Global only | Default choice |
  | B | Total control | You lose the defaults unless you reapply them | Rare |
  | C | Per-endpoint shape | More annotations | Views, partial DTOs |

- Agent: "Ask whether the customization is global or endpoint-specific. Warn that Quarkus 4 renames the customizer (Migration Note)."
- Source: https://quarkus.io/version/3.40/guides/rest-json , https://quarkus.io/version/3.40/guides/rest (2026-10-14)

**C5. OpenAPI / Swagger UI exposure**
> Confidence: 🟡 Medium
- Options: dev/test-only Swagger UI (default) vs `quarkus.swagger-ui.always-include=true` (build-time).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Default | Smaller prod attack surface | No UI in prod | Most services |
  | always-include | Discoverability | Exposure | Internal APIs |

- Facts: artifact `quarkus-smallrye-openapi`; document at `/q/openapi`; UI at `/q/swagger-ui`; OpenAPI version `3.1.0` by default (https://quarkus.io/version/3.40/guides/openapi-swaggerui). The page does not state Quarkus REST compatibility outright; its example uses `rest-jackson`.
- Source: https://quarkus.io/version/3.40/guides/openapi-swaggerui (2026-10-14)

### 🚫 Forbidden Patterns

**F1. Blocking calls on an IO-thread (Uni/Multi) endpoint**
> Severity: Critical
> Confidence: 🟢 High
- Why: Reactive signatures "will be run on the IO thread by default" (rest guide 3.40). Blocking stalls the event loop.
- Impact: Throughput collapse, blocked-thread warnings.
- ❌ Wrong:
  ```java
  @GET public Uni<Order> get() { return Uni.createFrom().item(producerTemplate.requestBody("direct:x", null, Order.class)); } // blocks IO thread
  ```
- ✅ Correct:
  ```java
  @GET public Order get() { return producerTemplate.requestBody("direct:x", null, Order.class); } // worker thread
  ```
- Source: https://quarkus.io/version/3.40/guides/rest (2026-10-14)

**F2. Mixing RESTEasy Classic client with Quarkus REST**
> Severity: High
> Confidence: 🟢 High
- Why: "the `quarkus-resteasy-client` extension may not be used with Quarkus REST, use `quarkus-rest-client` instead".
- Impact: Build/runtime conflicts.
- ❌ Wrong:
  ```xml
  <artifactId>quarkus-rest</artifactId> ... <artifactId>quarkus-resteasy-client</artifactId>
  ```
- ✅ Correct:
  ```xml
  <artifactId>quarkus-rest</artifactId> ... <artifactId>quarkus-rest-client-jackson</artifactId>
  ```
- Source: https://quarkus.io/version/3.40/guides/rest (2026-10-14)

**F3. trust-all / hostname verification disabled in production**
> Severity: Critical
> Confidence: 🟢 High
- Why: rest-client guide: "This properties set should not be used in production". `verify-host` "should not be disabled in production as it makes the client vulnerable to MITM attacks". tls-registry: `trust-all` "should not be used in production".
- Impact: MITM exposure.
- ❌ Wrong:
  ```properties
  quarkus.tls.partner.trust-all=true
  quarkus.tls.partner.hostname-verification-algorithm=NONE
  ```
- ✅ Correct:
  ```properties
  quarkus.tls.partner.trust-store.pem.certs=certs/partner-ca.pem
  ```
- Source: https://quarkus.io/version/3.40/guides/rest-client , https://quarkus.io/version/3.40/guides/tls-registry-reference (2026-10-14)

**F4. CORS wildcard in production**
> Severity: High
> Confidence: 🟢 High
- Why: Quoted as posing "severe security risks".
- Impact: Cross-origin data access.
- ❌ Wrong:
  ```properties
  quarkus.http.cors.origins=*
  ```
- ✅ Correct:
  ```properties
  quarkus.http.cors.origins=https://app.example.com
  ```
- Source: https://quarkus.io/version/3.40/guides/security-cors (2026-10-14)

**F5. Expecting `@PermitAll` to override HTTP permission policies**
> Severity: High
> Confidence: 🟡 Medium
- Why: "`@PermitAll` cannot override HTTP-level security configurations".
- Impact: Unexpected 401/403, or a false sense of openness.
- ❌ Wrong:
  ```properties
  quarkus.http.auth.permission.all.paths=/*
  quarkus.http.auth.permission.all.policy=authenticated   # then @PermitAll on /health-ish resource expecting public access
  ```
- ✅ Correct:
  ```properties
  quarkus.http.auth.permission.public.paths=/api/public/*
  quarkus.http.auth.permission.public.policy=permit
  ```
- Source: https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference (2026-10-14)

**F6. Returning raw `Response` with entity types not visible at build time (native)**
> Severity: Medium
> Confidence: 🟢 High
- Why: The rest-json guide says that without reflection registration "no exception will be thrown". It recommends `@RegisterForReflection`, or `RestResponse<T>` so the type can be inferred at build time.
- Impact: Empty/incorrect JSON in native mode.
- ❌ Wrong:
  ```java
  @GET public Response get() { return Response.ok(new Order()).build(); }
  ```
- ✅ Correct:
  ```java
  @GET public RestResponse<Order> get() { return RestResponse.ok(new Order()); }
  ```
- Source: https://quarkus.io/version/3.40/guides/rest-json (2026-10-14)

**F7. Replacing masked-header defaults without re-adding Authorization/Cookie**
> Severity: Medium
> Confidence: 🟢 High
- Why: `quarkus.rest-client.logging.masked-headers` defaults to `Authorization, Cookie`. Setting it replaces them: "You **must** explicitly include them if you still need them masked."
- Impact: Credential leakage in logs.
- ❌ Wrong:
  ```properties
  quarkus.rest-client.logging.masked-headers=X-Api-Key
  ```
- ✅ Correct:
  ```properties
  quarkus.rest-client.logging.masked-headers=Authorization,Cookie,X-Api-Key
  ```
- Source: https://quarkus.io/version/3.40/guides/rest-client (2026-10-14)

---

## Migration Guide

> Confidence: 🟡 Medium | Sources: https://quarkus.io/version/3.40/guides/rest (2026-10-14) + https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0 (wiki, unversioned, 2026-10-14)

**Naming (3.15 conventions to 3.40)**:
- Server: use `quarkus-rest` (successor of RESTEasy Reactive per the 3.40 guide). The rest guide fragment read does not mention `quarkus-resteasy-reactive` aliases; whether they still exist in 3.40 is **UNVERIFIED (U7)**.
- Client: `quarkus-rest-client` / `quarkus-rest-client-jackson`; never `quarkus-resteasy-client` with Quarkus REST (High).
- Testing: `quarkus-junit` is the artifact in the 3.40 testing guide; no `quarkus-junit5` is mentioned (High, https://quarkus.io/version/3.40/guides/getting-started-testing). For Camel tests use `camel-quarkus-junit` (family fact, High, https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html).
- Config prefix: `quarkus.rest.*` (e.g., `quarkus.rest.path`) and `quarkus.rest-client.*` (High, 3.40 guides).

**Deprecated in 3.40 (removed in 4.0)**: `quarkus.rest-client.proxy-address`, `proxy-user`, `proxy-password`, `non-proxy-hosts`, `proxy-connect-timeout` and `multipart.max-chunk-size` are deprecated in the 3.40 reference (High, rest-client guide). The Quarkus 4 migration guide removes them in favour of `proxy-configuration-name` and `max-chunk-size` (Medium, wiki). ⚠️ Migration Note: use `proxy-configuration-name` now.

**Quarkus 4.0 preview (NOT for 3.40)**: Quarkus 4.0.0.Beta1 was published 2026-10-01, with the final release "planned for the end of November" and Java 21 as the new base (High, https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). Jackson 3: "everything has changed except for the annotations" (High, same post). The migration wiki adds (Medium): packages move from `com.fasterxml.jackson.databind` to `tools.jackson.databind`, while annotations keep `com.fasterxml.jackson.annotation`; Quarkus produces a `JsonMapper` bean; `ObjectMapperCustomizer` is renamed `JsonMapperBuilderCustomizer`; endpoints may no longer return REST Client `Response`/`RestResponse`; `SseEventSink.close()` throws `IOException`; RESTEasy 7 / partial Jakarta REST 4. No Camel Quarkus build on Quarkus 4 is known (Medium, family facts).

**Upgrade Steps** (representative):
1. Replace any `quarkus-resteasy*` artifacts with `quarkus-rest*` equivalents.
2. Replace `quarkus-junit5` with `quarkus-junit` (and `camel-quarkus-junit5` with `camel-quarkus-junit`).
3. Move proxy settings to `quarkus.rest-client."key".proxy-configuration-name`.
4. Move REST client TLS to `tls-configuration-name` + `quarkus.tls.<name>.*`.
5. `./mvnw quarkus:update` (representative; command not verified on a 3.40 page, **UNVERIFIED** is not counted because it is a tooling hint and not a claim used in patterns).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Java (virtual threads) | 21 | — | https://quarkus.io/version/3.40/guides/virtual-threads |
| Camel Quarkus | 3.40.x | 3.40.x | Quarkus 3.40.1, Camel 4.22.1 (family facts, https://camel.apache.org/camel-quarkus/latest/) |
| Jackson | 2.x | 2.x | exact version **UNVERIFIED (U4)**; Jackson 3 arrives only in Quarkus 4 |
| OpenAPI document | 3.1.0 default | — | https://quarkus.io/version/3.40/guides/openapi-swaggerui |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | camel-quarkus-examples quarkus-rest-json (main, pom 3.40.1) + https://quarkus.io/version/3.40/guides/rest]

**Lifecycle**:
```java
// Quarkus 3.40.x — resource class basics
@Path("/api/orders")                         // class prefix; method @Path appends
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class OrderResource {
    @GET @Path("/{id:\\d+}")                 // regex path constraint
    public RestResponse<Order> get(@RestPath String id, @RestQuery String expand) { ... }

    @POST @ResponseStatus(201)
    public Order create(@Valid @NotNull Order order) { ... }
}
```
```properties
# Quarkus 3.40.x — https://quarkus.io/version/3.40/guides/rest (config reference)
quarkus.rest.path=/            # build-time root (alt. @ApplicationPath); no default listed
# quarkus.rest.fail-on-duplicate=true      (default)
# quarkus.rest.removes-trailing-slash=true (default)
# quarkus.rest.default-produces=true       (default; application/json for application types)
# quarkus.rest.single-default-produces=true (default; text/plain for String)
# quarkus.rest.input-buffer-size=10k, output-buffer-size=8191 (defaults)
# quarkus.http.limits.max-form-attribute-size=2048 bytes per multipart part (default; 413 if exceeded)
```
Filters (rest guide 3.40): `@ServerRequestFilter` / `@ServerResponseFilter`. Pre-matching filters "are **always** run on an event-loop thread". Response filters and exception mappers do not run on streamed `Multi` responses. Response filters are skipped on client disconnect unless marked `@ServerResponseFilter(cancellable = false)`.

**Integration**: Quarkus REST ↔ Camel ProducerTemplate (camel-quarkus-platform-http / direct)
```java
// Quarkus 3.40.x + Camel Quarkus 3.40.x — pattern published in camel-quarkus-examples/quarkus-rest-json (main branch; Medium)
@Path("/api/orders")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class OrderResource {
    @Inject ProducerTemplate producerTemplate;          // Camel Quarkus CDI bean

    @POST                                              // blocking signature -> worker thread
    public Response createOrder(@Valid @NotNull Order order) {
        OrderResponse r = producerTemplate.requestBody("direct:processOrder", order, OrderResponse.class);
        return Response.status(Response.Status.CREATED).entity(r).build();
    }
}
// Route side: from("direct:processOrder")... (camel-quarkus-direct, camel-quarkus-bean, camel-quarkus-jackson in the example pom)
```
Example pom dependencies: `quarkus-rest`, `quarkus-rest-jackson`, `camel-quarkus-jackson`, `camel-quarkus-direct`, `camel-quarkus-bean`, `camel-quarkus-kafka`, `quarkus-hibernate-validator`; tests `quarkus-junit`, `rest-assured`, `awaitility`; `quarkus.platform.version` 3.40.1 (https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/quarkus-rest-json/pom.xml, main, Medium). The example uses no `camel-quarkus-platform-http`/`camel-quarkus-rest`, so it does not show both stacks together.

**Integration**: Quarkus REST ↔ Camel REST DSL on the same server
- platform-http: "Configuration of the platform HTTP server is managed by Quarkus". "care should be taken when modifying the router configuration when extensions such as RestEASY are present". REST DSL needs `camel-quarkus-rest` (High for the quotes, https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html).
- How path overlap between Quarkus REST resources and platform-http routes resolves: **IRRESOLVABLE (I1)**. Whether `quarkus.rest.path` affects platform-http routes: **UNVERIFIED (U3)**.

**Integration**: REST client ↔ quarkus.tls — see M3. HTTP server TLS: `quarkus.http.tls-configuration-name=<name>` (https://quarkus.io/version/3.40/guides/tls-registry-reference). Whether the Camel Quarkus 3.40.0 TLS bridging affects the inbound platform-http server: **IRRESOLVABLE (I2)** (family fact Unverified).

**Integration**: Quarkus ArC: resources may use `@Inject` fields or constructors; context objects (`HttpHeaders`, `UriInfo`, `SecurityContext`, ...) can be injected as parameters, fields or constructor args (rest guide 3.40, High). `@ServerExceptionMapper` methods "do not run CDI interceptors that apply to the other methods of the class" (High).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Quarkus 3.40.x)
./mvnw quarkus:dev                       # dev mode; Swagger UI at /q/swagger-ui (dev/test only by default)
curl -s localhost:8080/q/openapi         # Expected: OpenAPI 3.1.0 document
./mvnw test                              # @QuarkusTest on port 8081 by default (quarkus.http.test-port)
./mvnw verify -DskipITs=false            # @QuarkusIntegrationTest against the built artifact
./mvnw install -Dnative                  # native build (rest-client guide)
```
Sources: https://quarkus.io/version/3.40/guides/getting-started-testing , https://quarkus.io/version/3.40/guides/openapi-swaggerui , https://quarkus.io/version/3.40/guides/rest-client (2026-10-14)

**Mocking**:
```java
// Quarkus 3.40.x — requires quarkus-junit + quarkus-junit-mockito + rest-assured (test scope)
@QuarkusTest
@TestHTTPEndpoint(AccountResource.class)        // REST Assured base path from @Path
class AccountResourceTest {
    @InjectMock @RestClient PartnerApi partner;  // mock the REST client

    @Test void get() {
        Mockito.when(partner.get("1")).thenReturn(new Account("1"));
        given().when().get("/1").then().statusCode(200);
    }
}
```
- `QuarkusMock.installMockForType(..., RestClient.LITERAL)` is the programmatic variant. "Mocking does not work when using `@QuarkusIntegrationTest`". For HTTP-level stubbing, use WireMock via a `QuarkusTestResourceLifecycleManager` that returns `quarkus.rest-client."...".url` (https://quarkus.io/version/3.40/guides/rest-client, High).
- Camel routes behind ProducerTemplate: use `camel-quarkus-junit` (family facts, High).

---

## Production Readiness

- **Performance**: REST client pool size 50, `connection-ttl` 60000, `keep-alive-enabled` true, HTTP/2 off by default (https://quarkus.io/version/3.40/guides/rest-client). HTTP response compression is off by default ("not compressed by default", https://quarkus.io/version/3.40/guides/rest).
- **Scalability**: Prefer IO-thread endpoints for non-blocking stacks. Use `@RunOnVirtualThread` only for I/O-bound work, and watch pinning on Java 21–23 (https://quarkus.io/version/3.40/guides/virtual-threads).
- **Monitoring**: REST client logging via `quarkus.rest-client.logging.scope=request-response|all`, `body-limit` default 100 (rest-client guide). The Micrometer virtual-thread binder auto-enables with `micrometer-java21` (virtual-threads guide). Enable DEBUG on `org.jboss.resteasy.reactive.server.handlers.ParameterHandler` to diagnose parameter errors (rest guide).
- **Security**: Proactive auth on by default; consider `quarkus.security.jaxrs.deny-unannotated-endpoints=true`; CORS explicit origins; TLS via named buckets (TLSv1.3 default); never trust-all; Swagger UI excluded from prod by default; mapped exceptions should not leak internals (Quarkus REST does not log exceptions by default). Whether annotation checks run before body deserialization: **UNVERIFIED (U6)**.

---

## Reference Implementations

- camel-quarkus-examples `quarkus-rest-json` — Quarkus REST resource + `ProducerTemplate` → `direct:processOrder` (main branch, Medium): https://github.com/apache/camel-quarkus-examples/tree/main/quarkus-rest-json
- camel-quarkus-examples `rest-json` (Camel REST DSL counterpart, name only seen; content not read): https://github.com/apache/camel-quarkus-examples
- Quarkus REST guide 3.40: https://quarkus.io/version/3.40/guides/rest
- Quarkus REST Client guide 3.40: https://quarkus.io/version/3.40/guides/rest-client
- Writing JSON REST services 3.40: https://quarkus.io/version/3.40/guides/rest-json

---

## Source Bibliography

**Primary** (all accessed 2026-10-14):
- https://quarkus.io/version/3.40/guides/rest — Quarkus REST 3.40 (read in two parts, fully)
- https://quarkus.io/version/3.40/guides/rest-client — REST Client 3.40 (read in two parts; a header-section fragment was partially read)
- https://quarkus.io/version/3.40/guides/rest-json — "Writing JSON REST services - 3.40"
- https://quarkus.io/version/3.40/guides/virtual-threads
- https://quarkus.io/version/3.40/guides/security-cors
- https://quarkus.io/version/3.40/guides/openapi-swaggerui
- https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference
- https://quarkus.io/version/3.40/guides/security-proactive-authentication
- https://quarkus.io/version/3.40/guides/validation
- https://quarkus.io/version/3.40/guides/tls-registry-reference (first 100k chars read)
- https://quarkus.io/version/3.40/guides/getting-started-testing (first 100k chars read)
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html
- Family facts (orchestrator-verified 2026-10-14): https://quarkus.io/releases , https://camel.apache.org/releases/ , https://camel.apache.org/camel-quarkus/latest/ , https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html , https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html

**Validation** (Medium — unversioned / main branch):
- https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0
- https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/quarkus-rest-json/pom.xml
- https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/quarkus-rest-json/src/main/java/org/acme/rest/json/quarkus/OrderResource.java

**All Deep-Links**: as listed inline per claim above.

---

## Research Gaps

Unverified items (count = 6, matches `Unverified_Count`):
- U1: per-client `connect-timeout`/`read-timeout` inherit the global defaults (config reference lists no per-client default).
- U3: whether `quarkus.rest.path` affects Camel platform-http routes.
- U4: exact Jackson 2.x version shipped by Quarkus 3.40.1.
- U6: whether Quarkus REST security annotation checks run before request-body deserialization.
- U7: whether legacy `quarkus-resteasy-reactive*` artifact names still exist as aliases in 3.40.
- U8: Camel Quarkus-specific support end date for 3.40 (family fact: Unverified).

Irresolvable items (count = 2, matches `Irresolvable_Count`):
```
Gap: I1 — Behaviour when a Quarkus REST resource and a Camel platform-http route share a path on the same HTTP server
Impact: Ambiguous routing / shadowed endpoints
Workaround: Use disjoint path prefixes (e.g., quarkus.rest.path=/api vs Camel REST DSL under /camel)
Follow-up: camel-quarkus GitHub issues / platform-http extension source
§7-ref: Iteration 1 — IRRESOLVABLE
```
```
Gap: I2 — Whether the Camel Quarkus 3.40.0 quarkus.tls bridging affects the inbound platform-http server
Impact: Unknown TLS policy on the shared HTTP server
Workaround: Configure server TLS explicitly with quarkus.http.tls-configuration-name
Follow-up: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html, camel-quarkus issues
§7-ref: Iteration 3 — IRRESOLVABLE
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Implementation Blueprint | Quarkus REST resource calling Camel ProducerTemplate (sibling open question) | Resolved (Medium, main branch) | https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/quarkus-rest-json/src/main/java/org/acme/rest/json/quarkus/OrderResource.java (2026-10-14) |
| 1 | Conditional C2 | Quarkus REST + platform-http path overlap | ⚠️ IRRESOLVABLE — platform-http 3.40.x page only warns about RESTEasy router changes; no overlap rule | — |
| 2 | Mandatory M6/M7, C5, M5 | CORS defaults, security annotations, OpenAPI paths, validation 400 | Resolved | security-cors, security-authorize-web-endpoints-reference, openapi-swaggerui, validation (3.40, 2026-10-14) |
| 2 | Mandatory M2 | @RunOnVirtualThread rules | Resolved | https://quarkus.io/version/3.40/guides/virtual-threads (2026-10-14) |
| 3 | Mandatory M3 | REST client TLS via quarkus.tls, TLSv1.3 default | Resolved | https://quarkus.io/version/3.40/guides/tls-registry-reference (2026-10-14) |
| 3 | Production Readiness | Proactive auth default | Resolved | https://quarkus.io/version/3.40/guides/security-proactive-authentication (2026-10-14) |
| 3 | Implementation Blueprint | TLS bridging effect on inbound platform-http | ⚠️ IRRESOLVABLE — no 3.40 page states it | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (topic checklist from v3.15 file covered; v3.15 file not used as a source)
- [x] Pattern counts driven by domain needs (7 / 5 / 7)
- [x] Every anti-pattern has alternative
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (Camel ProducerTemplate, REST DSL caveat, ArC, testing, OpenAPI, TLS)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (deep) or downgraded to 🟡 Medium (M4, M6, M7 downgraded)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7 (I1, I2)

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: M1, M2, M3, M5 (✓✓ triangulated); F1–F4, F6, F7; all defaults quoted from `/version/3.40/` pages.
- **Medium Confidence (validate with user)**: M4, M6, M7 (single source); C2 (main-branch example); Quarkus 4 migration wiki items; the ProducerTemplate-in-resource pattern, which is officially published but on the main branch, not in 3.40.x-tagged docs.
- **Low Confidence (must ask human)**: U1, U3, U4, U6, U7, U8; I1, I2.
- **Edge Cases (pause)**: Quarkus 3.40 was released 2026-09-30, about 14 days before this research (<30 days), so docs may still change. Quarkus 4.0 Beta patterns (Jackson 3, `JsonMapperBuilderCustomizer`) must not be applied to 3.40.
- **Emergency Stop**: not triggered. Official versioned docs exist and the version is current LTS.
