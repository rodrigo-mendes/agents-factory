---
name: scaffolding-oci-function
description: Generates a complete, deploy-ready OCI Function project scaffold with all mandatory patterns pre-applied (initError, CMD, httpclient-jersey, observability, timeout budget). Use when creating a new function from scratch, adding a function to services/, or needing a guaranteed-deployable starting point with all postmortem patterns pre-applied.
---

## Version Context

**Technology**: OCI Functions (Fn Project) — Java runtime
**Target Versions**: FDK Java 1.1.x; OCI Java SDK 3.86.x; Java 17 (Amazon Corretto); Maven 3.x
**Support Status**: Active stable
**Version Lock rule**: always read the actual versions from an existing `services/*/pom.xml` — do not hardcode. Reuse exact FDK/SDK versions from the fleet so the new function stays consistent.

**Key version facts**:
- `fnproject/fn-java-fdk-build:jdk17-latest` and `fnproject/fn-java-fdk:jre17-latest` are the correct Docker base images for Java 17
- `oci-java-sdk-common-httpclient-jersey` is required whenever any OCI SDK module is used (missing it causes a runtime crash, not a compile error)
- `cmd:` in `func.yaml` must match the `CMD` instruction in the Dockerfile — mismatch causes 502

⚠️ **Version Lock**: Patterns target FDK 1.1.x / SDK 3.86.x. Do not mix with Fn 2.x patterns or GraalVM native configurations.

---

## Quick Navigation

