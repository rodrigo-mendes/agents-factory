# Blueprint: Dockerfile Template

Multi-stage Dockerfile for Java 17 OCI Functions. Replace `{{package}}` and `{{Class}}`.

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

# MANDATORY — without CMD, container exits immediately → 502
CMD ["{{groupId}}.{{package}}.{{Class}}Function::handler"]
```

## Checklist

- The `CMD` value must exactly match `cmd:` in `func.yaml` — a mismatch causes 502 with no useful error.
- Both JARs layers are required: the shaded JAR (`target/*.jar`) and the dependency JARs (`target/dependency/*.jar`).
- Base images: `fnproject/fn-java-fdk-build:jdk17-latest` (build stage) and `fnproject/fn-java-fdk:jre17-latest` (runtime stage).

## Worked Example (from the reference PoC)

The canonical template from `services/.templates/Dockerfile.template` (poc-oci-serverless):

```dockerfile
# ==============================================================================
# OCI Function Dockerfile Template
# Replace: {{PACKAGE}}, {{CLASS}}, {{HANDLER}}
# ==============================================================================

# --- Stage 1: Build ---
FROM fnproject/fn-java-fdk-build:jdk17-latest as build
WORKDIR /function
COPY pom.xml /function/pom.xml
RUN ["mvn", "package", "dependency:copy-dependencies", "-DincludeScope=runtime", \
     "-DskipTests=true", "-Dmdep.prependGroupId=true", "--fail-never"]
COPY src /function/src
RUN ["mvn", "package", "-DskipTests=true"]

# --- Stage 2: Runtime ---
FROM fnproject/fn-java-fdk:jre17-latest
WORKDIR /function
COPY --from=build /function/target/*.jar /function/app/
COPY --from=build /function/target/dependency/*.jar /function/app/

# ⚠️ MANDATORY: Without CMD, container immediately exits → HTTP 502 with zero logs
# This is the ONLY way Docker/Terraform know which class/method to invoke.
# Must match the `cmd:` field in func.yaml exactly.
CMD ["{{PACKAGE}}.{{CLASS}}::{{HANDLER}}"]
```

And the matching `func.yaml.template`:

```yaml
# from services/.templates/func.yaml.template (poc-oci-serverless)
schema_version: 20180708
name: {{FUNCTION_NAME}}
version: 0.0.1
runtime: java
build_image: fnproject/fn-java-fdk-build:jdk17-latest
run_image: fnproject/fn-java-fdk:jre17-latest
cmd: {{PACKAGE}}.{{CLASS}}::{{HANDLER}}
memory: 256
timeout: 60
```

The `cmd:` field and the Dockerfile `CMD` instruction MUST be identical strings.
