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
CMD ["com.brx.functions.{{package}}.{{Class}}Function::handler"]
```

## Checklist

- The `CMD` value must exactly match `cmd:` in `func.yaml` — a mismatch causes 502 with no useful error.
- Both JARs layers are required: the shaded JAR (`target/*.jar`) and the dependency JARs (`target/dependency/*.jar`).
- Base images: `fnproject/fn-java-fdk-build:jdk17-latest` (build stage) and `fnproject/fn-java-fdk:jre17-latest` (runtime stage).