- **[What This Skill Produces](#what-this-skill-produces)**
- **[Scaffold Parameters](#scaffold-parameters)**
- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅ Always Do / ⚠️ Ask First / 🚫 Never Do
- **[Templates](#templates)** — Handler, Response, Request, Dockerfile, build-push.sh
- **[Checklist: Scaffold Complete](#checklist-scaffold-complete)**
- **[External Resources](#external-resources)**
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**

---

## What This Skill Produces

A complete function directory under `services/<function-name>/` containing:

```
services/<function-name>/
├── Dockerfile          ← Multi-stage build with CMD (mandatory)
├── func.yaml           ← Function metadata, timeout=60s
├── pom.xml             ← FDK + OCI SDK BOM + httpclient-jersey
├── build-push.sh       ← Build & push script (executable)
├── README.md           ← Function description & endpoints
└── src/
    ├── main/java/com/brx/functions/<package>/
    │   ├── <Class>Function.java      ← Handler with initError + observability
    │   └── model/
    │       ├── <Name>Request.java    ← Input model
    │       └── <Name>Response.java   ← Output model with elapsed_ms
    └── test/java/com/brx/functions/<package>/
        └── <Class>FunctionTest.java  ← FnTestingRule unit test
```

---

## Scaffold Parameters

Before generating, collect:

| Parameter | Example | Required |
|-----------|---------|----------|
| `function-name` | `func-order-processor` | yes |
| `package` | `order.processor` | yes |
| `class-name` | `OrderProcessor` | yes |
| `handler-pattern` | APIGateway / ConnectorHub / Notification | yes |
| `uses-oci-sdk` | yes/no | yes |
| `uses-external-api` | yes/no (adds OAuth2, HttpClient) | yes |
| `uses-vault` | yes/no (adds OciSecretService) | yes |
| `memory-mb` | 256 (default) | optional |
| `timeout-s` | 60 (default) | optional |

---

## Blueprints & Guardrails

### ✅ Always Do

- Generate `CMD` in Dockerfile matching `func.yaml cmd:` — omitting CMD guarantees 502 on every invocation.
- Include `oci-java-sdk-common-httpclient-jersey` in `pom.xml` whenever any OCI SDK module is used.
- Implement the `initError` pattern in every handler: catch all `configure()` exceptions, store in `initError`, check `initError != null` as the FIRST action in `handler()`.
- Include `elapsed_ms` in all response models.
- Set `timeout` to 60s (or higher) for functions with external calls (OCI SDK, HTTP clients).
- Make `build-push.sh` call `preflight.sh` before building.
- Read FDK/SDK versions from an existing `services/*/pom.xml` — never hardcode.

### ⚠️ Ask First

**Handler pattern selection**
- `APIGatewayFunction`: use for REST/HTTP endpoints exposed via API Gateway. Provides typed request/response, routing helpers.
- `ConnectorHubFunction`: use for Service Connector Hub pipelines (log forwarding, streaming). Handler is void.
- `Notification`: use for OCI Notifications triggers (topic subscription). Payload is a JSON envelope.
- Ask: "Will this function be called from API Gateway, Service Connector Hub, or a Notification topic?" — the base class and test setup differ for each.

**OCI SDK inclusion**
- Adding any OCI SDK module increases cold start time (+100–400ms) and requires `httpclient-jersey`.
- Ask: "Does this function actually need to call OCI APIs directly, or can it rely on environment-injected config and existing service clients passed in?" — avoid the SDK if the function only delegates to another service.

**Vault integration**
- `OciSecretService` adds a cold-start OCI API call to retrieve secrets.
- Ask: "Are the required secrets already injected as function config keys via Terraform, or do they need to be fetched at runtime?" — prefer config-key injection for secrets that do not rotate frequently.

**Memory and timeout overrides**
- Defaults: 256 MB / 60s. Changing them has cost and concurrency implications.
- Ask: "What is the expected payload size and downstream latency? OCI bills per GB-second." — only increase memory if profiling shows GC pressure; only increase timeout if the SLA allows it.

### 🚫 Never Do

**Never create a Dockerfile without CMD**
```dockerfile
# 🚫 WRONG — container starts then immediately exits → 502 on every invoke
FROM fnproject/fn-java-fdk:jre17-latest
WORKDIR /function
COPY --from=build /function/target/*.jar /function/app/

# ✅ CORRECT — CMD must match func.yaml cmd:
CMD ["com.brx.functions.{{package}}.{{Class}}Function::handler"]
```
Impact: guaranteed 502 on every invocation; no error in function logs.

**Never use OCI SDK without httpclient-jersey**
```xml
<!-- 🚫 WRONG — compiles fine, crashes at runtime with NoClassDefFoundError -->
<dependency>
  <groupId>com.oracle.oci.sdk</groupId>
  <artifactId>oci-java-sdk-objectstorage</artifactId>
</dependency>

<!-- ✅ CORRECT — always pair with the HTTP client -->
<dependency>
  <groupId>com.oracle.oci.sdk</groupId>
  <artifactId>oci-java-sdk-objectstorage</artifactId>
</dependency>
<dependency>
  <groupId>com.oracle.oci.sdk</groupId>
  <artifactId>oci-java-sdk-common-httpclient-jersey</artifactId>
</dependency>
```
Impact: runtime crash on first OCI API call; stack trace buried in Fn logs.

**Never skip the initError pattern**
```java
// 🚫 WRONG — init failure is invisible; every invocation gets NullPointerException
@FnConfiguration
public void configure(RuntimeContext ctx) {
    this.client = new ObjectStorageClient(provider);
}

// ✅ CORRECT — capture init failure, report it on every invoke
@FnConfiguration
public void configure(RuntimeContext ctx) {
    try {
        this.client = new ObjectStorageClient(provider);
    } catch (Exception e) {
        this.initError = e.getClass().getName() + ": " + e.getMessage();
        LOG.severe("INIT FAILED: " + initError);
    }
}
// In handler(): if (initError != null) return error(500, ...)
```
Impact: cold-start failures produce cryptic NPEs on every hot invocation; debugging takes 5x longer.

**Never put credentials in func.yaml**
```yaml
# 🚫 WRONG — credentials visible in OCI Console and Terraform state
config:
  DB_PASSWORD: "s3cr3t"

# ✅ CORRECT — inject from Vault via Terraform resource config or OciSecretService at runtime
config:
  DB_SECRET_OCID: "${oci_vault_secret.db_password.id}"
```
Impact: credentials exposed in OCI Console, Terraform state files, and CI logs.

**Never set timeout < 60s for functions with SDK calls**
```yaml
# 🚫 WRONG — OCI SDK cold start alone can take 2–5s; 30s leaves no headroom
timeout: 30

# ✅ CORRECT
timeout: 60
```
Impact: function times out before completing the OCI API call; client receives 504.

---

## Templates

### Handler (APIGatewayFunction Pattern)

See [blueprints/java-handler-template.md](blueprints/java-handler-template.md) — complete `{{Class}}Function` class extending `APIGatewayFunction`, with `initError` pattern, `coldStart` flag, `configure()` try-catch, and timed `handler()` method pre-wired.

---

### Response Model

See [blueprints/java-response-model-template.md](blueprints/java-response-model-template.md) — `{{Class}}Response` with `status`, `elapsed_ms` (mandatory), `erro`/`detalhe` error fields, and static factory methods `ok()` and `error()`.

---

### Request Model

See [blueprints/java-request-model-template.md](blueprints/java-request-model-template.md) — `{{Class}}Request` skeleton with `@JsonIgnoreProperties(ignoreUnknown = true)` and placeholder fields; add `@JsonProperty`-annotated getters per input field.

---

### pom.xml

The full `pom.xml` template (Java 17, FDK 1.1.x, OCI SDK + `httpclient-jersey`, Shade plugin, OCIR-ready)
lives in [templates/pom.xml](templates/pom.xml) — apply the same `{{placeholders}}` used by the other templates.

---

### Dockerfile

See [blueprints/dockerfile-template.md](blueprints/dockerfile-template.md) — multi-stage build using `fnproject/fn-java-fdk-build:jdk17-latest` (build) and `fnproject/fn-java-fdk:jre17-latest` (runtime), with mandatory `CMD` instruction.

---

### build-push.sh

Runnable template: [assets/build-push.sh](assets/build-push.sh) — copy to `services/<function-name>/build-push.sh` and `chmod +x` it. No hardcoded values; reads `OCIR_REGION`, `OCIR_NAMESPACE`, `OCIR_REPO`, `OCIR_USERNAME`, `OCIR_PASSWORD` from `services/.env` and function name/version from `func.yaml`.

Documentation and `.env` variable reference: [blueprints/build-push-script.md](blueprints/build-push-script.md).

---

## Checklist: Scaffold Complete

After generating, verify ALL are true:

- [ ] Dockerfile has `CMD` instruction matching `func.yaml cmd:`
- [ ] `pom.xml` has `oci-java-sdk-common-httpclient-jersey` if any OCI SDK module is used
- [ ] Handler has `private String initError` field
- [ ] Handler's `configure()` wraps body in try-catch, sets `initError` on failure
- [ ] Handler checks `initError != null` as FIRST action
- [ ] Response model includes `elapsed_ms` field
- [ ] No credentials or secrets in `func.yaml`
- [ ] `build-push.sh` is executable and calls `preflight.sh`
- [ ] `func.yaml` timeout >= 60s if OCI SDK is used
- [ ] Test file exists with at least a smoke test

---

## Verification Loop

Run from the scaffolded function directory (the one containing `pom.xml`, `Dockerfile`, `func.yaml`) to confirm the fresh scaffold builds and containerizes:

```bash
# 1. Compile and package the function JAR (skip tests for a fast structural check)
mvn clean package -DskipTests   # expected exit code 0; produces target/*.jar

# 2. Run the test suite (must include the smoke test)
mvn test                        # expected exit code 0; all tests green

# 3. Build the container image (uses the generated Dockerfile; same as build-push.sh)
docker build --platform linux/amd64 -t "$(grep '^name:' func.yaml | awk '{print $2}'):latest" .
                                # expected exit code 0; image built successfully
```

---

## External Resources

- [OCI Functions Developer Guide](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsoverview.htm) — official Functions overview (verified 2026-07-26)
- [FDK Java GitHub](https://github.com/fnproject/fdk-java) — FDK source, release notes, examples (verified 2026-07-26)
- [OCI Java SDK releases](https://github.com/oracle/oci-java-sdk/releases) — SDK changelog and version history (verified 2026-07-26)
- [Amazon Corretto 17](https://aws.amazon.com/corretto/) — JDK used in base images (verified 2026-07-26)
- [OCI Pricing](https://www.oracle.com/cloud/pricing/) — Functions billing (GB-second, invocations) (verified 2026-07-26)
