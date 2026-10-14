# REST Client: Quarkus 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Source is https://quarkus.io/version/3.40/guides/rest-client (read in two parts; the header section was read only partly, register L3) unless a row says otherwise.

## Contents

- [Full example](#full-example)
- [Defaults](#defaults)
- [Return styles](#return-styles)
- [TLS](#tls)
- [Logging](#logging)
- [Deprecated settings](#deprecated-settings)
- [Mocking and testing](#mocking-and-testing)

## Full example

```java
// Quarkus 3.40.x
@RegisterRestClient(configKey = "partner-api")
@Path("/v1/accounts")
public interface PartnerApi {
    @GET @Path("/{id}") Account get(@RestPath String id);
}
```

```properties
# Quarkus 3.40.x
quarkus.rest-client.partner-api.url=https://partner.example.com
quarkus.rest-client.partner-api.connect-timeout=5000     # global default 15000
quarkus.rest-client.partner-api.read-timeout=10000       # global default 30000
quarkus.rest-client.partner-api.tls-configuration-name=partner
quarkus.tls.partner.trust-store.pem.certs=certs/partner-ca.pem
```

The config reference lists no default for the per-client `connect-timeout` and `read-timeout`; that they inherit the global value is (unverified) (register U1). Setting them explicitly avoids the question.

## Defaults

| Setting | Default |
|---|---|
| base URL | mandatory |
| `quarkus.rest-client.connect-timeout` | 15000 ms |
| `quarkus.rest-client.read-timeout` | 30000 ms |
| `connection-pool-size` | 50 |
| `connection-ttl` | 60000 |
| `keep-alive-enabled` | `true` |
| `http2` | `false` |

## Return styles

| Style | Behaviour | Use when |
|---|---|---|
| Blocking | Simplest; must not run on the event loop | Called from a blocking endpoint |
| `Uni` | Each subscription re-sends the request, so `onFailure().retry().atMost(n)` works | Called from a `Uni` endpoint |
| `CompletionStage` | JDK standard; retrying needs a new call | Interop |

## TLS

`tls-configuration-name` selects a `quarkus.tls.<name>` bucket and errors if the name is missing. Client extensions ignore the default `quarkus.tls.*` bucket except `trust-all` (https://quarkus.io/version/3.40/guides/tls-registry-reference). TLS defaults to TLSv1.3. `trust-all` and disabled `verify-host` must not be used in production ([never-do](./never-do-patterns.md#3-trust-all-or-disabled-hostname-verification-in-production)).

## Logging

`quarkus.rest-client.logging.scope=request-response|all`; `body-limit` default 100. `masked-headers` defaults to `Authorization, Cookie` and a custom value replaces them ([never-do](./never-do-patterns.md#5-replacing-masked-header-defaults-without-authorization-and-cookie)).

## Deprecated settings

`quarkus.rest-client.proxy-address`, `proxy-user`, `proxy-password`, `non-proxy-hosts`, `proxy-connect-timeout` and `multipart.max-chunk-size` are deprecated in the 3.40 reference. Use `quarkus.rest-client."key".proxy-configuration-name` and `max-chunk-size` now. That Quarkus 4 removes them is medium confidence ([preview](./migration-quarkus-4-preview.md#quarkus-4-preview-not-for-340)).

## Mocking and testing

Requires `quarkus-junit`, `quarkus-junit-mockito` and `rest-assured` (test scope).

```java
// Quarkus 3.40.x
@QuarkusTest
@TestHTTPEndpoint(AccountResource.class)        // REST Assured base path from @Path (medium confidence)
class AccountResourceTest {
    @InjectMock @RestClient PartnerApi partner;  // mock the REST client

    @Test void get() {
        Mockito.when(partner.get("1")).thenReturn(new Account("1"));
        given().when().get("/1").then().statusCode(200);
    }
}
```

`QuarkusMock.installMockForType(..., RestClient.LITERAL)` is the programmatic variant. "Mocking does not work when using `@QuarkusIntegrationTest`". For HTTP-level stubbing use WireMock through a `QuarkusTestResourceLifecycleManager` that returns the `quarkus.rest-client."...".url` value. Quarkus test details (artifacts, profiles, `@InjectMock`): skill `developing-quarkus-junit-v3-40`. Camel routes behind a `ProducerTemplate`: skill `developing-camel-quarkus-junit-v3-40`.
