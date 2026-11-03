# WireMock, Dev Services and Testcontainers

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-01: [quarkus-wiremock docs](https://docs.quarkiverse.io/quarkus-wiremock/dev/index.html), [Dev Services guide](https://quarkus.io/version/3.40/guides/dev-services), [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing), [Testcontainers releases](https://github.com/testcontainers/testcontainers-java/releases), [WireMock templating](https://wiremock.org/docs/response-templating/).

## Contents

- [WireMock through quarkus-wiremock](#wiremock-through-quarkus-wiremock)
- [URL wiring for the launched app](#url-wiring-for-the-launched-app)
- [Mappings, files and templating](#mappings-files-and-templating)
- [Manual WireMockServer resource](#manual-wiremockserver-resource)
- [Dev Services in ITs and without Docker](#dev-services-in-its-and-without-docker)
- [Testcontainers 2.0 test resources](#testcontainers-20-test-resources)

## WireMock through quarkus-wiremock

```xml
<dependency>
  <groupId>io.quarkiverse.wiremock</groupId>
  <artifactId>quarkus-wiremock</artifactId>
  <version>1.8.1</version>
  <scope>provided</scope>
</dependency>
<dependency>
  <groupId>io.quarkiverse.wiremock</groupId>
  <artifactId>quarkus-wiremock-test</artifactId>
  <version>1.8.1</version>
  <scope>test</scope>
</dependency>
```

```java
@QuarkusIntegrationTest
@ConnectWireMock(restClient = "orders-api")   // (unverified) redirect in the launched process; wiring below is explicit
class OrdersIT {
    WireMock wiremock;                          // injectable besides DevServicesContext
    @Test void R1_list_returnsOrders() {
        wiremock.register(get(urlEqualTo("/orders")).willReturn(okJson("[]")));
        given().when().get("/api/orders").then().statusCode(200);
    }
}
```

`@ConnectWireMock` works on `@QuarkusTest` and `@QuarkusIntegrationTest` (family fact F8). The `restClient` attribute redirect reaching the separate IT process is documented only as Dev Service values available through `ConfigProvider` and `DevServicesContext` (unverified), so do not rely on `restClient` for the launched process: set `quarkus.rest-client.orders-api.url` explicitly as in the next section, next to the annotation.

## URL wiring for the launched app

```properties
# src/main/resources/application.properties (the packaged file)
%it.quarkus.rest-client.orders-api.url=http://localhost:${quarkus.wiremock.devservices.port}
quarkus.wiremock.devservices.files-mapping=src/test/resources
```

Where the URL comes from, per case: jar IT with the Dev Service uses the packaged-properties expression above (F14); a Testcontainers or manual `WireMockServer` resource returns the URL in the `start()` map instead.

- Spike evidence (2026-10-31, no Docker on the machine): the packaged jar under `@QuarkusIntegrationTest` reached the WireMock Dev Service through this expression (medium confidence, not an official page; family fact F14).
- `%it.` keys apply only when `quarkus.test.integration-test-profile=it` is set; the default IT profile is `prod`, so without it the `%it.` key is ignored. Keeping the key under `%it.` stops production runs pointing at WireMock.
- Container-launched ITs: `localhost` inside the container is not the host, no official guidance exists (unverified); prefer jar ITs or the manual resource below.

## Mappings, files and templating

`src/test/resources/mappings/orders.json`:

```json
{
  "request": { "method": "GET", "urlPath": "/orders/42" },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "bodyFileName": "order-42.json",
    "transformers": ["response-template"]
  }
}
```

- Bodies go in `src/test/resources/__files/` and are referenced by `bodyFileName`.
- `transformers: ["response-template"]` enables templating per stub; global templating is a separate WireMock option.
- Stubs carry no real credentials. Unmatched requests return 404, which is the desired failure.

## Manual WireMockServer resource

Use `org.wiremock:wiremock` in a test resource when Dev Services are disabled or the extension is not allowed. The full resource is in [always-do patterns](./always-do-patterns.md#configuration-reaches-the-app): start on a dynamic port, return `quarkus.rest-client.<name>.url` from `start()`, stop in `stop()`.

## Dev Services in ITs and without Docker

- Dev Services work in integration tests, including container launch on a predictable network (`DevServicesContext.containerNetworkId()`).
- Container-based Dev Services, container ITs and Testcontainers resources all need Docker or Podman and fail at startup without one.
- Disable globally with `quarkus.devservices.enabled=false` or per service (`quarkus.datasource.devservices.enabled=false`); a Dev Service also stays off when the connection is configured explicitly.
- Start timeout `quarkus.devservices.timeout` (60 s default); `quarkus.devservices.launch-on-shared-network` defaults to `false`.
- CI without Docker: skip ITs with `-DskipITs=true`, or run only IT classes whose services are explicit. Whether the quarkus-wiremock Dev Service needs Docker is not stated officially (unverified); the spike ran it in-process without Docker (medium confidence).

## Testcontainers 2.0 test resources

```xml
<dependency>
  <groupId>org.testcontainers</groupId>
  <artifactId>testcontainers-postgresql</artifactId>  <!-- 2.x name; version from the Quarkus BOM -->
  <scope>test</scope>
</dependency>
```

```java
public class LegacyDbResource implements QuarkusTestResourceLifecycleManager,
        DevServicesContext.ContextAware {
    private Optional<String> networkId = Optional.empty();
    private PostgreSQLContainer db;
    @Override public void setIntegrationTestContext(DevServicesContext ctx) {
        networkId = ctx.containerNetworkId();
    }
    @Override public Map<String, String> start() {
        db = new PostgreSQLContainer("postgres:16");
        networkId.ifPresent(db::withNetworkMode);
        db.start();
        String url = db.getJdbcUrl();
        if (networkId.isPresent()) {   // app runs as a container: container host, unmapped port
            url = "jdbc:postgresql://" + db.getCurrentContainerInfo().getConfig().getHostName()
                + ":5432/" + db.getDatabaseName();
        }
        return Map.of("legacy.db.url", url, "legacy.db.user", db.getUsername(),
                      "legacy.db.password", db.getPassword());
    }
    @Override public void stop() { if (db != null) db.stop(); }
}
```

- The import `org.testcontainers.postgresql.PostgreSQLContainer` follows the 2.0 package rule but the module page does not print it (medium confidence).
- Module constructors need an explicit image name in 2.0.
- Prefer a Dev Service when one exists for the store; use this resource for services without one.
