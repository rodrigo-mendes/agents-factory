# OpenAPI: Contract-First and Code-First — Camel Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

- [Choosing a mode](#choosing-a-mode)
- [Contract-first setup](#contract-first-setup)
- [Code generation defaults](#code-generation-defaults)
- [Code-first publishing](#code-first-publishing)
- [Native mode](#native-mode)

## Choosing a mode

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Contract-first: `rest().openApi()` + `camel-quarkus-rest-openapi` | API governance, generated models, startup fails on a missing operation (medium confidence) | Spec must ship in native; default base path `/` can shadow other endpoints (medium confidence) | An API team owns the spec |
| Code-first: REST DSL + `camel-quarkus-openapi-java` | Fast iteration, type-safe Java DSL | Spec is derived; model classes need `@RegisterForReflection` (medium confidence); `LambdaRouteBuilder` REST unsupported | Internal APIs, spec optional |

Ask: "Is there an authoritative OpenAPI document?" If yes, contract-first. Sources: https://camel.apache.org/manual/rest-dsl-openapi.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html

## Contract-first setup

Since Camel 4.6, each `operationId` maps to `direct:<operationId>`; startup fails when a route is missing (medium confidence: unversioned page https://camel.apache.org/manual/rest-dsl-openapi.html). `missingOperation`: `fail` (default), `ignore`, `mock`; `mockIncludePattern` default `classpath:camel-mock/**` (https://camel.apache.org/components/4.22.x/rest-openapi-component.html).

```xml
<!-- https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/openapi-contract-first/pom.xml -->
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-rest-openapi</artifactId></dependency>
<dependency><groupId>org.apache.camel.quarkus</groupId><artifactId>camel-quarkus-openapi-java</artifactId></dependency>
<!-- quarkus-maven-plugin goals: generate-code, build -->
```

The rest-openapi producer needs a `RestProducerFactory` (`camel-quarkus-http` or `camel-quarkus-netty-http`) (rest-openapi extension page).

## Code generation defaults

Build-time defaults from https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html: `quarkus.camel.openapi.codegen.enabled=true`, `model-package=org.apache.camel.quarkus`, `use-bean-validation=false`, `not-null-jackson=false`, `ignore-unknown-properties=false`. Contract files under `src/main/openapi` (investigator notes, medium confidence).

## Code-first publishing

The `expose.enabled` default (`false`, build time) is High: versioned page https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html. Medium confidence applies only to the `apiContextPath` example value (main-branch example, no default on the main options page) and to the merge into `/q/openapi` (partial evidence).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `camel.rest.apiContextPath=/api-doc` (example value from the official example; no default on the main options page) | No extra extension | Separate path to secure | Camel-only API |
| `quarkus.camel.openapi.expose.enabled=true` (default `false`, build time) + `quarkus-smallrye-openapi` merges into `/q/openapi` | Single spec with Quarkus REST endpoints, Swagger UI | Extra dependency; build-time flag | Quarkus REST and Camel REST coexist |

Whether the doc path needs its own `quarkus.http.auth.permission` entry is (unverified); add an explicit permission as a workaround. Sources: https://raw.githubusercontent.com/apache/camel-quarkus-examples/main/openapi-contract-first/src/main/resources/application.properties ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html

## Native mode

(medium confidence) The contract-file location and the plural `includes` property name rest on a main-branch example and investigator notes, not on a versioned page read in full by the researcher (evidence rule).

- openapi-java: "It's the users responsibility to use `@RegisterForReflection` to register all model classes for reflection" (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/openapi-java.html).
- Contract files must be added to the native image (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/rest-openapi.html). That page mixes `quarkus.native.resources.include` and `includes`; the official example uses the plural `quarkus.native.resources.includes`.

```java
@io.quarkus.runtime.annotations.RegisterForReflection
public record Fruit(String name, String description) {}
```

3.40.0 release notes list #9195 (openapi-java native WARN/ERROR from the swagger ModelResolver, `@JsonValue` rendered as objects) and #9153 (native build fails when the kamelet `DelegatingSchemaResolver` is reachable without camel-jackson): https://camel.apache.org/releases/q-3.40.0/
