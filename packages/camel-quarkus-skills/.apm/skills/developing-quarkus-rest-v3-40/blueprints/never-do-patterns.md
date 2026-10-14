# Never-Do Patterns: Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Each anti-pattern and its alternative rest on versioned 3.40 pages. Medium-confidence pitfalls (CORS wildcard, `@PermitAll` versus HTTP permissions) are in [security and TLS](./security-and-tls.md).

## 1. Blocking call on an IO-thread endpoint

Reactive signatures "will be run on the IO thread by default". Blocking there stalls the event loop; the impact is throughput collapse and blocked-thread warnings.

```java
// 🚫 WRONG
@GET public Uni<Order> get() {
    return Uni.createFrom().item(blockingRepo.find("1"));   // evaluated on the IO thread
}

// ✅ CORRECT: blocking signature, worker thread
@GET public Order get() { return blockingRepo.find("1"); }
```

Source: https://quarkus.io/version/3.40/guides/rest

## 2. RESTEasy Classic client with Quarkus REST

The guide: "the `quarkus-resteasy-client` extension may not be used with Quarkus REST, use `quarkus-rest-client` instead".

```xml
<!-- 🚫 WRONG -->
<artifactId>quarkus-rest</artifactId> ... <artifactId>quarkus-resteasy-client</artifactId>
<!-- ✅ CORRECT -->
<artifactId>quarkus-rest</artifactId> ... <artifactId>quarkus-rest-client-jackson</artifactId>
```

Source: https://quarkus.io/version/3.40/guides/rest

## 3. trust-all or disabled hostname verification in production

The rest-client guide: this property set "should not be used in production"; `verify-host` "should not be disabled in production as it makes the client vulnerable to MITM attacks". The TLS registry says `trust-all` "should not be used in production".

```properties
# 🚫 WRONG
quarkus.tls.partner.trust-all=true
quarkus.tls.partner.hostname-verification-algorithm=NONE

# ✅ CORRECT
quarkus.tls.partner.trust-store.pem.certs=certs/partner-ca.pem
```

Sources: https://quarkus.io/version/3.40/guides/rest-client ; https://quarkus.io/version/3.40/guides/tls-registry-reference

## 4. Raw Response with an entity type unknown at build time (native)

The rest-json guide says that without reflection registration no exception is thrown; the JSON may be empty or wrong in native mode.

```java
// 🚫 WRONG
@GET public Response get() { return Response.ok(new Order()).build(); }

// ✅ CORRECT
@GET public RestResponse<Order> get() { return RestResponse.ok(new Order()); }
```

Source: https://quarkus.io/version/3.40/guides/rest-json

## 5. Replacing masked-header defaults without Authorization and Cookie

`quarkus.rest-client.logging.masked-headers` defaults to `Authorization, Cookie`. Setting it replaces them: "You **must** explicitly include them if you still need them masked". The impact is credential leakage in logs.

```properties
# 🚫 WRONG
quarkus.rest-client.logging.masked-headers=X-Api-Key

# ✅ CORRECT
quarkus.rest-client.logging.masked-headers=Authorization,Cookie,X-Api-Key
```

Source: https://quarkus.io/version/3.40/guides/rest-client
