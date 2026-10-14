# Version Compatibility Matrix

Tested and supported version combinations for OCI Functions Java projects.

---

## OCI Functions Java Stack

| Component | Version | GroupId:ArtifactId | Notes |
|-----------|---------|-------------------|-------|
| Java (source/target) | 17 | — | pom.xml compiler settings |
| Java (build/test JVM) | 21 (Corretto) | — | JAVA_HOME must point here |
| FDK Core | 1.1.11 | `com.fnproject.fn:api` | Pinned |
| fn-events | 1.1.11 | `com.fnproject.fn:fn-events` | Pinned |
| OCI SDK BOM | 3.86.1 | `com.oracle.oci.sdk:oci-java-sdk-bom` | Manages all SDK modules |
| JUnit | 4.13.2 | `junit:junit` | |
| Mockito | 5.12.0 | `org.mockito:mockito-core` | Bundles ByteBuddy 1.14.x |
| JaCoCo | 0.8.13 | `org.jacoco:jacoco-maven-plugin` | Supports Java 21-22 bytecode |
| Surefire | 3.2.2 | `org.apache.maven.plugins:maven-surefire-plugin` | |
| Jackson | 2.17.x | managed by FDK | Do not override |
| JAXB (API) | 4.0.2 | `jakarta.xml.bind:jakarta.xml.bind-api` | For XML marshalling |
| JAXB (Runtime) | 4.0.5 | `org.glassfish.jaxb:jaxb-runtime` | |

---

## Java Version Compatibility

| Java Version | Build | Test | Mock HttpClient | JaCoCo | Status |
|-------------|-------|------|-----------------|--------|--------|
| 17 | ✅ | ✅ | ✅ | 0.8.12+ | ✅ Fully supported |
| 21 (Corretto) | ✅ | ✅ | ✅ | 0.8.12+ | ✅ **Recommended** |
| 21 (OpenJDK) | ✅ | ✅ | ✅ | 0.8.12+ | ✅ Supported |
| 22-24 | ✅ | ⚠️ | ⚠️ | 0.8.13+ | ⚠️ Untested |
| 25+ (Homebrew) | ✅ | ❌ | ❌ Sealed class | 0.8.13+ | ❌ **Not supported** |

### Why Java 25+ Breaks Tests

Java 25 made `java.net.http.HttpClient` a sealed class. ByteBuddy (used by Mockito) cannot subclass sealed classes to create mocks. This is a fundamental JVM restriction — no library upgrade can fix it on Java 25.

**Workaround options for Java 25+ (if needed in future):**
1. Use Java 21 for testing (recommended)
2. Use interface-based abstraction (adds complexity)
3. Wait for Mockito to support sealed class mocking

---

## Dependency Override Rules

| Dependency | Can Override? | Reason |
|-----------|-------------|--------|
| FDK version | ✅ Yes | Pin to specific tested version |
| OCI SDK BOM | ✅ Yes | Pin to specific tested version |
| Mockito | ✅ Yes | Pin version in pom.xml |
| ByteBuddy | ❌ **NEVER** | Managed by Mockito — override causes conflicts |
| byte-buddy-agent | ❌ **NEVER** | Same as above |
| mockito-inline | ❌ **NEVER** | Does not exist in Mockito 5.x |
| JaCoCo | ✅ Yes | Must match JVM version |
| Jackson | ⚠️ Careful | FDK manages — only override if SDK requires newer |

---

## Known Incompatibilities

### ByteBuddy 1.15.x + JaCoCo 0.8.12
- **Symptom:** `Unsupported class file major version 69`
- **Cause:** ByteBuddy 1.15.10 generates Java 25 bytecode; JaCoCo 0.8.12 can't instrument it
- **Fix:** Remove explicit ByteBuddy override (let Mockito use 1.14.x), OR upgrade JaCoCo to 0.8.13

### Mockito 5.12.0 + Java 25
- **Symptom:** `Mockito cannot mock this class: class java.net.http.HttpClient`
- **Cause:** Sealed class in Java 25 prevents subclassing
- **Fix:** Use Java 21 for build/test

### mockito-inline artifact
- **Symptom:** `Could not find artifact org.mockito:mockito-inline:jar:5.12.0`
- **Cause:** Artifact removed in Mockito 5.x (inline is now default)
- **Fix:** Remove dependency from pom.xml

---

## Container Image Versions

| Image | Purpose | Base |
|-------|---------|------|
| `fnproject/fn-java-fdk-build:jdk17-latest` | Multi-stage build | OpenJDK 17 |
| `fnproject/fn-java-fdk:jre17-latest` | Runtime | OpenJDK JRE 17 |

---

## Last Updated
- **Date:** 2026-05-18
- **Validated on:** macOS (Corretto 21.0.11), Linux (CI/CD)
- **Update trigger:** When any component version changes or new Java release is tested
