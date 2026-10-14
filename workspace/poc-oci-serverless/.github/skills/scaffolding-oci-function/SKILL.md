# Skill: Scaffolding OCI Functions

**Description:** Generates a complete, deploy-ready OCI Function project scaffold with all mandatory patterns pre-applied (initError, CMD, httpclient-jersey, observability, timeout budget).

**Use when:**
- Creating a new function from scratch
- Adding a new function to the existing `services/` directory
- Need a guaranteed-deployable starting point (all postmortem patterns pre-applied)

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
| `function-name` | `func-order-processor` | ✅ |
| `package` | `order.processor` | ✅ |
| `class-name` | `OrderProcessor` | ✅ |
| `handler-pattern` | APIGateway / ConnectorHub / Notification | ✅ |
| `uses-oci-sdk` | yes/no | ✅ |
| `uses-external-api` | yes/no (adds OAuth2, HttpClient) | ✅ |
| `uses-vault` | yes/no (adds OciSecretService) | ✅ |
| `memory-mb` | 256 (default) | Optional |
| `timeout-s` | 60 (default) | Optional |

---

## Template: Handler (APIGatewayFunction Pattern)

```java
package com.brx.functions.{{package}};

import java.util.logging.Level;
import java.util.logging.Logger;

import com.brx.functions.{{package}}.model.{{Class}}Request;
import com.brx.functions.{{package}}.model.{{Class}}Response;
import com.fnproject.events.APIGatewayFunction;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;

public class {{Class}}Function extends APIGatewayFunction<{{Class}}Request, {{Class}}Response> {

    private static final Logger LOG = Logger.getLogger({{Class}}Function.class.getName());

    private String initError;
    private boolean coldStart = true;
    private String version;

    @Override
    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        super.configure(ctx);
        long start = System.currentTimeMillis();

        try {
            this.version = ctx.getConfigurationByKey("FN_APP_ID").orElse("local");

            // --- Initialize your resources here ---
            // SDK clients, HttpClient, ObjectMapper, etc.
            // Each subsystem should be logged:
            // LOG.info("INIT: Creating SDK client...");

            LOG.info("{{Class}}Function initialized successfully");
        } catch (Exception e) {
            this.initError = e.getClass().getName() + ": " + e.getMessage();
            LOG.severe("INIT FAILED: " + initError);
        }

        long elapsed = System.currentTimeMillis() - start;
        LOG.info(String.format("COLD_START completed in %dms | error=%s",
                elapsed, initError != null ? initError : "none"));
    }

    @Override
    public APIGatewayResponseEvent<{{Class}}Response> handler(APIGatewayRequestEvent<{{Class}}Request> req) {
        long startTime = System.currentTimeMillis();
        String path = req.getPath();
        LOG.info(String.format("INVOKE %s %s | coldStart=%s", req.getMethod(), path, coldStart));
        coldStart = false;

        try {
            // 0. Check initialization
            if (initError != null) {
                return error(500, {{Class}}Response.error("Function init failed", initError));
            }

            // 1. Validate input
            {{Class}}Request body = req.getBody();
            // TODO: Add input validation

            // 2. Business logic
            // TODO: Implement

            // 3. Return success
            long elapsed = System.currentTimeMillis() - startTime;
            LOG.info(String.format("COMPLETE %s | status=200 | elapsed=%dms", path, elapsed));
            return success({{Class}}Response.ok("Success", null, elapsed));

        } catch (Exception e) {
            long elapsed = System.currentTimeMillis() - startTime;
            String detail = e.getClass().getName() + ": " + e.getMessage();
            LOG.log(Level.SEVERE, String.format("FAILED %s | elapsed=%dms | %s", path, elapsed, detail), e);
            return error(500, {{Class}}Response.error("Internal server error", detail, elapsed));
        }
    }
}
```

---

## Template: Response Model

