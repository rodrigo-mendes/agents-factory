# ==============================================================================
# Multi-stage build para OCI Function Java
# Stage 1: Build com Maven
# Stage 2: Runtime mínimo com FDK JRE
# ==============================================================================

# --- BUILD STAGE ---
FROM fnproject/fn-java-fdk-build:jdk17-latest AS build-stage

WORKDIR /function

# Copiar pom.xml primeiro para cache de dependências
COPY pom.xml /function/pom.xml
RUN mvn package dependency:copy-dependencies \
    -DincludeScope=runtime \
    -DskipTests=true \
    -Dmdep.prependGroupId=true \
    -DoutputDirectory=target \
    --fail-never

# Copiar código-fonte e buildar
COPY src /function/src
RUN mvn package dependency:copy-dependencies \
    -DincludeScope=runtime \
    -DskipTests=true \
    -Dmdep.prependGroupId=true \
    -DoutputDirectory=target

# --- RUNTIME STAGE ---
FROM fnproject/fn-java-fdk:jre17-latest

WORKDIR /function

COPY --from=build-stage /function/target/*.jar /function/app/

CMD ["com.brx.functions.apifacade.ApiFacadeFunction::handler"]
