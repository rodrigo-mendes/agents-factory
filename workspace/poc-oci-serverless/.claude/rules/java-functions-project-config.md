---
paths:
  - "**/{pom.xml,func.yaml,Dockerfile}"
---
You are an OCI Functions Project Configuration specialist for FDK v1.1.x + Java 17.
Ensure all project files (pom.xml, func.yaml, Dockerfile) follow correct patterns for production-ready serverless Java.

For project directory layout, artifact naming, and configuration key naming conventions, see `java-functions-project-structure.md`.
For complete code patterns and Maven POM examples, load the skill: `.claude/skills/developing-oci-functions-java/SKILL.md`

## When to Load This Skill

Load `developing-oci-functions-java` when the user request involves:
- Creating or modifying pom.xml dependencies
- Configuring func.yaml settings
- Writing or modifying Dockerfile
- Sizing function memory and timeout

## Maven POM Rules

### Dependency Version Rules
- ALWAYS use OCI SDK BOM — `oci-java-sdk-bom` manages all SDK module versions
- ALWAYS pin FDK version (currently v1.1.11) — no LATEST or SNAPSHOT
- ALWAYS pin test dependency versions (JUnit 4.13.2, Mockito 5.12.0)
- SDK modules declared WITHOUT version when BOM is used
- Required FDK dependencies: `api` (core), `fn-events` (typed events)
- Required test dependencies: `testing-core`, `fn-events-testing`

### Version Reference

| Component | Version | GroupId:ArtifactId |
|-----------|---------|-------------------|
| FDK Core | 1.1.11 | `com.fnproject.fn:api` |
| fn-events | 1.1.11 | `com.fnproject.fn:fn-events` |
| OCI SDK BOM | 3.86.1 | `com.oracle.oci.sdk:oci-java-sdk-bom` |
| JUnit | 4.13.2 | `junit:junit` |
| Mockito | 5.12.0 | `org.mockito:mockito-core` |
| FDK Testing | 1.1.11 | `com.fnproject.fn:testing-core` |
| fn-events Testing | 1.1.11 | `com.fnproject.fn:fn-events-testing` |

## func.yaml Rules

### ⚠️ CRITICAL: func.yaml vs Docker/Terraform Deployment

`func.yaml` is used **ONLY by `fn` CLI** (local development). When deploying via Docker image + Terraform:

| Setting | fn CLI (func.yaml) | Docker/Terraform |
|---------|-------------------|------------------|
| Entry point | `cmd:` field | `CMD` instruction in Dockerfile |
| Config values | `config:` section | `oci_functions_application.config` in Terraform |
| Timeout | `timeout:` field | `timeout_in_seconds` in `oci_functions_function` |
| Memory | `memory:` field | `memory_in_mbs` in `oci_functions_function` |

**Implications:**
- Changing `cmd:` in func.yaml has NO EFFECT on Docker deployments — must also update Dockerfile CMD
- Config values in func.yaml are IGNORED by Docker deployments — must be set in Terraform
- **NEVER put secrets/credentials in func.yaml** — it's tracked by Git. Use OCI Vault + Terraform config references

### func.yaml Configuration

- `cmd`: use `::handler` for fn-events abstract classes, `::handleRequest` for direct POJO handlers
- `memory`: determines proportional CPU allocation (see sizing guide below)
- `timeout`: MUST accommodate all downstream calls + retries + buffer
- `config`: 4KB total limit for all keys+values — use for OCIDs and endpoints, NOT secret values
- Precedence: Function config > Application config > Defaults

## Dockerfile Rules

- Build image: `fnproject/fn-java-fdk-build:jdk17-latest`
- Runtime image: `fnproject/fn-java-fdk:jre17-latest`
- Multi-stage build: separate build and runtime stages for minimal image size
- Layer caching: copy pom.xml first, then source — dependencies cached across builds
- CMD: must match func.yaml `cmd` entry point

## Resource Sizing Guide

| Memory (MB) | CPU (approx) | Use Case |
|-------------|-------------|----------|
| 128 | ~0.08 vCPU | Minimal handlers, config lookups |
| 256 | ~0.17 vCPU | Simple API handlers, 1-2 SDK calls |
| 512 | ~0.33 vCPU | File processing, multiple SDK calls |
| 1024 | ~0.67 vCPU | Data transformations, JSON processing |
| 2048 | ~1.33 vCPU | Large file processing, complex computation |

### Sizing Strategy (Cost-Optimized)
- Start at 256MB for most functions
- Measure via OCI Monitoring `FunctionExecutionDuration` metric
- Increase only if cold start > SLA or execution hits CPU limits
- Compute shape: GENERIC_X86 (default, maximum compatibility)

### Timeout Configuration
- Default 30s is DANGEROUS — SDK default read timeout is 60s (exceeds function timeout)
- Recommended: 60s for functions with OCI SDK calls
- Calculate: sum of all downstream timeouts + retry budget + 20s buffer

## ✅ Always Do
- Use OCI SDK BOM for version alignment — `oci-java-sdk-bom`
- Pin ALL dependency versions — FDK, SDK, test libraries
- Use multi-stage Docker build — separate build and runtime stages
- Set `func.yaml` timeout to 60s for functions with OCI SDK calls
- Use `jdk17-latest` build image and `jre17-latest` runtime image
- Copy pom.xml before source in Dockerfile — layer caching optimization
- Match CMD in Dockerfile with `cmd` in func.yaml

## 🚫 Never Do
- Use LATEST or SNAPSHOT versions in pom.xml — reproducibility risk
- Mix SDK module versions — use BOM for alignment
- Use single-stage Docker build — bloated runtime image with build tools
- Set function timeout below SDK default read timeout (60s) without configuring SDK timeouts
- Skip test dependencies — `testing-core` and `fn-events-testing` required for FDK tests
- Override Mockito's bundled ByteBuddy version — causes JVM incompatibility cascades
- Add explicit `byte-buddy` or `byte-buddy-agent` dependencies — let Mockito manage transitively
- Add `mockito-inline` dependency — does not exist in Mockito 5.x (inline is default)

## JVM Version Enforcement

### Required Environment
- **Build JVM**: Java 21 (Amazon Corretto recommended)
- **Source/Target**: Java 17 (pom.xml compiler settings)
- **Container Runtime**: JRE 17 (fnproject/fn-java-fdk:jre17-latest)
- **NOT supported**: Java 25+ for testing (Mockito cannot mock sealed JDK classes)

### Pre-Build Validation (MANDATORY)
Before any Maven command, verify JVM consistency:
```bash
java -version 2>&1 | head -1
mvn -version 2>&1 | grep "Java version"
echo "JAVA_HOME=${JAVA_HOME:-NOT SET}"
```
All three MUST report the same major version. If they differ:
```bash
# macOS fix:
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
```

### .mvn/jvm.config
Every project SHOULD include `.mvn/jvm.config` (can be empty) to document JVM requirements.

### Dependency Anti-Patterns (CRITICAL)

❌ **Never add these to pom.xml:**
```xml
<!-- ❌ Does not exist in Mockito 5.x -->
<artifactId>mockito-inline</artifactId>

<!-- ❌ Conflicts with Mockito's bundled version -->
<artifactId>byte-buddy</artifactId>
<version>1.15.10</version>

<!-- ❌ Same conflict -->
<artifactId>byte-buddy-agent</artifactId>
```

✅ **Correct minimal test dependencies:**
```xml
<dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-core</artifactId>
    <version>5.12.0</version>
    <scope>test</scope>
</dependency>
<!-- ByteBuddy managed transitively by Mockito — DO NOT override -->
```
