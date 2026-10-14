# Always-Do Patterns: Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Each pattern rests on a versioned `https://quarkus.io/version/3.40/guides/` page. Medium-confidence topics are in [server resources](./server-resources.md), [security and TLS](./security-and-tls.md) and [Camel integration](./camel-integration.md).

## Contents

1. [Server and client artifacts](#1-server-and-client-artifacts)
2. [Thread by signature](#2-thread-by-signature)
3. [Virtual threads](#3-virtual-threads)
4. [Client URL and config key](#4-client-url-and-config-key)
5. [Named TLS bucket](#5-named-tls-bucket)
6. [Validation](#6-validation)
7. [RestResponse for native](#7-restresponse-for-native)

## 1. Server and client artifacts

The 3.40 guide names `quarkus-rest`, `quarkus-rest-jackson`, `quarkus-rest-jsonb` and `quarkus-rest-jaxb`, and says `quarkus-resteasy-client` "may not be used with Quarkus REST".

```xml
<!-- Quarkus 3.40.x: versions come from the Quarkus/Camel Quarkus BOM -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest</artifactId></dependency>
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest-jackson</artifactId></dependency>
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest-client-jackson</artifactId></dependency>
```

Sources: https://quarkus.io/version/3.40/guides/rest ; https://quarkus.io/version/3.40/guides/rest-client

## 2. Thread by signature

"The thread Quarkus REST will run endpoint methods on depends on the signature of the method". `Uni`, `Multi`, `CompletionStage`, `Publisher` and Kotlin `suspend` are non-blocking and run on the IO thread. `@Blocking` and `@NonBlocking` apply at method, class or `Application` level; `@Transactional` methods count as blocking.

```java
// Quarkus 3.40.x
@Path("/orders")
public class OrderResource {
    @GET @Path("/{id}")                    // plain return type: worker thread (blocking)
    public Order get(@RestPath String id) { return repo.find(id); }

    @GET @Path("/async/{id}")              // Uni: IO thread, never block here
    public Uni<Order> getAsync(@RestPath String id) { return reactiveRepo.find(id); }
}
```

Source: https://quarkus.io/version/3.40/guides/rest

## 3. Virtual threads

`@RunOnVirtualThread` is only valid on blocking endpoints and needs Java 21+. Whether to use it is an Ask First item (pinning on Java 21-23, medium confidence; register M9).

```java
// Quarkus 3.40.x, Java 21+
@GET @Path("/vt/{id}") @RunOnVirtualThread
public Order getVt(@RestPath String id) { return repo.find(id); }
```

Source: https://quarkus.io/version/3.40/guides/virtual-threads

## 4. Client URL and config key

"Setting the base URL of the client is mandatory". Inject with `@RestClient`, not plain `@Inject`.

```java
// Quarkus 3.40.x
@RegisterRestClient(configKey = "partner-api")
@Path("/v1/accounts")
public interface PartnerApi {
    @GET @Path("/{id}") Account get(@RestPath String id);
}

@Path("/accounts")
public class AccountResource {
    @RestClient PartnerApi partner;
    @GET @Path("/{id}") public Account get(@RestPath String id) { return partner.get(id); }
}
```

```properties
quarkus.rest-client.partner-api.url=https://partner.example.com
```

Source: https://quarkus.io/version/3.40/guides/rest-client

## 5. Named TLS bucket

`tls-configuration-name` selects `quarkus.tls.<name>.*`; an error is thrown if the name is missing. Client extensions ignore the default `quarkus.tls.*` bucket except `trust-all`, which must not be used in production.

```properties
# Quarkus 3.40.x
quarkus.rest-client.partner-api.tls-configuration-name=partner
quarkus.tls.partner.trust-store.pem.certs=certs/partner-ca.pem
```

Sources: https://quarkus.io/version/3.40/guides/rest-client (header section read only partly, register L3) ; https://quarkus.io/version/3.40/guides/tls-registry-reference (first 100k chars read, register L1)

## 6. Validation

With `quarkus-hibernate-validator`, constraint failures on endpoint parameters return a bad request with a validation report (`status: 400`, a `violations` array). Return-value and service-method violations produce a 5xx unless you map `ConstraintViolationException`.

```java
// Quarkus 3.40.x
@POST
public Response create(@Valid @NotNull Order order) { ... }   // invalid: 400 + violations
```

Source: https://quarkus.io/version/3.40/guides/validation

## 7. RestResponse for native

Without reflection registration the guide says "no exception will be thrown" for a raw `Response` entity. It recommends `@RegisterForReflection`, or `RestResponse<T>` so the type is known at build time.

```java
// Quarkus 3.40.x
@GET public RestResponse<Order> get() { return RestResponse.ok(new Order()); }
```

Source: https://quarkus.io/version/3.40/guides/rest-json