```java
package com.brx.functions.{{package}}.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class {{Class}}Response {
    private String status;
    private String message;
    private Object data;

    @JsonProperty("elapsed_ms")
    private long elapsedMs;

    private String erro;
    private String detalhe;

    @JsonProperty("cold_start")
    private Boolean coldStart;

    public static {{Class}}Response ok(String message, Object data, long elapsedMs) {
        {{Class}}Response r = new {{Class}}Response();
        r.status = "sucesso";
        r.message = message;
        r.data = data;
        r.elapsedMs = elapsedMs;
        return r;
    }

    public static {{Class}}Response error(String erro, String detalhe) {
        return error(erro, detalhe, 0);
    }

    public static {{Class}}Response error(String erro, String detalhe, long elapsedMs) {
        {{Class}}Response r = new {{Class}}Response();
        r.status = "erro";
        r.erro = erro;
        r.detalhe = detalhe;
        r.elapsedMs = elapsedMs;
        return r;
    }

    // Getters
    public String getStatus() { return status; }
    public String getMessage() { return message; }
    public Object getData() { return data; }
    public long getElapsedMs() { return elapsedMs; }
    public String getErro() { return erro; }
    public String getDetalhe() { return detalhe; }
    public Boolean getColdStart() { return coldStart; }
}
```

---

## Template: Request Model

```java
package com.brx.functions.{{package}}.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class {{Class}}Request {
    // TODO: Add request fields

    // Example:
    // @JsonProperty("resource_id")
    // private String resourceId;
}
```

---

