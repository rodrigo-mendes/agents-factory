# Server Resources: Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Facts come from https://quarkus.io/version/3.40/guides/rest unless a row says otherwise.

## Contents

- [Resource class basics](#resource-class-basics)
- [Configuration defaults](#configuration-defaults)
- [Filters](#filters)
- [Exception mapping](#exception-mapping)
- [CDI and context objects](#cdi-and-context-objects)
- [JSON customization](#json-customization)
- [OpenAPI and Swagger UI](#openapi-and-swagger-ui)
- [Testing](#testing)

## Resource class basics

```java
// Quarkus 3.40.x
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

JSON needs `quarkus-rest-jackson` or `quarkus-rest-jsonb`; XML needs `quarkus-rest-jaxb`.

## Configuration defaults

The rest guide is recorded as read only partly (register L5). The rows below have no verbatim quote recorded, except the compression row, so they are (medium confidence, L5; register M11).

| Key | Default | Source |
|---|---|---|
| `quarkus.rest.path` | build-time root (alternative: `@ApplicationPath`); no default listed. Whether it affects Camel platform-http routes is (unverified) (register U2) | https://quarkus.io/version/3.40/guides/rest |
| `quarkus.rest.fail-on-duplicate` | `true` | https://quarkus.io/version/3.40/guides/rest |
| `quarkus.rest.removes-trailing-slash` | `true` | https://quarkus.io/version/3.40/guides/rest |
| `quarkus.rest.default-produces` | `true` (`application/json` for application types) | https://quarkus.io/version/3.40/guides/rest |
| `quarkus.rest.single-default-produces` | `true` (`text/plain` for `String`) | https://quarkus.io/version/3.40/guides/rest |
| `quarkus.rest.input-buffer-size` / `output-buffer-size` | 10k / 8191 | https://quarkus.io/version/3.40/guides/rest |
| `quarkus.http.limits.max-form-attribute-size` | 2048 bytes per multipart part; 413 if exceeded | https://quarkus.io/version/3.40/guides/rest |
| HTTP response compression | not compressed by default | https://quarkus.io/version/3.40/guides/rest |

## Filters

Use `@ServerRequestFilter` and `@ServerResponseFilter`. Pre-matching filters "are always run on an event-loop thread" (High: verbatim quote recorded; register L5). Response filters and exception mappers do not run on streamed `Multi` responses. Response filters are skipped on client disconnect unless marked `@ServerResponseFilter(cancellable = false)` (these two sentences: medium confidence, L5; register M11).

## Exception mapping

(medium confidence: single page, partly read; register M1.) "When an exception occurs, Quarkus REST does not log it by default (for security reasons)". An `@ServerExceptionMapper` method in a resource class "will only be called if the exception is thrown in the same class", so put global mappers outside endpoint classes. Jakarta `ExceptionMapper` also works.

```java
// Quarkus 3.40.x: global mapper outside any resource class
public class GlobalMappers {
    private static final Logger LOG = Logger.getLogger(GlobalMappers.class);
    @ServerExceptionMapper
    public RestResponse<ErrorBody> map(OrderNotFoundException e) {
        LOG.debugf(e, "order not found");
        return RestResponse.status(Response.Status.NOT_FOUND, new ErrorBody(e.getMessage()));
    }
}
```

`@ServerExceptionMapper` methods "do not run CDI interceptors that apply to the other methods of the class" (High: verbatim quote recorded from a read part of the rest guide; register L5). To diagnose parameter errors, enable DEBUG on `org.jboss.resteasy.reactive.server.handlers.ParameterHandler`.

## CDI and context objects

(medium confidence, L5; register M11.) Resources may use `@Inject` fields or constructors. Context objects (`HttpHeaders`, `UriInfo`, `SecurityContext`) can be injected as parameters, fields or constructor arguments.

## JSON customization

Source: https://quarkus.io/version/3.40/guides/rest-json (High: the "simplest (and suggested) approach" quote is recorded from this page; the rest-guide part of this section is covered by register L5).

| Option | Use when |
|---|---|
| CDI bean `io.quarkus.jackson.ObjectMapperCustomizer` ("the simplest (and suggested) approach") | Default; keeps Quarkus defaults; global only |
| Your own `ObjectMapper` producer | Rare; you must apply all customizers yourself |
| `@CustomSerialization`, `@CustomDeserialization` or `@JsonView` | Per-endpoint shapes, partial DTOs |

`ObjectMapperCustomizer` is renamed in Quarkus 4 (medium confidence, wiki): [preview](./migration-quarkus-4-preview.md#quarkus-4-preview-not-for-340).

## OpenAPI and Swagger UI

(medium confidence; register M5.) Artifact `quarkus-smallrye-openapi`; document at `/q/openapi`; UI at `/q/swagger-ui`, included only in dev/test unless `quarkus.swagger-ui.always-include=true` (build-time). The page does not state Quarkus REST compatibility outright; its example uses `rest-jackson`. Source: https://quarkus.io/version/3.40/guides/openapi-swaggerui

## Testing

Source: https://quarkus.io/version/3.40/guides/getting-started-testing (read to 100k chars) and https://quarkus.io/version/3.40/guides/rest-client. See [REST client mocking](./rest-client.md#mocking-and-testing).

```bash
# Representative: adapt to your environment (Quarkus 3.40.x)
./mvnw quarkus:dev                    # Swagger UI at /q/swagger-ui (dev/test only by default)
curl -s localhost:8080/q/openapi      # Expected: OpenAPI 3.1.0 document
./mvnw test                           # @QuarkusTest, port 8081 by default (quarkus.http.test-port; medium confidence, L2)
./mvnw verify -DskipITs=false         # @QuarkusIntegrationTest against the built artifact
./mvnw install -Dnative               # native build
```
