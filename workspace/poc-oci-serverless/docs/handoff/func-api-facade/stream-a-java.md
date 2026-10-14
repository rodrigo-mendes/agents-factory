---
kind: work-order
from: "@oci-serverless-architect"
to: "@oci-functions-java"
capability: func-api-facade
stream: a-java
dependsOn: none
status: completed
createdAt: 2026-05-18T00:00:00Z
---

## Scope

Create the `services/func-api-facade/` Java project implementing the API Facade pattern (Pattern 03). This function acts as a transformation layer between API Gateway and OCI backend services (Vault, Object Storage).

## Components

- [ ] `pom.xml` — FDK 1.1.11, OCI SDK 3.86.0, fn-events, Jackson, JUnit 5, Mockito
- [ ] `func.yaml` — name: `func-api-facade`, memory: 256, timeout: 60, cmd: `com.brx.functions.apifacade.ApiFacadeFunction::handler`
- [ ] `Dockerfile` — Multi-stage build JDK 17 (fnproject/fn-java-fdk-build:jdk17-latest → fnproject/fn-java-fdk:jre17-latest)
- [ ] `src/main/java/com/brx/functions/apifacade/ApiFacadeFunction.java` — Handler extending `APIGatewayFunction<ApiFacadeRequest, ApiFacadeResponse>`
- [ ] `src/main/java/com/brx/functions/apifacade/model/ApiFacadeRequest.java` — Input DTO (Jackson)
- [ ] `src/main/java/com/brx/functions/apifacade/model/ApiFacadeResponse.java` — Output DTO (statusCode, message, data)
- [ ] `src/main/java/com/brx/functions/apifacade/service/OciServiceClient.java` — OCI SDK clients (ObjectStorageClient, SecretsClient)
- [ ] `src/test/java/com/brx/functions/apifacade/ApiFacadeFunctionTest.java` — 6 unit tests

## Constraints

### Naming & Package

- Directory: `services/func-api-facade/`
- Package: `com.brx.functions.apifacade`
- Artifact: `func-api-facade`

### Handler Specification

| Aspect | Value |
|--------|-------|
| Base class | `APIGatewayFunction<ApiFacadeRequest, ApiFacadeResponse>` (fn-events) |
| Init | `@FnConfiguration` — reads `ENVIRONMENT` config, instantiates `OciServiceClient` |
| Routing | `switch(path)` — `/hello`, `/secret`, `/store` |
| Error codes | 400 (input inválido), 404 (rota não encontrada), 405 (método errado), 503 (OCI indisponível) |
| Logging | JSON structured (`{"event":"request","method":"...","path":"..."}`) |

### OCI Service Client Specification

| Aspect | Value |
|--------|-------|
| Auth | Resource Principal (OCI Functions) / Config File (local dev) |
| Retry | 3 attempts, exponential backoff with jitter (5s base) |
| Timeouts | 5s connection, 15s read |
| Clients | `ObjectStorageClient`, `SecretsClient` |

### Route Behavior

| Path | Method | Behavior |
|------|--------|----------|
| `/hello` | GET, POST | Returns message with environment variable |
| `/secret` | POST | Reads secret from Vault via `secretId` in request body |
| `/store` | POST | CRUD Object Storage via `bucket`, `objectName`, `content` in request body |

### func.yaml

```yaml
schema_version: 20180708
name: func-api-facade
version: 0.0.1
runtime: java
build_image: fnproject/fn-java-fdk-build:jdk17-latest
run_image: fnproject/fn-java-fdk:jre17-latest
cmd: com.brx.functions.apifacade.ApiFacadeFunction::handler
memory: 256
timeout: 60
config:
  ENVIRONMENT: dev
```

### Dependencies (pom.xml)

| GroupId | ArtifactId | Version | Scope |
|---------|-----------|---------|-------|
| com.fnproject.fn | api | 1.1.11 | compile |
| com.fnproject.fn | fn-events | 1.1.11 | compile |
| com.oracle.oci.sdk | oci-java-sdk-common | 3.86.0 | compile |
| com.oracle.oci.sdk | oci-java-sdk-secrets | 3.86.0 | compile |
| com.oracle.oci.sdk | oci-java-sdk-objectstorage | 3.86.0 | compile |
| com.fnproject.fn | testing-core | 1.1.11 | test |
| com.fnproject.fn | fn-events-testing | 1.1.11 | test |
| org.mockito | mockito-core | 5.x | test |
| org.junit.jupiter | junit-jupiter | 5.x | test |

## Dependencies

- No external dependencies — this stream can start immediately
- Reference existing `services/api-handler/` as implementation pattern (similar structure)
- Follow instructions in `.github/instructions/java-functions-*.instructions.md`

## Acceptance Criteria

- [ ] `cd services/func-api-facade && mvn clean package` compiles without errors
- [ ] All 6 tests pass:
  - `testHelloRoute` — GET /hello → 200 + message with environment
  - `testUnknownRoute` — GET /unknown → 404 "Route not found"
  - `testSecretRouteMissingResourceId` — POST /secret without body → 400
  - `testStoreRouteMissingFields` — POST /store without bucket/object → 400
  - `testSecretRouteOciUnavailable` — POST /secret with OCI client null → 503
  - `testSecretRouteWrongMethod` — GET /secret → 405
- [ ] `func.yaml` matches specification above
- [ ] Dockerfile builds successfully with `fn build`