## Template: pom.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.brx.functions</groupId>
    <artifactId>{{function-name}}</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <fdk.version>1.1.11</fdk.version>
    </properties>

    <dependencyManagement>
        <dependencies>
            <!-- OCI SDK BOM — manages ALL SDK module versions -->
            <dependency>
                <groupId>com.oracle.oci.sdk</groupId>
                <artifactId>oci-java-sdk-bom</artifactId>
                <version>3.86.1</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <dependencies>
        <!-- FDK Core -->
        <dependency>
            <groupId>com.fnproject.fn</groupId>
            <artifactId>api</artifactId>
            <version>${fdk.version}</version>
        </dependency>

        <!-- FDK Events (APIGatewayFunction typed abstractions) -->
        <dependency>
            <groupId>com.fnproject.fn</groupId>
            <artifactId>fn-events</artifactId>
            <version>${fdk.version}</version>
        </dependency>

        <!-- JSON Processing -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.17.2</version>
        </dependency>

        <!-- ================================================================
             OCI SDK Dependencies (uncomment as needed)
             ================================================================ -->

        <!-- OCI SDK HTTP Client Provider (MANDATORY if using ANY OCI SDK module) -->
        <!-- Without this: "NoSuchElementException: No http provider available" -->
        <!--
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-common-httpclient-jersey</artifactId>
        </dependency>
        -->

        <!-- OCI SDK Common (Resource Principal auth, base client) -->
        <!--
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-common</artifactId>
        </dependency>
        -->

        <!-- OCI Vault/Secrets (for credential retrieval) -->
        <!--
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-vault</artifactId>
        </dependency>
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-secrets</artifactId>
        </dependency>
        -->

        <!-- OCI Object Storage -->
        <!--
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-objectstorage</artifactId>
        </dependency>
        -->

        <!-- ================================================================
             Test Dependencies
             ================================================================ -->
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.mockito</groupId>
            <artifactId>mockito-core</artifactId>
            <version>5.12.0</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.fnproject.fn</groupId>
            <artifactId>testing-core</artifactId>
            <version>${fdk.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.fnproject.fn</groupId>
            <artifactId>fn-events-testing</artifactId>
            <version>${fdk.version}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>17</source>
                    <target>17</target>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.5</version>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-dependency-plugin</artifactId>
                <version>3.6.1</version>
                <executions>
                    <execution>
                        <id>copy-dependencies</id>
                        <phase>package</phase>
                        <goals><goal>copy-dependencies</goal></goals>
                        <configuration>
                            <outputDirectory>${project.build.directory}/dependency</outputDirectory>
                            <includeScope>runtime</includeScope>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>

    <repositories>
        <repository>
            <id>fn-release</id>
            <url>https://dl.bintray.com/fnproject/fnproject</url>
            <releases><enabled>true</enabled></releases>
            <snapshots><enabled>false</enabled></snapshots>
        </repository>
    </repositories>
</project>
```

---

## Template: Dockerfile

```dockerfile
FROM fnproject/fn-java-fdk-build:jdk17-latest as build

WORKDIR /function
COPY pom.xml /function/pom.xml
RUN ["mvn", "package", "dependency:copy-dependencies", "-DincludeScope=runtime", \
     "-DskipTests=true", "-Dmdep.prependGroupId=true", "--fail-never"]

COPY src /function/src
RUN ["mvn", "package", "-DskipTests=true"]

FROM fnproject/fn-java-fdk:jre17-latest

WORKDIR /function
COPY --from=build /function/target/*.jar /function/app/
COPY --from=build /function/target/dependency/*.jar /function/app/

# ⚠️ MANDATORY — without CMD, container dies immediately → 502
CMD ["com.brx.functions.{{package}}.{{Class}}Function::handler"]
```

---

## Template: build-push.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

# Pre-flight checks
if [[ -f "${SCRIPT_DIR}/../../scripts/preflight.sh" ]]; then
  echo "==> Running pre-flight checks..."
  "${SCRIPT_DIR}/../../scripts/preflight.sh" "${SCRIPT_DIR}"
fi

# Load environment
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} not found."
  exit 1
fi
source "${ENV_FILE}"

for var in OCIR_REGION OCIR_NAMESPACE OCIR_REPO OCIR_USERNAME OCIR_PASSWORD; do
  if [[ -z "${!var:-}" ]]; then
    echo "ERROR: ${var} not set in ${ENV_FILE}"
    exit 1
  fi
done

echo "==> Logging in to ${OCIR_REGION}.ocir.io"
echo "${OCIR_PASSWORD}" | docker login "${OCIR_REGION}.ocir.io" -u "${OCIR_USERNAME}" --password-stdin

FUNC_NAME=$(grep '^name:' "${SCRIPT_DIR}/func.yaml" | awk '{print $2}')
TAG="${1:-$(grep '^version:' "${SCRIPT_DIR}/func.yaml" | awk '{print $2}')}"
PLATFORM="${PLATFORM:-linux/amd64}"
IMAGE="${OCIR_REGION}.ocir.io/${OCIR_NAMESPACE}/${OCIR_REPO}/${FUNC_NAME}:${TAG}"

echo "==> Building ${IMAGE} (platform: ${PLATFORM})"
env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy \
  docker build --platform "${PLATFORM}" -t "${IMAGE}" "${SCRIPT_DIR}"

echo "==> Pushing ${IMAGE}"
docker push "${IMAGE}"

echo ""
echo "Done! Image URI: ${IMAGE}"
```

---

## Checklist: Scaffold Complete

After generating, verify ALL are true:

- [ ] Dockerfile has `CMD` instruction matching func.yaml `cmd:`
- [ ] pom.xml has `oci-java-sdk-common-httpclient-jersey` if any OCI SDK is used
- [ ] Handler has `private String initError` field
- [ ] Handler's `configure()` wraps body in try-catch, sets initError on failure
- [ ] Handler checks `initError != null` as FIRST action
- [ ] Response model includes `elapsed_ms` field
- [ ] No credentials or secrets in func.yaml
- [ ] `build-push.sh` is executable and calls preflight.sh
- [ ] func.yaml timeout ≥ 60s if OCI SDK is used
- [ ] Test file exists with at least a smoke test

---

## ✅ Always Do
- Generate CMD in Dockerfile matching func.yaml cmd — NEVER omit
- Include httpclient-jersey if any OCI SDK module is used
- Implement initError pattern in EVERY handler
- Include elapsed_ms in all response models
- Set timeout to 60s for functions with external calls
- Make build-push.sh call preflight.sh before building

## 🚫 Never Do
- Create a Dockerfile without CMD — guaranteed 502
- Use OCI SDK without httpclient-jersey — guaranteed runtime crash
- Skip initError pattern — makes debugging 5x slower
- Put credentials in func.yaml — security vulnerability
- Set timeout < 60s for functions with SDK calls — timeout before response
